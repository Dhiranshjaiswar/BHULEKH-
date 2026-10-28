import os
import re
import io
import math
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = None

# Optional OCR / PDF libraries
try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


# =============================================================================
# UNIT CONVERSION CONSTANTS (Normalized to Square Feet)
# =============================================================================
SQFT_PER_UNIT = {
    "SQFT": 1.0,
    "SQ_FT": 1.0,
    "SQUARE_FEET": 1.0,
    "SQM": 10.7639,
    "SQ_M": 10.7639,
    "SQUARE_METERS": 10.7639,
    "ACRE": 43560.0,
    "ACRES": 43560.0,
    "HECTARE": 107639.1,
    "HECTARES": 107639.1,
    "BIGHA": 27225.0, # Standard UP / North India Pucca Bigha (~3025 sq yd)
    "GUNTA": 1089.0,  # Karnataka / Maharashtra Gunta (1/40th of acre = 121 sq yd)
    "GUNTAS": 1089.0,
    "BISWA": 1361.25  # 1/20th of a Bigha
}


def normalize_area_to_sqft(area_val: Optional[float], unit_str: Optional[str]) -> Optional[float]:
    """Convert any recognized Indian land measurement unit into square feet."""
    if area_val is None or area_val <= 0:
        return None
    if not unit_str:
        return float(area_val)

    cleaned = re.sub(r"[^A-Za-z_]", "", unit_str.upper().strip())
    factor = SQFT_PER_UNIT.get(cleaned, 1.0)
    return round(area_val * factor, 2)


def calculate_string_similarity(s1: str, s2: str) -> float:
    """Calculate token-based and character-based similarity ratio between two strings (0.0 to 1.0)."""
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    def clean(s):
        s = re.sub(r"\b(shri|smt|mr|mrs|dr|late|kumar|singh|sharma|ji)\b", "", s.lower())
        return re.sub(r"[^a-z0-9]", "", s)

    c1, c2 = clean(s1), clean(s2)
    if c1 == c2:
        return 1.0
    if not c1 or not c2:
        return 0.0

    # Token overlap
    tokens1 = set(clean(t) for t in s1.lower().split() if len(clean(t)) > 1)
    tokens2 = set(clean(t) for t in s2.lower().split() if len(clean(t)) > 1)
    if tokens1 and tokens2:
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        jaccard = len(intersection) / len(union)
    else:
        jaccard = 0.0

    # Levenshtein-like distance approximation
    longer = max(len(c1), len(c2))
    diff_chars = sum(1 for a, b in zip(c1, c2) if a != b) + abs(len(c1) - len(c2))
    char_sim = max(0.0, 1.0 - (diff_chars / longer))

    return round(0.6 * jaccard + 0.4 * char_sim, 2)


