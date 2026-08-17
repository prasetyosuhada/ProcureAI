import os
import pytest

# Ensure offline mock mode for fast unit tests
os.environ["GEMINI_API_KEY"] = ""
from app.core.config import settings
settings.GEMINI_API_KEY = ""
