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

### Backend (FastAPI Python) — Render

The repository-root `render.yaml` now defines only the backend. In Render, create or sync that Blueprint from `main`; do not set `rootDir` to `backend`, because the start command imports the top-level `backend` package.

- **Runtime**: Python 3.13.5.
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python -m uvicorn backend.server:app --host 0.0.0.0 --port $PORT`
- **Health Check Path**: `/health` (the platform must receive HTTP 200 before cutover).
- **Required Render environment variables**: `GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, and `ALLOWED_ORIGINS`. The production server intentionally refuses to start without these values. Set `ALLOWED_ORIGINS` to the exact Vercel production origin, for example `https://your-project.vercel.app` (comma-separate any additional approved custom domains). Never use `*`.
- **Verify before configuring Vercel**: open `https://<your-render-service>.onrender.com/health` and confirm HTTP 200, then open `/ready` and confirm it returns HTTP 200. A healthy process with `/ready` returning 503 does not have a usable data source.
- **Readiness Check Path**: `/ready` verifies the active corpus or makes a small authenticated Supabase query. Use it for alerting; `/health` stays lightweight for platform liveness probes.
- **Worker scaling prerequisite**: the rate limiter and profile cache are process-local. Before adding Uvicorn workers or horizontal replicas, move rate limiting and shared cache coordination to Redis (or an equivalent shared service), then load-test Gemini and Supabase concurrency limits. The checked-in Render service stays single-worker until that is in place.

### Frontend (Astro Static Site) — Vercel

Import the repository root in Vercel. The checked-in `vercel.json` installs and builds from `frontend/` and publishes `frontend/dist`, so no Vercel dashboard build or output-directory override is needed.

- **Environment Variable**: set `PUBLIC_API_BASE_URL=https://<your-render-service>.onrender.com` for Production, Preview, and Development as appropriate. It is a public browser value, so it must contain only the Render API origin and no secret.
- **Redeploy after setting the variable**: Astro writes `PUBLIC_` variables into the static build. Changing it without a new Vercel deployment leaves the old bundle in place.
- **Verify**: in the deployed browser, perform a search. If it fails, first test the browser request's `Origin` against Render's `ALLOWED_ORIGINS`; direct navigation to the API alone does not prove CORS is correct.

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
