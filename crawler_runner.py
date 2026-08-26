"""
Main Pipeline Runner for Portfolio Stock Briefing
Collects real-time stock prices, analyst consensus, and latest news,
then generates AI 4-block summaries and exports data to JSON / JS.
"""

import os
import sys
import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Force UTF-8 stdout on Windows console
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from core.config import load_stocks, BASE_DIR, DATA_DIR, GEMINI_API_KEY
from core.stock_data import fetch_stock_info
from core.news_crawler import fetch_news_for_stock
from core.ai_summarizer import summarize_stock

KST = timezone(timedelta(hours=9))

def run_pipeline():
    start_time = time.time()
    now_kst = datetime.now(KST)
    weekday_kr = ["월", "화", "수", "목", "금", "토", "일"][now_kst.weekday()]
    date_str = f"{now_kst.year}년 {now_kst.month:02d}월 {now_kst.day:02d}일 ({weekday_kr})"

    print("=" * 65)
    print("  [Portfolio Stock Briefing] Daily Intelligence Pipeline")
    print(f"  Execution Time (KST): {now_kst.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  AI Mode: {'Gemini 1.5 Flash (Cloud API)' if GEMINI_API_KEY else 'Rule-based NLP Engine (100% Free)'}")
    print("=" * 65)

    stocks = load_stocks()
    print(f"\n>>> Loaded {len(stocks)} stocks from stocks.json")

    processed_stocks = []

    for idx, s in enumerate(stocks, 1):
        name = s.get("name", "")
        ticker = s.get("ticker", "")
        market = s.get("market", "KR")
        print(f"\n[{idx}/{len(stocks)}] Processing {name} ({ticker}, {market})...")

        # 1. Fetch Price & Consensus
        print("    -> 1/3 Fetching price & analyst target consensus...")
        stock_info = fetch_stock_info(s)
        status_sym = "▲" if stock_info["status"] == "up" else ("▼" if stock_info["status"] == "down" else "─")
        print(f"       Price: {stock_info['display_price']} ({status_sym} {stock_info['change_rate']:+.2f}%)")
        print(f"       Target: {stock_info['analyst_consensus']['display_target_price']} ({stock_info['analyst_consensus']['opinion']})")

        # 2. Fetch News & Research Articles
        print("    -> 2/3 Crawling latest news & research reports...")
        news_list = fetch_news_for_stock(s)
        print(f"       Collected {len(news_list)} news articles.")

        # 3. AI Summarization & Sentiment
        print("    -> 3/3 Generating 4-block AI summary (Fact, Reaction, Upside, Downside)...")
        ai_brief = summarize_stock(stock_info, news_list)
        print(f"       AI Sentiment: {ai_brief['sentiment_label']} ({ai_brief['sentiment_score']:+d} pts)")

        item = {
            "ticker": ticker,
            "name": name,
            "market": market,
            "category": s.get("category", ""),
            "price_info": stock_info,
            "ai_brief": ai_brief,
            "news": news_list
        }
        processed_stocks.append(item)

    output_data = {
        "metadata": {
            "title": "보유/관심 종목 모닝 스마트 브리핑",
            "updated_at": now_kst.strftime("%Y-%m-%d %H:%M:%S"),
            "date_str": date_str,
            "stock_count": len(processed_stocks),
            "ai_mode": "Gemini AI" if GEMINI_API_KEY else "NLP Fallback"
        },
        "stocks": processed_stocks
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    json_path = DATA_DIR / "briefing_data.json"
    root_json_path = BASE_DIR / "briefing_data.json"
    js_path = BASE_DIR / "data.js"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    with open(root_json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    with open(js_path, "w", encoding="utf-8") as f:
        f.write(f"window.BRIEFING_DATA = {json.dumps(output_data, ensure_ascii=False, indent=2)};\n")

    elapsed = time.time() - start_time
    print("\n" + "=" * 65)
    print(f"  [SUCCESS] Pipeline Completed in {elapsed:.2f} seconds!")
    print(f"  - Output saved: {json_path}")
    print(f"  - Offline JS: {js_path}")
    print("=" * 65)

if __name__ == "__main__":
    run_pipeline()
