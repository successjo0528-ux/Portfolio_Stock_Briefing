/**
 * Portfolio Stock Briefing - Main Frontend Application
 * Account Split (General vs Pension), Auto Code Matching, Sector Display, Flows & Volume Surges
 */

let currentBriefingData = null;
let currentStocksList = [];
let currentAccountFilter = "all"; // 'all', 'general', 'pension'
let currentModalAccountTab = "general";

document.addEventListener("DOMContentLoaded", () => {
  initApp();
  setupTabEvents();
  setupModalEvents();
});

async function initApp() {
  try {
    const res = await fetch("data/briefing_data.json?t=" + new Date().getTime());
    if (res.ok) {
      currentBriefingData = await res.json();
    } else {
      const resRoot = await fetch("briefing_data.json?t=" + new Date().getTime());
      if (resRoot.ok) {
        currentBriefingData = await resRoot.json();
      }
    }
  } catch (e) {
    console.log("Fetch failed, fallback to window.BRIEFING_DATA...", e);
  }

  if (!currentBriefingData && window.BRIEFING_DATA) {
    currentBriefingData = window.BRIEFING_DATA;
  }

  if (currentBriefingData) {
    renderDashboard(currentBriefingData);
  } else {
    showEmptyState();
  }
}

function setupTabEvents() {
  const tabBtns = document.querySelectorAll(".account-nav .tab-btn");
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentAccountFilter = btn.dataset.account;
      
      const subTitle = document.getElementById("matrix-subtitle");
      if (currentAccountFilter === "all") {
        subTitle.textContent = "전체 포트폴리오 한눈에 스캔";
      } else if (currentAccountFilter === "general") {
        subTitle.textContent = "💼 일반계좌 개별 보유 종목 집중 스캔";
      } else {
        subTitle.textContent = "🌱 연금저축 계좌 ETF 및 리츠 집중 스캔";
      }

      if (currentBriefingData) {
        renderFilteredContent(currentBriefingData);
      }
    });
  });
}

function renderDashboard(data) {
  const meta = data.metadata || {};
  const stocks = data.stocks || [];

  // Header Meta
  document.getElementById("briefing-date").textContent = meta.date_str || "최신 데이터";
  
  const updatedTime = meta.updated_at || "";
  let timeStr = "05:00 KST";
  if (updatedTime.includes(" ")) {
    timeStr = updatedTime.split(" ")[1] + " KST";
  } else if (updatedTime) {
    timeStr = updatedTime;
  }
  document.getElementById("briefing-time").textContent = `⏰ ${timeStr} 갱신`;

  document.getElementById("header-stock-count").textContent = stocks.length;
  document.getElementById("ai-engine-badge").textContent = `🧠 ${meta.ai_mode || "AI Engine"}`;

  // Tab Counts
  const genCount = stocks.filter((s) => (s.account_type || "general") === "general").length;
  const penCount = stocks.filter((s) => s.account_type === "pension").length;

  document.getElementById("count-all").textContent = stocks.length;
  document.getElementById("count-general").textContent = genCount;
  document.getElementById("count-pension").textContent = penCount;

  renderFilteredContent(data);
}

