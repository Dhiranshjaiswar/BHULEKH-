const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export interface User {
  id: string;
  username: string;
  full_name: string;
  email: string;
  role: string;
  department: string;
  phone_masked: string;
  aadhaar_masked: string;
  pan_masked: string;
}

export interface Parcel {
  id: string;
  ulin_pin: string;
  state: string;
  revenue_authority: string;
  district: string;
  tehsil: string;
  village: string;
  khasra_no: string;
  khata_no: string;
  land_use: string;
  area_sqft: number;
  area_sqm: number;
  area_local_unit: string;
  circle_rate_sqft_2026: number;
  circle_rate_2026: number;
  circle_rate_2025: number;
  circle_rate_2024: number;
  estimated_govt_value_lakhs: number;
  formatted_value_str: string;
  ownership_status: string;
  current_owner_id?: string;
  current_owner_name?: string;
  is_for_sale: boolean;
  listing_price_lakhs?: number;
  is_disputed: boolean;
  dispute_case_no?: string;
  dispute_details?: string;
  is_mortgaged: boolean;
  mortgage_bank?: string;
  mortgage_amount_lakhs?: number;
  tax_cleared: boolean;
  boundary_verified: boolean;
  risk_rating: 'LOW_RISK' | 'REVIEW_REQUIRED' | 'HIGH_RISK';
  centroid_lat: number;
  centroid_lng: number;
  geometry_geojson: string;
  ownership_history?: OwnershipHistory[];
  documents?: DocumentRecord[];
}

export interface OwnershipHistory {
  id: number;
  year: number;
  previous_owner_name?: string;
  new_owner_name: string;
  transfer_type: string;
  transaction_value_lakhs: number;
  registration_number: string;
  registration_date: string;
  document_hash?: string;
  ledger_tx_hash?: string;
  approving_authority: string;
}

export interface DocumentRecord {
  id: string;
  application_id?: string;
  parcel_id: string;
  doc_type: string;
  title: string;
  file_name: string;
  file_size_kb: number;
  mime_type: string;
  sha256_hash: string;
  verification_status: string;
  uploaded_by: string;
  uploaded_at: string;
  remarks?: string;
}

export interface ApplicationStage {
  id: number;
  stage_order: number;
  stage_name: string;
  department: string;
  assigned_role: string;
  assigned_officer_id?: string;
  assigned_officer_name?: string;
  status: string;
  sla_days: number;
  assigned_at: string;
  deadline_at: string;
  completed_at?: string;
  officer_remarks?: string;
  digital_signature?: string;
  time_remaining_str?: string;
  is_breached?: boolean;
}

export interface ApplicationRecord {
  id: string;
  parcel_id: string;
  applicant_id: string;
  applicant_name?: string;
  buyer_name: string;
  buyer_masked_aadhaar: string;
  buyer_phone_masked: string;
  transfer_type: string;
  declared_value_lakhs: number;
  formatted_declared_value: string;
  stamp_duty_paid_lakhs: number;
  current_stage_index: number;
  status: string;
  created_at: string;
  sla_deadline: string;
  is_sla_breached: boolean;
  supervisor_notified: boolean;
  delay_explanation?: string;
  rejection_category?: string;
  rejection_remarks?: string;
  rejection_officer_name?: string;
  rejection_department?: string;
  rejected_at?: string;
  is_appealed: boolean;
  appeal_remarks?: string;
  appealed_at?: string;
  appeal_status?: string;
  final_ledger_block_index?: number;
  final_ledger_tx_hash?: string;
  parcel_district?: string;
  parcel_village?: string;
  parcel?: Parcel;
  stages?: ApplicationStage[];
  documents?: DocumentRecord[];
}

export interface LedgerBlock {
  block_index: number;
  timestamp: string;
  parcel_id: string;
  event_type: string;
  payload_json: string;
  payload_hash: string;
  previous_hash: string;
  merkle_root: string;
  officer_signatures: string;
  block_hash: string;
  nonce: number;
}

