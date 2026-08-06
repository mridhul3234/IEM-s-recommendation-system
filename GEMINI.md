# Project Rules & Context: AcousticSearch

You are working on **AcousticSearch**, an AI-powered In-Ear Monitor (IEM) Recommendation Engine. Read this document before making any changes.

## Core Architecture
1. **Backend**: Python-based pipeline leveraging `fastapi`, `uvicorn`, `sentence-transformers`, and the Google Gemini API. The server runs on `http://0.0.0.0:8000` via `python server.py`.
2. **Frontend**: Astro v5 + React + TailwindCSS v3 application. It uses a custom "Acoustic" design language with deep space navy and copper accents. It runs on `http://localhost:4321` via `npm run dev`.
3. **Database**: Supabase PostgreSQL with `pgvector` extension for semantic matching.

## The Search Pipeline (Hybrid Search)
1. User types a free-text query in the Astro UI.
2. The UI sends a GET request to the Python backend `/search?q="..."` endpoint.
3. The backend uses Gemini to translate the user query into a 10-dimensional acoustic feature dictionary (sub-bass, bass, mids, etc).
4. The query string is embedded into a dense vector (384d) using `all-MiniLM-L6-v2`.
5. The dense vector is used to perform a cosine similarity search against the Supabase `iems` table (`match_iems` RPC function).
6. The top semantic results are re-ranked locally using a **Hybrid Score** (semantic distance + acoustic euclidean distance) with $\alpha = 0.5$.

## Guidelines for Changing Code
- **Never fabricate frequency-response data or eval results.**
- Keep the Astro frontend minimal. We do not want user authentication or complex dashboards. Stick to the Acoustic design language.
- When starting the Astro dev server, ensure `astro@^5.0.0` and `tailwindcss@^3.4.0` are strictly maintained in `package.json` to prevent local node module resolution issues on Windows.
- Always use environment variables for `SUPABASE_URL`, `SUPABASE_KEY`, and `GEMINI_API_KEY`. Never hardcode them.

## Important Files
- `server.py`: The FastAPI backend entrypoint.
- `search.py`: The hybrid vector re-ranking logic.
- `infer.py`: The Gemini API parsing logic that extracts target acoustic features from user intent.
- `features.py`: The math that calculates sibilance risk and tonal tilt from FR deviations.
- `frontend/src/components/SearchApp.jsx`: The main client-side React island.
- `frontend/src/components/MiniChart.jsx`: The SVG visualization of the IEM tuning frequency.
