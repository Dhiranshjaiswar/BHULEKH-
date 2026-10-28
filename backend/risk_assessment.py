import math
from typing import Dict, Any, List, Optional
from datetime import datetime

# =============================================================================
# SCORING ENGINE RULES & WEIGHT CONFIGURATION
# =============================================================================
RISK_RULES_CONFIG = {
    # 1. Cross-Document Inconsistencies
    "OWNER_MISMATCH": {
        "name": "Recorded Ownership Divergence",
        "category": "TITLE_INTEGRITY",
        "severity": "CRITICAL",
        "score_weight": 30,
        "significance": "Documents exhibit fundamentally divergent owner names without an intervening registered conveyance or succession mutation.",
        "action": "Demand certified 30-year search report from Sub-Registrar and verify lineage in Revenue Court succession register."
    },
    "KHASRA_MISMATCH": {
        "name": "Cadastral Survey / Khasra Number Conflict",
        "category": "PARCEL_IDENTIFICATION",
        "severity": "CRITICAL",
        "score_weight": 25,
        "significance": "Documents reference different Khasra/Survey parcels, indicating either a cross-property mix-up or unrecorded sub-division (Batwara).",
        "action": "Commission spot physical verification and inspect the official village Shajra cadastral map at Tehsil."
    },
    "AREA_DIVERGENCE_HIGH": {
        "name": "Material Land Area Discrepancy (>5%)",
        "category": "MEASUREMENT_ACCURACY",
        "severity": "HIGH",
        "score_weight": 20,
        "significance": "Declared land extent diverges significantly between documents, risking conveyance of encroached or non-existent land.",
        "action": "Conduct total-station DGPS boundary survey by government-certified cadastral surveyor before executing deed."
    },
    "AREA_DIVERGENCE_LOW": {
        "name": "Minor Land Area Variance (1-5%)",
        "category": "MEASUREMENT_ACCURACY",
        "severity": "ADVISORY",
        "score_weight": 5,
        "significance": "Slight variation likely attributable to imperial-to-metric unit conversion or rounding in local revenue units.",
        "action": "Record precise metric extent in upcoming mutation petition."
    },
    "VILLAGE_MISMATCH": {
        "name": "Revenue Village / Mauza Conflict",
        "category": "JURISDICTION",
        "severity": "CRITICAL",
        "score_weight": 25,
        "significance": "Documents cite different revenue villages, pointing to severe jurisdictional error or mismatched records.",
        "action": "Verify Revenue Jurisdiction Directory with Sub-Divisional Magistrate."
    },
    "OWNER_SPELLING_VARIANCE": {
        "name": "Owner Name Transliteration / Formatting Variance",
        "category": "TITLE_INTEGRITY",
        "severity": "WARNING",
        "score_weight": 8,
        "significance": "Minor spelling differences between English deeds and vernacular revenue passbooks.",
        "action": "Obtain notarized identity affidavit and link Aadhaar/PAN KYC."
    },

    # 2. Statutory Encumbrances & Court Litigation
    "ACTIVE_COURT_DISPUTE": {
        "name": "Active Court Injunction / Revenue Dispute Flagged",
        "category": "LEGAL_ENCUMBRANCE",
        "severity": "CRITICAL",
        "score_weight": 35,
        "significance": "The parcel has an active civil suit or revenue stay order flagged on the national judicial data grid (NJDG). Any transfer is subject to lis pendens (Section 52 of Transfer of Property Act).",
        "action": "Obtain certified copy of order sheet from relevant e-Court or Revenue Court before entering agreements."
    },
    "ACTIVE_BANK_MORTGAGE": {
        "name": "Active Financial Institution Lien / Mortgage",
        "category": "FINANCIAL_ENCUMBRANCE",
        "severity": "HIGH",
        "score_weight": 20,
        "significance": "Commercial bank holds an equitable mortgage or charge on the parcel. Property cannot be freely transferred without Bank NOC.",
        "action": "Request formal No-Objection Certificate (NOC) and Discharge Deed from the mortgaging bank."
    },
    "UNVERIFIED_BOUNDARY": {
        "name": "Cadastral Boundary Not Demarcated",
        "category": "SURVEY_ENCUMBRANCE",
        "severity": "WARNING",
        "score_weight": 12,
        "significance": "Physical ground boundary has not been confirmed via DGPS cadastral survey, posing risk of neighbour boundary encroachment.",
        "action": "File Form 24 for boundary demarcation (Hadd-Shikani) with Tehsil Surveyor."
    },
    "OUTSTANDING_LAND_REVENUE": {
        "name": "Unpaid Land Revenue / Property Tax",
        "category": "STATUTORY_DUES",
        "severity": "ADVISORY",
        "score_weight": 8,
        "significance": "Outstanding government cess or municipal property tax liability attaches as a first statutory charge on the property.",
        "action": "Demand latest No-Dues Certificate and tax clearance challan from municipal corporation/Tehsil."
    },

    # 3. Completeness & Chain of Title Gaps
    "MISSING_KHASRA_IDENTIFIER": {
        "name": "Missing Primary Khasra Identifier",
        "category": "RECORD_COMPLETENESS",
        "severity": "HIGH",
        "score_weight": 18,
        "significance": "Document lacks standard cadastral parcel survey number, impeding geographic verification.",
        "action": "Obtain certified copy of latest Record of Rights (Khatauni / 7-12) containing full Khasra schedule."
    },
    "MISSING_DEED_REFERENCE": {
        "name": "Missing Statutory Deed Registration Number",
        "category": "RECORD_COMPLETENESS",
        "severity": "WARNING",
        "score_weight": 10,
        "significance": "No official Book/Volume or SRO registration reference provided.",
        "action": "Search SRO digital index records to retrieve formal registration certificate."
    },
    "SINGLE_DOCUMENT_ONLY": {
        "name": "Isolated Document (Absence of Corroborating Record)",
        "category": "CHAIN_OF_TITLE",
        "severity": "WARNING",
        "score_weight": 15,
        "significance": "Review relies on a single uncorroborated document. Indian revenue jurisprudence requires matching both the registered deed and the government Record of Rights (Khatauni).",
        "action": "Upload or obtain the corresponding state revenue portal Jamabandi / Khatauni passbook extract."
    }
}


