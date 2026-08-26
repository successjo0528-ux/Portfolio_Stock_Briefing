"""
Configuration and Stocks Management Module
"""

import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STOCKS_FILE = BASE_DIR / "stocks.json"
DATA_DIR = BASE_DIR / "data"
ENV_FILE = BASE_DIR / ".env"

# 1. Manual .env parsing fallback
if ENV_FILE.exists():
    try:
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'").strip('"')
                    if k and v:
                        os.environ[k] = v
    except Exception:
        pass

# 2. Also try dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE)
except ImportError:
    pass

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
if GEMINI_API_KEY == "your_gemini_api_key_here":
    GEMINI_API_KEY = ""

DEFAULT_STOCKS = [
    {"ticker": "NVDA", "name": "엔비디아", "market": "US", "category": "AI/반도체"},
    {"ticker": "005930", "name": "삼성전자", "market": "KR", "category": "반도체/IT"}
]

def load_stocks():
    """Load stock portfolio from stocks.json."""
    if not STOCKS_FILE.exists():
        save_stocks(DEFAULT_STOCKS)
        return DEFAULT_STOCKS
    
    try:
        with open(STOCKS_FILE, "r", encoding="utf-8") as f:
            stocks = json.load(f)
            if isinstance(stocks, list) and len(stocks) > 0:
                return stocks
    except Exception as e:
        print(f"[Config] Error loading stocks.json: {e}, using defaults.")
    
    return DEFAULT_STOCKS

def save_stocks(stocks):
    """Save stock portfolio to stocks.json."""
    try:
        with open(STOCKS_FILE, "w", encoding="utf-8") as f:
            json.dump(stocks, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[Config] Error saving stocks.json: {e}")
        return False
