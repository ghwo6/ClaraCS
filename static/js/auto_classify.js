// ---- 마지막 분류 시각 표시 유틸 ----
function nowStringKST() {
  const parts = new Intl.DateTimeFormat("ko-KR", {
    timeZone: "Asia/Seoul",
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", hour12: false
  }).formatToParts(new Date());
  const get = t => parts.find(p => p.type === t)?.value || "";
  const y = get("year"), m = get("month"), d = get("day");
  const hh = get("hour"), mm = get("minute");
  return `${y}-${m}-${d} ${hh}:${mm}`;
}
function setLastRunLabel(ts) {
  const el = document.getElementById("last-run-at");
  if (!el) return;
  
  // 날짜가 없으면 텍스트도 숨김
  if (!ts || ts === '-') {
    el.textContent = '';
    el.style.display = 'none';
  } else {
    el.textContent = `마지막 분류 : ${ts}`;
    el.style.display = 'inline';
  }
}

// ---------- 유틸 ----------
function truncate15(s) {
  if (!s) return "";
  return [...s].length > 15 ? [...s].slice(0, 15).join("") + "..." : s;
}
function joinKeywords(arr) {
  if (!Array.isArray(arr)) return "";
  return arr.join(", ");
}
function flatAllByCategory(all_by_category) {
  if (!all_by_category) return [];
  // 모든 카테고리의 모든 티켓 (우선순위 기반 정렬)
  const order = ["품질/하자", "서비스", "배송", "AS/수리", "결제", "이벤트", "일반", "기타"];
  const rows = [];
  for (const cat of order) {
    const items = all_by_category[cat] || [];
    for (const it of items) {
      rows.push({
        received_at: it.received_at || "-",
        channel: it.channel || "-",
        content: it.content || "",
        preview: it.preview || truncate15(it.content || ""),
        category: cat,
        keywords: Array.isArray(it.keywords) ? it.keywords : [],
        confidence: it.confidence || "-"
      });
    }
  }
  return rows;
}


