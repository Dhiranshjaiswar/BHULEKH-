'use client';

import React, { useState, useEffect } from 'react';
import { 
  User, Parcel, ApplicationRecord, LedgerBlock, AuditEvent, OfficerStats, api,
  ParsedDocument, DocumentDiscrepancy
} from '@/lib/api';
import { Header } from '@/components/Header';
import { CadastralMap } from '@/components/CadastralMap';
import { CitizenPortal } from '@/components/CitizenPortal';
import { OfficerQueue } from '@/components/OfficerQueue';
import { PublicRegistry } from '@/components/PublicRegistry';
import { BlockchainLedger } from '@/components/BlockchainLedger';
import { AuditTrail } from '@/components/AuditTrail';
import { DocumentVerification } from '@/components/DocumentVerification';
import { RiskAssessment } from '@/components/RiskAssessment';
import { DelayAnalytics } from '@/components/DelayAnalytics';
import { Landmark, Shield, Lock, ExternalLink, Cpu } from 'lucide-react';

export default function Home() {
  const [users, setUsers] = useState<User[]>([]);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [parcels, setParcels] = useState<Parcel[]>([]);
  const [selectedParcel, setSelectedParcel] = useState<Parcel | null>(null);
  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [ledgerBlocks, setLedgerBlocks] = useState<LedgerBlock[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [officerStats, setOfficerStats] = useState<OfficerStats | null>(null);
  const [activeTab, setActiveTab] = useState<string>('gis-map');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [forwardedDocs, setForwardedDocs] = useState<ParsedDocument[]>([]);
  const [forwardedDiscrepancies, setForwardedDiscrepancies] = useState<DocumentDiscrepancy[]>([]);

  const handleForwardToRiskAssessment = (docs: ParsedDocument[], discrepancies: DocumentDiscrepancy[]) => {
    setForwardedDocs(docs);
    setForwardedDiscrepancies(discrepancies);
    setActiveTab('ai-risk-assessment');
  };

  const loadData = async () => {
    try {
      setBackendError(null);
      const [uList, pList, aList, bList, evList, oStats] = await Promise.all([
        api.getUsers(),
        api.getParcels(),
        api.getApplications(),
        api.getLedgerBlocks(),
        api.getAuditEvents(),
        api.getOfficerStats()
      ]);

      setUsers(uList);
      if (!currentUser && uList.length > 0) {
        // Default to Rajesh Sharma (Citizen) or first user
        const defaultUser = uList.find(u => u.username === 'rajesh_sharma') || uList[0];
        setCurrentUser(defaultUser);
      }
      setParcels(pList);
      setApplications(aList);
      setLedgerBlocks(bList);
      setAuditEvents(evList);
      setOfficerStats(oStats);
    } catch (err: any) {
      console.error('Error fetching data from backend API:', err);
      setBackendError('Backend API (http://localhost:8000) is unreachable. The Cadastral Map and application services require the local FastAPI server to be running.');
    } finally {
      setIsLoading(false);
    }
  };

  const loadOfflineDemoMode = () => {
    const demoUser: User = {
      id: 'usr_citizen_1',
      username: 'rajesh_sharma',
      full_name: 'Rajesh Kumar Sharma',
      email: 'rajesh.sharma@example.gov.in',
      role: 'CITIZEN',
      department: 'Citizen (Landowner)',
      phone_masked: '+91 98XXX-XX101',
      aadhaar_masked: 'XXXX-XXXX-4589',
      pan_masked: 'ABFPS4589K'
    };

    const demoParcels: Parcel[] = [
      {
        id: 'UP-GZB-IND-00012345',
        ulin_pin: 'UP08GZB012345',
        state: 'Uttar Pradesh',
        revenue_authority: 'Board of Revenue, Uttar Pradesh',
        district: 'Ghaziabad',
        tehsil: 'Modinagar',
        village: 'Muradnagar',
        khasra_no: '142/1',
        khata_no: '00412',
        land_use: 'Residential',
        area_sqft: 4850.0,
        area_sqm: 450.58,
        area_local_unit: '0.11 Acres / 538.8 Sq Yd',
        circle_rate_sqft_2026: 2600.0,
        circle_rate_2026: 28000.0,
        circle_rate_2025: 24500.0,
        circle_rate_2024: 21000.0,
        estimated_govt_value_lakhs: 126.1,
        formatted_value_str: '₹1.26 Crores',
        current_owner_id: 'usr_citizen_1',
        current_owner_name: 'Rajesh Kumar Sharma',
        ownership_status: 'Statutorily Verified',
        is_for_sale: false,
        is_disputed: false,
        is_mortgaged: false,
        tax_cleared: true,
        boundary_verified: true,
        risk_rating: 'LOW_RISK',
        centroid_lat: 28.7750,
        centroid_lng: 77.5020,
        geometry_geojson: JSON.stringify({
          type: "Polygon",
          coordinates: [[
            [77.5000, 28.7735],
            [77.5040, 28.7738],
            [77.5042, 28.7765],
            [77.5002, 28.7762],
            [77.5000, 28.7735]
          ]]
        })
      },
      {
        id: 'UP-GZB-IND-00012346',
        ulin_pin: 'UP08GZB012346',
        state: 'Uttar Pradesh',
        revenue_authority: 'Board of Revenue, Uttar Pradesh',
        district: 'Ghaziabad',
        tehsil: 'Modinagar',
        village: 'Muradnagar',
        khasra_no: '142/2',
        khata_no: '00412',
        land_use: 'Commercial',
        area_sqft: 10890.0,
        area_sqm: 1011.7,
        area_local_unit: '0.25 Acres / 1.5 Bigha',
        circle_rate_sqft_2026: 4200.0,
        circle_rate_2026: 45200.0,
        circle_rate_2025: 39500.0,
        circle_rate_2024: 34000.0,
        estimated_govt_value_lakhs: 457.38,
        formatted_value_str: '₹4.57 Crores',
        current_owner_id: 'usr_citizen_1',
        current_owner_name: 'Rajesh Kumar Sharma',
        ownership_status: 'Statutorily Verified',
        is_for_sale: true,
        listing_price_lakhs: 495.0,
        is_disputed: false,
        is_mortgaged: false,
        tax_cleared: true,
        boundary_verified: true,
        risk_rating: 'LOW_RISK',
        centroid_lat: 28.7780,
        centroid_lng: 77.5050,
        geometry_geojson: JSON.stringify({
          type: "Polygon",
          coordinates: [[
            [77.5030, 28.7765],
            [77.5070, 28.7768],
            [77.5072, 28.7795],
            [77.5032, 28.7792],
            [77.5030, 28.7765]
          ]]
        })
      }
    ];

    setUsers([demoUser]);
    setCurrentUser(demoUser);
    setParcels(demoParcels);
    setBackendError(null);
  };

useEffect(() => {
  loadData();

  // Temporarily disabled to test the Risk Assessment refresh.
  // const interval = setInterval(loadData, 10000);
  // return () => clearInterval(interval);
}, []);


  const handleSelectUser = (u: User) => {
    setCurrentUser(u);
    if (u.role === 'CITIZEN') {
      setActiveTab('citizen-portal');
    } else {
      setActiveTab('officer-queue');
    }
  };

  const handleSelectParcelForMap = (p: Parcel) => {
    setSelectedParcel(p);
    setActiveTab('gis-map');
  };

  const handleToggleSaleListing = async (p: Parcel, isForSale: boolean, price?: number) => {
    if (!currentUser) return;
    try {
      await api.toggleListing(p.id, isForSale, price, currentUser.full_name);
      await loadData();
      if (selectedParcel?.id === p.id) {
        const updated = await api.getParcelDetail(p.id);
        setSelectedParcel(updated);
      }
    } catch (e: any) {
      alert(`Error toggling listing: ${e.message}`);
    }
  };

  const handleInitiateTransfer = (p: Parcel) => {
    setActiveTab('citizen-portal');
  };

  if (backendError && !currentUser) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl border border-slate-200 p-6 space-y-4 text-center">
          <div className="w-12 h-12 rounded-xl bg-amber-100 border border-amber-300 text-amber-800 flex items-center justify-center mx-auto">
            <Landmark className="w-6 h-6 text-[#0a2540]" />
          </div>
          <div className="space-y-1">
            <h2 className="text-base font-extrabold text-[#0a2540]">Backend API Connection Required</h2>
            <p className="text-xs text-slate-600 leading-relaxed">
              The Cadastral Map loads parcel GIS coordinates and title records from the local FastAPI backend (<code className="font-mono bg-slate-100 px-1 py-0.5 rounded text-[11px]">http://localhost:8000/api</code>).
            </p>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-left text-xs space-y-1.5 font-mono">
            <span className="text-[10px] uppercase font-bold text-slate-500 font-sans block">Start Backend Command:</span>
            <div className="text-slate-800 bg-white p-2 rounded border border-slate-200 select-all text-[11px]">
              cd backend<br />
              python seed_data.py<br />
              python -m uvicorn main:app --port 8000 --reload
            </div>
          </div>

          <div className="pt-2 flex flex-col gap-2">
            <button
              onClick={() => {
                setIsLoading(true);
                loadData();
              }}
              className="w-full py-2.5 rounded-lg bg-[#0a2540] hover:bg-slate-800 text-white text-xs font-bold transition shadow-sm"
            >
              Retry Connection
            </button>
            <button
              onClick={loadOfflineDemoMode}
              className="w-full py-2 rounded-lg bg-amber-50 hover:bg-amber-100 border border-amber-300 text-amber-900 text-xs font-bold transition"
            >
              Preview Map in Offline Demo Mode
            </button>
          </div>

          <p className="text-[10px] text-slate-400">
            Note: No external map API key is needed. The map uses open-source OpenStreetMap, CartoDB, and Esri Satellite basemaps.
          </p>
        </div>
      </div>
    );
  }

  if (isLoading || !currentUser) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center space-y-4">
        <div className="w-14 h-14 bg-slate-200 border-2 border-slate-300 rounded-xl flex flex-col items-center justify-center p-1 animate-pulse">
          <Landmark className="w-8 h-8 text-[#0a2540]" />
        </div>
        <div className="text-center space-y-1">
          <h2 className="text-base font-extrabold text-[#0a2540] tracking-tight">BHULEKH LEDGER</h2>
          <p className="text-xs text-slate-500 font-medium">Connecting to National Cadastral Node & Sovereign Blockchain...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col justify-between">
      
      {/* Header */}
      <Header
        currentUser={currentUser}
        onSelectUser={handleSelectUser}
        users={users}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex-1 w-full">
        {activeTab === 'gis-map' && (
          <CadastralMap
            parcels={parcels}
            selectedParcel={selectedParcel}
            onSelectParcel={setSelectedParcel}
            currentUser={currentUser}
            onInitiateTransfer={handleInitiateTransfer}
            onToggleSaleListing={handleToggleSaleListing}
            onAssessRisk={(p) => {
              setSelectedParcel(p);
              setActiveTab('ai-risk-assessment');
            }}
          />
        )}

        {activeTab === 'citizen-portal' && (
          <CitizenPortal
            currentUser={currentUser}
            parcels={parcels}
            applications={applications}
            onSelectParcelForMap={handleSelectParcelForMap}
            onRefreshData={loadData}
          />
        )}

        {activeTab === 'officer-queue' && (
          <OfficerQueue
            currentUser={currentUser}
            applications={applications}
            stats={officerStats}
            onRefreshData={loadData}
            onOpenDelayAnalytics={() => setActiveTab('ai-delay-analytics')}
          />
        )}

        {activeTab === 'ai-doc-verify' && (
          <DocumentVerification
            onForwardToRiskAssessment={handleForwardToRiskAssessment}
          />
        )}

        {activeTab === 'ai-risk-assessment' && (
          <RiskAssessment
            initialDocs={forwardedDocs}
            initialDiscrepancies={forwardedDiscrepancies}
            parcels={parcels}
          />
        )}

        {activeTab === 'ai-delay-analytics' && (
          <DelayAnalytics />
        )}

        {activeTab === 'public-registry' && (
          <PublicRegistry
            parcels={parcels}
            onSelectParcelForMap={handleSelectParcelForMap}
          />
        )}

        {activeTab === 'blockchain-ledger' && (
          <BlockchainLedger
            blocks={ledgerBlocks}
            onRefreshData={loadData}
          />
        )}

        {activeTab === 'audit-trail' && (
          <AuditTrail
            events={auditEvents}
            onRefresh={loadData}
          />
        )}
      </main>

      {/* Official Government Footer */}
      <footer className="bg-slate-900 text-slate-300 text-xs border-t-4 border-[#FF9933] mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 border-b border-slate-800 pb-6">
            
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Landmark className="w-5 h-5 text-amber-400" />
                <span className="font-extrabold text-white text-sm">BHULEKH LEDGER</span>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                National Digital Land Governance & Sovereign Ownership Infrastructure (DLRP-2026). Developed in collaboration with the Department of Land Resources & NIC.
              </p>
            </div>

            <div className="space-y-1 text-[11px]">
              <span className="font-bold text-white uppercase tracking-wider block mb-2">Statutory Principles</span>
              <p className="text-slate-400">✓ Authoritative Government Clearance as Legal Truth</p>
              <p className="text-slate-400">✓ Off-Chain PII Isolation (No Aadhaar On-Chain)</p>
              <p className="text-slate-400">✓ Public Services Guarantee SLA Compliance</p>
              <p className="text-slate-400">✓ Cryptographic SHA-256 Tamper Proofs</p>
            </div>

            <div className="space-y-1 text-[11px]">
              <span className="font-bold text-white uppercase tracking-wider block mb-2">Government Portals</span>
              <p className="text-slate-400 hover:text-white cursor-pointer">Digital India Land Record Modernization (DILRMP)</p>
              <p className="text-slate-400 hover:text-white cursor-pointer">Unique Land Parcel Identification Number (ULPIN / Bhu-Aadhaar)</p>
              <p className="text-slate-400 hover:text-white cursor-pointer">National Generic Document Registration System (NGDRS)</p>
              <p className="text-slate-400 hover:text-white cursor-pointer">National Judicial Data Grid (e-Courts NJDG)</p>
            </div>

            <div className="space-y-2 text-[11px]">
              <span className="font-bold text-white uppercase tracking-wider block mb-2">Legal Disclaimer</span>
              <p className="text-slate-400 leading-relaxed">
                This prototype application is designed for administrative proof-of-concept purposes. All names, parcel identifiers, and cadastral boundaries displayed are fictional demonstration data.
              </p>
            </div>

          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between text-[10px] text-slate-500 gap-2">
            <div>
              © 2026 Ministry of Rural Development & National Informatics Centre (NIC). All Rights Reserved.
            </div>
            <div className="flex items-center gap-4">
              <span>Security Audited (CERT-In Standard)</span>
              <span>•</span>
              <span>W3C WCAG 2.1 AAA Compliant</span>
              <span>•</span>
              <span className="font-mono">Node ID: NIC-DLRP-NODE-01</span>
            </div>
          </div>

        </div>
      </footer>

    </div>
  );
}
