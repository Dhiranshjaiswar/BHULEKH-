<<<<<<< HEAD
# BHULEKH (भूलेख) — AI-Powered Land Intelligence Platform
### Sovereign Digital Land Governance, Evidence-Based Risk Assessment & Administrative Delay Analytics

A comprehensive digital land governance platform upgraded with three practical, production-ready AI tools for the Indian land records ecosystem (DILRMP / ULPIN Bhu-Aadhaar).

---

## 1. What BHULEKH Does

BHULEKH transforms traditional land records into an intelligent, verifiable governance platform. It unites:
- **Statutory Source of Truth**: Government revenue authorities and registration officers remain the legal authority of title; cryptographic ledger blocks provide tamper-evident provenance.
- **Cadastral GIS Mapping**: Interactive GeoJSON parcels with Circle Rate valuation calculations (`Area × Circle Rate`).
- **Statutory Workflow & Public Services SLA**: 5-stage administrative clearance pipeline with automated SLA breach detection and escalation under the Right to Public Services Act.
- **Privacy by Design**: Off-chain storage of PII and raw documents; cryptographic SHA-256 fingerprints recorded on-ledger.

---

## 2. The Three New AI Features

### 🔍 Tool 1: AI Land Document Verification & Discrepancy Detection
- **Multi-Format Ingestion**: Supports PDF documents, JPG, JPEG, and PNG deed scans.
- **Text & OCR Pipeline**: Direct digital text extraction via `pypdf`; OCR fallback via `pytesseract` / PIL for scanned deeds with transparent status reporting when host OCR binaries are unavailable.
- **Structured Field Extraction**: Extracts Khasra/Survey numbers, Khata holding numbers, Plot numbers, recorded owner names, transaction dates, and land area across Indian units (Sq. Ft., Sq. M., Acres, Bigha, Guntas, Hectares).
- **Deterministic Discrepancy Engine**:
  - Reconciles and normalizes all land areas into square feet before comparison.
  - Compares owner names with token similarity to differentiate minor spelling variations from material party divergence.
  - Classifies findings as `CONSISTENT`, `MINOR_VARIATION`, `POSSIBLE_DISCREPANCY`, or `SIGNIFICANT_DISCREPANCY`.
  - Pinpoints source provenance and exact character snippets for each finding.
- **Review & Correction Interface**: Allows citizens or revenue officers to review and edit extracted fields before running cross-comparison.
- **Grounded Narrative & Reports**: Explains findings strictly using observed facts; downloadable JSON audit report.

### 🛡️ Tool 2: Evidence-Based AI Land Risk Assessment
- **Deterministic 100-Point Scoring Engine**: Transparent, reproducible scoring methodology based on defined statutory weights rather than opaque LLM guesses.
- **Evaluated Factor Categories**:
  1. *Title Integrity & Discrepancies* (Owner name conflicts, Khasra mismatches).
  2. *Measurement Accuracy* (Material area divergence >5%).
  3. *Statutory Encumbrances* (Active e-Court civil disputes, active commercial bank liens).
  4. *Survey Demarcation* (Cadastral boundary unverified flags).
  5. *Completeness & Chain of Title* (Missing Khatauni extracts, isolated deeds).
- **Clear Classification Statuses**:
  - `Lower level of identified record-related concerns` (Score 0 - 25)
  - `Moderate level of identified record-related concerns` (Score 26 - 55)
  - `Higher level of identified record-related concerns` (Score 56 - 100)
  - `Insufficient information to assess` (When required key data is missing)
- **Honest Evidence Grounding**: Distinguishes between verified discrepancies, unverified data, and missing records.
- **Grounded AI Explanation**: Accessible summaries and prioritized due-diligence roadmaps.
- **Statutory Disclaimer**: Explicitly states that the tool does not replace official Revenue Court adjudication or a certified advocate title search.

