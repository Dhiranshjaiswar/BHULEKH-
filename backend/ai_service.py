import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("bhulekh.ai_service")

# Configuration via environment variables
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "none").lower()
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")

def get_configured_provider() -> str:
    """Return active provider if API key exists, otherwise 'deterministic_fallback'."""
    if not LLM_API_KEY:
        return "deterministic_fallback"
    return LLM_PROVIDER if LLM_PROVIDER != "none" else "deterministic_fallback"


class AIService:
    """
    Central AI Explanation Service for BHULEKH.
    
    Principles:
    1. Deterministic engines compute all facts, scores, discrepancies, and metrics.
    2. The LLM is used solely to generate clear, grounded human-readable explanations.
    3. If LLM is not configured, offline, or returns an error, robust rule-based templates
       provide comprehensive, deterministic explanations without failing or hallucinating.
    """

    @classmethod
    def is_llm_available(cls) -> bool:
        return bool(LLM_API_KEY and LLM_PROVIDER not in ("none", "fallback", ""))

    @classmethod
    def call_llm(cls, system_prompt: str, user_prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Attempt to call the configured LLM provider. Returns None on failure."""
        if not cls.is_llm_available():
            return None

        provider = LLM_PROVIDER
        try:
            # 1. Google Gemini Provider
            if provider in ("gemini", "google"):
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=LLM_API_KEY)
                    model_name = LLM_MODEL or "gemini-1.5-flash"
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system_prompt
                    )
                    response = model.generate_content(user_prompt)
                    if response and response.text:
                        return response.text.strip()
                except Exception as e:
                    logger.warning(f"Google Gemini call failed: {e}. Falling back to deterministic engine.")
                    return None

            # 2. OpenAI Provider
            elif provider in ("openai", "azure_openai"):
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=LLM_API_KEY, timeout=12.0)
                    model_name = LLM_MODEL or "gpt-4o-mini"
                    res = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        max_tokens=max_tokens,
                        temperature=0.2
                    )
                    if res.choices and res.choices[0].message.content:
                        return res.choices[0].message.content.strip()
                except Exception as e:
                    logger.warning(f"OpenAI call failed: {e}. Falling back to deterministic engine.")
                    return None

            # 3. Groq Provider
            elif provider == "groq":
                try:
                    from groq import Groq
                    client = Groq(api_key=LLM_API_KEY, timeout=10.0)
                    model_name = LLM_MODEL or "llama-3.1-8b-instant"
                    res = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        max_tokens=max_tokens,
                        temperature=0.2
                    )
                    if res.choices and res.choices[0].message.content:
                        return res.choices[0].message.content.strip()
                except Exception as e:
                    logger.warning(f"Groq call failed: {e}. Falling back to deterministic engine.")
                    return None

        except Exception as outer_err:
            logger.error(f"Error in call_llm: {outer_err}")
            return None

        return None

    # =========================================================================
    # 1. DOCUMENT VERIFICATION EXPLANATIONS
    # =========================================================================
    @classmethod
    def generate_discrepancy_explanation(
        cls,
        documents_summary: List[Dict[str, Any]],
        discrepancies: List[Dict[str, Any]],
        overall_consistent: bool
    ) -> Dict[str, Any]:
        """
        Produce a grounded narrative of the document comparison results.
        """
        system_prompt = (
            "You are an impartial land document verification assistant for the Indian land administration system (BHULEKH). "
            "Explain the exact discrepancies found between the provided land documents. "
            "CRITICAL RULES:\n"
            "1. ONLY reference facts and differences explicitly present in the comparison results.\n"
            "2. DO NOT declare documents fake or accuse anyone of fraud; attribute differences to possible clerical errors, transliteration, unrecorded transactions, or boundary revisions.\n"
            "3. State actionable official verification steps (e.g. check Tehsil Khasra register, consult Sub-Registrar).\n"
            "4. Be concise, structured, and professional."
        )

        user_prompt = f"""
Documents Reviewed:
{json.dumps(documents_summary, indent=2)}

Deterministic Discrepancy Findings:
{json.dumps(discrepancies, indent=2)}

Overall Consistent: {overall_consistent}

Provide:
1. Executive Summary
2. Key Discrepancies Explained
3. Recommended Official Verification Steps
"""

        ai_text = cls.call_llm(system_prompt, user_prompt)
        if ai_text:
            return {
                "explanation_text": ai_text,
                "is_ai_generated": True,
                "provider": LLM_PROVIDER
            }

        # Deterministic Fallback Narrative
        return {
            "explanation_text": cls._deterministic_discrepancy_narrative(documents_summary, discrepancies, overall_consistent),
            "is_ai_generated": False,
            "provider": "deterministic_rules"
        }

    @staticmethod
    def _deterministic_discrepancy_narrative(
        docs: List[Dict[str, Any]],
        discrepancies: List[Dict[str, Any]],
        overall_consistent: bool
    ) -> str:
        doc_names = ", ".join([d.get("title", d.get("file_name", "Document")) for d in docs])
        
        if overall_consistent and not discrepancies:
            return (
                f"### Verification Summary: Consistent Records\n\n"
                f"A cross-comparison between **{len(docs)} document(s)** ({doc_names}) indicates that all extracted identifiers, "
                f"recorded ownership details, parcel numbers, and reported land areas are **mutually consistent** within normal formatting tolerances.\n\n"
                f"**Verification Advice:**\n"
                f"- Extracted values match across supplied deeds and extracts.\n"
                f"- For final statutory clearance, confirm active non-encumbrance status at the local Sub-Registrar's Office (SRO)."
            )

        significant = [d for d in discrepancies if d.get("severity") in ("CRITICAL", "SIGNIFICANT_DISCREPANCY", "HIGH")]
        possible = [d for d in discrepancies if d.get("severity") in ("POSSIBLE_DISCREPANCY", "MEDIUM", "MODERATE")]
        minor = [d for d in discrepancies if d.get("severity") in ("MINOR_VARIATION", "LOW")]

        lines = [
            f"### Document Verification Analysis",
            f"Cross-document analysis across **{len(docs)} document(s)** ({doc_names}) identified **{len(discrepancies)} variance(s)** "
            f"({len(significant)} significant, {len(possible)} possible, and {len(minor)} minor formatting variations).\n"
        ]

        if significant:
            lines.append("#### Significant Findings Requiring Official Review:")
            for s in significant:
                lines.append(
                    f"- **{s.get('field_label', s.get('field'))}**: {s.get('description', '')} "
                    f"*(Doc 1: '{s.get('doc1_value')}' vs Doc 2: '{s.get('doc2_value')}')*. "
                    f"**Impact:** {s.get('impact', 'Potential title ambiguity')}. "
                    f"**Action:** {s.get('recommended_action', 'Verify with Revenue Authority')}."
                )
            lines.append("")

        if possible:
            lines.append("#### Potential Variations to Investigate:")
            for p in possible:
                lines.append(
                    f"- **{p.get('field_label', p.get('field'))}**: {p.get('description', '')} "
                    f"*(Observed: '{p.get('doc1_value')}' vs '{p.get('doc2_value')}')*. "
                    f"**Action:** {p.get('recommended_action', 'Cross-check Jamabandi register')}."
                )
            lines.append("")

        lines.append("#### Recommended Verification Protocol:")
        lines.append("1. **Do not assume fraudulent intent**: Name and area discrepancies often stem from legacy regional script transliteration (Hindi to English) or colonial land measurement conversions.")
        lines.append("2. **Inspect Original Khasra / Khatauni**: Cross-verify the disputed parcel number with the official district Bhulekh / Jamabandi portal.")
        lines.append("3. **Seek Field Demarcation**: If area or boundary boundaries diverge, commission a licensed cadastral survey before entering into statutory transaction.")

        return "\n".join(lines)

    # =========================================================================
    # 2. LAND RISK ASSESSMENT EXPLANATIONS
    # =========================================================================
    @classmethod
    def generate_risk_assessment_explanation(cls, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Produce a clear, transparent explanation of the land record risk assessment.
        """
        system_prompt = (
            "You are a land risk advisory specialist for the Indian land records domain. "
            "Explain the land record risk assessment based strictly on the provided deterministic factors, "
            "scores, and evidence. "
            "CRITICAL RULES:\n"
            "1. Ground every claim on the supplied risk indicators and completeness scores.\n"
            "2. State clearly that this is an administrative document review and NOT an official title certificate or legal court verdict.\n"
            "3. Clearly distinguish between detected discrepancies and missing/unverified documents.\n"
            "4. Provide constructive next steps."
        )

        user_prompt = f"""
Risk Assessment Results:
{json.dumps(assessment, indent=2)}

Provide:
1. Executive Risk Level Summary
2. Evidence Breakdown of Identified Factors
3. Information Gaps & Missing Chain-of-Title
4. Prioritized Due Diligence Checklist
"""

        ai_text = cls.call_llm(system_prompt, user_prompt)
        if ai_text:
            return {
                "explanation_text": ai_text,
                "is_ai_generated": True,
                "provider": LLM_PROVIDER
            }

        return {
            "explanation_text": cls._deterministic_risk_narrative(assessment),
            "is_ai_generated": False,
            "provider": "deterministic_rules"
        }

    @staticmethod
    def _deterministic_risk_narrative(assessment: Dict[str, Any]) -> str:
        score = assessment.get("risk_score", 0)
        category = assessment.get("risk_category", "Lower level of identified record-related concerns")
        factors = assessment.get("evaluated_factors", [])
        gaps = assessment.get("information_gaps", [])
        actions = assessment.get("recommended_actions", [])

        lines = [
            f"### Land Record Risk Assessment: {category}",
            f"**Deterministic Risk Score:** **{score} / 100** | **Assessment Completeness:** **{assessment.get('completeness_percentage', 100)}%**\n",
            f"This evaluation synthesizes extracted document facts, cross-deed discrepancy results, statutory encumbrance records, "
            f"and chain-of-title completeness under standard revenue governance guidelines.\n"
        ]

        if factors:
            lines.append("#### Evaluated Risk Indicators & Evidence:")
            for f in factors:
                lines.append(
                    f"- **[{f.get('severity', 'INFO')}] {f.get('factor_name')}** (Weight: {f.get('score_contribution', 0)} pts)\n"
                    f"  * **Evidence:** {f.get('evidence')}\n"
                    f"  * **Significance:** {f.get('significance')}\n"
                    f"  * **Recommended Action:** {f.get('action')}"
                )
            lines.append("")
        else:
            lines.append("✓ **No critical record-related risk factors were flagged in the provided documentation.**\n")

        if gaps:
            lines.append("#### Information Gaps & Unverified Elements:")
            for g in gaps:
                lines.append(f"- **{g.get('item')}**: {g.get('description')} *(Impact: {g.get('impact')})*")
            lines.append("")

        if actions:
            lines.append("#### Actionable Verification Roadmap:")
            for i, act in enumerate(actions, 1):
                lines.append(f"{i}. {act}")
            lines.append("")

        lines.append("*(Notice: This assessment is an automated analysis of submitted records and available registry data. It does not replace a Title Search Report by a licensed Advocate or statutory verification by the Revenue Court.)*")

        return "\n".join(lines)

    # =========================================================================
    # 3. ADMINISTRATIVE DELAY ANALYSIS INSIGHTS
    # =========================================================================
    @classmethod
    def generate_delay_analytics_insights(cls, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Produce administrative workflow insights from calculated delay metrics.
        """
        system_prompt = (
            "You are an administrative process consultant for Indian state revenue and land departments. "
            "Synthesize the provided deterministic workflow metrics into clear, evidence-based administrative insights. "
            "CRITICAL RULES:\n"
            "1. Reference the exact numbers (average days, median days, SLA breach rates, backlog counts).\n"
            "2. Never accuse individual officers of misconduct; focus on procedural bottlenecks, staffing, survey complexities, and inter-departmental dependencies.\n"
            "3. Provide realistic administrative reform suggestions (e.g. digital surveyor dispatch, automated e-Court sync, pre-cleared NOC checklists)."
        )

        user_prompt = f"""
Administrative Delay Metrics:
{json.dumps(analytics_data, indent=2)}

Provide:
1. Executive Workflow Health Assessment
2. Primary Bottleneck Stages & Root-Cause Patterns
3. Key SLA Adherence Highlights
4. Administrative Action Plan for Revenue Leadership
"""

        ai_text = cls.call_llm(system_prompt, user_prompt)
        if ai_text:
            return {
                "insights_text": ai_text,
                "is_ai_generated": True,
                "provider": LLM_PROVIDER
            }

        return {
            "insights_text": cls._deterministic_delay_narrative(analytics_data),
            "is_ai_generated": False,
            "provider": "deterministic_rules"
        }

    @staticmethod
    def _deterministic_delay_narrative(analytics: Dict[str, Any]) -> str:
        summary = analytics.get("summary", {})
        bottlenecks = analytics.get("bottlenecks", [])
        stage_metrics = analytics.get("stages", [])

        total = summary.get("total_applications", 0)
        pending = summary.get("pending_applications", 0)
        completed = summary.get("completed_applications", 0)
        avg_completion = summary.get("avg_completion_days", 0)
        median_completion = summary.get("median_completion_days", 0)
        breach_count = summary.get("sla_breached_count", 0)
        breach_rate = summary.get("sla_breach_rate_pct", 0)

        lines = [
            "### Administrative Workflow & Delay Intelligence Report",
            f"Analysis of **{total} administrative applications** indicates that **{completed} cases are completed** with an average turnaround time of **{avg_completion:.1f} days** (median: **{median_completion:.1f} days**). "
            f"Currently, **{pending} cases are pending active review**, and **{breach_count} cases ({breach_rate:.1f}%) have breached statutory SLA deadlines** under the Public Services Guarantee Act.\n"
        ]

        if bottlenecks:
            lines.append("#### Critical Processing Bottlenecks Identified:")
            for b in bottlenecks:
                lines.append(
                    f"- **{b.get('stage_name')} ({b.get('department')})**: "
                    f"**Status:** {b.get('severity')}. "
                    f"**Metric:** {b.get('finding')}. "
                    f"**Underlying Cause:** {b.get('likely_cause')}. "
                    f"**Intervention:** {b.get('recommended_remedy')}."
                )
            lines.append("")

        if stage_metrics:
            lines.append("#### Departmental Stage Throughput Summary:")
            for s in stage_metrics:
                lines.append(
                    f"- **{s.get('stage_name')}**: Avg Duration: **{s.get('avg_duration_days', 0):.1f} days** "
                    f"(Statutory SLA: {s.get('statutory_sla_days')} days) | Backlog: {s.get('pending_count')} cases "
                    f"| SLA Breaches: {s.get('breach_count')} cases."
                )
            lines.append("")

        lines.append("#### Targeted Process Improvement Recommendations:")
        lines.append("1. **Modernize Cadastral Demarcation**: Field ground surveys routinely cause the highest cycle-time variability; deploy Rover DGPS and drone imagery to compress survey turnaround times.")
        lines.append("2. **Inter-Departmental e-Court API Integration**: Automate the legal dispute clearance stage by linking court case management registries (NJDG) to eliminate manual judicial liaison delays.")
        lines.append("3. **Supervisory SLA Exception Escalations**: Enforce automated 48-hour SDM alerts prior to SLA breach dates to prevent accumulation of overdue cases.")

        return "\n".join(lines)