class LandRiskAssessmentEngine:
    """
    Deterministic evidence-based risk assessment engine for land records.
    """

    @classmethod
    def evaluate_risk(
        cls,
        documents: List[Dict[str, Any]],
        discrepancies: Optional[List[Dict[str, Any]]] = None,
        parcel_record: Optional[Dict[str, Any]] = None,
        user_declared_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compute a transparent risk evaluation across submitted documents,
        cross-document discrepancies, and linked statutory registry flags.
        """
        evaluated_factors: List[Dict[str, Any]] = []
        information_gaps: List[Dict[str, Any]] = []
        recommended_actions: List[str] = []

        total_score = 0
        max_possible_penalty = 100

        # ---------------------------------------------------------------------
        # 1. Evaluate Discrepancy Findings (from Document Verification Tool)
        # ---------------------------------------------------------------------
        if discrepancies:
            for d in discrepancies:
                field = d.get("field")
                sev = d.get("severity")
                doc1_val = d.get("doc1_value")
                doc2_val = d.get("doc2_value")

                if field == "owner_names":
                    if sev == "SIGNIFICANT_DISCREPANCY":
                        rule = RISK_RULES_CONFIG["OWNER_MISMATCH"]
                        evaluated_factors.append({
                            "factor_id": "OWNER_MISMATCH",
                            "factor_name": rule["name"],
                            "category": rule["category"],
                            "severity": rule["severity"],
                            "score_contribution": rule["score_weight"],
                            "evidence": f"Recorded owner mismatch: '{doc1_val}' in {d.get('doc1_title')} vs '{doc2_val}' in {d.get('doc2_title')}.",
                            "significance": rule["significance"],
                            "action": rule["action"]
                        })
                        total_score += rule["score_weight"]
                        recommended_actions.append(rule["action"])
                    elif sev == "MINOR_VARIATION":
                        rule = RISK_RULES_CONFIG["OWNER_SPELLING_VARIANCE"]
                        evaluated_factors.append({
                            "factor_id": "OWNER_SPELLING_VARIANCE",
                            "factor_name": rule["name"],
                            "category": rule["category"],
                            "severity": rule["severity"],
                            "score_contribution": rule["score_weight"],
                            "evidence": f"Spelling variance in owner name: '{doc1_val}' vs '{doc2_val}'.",
                            "significance": rule["significance"],
                            "action": rule["action"]
                        })
                        total_score += rule["score_weight"]

                elif field == "khasra_no":
                    rule = RISK_RULES_CONFIG["KHASRA_MISMATCH"]
                    evaluated_factors.append({
                        "factor_id": "KHASRA_MISMATCH",
                        "factor_name": rule["name"],
                        "category": rule["category"],
                        "severity": rule["severity"],
                        "score_contribution": rule["score_weight"],
                        "evidence": f"Conflicting parcel numbers: '{doc1_val}' vs '{doc2_val}'.",
                        "significance": rule["significance"],
                        "action": rule["action"]
                    })
                    total_score += rule["score_weight"]
                    recommended_actions.append(rule["action"])

                elif field == "land_area":
                    if sev == "SIGNIFICANT_DISCREPANCY":
                        rule = RISK_RULES_CONFIG["AREA_DIVERGENCE_HIGH"]
                        evaluated_factors.append({
                            "factor_id": "AREA_DIVERGENCE_HIGH",
                            "factor_name": rule["name"],
                            "category": rule["category"],
                            "severity": rule["severity"],
                            "score_contribution": rule["score_weight"],
                            "evidence": f"Discrepant land area: '{doc1_val}' vs '{doc2_val}'.",
                            "significance": rule["significance"],
                            "action": rule["action"]
                        })
                        total_score += rule["score_weight"]
                        recommended_actions.append(rule["action"])
                    elif sev == "MINOR_VARIATION":
                        rule = RISK_RULES_CONFIG["AREA_DIVERGENCE_LOW"]
                        evaluated_factors.append({
                            "factor_id": "AREA_DIVERGENCE_LOW",
                            "factor_name": rule["name"],
                            "category": rule["category"],
                            "severity": rule["severity"],
                            "score_contribution": rule["score_weight"],
                            "evidence": f"Minor area variance: '{doc1_val}' vs '{doc2_val}'.",
                            "significance": rule["significance"],
                            "action": rule["action"]
                        })
                        total_score += rule["score_weight"]

                elif field == "village":
                    rule = RISK_RULES_CONFIG["VILLAGE_MISMATCH"]
                    evaluated_factors.append({
                        "factor_id": "VILLAGE_MISMATCH",
                        "factor_name": rule["name"],
                        "category": rule["category"],
                        "severity": rule["severity"],
                        "score_contribution": rule["score_weight"],
                        "evidence": f"Village records conflict: '{doc1_val}' vs '{doc2_val}'.",
                        "significance": rule["significance"],
                        "action": rule["action"]
                    })
                    total_score += rule["score_weight"]
                    recommended_actions.append(rule["action"])

        # ---------------------------------------------------------------------
        # 2. Evaluate Linked Parcel Registry Data (if available in database)
        # ---------------------------------------------------------------------
        if parcel_record:
            # Active Court Injunction
            if parcel_record.get("is_disputed"):
                rule = RISK_RULES_CONFIG["ACTIVE_COURT_DISPUTE"]
                details = parcel_record.get("dispute_details") or "Civil injunction flagged on parcel."
                case_no = parcel_record.get("dispute_case_no") or "Case No. Recorded"
                evaluated_factors.append({
                    "factor_id": "ACTIVE_COURT_DISPUTE",
                    "factor_name": rule["name"],
                    "category": rule["category"],
                    "severity": rule["severity"],
                    "score_contribution": rule["score_weight"],
                    "evidence": f"Flagged in registry: '{case_no}' — {details}",
                    "significance": rule["significance"],
                    "action": rule["action"]
                })
                total_score += rule["score_weight"]
                recommended_actions.append(rule["action"])

            # Active Bank Mortgage / Lien
            if parcel_record.get("is_mortgaged"):
                rule = RISK_RULES_CONFIG["ACTIVE_BANK_MORTGAGE"]
                bank = parcel_record.get("mortgage_bank") or "Commercial Bank"
                amt = parcel_record.get("mortgage_amount_lakhs")
                amt_str = f"₹{amt} Lakhs" if amt else "Amount Unspecified"
                evaluated_factors.append({
                    "factor_id": "ACTIVE_BANK_MORTGAGE",
                    "factor_name": rule["name"],
                    "category": rule["category"],
                    "severity": rule["severity"],
                    "score_contribution": rule["score_weight"],
                    "evidence": f"Active lien registered by {bank} ({amt_str}).",
                    "significance": rule["significance"],
                    "action": rule["action"]
                })
                total_score += rule["score_weight"]
                recommended_actions.append(rule["action"])

            # Unverified Boundary
            if parcel_record.get("boundary_verified") is False:
                rule = RISK_RULES_CONFIG["UNVERIFIED_BOUNDARY"]
                evaluated_factors.append({
                    "factor_id": "UNVERIFIED_BOUNDARY",
                    "factor_name": rule["name"],
                    "category": rule["category"],
                    "severity": rule["severity"],
                    "score_contribution": rule["score_weight"],
                    "evidence": "Cadastral GIS ground boundary demarcated as unverified.",
                    "significance": rule["significance"],
                    "action": rule["action"]
                })
                total_score += rule["score_weight"]

            # Tax Clearance
            if parcel_record.get("tax_cleared") is False:
                rule = RISK_RULES_CONFIG["OUTSTANDING_LAND_REVENUE"]
                evaluated_factors.append({
                    "factor_id": "OUTSTANDING_LAND_REVENUE",
                    "factor_name": rule["name"],
                    "category": rule["category"],
                    "severity": rule["severity"],
                    "score_contribution": rule["score_weight"],
                    "evidence": "Outstanding land revenue or local cess flagged as unpaid.",
                    "significance": rule["significance"],
                    "action": rule["action"]
                })
                total_score += rule["score_weight"]

        # ---------------------------------------------------------------------
        # 3. Evaluate Document Set Completeness & Information Gaps
        # ---------------------------------------------------------------------
        doc_count = len(documents) if documents else 0

        if doc_count == 0:
            # No documents provided at all
            return {
                "risk_score": 0,
                "risk_category": "Insufficient information to assess",
                "risk_level_code": "INSUFFICIENT_DATA",
                "completeness_percentage": 0,
                "is_sufficient_evidence": False,
                "evaluated_factors": [],
                "information_gaps": [{
                    "item": "No Title Documents Uploaded",
                    "description": "Assessment requires at least one registered deed or revenue extract.",
                    "impact": "Cannot assess title integrity."
                }],
                "recommended_actions": ["Upload registered Sale Deed or certified Record of Rights extract."],
                "assessment_timestamp": datetime.utcnow().isoformat() + "Z",
                "disclaimer": "This automated assessment is an informational tool and does not constitute a legal title opinion or government guarantee."
            }

        # Single Document warning
        if doc_count == 1:
            rule = RISK_RULES_CONFIG["SINGLE_DOCUMENT_ONLY"]
            evaluated_factors.append({
                "factor_id": "SINGLE_DOCUMENT_ONLY",
                "factor_name": rule["name"],
                "category": rule["category"],
                "severity": rule["severity"],
                "score_contribution": rule["score_weight"],
                "evidence": f"Only 1 document provided ({documents[0].get('title', 'Document')}). Independent revenue corroboration is absent.",
                "significance": rule["significance"],
                "action": rule["action"]
            })
            total_score += rule["score_weight"]
            information_gaps.append({
                "item": "Independent Revenue Record (Khatauni / Jamabandi)",
                "description": "Corroboration from current Tehsil Record of Rights is missing.",
                "impact": "Single-source reliance increases risk of unrecorded transfers or cancelled deeds."
            })
            recommended_actions.append(rule["action"])

        # Check for missing Khasra in any document
        for idx, doc in enumerate(documents, 1):
            f = doc.get("fields", {})
            d_name = doc.get("title", f"Document #{idx}")
            if not f.get("khasra_no"):
                information_gaps.append({
                    "item": f"Khasra Identifier Missing in {d_name}",
                    "description": "Document does not explicitly specify parcel khasra / survey number.",
                    "impact": "Geographic linkage cannot be statutorily affirmed."
                })
            if not f.get("document_ref_no"):
                information_gaps.append({
                    "item": f"Registration / Reference Number Missing in {d_name}",
                    "description": "Official registration reference number was not detected.",
                    "impact": "Hindered direct online SRO verification."
                })

        # Cap the final score to 100
        normalized_score = min(100, max(0, total_score))

        # Determine Assessment Status
        if normalized_score <= 25:
            category = "Lower level of identified record-related concerns"
            level_code = "LOW_RISK"
        elif normalized_score <= 55:
            category = "Moderate level of identified record-related concerns"
            level_code = "MODERATE_RISK"
        else:
            category = "Higher level of identified record-related concerns"
            level_code = "HIGH_RISK"

        # Calculate Completeness Percentage
        # Base: 40% for 1 doc, 75% for 2 docs, 90% for 3+ docs, minus 10% for each critical missing field
        base_completeness = 40 if doc_count == 1 else (75 if doc_count == 2 else 90)
        if parcel_record:
            base_completeness = min(100, base_completeness + 10)
        gap_penalty = min(30, len(information_gaps) * 5)
        completeness_pct = max(30, min(100, base_completeness - gap_penalty))

        # Default actions if none was triggered
        if not recommended_actions:
            recommended_actions = [
                "Obtain official non-encumbrance certificate (EC / Barah Sala) for past 12-30 years from Sub-Registrar.",
                "Verify latest khatauni entry online on state Bhulekh portal to confirm active mutation.",
                "Ensure ground boundaries match the village cadastral map before completing transactions."
            ]

        # Deduplicate actions
        unique_actions = list(dict.fromkeys(recommended_actions))

        return {
            "risk_score": normalized_score,
            "risk_category": category,
            "risk_level_code": level_code,
            "completeness_percentage": completeness_pct,
            "is_sufficient_evidence": True,
            "documents_evaluated_count": doc_count,
            "discrepancies_evaluated_count": len(discrepancies) if discrepancies else 0,
            "evaluated_factors": evaluated_factors,
            "information_gaps": information_gaps,
            "recommended_actions": unique_actions,
            "assessment_timestamp": datetime.utcnow().isoformat() + "Z",
            "disclaimer": "This automated assessment is an informational tool and does not constitute a legal title opinion or government guarantee."
        }