// ---------- 렌더 ----------
function renderCategoryTable(rows) {
  const tbody = document.getElementById("categoryTableBody");
  if (!tbody) return;
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td>${r.category}</td>
      <td class="right">${(r.count ?? 0).toLocaleString()}</td>
      <td class="right">${((r.ratio ?? 0)*100).toFixed(1)}%</td>
      <td>${joinKeywords(r.keywords)}</td>
    </tr>
  `).join("");
}

// 채널 도넛 색상/순서 (백엔드 카테고리명과 일치 - 우선순위 기반, 파스텔톤)
const CHANNEL_CATEGORY_ORDER = ["품질/하자", "서비스", "배송", "AS/수리", "결제", "이벤트", "일반", "기타"];
const CHANNEL_CATEGORY_COLORS = {
  "품질/하자": "#FF6384",
  "서비스": "#36A2EB",
  "배송": "#FFCE56",
  "AS/수리": "#4BC0C0",
  "결제": "#9966FF",
  "이벤트": "#FF9F40",
  "일반": "#C9CBCF",
  "기타": "#E7E9ED"
};

// conic-gradient 백그라운드 생성
function donutBackground(byCategory, total){
  let start = 0, segs = [];
  CHANNEL_CATEGORY_ORDER.forEach(cat=>{
    const v = (byCategory?.[cat] || 0);
    const deg = total ? (v/total)*360 : 0;
    if(deg>0) segs.push(`${CHANNEL_CATEGORY_COLORS[cat]} ${start}deg ${start+deg}deg`);
    start += deg;
  });
  return segs.length ? `conic-gradient(${segs.join(",")})` : "#1f2937";
}

function renderChannelCards(items){
  const wrap = document.getElementById("channelCards");
  if(!wrap) return;

  // 채널별 총합 대비 비율(상단 '건수/퍼센트'에 사용+ 중앙 표기에도 사용)
  const grandTotal = items.reduce((acc,cur)=> acc + (cur.count||0), 0) || 1;

  wrap.innerHTML = items.map(x=>{
    const total = x.count || 0;
    const cats  = x.by_category || {};
    const pct   = ((total / grandTotal) * 100).toFixed(1);
    const bg    = donutBackground(cats, total);


    return `
      <div class="channel-card">
        <!-- 1) 채널명(맨 위, 가운데) -->
          <div class="ch-title">${x.channel}</div>
        <!-- 2) 건수/퍼센트(작은 글자, 연한 색) -->
          <div class="ch-sub">${total.toLocaleString()}건 · ${pct}%</div>
        <!-- 3) 도넛(가운데) -->
          <div class="donut" style="background:${bg}" data-total="${total}" data-categories='${JSON.stringify(cats)}'>
            <div class="labels"></div>   <!-- ⬅ 라벨를 올릴 레이어 -->
            <div class="hole">
              <div class="donut-center-text">${total.toLocaleString()}</div>
            </div>     <!-- ⬅ 가운데 수치 표시 -->
          </div>
      </div>
    `;
  }).join("");

// 라벨 배치 및 호버 이벤트 추가
  const cards = Array.from(wrap.querySelectorAll('.channel-card'));
  cards.forEach((card, i) => {
    const donut = card.querySelector('.donut');
    const info  = items[i] || {};
    placeDonutLabels(donut, info.by_category || {}, info.count || 0);
    
    // 호버 툴팁 이벤트 추가
    addDonutHoverTooltip(donut, info.by_category || {}, info.count || 0);
  });

  // 리사이즈 대응 위해 데이터 저장 + 재계산 훅
  window.__lastChannelInfo = items;
  if (!window.__relabelBound) {
    window.__relabelBound = true;
    window.addEventListener('resize', () => {
      clearTimeout(window.__relabelTimer);
      window.__relabelTimer = setTimeout(() => {
        const donuts = document.querySelectorAll('#channelCards .channel-card');
        const data = window.__lastChannelInfo || [];
        donuts.forEach((card, i) => {
          const donut = card.querySelector('.donut');
          const info  = data[i] || {};
          placeDonutLabels(donut, info.by_category || {}, info.count || 0);
        });
      }, 120);
    });
  }


  // 높이 동기화 유지
  if (typeof adjustChannelsPanelHeight === "function") {
    requestAnimationFrame(adjustChannelsPanelHeight);
  }
}

// 도넛 호버 툴팁 추가
function addDonutHoverTooltip(donutElement, byCategory, total) {
  if (!donutElement) return;
  
  let tooltip = null;
  
  donutElement.addEventListener('mouseenter', (e) => {
    if (tooltip) return; // 이미 툴팁이 있으면 중복 생성 방지
    
    // 툴팁 HTML 생성
    let tooltipHtml = '<div class="donut-tooltip">';
    tooltipHtml += '<div class="tooltip-header">카테고리별 분포</div>';
    
    const categories = Object.entries(byCategory)
      .filter(([cat, count]) => count > 0)
      .sort((a, b) => b[1] - a[1]); // 내림차순 정렬
    
    categories.forEach(([category, count]) => {
      const percentage = total > 0 ? ((count / total) * 100).toFixed(1) : 0;
      const color = CHANNEL_CATEGORY_COLORS[category] || '#666';
      
      tooltipHtml += `
        <div class="tooltip-item">
          <span class="tooltip-dot" style="background-color: ${color}"></span>
          <span class="tooltip-category">${category}</span>
          <span class="tooltip-count">${count.toLocaleString()}건</span>
          <span class="tooltip-percentage">(${percentage}%)</span>
        </div>
      `;
    });
    
    tooltipHtml += '</div>';
    
    // 툴팁 요소 생성
    tooltip = document.createElement('div');
    tooltip.innerHTML = tooltipHtml;
    tooltip = tooltip.firstElementChild;
    
    // 툴팁 스타일 적용
    tooltip.style.cssText = `
      position: absolute;
      background: rgba(0, 0, 0, 0.9);
      color: white;
      padding: 12px;
      border-radius: 8px;
      font-size: 12px;
      z-index: 1000;
      pointer-events: none;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      min-width: 200px;
    `;
    
    // 툴팁 위치 계산
    const rect = donutElement.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();
    
    let left = rect.left + rect.width / 2 - tooltipRect.width / 2;
    let top = rect.top - tooltipRect.height - 10;
    
    // 화면 경계 체크
    if (left < 10) left = 10;
    if (left + tooltipRect.width > window.innerWidth - 10) {
      left = window.innerWidth - tooltipRect.width - 10;
    }
    if (top < 10) {
      top = rect.bottom + 10;
    }
    
    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
    
    document.body.appendChild(tooltip);
  });
  
  donutElement.addEventListener('mouseleave', () => {
    if (tooltip) {
      tooltip.remove();
      tooltip = null;
    }
  });
}

// === 라벨 배치 설정값(원하는 대로 조절) ===
const LABEL_PCT_MIN = 1.0;    // 이 % 미만 조각은 라벨 생략
const LABEL_OFFSET_PX = 10;    // 도넛 외곽선에서 바깥쪽으로 얼마나 띄울지(px)

// byCategory: { "배송":123, ... }, total: 수치 합
function placeDonutLabels(el, byCategory, total) {
  if (!el) return;
  const layer = el.querySelector('.labels');
  if (!layer) return;

  layer.innerHTML = '';
  if (!total) return;

  const size = el.clientWidth;        // 도넛 실제 렌더 폭
  const R = size / 2;                 // 반지름
  const labelR = R + LABEL_OFFSET_PX; // 라벨 반경(도넛 바깥)

  let startDeg = 0;
  CHANNEL_CATEGORY_ORDER.forEach(cat => {
    const v = (byCategory?.[cat] || 0);
    if (v <= 0) return;

    const ratio = v / total;
    const deg   = ratio * 360;
    const mid   = startDeg + deg / 2;

    // CSS conic-gradient 기준(우측 = 0deg) → 수학각도로 변환(위쪽= -90 보정)
    const rad = (mid - 90) * Math.PI / 180;

    // 퍼센트 문자열
    const pctStr = (ratio * 100).toFixed(1) + '%';
    if (ratio * 100 < LABEL_PCT_MIN) { startDeg += deg; return; } // 너무 작은 조각은 생략

    // 위치: 중심(50%, 50%)에서 labelR만큼 이동 → % 좌표로 환산
    const x = 50 + (labelR / size * 100) * Math.cos(rad);
    const y = 50 + (labelR / size * 100) * Math.sin(rad);

    const span = document.createElement('span');
    span.className = 'slice-label';
    span.style.left = x + '%';
    span.style.top  = y + '%';
    span.textContent = pctStr;        // 필요하면 `${pctStr}` 대신 `${cat} ${pctStr}`

    layer.appendChild(span);
    startDeg += deg;
  });
}


// 좌측 합계 높이 = 우측(채널) 카드 높이로 정확히 동기화
function syncChannelsHeight() {
  const grid = document.querySelector("#classify .classify-grid");
  const left1 = document.getElementById("catCard");
  const left2 = document.getElementById("reliabilityCard");
  const right = document.getElementById("channelsCard");
  const body = document.getElementById("channelCards");
  if (!grid || !left1 || !left2 || !right || !body) return;

  const rowGap = parseFloat(getComputedStyle(grid).rowGap || "0");  // 좌측 두 카드 사이 간격
  const targetH = left1.offsetHeight + rowGap + left2.offsetHeight;

  // 우측 카드 패딩/보더/헤더 높이 반영
  const cs = getComputedStyle(right);
  const padV = parseFloat(cs.paddingTop || "0") + parseFloat(cs.paddingBottom || "0");
  const brdV = parseFloat(cs.borderTopWidth || "0") + parseFloat(cs.borderBottomWidth || "0");
  const head = right.querySelector(".channels-head");
  const headH = head ? head.offsetHeight : 0;
  const headMB = head ? parseFloat(getComputedStyle(head).marginBottom || "0") : 0; // new!

  // 우측 전체 높이 + 본문 스크롤 높이
  right.style.height = targetH + "px";
  const bodyH = Math.max(0, targetH - padV - brdV - headH - headMB); // new!!
  body.style.height = bodyH + "px";
}

if (!window.__syncResizeBound) {               // 중복 바인딩 방지(스크립트 재로딩 대비)
  window.__syncResizeBound = true;
  window.addEventListener("resize", () => {
    clearTimeout(window.__syncTimer);
    window.__syncTimer = setTimeout(syncChannelsHeight, 120);
  });
}

function renderReliability(r, ui) {
  const box = document.getElementById("reliabilityBox");
  if (!box) return;
  
  const total = r.total_tickets || 0;
  const avgConf = r.average_confidence ?? 0;
  const highCount = r.high_confidence_count || 0;
  const lowCount = r.low_confidence_count || 0;
  const needsReview = r.needs_review_count || 0;
  
  // 신뢰도 기준 상태 판단
  const th = (ui && ui.accuracy_color_thresholds) || { good: 0.90, warn: 0.75 };
  let state = "bad";
  if (avgConf >= th.good) state = "good";
  else if (avgConf >= th.warn) state = "warn";

  // 상태 뱃지
  const badge =
    state === "good" ? `<span class="badge ok">신뢰도 높음</span>` :
    state === "warn" ? `<span class="badge warn">보통</span>` :
                       `<span class="badge danger">재검토 필요</span>`;

  // 신뢰도 퍼센트 표시
  const avgPercent = (avgConf * 100).toFixed(1);
  const highPercent = total > 0 ? ((highCount / total) * 100).toFixed(1) : 0;
  const lowPercent = total > 0 ? ((lowCount / total) * 100).toFixed(1) : 0;

  box.innerHTML = `
    <div style="text-align:center; padding: 12px 0;">
      <div style="margin-bottom:12px">${badge}</div>
      
      <div style="font-size: 28px; font-weight: 700; color: var(--brand); margin-bottom: 8px;">
        ${avgPercent}%
      </div>
      <div style="font-size: 13px; color: var(--muted); margin-bottom: 16px;">
        평균 신뢰도
      </div>
      
      <div style="display: flex; justify-content: space-around; gap: 16px; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--line);">
        <div style="text-align: center;">
          <div style="font-size: 20px; font-weight: 600; color: #10b981;">${highCount}</div>
          <div style="font-size: 11px; color: var(--muted); margin-top: 4px;">높은 신뢰도</div>
          <div style="font-size: 10px; color: var(--muted);">(${highPercent}%)</div>
        </div>
        <div style="text-align: center;">
          <div style="font-size: 20px; font-weight: 600; color: #ef4444;">${needsReview}</div>
          <div style="font-size: 11px; color: var(--muted); margin-top: 4px;">재검토 필요</div>
          <div style="font-size: 10px; color: var(--muted);">(${lowPercent}%)</div>
        </div>
      </div>
    </div>
  `;
}

// 티켓 데이터 저장 (페이지네이션/검색용)
let allTickets = [];
let filteredTickets = [];
let currentPage = 1;
const ITEMS_PER_PAGE = 10;

function renderTicketTableFromAll(all_by_category) {
  const tbody = document.getElementById("ticketTableBody");
  if (!tbody) return;
  
  // 전체 티켓 저장
  allTickets = flatAllByCategory(all_by_category);
  filteredTickets = [...allTickets];
  currentPage = 1;
  
  // 티켓 카운트 업데이트
  updateTicketCount(allTickets.length);
  
  // 검색 및 필터 이벤트 바인딩
  bindSearchEvent();
  bindFilterEvents();
  
  // 첫 페이지 렌더링
  renderTicketTable();
}

function updateTicketCount(count) {
  const countEl = document.getElementById("ticket-count");
  if (countEl) {
    countEl.textContent = `총 ${count.toLocaleString()}건`;
  }
}

function bindSearchEvent() {
  const searchInput = document.getElementById("ticket-search");
  if (!searchInput) return;
  
  // 이미 바인딩 되었으면 스킵
  if (searchInput.dataset.bound) return;
  searchInput.dataset.bound = 'true';
  
  searchInput.addEventListener('input', function(e) {
    applyFilters();
  });
}

function bindFilterEvents() {
  // 필터 이벤트 바인딩
  const dateFilter = document.getElementById('date-filter');
  const channelFilter = document.getElementById('channel-filter');
  const categoryFilter = document.getElementById('category-filter');
  const sortSelect = document.getElementById('sort-select');
  const clearFilters = document.getElementById('clear-filters');
  
  if (dateFilter) {
    dateFilter.addEventListener('change', applyFilters);
  }
  
  if (channelFilter) {
    channelFilter.addEventListener('change', applyFilters);
  }
  
  if (categoryFilter) {
    categoryFilter.addEventListener('change', applyFilters);
  }
  
  if (sortSelect) {
    sortSelect.addEventListener('change', applySorting);
  }
  
  if (clearFilters) {
    clearFilters.addEventListener('click', function() {
      // 모든 필터 초기화
      if (dateFilter) dateFilter.value = '';
      if (channelFilter) channelFilter.value = '';
      if (categoryFilter) categoryFilter.value = '';
      if (sortSelect) sortSelect.value = 'date-desc';
      if (document.getElementById('ticket-search')) {
        document.getElementById('ticket-search').value = '';
      }
      applyFilters();
    });
  }
}

function applyFilters() {
  const searchKeyword = document.getElementById('ticket-search')?.value.toLowerCase().trim() || '';
  const dateFilter = document.getElementById('date-filter')?.value || '';
  const channelFilter = document.getElementById('channel-filter')?.value || '';
  const categoryFilter = document.getElementById('category-filter')?.value || '';
  
  filteredTickets = allTickets.filter(ticket => {
    // 검색어 필터링
    if (searchKeyword) {
      const matchesSearch = (
        (ticket.content && ticket.content.toLowerCase().includes(searchKeyword)) ||
        (ticket.channel && ticket.channel.toLowerCase().includes(searchKeyword)) ||
        (ticket.category && ticket.category.toLowerCase().includes(searchKeyword))
      );
      if (!matchesSearch) return false;
    }
    
    // 날짜 필터링
    if (dateFilter) {
      const ticketDate = new Date(ticket.received_at);
      const now = new Date();
      const daysDiff = Math.floor((now - ticketDate) / (1000 * 60 * 60 * 24));
      
      switch (dateFilter) {
        case 'today':
          if (daysDiff > 0) return false;
          break;
        case 'week':
          if (daysDiff > 7) return false;
          break;
        case 'month':
          if (daysDiff > 30) return false;
          break;
        case 'quarter':
          if (daysDiff > 90) return false;
          break;
      }
    }
    
    // 채널 필터링
    if (channelFilter && ticket.channel !== channelFilter) {
      return false;
    }
    
    // 카테고리 필터링
    if (categoryFilter && ticket.category !== categoryFilter) {
      return false;
    }
    
    return true;
  });
  
  // 정렬 적용
  applySorting();
    
    // 첫 페이지로 리셋
    currentPage = 1;
    updateTicketCount(filteredTickets.length);
    renderTicketTable();
}

function applySorting() {
  const sortSelect = document.getElementById('sort-select');
  if (!sortSelect || !filteredTickets.length) return;
  
  const sortValue = sortSelect.value;
  
  filteredTickets.sort((a, b) => {
    switch (sortValue) {
      case 'date-desc':
        return new Date(b.received_at) - new Date(a.received_at);
      case 'date-asc':
        return new Date(a.received_at) - new Date(b.received_at);
      case 'confidence-desc':
        return getConfidenceValue(b.confidence) - getConfidenceValue(a.confidence);
      case 'confidence-asc':
        return getConfidenceValue(a.confidence) - getConfidenceValue(b.confidence);
      case 'category':
        return (a.category || '').localeCompare(b.category || '');
      case 'channel':
        return (a.channel || '').localeCompare(b.channel || '');
      default:
        return 0;
    }
  });
  
  // 정렬 후 테이블 다시 렌더링
  renderTicketTable();
}

function getConfidenceValue(confidence) {
  const confidenceMap = {
    '상': 3,
    '중': 2,
    '하': 1
  };
  return confidenceMap[confidence] || 0;
}


function renderTicketTable() {
  const tbody = document.getElementById("ticketTableBody");
  if (!tbody) return;
  
  // 페이지네이션 계산
  const totalPages = Math.ceil(filteredTickets.length / ITEMS_PER_PAGE);
  const startIdx = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIdx = startIdx + ITEMS_PER_PAGE;
  const pageTickets = filteredTickets.slice(startIdx, endIdx);
  
  // 티켓이 없을 때
  if (pageTickets.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:40px; color:var(--muted);">
      ${filteredTickets.length === 0 && allTickets.length > 0 ? '검색 결과가 없습니다.' : '티켓 데이터가 없습니다.'}
    </td></tr>`;
    renderPagination(0, 0);
    return;
  }
  
  // 티켓 렌더링
  tbody.innerHTML = pageTickets.map(t => `
    <tr>
      <td>${t.received_at}</td>
      <td>${t.channel}</td>
      <td>${truncate15(t.content)}</td>
      <td>${t.category}</td>
      <td>${joinKeywords(t.keywords)}</td>
      <td class="right">${t.confidence}</td>
    </tr>
  `).join("");
  
  // 페이지네이션 렌더링
  renderPagination(currentPage, totalPages);
}

