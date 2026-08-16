"""
conftest.py — shared fixtures and test configuration.
"""

import os
import sys

# Import the backend exactly as deployed, without relying on the checkout root.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

# Set dummy environment variables so modules that call load_dotenv() at import
# time don't pick up the real .env and don't crash on missing keys.
os.environ.setdefault("GEMINI_API_KEY", "")
os.environ.setdefault("SUPABASE_URL", "")
os.environ.setdefault("SUPABASE_KEY", "")
