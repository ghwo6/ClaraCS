// static/js/auto_classify.js  (전체 교체본)

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
async function runClassification() {
  const btn = document.getElementById("btn-run-classify");
  btn.classList.add("active");
  btn.disabled = true;
  try {
    const res = await fetch("/api/classifications/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: 1, file_id: 123 })
    });
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    console.log("[auto] API result:", data);

    renderCategoryTable(data.category_info || []);
    renderChannelCards(data.channel_info || []);
    renderReliability(data.reliability_info || {}, data.ui || {});
    // 새로운 스키마(tickets.top3_by_category)에 맞춰 렌더
    if (data.tickets && data.tickets.top3_by_category) {
      renderTicketTableFromTop3(data.tickets.top3_by_category);
    } else if (Array.isArray(data.ticket_info)) {
      // 구 스키마가 올 경우를 위한 하위호환(필드 매핑)
      const tbody = document.getElementById("ticketTableBody");
      tbody.innerHTML = data.ticket_info.map(t => `
        <tr>
          <td>${t.created_at || "-"}</td>
          <td>${t.channel || "-"}</td>
          <td>${truncate15(t.title || t.content || "")}</td>
          <td>${t.category || "-"}</td>
          <td>${joinKeywords(t.keywords || [])}</td>
          <td class="right">${t.reliability ? (t.reliability*100).toFixed(1)+"%" : (t.importance || "-")}</td>
        </tr>
      `).join("");
    }
  } catch (e) {
    console.error(e);
    alert("분류 요청 실패: " + e.message);
  } finally {
    btn.classList.remove("active");
    btn.disabled = false;
  }
}

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
