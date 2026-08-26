"""
Stock Market Price, Flow (Foreign, Inst, Retail, Program), Volume Surge, Analyst Consensus,
Recent 3-Quarter Financial Earnings, ETF NAV/Disparity Metrics & Upcoming Event Calendar Collector.
"""

import re
import json
import datetime
from datetime import timezone, timedelta
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

_ETF_CACHE = {}

def get_etf_item(code: str) -> dict:
    """Fetch ETF data from Naver ETF Master API with memory cache."""
    global _ETF_CACHE
    if not _ETF_CACHE:
        try:
            url = "https://finance.naver.com/api/sise/etfItemList.nhn"
            res = requests.get(url, headers=HEADERS, timeout=6)
            if res.status_code == 200:
                items = res.json().get("result", {}).get("etfItemList", [])
                for it in items:
                    c = str(it.get("itemcode", "")).strip()
                    _ETF_CACHE[c] = it
        except Exception:
            pass
    return _ETF_CACHE.get(str(code).strip(), {})


def format_krw_amount(shares: int, price: int) -> str:
    """Helper to convert share volume to readable KRW amount (e.g. +1,240억, -350만)."""
    if shares == 0:
        return "0"
    amount_won = shares * price
    abs_won = abs(amount_won)
    sign = "+" if amount_won > 0 else "-"

    if abs_won >= 100_000_000: # >= 1억
        eok = abs_won / 100_000_000
        return f"{sign}{eok:,.1f}억"
    elif abs_won >= 10_000: # >= 1만
        man = abs_won / 10_000
        return f"{sign}{man:,.0f}만"
    else:
        return f"{sign}{abs_won:,}원"


def parse_clean_int(val_str: str) -> int:
    """Parse comma-separated string to signed integer."""
    if not val_str:
        return 0
    cleaned = str(val_str).replace(",", "").replace("+", "").strip()
    try:
        return int(cleaned)
    except ValueError:
        return 0


def fetch_kr_earnings_history(code: str) -> list:
    """
    Fetch the latest 3 confirmed quarterly Operating Profits and Net Incomes from Naver Finance.
    Automatically rolls forward when a new quarter is announced (dropping the oldest).
    """
    earnings_list = []
    try:
        url = f"https://finance.naver.com/item/main.naver?code={code}"
        res = requests.get(url, headers=HEADERS, timeout=6)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content.decode("cp949", errors="ignore"), "lxml")
            table = soup.select_one("div.section.cop_analysis table.tb_type1")
            if table:
                headers = [th.text.strip().replace("\n", "").replace("\t", "") for th in table.select("thead tr:nth-of-type(2) th")]
                quarter_headers = headers[4:] # 6 recent quarter names

                rows = table.select("tbody tr")
                if len(rows) >= 3:
                    op_tds = [td.text.strip().replace(",", "") for td in rows[1].select("td")][4:]
                    net_tds = [td.text.strip().replace(",", "") for td in rows[2].select("td")][4:]

                    valid_quarters = []
                    for idx, q_name in enumerate(quarter_headers):
                        if idx < len(op_tds) and idx < len(net_tds):
                            op_str = op_tds[idx]
                            net_str = net_tds[idx]
                            if op_str and op_str.replace("-", "").isdigit():
                                op_val = int(op_str)
                                net_val = int(net_str) if net_str.replace("-", "").isdigit() else 0
                                valid_quarters.append({
                                    "quarter": q_name.replace("(E)", "").strip(),
                                    "is_estimate": "(E)" in q_name,
                                    "op_profit": op_val,
                                    "op_profit_str": f"{op_val:,}억원",
                                    "net_income": net_val,
                                    "net_income_str": f"{net_val:,}억원"
                                })

                    reported = [q for q in valid_quarters if not q.get("is_estimate")]
                    if len(reported) >= 3:
                        target_quarters = reported[-3:]
                    else:
                        target_quarters = valid_quarters[-3:] if len(valid_quarters) >= 3 else valid_quarters

                    for i in range(len(target_quarters)):
                        curr = target_quarters[i]
                        if i > 0:
                            prev = target_quarters[i - 1]
                            prev_op = prev["op_profit"]
                            curr_op = curr["op_profit"]

                            if prev_op > 0 and curr_op > 0:
                                diff_rate = ((curr_op - prev_op) / prev_op) * 100
                                curr["op_change_rate"] = round(diff_rate, 1)
                                curr["op_change_str"] = f"{diff_rate:+.1f}%"
                                curr["op_status"] = "up" if diff_rate > 0 else ("down" if diff_rate < 0 else "same")
                            elif prev_op <= 0 and curr_op > 0:
                                curr["op_change_rate"] = 100.0
                                curr["op_change_str"] = "흑자전환 🟢"
                                curr["op_status"] = "turn_profit"
                            elif prev_op > 0 and curr_op <= 0:
                                curr["op_change_rate"] = -100.0
                                curr["op_change_str"] = "적자전환 🔴"
                                curr["op_status"] = "turn_loss"
                            else:
                                curr["op_change_rate"] = 0.0
                                curr["op_change_str"] = "적자지속"
                                curr["op_status"] = "loss_cont"
                        else:
                            curr["op_change_rate"] = 0.0
                            curr["op_change_str"] = "기준 분기"
                            curr["op_status"] = "same"

                        earnings_list.append(curr)
    except Exception as e:
        print(f"[Earnings] Error fetching earnings for {code}: {e}")

    return earnings_list


