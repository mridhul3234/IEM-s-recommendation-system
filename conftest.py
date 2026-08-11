"""
conftest.py — shared fixtures and test configuration.
"""

import os
import sys

# Ensure the project root is on sys.path for all test modules.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set dummy environment variables so modules that call load_dotenv() at import
# time don't pick up the real .env and don't crash on missing keys.
os.environ.setdefault("GEMINI_API_KEY", "")
os.environ.setdefault("SUPABASE_URL", "")
os.environ.setdefault("SUPABASE_KEY", "")
