# IEM Recommender — Stage 1 Scaffold (Normalization + Feature Extraction)

This is the first working slice of the AI IEM recommendation engine: it
loads real frequency-response (FR) measurements, normalizes them against a
neutral target, and extracts a compact, interpretable acoustic fingerprint
per IEM. This fingerprint is the foundation everything else (LLM
description generation, embeddings, vector search, explainability) gets
built on top of.

## What's actually validated right now

Ran end-to-end against 8 real IEMs spanning different price points and
known tuning styles (budget V-shaped, planar, balanced-armature hybrid,
etc.) — `python3 run_demo.py` — and confirmed:

- The pipeline runs without errors on real (not synthetic) measurement data
- Different IEMs produce meaningfully different feature vectors (e.g. the
  1MORE Triple Driver comes out clearly bassiest at +4.32 dB vs target;
  the Moondrop Blessing 2 comes out with the brightest tonal tilt) —
  so the features are actually discriminating between tunings, not just
  noise
- The rule-based description generator (`describe.py`) produces
  differentiated text per IEM, which is what the embedding step will
  operate on next

**Known rough edge:** the sibilance-risk metric is currently flagging
most of the 8 test IEMs as "noticeable," which is very likely too
aggressive — either the baseline-vs-peak calculation needs tightening, or
the fixed `>3` threshold in `describe.py` needs to be calibrated against
IEMs people actually agree are sibilant vs. smooth, rather than picked
by eyeballing 8 examples. This is exactly what the eval step (below)
is for — don't hand-tune thresholds against a vibe, validate them
against known archetypes.

## Files

- `normalize.py` — loads a raw two-column FR CSV, resamples onto a
  common log-frequency grid, and computes deviation from a target curve
  (with level-anchoring at 1kHz so overall recording level doesn't get
  mistaken for a tonal difference)
- `features.py` — collapses the deviation curve into 7 named frequency
  bands (sub-bass through air) plus 3 derived signals: sibilance risk,
  overall tonal tilt (warm↔bright), and a bass-to-treble ratio
- `describe.py` — rule-based placeholder that turns a feature dict into
  a short tonal description. This is what gets replaced by an actual LLM
  call in the next stage — the `PROMPT_TEMPLATE` in this file is already
  shaped to drop straight into an API call
- `run_demo.py` — runs the full pipeline against the sample data and
  prints a feature table + generated descriptions, so you can sanity
  check any change against real curves in seconds
- `sample_data/` — 8 real IEM measurements + the Harman in-ear 2019
  target curve (see attribution below)

## Data source & attribution

Measurement data comes from
[AutoEq](https://github.com/jaakkopasanen/AutoEq) (MIT licensed,
© Jaakko Pasanen), which aggregates numerical FR measurements from
several independent reviewers. The 8 sample files here were measured by
**oratory1990** and redistributed through AutoEq's `measurements/`
folder. If you scale this up or publish it, keep the MIT license notice
and credit both AutoEq and the original measuring reviewer per IEM.

To pull the full ~200-model oratory1990 in-ear set (not just the 8-model
sample here):

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/jaakkopasanen/AutoEq.git
cd AutoEq
git sparse-checkout set "measurements/oratory1990/data/in-ear" targets
```

Then point `IEM_DIR` in `run_demo.py` at the full folder instead of
`sample_data/in-ear`.

## Run it

```bash
pip install -r requirements.txt
python3 run_demo.py
```

## Next steps (in order)

1. **Fix the sibilance calibration** — pull in a handful of IEMs with
   known, agreed-upon sibilance (forum/Crinacle consensus), check
   whether the metric actually ranks them correctly, adjust the
   baseline/threshold from there instead of guessing
2. **Swap `describe.py`'s rule-based text for the real LLM call** using
   `PROMPT_TEMPLATE` — batch it once over the full dataset, cache the
   results (no need to regenerate on every query)
3. **Embed the descriptions** with a sentence-transformer
   (`all-MiniLM-L6-v2` is a solid free local default) and store vectors
   in pgvector via Supabase
4. **Query time**: embed the user's free-text request the same way,
   cosine-similarity search, optionally re-rank using
   `features.to_vector()` for a hybrid semantic + acoustic-distance score
5. **Explainability overlay**: for a given match, show which band(s)
   drove the similarity — you already have the per-band numbers, this is
   mostly a rendering problem at that point
6. **Eval harness**: hold out a few IEMs with known tags (basshead,
   neutral, bright) and measure whether querying those descriptors
   actually retrieves them in the top-k — this is also where you'd
   properly validate the sibilance fix from step 1