def generate_upcoming_events(stock_info: dict) -> list:
    """Generate intelligent upcoming events and calendar for stocks & ETFs."""
    events = []
    is_etf = bool(stock_info.get("etf_metrics")) or stock_info.get("account_type") == "pension"
    name = stock_info.get("name", "")

    # 1. Earnings Season Schedule
    if not is_etf:
        events.append({
            "type": "earnings",
            "title": "📊 3분기 실적 발표 예정",
            "date_desc": "2026.10월 말 ~ 11월 중순",
            "badge": "실적 공시"
        })
        events.append({
            "type": "dividend",
            "title": "💰 2026년 결산 배당 기준일",
            "date_desc": "2026.12월 말 (주주명부 폐쇄)",
            "badge": "배당 일정"
        })
    else:
        # ETF distribution cycle
        if any(k in name for k in ["미국배당", "초단기", "국채", "화장품", "월"]):
            events.append({
                "type": "etf_dist",
                "title": "💵 월말 분배금 지급 기준일",
                "date_desc": "매월 마지막 영업일 (월분배)",
                "badge": "월분배금"
            })
        else:
            events.append({
                "type": "etf_dist",
                "title": "💵 분기 분배금 지급 기준일",
                "date_desc": "1/4/7/10월 마지막 영업일",
                "badge": "분기분배"
            })
        events.append({
            "type": "rebalancing",
            "title": "⚖️ 기초지수 정기 리밸런싱",
            "date_desc": "연 2회 (6월/12월 정기변경)",
            "badge": "지수변경"
        })

    return events


