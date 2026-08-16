"""
test_config.py

Unit tests for config.py module and fail-fast startup validation.
"""

import pytest
from config import Settings, validate_config, _is_placeholder


class TestConfigValidation:
    def test_placeholder_detector(self):
        assert _is_placeholder("your_api_key") is True
        assert _is_placeholder("YOUR_SUPABASE_KEY") is True
        assert _is_placeholder("your-project-id.supabase.co") is True
        assert _is_placeholder("placeholder_api_key") is True
        assert _is_placeholder("real_api_key_123456789") is False

    def test_development_mode_validation_passes(self):
        dev_settings = Settings(
            app_env="development",
            gemini_api_key="",
            supabase_url="",
            supabase_key="",
            backend_host="0.0.0.0",
            backend_port=8000,
            allowed_origins=["*"],
            rate_limit_search=30,
            rate_limit_max_clients=100,
        )
        # In development mode, missing keys log warnings but do NOT raise an error
        validate_config(dev_settings)

    def test_production_mode_raises_on_missing_keys(self):
        prod_settings = Settings(
            app_env="production",
            gemini_api_key="your_placeholder_key",
            supabase_url="https://your-project-id.supabase.co",
            supabase_key="your_placeholder_key",
            backend_host="0.0.0.0",
            backend_port=8000,
            allowed_origins=["https://acousticsearch.app"],
            rate_limit_search=30,
            rate_limit_max_clients=100,
        )
        with pytest.raises(RuntimeError, match="FATAL: Production mode"):
            validate_config(prod_settings)

    def test_production_mode_passes_with_real_keys(self):
        prod_settings = Settings(
            app_env="production",
            gemini_api_key="AIzaSyREAL_GEMINI_KEY_0987654321",
            supabase_url="https://realprojectid.supabase.co",
            supabase_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.REAL_KEY",
            backend_host="0.0.0.0",
            backend_port=8000,
            allowed_origins=["https://acousticsearch.app"],
            rate_limit_search=30,
            rate_limit_max_clients=100,
        )
        # Should complete without error
        validate_config(prod_settings)

    def test_production_rejects_wildcard_origin(self):
        prod_settings = Settings(
            app_env="production", gemini_api_key="real_key", supabase_url="https://real.supabase.co",
            supabase_key="real_supabase_key", backend_host="0.0.0.0", backend_port=8000,
            allowed_origins=["*"], rate_limit_search=30,
            rate_limit_max_clients=100,
        )
        with pytest.raises(RuntimeError, match="non-wildcard"):
            validate_config(prod_settings)