export interface AuditEvent {
  id: number;
  entity_type: string;
  entity_id: string;
  actor_name: string;
  actor_role: string;
  action: string;
  details: string;
  ip_address: string;
  timestamp: string;
}

export interface OfficerStats {
  total_assigned: number;
  pending: number;
  approved: number;
  rejected: number;
  sla_approaching: number;
  sla_breached: number;
  appeals: number;
  disputed_parcels: number;
}

export const api = {
  getUsers: async (role?: string): Promise<User[]> => {
    const res = await fetch(`${API_BASE}/users${role ? `?role=${role}` : ''}`);
    return res.json();
  },
  
  getParcels: async (params: Record<string, string | boolean | undefined> = {}): Promise<Parcel[]> => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== '') {
        searchParams.append(key, String(val));
      }
    });
    const res = await fetch(`${API_BASE}/parcels?${searchParams.toString()}`);
    return res.json();
  },

  getParcelDetail: async (id: string): Promise<Parcel> => {
    const res = await fetch(`${API_BASE}/parcels/${id}`);
    if (!res.ok) throw new Error('Failed to fetch parcel detail');
    return res.json();
  },

  toggleListing: async (parcelId: string, isForSale: boolean, listingPriceLakhs?: number, actorName?: string) => {
    const res = await fetch(`${API_BASE}/parcels/${parcelId}/toggle-listing?actor_name=${encodeURIComponent(actorName || 'Citizen Landowner')}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_for_sale: isForSale, listing_price_lakhs: listingPriceLakhs })
    });
    return res.json();
  },

  getApplications: async (params: Record<string, string | boolean | undefined> = {}): Promise<ApplicationRecord[]> => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== '') {
        searchParams.append(key, String(val));
      }
    });
    const res = await fetch(`${API_BASE}/applications?${searchParams.toString()}`);
    return res.json();
  },

  getApplicationDetail: async (id: string): Promise<ApplicationRecord> => {
    const res = await fetch(`${API_BASE}/applications/${id}`);
    if (!res.ok) throw new Error('Failed to fetch application detail');
    return res.json();
  },

  submitApplication: async (payload: any, applicantId: string = 'usr_citizen_1'): Promise<ApplicationRecord> => {
    const res = await fetch(`${API_BASE}/applications?applicant_id=${applicantId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to submit application');
    }
    return res.json();
  },

  officerAction: async (applicationId: string, payload: any): Promise<ApplicationRecord> => {
    const res = await fetch(`${API_BASE}/applications/${applicationId}/officer-action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to execute officer action');
    }
    return res.json();
  },

  citizenCorrection: async (applicationId: string, payload: any, actorName: string): Promise<ApplicationRecord> => {
    const res = await fetch(`${API_BASE}/applications/${applicationId}/citizen-correction?actor_name=${encodeURIComponent(actorName)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to submit correction');
    }
    return res.json();
  },

  citizenAppeal: async (applicationId: string, appealRemarks: string, actorName: string): Promise<ApplicationRecord> => {
    const res = await fetch(`${API_BASE}/applications/${applicationId}/citizen-appeal?actor_name=${encodeURIComponent(actorName)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ appeal_remarks: appealRemarks })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to file appeal');
    }
    return res.json();
  },

  getLedgerBlocks: async (parcelId?: string): Promise<LedgerBlock[]> => {
    const res = await fetch(`${API_BASE}/ledger/blocks${parcelId ? `?parcel_id=${parcelId}` : ''}`);
    return res.json();
  },

  verifyLedgerChain: async () => {
    const res = await fetch(`${API_BASE}/ledger/verify-chain`);
    return res.json();
  },

  simulateTamper: async (blockIndex: number, field: string, value: string) => {
    const res = await fetch(`${API_BASE}/ledger/simulate-tamper`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        block_index: blockIndex,
        tampered_payload_field: field,
        fraudulent_value: value
      })
    });
    return res.json();
  },

  resetTamper: async () => {
    const res = await fetch(`${API_BASE}/ledger/reset-tamper`, { method: 'POST' });
    return res.json();
  },

  getAuditEvents: async (entityId?: string): Promise<AuditEvent[]> => {
    const res = await fetch(`${API_BASE}/audit-events${entityId ? `?entity_id=${entityId}` : ''}`);
    return res.json();
  },

  getOfficerStats: async (): Promise<OfficerStats> => {
    const res = await fetch(`${API_BASE}/stats/officer-dashboard`);
    return res.json();
  },

  getCitizenStats: async (userId: string) => {
    const res = await fetch(`${API_BASE}/stats/citizen-dashboard/${userId}`);
    return res.json();
  },

  getSlaRules: async () => {
    const res = await fetch(`${API_BASE}/config/sla-rules`);
    return res.json();
  },

  // ==================== AI TOOL 1: DOCUMENT VERIFICATION ====================
  getDocumentPresets: async (): Promise<any[]> => {
    const res = await fetch(`${API_BASE}/ai/documents/presets`);
    return res.json();
  },

  uploadDocument: async (file: File, docTypeHint?: string): Promise<ParsedDocument> => {
    const formData = new FormData();
    formData.append('file', file);
    const url = `${API_BASE}/ai/documents/upload${docTypeHint ? `?doc_type_hint=${encodeURIComponent(docTypeHint)}` : ''}`;
    const res = await fetch(url, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to upload and extract document');
    }
    return res.json();
  },

  compareDocuments: async (doc1: ParsedDocument, doc2: ParsedDocument): Promise<ComparisonResult> => {
    const res = await fetch(`${API_BASE}/ai/documents/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ doc1, doc2 })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to compare documents');
    }
    return res.json();
  },

  // ==================== AI TOOL 2: LAND RISK ASSESSMENT ====================
  performRiskAssessment: async (
    documents: any[],
    discrepancies?: any[],
    parcelId?: string,
    userDeclaredData?: any
  ): Promise<RiskAssessmentResult> => {
    const res = await fetch(`${API_BASE}/ai/risk-assessment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        documents,
        discrepancies,
        parcel_id: parcelId,
        user_declared_data: userDeclaredData
      })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to evaluate land risk');
    }
    return res.json();
  },

  assessParcelRisk: async (parcelId: string): Promise<RiskAssessmentResult> => {
    const res = await fetch(`${API_BASE}/ai/risk-assessment/parcel/${encodeURIComponent(parcelId)}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to evaluate parcel risk');
    }
    return res.json();
  },

  // ==================== AI TOOL 3: ADMINISTRATIVE DELAYS ====================
  getDelayAnalytics: async (
    appType?: string,
    status?: string,
    department?: string
  ): Promise<DelayAnalyticsResult> => {
    const params = new URLSearchParams();
    if (appType && appType !== 'ALL') params.append('application_type', appType);
    if (status && status !== 'ALL') params.append('status', status);
    if (department && department !== 'ALL') params.append('department', department);

    const url = `${API_BASE}/analytics/administrative-delays${params.toString() ? `?${params.toString()}` : ''}`;
    const res = await fetch(url);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to fetch delay analytics');
    }
    return res.json();
  },

  getDelayCases: async (status?: string, department?: string): Promise<any[]> => {
    const params = new URLSearchParams();
    if (status && status !== 'ALL') params.append('status', status);
    if (department && department !== 'ALL') params.append('department', department);

    const url = `${API_BASE}/analytics/administrative-delays/cases${params.toString() ? `?${params.toString()}` : ''}`;
    const res = await fetch(url);
    return res.json();
  }
};

