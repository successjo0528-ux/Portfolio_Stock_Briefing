@echo off
chcp 65001 > nul
cls
echo =================================================================
echo   [Portfolio Stock Briefing] GitHub Repository Push Tool
echo =================================================================
echo.

set /p REPO_URL="GitHub 저장소 URL을 입력하세요 (예: https://github.com/your-name/Portfolio_Stock_Briefing.git): "

if "%REPO_URL%"=="" (
    echo [오류] GitHub 저장소 URL이 입력되지 않았습니다.
    pause
    exit /b
)

echo.
echo [1/4] Git 저장소 초기화 및 브랜치 설정...
git init
git branch -M main

echo.
echo [2/4] 전체 소스코드 및 브리핑 데이터 추가...
git add .

echo.
echo [3/4] 변경사항 커밋...
git commit -m "🚀 Initial Commit: Portfolio Stock Intelligence Briefing (45 stocks, flows, consensus, volume surge)"

echo.
echo [4/4] 원격 저장소 연결 및 GitHub 푸시...
git remote remove origin > nul 2>&1
git remote add origin %REPO_URL%
git push -u origin main --force

echo.
echo =================================================================
echo   [완료] GitHub에 성공적으로 업로드되었습니다!
echo   
echo   [GitHub Pages 활성화 방법 (웹 브라우저로 매일 보기)]
echo   1. GitHub 저장소 페이지 > Settings > Pages 이동
echo   2. Branch를 'main' / Folder를 '/ (root)'로 선택 후 Save
echo   3. 1~2분 후 나오는 주소(예: https://아이디.github.io/레포명/)로 접속하시면
echo      스마트폰과 PC에서 매일 아침 모바일 웹 브런치 형태로 보실 수 있습니다!
echo =================================================================
pause
