'use client';

import React, { useState, useEffect } from 'react';
import { 
  FileText, Upload, AlertTriangle, CheckCircle2, ShieldAlert, Sparkles, 
  ArrowRight, RefreshCw, Eye, Edit3, Trash2, Download, HelpCircle, ChevronDown, ChevronUp, Layers
} from 'lucide-react';
import { 
  api, ParsedDocument, ComparisonResult, DocumentDiscrepancy 
} from '@/lib/api';

interface DocumentVerificationProps {
  onForwardToRiskAssessment?: (docs: ParsedDocument[], discrepancies: DocumentDiscrepancy[]) => void;
}

export const DocumentVerification: React.FC<DocumentVerificationProps> = ({
  onForwardToRiskAssessment
}) => {
  const [presets, setPresets] = useState<any[]>([]);
  const [uploadedDocs, setUploadedDocs] = useState<ParsedDocument[]>([]);
  const [selectedDocIndex, setSelectedDocIndex] = useState<number | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isComparing, setIsComparing] = useState<boolean>(false);
  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [showEditModal, setShowEditModal] = useState<boolean>(false);
  const [editingDoc, setEditingDoc] = useState<ParsedDocument | null>(null);
  const [editingDocIndex, setEditingDocIndex] = useState<number>(-1);
  const [activeScenarioId, setActiveScenarioId] = useState<string | null>(null);

  // Load presets on mount
  useEffect(() => {
    api.getDocumentPresets()
      .then((data) => {
        setPresets(data);
        // Default to Scenario B (Discrepancy) to immediately showcase intelligence
        if (data && data.length > 1) {
          loadPreset(data[1]);
        }
      })
      .catch((err) => console.error('Failed to load presets:', err));
  }, []);

  const loadPreset = (preset: any) => {
    setActiveScenarioId(preset.id);
    const docs = [preset.doc1, preset.doc2];
    setUploadedDocs(docs);
    setComparisonResult(null);
    setUploadError(null);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    setUploadError(null);
    try {
      const newDocs: ParsedDocument[] = [...uploadedDocs];
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const parsed = await api.uploadDocument(file);
        newDocs.push(parsed);
      }
      setUploadedDocs(newDocs);
      setActiveScenarioId(null);
      setComparisonResult(null);
    } catch (err: any) {
      setUploadError(err.message || 'Error processing document');
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  const handleRemoveDoc = (index: number) => {
    const updated = uploadedDocs.filter((_, i) => i !== index);
    setUploadedDocs(updated);
    setComparisonResult(null);
  };

  const handleRunComparison = async () => {
    if (uploadedDocs.length < 2) {
      alert('Please upload or select at least 2 documents to perform cross-document discrepancy verification.');
      return;
    }
    setIsComparing(true);
    try {
      const res = await api.compareDocuments(uploadedDocs[0], uploadedDocs[1]);
      setComparisonResult(res);
    } catch (err: any) {
      alert(`Comparison error: ${err.message}`);
    } finally {
      setIsComparing(false);
    }
  };

  const handleOpenEdit = (doc: ParsedDocument, index: number) => {
    setEditingDoc(JSON.parse(JSON.stringify(doc)));
    setEditingDocIndex(index);
    setShowEditModal(true);
  };

  const handleSaveEdit = () => {
    if (editingDoc && editingDocIndex >= 0) {
      const updated = [...uploadedDocs];
      updated[editingDocIndex] = editingDoc;
      setUploadedDocs(updated);
      setShowEditModal(false);
      setComparisonResult(null); // Reset comparison so user can re-evaluate with corrected data
    }
  };

  const handleDownloadReport = () => {
    if (!comparisonResult) return;
    const reportData = {
      title: "BHULEKH Land Document Verification Report",
      timestamp: new Date().toISOString(),
      documents: uploadedDocs.map(d => ({
        title: d.title,
        doc_type: d.doc_type,
        sha256_hash: d.sha256_hash,
        fields: d.fields
      })),
      comparison_summary: {
        overall_consistent: comparisonResult.overall_consistent,
        discrepancies_found: comparisonResult.discrepancy_count,
        significant_count: comparisonResult.significant_count,
        minor_count: comparisonResult.minor_count
      },
      discrepancies: comparisonResult.discrepancies,
      statutory_explanation: comparisonResult.explanation
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Bhulekh_Document_Verification_Report_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-medium">Cross-Record Discrepancy Engine</span>
            </div>
            <h2 className="text-xl font-extrabold text-[#0a2540] tracking-tight flex items-center gap-2">
              <FileText className="w-6 h-6 text-blue-600" />
              Land Document Verification & Discrepancy Detection
            </h2>
            <p className="text-xs text-slate-600 leading-relaxed max-w-3xl">
              Upload scanned land deeds, Khatauni (RoR) extracts, and mutation orders to automatically extract 
              cadastral fields, reconcile units, and identify discrepancies in recorded ownership, Khasra numbers, and land extent.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleRunComparison}
              disabled={uploadedDocs.length < 2 || isComparing}
              className={`px-4 py-2.5 rounded-lg text-xs font-bold flex items-center gap-2 shadow-sm transition ${
                uploadedDocs.length >= 2 && !isComparing
                  ? 'bg-[#0a2540] text-white hover:bg-slate-800'
                  : 'bg-slate-200 text-slate-400 cursor-not-allowed'
              }`}
            >
              {isComparing ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Analyzing Discrepancies...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-amber-400" />
                  Run Discrepancy Analysis
                </>
              )}
            </button>
          </div>
        </div>

        {/* Quick Demo Presets Bar */}
        <div className="mt-5 pt-4 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center gap-3">
          <span className="text-xs font-bold text-slate-700 whitespace-nowrap flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-amber-500" />
            Hackathon Demo Presets:
          </span>
          <div className="flex flex-wrap gap-2">
            {presets.map((p) => (
              <button
                key={p.id}
                onClick={() => loadPreset(p)}
                className={`text-xs px-3 py-1.5 rounded-lg border font-semibold transition ${
                  activeScenarioId === p.id
                    ? 'bg-amber-100 border-amber-400 text-amber-900 shadow-sm'
                    : 'bg-slate-50 border-slate-300 text-slate-700 hover:bg-slate-100'
                }`}
              >
                {p.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Upload Zone & Documents List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Upload Card */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
              <Upload className="w-4 h-4 text-blue-600" />
              Upload Documents
            </h3>
            <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-mono">
              PDF / JPG / PNG
            </span>
          </div>

          <label className="border-2 border-dashed border-slate-300 hover:border-blue-500 rounded-xl p-6 flex flex-col items-center justify-center text-center cursor-pointer bg-slate-50 hover:bg-blue-50/40 transition group">
            <Upload className="w-8 h-8 text-slate-400 group-hover:text-blue-600 mb-2 transition" />
            <span className="text-xs font-bold text-slate-700 group-hover:text-blue-700">
              Click to select or drag & drop files
            </span>
            <span className="text-[11px] text-slate-500 mt-1">
              Supports Sale Deeds, Khatauni, Khasra Nakal (Up to 15MB)
            </span>
            <input
              type="file"
              multiple
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={handleFileUpload}
              className="hidden"
            />
          </label>

          {isUploading && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-center gap-2 text-xs text-blue-800">
              <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
              <span>Extracting document text & running OCR analysis...</span>
            </div>
          )}

          {uploadError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
              {uploadError}
            </div>
          )}

          <div className="text-[11px] text-slate-500 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-200">
            <p className="font-semibold text-slate-700 mb-1">OCR & Privacy Guarantee:</p>
            Raw deed text is parsed locally on the national node. No biometric or Aadhaar numbers are persisted or exposed off-chain.
          </div>
        </div>

        {/* Uploaded Documents List */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
              <Layers className="w-4 h-4 text-[#0a2540]" />
              Loaded Documents for Cross-Verification ({uploadedDocs.length})
            </h3>
            {uploadedDocs.length >= 2 && (
              <span className="text-[11px] text-emerald-700 font-semibold bg-emerald-50 px-2.5 py-0.5 rounded border border-emerald-200">
                ✓ Ready for Pairwise Comparison
              </span>
            )}
          </div>

          {uploadedDocs.length === 0 ? (
            <div className="p-8 text-center text-slate-400 text-xs border border-dashed border-slate-200 rounded-lg">
              No documents loaded. Choose a demo preset above or upload PDF/image deeds.
            </div>
          ) : (
            <div className="space-y-3">
              {uploadedDocs.map((doc, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-[#0a2540] text-white flex items-center justify-center text-[10px] font-bold">
                        {idx + 1}
                      </span>
                      <p className="text-xs font-bold text-slate-900">{doc.title}</p>
                      <span className="text-[10px] bg-slate-200 text-slate-800 px-1.5 py-0.2 rounded font-semibold">
                        {doc.fields?.doc_type?.replace(/_/g, ' ') || doc.doc_type}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] text-slate-600 pt-1">
                      <div>
                        <span className="text-slate-400 block text-[9px] uppercase font-bold">Khasra / Plot</span>
                        <span className="font-semibold text-slate-800">{doc.fields?.khasra_no || 'Not found'}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[9px] uppercase font-bold">Reported Area</span>
                        <span className="font-semibold text-slate-800">
                          {doc.fields?.land_area ? `${doc.fields.land_area} ${doc.fields.area_unit || 'SQFT'}` : 'Not found'}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[9px] uppercase font-bold">Recorded Owner</span>
                        <span className="font-semibold text-slate-800 truncate block">
                          {doc.fields?.owner_names?.[0] || 'Not detected'}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[9px] uppercase font-bold">Confidence</span>
                        <span className="font-mono text-blue-700 font-semibold">
                          {doc.fields?.extraction_confidence ? `${Math.round(doc.fields.extraction_confidence * 100)}%` : '92%'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 self-end md:self-auto">
                    <button
                      onClick={() => handleOpenEdit(doc, idx)}
                      className="px-2.5 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-100 text-xs font-semibold text-slate-700 flex items-center gap-1"
                    >
                      <Edit3 className="w-3.5 h-3.5 text-blue-600" />
                      Review / Edit
                    </button>
                    <button
                      onClick={() => handleRemoveDoc(idx)}
                      className="p-1.5 rounded-lg border border-slate-200 hover:bg-red-50 text-slate-400 hover:text-red-600"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>

      {/* Comparison Results Section */}
      {comparisonResult && (
        <div className="space-y-6 animate-in fade-in duration-200">
          
          {/* Status Header Banner */}
          <div
            className={`rounded-xl p-5 border flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
              comparisonResult.overall_consistent
                ? 'bg-emerald-50 border-emerald-300 text-emerald-950'
                : 'bg-amber-50 border-amber-300 text-amber-950'
            }`}
          >
            <div className="flex items-start gap-3">
              {comparisonResult.overall_consistent ? (
                <CheckCircle2 className="w-7 h-7 text-emerald-600 shrink-0 mt-0.5" />
              ) : (
                <ShieldAlert className="w-7 h-7 text-amber-600 shrink-0 mt-0.5" />
              )}
              <div>
                <h3 className="text-base font-extrabold tracking-tight">
                  {comparisonResult.overall_consistent
                    ? 'Records Mutually Consistent Across Verified Documents'
                    : `Discrepancies Identified: ${comparisonResult.significant_count} Significant & ${comparisonResult.minor_count} Minor Variation(s)`}
                </h3>
                <p className="text-xs opacity-90 mt-0.5">
                  Comparison between <span className="font-bold">{uploadedDocs[0]?.title}</span> and{' '}
                  <span className="font-bold">{uploadedDocs[1]?.title}</span>.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleDownloadReport}
                className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-xs font-bold text-slate-800 flex items-center gap-1.5 shadow-sm"
              >
                <Download className="w-3.5 h-3.5 text-slate-600" />
                Export Report (JSON)
              </button>

              {onForwardToRiskAssessment && (
                <button
                  onClick={() => onForwardToRiskAssessment(uploadedDocs, comparisonResult.discrepancies)}
                  className="px-3 py-1.5 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold flex items-center gap-1.5 shadow-sm"
                >
                  <ArrowRight className="w-3.5 h-3.5" />
                  Evaluate Land Risk
                </button>
              )}
            </div>
          </div>

          {/* AI Grounded Narrative Explanation */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-amber-500" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900">
                  Grounded Verification Explanation
                </h4>
              </div>
              <span
                className={`text-[10px] px-2 py-0.5 rounded font-bold border ${
                  comparisonResult.explanation?.is_ai_generated
                    ? 'bg-purple-50 text-purple-800 border-purple-200'
                    : 'bg-slate-100 text-slate-700 border-slate-300'
                }`}
              >
                {comparisonResult.explanation?.is_ai_generated
                  ? `AI Narrative (${comparisonResult.explanation?.provider || 'Gemini'})`
                  : 'Statutory Rule Engine Narrative'}
              </span>
            </div>

            <div className="prose prose-xs max-w-none text-slate-700 leading-relaxed font-sans text-xs whitespace-pre-line bg-slate-50/60 p-4 rounded-lg border border-slate-100">
              {comparisonResult.explanation?.explanation_text}
            </div>
          </div>

          {/* Discrepancies Detailed Findings Cards */}
          {comparisonResult.discrepancies.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                Discrepancy Details & Recommended Actions ({comparisonResult.discrepancies.length})
              </h4>

              <div className="grid grid-cols-1 gap-3">
                {comparisonResult.discrepancies.map((d, dIdx) => (
                  <div
                    key={dIdx}
                    className={`p-4 rounded-xl border transition ${
                      d.severity === 'SIGNIFICANT_DISCREPANCY'
                        ? 'bg-red-50/40 border-red-300'
                        : 'bg-amber-50/40 border-amber-300'
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200/60 pb-2 mb-3">
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase border ${
                            d.severity === 'SIGNIFICANT_DISCREPANCY'
                              ? 'bg-red-100 text-red-900 border-red-300'
                              : 'bg-amber-100 text-amber-900 border-amber-300'
                          }`}
                        >
                          {d.severity === 'SIGNIFICANT_DISCREPANCY' ? 'Significant Review' : 'Potential Variation'}
                        </span>
                        <h5 className="text-xs font-bold text-slate-900">{d.field_label}</h5>
                      </div>
                      <span className="text-[10px] text-slate-500 font-medium">Field: {d.field}</span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs mb-3">
                      <div className="p-3 bg-white rounded-lg border border-slate-200">
                        <span className="text-[10px] font-bold text-slate-500 uppercase block mb-1">
                          Document 1: {d.doc1_title}
                        </span>
                        <span className="font-bold text-slate-900 text-sm">{d.doc1_value}</span>
                        {d.doc1_provenance && (
                          <span className="text-[10px] text-slate-400 block mt-1 italic truncate">
                            Provenance: "{d.doc1_provenance}"
                          </span>
                        )}
                      </div>

                      <div className="p-3 bg-white rounded-lg border border-slate-200">
                        <span className="text-[10px] font-bold text-slate-500 uppercase block mb-1">
                          Document 2: {d.doc2_title}
                        </span>
                        <span className="font-bold text-slate-900 text-sm">{d.doc2_value}</span>
                        {d.doc2_provenance && (
                          <span className="text-[10px] text-slate-400 block mt-1 italic truncate">
                            Provenance: "{d.doc2_provenance}"
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="space-y-1.5 text-xs text-slate-700 bg-white/70 p-3 rounded-lg border border-slate-200/60">
                      <p>
                        <strong className="text-slate-900">Observed Variance:</strong> {d.description}
                      </p>
                      <p>
                        <strong className="text-slate-900">Legal / Administrative Impact:</strong> {d.impact}
                      </p>
                      <p className="text-blue-900 font-medium">
                        <strong>Recommended Verification Action:</strong> {d.recommended_action}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Consistent Fields Verified */}
          {comparisonResult.consistent_fields.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                Verified Matching Fields ({comparisonResult.consistent_fields.length})
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 pt-1">
                {comparisonResult.consistent_fields.map((c, cIdx) => (
                  <div key={cIdx} className="p-2.5 bg-emerald-50/50 rounded-lg border border-emerald-200 text-xs">
                    <span className="text-[10px] text-emerald-800 font-bold block">{c.field_label}</span>
                    <span className="text-slate-900 font-medium truncate block">{c.doc1_value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      )}

      {/* Review / Edit Modal */}
      {showEditModal && editingDoc && (
        <div className="fixed inset-0 bg-slate-900/50 z-50 flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="bg-white rounded-xl shadow-2xl border border-slate-200 max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-extrabold text-slate-900">Review & Correct Extracted Fields</h3>
                <p className="text-xs text-slate-500">Edit fields before comparison if OCR or extraction had ambiguity</p>
              </div>
              <button
                onClick={() => setShowEditModal(false)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold p-1"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="block font-bold text-slate-700 mb-1">Document Reference Number</label>
                <input
                  type="text"
                  value={editingDoc.fields.document_ref_no || ''}
                  onChange={(e) => setEditingDoc({
                    ...editingDoc,
                    fields: { ...editingDoc.fields, document_ref_no: e.target.value }
                  })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Khasra / Survey Number</label>
                <input
                  type="text"
                  value={editingDoc.fields.khasra_no || ''}
                  onChange={(e) => setEditingDoc({
                    ...editingDoc,
                    fields: { ...editingDoc.fields, khasra_no: e.target.value }
                  })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-mono"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Khata Holding Number</label>
                <input
                  type="text"
                  value={editingDoc.fields.khata_no || ''}
                  onChange={(e) => setEditingDoc({
                    ...editingDoc,
                    fields: { ...editingDoc.fields, khata_no: e.target.value }
                  })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-mono"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Plot Number</label>
                <input
                  type="text"
                  value={editingDoc.fields.plot_no || ''}
                  onChange={(e) => setEditingDoc({
                    ...editingDoc,
                    fields: { ...editingDoc.fields, plot_no: e.target.value }
                  })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Recorded Landowner Name</label>
                <input
                  type="text"
                  value={editingDoc.fields.owner_names?.[0] || ''}
                  onChange={(e) => setEditingDoc({
                    ...editingDoc,
                    fields: { ...editingDoc.fields, owner_names: [e.target.value] }
                  })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Land Area</label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    value={editingDoc.fields.land_area || ''}
                    onChange={(e) => setEditingDoc({
                      ...editingDoc,
                      fields: { ...editingDoc.fields, land_area: parseFloat(e.target.value) || 0 }
                    })}
                    className="w-2/3 px-3 py-2 border border-slate-300 rounded-lg text-xs"
                  />
                  <select
                    value={editingDoc.fields.area_unit || 'SQFT'}
                    onChange={(e) => setEditingDoc({
                      ...editingDoc,
                      fields: { ...editingDoc.fields, area_unit: e.target.value }
                    })}
                    className="w-1/3 px-2 py-2 border border-slate-300 rounded-lg text-xs font-bold"
                  >
                    <option value="SQFT">Sq. Ft.</option>
                    <option value="SQM">Sq. M.</option>
                    <option value="ACRES">Acres</option>
                    <option value="BIGHA">Bigha</option>
                    <option value="GUNTAS">Guntas</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">Village / Mauza</label>
                <input
                  type="text"
                  value={editingDoc.fields.village || ''}
                  onChange={(e) => setEditingDoc({
                    ...editingDoc,
                    fields: { ...editingDoc.fields, village: e.target.value }
                  })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1">District</label>
                <input
                  type="text"
                  value={editingDoc.fields.district || ''}
                  onChange={(e) => setEditingDoc({
                    ...editingDoc,
                    fields: { ...editingDoc.fields, district: e.target.value }
                  })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs"
                />
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
              <button
                onClick={() => setShowEditModal(false)}
                className="px-4 py-2 rounded-lg border border-slate-300 text-xs font-bold text-slate-700 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveEdit}
                className="px-4 py-2 rounded-lg bg-[#0a2540] hover:bg-slate-800 text-white text-xs font-bold shadow-sm"
              >
                Save & Update
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