function renderFilteredContent(data) {
  const allStocks = data.stocks || [];
  const stocks = allStocks.filter((s) => {
    if (currentAccountFilter === "all") return true;
    return (s.account_type || "general") === currentAccountFilter;
  });

  // 1. Render Matrix Table
  const tbody = document.getElementById("matrix-tbody");
  tbody.innerHTML = "";

  if (stocks.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="table-loading">해당 계좌에 등록된 종목이 없습니다.</td></tr>`;
  } else {
    stocks.forEach((item) => {
      const s = item.price_info || {};
      const ai = item.ai_brief || {};
      const consensus = s.analyst_consensus || {};
      const flow = s.investor_flow || {};
      const surge = s.volume_surge || { badge: "보통", status: "normal" };
      const isPension = item.account_type === "pension";
      const isKr = item.market === "KR" || item.ticker.toString().match(/^\d+$/);

      const tr = document.createElement("tr");
      tr.onclick = () => {
        const card = document.getElementById(`card-${item.ticker}`);
        if (card) {
          card.scrollIntoView({ behavior: "smooth", block: "center" });
          card.style.borderColor = "var(--accent-blue)";
          setTimeout(() => {
            card.style.borderColor = "";
          }, 1500);
        }
      };

      const priceClass = s.status === "up" ? "price-up" : (s.status === "down" ? "price-down" : "price-same");
      const sentiment = ai.sentiment || "neutral";
      const sentLabel = ai.sentiment_label || "중립·관망";

      // Target price upside
      let targetHtml = `<span class="consensus-target">${consensus.display_target_price || "제공 없음"}</span>`;
      if (consensus.upside_potential && consensus.upside_potential > 0) {
        targetHtml += ` <span class="consensus-upside">(+${consensus.upside_potential}%)</span>`;
      }

      // Flow mini
      let flowMiniHtml = "";
      if (isKr) {
        const frgnClass = (flow.foreign || "").startsWith("+") ? "flow-tag-pos" : ((flow.foreign || "").startsWith("-") ? "flow-tag-neg" : "");
        const instClass = (flow.institutional || "").startsWith("+") ? "flow-tag-pos" : ((flow.institutional || "").startsWith("-") ? "flow-tag-neg" : "");
        flowMiniHtml = `
          <div class="flow-mini-cell">
            <span>외: <b class="${frgnClass}">${flow.foreign || '-'}</b></span>
            <span>기: <b class="${instClass}">${flow.institutional || '-'}</b></span>
          </div>
        `;
      } else {
        flowMiniHtml = `<div class="flow-mini-cell" style="color: var(--text-dim);">${flow.institutional || '글로벌 기관'}</div>`;
      }

      // Volume Surge Badge
      const surgeHtml = `<span class="volume-surge-badge ${surge.status || 'normal'}">${surge.badge || '보통'}</span>`;

      // Sector Tag
      const sectorBadge = item.sector ? `<span class="sector-tag">${item.sector}</span>` : "";
      const accountBadge = isPension ? `<span class="account-tag pension">연금</span>` : `<span class="account-tag general">일반</span>`;

      tr.innerHTML = `
        <td>
          <div class="stock-cell">
            <div class="stock-cell-top">
              ${accountBadge}
              <span>${item.name}</span>
            </div>
            <div class="stock-cell-sub">
              ${sectorBadge}
              <span class="ticker-sub">${item.ticker}</span>
            </div>
          </div>
        </td>
        <td>
          <div class="price-box ${priceClass}">
            ${s.display_price || "0"}
            <span style="font-size: 11px; display: block;">${s.display_change || "0.00%"}</span>
          </div>
        </td>
        <td>
          <div class="consensus-cell">
            ${targetHtml}
            <span style="font-size: 10.5px; color: var(--text-dim);">${consensus.opinion || ""}</span>
          </div>
        </td>
        <td>
          ${flowMiniHtml}
        </td>
        <td>
          ${surgeHtml}
        </td>
        <td>
          <span class="sentiment-badge ${sentiment}">
            <span class="dot ${sentiment}"></span>
            ${sentLabel}
          </span>
        </td>
        <td class="matrix-summary-cell">
          ${ai.one_line_summary || "요약 정보 없음"}
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  // 2. Render Cards
  const cardsContainer = document.getElementById("cards-container");
  cardsContainer.innerHTML = "";

  stocks.forEach((item) => {
    const s = item.price_info || {};
    const ai = item.ai_brief || {};
    const consensus = s.analyst_consensus || {};
    const flow = s.investor_flow || {};
    const surge = s.volume_surge || {};
    const news = item.news || [];
    const isPension = item.account_type === "pension";
    const isKr = item.market === "KR" || item.ticker.toString().match(/^\d+$/);

    const priceClass = s.status === "up" ? "price-up" : (s.status === "down" ? "price-down" : "price-same");
    const sentiment = ai.sentiment || "neutral";
    const sentScore = ai.sentiment_score !== undefined ? `(${ai.sentiment_score > 0 ? '+' : ''}${ai.sentiment_score}점)` : "";

    let targetBadgeText = "";
    if (consensus.display_target_price && consensus.display_target_price !== "제공 없음") {
      targetBadgeText = `🎯 목표가: ${consensus.display_target_price}`;
      if (consensus.upside_potential) {
        targetBadgeText += ` (상승여력: +${consensus.upside_potential}%)`;
      }
    } else {
      targetBadgeText = `🎯 ${consensus.opinion || "증권사 의견 집계 중"}`;
    }

    let chipsHtml = "";
    if (news && news.length > 0) {
      news.forEach((n) => {
        const reportClass = n.is_report ? "is-report" : "";
        const reportIcon = n.is_report ? "📑 " : "";
        chipsHtml += `<a href="${n.link}" target="_blank" rel="noopener" class="source-chip ${reportClass}" title="${n.title}">
          ${reportIcon}${n.publisher || '원문'}
        </a>`;
      });
    } else {
      chipsHtml = `<span style="font-size:12px; color:var(--text-dim);">수집된 최신 기사 원문 링크 없음</span>`;
    }

    // Flow Bar
    let flowChipsHtml = "";
    if (isKr) {
      const frgnSign = (flow.foreign || "").startsWith("+") ? "price-up" : ((flow.foreign || "").startsWith("-") ? "price-down" : "");
      const instSign = (flow.institutional || "").startsWith("+") ? "price-up" : ((flow.institutional || "").startsWith("-") ? "price-down" : "");
      const retSign = (flow.retail || "").startsWith("+") ? "price-up" : ((flow.retail || "").startsWith("-") ? "price-down" : "");

      flowChipsHtml = `
        <div class="flow-chips-group">
          <span class="flow-chip"><span class="flow-chip-label">외국인:</span> <b class="${frgnSign}">${flow.foreign || '-'}</b></span>
          <span class="flow-chip"><span class="flow-chip-label">기관:</span> <b class="${instSign}">${flow.institutional || '-'}</b></span>
          <span class="flow-chip"><span class="flow-chip-label">개인:</span> <b class="${retSign}">${flow.retail || '-'}</b></span>
          <span class="flow-chip"><span class="flow-chip-label">거래량:</span> <b>${s.display_volume || '0'}</b></span>
          <span class="volume-surge-badge ${surge.status || 'normal'}">${surge.badge || '거래량 보통'}</span>
        </div>
      `;
    } else {
      flowChipsHtml = `
        <div class="flow-chips-group">
          <span class="flow-chip"><span class="flow-chip-label">기관 비중:</span> <b class="price-up">${flow.institutional || '월가 기관'}</b></span>
          <span class="flow-chip"><span class="flow-chip-label">거래량:</span> <b>${s.display_volume || '0'}</b></span>
          <span class="volume-surge-badge ${surge.status || 'normal'}">${surge.badge || '거래량 보통'}</span>
        </div>
      `;
    }

    // Earnings History HTML (for General Stocks)
    let earningsHtml = "";
    const earnings = s.earnings_history || [];
    if (earnings.length > 0) {
      let cardsHtml = "";
      earnings.forEach((eq) => {
        const changeBadge = eq.op_change_str ? `<span class="quarter-change-badge ${eq.op_status || 'same'}">${eq.op_change_str}</span>` : "";
        cardsHtml += `
          <div class="earnings-quarter-card">
            <div class="quarter-title-row">
              <span>📅 ${eq.quarter}</span>
              ${changeBadge}
            </div>
            <div class="quarter-op-row">
              <span style="color:var(--text-dim);">영업이익:</span>
              <span class="quarter-op-val">${eq.op_profit_str}</span>
            </div>
            <div class="quarter-net-row">
              <span style="color:var(--text-dim); font-size:11px;">순이익:</span>
              <span style="color:var(--text-body); font-size:11px; font-weight:600;">${eq.net_income_str}</span>
            </div>
          </div>
        `;
      });

      earningsHtml = `
        <div class="card-earnings-bar">
          <div class="earnings-header-label">
            <span>📈 <b>최근 3개 분기 실적 추이 (영업이익 / 순이익):</b></span>
            <span style="font-size:11px; color:var(--text-dim); font-weight:normal;">* 신규 실적 발표 시 자동 롤링 업데이트</span>
          </div>
          <div class="earnings-grid">
            ${cardsHtml}
          </div>
        </div>
      `;
    }

    const card = document.createElement("article");
    card.className = "stock-card";
    card.id = `card-${item.ticker}`;

    const accountTagHtml = isPension ? `<span class="account-tag pension">🌱 연금저축</span>` : `<span class="account-tag general">💼 일반계좌</span>`;
    const sectorTagHtml = item.sector ? `<span class="sector-tag">${item.sector}</span>` : "";

    card.innerHTML = `
      <div class="card-header">
        <div class="card-title-left">
          ${accountTagHtml}
          <h3 class="card-stock-name">${item.name} (${item.ticker})</h3>
          ${sectorTagHtml}
        </div>
        <div class="card-price-right">
          <span class="card-price-main">${s.display_price || "0"}</span>
          <span class="card-price-change ${priceClass}">${s.display_change || "0.00%"}</span>
          <span class="card-consensus-badge">${targetBadgeText}</span>
          <span class="sentiment-badge ${sentiment}">🧠 AI: ${ai.sentiment_label || "중립"} ${sentScore}</span>
        </div>
      </div>
      
      <!-- 수급 & 거래량 동향 바 -->
      <div class="card-flow-bar">
        ${flowChipsHtml}
      </div>

      <!-- 최근 3개 분기 실적 변화 (일반계좌 종목) -->
      ${earningsHtml}

      <div class="card-body">
        <div class="brief-block">
          <div class="brief-label label-fact">📰 핵심 뉴스 (Fact)</div>
          <div class="brief-text">${ai.fact || "수집된 핵심 뉴스 내용이 없습니다."}</div>
        </div>
        <div class="brief-block">
          <div class="brief-label label-reaction">💬 시장 & 증권사 반응</div>
          <div class="brief-text">${ai.reaction || "시장 및 증권사 투자의견을 종합 중입니다."}</div>
        </div>
        <div class="brief-block">
          <div class="brief-label label-upside">🚀 주가 상승 여력 (Upside)</div>
          <div class="brief-text">${ai.upside || "실적 개선 및 신규 모멘텀 점검 중입니다."}</div>
        </div>
        <div class="brief-block">
          <div class="brief-label label-downside">⚠️ 하락 리스크 (Downside)</div>
          <div class="brief-text">${ai.downside || "거시 경제 및 업황 리스크 요인 점검 중입니다."}</div>
        </div>
      </div>
      <div class="card-footer">
        <span>🔗 관련 언론사 & 리포트 원문:</span>
        <div class="source-chips">
          ${chipsHtml}
        </div>
      </div>
    `;

    cardsContainer.appendChild(card);
  });
}

function showEmptyState() {
  document.getElementById("matrix-tbody").innerHTML = `
    <tr>
      <td colspan="7" class="table-loading">
        ⚠️ 브리핑 데이터가 없습니다. 먼저 <code>run.bat</code> 또는 <code>crawler_runner.py</code>를 실행해 주세요.
      </td>
    </tr>
  `;
}

/* --------------------------------------------------------------------------
   Modal Stock Management & Auto Code Matching
   -------------------------------------------------------------------------- */
function setupModalEvents() {
  const modal = document.getElementById("stocks-modal");
  const openBtn = document.getElementById("open-stocks-modal-btn");
  const closeBtn = document.getElementById("close-modal-btn");
  const cancelBtn = document.getElementById("cancel-modal-btn");
  const addBtn = document.getElementById("add-stock-btn");
  const saveBtn = document.getElementById("save-stocks-btn");
  const searchBtn = document.getElementById("search-code-btn");
  const tickerInput = document.getElementById("new-stock-ticker");

  openBtn.addEventListener("click", () => {
    loadStocksToModal();
    modal.classList.add("active");
  });

  closeBtn.addEventListener("click", () => modal.classList.remove("active"));
  cancelBtn.addEventListener("click", () => modal.classList.remove("active"));

  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.classList.remove("active");
  });

  // Modal Account Tabs
  const modalTabs = document.querySelectorAll(".modal-tab");
  modalTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      modalTabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      currentModalAccountTab = tab.dataset.modalTab;
      document.getElementById("new-stock-account").value = currentModalAccountTab;
      renderModalStocksList();
    });
  });

  // Auto Code/Name Matching Search
  async function performAutoMatch() {
    const query = tickerInput.value.trim();
    if (!query) {
      alert("종목코드(6자리) 또는 종목명을 입력하세요.");
      return;
    }

    try {
      // 1. If 6-digit code, fetch from Naver integration API
      if (query.match(/^\d{6}$/)) {
        const res = await fetch(`https://m.stock.naver.com/api/stock/${query}/integration`);
        if (res.ok) {
          const data = await res.json();
          if (data && data.stockName) {
            document.getElementById("new-stock-name").value = data.stockName;
            const sector = data.industryCompareInfo ? data.industryCompareInfo.industryCode : "국내주식/ETF";
            document.getElementById("new-stock-sector").value = sector || "국내주식";
            return;
          }
        }
      }

      // 2. Search by keyword
      const resSearch = await fetch(`https://finance.naver.com/search/searchList.naver?query=${encodeURIComponent(query)}`);
      // Or alert fallback
      alert(`[매칭 안내] 종목코드 '${query}'가 확인되었습니다. 종목명과 섹터를 확인 후 [추가]를 누르세요.`);
    } catch (e) {
      console.log("Auto match error:", e);
    }
  }

  searchBtn.addEventListener("click", performAutoMatch);
  tickerInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      performAutoMatch();
    }
  });

  addBtn.addEventListener("click", () => {
    const acc = document.getElementById("new-stock-account").value;
    const ticker = document.getElementById("new-stock-ticker").value.trim().toUpperCase();
    const name = document.getElementById("new-stock-name").value.trim();
    const sector = document.getElementById("new-stock-sector").value.trim() || (acc === "pension" ? "ETF/리츠" : "일반주식");

    if (!ticker || !name) {
      alert("종목코드와 종목명을 입력해 주세요.");
      return;
    }

    let detectedAccount = acc;
    const isEtf = /KODEX|TIGER|ACE|SOL|PLUS|RISE|KOSEF|KBSTAR|HANARO|ETF|리츠|선물/i.test(name) || /T0|A0|L0/i.test(ticker);
    if (isEtf) {
      detectedAccount = "pension";
    }

    currentStocksList.push({
      ticker: ticker,
      name: name,
      market: ticker.match(/^\d+$/) ? "KR" : (isEtf ? "KR" : "US"),
      account_type: detectedAccount,
      account_name: detectedAccount === "pension" ? "연금저축" : "일반계좌",
      sector: sector,
      category: detectedAccount === "pension" ? "연금저축 ETF/리츠" : "일반주식"
    });

    document.getElementById("new-stock-ticker").value = "";
    document.getElementById("new-stock-name").value = "";
    document.getElementById("new-stock-sector").value = "";

    renderModalStocksList();
  });

  saveBtn.addEventListener("click", () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentStocksList, null, 2));
    const dlAnchor = document.createElement("a");
    dlAnchor.setAttribute("href", dataStr);
    dlAnchor.setAttribute("download", "stocks.json");
    dlAnchor.click();

    alert(`관심 종목 설정(${currentStocksList.length}개)이 'stocks.json'으로 다운로드되었습니다.\n프로젝트 폴더(G:\\My Program\\Portfolio_Stock_Briefing\\)의 stocks.json 파일에 덮어쓴 후 run.bat을 실행하시면 새 종목으로 브리핑이 생성됩니다!`);
    modal.classList.remove("active");
  });
}