function renderPagination(current, total) {
  const paginationEl = document.getElementById("ticket-pagination");
  if (!paginationEl) return;
  
  if (total <= 1) {
    paginationEl.innerHTML = '';
    return;
  }
  
  let html = '';
  
  // 이전 버튼
  html += `<button onclick="goToPage(${current - 1})" ${current <= 1 ? 'disabled' : ''}>‹ 이전</button>`;
  
  // 페이지 번호
  const maxButtons = 5;
  let startPage = Math.max(1, current - Math.floor(maxButtons / 2));
  let endPage = Math.min(total, startPage + maxButtons - 1);
  
  // 시작 페이지 조정
  if (endPage - startPage < maxButtons - 1) {
    startPage = Math.max(1, endPage - maxButtons + 1);
  }
  
  // 첫 페이지
  if (startPage > 1) {
    html += `<button onclick="goToPage(1)">1</button>`;
    if (startPage > 2) {
      html += `<span class="page-info">...</span>`;
    }
  }
  
  // 페이지 버튼들
  for (let i = startPage; i <= endPage; i++) {
    html += `<button onclick="goToPage(${i})" class="${i === current ? 'active' : ''}">${i}</button>`;
  }
  
  // 마지막 페이지
  if (endPage < total) {
    if (endPage < total - 1) {
      html += `<span class="page-info">...</span>`;
    }
    html += `<button onclick="goToPage(${total})">${total}</button>`;
  }
  
  // 다음 버튼
  html += `<button onclick="goToPage(${current + 1})" ${current >= total ? 'disabled' : ''}>다음 ›</button>`;
  
  // 페이지 정보
  html += `<span class="page-info">${current} / ${total} 페이지</span>`;
  
  paginationEl.innerHTML = html;
}

