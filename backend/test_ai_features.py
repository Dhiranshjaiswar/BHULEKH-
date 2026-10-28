import pytest
from fastapi.testclient import TestClient
from main import app
from document_verification import (
    DocumentExtractionEngine, DiscrepancyComparisonEngine,
    normalize_area_to_sqft, calculate_string_similarity, get_sample_document_presets
)
from risk_assessment import LandRiskAssessmentEngine
from delay_analytics import DelayAnalyticsEngine, generate_synthetic_workflow_records
from ai_service import AIService

client = TestClient(app)

# =============================================================================
# 1. DOCUMENT VERIFICATION TESTS
# =============================================================================

def test_unit_conversion():
    """Verify standard Indian land area unit conversions into square feet."""
    assert normalize_area_to_sqft(1.0, "ACRE") == 43560.0
    assert normalize_area_to_sqft(2.0, "ACRES") == 87120.0
    assert normalize_area_to_sqft(1.0, "BIGHA") == 27225.0
    assert normalize_area_to_sqft(10.0, "GUNTA") == 10890.0
    assert normalize_area_to_sqft(100.0, "SQM") == 1076.39
    assert normalize_area_to_sqft(5000.0, "SQFT") == 5000.0
    assert normalize_area_to_sqft(None, "SQFT") is None


def test_string_similarity():
    """Verify name similarity calculation for transliterations vs distinct names."""
    # Identical
    assert calculate_string_similarity("Rajesh Kumar Sharma", "Rajesh Kumar Sharma") == 1.0
    # Minor transliteration / initials / honorific
    sim_minor = calculate_string_similarity("Rajesh Kumar Sharma", "Rajesh K. Sharma")
    assert sim_minor >= 0.70
    # Completely different person
    sim_diff = calculate_string_similarity("Rajesh Kumar Sharma", "Vikramaditya Singh")
    assert sim_diff < 0.30


def test_structured_field_extraction():
    """Verify structured field extraction from sample land deed text."""
    sample_deed_text = """
    GOVERNMENT OF UTTAR PRADESH - REGISTRATION DEPARTMENT
    SUB-REGISTRAR OFFICE MODINAGAR, DISTRICT GHAZIABAD
    REGISTERED CONVEYANCE SALE DEED
    Registration No: REG-GZB/2026/0042
    Dated: 15-01-2026
    
    This Indenture made in favour of:
    Purchaser/Landowner: Rajesh Kumar Sharma, s/o Ramesh Chandra Sharma
    Mauza/Village: Muradnagar, Tehsil: Modinagar, District: Ghaziabad
    Khasra No: 142/1, Khata No: 00412, Plot No: Plot-142A
    Total Land Area: 4850.0 Sq. Ft. (450.58 Sq. Meters)
    Declared Valuation: Rs. 1,26,10,000/-
    """
    fields = DocumentExtractionEngine.extract_structured_fields(sample_deed_text, "Sale_Deed.pdf")

    assert fields["doc_type"] == "SALE_DEED"
    assert fields["document_ref_no"] == "REG-GZB/2026/0042"
    assert fields["khasra_no"] == "142/1"
    assert fields["khata_no"] == "00412"
    assert fields["land_area"] == 4850.0
    assert fields["area_unit"] == "SQFT"
    assert fields["normalized_area_sqft"] == 4850.0
    assert "Rajesh Kumar Sharma" in fields["owner_names"]
    assert fields["extraction_confidence"] >= 0.75


def test_deterministic_discrepancy_matching_consistent():
    """Verify matching documents produce no significant discrepancies."""
    presets = get_sample_document_presets()
    consistent_scenario = presets[0] # Scenario A
    doc1 = consistent_scenario["doc1"]
    doc2 = consistent_scenario["doc2"]

    result = DiscrepancyComparisonEngine.compare_documents(doc1, doc2)
    assert result["overall_consistent"] is True
    assert result["significant_count"] == 0
    assert result["discrepancy_count"] == 0
    assert result["consistent_field_count"] >= 3


def test_deterministic_discrepancy_khasra_and_area_divergence():
    """Verify discrepancies are flagged when Khasra and Area diverge."""
    presets = get_sample_document_presets()
    discrepant_scenario = presets[1] # Scenario B: Khasra 142/1 vs 142/2 & 4850 sqft vs 5900 sqft
    doc1 = discrepant_scenario["doc1"]
    doc2 = discrepant_scenario["doc2"]

    result = DiscrepancyComparisonEngine.compare_documents(doc1, doc2)
    assert result["overall_consistent"] is False
    assert result["significant_count"] >= 2 # Khasra & Land Area

    discrepant_fields = [d["field"] for d in result["discrepancies"]]
    assert "khasra_no" in discrepant_fields
    assert "land_area" in discrepant_fields


