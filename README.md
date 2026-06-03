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

### 4. LLM provider

Two options, switched by `LLM_PROVIDER` in `.env` (defaults to `ollama`):

```
# Local / self-hosted (keeps data on your machine):
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.2

# Free hosted (best for cloud demo — Ollama can't run on free tiers):
LLM_PROVIDER=groq
LLM_API_KEY=gsk_...            # from https://console.groq.com
GROQ_MODEL=llama-3.3-70b-versatile
```

Either way, regex fallback runs if the LLM is unavailable.

### 5. OCR

Image uploads use **Tesseract** if installed. For local handwriting fallback you can also install EasyOCR (PyTorch, ~2GB — left out of the deploy image):

```powershell
pip install -r requirements-optional.txt
```

Optional faster OCR on Windows — install [Tesseract for Windows](https://github.com/UB-Mannheim/tesseract/wiki) and add to PATH.

### 6. Email notifications (optional)

```
EMAIL_PROVIDER=resend
RESEND_API_KEY=re_...          # from https://resend.com (free tier)
EMAIL_FROM=onboarding@resend.dev
```

Defaults to `none` (no emails sent). Sends are failure-tolerant — a send error never blocks a claim.

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

## Free demo deployment

Everything below uses free tiers. **Sample/fake data only — not for real PII.**

| Layer | Service | Notes |
|-------|---------|-------|
| Backend (FastAPI) | Render (Docker) | `render.yaml` blueprint included. Free web service + free Postgres. |
| LLM | Groq | `LLM_PROVIDER=groq` + `LLM_API_KEY`. Free, hosted Llama. |
| Email | Resend | `EMAIL_PROVIDER=resend` + `RESEND_API_KEY`. Free tier. |
| Frontend (React) | Vercel | `frontend/vercel.json` proxies `/api/*` to the backend. |

**Backend (Render):**
1. Push this repo to GitHub.
2. Render → New → Blueprint → select the repo (uses `render.yaml`).
3. Fill the dashboard secrets: `LLM_API_KEY`, `RESEND_API_KEY`, and `FRONTEND_URL` (your Vercel URL).
4. Deploy. Note the app URL, e.g. `https://medclaim-api.onrender.com`.

**Frontend (Vercel):**
1. Edit `frontend/vercel.json` → set the rewrite `destination` to your Render URL.
2. Vercel → New Project → import repo → root directory `frontend`.
3. Deploy. The `/api/*` rewrite proxies to the backend (no CORS setup needed).

> Render free web services sleep after ~15 min idle (first request cold-starts in ~30–50s). Fine for a demo. EasyOCR is excluded from the deploy image to stay within free limits — use Tesseract or `.txt`/`.pdf` samples there.

## Production (PRD) — different stack

For real PII, do **not** use the free tiers above. Run the Docker Compose stack on a controlled VM (on-prem or your cloud region), keep **Ollama + Tesseract self-hosted** (data stays in-network), add Celery+Redis for async, internal SMTP, HTTPS/nginx, DB backups, SSO, and audit logging.

## Not in scope (workshop)

Real PII, real SAP RFC, SSO, audit logging — see PRD notes above.
