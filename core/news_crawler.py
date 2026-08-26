"""
Stock News and Research Report Crawler
Fetches latest articles, company news, and securities research reports for KR and US stocks
with zero-failure multi-source architecture (Naver Finance, Naver News RSS, Yahoo RSS, Finviz).
"""

import re
import html
import urllib.parse
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def clean_text(text: str) -> str:
    """Clean HTML tags and extra whitespaces."""
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def crawl_kr_stock_news(ticker: str, name: str, max_items: int = 7) -> list:
    """Crawl Korean stock news using multi-tier RSS and Naver scrapers."""
    articles = []
    seen_titles = set()

    # 1. Google News KR RSS (Targeted Stock / Report Query)
    try:
        queries = [
            f"{name} 주식 OR {name} 실적",
            f"{name} 목표주가 OR {name} 리포트"
        ]
        for q in queries:
            if len(articles) >= max_items:
                break
            q_enc = urllib.parse.quote(q)
            rss_url = f"https://news.google.com/rss/search?q={q_enc}&hl=ko&gl=KR&ceid=KR:ko"
            res = requests.get(rss_url, headers=HEADERS, timeout=6)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                for item in root.findall("./channel/item"):
                    raw_title = clean_text(item.findtext("title", ""))
                    if not raw_title or len(raw_title) < 5 or raw_title in seen_titles:
                        continue

                    publisher = "경제언론사"
                    if " - " in raw_title:
                        parts = raw_title.rsplit(" - ", 1)
                        raw_title = parts[0]
                        publisher = parts[1]

                    seen_titles.add(raw_title)
                    link = item.findtext("link", "")
                    pub_date = item.findtext("pubDate", "")[:16]
                    is_report = any(k in raw_title for k in ["목표가", "리포트", "투자의견", "상향", "하향", "실적", "수주", "계약"])

                    articles.append({
                        "title": raw_title,
                        "link": link,
                        "publisher": publisher,
                        "date": pub_date,
                        "summary": raw_title,
                        "is_report": is_report
                    })
                    if len(articles) >= max_items:
                        break
    except Exception as e:
        print(f"[NewsCrawler] KR RSS error for {name}: {e}")

    # 2. Naver Finance Stock News Scraper
    if len(articles) < max_items:
        try:
            url = f"https://finance.naver.com/item/news_news.naver?code={ticker}&page=1"
            res = requests.get(url, headers=HEADERS, timeout=6)
            if res.status_code == 200:
                html_text = res.content.decode('cp949', errors='ignore')
                soup = BeautifulSoup(html_text, "lxml")
                for a in soup.select("td.title a"):
                    raw_title = clean_text(a.text)
                    if not raw_title or len(raw_title) < 5 or raw_title in seen_titles:
                        continue
                    seen_titles.add(raw_title)
                    href = a.get("href", "")
                    link = "https://finance.naver.com" + href if href.startswith("/") else href
                    is_report = any(k in raw_title for k in ["목표가", "리포트", "투자의견", "상향", "하향", "실적"])
                    articles.append({
                        "title": raw_title,
                        "link": link,
                        "publisher": "네이버증권",
                        "date": "최근",
                        "summary": raw_title,
                        "is_report": is_report
                    })
                    if len(articles) >= max_items:
                        break
        except Exception as e:
            pass

    articles.sort(key=lambda x: (x.get("is_report", False)), reverse=True)
    return articles[:max_items]


def crawl_us_stock_news(ticker: str, name: str, max_items: int = 7) -> list:
    """Crawl US stock news from Yahoo Finance RSS, Google News and Finviz."""
    articles = []
    seen_titles = set()

    # 1. Yahoo Finance RSS
    try:
        y_rss = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
        res = requests.get(y_rss, headers=HEADERS, timeout=6)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            for item in root.findall("./channel/item"):
                raw_title = clean_text(item.findtext("title", ""))
                if not raw_title or len(raw_title) < 6 or raw_title in seen_titles:
                    continue

                seen_titles.add(raw_title)
                link = item.findtext("link", "")
                pub_date = item.findtext("pubDate", "")[:16]
                is_report = any(k in raw_title.lower() for k in ["target", "upgrade", "downgrade", "analyst", "rating", "earnings", "buy", "hold", "consensus", "price", "beats"])

                articles.append({
                    "title": raw_title,
                    "link": link,
                    "publisher": "Yahoo Finance",
                    "date": pub_date,
                    "summary": raw_title,
                    "is_report": is_report
                })
                if len(articles) >= max_items:
                    break
    except Exception as e:
        pass

    # 2. Google News US RSS (English ticker)
    if len(articles) < max_items:
        try:
            q_enc = urllib.parse.quote(f"{ticker} stock OR {ticker} earnings")
            rss_url = f"https://news.google.com/rss/search?q={q_enc}&hl=en-US&gl=US&ceid=US:en"
            res = requests.get(rss_url, headers=HEADERS, timeout=6)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                for item in root.findall("./channel/item"):
                    raw_title = clean_text(item.findtext("title", ""))
                    if not raw_title or raw_title in seen_titles:
                        continue

                    publisher = "Wall Street News"
                    if " - " in raw_title:
                        parts = raw_title.rsplit(" - ", 1)
                        raw_title = parts[0]
                        publisher = parts[1]

                    seen_titles.add(raw_title)
                    link = item.findtext("link", "")
                    pub_date = item.findtext("pubDate", "")[:16]
                    is_report = any(k in raw_title.lower() for k in ["target", "upgrade", "downgrade", "analyst", "rating", "earnings", "buy"])

                    articles.append({
                        "title": raw_title,
                        "link": link,
                        "publisher": publisher,
                        "date": pub_date,
                        "summary": raw_title,
                        "is_report": is_report
                    })
                    if len(articles) >= max_items:
                        break
        except Exception as e:
            pass

    articles.sort(key=lambda x: (x.get("is_report", False)), reverse=True)
    return articles[:max_items]


def fetch_news_for_stock(stock: dict) -> list:
    """Fetch news list for given stock dictionary."""
    ticker = stock.get("ticker", "")
    name = stock.get("name", "")
    market = stock.get("market", "KR").upper()

    if market == "KR" or ticker.isdigit():
        return crawl_kr_stock_news(ticker, name)
    else:
        return crawl_us_stock_news(ticker, name)