def test_deterministic_discrepancy_owner_divergence():
    """Verify critical discrepancy when recorded owners fundamentally diverge."""
    presets = get_sample_document_presets()
    owner_conflict_scenario = presets[2] # Scenario C: Rajesh Sharma vs Priya Verma
    doc1 = owner_conflict_scenario["doc1"]
    doc2 = owner_conflict_scenario["doc2"]

    result = DiscrepancyComparisonEngine.compare_documents(doc1, doc2)
    assert result["overall_consistent"] is False
    owner_disc = next((d for d in result["discrepancies"] if d["field"] == "owner_names"), None)
    assert owner_disc is not None
    assert owner_disc["severity"] == "SIGNIFICANT_DISCREPANCY"


# =============================================================================
# 2. LAND RISK ASSESSMENT TESTS
# =============================================================================

def test_risk_assessment_consistent_docs():
    """Verify consistent documents yield low risk score <= 25."""
    presets = get_sample_document_presets()
    docs = [presets[0]["doc1"], presets[0]["doc2"]]

    assessment = LandRiskAssessmentEngine.evaluate_risk(documents=docs, discrepancies=[])
    assert assessment["risk_level_code"] == "LOW_RISK"
    assert assessment["risk_score"] <= 25
    assert assessment["is_sufficient_evidence"] is True
    assert assessment["completeness_percentage"] >= 70


def test_risk_assessment_discrepant_and_encumbered():
    """Verify significant discrepancies and active court dispute elevate risk."""
    presets = get_sample_document_presets()
    docs = [presets[1]["doc1"], presets[1]["doc2"]]
    comp = DiscrepancyComparisonEngine.compare_documents(docs[0], docs[1])

    mock_parcel_encumbered = {
        "id": "UP-GZB-IND-00012345",
        "ulin_pin": "UP08GZB012345",
        "is_disputed": True,
        "dispute_case_no": "OS/2026/GZB/88",
        "dispute_details": "Civil dispute pending in Revenue Court",
        "is_mortgaged": True,
        "mortgage_bank": "State Bank of India",
        "mortgage_amount_lakhs": 45.0,
        "tax_cleared": False,
        "boundary_verified": False
    }

    assessment = LandRiskAssessmentEngine.evaluate_risk(
        documents=docs,
        discrepancies=comp["discrepancies"],
        parcel_record=mock_parcel_encumbered
    )

    assert assessment["risk_level_code"] == "HIGH_RISK"
    assert assessment["risk_score"] >= 60

    factor_ids = [f["factor_id"] for f in assessment["evaluated_factors"]]
    assert "KHASRA_MISMATCH" in factor_ids
    assert "AREA_DIVERGENCE_HIGH" in factor_ids
    assert "ACTIVE_COURT_DISPUTE" in factor_ids
    assert "ACTIVE_BANK_MORTGAGE" in factor_ids


def test_risk_assessment_empty_documents():
    """Verify proper handling when no documents are provided."""
    assessment = LandRiskAssessmentEngine.evaluate_risk(documents=[])
    assert assessment["risk_level_code"] == "INSUFFICIENT_DATA"
    assert assessment["is_sufficient_evidence"] is False
    assert len(assessment["information_gaps"]) >= 1


# =============================================================================
# 3. ADMINISTRATIVE DELAY ANALYTICS TESTS
# =============================================================================

def test_administrative_delay_analytics_metrics():
    """Verify deterministic metrics calculation across synthetic workflow dataset."""
    records = generate_synthetic_workflow_records()
    assert len(records) >= 20

    metrics = DelayAnalyticsEngine.calculate_metrics(records)
    summary = metrics["summary"]

    assert summary["total_applications"] == len(records)
    assert summary["completed_applications"] > 0
    assert summary["pending_applications"] > 0
    assert summary["avg_completion_days"] > 0
    assert summary["median_completion_days"] > 0
    assert summary["sla_breached_count"] >= 1
    assert summary["sla_breach_rate_pct"] > 0

    # Verify stage breakdown has all 5 stages
    assert len(metrics["stages"]) == 5
    # Verify bottleneck rules caught at least one bottleneck
    assert len(metrics["bottlenecks"]) >= 1


def test_administrative_delay_filtering():
    """Verify analytics filters operate correctly."""
    records = generate_synthetic_workflow_records()

    # Filter by status: APPROVED
    approved_metrics = DelayAnalyticsEngine.calculate_metrics(records, filter_status="APPROVED")
    assert approved_metrics["summary"]["pending_applications"] == 0
    assert approved_metrics["summary"]["completed_applications"] == approved_metrics["summary"]["total_applications"]

    # Filter by application type
    sale_metrics = DelayAnalyticsEngine.calculate_metrics(records, filter_type="SALE_DEED_MUTATION")
    assert sale_metrics["summary"]["total_applications"] > 0
    for r in sale_metrics["records"]:
        assert r["application_type"] == "SALE_DEED_MUTATION"


# =============================================================================
# 4. API ENDPOINTS INTEGRATION TESTS
# =============================================================================

