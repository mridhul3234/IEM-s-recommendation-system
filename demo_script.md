# AcousticSearch: Presentation & Demo Script

*(Use this script to narrate your demo during a presentation, interview, or hackathon.)*

## 1. The Hook (The Problem)
"Finding the perfect pair of headphones or IEMs is incredibly difficult. You either have to rely on confusing audiophile jargon like 'V-shaped' and 'sibilant', or you have to stare at raw frequency response graphs that are essentially just math. **AcousticSearch** bridges this gap. It's an AI-powered engine that lets you type exactly what you want in plain English, and it translates that into an objective acoustic mathematical target to find the perfect match."

## 2. The Architecture (How it Works)
"Here's how we built it. We started by parsing raw frequency response data—measured by oratory1990 and distributed by AutoEq—and calculating its deviation against the Harman neutral target. 

Instead of letting an LLM hallucinate answers based on brand hype, we use Google's Gemini to translate the user's natural language query into a 10-dimensional acoustic feature vector. We then embed the query using sentence-transformers and run a rapid semantic retrieval against our Supabase `pgvector` database."

## 3. The Secret Sauce (Hybrid Ranking)
"But pure semantic search isn't enough for audio precision. Our engine uses a **Hybrid Search Pipeline**. We take the top candidates from the vector database and rerank them locally by computing the Euclidean distance between the user's inferred acoustic target and the actual, measured frequency response of the IEM. 

As you can see on the screen, this guarantees our recommendations are grounded in objective, physical measurements. If you ask for 'thumpy bass', the math guarantees the recommended IEM actually measures hot in the sub-bass region."

## 4. The Live Demo (The UI)
*(Action: Type "I want thumpy bass but relaxed treble, something warm" into the Astro UI search bar).*

"When we hit search, the FastAPI backend instantly runs the hybrid pipeline. It extracts the features, pulls candidates from Supabase, and renders the top results on our Astro frontend. Notice the **Explainability** badges—the system actually tells you *why* it recommended the IEM by analyzing which acoustic bands drove the match, and plots it visually on this mini oscilloscope chart."

## 5. The Proof (Evaluation)
"We didn't just build it and hope it works. We built a custom evaluation harness measuring Precision@3 across dozens of queries. Our tests proved that applying this 50/50 semantic and acoustic hybrid approach completely eliminates LLM hallucination and drastically outperforms traditional text-only vector search."
