# NRL Medical Claim Engine — AI Workshop 2026

Training implementation: medical bill extraction, claim validation, and in-app calculation display.

## Quick start

### Option A — use startup scripts (easiest)

From project root `E:\AI Workshop 2026`:

```powershell
# Terminal 1 — ensure Docker Postgres is up first
docker compose up -d db redis

# Terminal 1 — backend
.\run-backend.ps1

# Terminal 2 — frontend
.\run-frontend.ps1
```

### Option B — manual commands

**Important:** run uvicorn from the `backend` folder, not the project root.

```powershell
cd "e:\AI Workshop 2026"
docker compose up -d db redis
```

```powershell
cd "e:\AI Workshop 2026\backend"
.venv\Scripts\activate
$env:DATABASE_URL="postgresql://medclaim:medclaim@localhost:5432/medclaim"
uvicorn app.main:app --reload --port 8000
```

```powershell
cd "e:\AI Workshop 2026\frontend"
npm install
npm run dev
```

Open http://127.0.0.1:5173

### Common error

`ModuleNotFoundError: No module named 'app'` — you ran uvicorn from the **project root**. Use `.\run-backend.ps1` or `cd backend` first.

### 4. Ollama (optional)

If Ollama is running locally, extraction uses your model. Set in `.env`:

```
LLM_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.2
```

Without Tesseract, image uploads use **EasyOCR** (first run downloads ~100MB models).

```powershell
pip install -r requirements.txt
```

Optional faster OCR — install [Tesseract for Windows](https://github.com/UB-Mannheim/tesseract/wiki) and add to PATH.

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