def fetch_kr_stock_data(ticker: str, name: str) -> dict:
    """Fetch Korean stock/ETF price, volume surge, investor flows, earnings, ETF metrics & events."""
    code = ticker.strip()
    result = {
        "ticker": code,
        "name": name,
        "market": "KR",
        "currency": "KRW",
        "current_price": 0,
        "change_val": 0,
        "change_rate": 0.0,
        "display_price": "0원",
        "display_change": "0.00%",
        "status": "same",
        "high_52w": 0,
        "low_52w": 0,
        "volume": 0,
        "display_volume": "0주",
        "avg_volume_20d": 0,
        "volume_surge": {
            "ratio": 100.0,
            "status": "normal",
            "badge": "거래량 보통 (100%)",
            "desc": "20일 평균 거래량 수준"
        },
        "investor_flow": {
            "foreign": "0",
            "institutional": "0",
            "retail": "0",
            "program": "0",
            "institution_detail": {
                "pension": "장기 스마트머니",
                "financial_invest": "증권사 헷지",
                "trust": "투신 펀드",
                "private_equity": "사모펀드",
                "insurance": "기관 종합"
            }
        },
        "analyst_consensus": {
            "opinion": "투자의견 매수 (Buy)",
            "target_price": 0,
            "display_target_price": "제공 없음",
            "upside_potential": 0.0,
            "analyst_count": 0
        },
        "earnings_history": [],
        "etf_metrics": {}, # 제안 2: ETF 전용 지표
        "upcoming_events": [] # 제안 3: 주요 일정 캘린더
    }

    # 1. Check ETF Master API first if ETF
    etf_info = get_etf_item(code)
    if etf_info:
        now_p = parse_clean_int(etf_info.get("nowVal"))
        diff_p = parse_clean_int(etf_info.get("changeVal"))
        rate_p = float(etf_info.get("changeRate", 0.0))
        vol_p = parse_clean_int(etf_info.get("quant"))
        nav_p = float(etf_info.get("nav", 0.0))
        three_month = float(etf_info.get("threeMonthEarnRate", 0.0))
        market_sum = parse_clean_int(etf_info.get("marketSum"))

        if now_p > 0:
            result["current_price"] = now_p
            result["display_price"] = f"{now_p:,}원"
            result["volume"] = vol_p
            result["display_volume"] = f"{vol_p:,}주"
            result["change_rate"] = rate_p

            if diff_p > 0:
                result["status"] = "up"
                result["change_val"] = diff_p
                result["display_change"] = f"▲ {diff_p:,} (+{rate_p:.2f}%)"
            elif diff_p < 0:
                result["status"] = "down"
                result["change_val"] = diff_p
                result["display_change"] = f"▼ {abs(diff_p):,} ({rate_p:.2f}%)"
            else:
                result["status"] = "same"
                result["display_change"] = "0 (0.00%)"

            # [제안 2] ETF Metrics Calculation
            if nav_p > 0:
                disparity = ((now_p - nav_p) / nav_p) * 100
                disp_abs = abs(disparity)
                if disp_abs <= 0.5:
                    disp_badge = f"적정 수준 ({disparity:+.2f}%)"
                    disp_status = "good"
                elif disparity > 0.5:
                    disp_badge = f"고평가 주의 ({disparity:+.2f}%)"
                    disp_status = "high"
                else:
                    disp_badge = f"저평가 기회 ({disparity:+.2f}%)"
                    disp_status = "low"

                result["etf_metrics"] = {
                    "nav": round(nav_p, 1),
                    "nav_str": f"{nav_p:,.1f}원",
                    "disparity_rate": round(disparity, 2),
                    "disparity_badge": disp_badge,
                    "disparity_status": disp_status,
                    "three_month_return": round(three_month, 2),
                    "three_month_str": f"{three_month:+.2f}%",
                    "market_cap_str": f"{market_sum:,}억원" if market_sum else "-",
                    "distribution_cycle": "월분배" if any(k in name for k in ["미국배당", "초단기", "국채", "화장품"]) else "분기/결산분배"
                }

    # 2. Integration API for Regular Stocks & Flows
    try:
        api_url = f"https://m.stock.naver.com/api/stock/{code}/integration"
        res = requests.get(api_url, headers=HEADERS, timeout=6)
        if res.status_code == 200:
            data = res.json()

            deal_infos = data.get("dealTrendInfos", [])
            if deal_infos:
                latest = deal_infos[0]
                close_p = parse_clean_int(latest.get("closePrice"))
                diff_p = parse_clean_int(latest.get("compareToPreviousClosePrice"))
                vol_p = parse_clean_int(latest.get("accumulatedTradingVolume"))

                frgn_quant = parse_clean_int(latest.get("foreignerPureBuyQuant"))
                inst_quant = parse_clean_int(latest.get("organPureBuyQuant"))
                ret_quant = parse_clean_int(latest.get("individualPureBuyQuant"))

                if close_p > 0 and result["current_price"] == 0:
                    result["current_price"] = close_p
                    result["display_price"] = f"{close_p:,}원"
                    result["change_val"] = diff_p
                    result["volume"] = vol_p
                    result["display_volume"] = f"{vol_p:,}주"

                    status_name = latest.get("compareToPreviousPrice", {}).get("name", "UNCHANGED")
                    if status_name in ["RISING", "UPPER_LIMIT"]:
                        result["status"] = "up"
                    elif status_name in ["FALLING", "LOWER_LIMIT"]:
                        result["status"] = "down"
                        result["change_val"] = -abs(diff_p)
                    else:
                        result["status"] = "same"

                    prev_close = close_p - result["change_val"]
                    rate = (result["change_val"] / prev_close) * 100 if prev_close else 0.0
                    result["change_rate"] = round(rate, 2)
                    sign = "▲" if result["status"] == "up" else ("▼" if result["status"] == "down" else "─")
                    result["display_change"] = f"{sign} {abs(result['change_val']):,} ({rate:+.2f}%)"

                if close_p > 0:
                    result["investor_flow"]["foreign"] = format_krw_amount(frgn_quant, close_p)
                    result["investor_flow"]["institutional"] = format_krw_amount(inst_quant, close_p)
                    result["investor_flow"]["retail"] = format_krw_amount(ret_quant, close_p)

            # Consensus
            cons = data.get("consensusInfo")
            if cons and cons.get("priceTargetMean"):
                target_val = parse_clean_int(cons.get("priceTargetMean"))
                if target_val > 0:
                    result["analyst_consensus"]["target_price"] = target_val
                    result["analyst_consensus"]["display_target_price"] = f"{target_val:,}원"
                    if result["current_price"] > 0:
                        upside = ((target_val - result["current_price"]) / result["current_price"]) * 100
                        result["analyst_consensus"]["upside_potential"] = round(upside, 1)

                recom = cons.get("recommMean", "4.0")
                try:
                    r_score = float(recom)
                    result["analyst_consensus"]["opinion"] = f"투자의견 매수 ({r_score:.2f})" if r_score >= 3.5 else f"투자의견 중립 ({r_score:.2f})"
                except ValueError:
                    result["analyst_consensus"]["opinion"] = "투자의견 매수 (Buy)"
    except Exception:
        pass

    # 3. 20-day Volume Surge from Yahoo Chart
    for suffix in [".KS", ".KQ"]:
        try:
            y_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}{suffix}?range=1mo&interval=1d"
            y_res = requests.get(y_url, headers=HEADERS, timeout=5)
            if y_res.status_code == 200:
                y_data = y_res.json()
                if "chart" in y_data and y_data["chart"]["result"]:
                    meta = y_data["chart"]["result"][0]["meta"]
                    result["high_52w"] = int(meta.get("fiftyTwoWeekHigh", 0))
                    result["low_52w"] = int(meta.get("fiftyTwoWeekLow", 0))

                    quotes = y_data["chart"]["result"][0]["indicators"]["quote"][0]
                    vols = [v for v in quotes.get("volume", []) if v is not None and v > 0]
                    if vols:
                        curr_vol = result["volume"] if result["volume"] > 0 else vols[-1]
                        avg_vol = int(sum(vols[-20:]) / len(vols[-20:])) if len(vols) >= 5 else curr_vol
                        result["avg_volume_20d"] = avg_vol

                        if avg_vol > 0:
                            surge_ratio = round((curr_vol / avg_vol) * 100, 1)
                            result["volume_surge"]["ratio"] = surge_ratio
                            if surge_ratio >= 400:
                                result["volume_surge"]["status"] = "surge_extreme"
                                result["volume_surge"]["badge"] = f"🚨 역대급 거래량 폭증 ({surge_ratio}%)"
                                result["volume_surge"]["desc"] = f"20일 평균 대비 {surge_ratio/100:.1f}배 대량 거래 터짐"
                            elif surge_ratio >= 200:
                                result["volume_surge"]["status"] = "surge"
                                result["volume_surge"]["badge"] = f"💥 거래량 급증 ({surge_ratio}%)"
                                result["volume_surge"]["desc"] = f"20일 평균 대비 {surge_ratio/100:.1f}배 유입"
                            elif surge_ratio <= 50:
                                result["volume_surge"]["status"] = "low"
                                result["volume_surge"]["badge"] = f"거래량 한산 ({surge_ratio}%)"
                                result["volume_surge"]["desc"] = "평균 대비 거래량 감소"
                            else:
                                result["volume_surge"]["status"] = "normal"
                                result["volume_surge"]["badge"] = f"거래량 평이 ({surge_ratio}%)"
                                result["volume_surge"]["desc"] = "평균 수준 유지"
                    break
        except Exception:
            pass

    # 4. Fetch Recent 3-Quarter Earnings for Regular Stocks
    if not etf_info:
        result["earnings_history"] = fetch_kr_earnings_history(code)

    # 5. [제안 3] Generate Upcoming Events Calendar
    result["upcoming_events"] = generate_upcoming_events(result)

    return result


