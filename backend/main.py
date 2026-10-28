import datetime
import json
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).resolve().parent / ".env")
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Query, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db, engine, Base
from models import (
    User, Parcel, OwnershipHistory, Application, ApplicationStage,
    Document, AuditEvent, LedgerBlock
)
from schemas import (
    UserOut, ParcelPublicOut, ParcelDetail, OwnershipHistoryOut,
    DocumentOut, ApplicationSummary, ApplicationDetail,
    ApplicationCreateRequest, OfficerActionRequest,
    CitizenCorrectionRequest, CitizenAppealRequest,
    PropertyListingToggleRequest, AuditEventOut,
    LedgerBlockOut, TamperSimulateRequest, OfficerDashboardStats,
    DocumentCompareRequest, RiskAssessmentRequest
)
import crud
from ledger import BhulekhLedgerEngine, calculate_sha256
from sla_engine import evaluate_and_update_application_slas, calculate_sla_status, STAGE_SLA_CONFIG, REJECTION_CATEGORIES
import seed_data

from ai_service import AIService, get_configured_provider
from document_verification import (
    DocumentExtractionEngine, DiscrepancyComparisonEngine, get_sample_document_presets
)
from risk_assessment import LandRiskAssessmentEngine
from delay_analytics import DelayAnalyticsEngine, generate_synthetic_workflow_records