// ==================== AI FEATURES INTERFACES ====================

export interface DocumentFields {
  doc_type: string;
  document_ref_no?: string;
  state?: string;
  district?: string;
  tehsil?: string;
  village?: string;
  khata_no?: string;
  khasra_no?: string;
  plot_no?: string;
  owner_names: string[];
  party_names?: string[];
  land_area?: number;
  area_unit?: string;
  normalized_area_sqft?: number;
  transaction_date?: string;
  mutation_status?: string;
  issuing_authority?: string;
  extraction_confidence: number;
  field_provenance?: Record<string, string>;
}

export interface ParsedDocument {
  title: string;
  file_name: string;
  doc_type: string;
  file_size_kb?: number;
  sha256_hash?: string;
  raw_text?: string;
  extraction_method?: string;
  ocr_available?: boolean;
  status?: string;
  warnings?: string[];
  fields: DocumentFields;
}

export interface DocumentDiscrepancy {
  field: string;
  field_label: string;
  severity: 'CRITICAL' | 'SIGNIFICANT_DISCREPANCY' | 'POSSIBLE_DISCREPANCY' | 'MINOR_VARIATION' | 'LOW';
  doc1_title: string;
  doc1_value: string;
  doc1_provenance?: string;
  doc2_title: string;
  doc2_value: string;
  doc2_provenance?: string;
  description: string;
  impact: string;
  recommended_action: string;
  uncertainty?: string;
}