### ⏱️ Tool 3: AI-Powered Administrative Delay Analysis
- **Turnaround Cycle-Time Metrics**: Computes average and median processing durations for completed applications, plus the average age of pending backlog.
- **Departmental Stage Throughput**: Evaluates cycle times against statutory deadlines across all 5 workflow departments:
  - Revenue Record & Jamabandi Verification (SLA: 7 days)
  - Cadastral Survey & Demarcation (SLA: 5 days)
  - Legal Dispute & e-Courts Liaison (SLA: 3 days)
  - Sub-Registrar Deed Registration (SLA: 4 days)
  - SDM Final Title Approval (SLA: 2 days)
- **Deterministic Bottleneck Detection**:
  - Flags stages with disproportionate pending queues (>35% of total backlog).
  - Pinpoints stages exceeding statutory SLA limits.
  - Highlights stages with high rejection ground clusters.
- **Actionable AI Administrative Insights**: Grounded executive reform recommendations to compress cycle times.
- **Illustrative Demonstration Dataset**: Incorporates platform cases along with a clearly designated synthetic demonstration dataset to showcase real-world bottlenecks.

---

## 3. Technology Stack

- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, Lucide Icons, Leaflet GIS, React-Leaflet
- **Backend**: Python 3.13 / 3.14, FastAPI, SQLAlchemy, SQLite, Pydantic v2
- **Document Processing**: `pypdf` (PDF digital text extraction), `Pillow` (image verification), `pytesseract` (OCR engine binding)
- **AI / LLM Integration**: Google Gemini (`google-generativeai`), OpenAI (`openai`), Groq, with high-quality deterministic fallback engines
- **Cryptography**: Standard SHA-256, Merkle Tree Root Computation, Simulated X.509 NIC DSC Digital Signatures

---

## 4. Environment Variables Configuration

Copy `.env.example` to create your local `.env`:

```bash
cp .env.example .env
```

### Supported Configuration Keys:

| Variable | Description | Default | Required? |
| :--- | :--- | :--- | :--- |
| `LLM_PROVIDER` | AI Provider: `gemini`, `openai`, `groq`, or `none` | `none` | Optional |
| `LLM_API_KEY` | Secret API key for the chosen LLM provider | `""` | Optional |
| `LLM_MODEL` | Custom model name (e.g. `gemini-1.5-flash`, `gpt-4o-mini`) | Provider default | Optional |
| `NEXT_PUBLIC_API_URL` | Frontend API endpoint URL | `http://localhost:8000/api` | Required for UI |

### Running 100% Without an LLM API Key:
If you do not configure an API key (`LLM_PROVIDER=none` or empty `LLM_API_KEY`), **BHULEKH runs completely offline and 100% usable!** The built-in deterministic rule engine produces comprehensive, legally grounded explanations, scoring results, and bottleneck insights without calling any external API.

---

## 5. Quick Start Instructions

### Prerequisites
- Python 3.10+ (tested on Python 3.13 and Python 3.14)
- Node.js 18+ and npm

### 1. Backend Setup & Launch

```bash
# Navigate to the backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Seed the database with sample parcels, users, applications, and blockchain genesis
python seed_data.py

# Start the FastAPI server
uvicorn main:app --port 8000 --reload
```

- **Backend API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### 2. Frontend Setup & Launch

