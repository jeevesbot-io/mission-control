"""Pytest configuration — ensure test environment is set before any imports."""
import os

# Must be set before main.py is imported, as Settings() is instantiated at module level.
# Without DEBUG=true, the validator rejects the default 'change-me' session secret.
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("SESSION_SECRET", "test-secret-key-not-for-production")
