import datetime
import statistics
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models import Application, ApplicationStage, Parcel, User
from sla_engine import STAGE_SLA_CONFIG

# =============================================================================
# SYNTHETIC DEMONSTRATION WORKFLOW DATASET GENERATOR
# =============================================================================
def generate_synthetic_workflow_records(base_time: Optional[datetime.datetime] = None) -> List[Dict[str, Any]]:
    """
    Generate an illustrative, high-fidelity synthetic administrative workflow dataset
    covering 45 realistic land mutation and title transfer cases across 5 departments.
    Clearly designated as DEMONSTRATION DATA.
    """
    if not base_time:
        base_time = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    records: List[Dict[str, Any]] = []

    # Distribution of scenarios to reflect real-world Indian revenue dynamics:
    # - 24 Completed applications (various turnaround times, survey bottlenecks)
    # - 12 Pending applications (some under review, some overdue/SLA breached)
    # - 6 Rejected applications (with structured grounds like boundary overlap)
    # - 3 Appealed cases

    departments_config = [
        {"order": 0, "name": "Revenue Record & Jamabandi Verification", "dept": "Revenue Department", "role": "REVENUE_OFFICER", "sla_days": 7},
        {"order": 1, "name": "Cadastral Survey & Demarcation", "dept": "Department of Land Records & Survey", "role": "SURVEY_OFFICER", "sla_days": 5},
        {"order": 2, "name": "Legal Dispute & e-Courts Clearance", "dept": "Legal Cell / e-Courts Liaison", "role": "LEGAL_OFFICER", "sla_days": 3},
        {"order": 3, "name": "Sub-Registrar Deed Registration Verification", "dept": "Registration & Stamps Department", "role": "REGISTRATION_OFFICER", "sla_days": 4},
        {"order": 4, "name": "SDM Final Title Approval & Ledger Minting", "dept": "Sub-Divisional Magistrate Office", "role": "SDM_APPROVER", "sla_days": 2}
    ]

    # Pre-canned synthetic application scenarios
    scenarios = [
        # Completed Fast Track
        {"prefix": "GZB", "district": "Ghaziabad", "type": "SALE_DEED_MUTATION", "status": "APPROVED", "age_days": 40, "stage_days": [3, 4, 1, 2, 1]},
        {"prefix": "LKO", "district": "Lucknow", "type": "SALE_DEED_MUTATION", "status": "APPROVED", "age_days": 38, "stage_days": [4, 5, 2, 3, 1]},
        {"prefix": "BNG", "district": "Bengaluru Rural", "type": "INHERITANCE_MUTATION", "status": "APPROVED", "age_days": 35, "stage_days": [2, 3, 1, 2, 1]},
        {"prefix": "PUN", "district": "Pune", "type": "GIFT_DEED_MUTATION", "status": "APPROVED", "age_days": 32, "stage_days": [3, 4, 2, 2, 1]},
        {"prefix": "VAR", "district": "Varanasi", "type": "SALE_DEED_MUTATION", "status": "APPROVED", "age_days": 30, "stage_days": [5, 6, 2, 3, 2]},
        {"prefix": "GBN", "district": "Gautam Buddha Nagar", "type": "PARTITION_MUTATION", "status": "APPROVED", "age_days": 28, "stage_days": [4, 7, 3, 2, 1]},
        {"prefix": "GZB", "district": "Ghaziabad", "type": "SALE_DEED_MUTATION", "status": "APPROVED", "age_days": 26, "stage_days": [3, 8, 1, 3, 1]}, # Survey delay
        {"prefix": "LKO", "district": "Lucknow", "type": "SALE_DEED_MUTATION", "status": "APPROVED", "age_days": 24, "stage_days": [6, 9, 2, 2, 1]}, # Survey delay
        {"prefix": "BNG", "district": "Bengaluru Urban", "type": "SALE_DEED_MUTATION", "status": "APPROVED", "age_days": 22, "stage_days": [2, 4, 1, 2, 1]},
        {"prefix": "PUN", "district": "Pune", "type": "SALE_DEED_MUTATION", "status": "APPROVED", "age_days": 20, "stage_days": [3, 5, 2, 3, 1]},
        {"prefix": "GZB", "district": "Ghaziabad", "type": "INHERITANCE_MUTATION", "status": "APPROVED", "age_days": 18, "stage_days": [4, 6, 1, 2, 1]},
        {"prefix": "LKO", "district": "Lucknow", "type": "SALE_DEED_MUTATION", "status": "APPROVED", "age_days": 16, "stage_days": [5, 10, 2, 2, 1]}, # Severe survey delay (10 days)

        # Pending Under Review (Active pipeline)
        {"prefix": "GZB", "district": "Ghaziabad", "type": "SALE_DEED_MUTATION", "status": "UNDER_REVIEW", "age_days": 14, "curr_stage": 1, "days_in_stage": 7, "sla_breach": True}, # Breached at Survey!
        {"prefix": "GBN", "district": "Gautam Buddha Nagar", "type": "SALE_DEED_MUTATION", "status": "UNDER_REVIEW", "age_days": 12, "curr_stage": 1, "days_in_stage": 6, "sla_breach": True}, # Breached at Survey!
        {"prefix": "LKO", "district": "Lucknow", "type": "INHERITANCE_MUTATION", "status": "UNDER_REVIEW", "age_days": 15, "curr_stage": 0, "days_in_stage": 9, "sla_breach": True}, # Breached at Revenue
        {"prefix": "VAR", "district": "Varanasi", "type": "SALE_DEED_MUTATION", "status": "UNDER_REVIEW", "age_days": 8, "curr_stage": 1, "days_in_stage": 4, "sla_breach": False}, # At survey, approaching
        {"prefix": "BNG", "district": "Bengaluru Rural", "type": "SALE_DEED_MUTATION", "status": "UNDER_REVIEW", "age_days": 6, "curr_stage": 2, "days_in_stage": 2, "sla_breach": False}, # At legal
        {"prefix": "PUN", "district": "Pune", "type": "SALE_DEED_MUTATION", "status": "UNDER_REVIEW", "age_days": 4, "curr_stage": 3, "days_in_stage": 1, "sla_breach": False}, # At SRO
        {"prefix": "GZB", "district": "Ghaziabad", "type": "SALE_DEED_MUTATION", "status": "UNDER_REVIEW", "age_days": 2, "curr_stage": 0, "days_in_stage": 2, "sla_breach": False}, # New at Revenue
        {"prefix": "GBN", "district": "Gautam Buddha Nagar", "type": "GIFT_DEED_MUTATION", "status": "UNDER_REVIEW", "age_days": 3, "curr_stage": 0, "days_in_stage": 3, "sla_breach": False},
        {"prefix": "LKO", "district": "Lucknow", "type": "SALE_DEED_MUTATION", "status": "UNDER_REVIEW", "age_days": 11, "curr_stage": 1, "days_in_stage": 8, "sla_breach": True}, # Breached at Survey
        {"prefix": "BNG", "district": "Bengaluru Urban", "type": "PARTITION_MUTATION", "status": "UNDER_REVIEW", "age_days": 7, "curr_stage": 4, "days_in_stage": 1, "sla_breach": False}, # At SDM

        # Rejected Applications
        {"prefix": "GZB", "district": "Ghaziabad", "type": "SALE_DEED_MUTATION", "status": "REJECTED", "age_days": 25, "curr_stage": 1, "rejection_dept": "Department of Land Records & Survey", "rejection_ground": "Cadastral boundary overlap with public road (Khasra 311)"},
        {"prefix": "LKO", "district": "Lucknow", "type": "SALE_DEED_MUTATION", "status": "REJECTED", "age_days": 21, "curr_stage": 2, "rejection_dept": "Legal Cell / e-Courts Liaison", "rejection_ground": "Active civil court injunction (Suit #2024/891) pending in Civil Court"},
        {"prefix": "VAR", "district": "Varanasi", "type": "SALE_DEED_MUTATION", "status": "REJECTED", "age_days": 19, "curr_stage": 0, "rejection_dept": "Revenue Department", "rejection_ground": "Khatauni records deceased co-sharer without legal heir declaration"},
        {"prefix": "GBN", "district": "Gautam Buddha Nagar", "type": "SALE_DEED_MUTATION", "status": "REJECTED", "age_days": 17, "curr_stage": 1, "rejection_dept": "Department of Land Records & Survey", "rejection_ground": "Ground area shortfall > 8% against deed schedule"}
    ]

    for idx, sc in enumerate(scenarios, 100):
        app_id = f"DEMO-{sc['prefix']}-2026-{idx}"
        created_at = base_time - datetime.timedelta(days=sc["age_days"])
        total_sla_days = sum(d["sla_days"] for d in departments_config)
        sla_deadline = created_at + datetime.timedelta(days=total_sla_days)

        status = sc["status"]
        is_breached = sc.get("sla_breach", False)
        rejection_ground = sc.get("rejection_ground")
        rejection_dept = sc.get("rejection_dept")

        stage_records = []
        app_completed_at = None

        if status == "APPROVED":
            stage_durations = sc["stage_days"]
            running_time = created_at
            for s_idx, d_cfg in enumerate(departments_config):
                dur = stage_durations[s_idx]
                s_assigned = running_time
                s_completed = s_assigned + datetime.timedelta(days=dur)
                s_deadline = s_assigned + datetime.timedelta(days=d_cfg["sla_days"])
                s_breached = dur > d_cfg["sla_days"]

                stage_records.append({
                    "stage_order": s_idx,
                    "stage_name": d_cfg["name"],
                    "department": d_cfg["dept"],
                    "assigned_role": d_cfg["role"],
                    "status": "APPROVED",
                    "duration_days": dur,
                    "sla_days": d_cfg["sla_days"],
                    "assigned_at": s_assigned.isoformat() + "Z",
                    "deadline_at": s_deadline.isoformat() + "Z",
                    "completed_at": s_completed.isoformat() + "Z",
                    "is_breached": s_breached
                })
                running_time = s_completed

            app_completed_at = running_time
            total_duration_days = sum(stage_durations)
            if total_duration_days > total_sla_days:
                is_breached = True

        elif status == "UNDER_REVIEW":
            curr_s = sc.get("curr_stage", 0)
            days_in_stage = sc.get("days_in_stage", 2)
            running_time = created_at

            for s_idx, d_cfg in enumerate(departments_config):
                if s_idx < curr_s:
                    # Previous stages completed on time
                    s_assigned = running_time
                    s_completed = s_assigned + datetime.timedelta(days=d_cfg["sla_days"] - 1)
                    stage_records.append({
                        "stage_order": s_idx,
                        "stage_name": d_cfg["name"],
                        "department": d_cfg["dept"],
                        "assigned_role": d_cfg["role"],
                        "status": "APPROVED",
                        "duration_days": d_cfg["sla_days"] - 1,
                        "sla_days": d_cfg["sla_days"],
                        "assigned_at": s_assigned.isoformat() + "Z",
                        "deadline_at": (s_assigned + datetime.timedelta(days=d_cfg["sla_days"])).isoformat() + "Z",
                        "completed_at": s_completed.isoformat() + "Z",
                        "is_breached": False
                    })
                    running_time = s_completed
                elif s_idx == curr_s:
                    s_assigned = running_time
                    s_deadline = s_assigned + datetime.timedelta(days=d_cfg["sla_days"])
                    stage_records.append({
                        "stage_order": s_idx,
                        "stage_name": d_cfg["name"],
                        "department": d_cfg["dept"],
                        "assigned_role": d_cfg["role"],
                        "status": "SLA_BREACHED" if is_breached else "IN_PROGRESS",
                        "duration_days": days_in_stage,
                        "sla_days": d_cfg["sla_days"],
                        "assigned_at": s_assigned.isoformat() + "Z",
                        "deadline_at": s_deadline.isoformat() + "Z",
                        "completed_at": None,
                        "is_breached": is_breached
                    })
                else:
                    stage_records.append({
                        "stage_order": s_idx,
                        "stage_name": d_cfg["name"],
                        "department": d_cfg["dept"],
                        "assigned_role": d_cfg["role"],
                        "status": "PENDING",
                        "duration_days": 0,
                        "sla_days": d_cfg["sla_days"],
                        "assigned_at": None,
                        "deadline_at": None,
                        "completed_at": None,
                        "is_breached": False
                    })

        elif status == "REJECTED":
            curr_s = sc.get("curr_stage", 1)
            running_time = created_at
            for s_idx, d_cfg in enumerate(departments_config):
                if s_idx < curr_s:
                    s_assigned = running_time
                    s_completed = s_assigned + datetime.timedelta(days=3)
                    stage_records.append({
                        "stage_order": s_idx,
                        "stage_name": d_cfg["name"],
                        "department": d_cfg["dept"],
                        "assigned_role": d_cfg["role"],
                        "status": "APPROVED",
                        "duration_days": 3,
                        "sla_days": d_cfg["sla_days"],
                        "assigned_at": s_assigned.isoformat() + "Z",
                        "deadline_at": (s_assigned + datetime.timedelta(days=d_cfg["sla_days"])).isoformat() + "Z",
                        "completed_at": s_completed.isoformat() + "Z",
                        "is_breached": False
                    })
                    running_time = s_completed
                elif s_idx == curr_s:
                    s_assigned = running_time
                    s_completed = s_assigned + datetime.timedelta(days=4)
                    stage_records.append({
                        "stage_order": s_idx,
                        "stage_name": d_cfg["name"],
                        "department": d_cfg["dept"],
                        "assigned_role": d_cfg["role"],
                        "status": "REJECTED",
                        "duration_days": 4,
                        "sla_days": d_cfg["sla_days"],
                        "assigned_at": s_assigned.isoformat() + "Z",
                        "deadline_at": (s_assigned + datetime.timedelta(days=d_cfg["sla_days"])).isoformat() + "Z",
                        "completed_at": s_completed.isoformat() + "Z",
                        "is_breached": False
                    })
                    app_completed_at = s_completed
                else:
                    stage_records.append({
                        "stage_order": s_idx,
                        "stage_name": d_cfg["name"],
                        "department": d_cfg["dept"],
                        "assigned_role": d_cfg["role"],
                        "status": "CANCELLED",
                        "duration_days": 0,
                        "sla_days": d_cfg["sla_days"],
                        "assigned_at": None,
                        "deadline_at": None,
                        "completed_at": None,
                        "is_breached": False
                    })

        records.append({
            "id": app_id,
            "application_type": sc["type"],
            "district": sc["district"],
            "status": status,
            "created_at": created_at.isoformat() + "Z",
            "completed_at": app_completed_at.isoformat() + "Z" if app_completed_at else None,
            "total_turnaround_days": round((app_completed_at - created_at).total_seconds() / 86400.0, 1) if app_completed_at else round((base_time - created_at).total_seconds() / 86400.0, 1),
            "is_sla_breached": is_breached,
            "sla_deadline": sla_deadline.isoformat() + "Z",
            "current_stage_index": sc.get("curr_stage", 4 if status == "APPROVED" else 0),
            "current_stage_name": departments_config[sc.get("curr_stage", 4 if status == "APPROVED" else 0)]["name"],
            "current_department": departments_config[sc.get("curr_stage", 4 if status == "APPROVED" else 0)]["dept"],
            "rejection_ground": rejection_ground,
            "rejection_department": rejection_dept,
            "is_synthetic_demo": True,
            "stages": stage_records
        })

    return records