app = FastAPI(
    title="BHULEKH LEDGER API",
    description="Statutory Digital Land Governance & Sovereign Cryptographic Ownership Infrastructure",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    db = next(get_db())
    try:
        evaluate_and_update_application_slas(db)
    finally:
        db.close()

@app.get("/api/health")
def health_check():
    return {
        "status": "OPERATIONAL",
        "service": "Bhulekh Ledger National Infrastructure",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "jurisdiction": "Republic of India",
        "ledger_engine": "Permissioned SHA-256 / Merkle Multi-Sign Engine"
    }

# ==================== USERS & RBAC ====================

@app.get("/api/users", response_model=List[UserOut])
def get_all_users(role: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.all()

@app.get("/api/users/{user_id}", response_model=UserOut)
def get_user_by_id(user_id: str, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return u

# ==================== PARCELS & GIS ====================

def map_parcel_public(p: Parcel) -> Dict[str, Any]:
    # Circle rate valuation in Lakhs
    estimated_lakhs = round((p.area_sqft * p.circle_rate_sqft_2026) / 100000.0, 2)
    formatted_val = crud.format_indian_currency(estimated_lakhs)
    
    return {
        "id": p.id,
        "ulin_pin": p.ulin_pin,
        "state": p.state,
        "revenue_authority": p.revenue_authority,
        "district": p.district,
        "tehsil": p.tehsil,
        "village": p.village,
        "khasra_no": p.khasra_no,
        "khata_no": p.khata_no,
        "land_use": p.land_use,
        "area_sqft": p.area_sqft,
        "area_sqm": p.area_sqm,
        "area_local_unit": p.area_local_unit,
        "circle_rate_sqft_2026": p.circle_rate_sqft_2026,
        "circle_rate_2026": p.circle_rate_2026,
        "circle_rate_2025": p.circle_rate_2025,
        "circle_rate_2024": p.circle_rate_2024,
        "estimated_govt_value_lakhs": estimated_lakhs,
        "formatted_value_str": formatted_val,
        "current_owner_id": p.current_owner_id,
        "current_owner_name": p.current_owner_name,
        "ownership_status": "Statutorily Verified" if not p.is_disputed else "Dispute / Injunction Flagged",
        "is_for_sale": p.is_for_sale,
        "listing_price_lakhs": p.listing_price_lakhs,
        "is_disputed": p.is_disputed,
        "is_mortgaged": p.is_mortgaged,
        "tax_cleared": p.tax_cleared,
        "boundary_verified": p.boundary_verified,
        "risk_rating": p.risk_rating,
        "centroid_lat": p.centroid_lat,
        "centroid_lng": p.centroid_lng,
        "geometry_geojson": p.geometry_geojson
    }

def map_parcel_detail(p: Parcel) -> Dict[str, Any]:
    base = map_parcel_public(p)
    base.update({
        "current_owner_id": p.current_owner_id,
        "current_owner_name": p.current_owner_name,
        "dispute_case_no": p.dispute_case_no,
        "dispute_details": p.dispute_details,
        "mortgage_bank": p.mortgage_bank,
        "mortgage_amount_lakhs": p.mortgage_amount_lakhs,
        "ownership_history": p.ownership_history,
        "documents": p.documents
    })
    return base

@app.get("/api/parcels", response_model=List[ParcelPublicOut])
def list_parcels(
    state: Optional[str] = None,
    district: Optional[str] = None,
    tehsil: Optional[str] = None,
    village: Optional[str] = None,
    land_use: Optional[str] = None,
    is_for_sale: Optional[bool] = None,
    is_disputed: Optional[bool] = None,
    search: Optional[str] = None,
    owner_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    parcels = crud.get_parcels(
        db=db,
        state=state,
        district=district,
        tehsil=tehsil,
        village=village,
        land_use=land_use,
        is_for_sale=is_for_sale,
        is_disputed=is_disputed,
        search=search,
        owner_id=owner_id
    )
    return [map_parcel_public(p) for p in parcels]

@app.get("/api/parcels/{parcel_id}", response_model=ParcelDetail)
def get_parcel_detail(parcel_id: str, db: Session = Depends(get_db)):
    p = crud.get_parcel_by_id(db, parcel_id)
    if not p:
        raise HTTPException(status_code=404, detail="Parcel record not found")
    return map_parcel_detail(p)

@app.post("/api/parcels/{parcel_id}/toggle-listing")
def toggle_listing(
    parcel_id: str,
    req: PropertyListingToggleRequest,
    actor_name: str = Query("Citizen Landowner"),
    db: Session = Depends(get_db)
):
    p = crud.toggle_property_listing(db, parcel_id, req, actor_name)
    if not p:
        raise HTTPException(status_code=404, detail="Parcel not found")
    return {
        "message": "Listing status updated successfully",
        "is_for_sale": p.is_for_sale,
        "listing_price_lakhs": p.listing_price_lakhs,
        "formatted_price": crud.format_indian_currency(p.listing_price_lakhs or 0)
    }

# ==================== APPLICATIONS & WORKFLOW ====================

def enrich_stage(s: ApplicationStage) -> Dict[str, Any]:
    sla_info = calculate_sla_status(s.deadline_at, s.completed_at)
    return {
        "id": s.id,
        "stage_order": s.stage_order,
        "stage_name": s.stage_name,
        "department": s.department,
        "assigned_role": s.assigned_role,
        "assigned_officer_id": s.assigned_officer_id,
        "assigned_officer_name": s.assigned_officer_name,
        "status": s.status,
        "sla_days": s.sla_days,
        "assigned_at": s.assigned_at,
        "deadline_at": s.deadline_at,
        "completed_at": s.completed_at,
        "officer_remarks": s.officer_remarks,
        "digital_signature": s.digital_signature,
        "time_remaining_str": sla_info["time_remaining_str"],
        "is_breached": sla_info["is_breached"]
    }

def enrich_application(app: Application) -> Dict[str, Any]:
    enriched_stages = [enrich_stage(s) for s in app.stages]
    return {
        "id": app.id,
        "parcel_id": app.parcel_id,
        "applicant_id": app.applicant_id,
        "applicant_name": app.applicant.full_name if app.applicant else "Citizen",
        "buyer_name": app.buyer_name,
        "buyer_masked_aadhaar": app.buyer_masked_aadhaar,
        "buyer_phone_masked": app.buyer_phone_masked,
        "transfer_type": app.transfer_type,
        "declared_value_lakhs": app.declared_value_lakhs,
        "formatted_declared_value": crud.format_indian_currency(app.declared_value_lakhs),
        "stamp_duty_paid_lakhs": app.stamp_duty_paid_lakhs,
        "current_stage_index": app.current_stage_index,
        "status": app.status,
        "created_at": app.created_at,
        "sla_deadline": app.sla_deadline,
        "is_sla_breached": app.is_sla_breached,
        "supervisor_notified": app.supervisor_notified,
        "delay_explanation": app.delay_explanation,
        "rejection_category": app.rejection_category,
        "rejection_remarks": app.rejection_remarks,
        "rejection_officer_name": app.rejection_officer_name,
        "rejection_department": app.rejection_department,
        "rejected_at": app.rejected_at,
        "is_appealed": app.is_appealed,
        "appeal_remarks": app.appeal_remarks,
        "appealed_at": app.appealed_at,
        "appeal_status": app.appeal_status,
        "final_ledger_block_index": app.final_ledger_block_index,
        "final_ledger_tx_hash": app.final_ledger_tx_hash,
        "parcel_district": app.parcel.district if app.parcel else None,
        "parcel_village": app.parcel.village if app.parcel else None,
        "parcel": map_parcel_detail(app.parcel) if app.parcel else None,
        "stages": enriched_stages,
        "documents": app.documents
    }

@app.get("/api/applications", response_model=List[ApplicationSummary])
def list_applications(
    applicant_id: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    is_breached: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    evaluate_and_update_application_slas(db)
    query = db.query(Application)
    if applicant_id:
        query = query.filter(Application.applicant_id == applicant_id)
    if status:
        query = query.filter(Application.status == status)
    if is_breached is not None:
        query = query.filter(Application.is_sla_breached == is_breached)
    
    apps = query.order_by(desc(Application.created_at)).all()
    
    if role and role not in ["CITIZEN", "ADMIN", "SDM_APPROVER"]:
        filtered = []
        for a in apps:
            curr_stage = next((s for s in a.stages if s.stage_order == a.current_stage_index), None)
            if curr_stage and curr_stage.assigned_role == role:
                filtered.append(a)
        apps = filtered

    return [enrich_application(a) for a in apps]

@app.get("/api/applications/{application_id}", response_model=ApplicationDetail)
def get_application_detail(application_id: str, db: Session = Depends(get_db)):
    evaluate_and_update_application_slas(db)
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return enrich_application(app)

@app.post("/api/applications", response_model=ApplicationDetail)
def submit_new_application(
    req: ApplicationCreateRequest,
    applicant_id: str = Query("usr_citizen_1"),
    db: Session = Depends(get_db)
):
    try:
        app = crud.create_application(db, applicant_id, req)
        return enrich_application(app)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/applications/{application_id}/officer-action", response_model=ApplicationDetail)
def officer_action(
    application_id: str,
    req: OfficerActionRequest,
    db: Session = Depends(get_db)
):
    try:
        app = crud.process_officer_action(db, application_id, req)
        return enrich_application(app)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/applications/{application_id}/citizen-correction", response_model=ApplicationDetail)
def citizen_correction(
    application_id: str,
    req: CitizenCorrectionRequest,
    actor_name: str = Query("Rajesh Kumar Sharma"),
    db: Session = Depends(get_db)
):
    try:
        app = crud.submit_citizen_correction(db, application_id, req, actor_name)
        return enrich_application(app)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/applications/{application_id}/citizen-appeal", response_model=ApplicationDetail)
def citizen_appeal(
    application_id: str,
    req: CitizenAppealRequest,
    actor_name: str = Query("Rajesh Kumar Sharma"),
    db: Session = Depends(get_db)
):
    try:
        app = crud.submit_citizen_appeal(db, application_id, req, actor_name)
        return enrich_application(app)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== BLOCKCHAIN LEDGER & AUDIT TRAIL ====================

@app.get("/api/ledger/blocks", response_model=List[LedgerBlockOut])
def get_ledger_blocks(parcel_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(LedgerBlock)
    if parcel_id:
        query = query.filter(LedgerBlock.parcel_id == parcel_id)
    return query.order_by(LedgerBlock.block_index).all()

@app.get("/api/ledger/verify-chain")
def verify_ledger_integrity(db: Session = Depends(get_db)):
    blocks = db.query(LedgerBlock).order_by(LedgerBlock.block_index).all()
    result = BhulekhLedgerEngine.verify_ledger_chain(blocks)
    return result

@app.post("/api/ledger/simulate-tamper")
def simulate_ledger_tamper(req: TamperSimulateRequest, db: Session = Depends(get_db)):
    block = db.query(LedgerBlock).filter(LedgerBlock.block_index == req.block_index).first()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    
    try:
        data = json.loads(block.payload_json)
    except Exception:
        data = {"tampered": True}
    
    data[req.tampered_payload_field] = req.fraudulent_value
    block.payload_json = json.dumps(data)
    db.commit()

    audit = AuditEvent(
        entity_type="LEDGER",
        entity_id=f"BLOCK_#{req.block_index}",
        actor_name="Security Research / Chaos Engine",
        actor_role="TEST_AUDITOR",
        action="TAMPER_SIMULATION_INJECTED",
        details=f"Injected fraudulent payload into Block #{req.block_index}. Changed '{req.tampered_payload_field}' to '{req.fraudulent_value}'."
    )
    db.add(audit)
    db.commit()

    blocks = db.query(LedgerBlock).order_by(LedgerBlock.block_index).all()
    verification = BhulekhLedgerEngine.verify_ledger_chain(blocks)

    return {
        "message": "Tamper simulation executed! Verify how the cryptographic consensus flagged the fraud.",
        "tampered_block_index": req.block_index,
        "verification_result": verification
    }

@app.post("/api/ledger/reset-tamper")
def reset_tamper_demo():
    seed_data.seed_database()
    return {"message": "Database and ledger reset to pristine verified state!"}

@app.get("/api/audit-events", response_model=List[AuditEventOut])
def get_audit_events(
    entity_id: Optional[str] = None,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(AuditEvent)
    if entity_id:
        query = query.filter(AuditEvent.entity_id == entity_id)
    return query.order_by(desc(AuditEvent.timestamp)).limit(limit).all()

# ==================== DASHBOARD STATS ====================

@app.get("/api/stats/officer-dashboard", response_model=OfficerDashboardStats)
def get_officer_dashboard_stats(role: Optional[str] = None, db: Session = Depends(get_db)):
    evaluate_and_update_application_slas(db)
    
    total = db.query(Application).count()
    pending = db.query(Application).filter(Application.status.in_(["SUBMITTED", "UNDER_REVIEW", "CORRECTION_REQUESTED"])).count()
    approved = db.query(Application).filter(Application.status == "APPROVED").count()
    rejected = db.query(Application).filter(Application.status == "REJECTED").count()
    sla_breached = db.query(Application).filter(Application.is_sla_breached == True).count()
    appeals = db.query(Application).filter(Application.is_appealed == True).count()
    disputed = db.query(Parcel).filter(Parcel.is_disputed == True).count()

    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    approaching = 0
    active_stages = db.query(ApplicationStage).filter(ApplicationStage.status.in_(["PENDING", "IN_PROGRESS"])).all()
    for s in active_stages:
        if s.deadline_at > now and (s.deadline_at - now).total_seconds() < 86400:
            approaching += 1

    return {
        "total_assigned": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "sla_approaching": approaching,
        "sla_breached": sla_breached,
        "appeals": appeals,
        "disputed_parcels": disputed
    }

@app.get("/api/stats/citizen-dashboard/{user_id}")
def get_citizen_dashboard_stats(user_id: str, db: Session = Depends(get_db)):
    owned_parcels = db.query(Parcel).filter(Parcel.current_owner_id == user_id).all()
    total_area_sqft = sum(p.area_sqft for p in owned_parcels)
    total_est_val = sum((p.area_sqft * p.circle_rate_sqft_2026) / 100000.0 for p in owned_parcels)
    active_apps = db.query(Application).filter(Application.applicant_id == user_id).all()

    return {
        "owned_parcels_count": len(owned_parcels),
        "total_land_area_sqft": total_area_sqft,
        "total_estimated_value_lakhs": round(total_est_val, 2),
        "formatted_total_value": crud.format_indian_currency(total_est_val),
        "active_applications_count": len(active_apps),
        "parcels": [map_parcel_public(p) for p in owned_parcels]
    }

@app.get("/api/config/sla-rules")
def get_sla_rules():
    return {
        "stages": STAGE_SLA_CONFIG,
        "rejection_categories": REJECTION_CATEGORIES
    }

# ==================== TOOL 1: AI DOCUMENT VERIFICATION ====================

@app.get("/api/ai/documents/presets")
def get_document_presets():
    """Return pre-configured sample document comparison pairs for instant 1-click testing."""
    return get_sample_document_presets()

@app.post("/api/ai/documents/upload")
async def upload_and_extract_document(
    file: UploadFile = File(...),
    doc_type_hint: Optional[str] = Query(None)
):
    """
    Upload and parse land records (PDF, JPG, PNG).
    Extracts text, executes OCR if applicable, and extracts structured fields.
    """
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Max file size 15MB
    if len(file_bytes) > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds maximum permissible size (15MB).")

    extraction = DocumentExtractionEngine.extract_text_from_file(
        file_bytes=file_bytes,
        filename=file.filename or "document.pdf",
        content_type=file.content_type or "application/octet-stream"
    )

    structured_fields = DocumentExtractionEngine.extract_structured_fields(
        raw_text=extraction.get("raw_text", ""),
        filename=file.filename or "document.pdf"
    )

    if doc_type_hint:
        structured_fields["doc_type"] = doc_type_hint

    return {
        "title": file.filename or "Uploaded Document",
        "file_name": file.filename or "Uploaded Document",
        "doc_type": structured_fields.get("doc_type", "SALE_DEED"),
        "file_size_kb": extraction.get("file_size_kb", 0),
        "sha256_hash": extraction.get("sha256_hash", ""),
        "raw_text": extraction.get("raw_text", ""),
        "extraction_method": extraction.get("extraction_method"),
        "ocr_available": extraction.get("ocr_available", False),
        "status": extraction.get("status", "SUCCESS"),
        "warnings": extraction.get("warnings", []),
        "fields": structured_fields
    }

@app.post("/api/ai/documents/compare")
def compare_documents(req: DocumentCompareRequest):
    """
    Deterministically compare two land documents and generate grounded AI explanation.
    """
    comparison = DiscrepancyComparisonEngine.compare_documents(req.doc1, req.doc2)
    
    docs_summary = [
        {"title": req.doc1.get("title", "Document 1"), "fields": req.doc1.get("fields", {})},
        {"title": req.doc2.get("title", "Document 2"), "fields": req.doc2.get("fields", {})}
    ]

    explanation = AIService.generate_discrepancy_explanation(
        documents_summary=docs_summary,
        discrepancies=comparison.get("discrepancies", []),
        overall_consistent=comparison.get("overall_consistent", False)
    )

    comparison["explanation"] = explanation
    comparison["provider"] = get_configured_provider()
    return comparison


# ==================== TOOL 2: EVIDENCE-BASED LAND RISK ASSESSMENT ====================

@app.post("/api/ai/risk-assessment")
def perform_risk_assessment(req: RiskAssessmentRequest, db: Session = Depends(get_db)):
    """
    Perform transparent, evidence-based land risk assessment across submitted documents,
    discrepancies, and optional linked database parcel encumbrance data.
    """
    parcel_record = None
    if req.parcel_id:
        p = crud.get_parcel_by_id(db, req.parcel_id)
        if p:
            parcel_record = {
                "id": p.id,
                "ulin_pin": p.ulin_pin,
                "is_disputed": p.is_disputed,
                "dispute_case_no": p.dispute_case_no,
                "dispute_details": p.dispute_details,
                "is_mortgaged": p.is_mortgaged,
                "mortgage_bank": p.mortgage_bank,
                "mortgage_amount_lakhs": p.mortgage_amount_lakhs,
                "tax_cleared": p.tax_cleared,
                "boundary_verified": p.boundary_verified,
                "risk_rating": p.risk_rating
            }

    assessment = LandRiskAssessmentEngine.evaluate_risk(
        documents=req.documents,
        discrepancies=req.discrepancies,
        parcel_record=parcel_record,
        user_declared_data=req.user_declared_data
    )

    explanation = AIService.generate_risk_assessment_explanation(assessment)
    assessment["explanation"] = explanation
    assessment["provider"] = get_configured_provider()
    assessment["parcel_details"] = parcel_record
    return assessment

@app.get("/api/ai/risk-assessment/parcel/{parcel_id}")
def assess_parcel_risk(parcel_id: str, db: Session = Depends(get_db)):
    """
    1-click instant risk assessment for any parcel in the registry.
    """
    p = crud.get_parcel_by_id(db, parcel_id)
    if not p:
        raise HTTPException(status_code=404, detail="Parcel not found")

    parcel_record = {
        "id": p.id,
        "ulin_pin": p.ulin_pin,
        "is_disputed": p.is_disputed,
        "dispute_case_no": p.dispute_case_no,
        "dispute_details": p.dispute_details,
        "is_mortgaged": p.is_mortgaged,
        "mortgage_bank": p.mortgage_bank,
        "mortgage_amount_lakhs": p.mortgage_amount_lakhs,
        "tax_cleared": p.tax_cleared,
        "boundary_verified": p.boundary_verified,
        "risk_rating": p.risk_rating
    }

    # Synthesize document records from parcel
    mock_docs = [{
        "title": f"Official Cadastral Record ({p.ulin_pin})",
        "file_name": f"Cadastral_{p.ulin_pin}.pdf",
        "doc_type": "RECORD_OF_RIGHTS",
        "fields": {
            "doc_type": "RECORD_OF_RIGHTS",
            "document_ref_no": p.ulin_pin,
            "state": p.state,
            "district": p.district,
            "tehsil": p.tehsil,
            "village": p.village,
            "khasra_no": p.khasra_no,
            "khata_no": p.khata_no,
            "owner_names": [p.current_owner_name],
            "land_area": p.area_sqft,
            "area_unit": "SQFT",
            "normalized_area_sqft": p.area_sqft
        }
    }]

    assessment = LandRiskAssessmentEngine.evaluate_risk(
        documents=mock_docs,
        discrepancies=[],
        parcel_record=parcel_record
    )

    explanation = AIService.generate_risk_assessment_explanation(assessment)
    assessment["explanation"] = explanation
    assessment["provider"] = get_configured_provider()
    assessment["parcel_details"] = parcel_record
    return assessment


# ==================== TOOL 3: ADMINISTRATIVE DELAY ANALYTICS ====================

@app.get("/api/analytics/administrative-delays")
def get_administrative_delay_analytics(
    application_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Calculate deterministic administrative delay metrics, stage durations,
    and bottleneck stages across workflow records, backed by grounded AI insights.
    """
    db_apps = db.query(Application).all()
    records: List[Dict[str, Any]] = []

    for a in db_apps:
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        total_days = round((now - a.created_at).total_seconds() / 86400.0, 1)
        curr_stage = next((s for s in a.stages if s.stage_order == a.current_stage_index), None)

        st_records = []
        for s in a.stages:
            st_dur = 0
            if s.completed_at:
                st_dur = round((s.completed_at - s.assigned_at).total_seconds() / 86400.0, 1)
            elif s.assigned_at:
                st_dur = round((now - s.assigned_at).total_seconds() / 86400.0, 1)

            st_records.append({
                "stage_order": s.stage_order,
                "stage_name": s.stage_name,
                "department": s.department,
                "assigned_role": s.assigned_role,
                "status": s.status,
                "duration_days": st_dur,
                "sla_days": s.sla_days,
                "assigned_at": s.assigned_at.isoformat() + "Z" if s.assigned_at else None,
                "deadline_at": s.deadline_at.isoformat() + "Z" if s.deadline_at else None,
                "completed_at": s.completed_at.isoformat() + "Z" if s.completed_at else None,
                "is_breached": s.status == "SLA_BREACHED" or (s.deadline_at < now and s.status in ("PENDING", "IN_PROGRESS"))
            })

        records.append({
            "id": a.id,
            "application_type": a.transfer_type,
            "district": a.parcel.district if a.parcel else "Ghaziabad",
            "status": a.status,
            "created_at": a.created_at.isoformat() + "Z",
            "completed_at": a.updated_at.isoformat() + "Z" if a.status == "APPROVED" else None,
            "total_turnaround_days": total_days,
            "is_sla_breached": a.is_sla_breached,
            "sla_deadline": a.sla_deadline.isoformat() + "Z",
            "current_stage_index": a.current_stage_index,
            "current_stage_name": curr_stage.stage_name if curr_stage else "SDM Final Review",
            "current_department": curr_stage.department if curr_stage else "SDM Office",
            "rejection_ground": a.rejection_remarks,
            "rejection_department": a.rejection_department,
            "is_synthetic_demo": False,
            "stages": st_records
        })

    synthetic_records = generate_synthetic_workflow_records()
    all_combined = records + synthetic_records

    analytics = DelayAnalyticsEngine.calculate_metrics(
        applications=all_combined,
        filter_type=application_type,
        filter_status=status,
        filter_dept=department
    )

    insights = AIService.generate_delay_analytics_insights(analytics)
    analytics["ai_insights"] = insights
    analytics["provider"] = get_configured_provider()

    return analytics

@app.get("/api/analytics/administrative-delays/cases")
def get_delay_cases(
    status: Optional[str] = None,
    department: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Return individual application cases for drill-down investigation."""
    synthetic_records = generate_synthetic_workflow_records()
    if status and status != "ALL":
        synthetic_records = [r for r in synthetic_records if r.get("status") == status]
    if department and department != "ALL":
        synthetic_records = [r for r in synthetic_records if r.get("current_department") == department]
    return synthetic_records

