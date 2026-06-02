# NRL Medical Claim Engine — AI Workshop 2026

Training implementation: medical bill extraction, claim validation, and in-app calculation display.

## Quick start

### 1. Start database & API (Docker)

```bash
cd "e:\AI Workshop 2026"
docker compose up -d db redis
```

### 2. Backend (local Python)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

set DATABASE_URL=postgresql://medclaim:medclaim@localhost:5432/medclaim
uvicorn app.main:app --reload --port 8000
```

Or run full stack in Docker:

```bash
docker compose up --build
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### 4. Ollama (optional)

If Ollama is running locally, extraction uses your model. Set in `.env`:

```
LLM_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.2
```

Without Ollama, the app falls back to regex extraction.

## Demo accounts

| Username | Password | Role |
|----------|----------|------|
| employee_workman | demo123 | Employee (non-mgmt, Grade VII) |
| employee_mgmt | demo123 | Employee (management, JG E) |
| reviewer | demo123 | Claims reviewer |
| admin | demo123 | Admin |

## Workshop sample

Upload `sample_claims/sample_hospital_bill.txt` renamed to `.pdf` or paste content into a PDF, or upload the `.txt` file directly for regex testing.

Expected behavior for workman + GNRC bill:
- Room charge capped at ₹4,500/day (X class) or ₹3,555 (Y class)
- Discount 8.5% matches synthetic seed → OK
- Paracetamol → reimbursable
- Sugar testing kit → non-reimbursable

## Project structure

```
backend/app/pipeline/   OCR, classify, extract, claim_validator
backend/app/services/   sap_mock.py (training only)
frontend/src/pages/     Login, claims, calculation panel, review
seed/                   Synthetic hospital discounts CSV
docs/manuals/           Copy compensation PDFs here (reference)
```

## Tests

```bash
cd backend
pytest tests/ -v
```

## SAP integration (training)

`SAP_USE_MOCK=true` — no real RFC required. Optional FM contract documented in plan.

## Not in scope

Production deployment, real PII, internal SMTP, real SAP RFC.