In a separate terminal:

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the Next.js development server
npm run dev
```

- **Frontend Application**: [http://localhost:3000](http://localhost:3000)

---

## 6. Automated Testing

BHULEKH includes a complete test suite covering the original blockchain/SLA workflow alongside the three AI features.

Run the complete test suite:
```bash
cd backend
python -m pytest test_api.py test_ai_features.py -v
```

### Test Coverage Highlights:
- **Document Verification**: Unit conversion (Acres, Bigha, Guntas to Sqft), string similarity/transliteration, structured regex field extraction, deterministic consistency matching, Khasra and Area divergence detection, owner mismatch detection, and invalid upload handling.
- **Risk Assessment**: Low-risk consistent documents, high-risk litigated/discrepant documents, missing document handling, score boundaries, and input reproducibility.
- **Administrative Delays**: Average/median cycle times, stage duration metrics, bottleneck detection rules, status/type filters, and empty dataset handling.
- **Integration**: Health checks, parcel queries, tamper simulator, and API endpoints for all 3 AI tools.

---

## 7. Step-by-Step Demonstration Guide

### Demo Workflow 1: Document Verification & Discrepancy Detection
1. In the top navigation bar, click **"AI Doc Verification"**.
2. Click **"Scenario B: Khasra & Land Area Discrepancy"** from the Hackathon Demo Presets.
3. Review the two loaded documents: Conveyance Deed vs Mutation Order.
4. Click **"Run Discrepancy Analysis"**.
5. Observe:
   - Status alert highlighting identified discrepancies.
   - Grounded AI / Statutory narrative explaining that Khasra `142/1` diverges from `142/2` and land area diverges by 21%.
   - Detailed cards with exact provenance snippets, legal impacts, and recommended next steps.
6. Click **"Review / Edit"** on any document to test manual field correction, and observe the system re-evaluate.
7. Click **"Export Report (JSON)"** to download the structured verification report.

### Demo Workflow 2: Evidence-Based Land Risk Assessment
1. From the Document Verification screen, click **"Evaluate Land Risk"** (or click **"Land Risk Assessment"** in the top navigation bar).
2. The engine immediately evaluates the documents and discrepancies.
3. Observe:
   - Overall Risk Score (e.g. 70/100: Higher level of identified record-related concerns).
   - Evidence Completeness Meter (e.g. 75%).
   - Grounded Risk Explanation referencing the exact discrepancy factors.
   - Evaluated Risk Factor cards with points contribution (`+25 pts` Khasra mismatch, `+20 pts` Area divergence).
   - Information Gaps and Prioritized Due Diligence Roadmap.
4. Select a parcel from the dropdown (e.g. `UP-GZB-IND-00012345`) to assess risk on a clean registered parcel, and observe the score drop to **Low Risk (15/100)**!
5. Select a mortgaged or litigated parcel to observe how active court injunctions elevate the risk score.

### Demo Workflow 3: Administrative Delay Analytics
1. In the top navigation bar, click **"Delay Analytics"** (or click the shortcut from the Officer Task Queue).
2. Inspect the KPI cards: Total applications, Average turnaround (days), Active pending backlog, and SLA breach rate.
3. Read the **AI Administrative Insights** summarizing that Cadastral Demarcation experiences the highest turnaround variability.
4. Review the **Departmental Stage Cycle-Time vs Statutory SLA Limits** table:
   - Notice the visual progress bars showing Cadastral Demarcation averaging 6.8 days against a 5-day statutory limit.
   - Notice the identified bottleneck alert cards with recommended administrative interventions (e.g. deploying Rover DGPS units).
5. Use the **Workflow Filters** dropdown to filter by *Application Type* (e.g. Sale Deed Mutation) or *Status* (e.g. Pending Under Review) to see real-time recalculated metrics.

---

## 8. Responsible AI & Legal Disclaimers

1. **Non-Adjudicatory**: BHULEKH provides automated decision-support and consistency auditing. It does not establish legal land ownership or replace Revenue Courts or Sub-Registrars.
2. **Explainability & Grounding**: All numerical scores, discrepancies, and metrics are calculated deterministically in backend application code. AI language models are used solely to generate grounded human-readable summaries and never fabricate missing facts.
3. **Synthetic Demonstration Data**: To protect citizen privacy during demonstrations, synthetic administrative records are clearly labeled with a prominent notice badge.
=======
# BHULEKH-
BHULEKH Ledger — An AI-assisted land intelligence platform for exploring digital land holdings, identifying document discrepancies, assessing potential risks, analyzing administrative delays, and demonstrating cryptographic record integrity.
>>>>>>> 0ced5349b686b64179f3c350dddfd84b88e17a03
