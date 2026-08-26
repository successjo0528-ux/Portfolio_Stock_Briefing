"""
AI Summarizer & Sentiment Analyzer Module
Uses Google Gemini REST API or Quantitative NLP to generate briefings with
deep integration of Investor Flows (Foreign/Inst/Retail/Program/Pension) and Volume Surges.
"""

import json
import re
import requests
from core.config import GEMINI_API_KEY

POSITIVE_KEYWORDS = [
    "상향", "매수", "호실적", "서프라이즈", "사상 최대", "급등", "상승", "순매수", 
    "신고가", "계약", "수주", "승인", "검증", "통과", "확대", "성장", "호재",
    "upgrade", "buy", "beat", "record", "rally", "growth", "jump", "bull"
]
NEGATIVE_KEYWORDS = [
    "하향", "매도", "어닝쇼크", "적자", "급락", "하락", "순매도", "신저가", 
    "취소", "지연", "불확실", "우려", "경고", "제재", "소송", "악재", "발열",
    "downgrade", "sell", "miss", "drop", "fall", "warning", "risk", "delay"
]

def fallback_summarize(stock_info: dict, news_list: list) -> dict:
    """Quantitative NLP Fallback incorporating flows and volume surge."""
    name = stock_info.get("name", "")
    ticker = stock_info.get("ticker", "")
    change_rate = stock_info.get("change_rate", 0.0)
    consensus = stock_info.get("analyst_consensus", {})
    target_str = consensus.get("display_target_price", "미제공")
    opinion = consensus.get("opinion", "")
    flow = stock_info.get("investor_flow", {})
    vol_surge = stock_info.get("volume_surge", {})

    score = 0
    if change_rate > 1.5:
        score += 25
    elif change_rate < -1.5:
        score -= 25

    # Check foreign/inst flow positive/negative
    frgn_str = flow.get("foreign", "")
    if "+" in frgn_str:
        score += 15
    elif "-" in frgn_str:
        score -= 15

    inst_str = flow.get("institutional", "")
    if "+" in inst_str:
        score += 15
    elif "-" in inst_str:
        score -= 15

    titles = [a.get("title", "") for a in news_list]
    all_text = " ".join(titles).lower()

    pos_hits = [k for k in POSITIVE_KEYWORDS if k in all_text]
    neg_hits = [k for k in NEGATIVE_KEYWORDS if k in all_text]
    score += (len(pos_hits) * 10) - (len(neg_hits) * 10)
    score = max(min(score, 100), -100)

    if score >= 25:
        sentiment = "bull"
        sentiment_label = "호재 우세"
    elif score <= -25:
        sentiment = "bear"
        sentiment_label = "리스크 주의"
    else:
        sentiment = "neutral"
        sentiment_label = "중립·관망"

    top_title_1 = titles[0] if len(titles) > 0 else f"{name} 주가 및 시장 동향 점검"
    top_title_2 = titles[1] if len(titles) > 1 else ""

    fact = f"최근 주요 소식으로 '{top_title_1}' 등이 보도되며 시장의 이목이 집중되었습니다."
    if top_title_2:
        fact += f" 또한 '{top_title_2}' 관련 이슈가 함께 거론되고 있습니다."

    # Construct Flow & Reaction text
    detail = flow.get("institution_detail", {})
    pension_txt = f", 연기금({detail.get('pension')})" if detail.get("pension") and detail.get("pension") != "0" else ""
    prog_txt = f", 프로그램({flow.get('program')})" if flow.get("program") and flow.get("program") != "집계 중" else ""
    surge_txt = f" [{vol_surge.get('badge')}]" if vol_surge.get("status") in ["surge", "surge_extreme"] else ""

    reaction = f"금일 주가는 {stock_info.get('display_change', '0.00%')}{surge_txt} 흐름을 기록했습니다. 수급은 외국인({flow.get('foreign', '-')}), 기관({flow.get('institutional', '-')}{pension_txt}), 개인({flow.get('retail', '-')}){prog_txt} 동향을 보였으며, {opinion}"
    if target_str not in ["제공 없음", "미제공"]:
        reaction += f" (목표주가: {target_str})"
    reaction += " 흐름입니다."

    if sentiment == "bull":
        upside = f"{name}의 실적 개선 기대감 및 주요 수급 주체의 순매수 유입이 추가 상승 모멘텀을 지지하고 있습니다."
        downside = "단기 주가 반등에 따른 차익 실현 매물 출회 및 글로벌 거시경제 변동성을 점검할 필요가 있습니다."
    elif sentiment == "bear":
        upside = "과도한 낙폭에 따른 기술적 저가 매수세 유입 및 밸류에이션 매력 부각 가능성이 있습니다."
        downside = f"외국인/기관의 매도 압력 및 단기 악재성 이슈로 인한 투자 심리 위축이 하방 압력으로 작용하고 있습니다."
    else:
        upside = "향후 실적 가시성 확보 및 신규 사업 모멘텀 구체화 시 재평가 가능성이 열려 있습니다."
        downside = "뚜렷한 추가 상승 동력 부재 시 박스권 횡보 및 거시 변동성에 따른 등락 가능성이 있습니다."

    one_line = f"{top_title_1[:45]}..." if len(top_title_1) > 45 else top_title_1

    return {
        "fact": fact,
        "reaction": reaction,
        "upside": upside,
        "downside": downside,
        "sentiment": sentiment,
        "sentiment_label": sentiment_label,
        "sentiment_score": score,
        "one_line_summary": one_line,
        "ai_engine": "Quantitative NLP Fallback"
    }


