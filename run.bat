@echo off
chcp 65001 > nul
cd /d "%~dp0"
title Portfolio Stock Briefing Launcher

echo =====================================================================
echo   [Portfolio Stock Briefing] 보유/관심 종목 모닝 스마트 브리핑
echo =====================================================================
echo.
echo 1. 최신 데이터 크롤링 및 웹 대시보드 실행 (로컬 직접 크롤링)
echo 2. 기존 데이터로 바로 웹 대시보드 열기
echo 3. 최신 데이터 크롤링만 실행
echo 4. GitHub 원격 최신 데이터 동기화 (git pull) 후 대시보드 열기 (추천)
echo.
set /p opt="실행할 번호를 입력하세요 (기본값: 4): "
if "%opt%"=="" set opt=4

if "%opt%"=="1" goto opt1
if "%opt%"=="2" goto opt2
if "%opt%"=="3" goto opt3
if "%opt%"=="4" goto opt4
goto opt4

:opt4
echo.
echo [1/2] GitHub에서 최신 브리핑 데이터를 동기화합니다 (git pull)...
git pull origin main
echo.
echo [2/2] 로컬 웹 브리핑 대시보드를 시작합니다...
python launcher.py
goto end

:opt1
echo.
echo [1/2] 최신 주가 시세, 뉴스, 증권사 리포트 크롤링 및 AI 요약 중...
python crawler_runner.py
echo.
echo [2/2] 로컬 웹 브리핑 대시보드를 시작합니다...
python launcher.py
goto end

:opt2
echo.
echo 로컬 웹 브리핑 대시보드를 시작합니다...
python launcher.py
goto end

:opt3
echo.
echo 데이터 크롤링 및 AI 요약을 실행합니다...
python crawler_runner.py
pause
goto end

:end
