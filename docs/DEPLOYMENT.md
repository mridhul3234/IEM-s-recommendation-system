# Production Deployment & Release Guide — AcousticSearch

## Overview

This guide details the deployment architecture, CI/CD pipeline, environment configurations, and emergency rollback runbook for **AcousticSearch**.

---

## 1. Environment Architecture

| Environment | Purpose | Trigger | API Base URL | DB Backend |
|---|---|---|---|---|
| **Development** | Local testing & dev | Local `npm run dev` / `python -m uvicorn backend.server:app` | `http://localhost:8000` | Local CSV fallback / Dev Supabase |
| **Staging** | Pre-release verification | Manual host deployment | Your staging API URL | Staging Supabase |
| **Production** | Live audiophile traffic | Host deployment from an approved commit | Your production API URL | Production Supabase pgvector |

---

## 2. CI/CD Pipeline Flow ([`.github/workflows/ci-cd.yml`](file:///.github/workflows/ci-cd.yml))

1. **Pull Request / Commit Stage**:
   - Runs **Python 3.13 Backend Test Suite**: `pytest` (102 tests pass).
   - Runs **Node 22 Frontend Build Verification**: `npm ci && npm run build`.
2. This workflow deliberately does **not** deploy. The earlier deployment jobs only printed messages and could not release or health-check anything.
3. Deploy through the configured host (for example Render's connected branch/manual deploy), then run the health check below before calling a release complete.

---

## 3. GitHub Actions Secrets Configuration

Configure the following secrets in **GitHub Repo Settings -> Secrets and variables -> Actions**:

- `GEMINI_API_KEY`: Production Google AI Studio API key.
- `SUPABASE_URL`: Production Supabase project URL (`https://<project-id>.supabase.co`).
- `SUPABASE_KEY`: Production Supabase anonymous/service key.
- `ALLOWED_ORIGINS`: Production CORS origins (`https://acousticsearch.app`).
- `ALLOWED_ORIGINS` is enforced for browser requests. For non-browser client authentication or multi-instance rate limits, put the backend behind an authenticated edge proxy; a secret embedded in this static frontend would not be a security boundary.

---

## 4. Hosting & Zero-Downtime Deployment Setup

### Backend (FastAPI Python) — e.g., Render / Railway / Docker
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python -m uvicorn backend.server:app --host 0.0.0.0 --port $PORT`
- **Health Check Path**: `/health` (Zero-downtime rolling cutover waits for HTTP 200 `{"status": "ok"}`).

### Frontend (Astro Static Site) — e.g., Cloudflare Pages / Vercel / Netlify
- **Framework Preset**: Astro
- **Build Command**: `npm run build` (inside `frontend/`)
- **Output Directory**: `frontend/dist`
- **Environment Variables**: Set `PUBLIC_API_BASE_URL=https://api.acousticsearch.app`.

---

## 5. Health Check Verification & Cutover

Post-deployment, verify backend health:
```bash
curl -f https://api.acousticsearch.app/health
```
Expected Response:
```json
{
  "status": "ok",
  "service": "AcousticSearch API",
  "supabase_configured": true,
  "local_items_loaded": 10,
  "timestamp": "2026-08-11T21:54:00Z"
}
```

---

## 6. Emergency Rollback Runbook (One-Command Rollback)

If a production release encounters a critical bug or outage:

### Method 1: Instant Platform Rollback (Zero Downtime)
- **Cloudflare Pages / Vercel**: Navigate to Deployment History -> Click **Rollback to Previous Deployment**.
- **Render / Railway**: Click **Rollback to Previous Release**.

### Method 2: Git Tag Rollback
Revert `main` and deploy previous release tag:
```bash
# 1. Revert main commit
git revert HEAD -m 1 --no-edit

# 2. Tag fallback hotfix
git tag v1.0.1 -m "Rollback to stable"
git push origin main --tags
```
The CI workflow will verify tests. Trigger the rollback using your hosting provider and verify `/health` before reopening traffic.

---

## 7. Database Backup Retention & Disaster Recovery Procedure

### Automated Backup Retention Policy
- **Database Engine**: Supabase PostgreSQL with `pgvector` extension.
- **Backup Strategy**: Daily automated Write-Ahead Log (WAL) snapshots + Point-In-Time Recovery (PITR).
- **Retention Period**: 7 days (Free / Pro Tier default) to 30 days (Enterprise).

### Database Restore Procedure
1. Navigate to **Supabase Dashboard -> Database -> Backups**.
2. Select **Point in Time** or choose a daily snapshot prior to the outage.
3. Click **Restore Backup** (or provision a new staging database from the backup).
4. Verify table integrity:
   ```sql
   SELECT count(*) FROM iems;
   ```
5. Re-run migration validation if needed:
   ```bash
   python scripts/migrate_to_supabase.py --confirm-production --price-catalog reviewed_prices.json
   ```
