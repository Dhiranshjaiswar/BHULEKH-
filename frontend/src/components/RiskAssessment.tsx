'use client';

import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, AlertOctagon, AlertTriangle, CheckCircle, Info, Sparkles, 
  ArrowRight, Download, RefreshCw, FileSearch, Building2, MapPin, Landmark
} from 'lucide-react';
import { 
  api, RiskAssessmentResult, ParsedDocument, DocumentDiscrepancy, Parcel 
} from '@/lib/api';

interface RiskAssessmentProps {
  initialDocs?: ParsedDocument[];
  initialDiscrepancies?: DocumentDiscrepancy[];
  parcels?: Parcel[];
}

export const RiskAssessment: React.FC<RiskAssessmentProps> = ({
  initialDocs = [],
  initialDiscrepancies = [],
  parcels = []
}) => {
  const [selectedParcelId, setSelectedParcelId] = useState<string>('');
  const [docsToAssess, setDocsToAssess] = useState<ParsedDocument[]>(initialDocs);
  const [discrepanciesToAssess, setDiscrepanciesToAssess] = useState<DocumentDiscrepancy[]>(initialDiscrepancies);
  const [assessmentResult, setAssessmentResult] = useState<RiskAssessmentResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // If initial docs were passed from Tool 1, automatically run assessment
  useEffect(() => {
    if (initialDocs.length > 0) {
      setDocsToAssess(initialDocs);
      setDiscrepanciesToAssess(initialDiscrepancies);
      runAssessmentWithData(initialDocs, initialDiscrepancies);
    } else if (parcels.length > 0 && !selectedParcelId) {
      // Default to first parcel
      setSelectedParcelId(parcels[0].id);
      runParcelAssessment(parcels[0].id);
    }
  }, [initialDocs, initialDiscrepancies, parcels]);

  const runAssessmentWithData = async (docs: ParsedDocument[], discrepancies: DocumentDiscrepancy[], parcelId?: string) => {
    setIsLoading(true);
    try {
      const res = await api.performRiskAssessment(docs, discrepancies, parcelId);
      setAssessmentResult(res);
    } catch (err: any) {
      alert(`Assessment error: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const runParcelAssessment = async (pId: string) => {
    if (!pId) return;
    setIsLoading(true);
    try {
      const res = await api.assessParcelRisk(pId);
      setAssessmentResult(res);
      setSelectedParcelId(pId);
    } catch (err: any) {
      alert(`Error assessing parcel: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadReport = () => {
    if (!assessmentResult) return;
    const blob = new Blob([JSON.stringify(assessmentResult, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Bhulekh_Land_Risk_Assessment_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getScoreColor = (score: number) => {
    if (score <= 25) return 'text-emerald-700 bg-emerald-50 border-emerald-300';
    if (score <= 55) return 'text-amber-700 bg-amber-50 border-amber-300';
    return 'text-red-700 bg-red-50 border-red-300';
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-medium">Transparent Due Diligence Engine</span>
            </div>
            <h2 className="text-xl font-extrabold text-[#0a2540] tracking-tight flex items-center gap-2">
              <ShieldCheck className="w-6 h-6 text-emerald-600" />
              Evidence-Based AI Land Risk Assessment
            </h2>
            <p className="text-xs text-slate-600 leading-relaxed max-w-3xl">
              Deterministic, multi-factor risk evaluation synthesizing verified title document discrepancies, 
              cadastral survey boundary integrity, and active statutory court injunctions or bank charges.
            </p>
          </div>

          {/* Quick Actions */}
          <div className="flex flex-wrap items-center gap-2">
            {parcels.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500 font-bold hidden sm:inline">Select Registry Parcel:</span>
                <select
                  value={selectedParcelId}
                  onChange={(e) => runParcelAssessment(e.target.value)}
                  className="px-3 py-2 rounded-lg border border-slate-300 text-xs font-semibold bg-slate-50 text-slate-800"
                >
                  {parcels.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.ulin_pin} — {p.district} ({p.current_owner_name})
                    </option>
                  ))}
                </select>
              </div>
            )}

            <button
              onClick={() => {
                if (selectedParcelId) runParcelAssessment(selectedParcelId);
                else if (docsToAssess.length > 0) runAssessmentWithData(docsToAssess, discrepanciesToAssess);
              }}
              disabled={isLoading}
              className="px-3 py-2 rounded-lg bg-[#0a2540] text-white text-xs font-bold flex items-center gap-1.5 shadow-sm hover:bg-slate-800 transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              Re-Evaluate
            </button>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center space-y-3">
          <RefreshCw className="w-8 h-8 text-emerald-600 animate-spin mx-auto" />
          <h3 className="text-sm font-bold text-slate-800">Calculating Transparent Evidence Factors...</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Evaluating document discrepancies, e-Court litigation flags, and chain-of-title completeness.
          </p>
        </div>
      ) : assessmentResult ? (
        <div className="space-y-6 animate-in fade-in duration-200">
          
          {/* Executive Risk Score & Completeness Card */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Score Metric Card */}
            <div className={`p-6 rounded-xl border shadow-sm flex flex-col justify-between ${getScoreColor(assessmentResult.risk_score)}`}>
              <div className="space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-wider block opacity-75">
                  Overall Title Risk Score
                </span>
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-extrabold tracking-tight">{assessmentResult.risk_score}</span>
                  <span className="text-sm font-bold opacity-70">/ 100</span>
                </div>
              </div>

              <div className="pt-4 border-t border-current/20 mt-4 space-y-1">
                <span className="text-xs font-extrabold block">
                  {assessmentResult.risk_category}
                </span>
                <span className="text-[11px] opacity-80 block">
                  {assessmentResult.risk_score <= 25
                    ? 'No critical record defects found in reviewed documentation.'
                    : assessmentResult.risk_score <= 55
                    ? 'Actionable record variations or encumbrances require verification.'
                    : 'Significant title divergence or active dispute flagged!'}
                </span>
              </div>
            </div>

            {/* Assessment Completeness Card */}
            <div className="p-6 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
              <div className="space-y-1">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                  Assessment Evidence Completeness
                </span>
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-extrabold text-[#0a2540] tracking-tight">
                    {assessmentResult.completeness_percentage}%
                  </span>
                  <span className="text-xs text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded">
                    Statutory Depth
                  </span>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100 mt-4 space-y-2">
                <div className="w-full bg-slate-100 rounded-full h-2">
                  <div
                    className="bg-emerald-600 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${assessmentResult.completeness_percentage}%` }}
                  ></div>
                </div>
                <div className="flex justify-between text-[10px] text-slate-500 font-medium">
                  <span>{assessmentResult.documents_evaluated_count} Documents Reviewed</span>
                  <span>{assessmentResult.discrepancies_evaluated_count} Discrepancies Analyzed</span>
                </div>
              </div>
            </div>

            {/* Export & Actions Card */}
            <div className="p-6 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
              <div className="space-y-2">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                  Due Diligence Export
                </span>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Download a certified audit package containing evaluated risk weights, verified evidence snippets, and due diligence roadmap.
                </p>
              </div>

              <div className="pt-4 border-t border-slate-100 mt-4 flex items-center gap-2">
                <button
                  onClick={handleDownloadReport}
                  className="w-full py-2.5 rounded-lg border border-slate-300 bg-slate-50 hover:bg-slate-100 text-xs font-bold text-slate-800 flex items-center justify-center gap-2 shadow-sm transition"
                >
                  <Download className="w-3.5 h-3.5 text-slate-600" />
                  Download Risk Report (JSON)
                </button>
              </div>
            </div>

          </div>

          {/* AI Grounded Narrative Explanation */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-emerald-600" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900">
                  Grounded Risk Explanation
                </h4>
              </div>
              <span
                className={`text-[10px] px-2 py-0.5 rounded font-bold border ${
                  assessmentResult.explanation?.is_ai_generated
                    ? 'bg-purple-50 text-purple-800 border-purple-200'
                    : 'bg-slate-100 text-slate-700 border-slate-300'
                }`}
              >
                {assessmentResult.explanation?.is_ai_generated
                  ? `AI Narrative (${assessmentResult.explanation?.provider || 'Gemini'})`
                  : 'Deterministic Statutory Rule Engine'}
              </span>
            </div>

            <div className="prose prose-xs max-w-none text-slate-700 leading-relaxed font-sans text-xs whitespace-pre-line bg-slate-50/60 p-4 rounded-lg border border-slate-100">
              {assessmentResult.explanation?.explanation_text}
            </div>
          </div>

          {/* Evaluated Risk Indicators Breakdown */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              Evaluated Risk Indicators & Statutory Evidence ({assessmentResult.evaluated_factors.length})
            </h4>

            {assessmentResult.evaluated_factors.length === 0 ? (
              <div className="p-5 bg-emerald-50 rounded-xl border border-emerald-200 text-emerald-900 text-xs flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
                <span>No adverse record factors, encumbrances, or boundary disputes detected in the reviewed documentation.</span>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-3">
                {assessmentResult.evaluated_factors.map((f, fIdx) => (
                  <div
                    key={fIdx}
                    className={`p-4 rounded-xl border transition ${
                      f.severity === 'CRITICAL'
                        ? 'bg-red-50/40 border-red-300'
                        : f.severity === 'HIGH'
                        ? 'bg-amber-50/40 border-amber-300'
                        : 'bg-slate-50 border-slate-200'
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200/60 pb-2 mb-2.5">
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase border ${
                            f.severity === 'CRITICAL'
                              ? 'bg-red-100 text-red-900 border-red-300'
                              : f.severity === 'HIGH'
                              ? 'bg-amber-100 text-amber-900 border-amber-300'
                              : 'bg-blue-100 text-blue-900 border-blue-200'
                          }`}
                        >
                          {f.severity}
                        </span>
                        <h5 className="text-xs font-bold text-slate-900">{f.factor_name}</h5>
                      </div>
                      <span className="text-[11px] font-mono font-bold text-slate-700 bg-white px-2 py-0.5 rounded border border-slate-200">
                        Score Impact: +{f.score_contribution} pts
                      </span>
                    </div>

                    <div className="space-y-1.5 text-xs text-slate-700 bg-white/70 p-3 rounded-lg border border-slate-200/60">
                      <p>
                        <strong className="text-slate-900">Evidence Record:</strong> {f.evidence}
                      </p>
                      <p>
                        <strong className="text-slate-900">Significance:</strong> {f.significance}
                      </p>
                      <p className="text-blue-900 font-medium">
                        <strong>Mandatory Due Diligence Action:</strong> {f.action}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Information Gaps & Recommended Roadmap */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Information Gaps */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
                <Info className="w-4 h-4 text-blue-600" />
                Information Gaps & Absent Records ({assessmentResult.information_gaps.length})
              </h4>
              <p className="text-[11px] text-slate-500">
                Documents or identifiers not provided in this assessment. An absent document is distinct from an inconsistent record.
              </p>

              {assessmentResult.information_gaps.length === 0 ? (
                <div className="text-xs text-slate-500 italic p-3 bg-slate-50 rounded-lg">
                  No missing critical identifiers.
                </div>
              ) : (
                <div className="space-y-2">
                  {assessmentResult.information_gaps.map((g, gIdx) => (
                    <div key={gIdx} className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs space-y-1">
                      <span className="font-bold text-slate-900 block">{g.item}</span>
                      <p className="text-slate-600">{g.description}</p>
                      <span className="text-[10px] text-amber-800 font-semibold block">Impact: {g.impact}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Actionable Due Diligence Roadmap */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-600" />
                Prioritized Due Diligence Roadmap
              </h4>
              <p className="text-[11px] text-slate-500">
                Statutory verification checklist before entering into sale agreement or statutory registration:
              </p>

              <div className="space-y-2">
                {assessmentResult.recommended_actions.map((act, aIdx) => (
                  <div key={aIdx} className="p-3 bg-emerald-50/40 rounded-lg border border-emerald-200 text-xs flex items-start gap-2.5">
                    <span className="w-5 h-5 rounded-full bg-emerald-700 text-white flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">
                      {aIdx + 1}
                    </span>
                    <span className="text-slate-800 leading-relaxed font-medium">{act}</span>
                  </div>
                ))}
              </div>
            </div>

          </div>

          {/* Statutory Legal Disclaimer */}
          <div className="p-4 bg-slate-100 rounded-xl border border-slate-200 text-[11px] text-slate-600 leading-relaxed">
            <span className="font-bold text-slate-800 uppercase block mb-1">Administrative & Statutory Disclaimer:</span>
            {assessmentResult.disclaimer} This tool synthesizes evidence from submitted deeds and available registry indices. 
            It does not constitute an official Government Title Guarantee or legal advocate certificate. Statutory authority remains exclusively vested in the Revenue Courts and Registration Authorities.
          </div>

        </div>
      ) : null}
    </div>
  );
};
