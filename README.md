# 📊 Portfolio Stock Daily Intelligence Briefing

보유 및 관심 종목(일반계좌 27개 + 연금저축 18개)의 **실시간 시세, 외인/기관 수급, 프로그램 매매, 거래량 폭증 감지, 증권사 목표가 컨센서스, 최신 뉴스 4대 블록 AI 요약**을 매일 새벽 05:00 KST에 무인 자동으로 수집·발행하는 데일리 인텔리전스 시스템입니다.

---

## 🌟 주요 핵심 기능

1. **⚡ 10초 모닝 퀵 매트릭스 & 심층 브리핑 카드**
   - **계좌 분리 탭**: `[🌐 전체 (45)]`, `[💼 일반계좌 (27)]`, `[🌱 연금저축 (18)]` 원클릭 뷰 전환.
   - **수급 대시보드**: 외국인, 기관(연기금/금융투자/투신/사모 세부 분류), 개인 순매수 금액 집계.
   - **거래량 폭증 감지**: 20일 평균 대비 `🚨 역대급 거래량 폭증 (400%+)` 및 `💥 급증 (200%+)` 뱃지 알림.
   - **증권사 컨센서스**: 국내/미국 증권사 투자의견, 목표주가, 상승 여력(%) 자동 계산.
   - **4대 블록 브리핑**: 📰 팩트 뉴스 / 💬 시장·수급 반응 / 🚀 상승 여력 / ⚠️ 하락 리스크.

2. **⏰ 매일 아침 05:00 KST 무인 자동 크롤링 (GitHub Actions)**
   - PC 전원이 꺼져 있어도 GitHub 클라우드 러너가 매일 새벽 5시에 최신 데이터를 수집하고 웹페이지를 자동 갱신합니다.

3. **📱 웹 브런치(GitHub Pages) 형태로 모바일/PC 어디서나 열람**
   - 별도 앱 설치 없이 스마트폰 브라우저나 PC에서 나만의 전용 데일리 브리핑 웹사이트로 열람 가능.

---

## 🚀 GitHub 배포 및 모바일 웹(Pages) 설정 가이드

### 1단계: GitHub 새 저장소(Repository) 생성
1. [GitHub.com](https://github.com)에 로그인 후 우측 상단 `+` > **New repository** 클릭
2. Repository name 입력 (예: `Portfolio_Stock_Briefing`)
3. **Public** 선택 후 **Create repository** 클릭

### 2단계: 프로젝트 코드 업로드 (원클릭)
1. 폴더 내 [`push_to_github.bat`](file:///G:/My%20Program/Portfolio_Stock_Briefing/push_to_github.bat) 파일을 더블 클릭합니다.
2. 생성한 GitHub 저장소 주소(예: `https://github.com/아이디/Portfolio_Stock_Briefing.git`)를 붙여넣고 엔터를 치면 전체 파일이 즉시 업로드됩니다.

### 3단계: GitHub Pages 활성화 (나만의 모바일 브리핑 웹사이트 오픈)
1. GitHub 저장소 상단 메뉴의 **Settings** > 좌측 사이드바 **Pages** 클릭
2. **Build and deployment** 섹션의 Source에서 **Deploy from a branch** 선택
3. Branch를 `main` / 폴더를 `/ (root)`로 지정하고 **Save** 클릭
4. 약 1~2분 후 상단에 생성되는 나만의 전용 웹사이트 링크(`https://아이디.github.io/Portfolio_Stock_Briefing/`)를 스마트폰 홈 화면에 바로가기 추가하시면 매일 아침 브런치 매거진처럼 열람하실 수 있습니다!

### 4단계: (선택) Gemini API 키 등록 (AI 심층 요약 활성화)
- 저장소 **Settings** > **Secrets and variables** > **Actions** 이동
- **New repository secret** 클릭
- Name: `GEMINI_API_KEY`, Secret: `발급받은 구글 제미나이 API 키` 입력 후 저장

---

## 💡 종목 추가 및 자동 매칭 안내

- 웹 화면 상단의 **[⚙️ 종목 관리]** 버튼을 누르신 후, **종목코드 6자리(예: `005930`, `0008T0`)**만 입력하고 **[🔍 자동 매칭]**을 누르시면 종목명과 섹터, 카테고리가 자동으로 채워집니다.
- 매일 새벽 5시 자동 크롤러가 동작할 때도 새 종목의 시세, 수급, 뉴스, 목표가를 자동으로 분석하여 대시보드에 업데이트합니다.
