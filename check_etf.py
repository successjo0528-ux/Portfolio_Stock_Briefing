# -*- coding: utf-8 -*-
import sys
import requests

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

res = requests.get('https://finance.naver.com/api/sise/etfItemList.nhn', headers={'User-Agent': 'Mozilla/5.0'}).json()
items = res.get('result', {}).get('etfItemList', [])
print(f"Total ETFs in Korea: {len(items)}")

pension_names = [
    "SOL 화장품",
    "KODEX 미국휴머노이드",
    "TIGER 미국초단기",
    "차이나휴머노이드",
    "TIGER 농산물",
    "TIGER 구리",
    "TIGER 코스닥150",
    "TIGER 2차전지",
    "KODEX 미국S&P500",
    "KODEX 미국나스닥100",
    "SK리츠",
    "ACE KRX금현물",
    "ACE 글로벌자율주행",
    "TIGER 종합채권",
    "ACE 미국30년국채",
    "ACE 테슬라",
    "TIGER 미국배당",
    "일본엔화"
]

matched_dict = {}

for p in pension_names:
    found = []
    for it in items:
        # Check keyword in it['itemname']
        parts = p.split()
        if all(part.lower() in it.get('itemname', '').lower() for part in parts):
            found.append((it.get('itemcode'), it.get('itemname'), it.get('nowVal'), it.get('changeVal'), it.get('changeRate')))
    matched_dict[p] = found

for p, found in matched_dict.items():
    if found:
        print(f"[{p}] -> {found[0][0]}: {found[0][1]} (현재가: {found[0][2]:,}원, {found[0][4]}%)")
    else:
        print(f"[{p}] -> Not found in ETF list")