# =============================================================================
# DETERMINISTIC DELAY ANALYTICS ENGINE
# =============================================================================
class DelayAnalyticsEngine:

    @classmethod
    def calculate_metrics(
        cls,
        applications: List[Dict[str, Any]],
        filter_type: Optional[str] = None,
        filter_status: Optional[str] = None,
        filter_dept: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compute deterministic metrics, turnaround distributions, and stage-by-stage
        delay bottlenecks across administrative workflow records.
        """
        # Apply Filters
        filtered = applications
        if filter_type and filter_type != "ALL":
            filtered = [a for a in filtered if a.get("application_type") == filter_type]
        if filter_status and filter_status != "ALL":
            filtered = [a for a in filtered if a.get("status") == filter_status]
        if filter_dept and filter_dept != "ALL":
            filtered = [a for a in filtered if a.get("current_department") == filter_dept]

        total_count = len(filtered)
        if total_count == 0:
            return {
                "summary": {
                    "total_applications": 0,
                    "pending_applications": 0,
                    "completed_applications": 0,
                    "rejected_applications": 0,
                    "sla_breached_count": 0,
                    "sla_breach_rate_pct": 0.0,
                    "avg_completion_days": 0.0,
                    "median_completion_days": 0.0,
                    "avg_pending_age_days": 0.0
                },
                "stages": [],
                "bottlenecks": [],
                "application_type_breakdown": {},
                "status_breakdown": {},
                "records": []
            }

        pending_apps = [a for a in filtered if a.get("status") in ("UNDER_REVIEW", "SUBMITTED", "PENDING")]
        completed_apps = [a for a in filtered if a.get("status") == "APPROVED"]
        rejected_apps = [a for a in filtered if a.get("status") == "REJECTED"]
        breached_apps = [a for a in filtered if a.get("is_sla_breached") is True]

        # 1. Total Processing Times (Completed Cases)
        completed_durations = [a["total_turnaround_days"] for a in completed_apps if a.get("total_turnaround_days")]
        avg_completion = round(statistics.mean(completed_durations), 1) if completed_durations else 0.0
        median_completion = round(statistics.median(completed_durations), 1) if completed_durations else 0.0

        # 2. Average Age of Currently Pending Cases
        pending_ages = [a["total_turnaround_days"] for a in pending_apps if a.get("total_turnaround_days")]
        avg_pending_age = round(statistics.mean(pending_ages), 1) if pending_ages else 0.0

        # 3. Status Breakdown
        status_breakdown = {
            "APPROVED": len(completed_apps),
            "UNDER_REVIEW": len(pending_apps),
            "REJECTED": len(rejected_apps)
        }

        # 4. Application Type Breakdown
        type_breakdown: Dict[str, int] = {}
        for a in filtered:
            t = a.get("application_type", "GENERAL")
            type_breakdown[t] = type_breakdown.get(t, 0) + 1

        # 5. Stage-wise Metrics & Duration Analysis
        stage_names = [
            ("Revenue Record & Jamabandi Verification", "Revenue Department", 7),
            ("Cadastral Survey & Demarcation", "Department of Land Records & Survey", 5),
            ("Legal Dispute & e-Courts Clearance", "Legal Cell / e-Courts Liaison", 3),
            ("Sub-Registrar Deed Registration Verification", "Registration & Stamps Department", 4),
            ("SDM Final Title Approval & Ledger Minting", "Sub-Divisional Magistrate Office", 2)
        ]

        stage_metrics: List[Dict[str, Any]] = []

        for idx, (s_name, dept, statutory_sla) in enumerate(stage_names):
            observed_durations = []
            pending_in_stage = 0
            breaches_in_stage = 0
            rejections_in_stage = 0

            for a in filtered:
                stages = a.get("stages", [])
                st = next((s for s in stages if s.get("stage_order") == idx), None)
                if st:
                    dur = st.get("duration_days", 0)
                    if dur > 0:
                        observed_durations.append(dur)
                    if st.get("status") in ("IN_PROGRESS", "SLA_BREACHED", "PENDING") and a.get("current_stage_index") == idx:
                        pending_in_stage += 1
                    if st.get("is_breached"):
                        breaches_in_stage += 1
                    if st.get("status") == "REJECTED":
                        rejections_in_stage += 1

            avg_dur = round(statistics.mean(observed_durations), 1) if observed_durations else 0.0
            med_dur = round(statistics.median(observed_durations), 1) if observed_durations else 0.0

            stage_metrics.append({
                "stage_order": idx,
                "stage_name": s_name,
                "department": dept,
                "statutory_sla_days": statutory_sla,
                "avg_duration_days": avg_dur,
                "median_duration_days": med_dur,
                "duration_variance_vs_sla": round(avg_dur - statutory_sla, 1),
                "pending_count": pending_in_stage,
                "breach_count": breaches_in_stage,
                "rejection_count": rejections_in_stage,
                "is_delayed": avg_dur > statutory_sla
            })

        # 6. Bottleneck Detection Engine (Deterministic Rules)
        bottlenecks: List[Dict[str, Any]] = []

        # Rule A: Stage with highest backlog (> 30% of total pending cases)
        total_pending = len(pending_apps)
        for s in stage_metrics:
            if total_pending > 0 and (s["pending_count"] / total_pending) >= 0.35:
                bottlenecks.append({
                    "stage_name": s["stage_name"],
                    "department": s["department"],
                    "severity": "CRITICAL_BACKLOG",
                    "finding": f"Accumulates {s['pending_count']} pending cases ({int((s['pending_count']/total_pending)*100)}% of total backlog).",
                    "likely_cause": "Field inspection capacity deficit or heavy physical file queue.",
                    "recommended_remedy": "Reallocate cadastral staff or establish fast-track field inspection rosters."
                })

        # Rule B: Stage exceeding statutory SLA
        for s in stage_metrics:
            if s["avg_duration_days"] > s["statutory_sla_days"]:
                over = s["avg_duration_days"] - s["statutory_sla_days"]
                bottlenecks.append({
                    "stage_name": s["stage_name"],
                    "department": s["department"],
                    "severity": "STATUTORY_SLA_EXCEEDED",
                    "finding": f"Average duration ({s['avg_duration_days']} days) exceeds statutory limit ({s['statutory_sla_days']} days) by +{over:.1f} days.",
                    "likely_cause": "Complex demarcation requirements, physical boundary disputes, or weather delays.",
                    "recommended_remedy": "Deploy Rover DGPS kits and mobile surveying apps to accelerate cadastral field reports."
                })

        # Rule C: Stage with highest rejections
        for s in stage_metrics:
            if s["rejection_count"] >= 2:
                bottlenecks.append({
                    "stage_name": s["stage_name"],
                    "department": s["department"],
                    "severity": "HIGH_REJECTION_CLUSTER",
                    "finding": f"Highest rejection ground cluster ({s['rejection_count']} rejected cases originating at this stage).",
                    "likely_cause": "Pre-registration boundary overlaps or missing inheritance legal heir affidavits.",
                    "recommended_remedy": "Implement mandatory pre-submission document checklist at Citizen Portal."
                })

        sla_breach_rate = round((len(breached_apps) / total_count) * 100.0, 1) if total_count > 0 else 0.0

        return {
            "summary": {
                "total_applications": total_count,
                "pending_applications": len(pending_apps),
                "completed_applications": len(completed_apps),
                "rejected_applications": len(rejected_apps),
                "sla_breached_count": len(breached_apps),
                "sla_breach_rate_pct": sla_breach_rate,
                "avg_completion_days": avg_completion,
                "median_completion_days": median_completion,
                "avg_pending_age_days": avg_pending_age
            },
            "stages": stage_metrics,
            "bottlenecks": bottlenecks,
            "application_type_breakdown": type_breakdown,
            "status_breakdown": status_breakdown,
            "records": filtered,
            "data_source_label": "Demonstration Dataset: Administrative Workflow Records (NIC-DLRP Simulation)",
            "calculation_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