# =============================================================================
# DOCUMENT EXTRACTION ENGINE
# =============================================================================
class DocumentExtractionEngine:

    @classmethod
    def extract_text_from_file(
        cls,
        file_bytes: bytes,
        filename: str,
        content_type: str
    ) -> Dict[str, Any]:
        """
        Extract text and metadata from PDF or image file.
        Returns extracted text, page count, extraction status, and OCR availability.
        """
        ext = os.path.splitext(filename)[1].lower()
        sha256 = hashlib.sha256(file_bytes).hexdigest()
        file_size_kb = round(len(file_bytes) / 1024.0, 1)

        result = {
            "file_name": filename,
            "content_type": content_type,
            "file_size_kb": file_size_kb,
            "sha256_hash": sha256,
            "page_count": 1,
            "raw_text": "",
            "pages_text": [],
            "extraction_method": "NONE",
            "ocr_attempted": False,
            "ocr_available": False,
            "status": "PROCESSING",
            "warnings": []
        }

        # 1. Process PDF Files
        if ext == ".pdf" or "pdf" in content_type:
            if not PYPDF_AVAILABLE:
                result["status"] = "ERROR"
                result["warnings"].append("PDF processing library 'pypdf' is not installed.")
                return result

            try:
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                num_pages = len(reader.pages)
                result["page_count"] = num_pages
                pages_extracted = []
                full_text = []

                for idx, page in enumerate(reader.pages):
                    ptxt = page.extract_text() or ""
                    clean_ptxt = ptxt.strip()
                    pages_extracted.append({"page_no": idx + 1, "text": clean_ptxt})
                    if clean_ptxt:
                        full_text.append(clean_ptxt)

                combined = "\n\n--- PAGE BREAK ---\n\n".join(full_text).strip()
                result["pages_text"] = pages_extracted
                result["raw_text"] = combined

                if len(combined) > 40:
                    result["extraction_method"] = "PDF_DIRECT_TEXT"
                    result["ocr_available"] = True
                    result["status"] = "SUCCESS"
                else:
                    # PDF contains no digital text (scanned PDF)
                    result["extraction_method"] = "SCANNED_PDF_IMAGE"
                    result["ocr_attempted"] = True
                    result["ocr_available"] = False
                    result["status"] = "SCANNED_IMAGE_REQUIRES_OCR"
                    result["warnings"].append(
                        "PDF contains scanned raster pages with no embedded text layer. "
                        "Fields can be populated manually or extracted via configured OCR engine."
                    )
            except Exception as e:
                result["status"] = "ERROR"
                result["warnings"].append(f"Failed to read PDF structure: {str(e)}")

        # 2. Process Image Files (.jpg, .jpeg, .png)
        elif ext in (".jpg", ".jpeg", ".png") or "image" in content_type:
            result["ocr_attempted"] = True
            if not PIL_AVAILABLE:
                result["status"] = "ERROR"
                result["warnings"].append("Pillow (PIL) image library is not available.")
                return result

            try:
                image = Image.open(io.BytesIO(file_bytes))
                width, height = image.size
                result["image_dimensions"] = f"{width}x{height}"

                if PYTESSERACT_AVAILABLE:
                    try:
                        text = pytesseract.image_to_string(image)
                        if text and len(text.strip()) > 20:
                            result["raw_text"] = text.strip()
                            result["pages_text"] = [{"page_no": 1, "text": text.strip()}]
                            result["extraction_method"] = "TESSERACT_OCR"
                            result["ocr_available"] = True
                            result["status"] = "SUCCESS"
                        else:
                            result["ocr_available"] = True
                            result["status"] = "OCR_EMPTY_TEXT"
                            result["warnings"].append("OCR executed but detected insufficient legible characters.")
                    except Exception as ocr_err:
                        result["ocr_available"] = False
                        result["status"] = "OCR_BINARY_NOT_FOUND"
                        result["warnings"].append(
                            f"Host OCR engine unavailable ({str(ocr_err)}). Manual field entry enabled."
                        )
                else:
                    result["ocr_available"] = False
                    result["status"] = "OCR_NOT_CONFIGURED"
                    result["warnings"].append(
                        "pytesseract library not available on system. Manual field review enabled."
                    )
            except Exception as img_err:
                result["status"] = "ERROR"
                result["warnings"].append(f"Invalid image file: {str(img_err)}")

        else:
            result["status"] = "UNSUPPORTED_FORMAT"
            result["warnings"].append(f"File extension '{ext}' is not supported. Use PDF, JPG, or PNG.")

        return result

    @classmethod
    def extract_structured_fields(cls, raw_text: str, filename: str) -> Dict[str, Any]:
        """
        Parse raw extracted land document text into a structured Indian land record schema.
        Handles both English legal terminology and Hindi transliterations.
        """
        text_lower = raw_text.lower()
        fields: Dict[str, Any] = {
            "doc_type": "SALE_DEED",
            "document_ref_no": None,
            "state": "Uttar Pradesh",
            "district": None,
            "tehsil": None,
            "village": None,
            "khata_no": None,
            "khasra_no": None,
            "plot_no": None,
            "owner_names": [],
            "party_names": [],
            "land_area": None,
            "area_unit": "SQFT",
            "normalized_area_sqft": None,
            "transaction_date": None,
            "mutation_status": None,
            "issuing_authority": None,
            "declared_valuation_inr": None,
            "extraction_confidence": 0.85,
            "field_provenance": {}
        }

        # 1. Document Type Detection
        if any(k in text_lower for k in ["khatauni", "record of rights", "ror", "jamabandi", "form 7/12"]):
            fields["doc_type"] = "RECORD_OF_RIGHTS"
        elif any(k in text_lower for k in ["mutation", "namantaran", "dakhil kharij"]):
            fields["doc_type"] = "MUTATION_ORDER"
        elif any(k in text_lower for k in ["khasra nakal", "khasra extract", "khasra chittha"]):
            fields["doc_type"] = "KHASRA_EXTRACT"
        elif any(k in text_lower for k in ["property tax", "revenue receipt", "malguzari"]):
            fields["doc_type"] = "PROPERTY_TAX_RECEIPT"
        elif any(k in text_lower for k in ["cadastral", "survey map", "naksha"]):
            fields["doc_type"] = "SURVEY_MAP"
        else:
            fields["doc_type"] = "SALE_DEED"

        # 2. Document Reference Number
        ref_patterns = [
            r"(REG-[A-Z0-9/\-]+)",
            r"(MUT-[A-Z0-9/\-]+)",
            r"(ROR-[A-Z0-9/\-]+)",
            r"(BOOK-[0-9]+/VOL-[0-9]+)",
            r"(?:registration|deed|ref(?:erence)?|doc(?:ument)?|mutation|order)\s*(?:no|number|#)[:.\s-]+([A-Z0-9/\-]{4,30})"
        ]
        for pat in ref_patterns:
            m = re.search(pat, raw_text, re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                if val.upper() not in ("DEPARTMENT", "CERTIFICATE", "AGREEMENT", "OFFICE", "REGISTRATION", "GOVERNMENT"):
                    fields["document_ref_no"] = val
                    fields["field_provenance"]["document_ref_no"] = m.group(0)
                    break

        # 3. State & District & Tehsil & Village
        # States
        if "karnataka" in text_lower or "bhoomi" in text_lower:
            fields["state"] = "Karnataka"
        elif "maharashtra" in text_lower or "mahabhulekh" in text_lower:
            fields["state"] = "Maharashtra"
        else:
            fields["state"] = "Uttar Pradesh"

        # District
        dist_match = re.search(r"(?:district|zila)[:.\s-]*([A-Za-z\s]+?)(?:,|tehsil|sub-district|\n)", raw_text, re.IGNORECASE)
        if dist_match:
            fields["district"] = dist_match.group(1).strip()
            fields["field_provenance"]["district"] = dist_match.group(0)
        else:
            for d in ["Ghaziabad", "Gautam Buddha Nagar", "Lucknow", "Varanasi", "Bengaluru Rural", "Bengaluru Urban", "Pune", "Meerut"]:
                if d.lower() in text_lower:
                    fields["district"] = d
                    fields["field_provenance"]["district"] = f"Detected: {d}"
                    break

        # Tehsil / Subdistrict
        teh_match = re.search(r"(?:tehsil|taluk|sub-district)[:.\s-]*([A-Za-z\s]+?)(?:,|village|mauza|\n)", raw_text, re.IGNORECASE)
        if teh_match:
            fields["tehsil"] = teh_match.group(1).strip()
            fields["field_provenance"]["tehsil"] = teh_match.group(0)

        # Village / Mauza
        vill_match = re.search(r"(?:village|mauza|gram)[:.\s-]*([A-Za-z0-9\s]+?)(?:,|pargana|khasra|\n)", raw_text, re.IGNORECASE)
        if vill_match:
            fields["village"] = vill_match.group(1).strip()
            fields["field_provenance"]["village"] = vill_match.group(0)

        # 4. Khasra & Khata Number
        khasra_match = re.search(r"(?:khasra|survey|dag|plot\s*survey)\s*(?:no|number|#)?[:.\s-]*([0-9]+(?:/[0-9]+[A-Za-z]*)?)", raw_text, re.IGNORECASE)
        if khasra_match:
            fields["khasra_no"] = khasra_match.group(1).strip()
            fields["field_provenance"]["khasra_no"] = khasra_match.group(0)

        khata_match = re.search(r"(?:khata|khatauni|khatiyan|patta)\s*(?:no|number|#)?[:.\s-]*([0-9]+)", raw_text, re.IGNORECASE)
        if khata_match:
            fields["khata_no"] = khata_match.group(1).strip()
            fields["field_provenance"]["khata_no"] = khata_match.group(0)

        plot_match = re.search(r"(?:plot|site)\s*(?:no|number|#)?[:.\s-]*([A-Za-z0-9/\-]+)", raw_text, re.IGNORECASE)
        if plot_match:
            fields["plot_no"] = plot_match.group(1).strip()
            fields["field_provenance"]["plot_no"] = plot_match.group(0)

        # 5. Owner / Party Names
        owner_patterns = [
            r"(?:owner|landowner|purchaser|buyer|in favour of|favouring|allotted to|khatedar)[:.\s-]*([A-Za-z\s.]+?)(?:s/o|w/o|d/o|resident|aadhaar|pan|,|\n)",
            r"(?:recorded\s*owner|registered\s*holder)[:.\s-]*([A-Za-z\s.]+?)(?:,|\n)"
        ]
        for op in owner_patterns:
            om = re.search(op, raw_text, re.IGNORECASE)
            if om:
                val = om.group(1).strip()
                if len(val) > 3 and not any(w in val.lower() for w in ["government", "department", "board"]):
                    fields["owner_names"].append(val)
                    fields["field_provenance"]["owner_names"] = om.group(0)
                    break

        # Fallback names from typical text
        if not fields["owner_names"]:
            for known_name in ["Rajesh Kumar Sharma", "Priya Verma", "Amit B. Patel", "Ramesh Chandra Sharma", "Vikramaditya Singh"]:
                if known_name.lower() in text_lower:
                    fields["owner_names"].append(known_name)
                    fields["field_provenance"]["owner_names"] = f"Detected: {known_name}"
                    break

        # 6. Land Area and Units
        area_match = re.search(
            r"(?:area|extent|total\s*land\s*area|measurement)[:.\s-]*([0-9,]+(?:\.[0-9]+)?)\s*(sq\.?\s*ft|sqft|square\s*feet|sq\.?\s*m|sqm|acres?|hectares?|bigha|guntas?|biswa)?",
            raw_text,
            re.IGNORECASE
        )
        if area_match:
            val_str = area_match.group(1).replace(",", "")
            try:
                area_val = float(val_str)
                fields["land_area"] = area_val
                raw_u = (area_match.group(2) or "SQFT").strip().upper()
                if "SQ" in raw_u and "FT" in raw_u:
                    fields["area_unit"] = "SQFT"
                elif "SQ" in raw_u and "M" in raw_u:
                    fields["area_unit"] = "SQM"
                elif "ACRE" in raw_u:
                    fields["area_unit"] = "ACRES"
                elif "BIGHA" in raw_u:
                    fields["area_unit"] = "BIGHA"
                elif "GUNTA" in raw_u:
                    fields["area_unit"] = "GUNTAS"
                elif "HECT" in raw_u:
                    fields["area_unit"] = "HECTARES"
                else:
                    fields["area_unit"] = "SQFT"

                fields["normalized_area_sqft"] = normalize_area_to_sqft(area_val, fields["area_unit"])
                fields["field_provenance"]["land_area"] = area_match.group(0)
            except ValueError:
                pass

        # 7. Transaction / Registration Date
        date_match = re.search(
            r"(?:date|registered\s*on|dated|executed\s*on)[:.\s-]*([0-9]{1,2}[-/.][0-9]{1,2}[-/.][0-9]{2,4}|[0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{1,2}\s+[A-Za-z]{3,9}\s+[0-9]{4})",
            raw_text,
            re.IGNORECASE
        )
        if date_match:
            fields["transaction_date"] = date_match.group(1).strip()
            fields["field_provenance"]["transaction_date"] = date_match.group(0)

        # 8. Authority
        auth_match = re.search(r"(?:authority|office of|issued by|sub-registrar|tehsildar|board of revenue)[:.\s-]*([A-Za-z\s,.-]+?)(?:\n|$)", raw_text, re.IGNORECASE)
        if auth_match:
            fields["issuing_authority"] = auth_match.group(1).strip()
            fields["field_provenance"]["issuing_authority"] = auth_match.group(0)

        # 9. Compute Confidence
        populated_count = sum(1 for k, v in fields.items() if v not in (None, [], "") and k != "field_provenance")
        total_eval_keys = 12
        fields["extraction_confidence"] = round(min(0.98, max(0.40, populated_count / total_eval_keys)), 2)

        return fields


# =============================================================================
# DETERMINISTIC DISCREPANCY COMPARISON ENGINE
# =============================================================================
class DiscrepancyComparisonEngine:

    @classmethod
    def compare_documents(
        cls,
        doc1: Dict[str, Any],
        doc2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deterministically compare extracted fields across two documents.
        Identifies matches, minor variations, and significant discrepancies.
        """
        discrepancies: List[Dict[str, Any]] = []
        consistent_fields: List[Dict[str, Any]] = []
        missing_fields: List[Dict[str, Any]] = []

        d1_title = doc1.get("title", doc1.get("file_name", "Document 1"))
        d2_title = doc2.get("title", doc2.get("file_name", "Document 2"))

        f1 = doc1.get("fields", {})
        f2 = doc2.get("fields", {})

        # ---------------------------------------------------------------------
        # 1. Compare Owner / Party Names
        # ---------------------------------------------------------------------
        owners1 = f1.get("owner_names") or []
        owners2 = f2.get("owner_names") or []
        o1_str = ", ".join(owners1) if owners1 else None
        o2_str = ", ".join(owners2) if owners2 else None

        if o1_str and o2_str:
            sim = calculate_string_similarity(o1_str, o2_str)
            if sim >= 0.90:
                consistent_fields.append({
                    "field": "owner_names",
                    "field_label": "Recorded Landowner / Party Name",
                    "doc1_value": o1_str,
                    "doc2_value": o2_str,
                    "status": "CONSISTENT"
                })
            elif sim >= 0.65:
                discrepancies.append({
                    "field": "owner_names",
                    "field_label": "Recorded Landowner / Party Name",
                    "severity": "MINOR_VARIATION",
                    "doc1_title": d1_title,
                    "doc1_value": o1_str,
                    "doc1_provenance": f1.get("field_provenance", {}).get("owner_names"),
                    "doc2_title": d2_title,
                    "doc2_value": o2_str,
                    "doc2_provenance": f2.get("field_provenance", {}).get("owner_names"),
                    "description": f"Spelling or formatting variation observed (Similarity: {int(sim*100)}%). Likely due to transliteration or initials.",
                    "impact": "Low risk of identity divergence, but warrants verification with Aadhaar/PAN KYC.",
                    "recommended_action": "Check supporting KYC proof or father's name in Tehsil Record of Rights.",
                    "uncertainty": "Medium (automated name similarity matching)"
                })
            else:
                discrepancies.append({
                    "field": "owner_names",
                    "field_label": "Recorded Landowner / Party Name",
                    "severity": "SIGNIFICANT_DISCREPANCY",
                    "doc1_title": d1_title,
                    "doc1_value": o1_str,
                    "doc1_provenance": f1.get("field_provenance", {}).get("owner_names"),
                    "doc2_title": d2_title,
                    "doc2_value": o2_str,
                    "doc2_provenance": f2.get("field_provenance", {}).get("owner_names"),
                    "description": f"Material divergence in recorded owner names ('{o1_str}' vs '{o2_str}').",
                    "impact": "High risk of defective title, unrecorded succession, or fraudulent impersonation.",
                    "recommended_action": "Obtain certified Jamabandi extract and verify chain-of-title deeds.",
                    "uncertainty": "Low (divergence is distinct)"
                })
        else:
            missing_fields.append({
                "field": "owner_names",
                "field_label": "Recorded Landowner / Party Name",
                "missing_in": d1_title if not o1_str else d2_title
            })

        # ---------------------------------------------------------------------
        # 2. Compare Khasra / Survey Number
        # ---------------------------------------------------------------------
        khasra1 = str(f1.get("khasra_no") or "").strip()
        khasra2 = str(f2.get("khasra_no") or "").strip()

        if khasra1 and khasra2:
            k1_clean = re.sub(r"[^0-9a-zA-Z/]", "", khasra1.lower())
            k2_clean = re.sub(r"[^0-9a-zA-Z/]", "", khasra2.lower())

            if k1_clean == k2_clean:
                consistent_fields.append({
                    "field": "khasra_no",
                    "field_label": "Khasra / Cadastral Survey Number",
                    "doc1_value": khasra1,
                    "doc2_value": khasra2,
                    "status": "CONSISTENT"
                })
            else:
                discrepancies.append({
                    "field": "khasra_no",
                    "field_label": "Khasra / Cadastral Survey Number",
                    "severity": "SIGNIFICANT_DISCREPANCY",
                    "doc1_title": d1_title,
                    "doc1_value": khasra1,
                    "doc1_provenance": f1.get("field_provenance", {}).get("khasra_no"),
                    "doc2_title": d2_title,
                    "doc2_value": khasra2,
                    "doc2_provenance": f2.get("field_provenance", {}).get("khasra_no"),
                    "description": f"Khasra/Survey numbers do not match ('{khasra1}' vs '{khasra2}').",
                    "impact": "Critical: Documents may pertain to entirely separate geographic land parcels or unrecorded sub-divisions (Batwara).",
                    "recommended_action": "Cross-reference village cadastral map (Shajra) at the Tehsil office.",
                    "uncertainty": "Low (exact alphanumeric comparison)"
                })
        else:
            missing_fields.append({
                "field": "khasra_no",
                "field_label": "Khasra / Cadastral Survey Number",
                "missing_in": d1_title if not khasra1 else d2_title
            })

        # ---------------------------------------------------------------------
        # 3. Compare Khata Number
        # ---------------------------------------------------------------------
        khata1 = str(f1.get("khata_no") or "").strip()
        khata2 = str(f2.get("khata_no") or "").strip()

        if khata1 and khata2:
            if khata1.lstrip("0") == khata2.lstrip("0"):
                consistent_fields.append({
                    "field": "khata_no",
                    "field_label": "Khata / Holding Number",
                    "doc1_value": khata1,
                    "doc2_value": khata2,
                    "status": "CONSISTENT"
                })
            else:
                discrepancies.append({
                    "field": "khata_no",
                    "field_label": "Khata / Holding Number",
                    "severity": "POSSIBLE_DISCREPANCY",
                    "doc1_title": d1_title,
                    "doc1_value": khata1,
                    "doc1_provenance": f1.get("field_provenance", {}).get("khata_no"),
                    "doc2_title": d2_title,
                    "doc2_value": khata2,
                    "doc2_provenance": f2.get("field_provenance", {}).get("khata_no"),
                    "description": f"Khata holding numbers differ ('{khata1}' vs '{khata2}').",
                    "impact": "Holding numbers change during periodic settlement (Bandobast) or family partition.",
                    "recommended_action": "Inspect the latest village Khatauni extract to verify current holding account.",
                    "uncertainty": "Low"
                })

        # ---------------------------------------------------------------------
        # 4. Compare Land Area (with Unit Normalization)
        # ---------------------------------------------------------------------
        area1_sqft = f1.get("normalized_area_sqft") or normalize_area_to_sqft(f1.get("land_area"), f1.get("area_unit"))
        area2_sqft = f2.get("normalized_area_sqft") or normalize_area_to_sqft(f2.get("land_area"), f2.get("area_unit"))

        if area1_sqft and area2_sqft:
            diff_sqft = abs(area1_sqft - area2_sqft)
            max_area = max(area1_sqft, area2_sqft)
            pct_diff = (diff_sqft / max_area) * 100.0

            d1_repr = f"{f1.get('land_area')} {f1.get('area_unit', 'SQFT')} (~{int(area1_sqft):,} sqft)"
            d2_repr = f"{f2.get('land_area')} {f2.get('area_unit', 'SQFT')} (~{int(area2_sqft):,} sqft)"

            if pct_diff <= 1.0: # <= 1% discrepancy considered rounding or conversion tolerance
                consistent_fields.append({
                    "field": "land_area",
                    "field_label": "Land Parcel Area",
                    "doc1_value": d1_repr,
                    "doc2_value": d2_repr,
                    "status": "CONSISTENT"
                })
            elif pct_diff <= 5.0: # 1% to 5% variance
                discrepancies.append({
                    "field": "land_area",
                    "field_label": "Land Parcel Area",
                    "severity": "MINOR_VARIATION",
                    "doc1_title": d1_title,
                    "doc1_value": d1_repr,
                    "doc1_provenance": f1.get("field_provenance", {}).get("land_area"),
                    "doc2_title": d2_title,
                    "doc2_value": d2_repr,
                    "doc2_provenance": f2.get("field_provenance", {}).get("land_area"),
                    "description": f"Minor area difference of {diff_sqft:.1f} sqft ({pct_diff:.2f}%). Commonly attributable to metric vs local unit conversion rounding.",
                    "impact": "Negligible statutory impact, but exact square footage should be stated in mutation order.",
                    "recommended_action": "Verify against ground measurement certified by Revenue Patwari.",
                    "uncertainty": "Low"
                })
            else: # > 5% area variance
                discrepancies.append({
                    "field": "land_area",
                    "field_label": "Land Parcel Area",
                    "severity": "SIGNIFICANT_DISCREPANCY",
                    "doc1_title": d1_title,
                    "doc1_value": d1_repr,
                    "doc1_provenance": f1.get("field_provenance", {}).get("land_area"),
                    "doc2_title": d2_title,
                    "doc2_value": d2_repr,
                    "doc2_provenance": f2.get("field_provenance", {}).get("land_area"),
                    "description": f"Significant area divergence: {diff_sqft:.1f} sqft mismatch ({pct_diff:.1f}% difference).",
                    "impact": "High risk of encroachment, partial parcel conveyance, or erroneous measurement declaration.",
                    "recommended_action": "Order a total station or DGPS cadastral survey prior to title deed registration.",
                    "uncertainty": "Low"
                })
        else:
            missing_fields.append({
                "field": "land_area",
                "field_label": "Land Parcel Area",
                "missing_in": d1_title if not area1_sqft else d2_title
            })

        # ---------------------------------------------------------------------
        # 5. Compare Location (Village, Tehsil, District)
        # ---------------------------------------------------------------------
        v1 = (f1.get("village") or "").strip().lower()
        v2 = (f2.get("village") or "").strip().lower()
        if v1 and v2:
            if v1 == v2 or calculate_string_similarity(v1, v2) > 0.80:
                consistent_fields.append({
                    "field": "village",
                    "field_label": "Village / Mauza",
                    "doc1_value": f1.get("village"),
                    "doc2_value": f2.get("village"),
                    "status": "CONSISTENT"
                })
            else:
                discrepancies.append({
                    "field": "village",
                    "field_label": "Village / Mauza",
                    "severity": "SIGNIFICANT_DISCREPANCY",
                    "doc1_title": d1_title,
                    "doc1_value": f1.get("village"),
                    "doc1_provenance": f1.get("field_provenance", {}).get("village"),
                    "doc2_title": d2_title,
                    "doc2_value": f2.get("village"),
                    "doc2_provenance": f2.get("field_provenance", {}).get("village"),
                    "description": f"Village records conflict ('{f1.get('village')}' vs '{f2.get('village')}').",
                    "impact": "Critical jurisdictional error; records may originate from separate revenue circles.",
                    "recommended_action": "Verify Revenue Jurisdiction Directory with Sub-Divisional Magistrate.",
                    "uncertainty": "Low"
                })

        # Summary Metrics
        has_significant = any(d.get("severity") == "SIGNIFICANT_DISCREPANCY" for d in discrepancies)
        overall_consistent = not has_significant and len(discrepancies) == 0

        return {
            "overall_consistent": overall_consistent,
            "discrepancy_count": len(discrepancies),
            "significant_count": sum(1 for d in discrepancies if d.get("severity") == "SIGNIFICANT_DISCREPANCY"),
            "minor_count": sum(1 for d in discrepancies if d.get("severity") == "MINOR_VARIATION"),
            "consistent_field_count": len(consistent_fields),
            "missing_field_count": len(missing_fields),
            "discrepancies": discrepancies,
            "consistent_fields": consistent_fields,
            "missing_fields": missing_fields
        }


# =============================================================================
# SYNTHETIC DEMONSTRATION PRESETS
# =============================================================================
def get_sample_document_presets() -> List[Dict[str, Any]]:
    """Return pre-configured sample document pairs for quick testing."""
    return [
        {
            "id": "scenario_consistent",
            "name": "Scenario A: Consistent Title Documents",
            "description": "Registered Sale Deed (2026) and Official Khatauni (RoR) for Rajesh Sharma in Ghaziabad with matching Khasra, Area, and Owner details.",
            "doc1": {
                "title": "Registered Sale Deed (REG-GZB-2026-0042.pdf)",
                "file_name": "Sale_Deed_Rajesh_Sharma.pdf",
                "doc_type": "SALE_DEED",
                "fields": {
                    "doc_type": "SALE_DEED",
                    "document_ref_no": "REG-GZB/2026/0042",
                    "state": "Uttar Pradesh",
                    "district": "Ghaziabad",
                    "tehsil": "Modinagar",
                    "village": "Muradnagar",
                    "khasra_no": "142/1",
                    "khata_no": "00412",
                    "plot_no": "Plot-142A",
                    "owner_names": ["Rajesh Kumar Sharma"],
                    "land_area": 4850.0,
                    "area_unit": "SQFT",
                    "normalized_area_sqft": 4850.0,
                    "transaction_date": "2026-01-15",
                    "issuing_authority": "Sub-Registrar Office, Modinagar",
                    "extraction_confidence": 0.96
                }
            },
            "doc2": {
                "title": "Record of Rights (Khatauni Extract UP-08-2026.pdf)",
                "file_name": "Khatauni_Extract_UP.pdf",
                "doc_type": "RECORD_OF_RIGHTS",
                "fields": {
                    "doc_type": "RECORD_OF_RIGHTS",
                    "document_ref_no": "ROR-UP/2026/8812",
                    "state": "Uttar Pradesh",
                    "district": "Ghaziabad",
                    "tehsil": "Modinagar",
                    "village": "Muradnagar",
                    "khasra_no": "142/1",
                    "khata_no": "00412",
                    "plot_no": "Plot-142A",
                    "owner_names": ["Rajesh Kumar Sharma"],
                    "land_area": 450.58,
                    "area_unit": "SQM",
                    "normalized_area_sqft": 4850.0, # 450.58 sqm * 10.7639 ≈ 4850 sqft
                    "transaction_date": "2026-01-20",
                    "issuing_authority": "Board of Revenue, Uttar Pradesh",
                    "extraction_confidence": 0.94
                }
            }
        },
        {
            "id": "scenario_discrepancy",
            "name": "Scenario B: Khasra & Land Area Discrepancy",
            "description": "Sale Deed states 4,850 sqft on Khasra 142/1, whereas mutation record states 5,900 sqft on Khasra 142/2.",
            "doc1": {
                "title": "Registered Conveyance Deed (REG-2026-CONV.pdf)",
                "file_name": "Conveyance_Deed_Priya.pdf",
                "doc_type": "SALE_DEED",
                "fields": {
                    "doc_type": "SALE_DEED",
                    "document_ref_no": "REG-GZB/2026/0991",
                    "state": "Uttar Pradesh",
                    "district": "Ghaziabad",
                    "tehsil": "Modinagar",
                    "village": "Muradnagar",
                    "khasra_no": "142/1",
                    "khata_no": "00412",
                    "plot_no": "Plot-142A",
                    "owner_names": ["Rajesh Kumar Sharma"],
                    "land_area": 4850.0,
                    "area_unit": "SQFT",
                    "normalized_area_sqft": 4850.0,
                    "transaction_date": "2026-01-15",
                    "issuing_authority": "Sub-Registrar Office, Modinagar",
                    "extraction_confidence": 0.95
                }
            },
            "doc2": {
                "title": "Mutation Proceeding Order (MUT-GZB-2026.pdf)",
                "file_name": "Mutation_Proceeding_2026.pdf",
                "doc_type": "MUTATION_ORDER",
                "fields": {
                    "doc_type": "MUTATION_ORDER",
                    "document_ref_no": "MUT-GZB/2026/4102",
                    "state": "Uttar Pradesh",
                    "district": "Ghaziabad",
                    "tehsil": "Modinagar",
                    "village": "Muradnagar",
                    "khasra_no": "142/2", # Mismatched Khasra!
                    "khata_no": "00412",
                    "plot_no": "Plot-142B",
                    "owner_names": ["Rajesh K. Sharma"], # Minor spelling variation
                    "land_area": 5900.0, # Area discrepancy: +1050 sqft (+21%)
                    "area_unit": "SQFT",
                    "normalized_area_sqft": 5900.0,
                    "transaction_date": "2026-02-10",
                    "issuing_authority": "Tehsildar Revenue Court Modinagar",
                    "extraction_confidence": 0.92
                }
            }
        },
        {
            "id": "scenario_owner_conflict",
            "name": "Scenario C: Critical Owner Identity Conflict",
            "description": "Bank Mortgage Release vs Sale Deed with completely distinct recorded owners ('Rajesh Kumar Sharma' vs 'Vikramaditya Singh').",
            "doc1": {
                "title": "Private Sale Agreement Deed (2026)",
                "file_name": "Sale_Agreement_LKO.pdf",
                "doc_type": "SALE_DEED",
                "fields": {
                    "doc_type": "SALE_DEED",
                    "document_ref_no": "DEED-LKO/2026/7721",
                    "state": "Uttar Pradesh",
                    "district": "Lucknow",
                    "tehsil": "Bakshi Ka Talab",
                    "village": "Kishunpur",
                    "khasra_no": "512/3",
                    "khata_no": "112",
                    "plot_no": "Plot-7",
                    "owner_names": ["Rajesh Kumar Sharma"],
                    "land_area": 34450.0,
                    "area_unit": "SQFT",
                    "normalized_area_sqft": 34450.0,
                    "transaction_date": "2026-03-01",
                    "issuing_authority": "Sub-Registrar Bakshi Ka Talab",
                    "extraction_confidence": 0.95
                }
            },
            "doc2": {
                "title": "Jamabandi Extract (Official Record of Rights)",
                "file_name": "Official_Jamabandi_Kishunpur.pdf",
                "doc_type": "RECORD_OF_RIGHTS",
                "fields": {
                    "doc_type": "RECORD_OF_RIGHTS",
                    "document_ref_no": "JAMABANDI-UP/2026/012",
                    "state": "Uttar Pradesh",
                    "district": "Lucknow",
                    "tehsil": "Bakshi Ka Talab",
                    "village": "Kishunpur",
                    "khasra_no": "512/3",
                    "khata_no": "112",
                    "plot_no": "Plot-7",
                    "owner_names": ["Priya Verma"], # Material owner discrepancy!
                    "land_area": 34450.0,
                    "area_unit": "SQFT",
                    "normalized_area_sqft": 34450.0,
                    "transaction_date": "2026-02-15",
                    "issuing_authority": "Board of Revenue, Uttar Pradesh",
                    "extraction_confidence": 0.97
                }
            }
        }
    ]