def test_api_document_presets():
    """GET /api/ai/documents/presets returns pre-configured scenarios."""
    res = client.get("/api/ai/documents/presets")
    assert res.status_code == 200
    presets = res.json()
    assert len(presets) >= 3
    assert presets[0]["id"] == "scenario_consistent"


def test_api_document_compare_endpoint():
    """POST /api/ai/documents/compare compares documents and returns grounded explanation."""
    presets = get_sample_document_presets()
    payload = {
        "doc1": presets[0]["doc1"],
        "doc2": presets[0]["doc2"]
    }
    res = client.post("/api/ai/documents/compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "overall_consistent" in data
    assert "explanation" in data
    assert "explanation_text" in data["explanation"]
    assert data["explanation"]["is_ai_generated"] in (True, False)


def test_api_risk_assessment_endpoint():
    """POST /api/ai/risk-assessment evaluates submitted documents and returns factors."""
    presets = get_sample_document_presets()
    payload = {
        "documents": [presets[1]["doc1"], presets[1]["doc2"]],
        "discrepancies": []
    }
    res = client.post("/api/ai/risk-assessment", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "risk_score" in data
    assert "risk_category" in data
    assert "evaluated_factors" in data
    assert "recommended_actions" in data
    assert "explanation" in data


def test_api_parcel_risk_assessment_endpoint():
    """GET /api/ai/risk-assessment/parcel/{parcel_id} evaluates risk for a DB parcel."""
    res = client.get("/api/ai/risk-assessment/parcel/UP-GZB-IND-00012345")
    assert res.status_code == 200
    data = res.json()
    assert data["risk_score"] >= 0
    assert "evaluated_factors" in data
    assert "parcel_details" in data


def test_api_delay_analytics_endpoint():
    """GET /api/analytics/administrative-delays returns metrics, bottlenecks, and insights."""
    res = client.get("/api/analytics/administrative-delays")
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "stages" in data
    assert "bottlenecks" in data
    assert "ai_insights" in data
    assert "data_source_label" in data


def test_api_delay_cases_endpoint():
    """GET /api/analytics/administrative-delays/cases returns workflow records."""
    res = client.get("/api/analytics/administrative-delays/cases?status=UNDER_REVIEW")
    assert res.status_code == 200
    cases = res.json()
    assert isinstance(cases, list)
    for c in cases:
        assert c["status"] == "UNDER_REVIEW"


# =============================================================================
# 5. ADDITIONAL EDGE CASE & RESILIENCE TESTS
# =============================================================================

def test_empty_document_upload_rejection():
    """Verify empty file upload is rejected with HTTP 400."""
    res = client.post(
        "/api/ai/documents/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")}
    )
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


def test_unsupported_file_type_handling():
    """Verify unparseable or unsupported file extensions report proper status."""
    res = client.post(
        "/api/ai/documents/upload",
        files={"file": ("malicious.exe", b"MZ_binary_content_here", "application/x-dosexec")}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "UNSUPPORTED_FORMAT"
    assert len(data["warnings"]) >= 1


def test_deterministic_scoring_reproducibility():
    """Verify same inputs deterministically produce identical risk score."""
    presets = get_sample_document_presets()
    docs = [presets[1]["doc1"], presets[1]["doc2"]]
    comp = DiscrepancyComparisonEngine.compare_documents(docs[0], docs[1])

    score1 = LandRiskAssessmentEngine.evaluate_risk(documents=docs, discrepancies=comp["discrepancies"])
    score2 = LandRiskAssessmentEngine.evaluate_risk(documents=docs, discrepancies=comp["discrepancies"])

    assert score1["risk_score"] == score2["risk_score"]
    assert score1["risk_category"] == score2["risk_category"]
    assert score1["completeness_percentage"] == score2["completeness_percentage"]


def test_empty_delay_dataset_handling():
    """Verify DelayAnalyticsEngine handles 0 records gracefully without ZeroDivisionError."""
    res = DelayAnalyticsEngine.calculate_metrics([])
    assert res["summary"]["total_applications"] == 0
    assert res["summary"]["avg_completion_days"] == 0.0
    assert res["summary"]["median_completion_days"] == 0.0
    assert res["summary"]["sla_breach_rate_pct"] == 0.0


def test_llm_fallback_narrative_generation():
    """Verify AIService produces comprehensive text when LLM key is absent."""
    presets = get_sample_document_presets()
    comp = DiscrepancyComparisonEngine.compare_documents(presets[1]["doc1"], presets[1]["doc2"])

    explanation = AIService.generate_discrepancy_explanation(
        documents_summary=[{"title": "Doc A"}, {"title": "Doc B"}],
        discrepancies=comp["discrepancies"],
        overall_consistent=False
    )
    assert "explanation_text" in explanation
    assert len(explanation["explanation_text"]) > 50
    assert explanation["is_ai_generated"] in (True, False)