def gemini_rest_summarize(stock_info: dict, news_list: list) -> dict:
    """Call Google Gemini REST API directly with full market data context."""
    if not GEMINI_API_KEY:
        return fallback_summarize(stock_info, news_list)

    name = stock_info.get("name", "")
    ticker = stock_info.get("ticker", "")
    market = stock_info.get("market", "KR")
    price = stock_info.get("display_price", "")
    change = stock_info.get("display_change", "")
    consensus = stock_info.get("analyst_consensus", {})
    flow = stock_info.get("investor_flow", {})
    vol_surge = stock_info.get("volume_surge", {})
    detail = flow.get("institution_detail", {})

    news_text_list = []
    for i, n in enumerate(news_list, 1):
        news_text_list.append(f"{i}. [{n.get('publisher', '언론사')}] {n.get('title', '')}")
    news_payload = "\n".join(news_text_list)

    prompt = f"""
당신은 월가와 여의도의 최고 수석 주식 애널리스트입니다.
제공된 실시간 주가, 투자자별 수급(외인/기관/개인/연기금/프로그램), 거래량 폭증 지표, 증권사/월가 리포트 및 최신 뉴스를 종합 분석하여 모닝 브리핑을 작성하세요.

[종목 및 시장 수급 팩트]
- 종목명: {name} ({ticker}, {market})
- 현재가 및 등락률: {price} ({change})
- 거래량 상태: {stock_info.get('display_volume')} ({vol_surge.get('badge')}, {vol_surge.get('desc')})
- 수급 동향: 외국인({flow.get('foreign')}), 기관({flow.get('institutional')}), 개인({flow.get('retail')}), 프로그램({flow.get('program')})
- 기관 세부 분류: 연기금({detail.get('pension')}), 금융투자({detail.get('financial_invest')}), 투신({detail.get('trust')}), 사모펀드({detail.get('private_equity')})
- 증권사/월가 투자의견 및 목표가: {consensus.get('opinion', '')} / {consensus.get('display_target_price', '미제공')} (상승여력: {consensus.get('upside_potential', 0)}%)

[최근 24시간 수집된 뉴스 및 리포트 목록]
{news_payload if news_payload else "최근 특이 뉴스 없음, 수급 및 차트 동향 중심 분석"}

[작성 요구사항 - 반드시 아래 JSON 포맷으로 한국어로만 응답]
{{
  "fact": "📰 핵심 뉴스: 기사들의 중복을 없애고 가장 핵심적인 기업 팩트/이슈를 1~2줄 압축",
  "reaction": "💬 시장 & 증권사 반응: 주가 등락과 함께 '외국인/기관/연기금/프로그램 순매수' 및 '거래량 폭증 여부', 증권사/월가 목표주가 평가를 유기적으로 결합하여 1~2줄 작성",
  "upside": "🚀 주가 상승 여력: 실적 성장, 신제품, 수급 주도권(외인/연기금 매수세 등) 모멘텀을 1~2줄 작성",
  "downside": "⚠️ 주가 하락 리스크: 기관/외인 매도 압력, 단기 급등 피로감, 업황 리스크 요인을 1~2줄 작성",
  "sentiment": "bull 또는 bear 또는 neutral 중 택1",
  "sentiment_label": "호재 우세 또는 리스크 주의 또는 중립·관망 중 택1",
  "sentiment_score": -100부터 100 사이의 정수,
  "one_line_summary": "10초 퀵 매트릭스용 핵심 1줄 압축 요약 (35자 내외)"
}}
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2
        }
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        if res.status_code == 200:
            res_data = res.json()
            raw_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(raw_text.strip())
            parsed["ai_engine"] = "Gemini 1.5 Flash AI"
            return parsed
        else:
            return fallback_summarize(stock_info, news_list)
    except Exception as e:
        return fallback_summarize(stock_info, news_list)


def summarize_stock(stock_info: dict, news_list: list) -> dict:
    """Main routing function for stock summarization."""
    if GEMINI_API_KEY:
        return gemini_rest_summarize(stock_info, news_list)
    else:
        return fallback_summarize(stock_info, news_list)
