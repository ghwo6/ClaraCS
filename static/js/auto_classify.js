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

function renderChannelCards(items) {
  const wrap = document.getElementById("channelCards");
  if (!wrap) return;
  wrap.innerHTML = items.map(x => {
    const total = x.count || 0;
    const cats = x.by_category || {};
    const catList = Object.entries(cats).map(([k,v]) =>
      `<li>${k}: ${v.toLocaleString()} (${(v/total*100).toFixed(1)}%)</li>`
    ).join("");
    return `
      <div class="channel-card">
        <div class="title">${x.channel}</div>
        <div class="big">${total.toLocaleString()}</div>
        <ul class="mini">${catList}</ul>
      </div>
    `;
  }).join("");
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

  // 상태 뱃지 색상은 기존 CSS 배지 스타일 활용(없으면 텍스트만 출력됩니다)
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

// ---------- 실행 ----------
window.runClassification = async function runClassification() {
  const btn = document.getElementById("btn-run-classify");
  btn?.classList.add("active");
  if (btn) btn.disabled = true;

  try {
    const res = await fetch("/api/classifications/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: 1, file_id: 123 })
    });
    if (!res.ok) throw new Error("HTTP " + res.status);

    const data = await res.json();
    // --- 기존 렌더링 ---
    renderCategoryTable(data.category_info || []);
    renderChannelCards(data.channel_info || []);
    renderReliability(data.reliability_info || {}, data.ui || {});
    if (data.tickets?.top3_by_category) {
      renderTicketTableFromTop3(data.tickets.top3_by_category);
    }

    // --- 여기서만(성공 시) 마지막 분류 시각 갱신 & 저장 ---
    const ts = nowStringKST();
    setLastRunLabel(ts);
    localStorage.setItem("autoclass:last_run_at", ts);
    // (선택) 결과 데이터도 계속 저장
    localStorage.setItem("autoclass:last", JSON.stringify(data));
  } catch (e) {
    console.error(e);
    alert("분류 요청 실패: " + e.message);
  } finally {
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


// 페이지 로드 시 마지막 분류 시각 복원
(function restoreLastRunAt() {
  const saved = localStorage.getItem("autoclass:last_run_at");
  if (saved) setLastRunLabel(saved);
})();