function goToPage(page) {
  const totalPages = Math.ceil(filteredTickets.length / ITEMS_PER_PAGE);
  
  if (page < 1 || page > totalPages) return;
  
  currentPage = page;
  renderTicketTable();
  
  // 테이블 상단으로 스크롤
  const ticketCard = document.querySelector('.card--tickets');
  if (ticketCard) {
    ticketCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// 전역 함수로 등록
window.goToPage = goToPage;

// ---------- 로딩 표시 (body 영역 가운데) ----------
function showClassifyLoading(show, progress = 0) {
  const section = document.getElementById("classify");
  if (!section) return;
  
  const bodyDiv = section.querySelector('.body');
  if (!bodyDiv) return;
  
  if (show) {
    // 기존 로딩 인디케이터 제거
    const existingLoading = bodyDiv.querySelector('.loading-indicator');
    if (existingLoading) {
      existingLoading.remove();
    }
    
    // 1. 로딩 인디케이터 생성 (진행률 포함)
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading-indicator';
    loadingDiv.innerHTML = `
      <div class="spinner"></div>
      <p>티켓 분류 중...</p>
      <div class="progress-container">
        <div class="progress-bar">
          <div class="progress-fill" style="width: ${progress}%"></div>
        </div>
        <div class="progress-text">${progress}%</div>
      </div>
    `;
    
    // 2. body 영역에 추가
    bodyDiv.appendChild(loadingDiv);
    
    // 3. 딤드 추가 (동시에)
    section.classList.add('loading');
    
    // 4. 강제 리플로우로 즉시 렌더링
    loadingDiv.offsetHeight;
    
  } else {
    // 동시에 제거
    const loadingDiv = bodyDiv.querySelector('.loading-indicator');
    
    // 1. 로딩 인디케이터 제거
    if (loadingDiv) {
      loadingDiv.remove();
    }
    
    // 2. 딤드 제거
    section.classList.remove('loading');
  }
}

// 진행률 업데이트 함수
function updateClassifyProgress(progress) {
  const progressFill = document.querySelector('.progress-fill');
  const progressText = document.querySelector('.progress-text');
  
  if (progressFill) {
    progressFill.style.width = `${progress}%`;
  }
  
  if (progressText) {
    progressText.textContent = `${progress}%`;
  }
}

// 메시지 토스트 (리포트와 동일한 UI)
function showMessage(message, type = 'info') {
  const existingMessage = document.querySelector('.message-toast');
  if (existingMessage) existingMessage.remove();
  
  const messageDiv = document.createElement('div');
  messageDiv.className = `message-toast ${type}`;
  messageDiv.innerHTML = `
    <span>${message}</span>
    <button onclick="this.parentElement.remove()">×</button>
  `;
  
  document.body.appendChild(messageDiv);
  
  setTimeout(() => {
    if (messageDiv.parentElement) messageDiv.remove();
  }, 3000);  // 3초로 변경 (리포트와 동일)
}

// ---------- 실행 ----------
window.runClassification = async function runClassification() {
  const btn = document.getElementById("btn-run-classify");
  if (!btn) return;
  
  // 선택된 분류 엔진 확인
  const selectedEngine = document.querySelector('input[name="classifier-engine"]:checked')?.value || 'rule';
  const engineName = selectedEngine === 'ai' ? 'AI 기반' : '규칙 기반';
  
  // 버튼 비활성화
  btn.classList.add("active");
  btn.disabled = true;
  
  // 로딩 표시 (버튼 클릭 즉시)
  showClassifyLoading(true, 0);
  
  // 약간의 딜레이를 주어 로딩 화면이 완전히 렌더링되도록 보장
  await new Promise(resolve => setTimeout(resolve, 50));
  
  // 진행률 시뮬레이션 (3분의 1 속도로 조정)
  let progress = 0;
  const progressInterval = setInterval(() => {
    progress += Math.random() * 5; // 15에서 5로 변경 (3분의 1 속도)
    if (progress > 90) progress = 90;
    updateClassifyProgress(Math.floor(progress));
  }, 200);

  try {
    // 선택된 엔진과 함께 전송
    const res = await fetch("/api/classifications/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        user_id: 1, 
        file_id: 0,  // file_id: 0 → 최신 파일 자동 선택
        engine: selectedEngine  // 'rule' 또는 'ai'
      })
    });
    
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.error || `HTTP ${res.status}`);
    }

    const data = await res.json();
    
    // API 응답이 완료되면 프로그래스바를 빠르게 100%로 채우기
    clearInterval(progressInterval);
    
    // 프로그래스바가 100% 미만이면 빠르게 100%로 채우기
    if (progress < 100) {
      const fastProgressInterval = setInterval(() => {
        progress += 10;
        if (progress >= 100) {
          progress = 100;
          clearInterval(fastProgressInterval);
        }
        updateClassifyProgress(Math.floor(progress));
      }, 50); // 빠른 속도로 진행
    } else {
      updateClassifyProgress(100);
    }
    
    // 잠시 완료 상태 표시
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 로딩 종료 (렌더링 전에)
    showClassifyLoading(false);
    
    // 약간의 딜레이 후 렌더링 (로딩 해제 애니메이션 완료 대기)
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // --- 결과 렌더링 ---
    renderCategoryTable(data.category_info || []);
    renderChannelCards(data.channel_info || []);
    renderReliability(data.reliability_info || {}, data.ui || {});
    if (data.tickets?.all_by_category) {
      renderTicketTableFromAll(data.tickets.all_by_category);
    }
    requestAnimationFrame(syncChannelsHeight);

    // --- 마지막 분류 시각 갱신 & 저장 ---
    const ts = nowStringKST();
    setLastRunLabel(ts);
    localStorage.setItem("autoclass:last_run_at", ts);
    localStorage.setItem("autoclass:last", JSON.stringify(data));
    
    // 성공 메시지
    const totalTickets = data.meta?.total_tickets || 0;
    const usedEngine = data.meta?.engine_name || engineName;
    showMessage(`✓ ${totalTickets}건의 티켓 분류 완료 (${usedEngine})`, 'success');
    
  } catch (e) {
    console.error(e);
    // 진행률 중단
    clearInterval(progressInterval);
    showMessage(`✗ 분류 실패: ${e.message}`, 'error');
    // 에러 시에도 로딩 종료
    showClassifyLoading(false);
  } finally {
    // 버튼 활성화
    btn.classList.remove("active");
    btn.disabled = false;
  }
};