def fetch_us_stock_data(ticker: str, name: str) -> dict:
    """Fetch US stock price, volume surge, institutional ownership, Wall Street consensus & events."""
    code = ticker.strip().upper()
    result = {
        "ticker": code,
        "name": name,
        "market": "US",
        "currency": "USD",
        "current_price": 0.0,
        "change_val": 0.0,
        "change_rate": 0.0,
        "display_price": "$0.00",
        "display_change": "0.00%",
        "status": "same",
        "high_52w": 0.0,
        "low_52w": 0.0,
        "volume": 0,
        "display_volume": "0",
        "avg_volume_20d": 0,
        "volume_surge": {
            "ratio": 100.0,
            "status": "normal",
            "badge": "보통 (100%)",
            "desc": "평균 거래량 수준"
        },
        "investor_flow": {
            "foreign": "글로벌 유동성",
            "institutional": "기관 비중 70%+",
            "retail": "개인 수급",
            "program": "패시브/알고리즘 연동",
            "institution_detail": {
                "pension": "월가 연기금",
                "financial_invest": "투자은행(IB)",
                "trust": "글로벌 헤지펀드",
                "private_equity": "사모펀드",
                "insurance": "패시브 ETF"
            }
        },
        "analyst_consensus": {
            "opinion": "월가 매수 의견 (Buy)",
            "target_price": 0.0,
            "target_high": 0.0,
            "target_low": 0.0,
            "display_target_price": "제공 없음",
            "upside_potential": 0.0,
            "analyst_count": 0
        },
        "earnings_history": [],
        "etf_metrics": {},
        "upcoming_events": [
            {
                "type": "earnings",
                "title": "📊 Wall Street Q3 Earnings Release",
                "date_desc": "2026.10월 하순 예정",
                "badge": "실적 발표"
            }
        ]
    }

    # 1. Price and Volume History from Yahoo Chart API
    try:
        chart_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}?range=1mo&interval=1d"
        c_res = requests.get(chart_url, headers=HEADERS, timeout=8)
        if c_res.status_code == 200:
            c_data = c_res.json()
            if "chart" in c_data and c_data["chart"]["result"]:
                meta = c_data["chart"]["result"][0]["meta"]
                curr_price = float(meta.get("regularMarketPrice", 0.0))
                prev_close = float(meta.get("chartPreviousClose", curr_price))

                if curr_price > 0:
                    diff = curr_price - prev_close
                    rate = (diff / prev_close) * 100 if prev_close else 0.0
                    result["current_price"] = round(curr_price, 2)
                    result["display_price"] = f"${curr_price:,.2f}"
                    result["change_val"] = round(diff, 2)
                    result["change_rate"] = round(rate, 2)
                    result["status"] = "up" if diff > 0 else ("down" if diff < 0 else "same")
                    sign = "▲" if diff > 0 else ("▼" if diff < 0 else "─")
                    result["display_change"] = f"{sign} ${abs(diff):.2f} ({rate:+.2f}%)"
                    result["high_52w"] = float(meta.get("fiftyTwoWeekHigh", 0.0))
                    result["low_52w"] = float(meta.get("fiftyTwoWeekLow", 0.0))

                    quotes = c_data["chart"]["result"][0]["indicators"]["quote"][0]
                    vols = [v for v in quotes.get("volume", []) if v is not None and v > 0]
                    if vols:
                        curr_vol = vols[-1]
                        avg_vol = int(sum(vols[-20:]) / len(vols[-20:])) if len(vols) >= 5 else curr_vol
                        result["volume"] = curr_vol
                        result["display_volume"] = f"{curr_vol:,.0f}"
                        result["avg_volume_20d"] = avg_vol

                        if avg_vol > 0:
                            surge_ratio = round((curr_vol / avg_vol) * 100, 1)
                            result["volume_surge"]["ratio"] = surge_ratio
                            if surge_ratio >= 300:
                                result["volume_surge"]["status"] = "surge_extreme"
                                result["volume_surge"]["badge"] = f"🚨 역대급 거래량 폭증 ({surge_ratio}%)"
                                result["volume_surge"]["desc"] = f"월가 평균 대비 {surge_ratio/100:.1f}배 대량 거래"
                            elif surge_ratio >= 180:
                                result["volume_surge"]["status"] = "surge"
                                result["volume_surge"]["badge"] = f"💥 거래량 급증 ({surge_ratio}%)"
                                result["volume_surge"]["desc"] = f"월가 평균 대비 {surge_ratio/100:.1f}배 유입"
                            else:
                                result["volume_surge"]["status"] = "normal"
                                result["volume_surge"]["badge"] = f"거래량 평이 ({surge_ratio}%)"
                                result["volume_surge"]["desc"] = "평균 수준 유지"
    except Exception as e:
        print(f"[StockData] US Price error for {ticker}: {e}")

    # 2. Finviz parser for US
    try:
        finviz_url = f"https://finviz.com/quote.ashx?t={code}"
        f_res = requests.get(finviz_url, headers=HEADERS, timeout=8)
        if f_res.status_code == 200:
            f_soup = BeautifulSoup(f_res.text, "lxml")
            table = f_soup.select_one("table.snapshot-table2")
            if table:
                tds = table.select("td")
                for i in range(len(tds) - 1):
                    label = tds[i].text.strip()
                    val = tds[i + 1].text.strip()

                    if label == "Target Price":
                        try:
                            t_val = float(val.replace(",", ""))
                            if t_val > 0 and result["current_price"] > 0:
                                result["analyst_consensus"]["target_price"] = t_val
                                result["analyst_consensus"]["display_target_price"] = f"${t_val:,.2f}"
                                upside = ((t_val - result["current_price"]) / result["current_price"]) * 100
                                result["analyst_consensus"]["upside_potential"] = round(upside, 1)
                        except ValueError:
                            pass

                    elif label == "Recom":
                        try:
                            recom_score = float(val)
                            if recom_score <= 1.8:
                                result["analyst_consensus"]["opinion"] = f"월가: Strong Buy ({recom_score})"
                            elif recom_score <= 2.5:
                                result["analyst_consensus"]["opinion"] = f"월가: Buy ({recom_score})"
                            elif recom_score <= 3.5:
                                result["analyst_consensus"]["opinion"] = f"월가: Hold ({recom_score})"
                            else:
                                result["analyst_consensus"]["opinion"] = f"월가: Sell ({recom_score})"
                        except ValueError:
                            pass

                    elif label == "Inst Own":
                        result["investor_flow"]["institutional"] = f"기관 보유율 {val}"
                    elif label == "Short Float":
                        result["investor_flow"]["retail"] = f"공매도 잔고 {val}"
                    elif label == "Shs Float":
                        result["investor_flow"]["program"] = f"유통주식 {val}"

    except Exception as e:
        pass

    return result


def fetch_stock_info(stock: dict) -> dict:
    """Router for KR or US stock price, volume surge, investor flows & earnings."""
    ticker = stock.get("ticker", "")
    name = stock.get("name", "")
    market = stock.get("market", "KR").upper()
    category = stock.get("category", "")
    account_type = stock.get("account_type", "general")
    sector = stock.get("sector", "")

    if market == "KR" or ticker.isdigit() or ticker in _ETF_CACHE or len(ticker) == 6:
        data = fetch_kr_stock_data(ticker, name)
    else:
        data = fetch_us_stock_data(ticker, name)

    data["category"] = category
    data["account_type"] = account_type
    data["sector"] = sector
    return data