export interface ComparisonResult {
  overall_consistent: boolean;
  discrepancy_count: number;
  significant_count: number;
  minor_count: number;
  consistent_field_count: number;
  missing_field_count: number;
  discrepancies: DocumentDiscrepancy[];
  consistent_fields: Array<{ field: string; field_label: string; doc1_value: string; doc2_value: string; status: string }>;
  missing_fields: Array<{ field: string; field_label: string; missing_in: string }>;
  explanation: {
    explanation_text: string;
    is_ai_generated: boolean;
    provider: string;
  };
  provider: string;
}

export interface RiskFactor {
  factor_id: string;
  factor_name: string;
  category: string;
  severity: string;
  score_contribution: number;
  evidence: string;
  significance: string;
  action: string;
}

export interface RiskAssessmentResult {
  risk_score: number;
  risk_category: string;
  risk_level_code: 'LOW_RISK' | 'MODERATE_RISK' | 'HIGH_RISK' | 'INSUFFICIENT_DATA';
  completeness_percentage: number;
  is_sufficient_evidence: boolean;
  documents_evaluated_count: number;
  discrepancies_evaluated_count: number;
  evaluated_factors: RiskFactor[];
  information_gaps: Array<{ item: string; description: string; impact: string }>;
  recommended_actions: string[];
  explanation: {
    explanation_text: string;
    is_ai_generated: boolean;
    provider: string;
  };
  provider: string;
  parcel_details?: any;
  disclaimer: string;
}

export interface StageDelayMetric {
  stage_order: number;
  stage_name: string;
  department: string;
  statutory_sla_days: number;
  avg_duration_days: number;
  median_duration_days: number;
  duration_variance_vs_sla: number;
  pending_count: number;
  breach_count: number;
  rejection_count: number;
  is_delayed: boolean;
}

export interface BottleneckAlert {
  stage_name: string;
  department: string;
  severity: string;
  finding: string;
  likely_cause: string;
  recommended_remedy: string;
}

export interface DelayAnalyticsResult {
  summary: {
    total_applications: number;
    pending_applications: number;
    completed_applications: number;
    rejected_applications: number;
    sla_breached_count: number;
    sla_breach_rate_pct: number;
    avg_completion_days: number;
    median_completion_days: number;
    avg_pending_age_days: number;
  };
  stages: StageDelayMetric[];
  bottlenecks: BottleneckAlert[];
  application_type_breakdown: Record<string, number>;
  status_breakdown: Record<string, number>;
  records: any[];
  ai_insights: {
    insights_text: string;
    is_ai_generated: boolean;
    provider: string;
  };
  provider: string;
  data_source_label: string;
  calculation_timestamp: string;
}