// 초기화 함수 추가
function clearUIToInitial() {
  const cat = document.getElementById("categoryTableBody");
  const ch  = document.getElementById("channelCards");
  const rel = document.getElementById("reliabilityBox");
  const tik = document.getElementById("ticketTableBody");
  const pagination = document.getElementById("ticket-pagination");
  const searchInput = document.getElementById("ticket-search");
  
  if (cat) cat.innerHTML = `<tr><td colspan="4">[분류 실행]을 눌러 데이터를 불러오세요</td></tr>`;
  if (ch)  ch.innerHTML  = "";
  if (rel) rel.innerHTML = `-`;
  if (tik) tik.innerHTML = `<tr><td colspan="6">-</td></tr>`;
  if (pagination) pagination.innerHTML = '';
  if (searchInput) searchInput.value = '';
  
  // 티켓 데이터 초기화
  allTickets = [];
  filteredTickets = [];
  currentPage = 1;
  updateTicketCount(0);
  
  setLastRunLabel("-"); // 라벨도 초기화
}

window.resetClassification = function resetClassification() {
  // 로컬 저장 제거
  localStorage.removeItem("autoclass:last");
  localStorage.removeItem("autoclass:last_run_at");
  // 화면 초기화
  clearUIToInitial();
};

(function initializePage() {
  // 페이지 로드 시 마지막 분류 데이터가 있으면 자동으로 로드
  try {
    const ts = localStorage.getItem("autoclass:last_run_at");
    if (ts) setLastRunLabel(ts);

    const raw = localStorage.getItem("autoclass:last");
    if (raw) {
      const data = JSON.parse(raw);
      renderCategoryTable(data.category_info || []);
      renderChannelCards(data.channel_info || []);
      renderReliability(data.reliability_info || {}, data.ui || {});
      if (data.tickets?.all_by_category) {
        renderTicketTableFromAll(data.tickets.all_by_category);
      }
      requestAnimationFrame(syncChannelsHeight);
    } else {
      // 데이터가 없으면 초기 상태로 표시
      clearUIToInitial();
    }
  } catch(e) { 
    console.error('데이터 복원 실패:', e);
    clearUIToInitial();
  }
})();


// ---------- 클릭 바인딩(안전) ----------
(function bindRunButton() {
  function bind() {
    const btn = document.getElementById("btn-run-classify");
    if (!btn) { console.warn("[auto] btn-run-classify not found"); return; }
    btn.addEventListener("click", runClassification);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bind);
  } else {
    bind();
  }
})();

// ---------- 딥러닝 모델 버튼 이벤트 바인딩 ----------
(function bindDeepLearningButton() {
  function bind() {
    const aiRadio = document.querySelector('input[name="classifier-engine"][value="ai"]');
    if (!aiRadio) { console.warn("[auto] AI engine radio not found"); return; }
    
    aiRadio.addEventListener("change", function() {
      if (this.checked) {
        alert("🚧 딥러닝 모델 기능은 현재 준비 중입니다.\n\n키워드 매칭 엔진을 사용해주세요.");
        // 키워드 매칭으로 다시 선택
        const ruleRadio = document.querySelector('input[name="classifier-engine"][value="rule"]');
        if (ruleRadio) {
          ruleRadio.checked = true;
        }
      }
    });
  }
  
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bind);
  } else {
    bind();
  }
})();