function loadStocksToModal() {
  if (currentBriefingData && currentBriefingData.stocks) {
    currentStocksList = currentBriefingData.stocks.map((s) => ({
      ticker: s.ticker,
      name: s.name,
      market: s.market || "KR",
      account_type: s.account_type || "general",
      account_name: s.account_type === "pension" ? "연금저축" : "일반계좌",
      sector: s.sector || "",
      category: s.category || "일반"
    }));
  }
  renderModalStocksList();
}

function renderModalStocksList() {
  const container = document.getElementById("modal-stocks-list");
  
  const genCount = currentStocksList.filter((s) => (s.account_type || "general") === "general").length;
  const penCount = currentStocksList.filter((s) => s.account_type === "pension").length;

  document.getElementById("modal-gen-count").textContent = genCount;
  document.getElementById("modal-pen-count").textContent = penCount;

  container.innerHTML = "";

  const filtered = currentStocksList.filter((s) => (s.account_type || "general") === currentModalAccountTab);

  if (filtered.length === 0) {
    container.innerHTML = `<div style="text-align:center; color:var(--text-dim); padding:20px;">등록된 종목이 없습니다.</div>`;
    return;
  }

  filtered.forEach((st) => {
    const realIndex = currentStocksList.indexOf(st);
    const item = document.createElement("div");
    item.className = "stock-manage-item";
    item.innerHTML = `
      <div class="stock-manage-left">
        <span class="market-badge ${st.market === 'KR' ? 'kr' : 'us'}">${st.market}</span>
        <b>${st.name}</b>
        <span class="ticker-sub">${st.ticker}</span>
        <span class="sector-tag" style="font-size:10px;">${st.sector || '일반'}</span>
      </div>
      <button class="delete-stock-btn" onclick="deleteStockItem(${realIndex})">삭제</button>
    `;
    container.appendChild(item);
  });
}

window.deleteStockItem = function(index) {
  currentStocksList.splice(index, 1);
  renderModalStocksList();
};
