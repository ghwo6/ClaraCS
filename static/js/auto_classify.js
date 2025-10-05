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
  if (el) el.textContent = `마지막 분류 : ${ts}`;
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
function flatTop3ByCategory(top3_by_category) {
  if (!top3_by_category) return [];
  // 카테고리 5개 * 각 3건 = 최대 15건
  const order = ["배송","환불/취소","품질/하자","AS/설치","기타"];
  const rows = [];
  for (const cat of order) {
    const items = top3_by_category[cat] || [];
    for (const it of items) {
      rows.push({
        received_at: it.received_at || "-",
        channel: it.channel || "-",
        content: it.content || "",
        preview: it.preview || truncate15(it.content || ""),
        category: cat,
        keywords: Array.isArray(it.keywords) ? it.keywords : [],
        importance: it.importance || "-"
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

// 채널 도넛 색상/순서 (백엔드 카테고리명과 일치)
const CHANNEL_CATEGORY_ORDER = ["배송 문의","환불/교환","상품 문의","기술 지원","불만/클레임","기타"];
const CHANNEL_CATEGORY_COLORS = {
  "배송 문의": "#ef4444",      // 빨강
  "환불/교환": "#f59e0b",      // 주황
  "상품 문의": "#10b981",      // 초록
  "기술 지원": "#3b82f6",      // 파랑
  "불만/클레임": "#ff7875",    // 분홍
  "기타": "#9ca3af"           // 회색
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
          <div class="donut" style="background:${bg}">
            <div class="labels"></div>   <!-- ⬅ 라벨를 올릴 레이어 -->
            <div class="hole"></div>     <!-- ⬅ 가운데는 비워둠(중앙 % 제거) -->
             
          </div>
      </div>
    `;
  }).join("");

// 라벨 배치
  const cards = Array.from(wrap.querySelectorAll('.channel-card'));
  cards.forEach((card, i) => {
    const donut = card.querySelector('.donut');
    const info  = items[i] || {};
    placeDonutLabels(donut, info.by_category || {}, info.count || 0);
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
  const split = r.split || {};
  const acc = r.accuracy ?? 0;
  const th = (ui && ui.accuracy_color_thresholds) || { good: 0.95, warn: 0.90 };
  let state = "bad";
  if (acc >= th.good) state = "good";
  else if (acc >= th.warn) state = "warn";

  // 상태 뱃지 색상은 기존 CSS 배지 스타일 활용(없으면 텍스트만 출력)
  const badge =
    state === "good" ? `<span class="badge ok">정확도 양호</span>` :
    state === "warn" ? `<span class="badge warn">주의</span>` :
                       `<span class="badge danger">개선 필요</span>`;

  box.innerHTML = `
    <div style="text-align:center">
      <div style="margin-bottom:6px">${badge}</div>
      <div>train/val/test = ${split.train || 0} / ${split.val || 0} / ${split.test || 0} (%)</div>
      <div style="margin-top:4px">
        macro-F1: <b>${(r.macro_f1 || 0).toFixed(3)}</b> · 
        micro-F1: <b>${(r.micro_f1 || 0).toFixed(3)}</b> · 
        acc: <b>${acc.toFixed(3)}</b>
      </div>
    </div>
  `;
}

function renderTicketTableFromTop3(top3_by_category) {
  const tbody = document.getElementById("ticketTableBody");
  if (!tbody) return;
  const rows = flatTop3ByCategory(top3_by_category); // 최대 15건
  tbody.innerHTML = rows.map(t => `
    <tr>
      <td>${t.received_at}</td>
      <td>${t.channel}</td>
      <td>${truncate15(t.content)}</td>
      <td>${t.category}</td>
      <td>${joinKeywords(t.keywords)}</td>
      <td class="right">${t.importance}</td>
    </tr>
  `).join("");
}

// ---------- 로딩 표시 (리포트와 동일한 UI) ----------
function showClassifyLoading(show) {
  const section = document.getElementById("classify");
  if (!section) return;
  
  if (show) {
    section.classList.add('loading');
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading-indicator';
    loadingDiv.innerHTML = `
      <div class="spinner"></div>
      <p>티켓 분류 중...</p>
    `;
    section.appendChild(loadingDiv);
  } else {
    section.classList.remove('loading');
    const loadingDiv = section.querySelector('.loading-indicator');
    if (loadingDiv) loadingDiv.remove();
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
  btn?.classList.add("active");
  if (btn) btn.disabled = true;

  // 선택된 분류 엔진 확인
  const selectedEngine = document.querySelector('input[name="classifier-engine"]:checked')?.value || 'rule';
  const engineName = selectedEngine === 'ai' ? 'AI 기반' : '규칙 기반';
  
  // 로딩 표시
  showClassifyLoading(true);

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
    // --- 기존 렌더링 ---
    renderCategoryTable(data.category_info || []);
    renderChannelCards(data.channel_info || []);
    renderReliability(data.reliability_info || {}, data.ui || {});
    if (data.tickets?.top3_by_category) {
      renderTicketTableFromTop3(data.tickets.top3_by_category);
    }
    requestAnimationFrame(syncChannelsHeight);

    // --- 여기서만(성공 시) 마지막 분류 시각 갱신 & 저장 ---
    const ts = nowStringKST();
    setLastRunLabel(ts);
    localStorage.setItem("autoclass:last_run_at", ts);
    // (선택) 결과 데이터도 계속 저장
    localStorage.setItem("autoclass:last", JSON.stringify(data));
    
    // 성공 메시지
    const totalTickets = data.meta?.total_tickets || 0;
    const usedEngine = data.meta?.engine_name || engineName;
    showMessage(`✓ ${totalTickets}건의 티켓 분류 완료 (${usedEngine})`, 'success');
    
  } catch (e) {
    console.error(e);
    showMessage(`✗ 분류 실패: ${e.message}`, 'error');
  } finally {
    // 로딩 종료
    showClassifyLoading(false);
    btn?.classList.remove("active");
    if (btn) btn.disabled = false;
  }
};

// 초기화 함수 추가
function clearUIToInitial() {
  const cat = document.getElementById("categoryTableBody");
  const ch  = document.getElementById("channelCards");
  const rel = document.getElementById("reliabilityBox");
  const tik = document.getElementById("ticketTableBody");
  if (cat) cat.innerHTML = `<tr><td colspan="4">[분류 실행]을 눌러 데이터를 불러오세요</td></tr>`;
  if (ch)  ch.innerHTML  = "";
  if (rel) rel.innerHTML = `-`;
  if (tik) tik.innerHTML = `<tr><td colspan="6">-</td></tr>`;
  setLastRunLabel("-"); // 라벨도 초기화
}

window.resetClassification = function resetClassification() {
  // 로컬 저장 제거
  localStorage.removeItem("autoclass:last");
  localStorage.removeItem("autoclass:last_run_at");
  // 화면 초기화
  clearUIToInitial();
};

(function restoreLastState() {
  try {
    const ts = localStorage.getItem("autoclass:last_run_at");
    if (ts) setLastRunLabel(ts);

    const raw = localStorage.getItem("autoclass:last");
    if (raw) {
      const data = JSON.parse(raw);
      renderCategoryTable(data.category_info || []);
      renderChannelCards(data.channel_info || []);
      renderReliability(data.reliability_info || {}, data.ui || {});
      if (data.tickets?.top3_by_category) {
        renderTicketTableFromTop3(data.tickets.top3_by_category);
      }
      requestAnimationFrame(syncChannelsHeight); //new!
    } else {
      // 완전 초기 상태 보장
      clearUIToInitial();
    }
  } catch { /* 무시 */ }
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

