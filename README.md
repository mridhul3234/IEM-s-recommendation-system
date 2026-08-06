# AcousticSearch: AI IEM Recommendation Engine

AcousticSearch is an end-to-end recommendation engine that translates free-text human queries into precise mathematical acoustic targets, retrieving the closest matching In-Ear Monitors (IEMs) using a hybrid Semantic + Acoustic vector search pipeline.

## Architecture & Pipeline

1. **Feature Extraction (`normalize.py`, `features.py`)**: 
   Loads raw two-column FR (Frequency Response) CSV measurements, resamples them onto a common log-frequency grid, and computes deviation from the Harman in-ear 2019 target curve. It collapses the deviation into 7 acoustic bands (sub-bass through air) and 3 derived signals (sibilance risk, overall tonal tilt, and bass-to-treble ratio).
2. **LLM Translation (`describe.py`, `infer.py`)**: 
   - *Offline*: Uses Google's Gemini LLM to ingest the mathematical acoustic features of each IEM and translate them into a nuanced, human-readable paragraph describing its tonal profile.
   - *Online (Query time)*: Uses Gemini to parse a user's free-text request (e.g. "I want thumpy bass but relaxed treble") and directly infer a 10-dimensional acoustic feature target.
3. **Embeddings & Storage (`embed.py`, `db.py`)**:
   Uses `sentence-transformers/all-MiniLM-L6-v2` to embed the LLM-generated descriptions into 384-dimensional dense vectors. These vectors, along with the JSON features, are pushed to a **Supabase PostgreSQL** database utilizing the `pgvector` extension for rapid semantic retrieval.
4. **Hybrid Search (`search.py`)**:
   Retrieves candidates from Supabase using pure semantic cosine similarity, then reranks them locally using a hybrid score that blends the semantic similarity with the Euclidean distance of the 10-dimensional acoustic feature vectors ($\alpha = 0.5$).
5. **Explainability (`explain.py`)**:
   Analyzes the top retrieved IEMs against the user's inferred acoustic target and identifies the specific frequency bands that drove the match (e.g. "BASS_MATCH", "TREBLE_MATCH"), allowing the UI to explain *why* it was recommended.
6. **Frontend (`frontend/`, `server.py`)**:
   A sleek Astro + React single-page application built on a premium, dark-mode "Acoustic" design system. It interfaces with a Python FastAPI backend that serves the hybrid recommendation results and renders a dynamic SVG oscilloscope-style visualization of each IEM's tuning.

## Data source & attribution

Measurement data comes from [AutoEq](https://github.com/jaakkopasanen/AutoEq) (MIT licensed, © Jaakko Pasanen), which aggregates numerical FR measurements from several independent reviewers. The sample files provided in this repository were measured by **oratory1990** and redistributed through AutoEq's `measurements/` folder.

To scale up and pull the full ~200-model oratory1990 in-ear set:

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/jaakkopasanen/AutoEq.git
cd AutoEq
git sparse-checkout set "measurements/oratory1990/data/in-ear" targets
```

## Running the Project Locally

### 1. Requirements
- Python 3.10+
- Node.js v22+
- Gemini API Key (`GEMINI_API_KEY`)
- Supabase URL & Key (`SUPABASE_URL`, `SUPABASE_KEY`)

### 2. Backend Server
```bash
pip install -r requirements.txt
# Ensure environment variables are set
python server.py
```
The FastAPI backend will run on `http://0.0.0.0:8000`. It will attempt to connect to Supabase if the environment variables are provided, otherwise it will gracefully fall back to local in-memory semantic search.

### 3. Frontend UI
```bash
cd frontend
npm install
npm run dev
```
The Astro UI will run on `http://localhost:4321`.

## Evaluation

Precision@3 testing (`eval.py`) confirms that the hybrid approach ($\alpha = 0.5$) drastically outperforms pure semantic search by grounding LLM hallucinations in objective acoustic measurements. Sibilance risk calculations have been calibrated explicitly against absolute peak volumes in the 5k-8kHz bands to correctly identify known sibilant archetypes.
