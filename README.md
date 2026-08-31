# AEGIS-X

### A Model-Agnostic Framework for AI Reliability Monitoring, Failure Discovery, Prediction and Early Warning

---

## Current Development Status
> **Phase D — Step 1: AEGIS-X Professional Dashboard Foundation**  
> *Exposes AEGIS-X operational capabilities over a clean, modern Next.js TypeScript dashboard UI: Command Center Overview, Model Registry, Data Setup & Reference Fitting, Batch Monitor, Reliability Visualization, Stress Lab, Fault Lab, Failure Explorer, Failure Memory, Failure Prediction, and Early Warning.*

---

## Architectural Philosophy

AEGIS-X **surrounds an existing trained AI/ML model** rather than replacing it, retraining it, or modifying its parameters. It acts as an external reliability wrapper that evaluates the stability, distribution health, and operational boundaries of machine learning models deployed in production environments.

### Core Processing Flow

```
                  ┌───────────────────────┐
                  │      User Model       │
                  └───────────┬───────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │  AEGIS-X Integration Layer    │
              └───────────────┬───────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │  Reference + Evaluation Data  │
              └───────────────┬───────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │      Reliability Engine       │
              └───────────────┬───────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
      ┌──────────────┐ ┌──────────────┐ ┌───────────┐
      │OOD Detection │ │ Uncertainty  │ │Feature    │
      │              │ │ Estimation   │ │Drift      │
      └──────────────┘ └──────────────┘ └───────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │ Integrated Reliability        │
              │ Signal Fusion                 │
              └───────────────┬───────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │ Stress & Failure Analysis     │
              └───────────────┬───────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │ Failure Prediction & Warning  │
              └───────────────┬───────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │ Dashboard Command Center &    │
              │ Reliability Telemetry UI      │
              └───────────────────────────────┘
```

---

## Running the Application Locally

### 1. Launch FastAPI Backend
```bash
python -m uvicorn api.main:app --reload
```
- API Base URL: `http://127.0.0.1:8000/api/v1`
- OpenAPI Swagger UI: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`
- Readiness Check: `http://127.0.0.1:8000/ready`

### 2. Launch Next.js Dashboard
```bash
cd frontend
npm install
npm run dev
```
- Dashboard URL: `http://localhost:3000`

---

## Key Features & Dashboard Modules

* **Command Center Overview (`/dashboard`):** Real-time model count, active model status, system readiness, recent analyses, high-risk observation warnings, and individual signal risk summaries.
* **Model Registry (`/models`):** Register scikit-learn models (`.joblib`/`.pkl`), inspect model task type, features, prediction capabilities, and query capability readiness status.
* **Data Setup & Reference Fit (`/data`):** Upload baseline REFERENCE datasets and EVALUATION batch CSVs. Execute explicit `FIT REFERENCE STATE` baseline fitting.
* **Batch Operational Monitor (`/monitor`):** Select model, evaluation dataset, and fusion engine (`StressRobust` vs `Original`). Renders OOD, Uncertainty, Drift, and Fusion signals independently.
* **Reliability Signal Visualization (`/reliability`):** Detailed breakdown of individual risk detectors. Preserves label-free operational fusion and displays separate retrospective diagnostics when true target labels exist.
* **Stress Lab Engine (`/stress`):** Controlled synthetic stress testing (Gaussian Noise, Feature Dropout, Feature Permutation, Combined Stress) on dataset copies without mutating source data.
* **Fault Lab Engine (`/faults`):** Inject sensor bias, gain error, stuck-at, channel swap, or sign inversion physical faults; compare original vs faulted risk behavior.
* **Failure Explorer (`/failures`):** Observation-level failure event analysis, high-risk observation warnings, and label-aware silent failure rate statistics.
* **Failure Memory (`/memory`):** Fits unsupervised failure signature centroids (`Condition Profiles`) and matches incoming query condition profiles without re-fitting. Uses associative, non-causal language.
* **Failure Prediction (`/prediction`):** Onset-aware next-step failure prediction over controlled degradation states. Uses capability state safeguards (`status = NOT_AVAILABLE` if un-fitted).
* **Early Warning Engine (`/warnings`):** Dynamic multi-signal temporal warning queries and retrospective trajectory lead evaluations (`controlled_degradation_states` unit).
* **Reliability Reports (`/reports`):** Placeholder page logging historical analysis payloads.

---

## Scientific Scope & Nuance Disclosures

1. **Signal Fusion Notice:** While multi-signal integration (OOD + Uncertainty + Drift) provides comprehensive operational insight, multi-signal fusion is context-dependent and not mathematically guaranteed to be superior to single-signal monitors in all operational domains.
2. **Early-Warning Bounds:** Early-warning failure detection depends on the presence of detectable covariate shift or uncertainty degradation prior to task performance failure. Horizon units preserve `controlled_degradation_states` and are not clock time.
3. **Model Security Notice:** Deserializing pickled model files (`.joblib` / `.pkl`) can execute arbitrary Python code. Only upload model files from verified, trusted sources.

---

## Directory Structure

```
AEGIS-X-Product/
├── aegis/                # Core scientific reliability engine (Modules 1-13)
├── api/                  # FastAPI Production REST Application
│   ├── core/             # Config, Auth & Middleware
│   ├── db/               # Persistence Repositories (SQLite & Supabase PostgREST)
│   ├── routes/           # REST Route Handlers (/api/v1/)
│   ├── schemas/          # Pydantic Schemas
│   └── services/         # Domain Services
├── frontend/             # Next.js TypeScript Dashboard Application
│   ├── app/              # App Router Pages (/dashboard, /models, /data, etc.)
│   ├── components/       # Layout & UI Design System Components
│   ├── lib/              # Centralized Typed API Client & Utilities
│   ├── types/            # TypeScript Interfaces for API Contracts
│   └── __tests__/        # Frontend Unit & Safeguard Tests
├── storage/              # Models, Datasets, Artifacts, Results, and DB
├── supabase/             # PostgreSQL Migrations with RLS Policies
├── tests/                # Automated Backend Test Suites (166 tests passed)
├── requirements.txt
└── README.md
```

---

## License & Attribution

AEGIS-X Framework — Research & Productization Architecture.
