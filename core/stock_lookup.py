"""
Stock Master Lookup & Auto-Search Module
Provides ticker/name bi-directional search and sector categorization for KR/US stocks and ETFs.
"""

import urllib.parse
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def search_kr_stock(query: str) -> dict:
    """Search Korean stock/ETF by code or name using Naver Search."""
    q = query.strip()
    # If code (6 digits)
    if q.isdigit() and len(q) == 6:
        try:
            url = f"https://m.stock.naver.com/api/stock/{q}/integration"
            res = requests.get(url, headers=HEADERS, timeout=5)
            if res.status_code == 200:
                data = res.json()
                name = data.get("stockName", "")
                market = "KR"
                desc = data.get("description", "")
                industry = data.get("industryCompareInfo", {}).get("industryCode", "")
                return {
                    "ticker": q,
                    "name": name if name else q,
                    "market": market,
                    "sector": industry if industry else "국내주식/ETF",
                    "found": True
                }
        except Exception:
            pass

    # Search by Name
    try:
        q_enc = urllib.parse.quote(q.encode("euc-kr", errors="ignore"))
        url = f"https://finance.naver.com/search/searchList.naver?query={q_enc}"
        res = requests.get(url, headers=HEADERS, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content.decode("cp949", errors="ignore"), "lxml")
            item = soup.select_one("table.type_1 tbody tr td.tit a")
            if item:
                href = item.get("href", "")
                code = href.split("code=")[-1]
                full_name = item.text.strip()
                return {
                    "ticker": code,
                    "name": full_name,
                    "market": "KR",
                    "sector": "국내주식/ETF",
                    "found": True
                }
    except Exception as e:
        print(f"[StockLookup] Search error for {query}: {e}")

    return {"ticker": q, "name": q, "market": "KR", "sector": "일반", "found": False}
