import os
import sys
import json
import time
import datetime
import re
from datetime import timezone, timedelta
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from core.config import GEMINI_API_KEY, DATA_DIR
from core.stock_data import fetch_stock_info
from core.news_crawler import fetch_news_for_stock
from core.ai_summarizer import summarize_stock

def run_pipeline():
    start_time = time.time()
    now_kst = datetime.datetime.now(timezone(timedelta(hours=9)))
    weekdays_ko = ["월", "화", "수", "목", "금", "토", "일"]
    date_str = f"{now_kst.year}년 {now_kst.month:02d}월 {now_kst.day:02d}일 ({weekdays_ko[now_kst.weekday()]})"

    print("=" * 65)
    print(f"  [Portfolio Stock Briefing] Daily Intelligence Pipeline")
    print(f"  Execution Time (KST): {now_kst.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  AI Mode: {'Gemini 1.5 Flash (Cloud API)' if GEMINI_API_KEY else 'Quantitative NLP Fallback'}")
    print("=" * 65)

    stocks_file = BASE_DIR / "stocks.json"
    if not stocks_file.exists():
        print("[ERROR] stocks.json not found!")
        return

    with open(stocks_file, "r", encoding="utf-8") as f:
        stocks = json.load(f)

    print(f"\n>>> Loaded {len(stocks)} stocks from stocks.json")

    processed_stocks = []
    for idx, s in enumerate(stocks, 1):
        ticker = s.get("ticker", "")
        name = s.get("name", "")
        market = s.get("market", "KR")

        print(f"\n[{idx}/{len(stocks)}] Processing {name} ({ticker}, {market})...")

        # 1. Fetch Price & Consensus & ETF Metrics & Events
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

        # ETF or Pension Account Auto-Detection
        acc_type = s.get("account_type")
        is_etf = bool(re.search(r"KODEX|TIGER|ACE|SOL|PLUS|RISE|KOSEF|KBSTAR|HANARO|ETF|리츠|선물", name, re.I)) or bool(re.search(r"T0|A0|L0", ticker, re.I))
        if is_etf or acc_type == "pension":
            acc_type = "pension"
        else:
            acc_type = "general"

        item = {
            "ticker": ticker,
            "name": name,
            "market": market,
            "account_type": acc_type,
            "account_name": "연금저축" if acc_type == "pension" else "일반계좌",
            "category": "연금저축 ETF/리츠" if acc_type == "pension" else "일반주식",
            "sector": s.get("sector", ""),
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
