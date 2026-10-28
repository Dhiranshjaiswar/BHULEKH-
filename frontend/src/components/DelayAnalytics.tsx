'use client';

import React, { useState, useEffect } from 'react';
import { 
  Clock, AlertTriangle, TrendingUp, CheckCircle, Filter, Sparkles, 
  RefreshCw, Building2, BarChart2, ShieldAlert, ArrowRight, UserCheck, Layers, Info
} from 'lucide-react';
import { 
  api, DelayAnalyticsResult, StageDelayMetric, BottleneckAlert 
} from '@/lib/api';

export const DelayAnalytics: React.FC = () => {
  const [analytics, setAnalytics] = useState<DelayAnalyticsResult | null>(null);
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [selectedDept, setSelectedDept] = useState<string>('ALL');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'stages' | 'cases'>('overview');

  const loadAnalytics = async () => {
    setIsLoading(true);
    try {
      const data = await api.getDelayAnalytics(selectedType, selectedStatus, selectedDept);
      setAnalytics(data);
    } catch (err: any) {
      console.error('Error fetching delay analytics:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, [selectedType, selectedStatus, selectedDept]);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-medium">Public Service Guarantee SLA Analytics</span>
            </div>
            <h2 className="text-xl font-extrabold text-[#0a2540] tracking-tight flex items-center gap-2">
              <Clock className="w-6 h-6 text-indigo-600" />
              AI-Powered Administrative Delay Analysis
            </h2>
            <p className="text-xs text-slate-600 leading-relaxed max-w-3xl">
              Pinpoint statutory workflow bottlenecks across Revenue, Cadastral Survey, Legal Liaison, and Registration departments.
              Tracks turnaround distributions, overdue cases, and departmental throughput under the Right to Public Services Act.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={loadAnalytics}
              disabled={isLoading}
              className="px-3.5 py-2 rounded-lg bg-[#0a2540] text-white text-xs font-bold flex items-center gap-1.5 shadow-sm hover:bg-slate-800 transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh Analytics
            </button>
          </div>
        </div>

        {/* Demonstration Dataset Notice */}
        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center gap-2 text-[11px] text-amber-900 bg-amber-50/70 p-2.5 rounded-lg border border-amber-200">
          <Info className="w-4 h-4 text-amber-600 shrink-0" />
          <span>
            <strong>Demonstration Dataset Notice:</strong> Workflow metrics synthesize live platform applications combined with 
            clearly labeled synthetic demonstration cases to illustrate multi-departmental bottlenecks without disclosing real citizens' pending matters.
          </span>
        </div>
      </div>

      {/* Filter Controls Bar */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-700">
            <Filter className="w-4 h-4 text-indigo-600" />
            <span>Workflow Filters:</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 flex-1 max-w-3xl">
            {/* Application Type */}
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold bg-slate-50 text-slate-800"
            >
              <option value="ALL">All Application Types</option>
              <option value="SALE_DEED_MUTATION">Sale Deed Mutation</option>
              <option value="INHERITANCE_MUTATION">Inheritance Mutation (Varisat)</option>
              <option value="GIFT_DEED_MUTATION">Gift Deed Mutation</option>
              <option value="PARTITION_MUTATION">Partition / Batwara</option>
            </select>

            {/* Status */}
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold bg-slate-50 text-slate-800"
            >
              <option value="ALL">All Statuses</option>
              <option value="UNDER_REVIEW">Pending Under Review</option>
              <option value="APPROVED">Completed / Approved</option>
              <option value="REJECTED">Statutorily Rejected</option>
            </select>

            {/* Department */}
            <select
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
              className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold bg-slate-50 text-slate-800"
            >
              <option value="ALL">All Departments</option>
              <option value="Revenue Department">Revenue Department</option>
              <option value="Department of Land Records & Survey">Cadastral GIS Survey</option>
              <option value="Legal Cell / e-Courts Liaison">Legal Cell & e-Courts</option>
              <option value="Registration & Stamps Department">Sub-Registrar (SRO)</option>
              <option value="Sub-Divisional Magistrate Office">SDM Office</option>
            </select>
          </div>
        </div>
      </div>

      {isLoading || !analytics ? (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center space-y-3">
          <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mx-auto" />
          <h3 className="text-sm font-bold text-slate-800">Calculating Administrative Metrics & Cycle Times...</h3>
        </div>
      ) : (
        <div className="space-y-6 animate-in fade-in duration-200">
          
          {/* Top KPI Cards Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            
            {/* Total Cases */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                Total Evaluated Cases
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-[#0a2540]">
                  {analytics.summary.total_applications}
                </span>
                <span className="text-[11px] text-slate-500 font-medium">applications</span>
              </div>
              <span className="text-[10px] text-slate-400 block pt-1 border-t border-slate-100">
                {analytics.summary.completed_applications} completed • {analytics.summary.pending_applications} in pipeline
              </span>
            </div>

            {/* Average Turnaround (Completed) */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                Completed Processing Time
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-blue-700">
                  {analytics.summary.avg_completion_days}
                </span>
                <span className="text-xs text-slate-600 font-bold">days (avg)</span>
              </div>
              <span className="text-[10px] text-slate-500 block pt-1 border-t border-slate-100">
                Median turnaround: <strong>{analytics.summary.median_completion_days} days</strong>
              </span>
            </div>

            {/* Pending Backlog & Age */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                Active Pending Backlog
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-amber-700">
                  {analytics.summary.pending_applications}
                </span>
                <span className="text-xs text-slate-600 font-bold">cases</span>
              </div>
              <span className="text-[10px] text-slate-500 block pt-1 border-t border-slate-100">
                Avg age of pending cases: <strong>{analytics.summary.avg_pending_age_days} days</strong>
              </span>
            </div>

            {/* SLA Breaches & Rate */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                SLA Breached Cases
              </span>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-red-700">
                  {analytics.summary.sla_breached_count}
                </span>
                <span className="text-xs text-red-800 font-bold bg-red-100 px-1.5 py-0.5 rounded">
                  {analytics.summary.sla_breach_rate_pct}% Breach Rate
                </span>
              </div>
              <span className="text-[10px] text-slate-500 block pt-1 border-t border-slate-100">
                Statutory escalation triggered to SDM
              </span>
            </div>

          </div>

          {/* AI Grounded Administrative Insights */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-600" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900">
                  Grounded Administrative Insights & Reforms
                </h4>
              </div>
              <span
                className={`text-[10px] px-2 py-0.5 rounded font-bold border ${
                  analytics.ai_insights?.is_ai_generated
                    ? 'bg-purple-50 text-purple-800 border-purple-200'
                    : 'bg-slate-100 text-slate-700 border-slate-300'
                }`}
              >
                {analytics.ai_insights?.is_ai_generated
                  ? `AI Insights (${analytics.ai_insights?.provider || 'Gemini'})`
                  : 'Deterministic Administrative Rule Engine'}
              </span>
            </div>

            <div className="prose prose-xs max-w-none text-slate-700 leading-relaxed font-sans text-xs whitespace-pre-line bg-slate-50/60 p-4 rounded-lg border border-slate-100">
              {analytics.ai_insights?.insights_text}
            </div>
          </div>

          {/* Identified Bottlenecks Alert Cards */}
          {analytics.bottlenecks.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-600" />
                Critical Departmental Bottlenecks Identified ({analytics.bottlenecks.length})
              </h4>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {analytics.bottlenecks.map((b, bIdx) => (
                  <div
                    key={bIdx}
                    className="p-4 rounded-xl border border-red-200 bg-red-50/40 space-y-2 text-xs"
                  >
                    <div className="flex items-center justify-between border-b border-red-200/60 pb-2">
                      <span className="font-extrabold text-red-950">{b.stage_name}</span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded uppercase bg-red-100 text-red-900 border border-red-300">
                        {b.severity.replace(/_/g, ' ')}
                      </span>
                    </div>

                    <p className="text-slate-800">
                      <strong>Observed Pattern:</strong> {b.finding}
                    </p>
                    <p className="text-slate-600">
                      <strong>Probable Cause:</strong> {b.likely_cause}
                    </p>
                    <div className="pt-2 border-t border-red-200/40 text-blue-900 font-medium">
                      <strong>Administrative Intervention:</strong> {b.recommended_remedy}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Departmental Stage Throughput Table */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-indigo-600" />
                Departmental Stage Cycle-Time vs Statutory SLA Limits
              </h4>
              <span className="text-[10px] text-slate-500 font-medium">
                Public Services Guarantee Benchmark
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 font-bold uppercase text-[10px]">
                    <th className="py-2.5 px-3">Stage #</th>
                    <th className="py-2.5 px-3">Stage Name & Department</th>
                    <th className="py-2.5 px-3">Statutory SLA</th>
                    <th className="py-2.5 px-3">Observed Average</th>
                    <th className="py-2.5 px-3">Duration Variance</th>
                    <th className="py-2.5 px-3">Active Backlog</th>
                    <th className="py-2.5 px-3">SLA Breaches</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {analytics.stages.map((st) => (
                    <tr key={st.stage_order} className="hover:bg-slate-50 transition">
                      <td className="py-3 px-3 font-mono font-bold text-slate-400">
                        0{st.stage_order + 1}
                      </td>
                      <td className="py-3 px-3">
                        <span className="font-bold text-slate-900 block">{st.stage_name}</span>
                        <span className="text-[10px] text-slate-500">{st.department}</span>
                      </td>
                      <td className="py-3 px-3 font-semibold text-slate-700">
                        {st.statutory_sla_days} days
                      </td>
                      <td className="py-3 px-3 font-bold text-slate-900">
                        <div className="flex items-center gap-2">
                          <span>{st.avg_duration_days} days</span>
                          <div className="w-16 bg-slate-100 rounded-full h-1.5 hidden sm:block">
                            <div
                              className={`h-1.5 rounded-full ${st.is_delayed ? 'bg-red-500' : 'bg-emerald-500'}`}
                              style={{ width: `${Math.min(100, (st.avg_duration_days / st.statutory_sla_days) * 75)}%` }}
                            ></div>
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-3">
                        {st.duration_variance_vs_sla > 0 ? (
                          <span className="text-red-700 font-bold bg-red-50 px-2 py-0.5 rounded text-[10px] border border-red-200">
                            +{st.duration_variance_vs_sla} days OVER
                          </span>
                        ) : (
                          <span className="text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded text-[10px] border border-emerald-200">
                            {st.duration_variance_vs_sla} days (On Track)
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-3 font-semibold text-slate-800">
                        {st.pending_count} cases
                      </td>
                      <td className="py-3 px-3">
                        {st.breach_count > 0 ? (
                          <span className="text-red-700 font-bold">
                            ⚠ {st.breach_count} breached
                          </span>
                        ) : (
                          <span className="text-slate-400">0</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Drill-down Application Cases Table */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-600" />
                Underlying Administrative Cases ({analytics.records.length})
              </h4>
              <span className="text-[10px] text-slate-500">
                Sorted by submission timestamp
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 font-bold uppercase text-[10px]">
                    <th className="py-2.5 px-3">Application ID</th>
                    <th className="py-2.5 px-3">Type</th>
                    <th className="py-2.5 px-3">District</th>
                    <th className="py-2.5 px-3">Current Department / Stage</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Total Days</th>
                    <th className="py-2.5 px-3">SLA Flag</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {analytics.records.slice(0, 15).map((r, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 transition">
                      <td className="py-2.5 px-3 font-mono font-bold text-slate-800">
                        {r.id}
                        {r.is_synthetic_demo && (
                          <span className="ml-1 text-[9px] bg-slate-100 text-slate-500 px-1 py-0.2 rounded font-sans font-normal">
                            demo
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-slate-700">
                        {r.application_type?.replace(/_/g, ' ')}
                      </td>
                      <td className="py-2.5 px-3 text-slate-600 font-medium">
                        {r.district}
                      </td>
                      <td className="py-2.5 px-3">
                        <span className="font-semibold text-slate-800 block">{r.current_stage_name}</span>
                        <span className="text-[10px] text-slate-400">{r.current_department}</span>
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                            r.status === 'APPROVED'
                              ? 'bg-emerald-100 text-emerald-800'
                              : r.status === 'REJECTED'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          {r.status?.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono font-semibold text-slate-800">
                        {r.total_turnaround_days}d
                      </td>
                      <td className="py-2.5 px-3">
                        {r.is_sla_breached ? (
                          <span className="text-red-700 font-bold text-[10px] bg-red-50 border border-red-200 px-1.5 py-0.5 rounded">
                            ⚠ BREACHED
                          </span>
                        ) : (
                          <span className="text-emerald-700 font-semibold text-[10px]">
                            ✓ Compliant
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      )}
    </div>
  );
};
