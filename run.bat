@echo off
chcp 65001 > nul
title Portfolio Stock Briefing Launcher

echo =====================================================================
echo   [Portfolio Stock Briefing] 보유/관심 종목 모닝 스마트 브리핑
echo =====================================================================
echo.

cd /d "%~dp0"

echo [1/2] 최신 주가 시세, 뉴스, 증권사 리포트 크롤링 및 AI 요약 중...
python crawler_runner.py

echo.
echo [2/2] 로컬 브리핑 대시보드를 실행합니다...
python launcher.py

pause
