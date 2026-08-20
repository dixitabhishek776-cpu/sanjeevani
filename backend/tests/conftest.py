import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Tests never need a real API key — safety_agent.py's keyword pre-filter
# and every LLM call site are monkeypatched in these tests, so no network
# call or real credential is required to run this suite.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-used")
