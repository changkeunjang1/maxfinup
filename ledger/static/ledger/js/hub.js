/* MAX AI 종합법인자산관리허브 — 브라우저 로컬 저장 + 규칙 기반 AI 진단 */
(function () {
  "use strict";

  if (!document.getElementById("hubTool")) return;

  var STORE_KEY = "maxfinup.hub.v1";
  var COLORS = JSON.parse(document.getElementById("hubColors").textContent);
  var LABELS = JSON.parse(document.getElementById("hubLabels").textContent);
  var LINKS = JSON.parse(document.getElementById("hubLinks").textContent);
  var LIQUID = ["cash", "deposit", "securities"];
  var CASHLIKE = ["cash", "deposit"];

  var SAMPLE = [
    { name: "본사 사옥", category: "real_estate", amount: 1800000000, acquired_on: "2014-05-20", memo: "성수동, 대출 6억" },
    { name: "법인 정기예금", category: "deposit", amount: 250000000, acquired_on: "2025-11-01", memo: "1년 만기" },
    { name: "운영자금 통장", category: "cash", amount: 90000000, acquired_on: null, memo: "" },
    { name: "국내 ETF", category: "securities", amount: 120000000, acquired_on: "2024-03-12", memo: "" },
    { name: "업무용 차량 2대", category: "vehicle", amount: 85000000, acquired_on: "2023-07-01", memo: "리스 아님" }
  ];

  // ---------- state ----------
  function load() {
    try {
      var raw = localStorage.getItem(STORE_KEY);
      if (raw) {
        var parsed = JSON.parse(raw);
        if (parsed && Array.isArray(parsed.assets)) return parsed;
      }
    } catch (e) { /* storage unavailable */ }
    return { assets: [], monthlyCost: "", revenue: "", seq: 1 };
  }
  function save() {
    try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch (e) { /* ignore */ }
  }
  var state = load();

  // ---------- helpers ----------
  function $(id) { return document.getElementById(id); }
  function num(v) { var n = Number(v); return isFinite(n) ? n : 0; }
  function fmtWon(v) { return new Intl.NumberFormat("ko-KR").format(Math.round(num(v))) + "원"; }
  function fmtShort(v) {
    v = num(v);
    if (v >= 1e8) return (v / 1e8).toFixed(v >= 1e10 ? 0 : 1).replace(/\.0$/, "") + "억원";
    if (v >= 1e4) return Math.round(v / 1e4).toLocaleString("ko-KR") + "만원";
    return fmtWon(v);
  }
  function pct(part, whole) { return whole > 0 ? part / whole * 100 : 0; }
  function esc(s) { var d = document.createElement("div"); d.textContent = s == null ? "" : String(s); return d.innerHTML; }
  function colorOf(cat) { return COLORS[cat] || "#4a3aa7"; }
  function labelOf(cat) { return LABELS[cat] || cat; }

  function summarize() {
    var totals = {}, total = 0;
    state.assets.forEach(function (a) {
      totals[a.category] = (totals[a.category] || 0) + num(a.amount);
      total += num(a.amount);
    });
    var keys = Object.keys(totals).sort(function (x, y) { return totals[y] - totals[x]; });
    var sumOf = function (cats) { return cats.reduce(function (s, c) { return s + (totals[c] || 0); }, 0); };
    var monthly = num(state.monthlyCost);
    var cashlike = sumOf(CASHLIKE);
    return {
      totals: totals, total: total, keys: keys,
      liquid: sumOf(LIQUID), cashlike: cashlike,
      monthly: monthly, revenue: num(state.revenue),
      runway: monthly > 0 ? cashlike / monthly : null
    };
  }

  // ---------- AI diagnosis engine (rule-based) ----------
  function diagnose(s) {
    var out = [];
    function add(level, title, body, link, linkLabel) {
      out.push({ level: level, title: title, body: body, link: link, linkLabel: linkLabel });
    }
    if (!state.assets.length) {
      add("info", "자산을 등록하면 진단이 시작됩니다",
        "부동산·예금·주식·보험 등 법인 명의 자산을 추가하거나 '샘플 불러오기'로 미리 체험해 보세요.");
      return out;
    }

    var top = s.keys[0], topShare = pct(s.totals[top], s.total);
    if (topShare >= 70) {
      add("danger", labelOf(top) + " 비중 " + topShare.toFixed(0) + "% — 자산 편중 심각",
        "단일 분류에 자산이 과도하게 몰려 있어 해당 시장 충격에 그대로 노출됩니다. 분산 계획을 우선 검토하세요.",
        top === "real_estate" ? LINKS.realestate : LINKS.risk, top === "real_estate" ? "채권·부동산 보기" : "리스크 관리 편 보기");
    } else if (topShare >= 50) {
      add("warn", labelOf(top) + " 비중 " + topShare.toFixed(0) + "% — 편중 주의",
        "자산의 절반 이상이 한 분류에 있습니다. 유동성·수익원 분산 여지를 점검해 보세요.",
        top === "real_estate" ? LINKS.realestate : LINKS.risk, "관련 가이드 보기");
    }

    if (s.keys.length < 3) {
      add("warn", "자산 분류가 " + s.keys.length + "개뿐입니다",
        "분류가 적으면 특정 리스크에 취약합니다. 예금·채권 등 안정 자산과 보장성 자산 구성을 고려해 보세요.",
        LINKS.realestate, "채권·부동산 보기");
    }

    if (s.runway === null) {
      add("info", "월 고정비를 입력하면 운영자금 진단이 켜집니다",
        "현금·예금으로 몇 개월을 버틸 수 있는지 계산해 위기 대응력을 평가합니다.");
    } else if (s.runway < 3) {
      add("danger", "운영자금 버팀 기간 " + s.runway.toFixed(1) + "개월 — 유동성 위험",
        "현금·예금이 월 고정비의 3개월 미만입니다. 매출 공백 시 자금 경색 위험이 큽니다. 비유동 자산 일부의 유동화나 여신 한도 확보를 검토하세요.",
        LINKS.risk, "리스크 관리 편 보기");
    } else if (s.runway < 6) {
      add("warn", "운영자금 버팀 기간 " + s.runway.toFixed(1) + "개월",
        "일반적 권장 수준(6개월)보다 짧습니다. 비상 운영자금 적립 목표를 세워 보세요.",
        LINKS.risk, "리스크 관리 편 보기");
    } else if (s.runway > 24) {
      add("info", "유휴 현금 " + s.runway.toFixed(0) + "개월분 — 운용 효율 점검",
        "운영에 필요한 수준을 크게 넘는 현금은 수익률이 낮고 미처분 이익 누적으로 이어질 수 있습니다. 이익환원·운용 방안을 검토하세요.",
        LINKS.profit, "이익환원과 절세 보기");
    } else {
      add("good", "운영자금 버팀 기간 " + s.runway.toFixed(1) + "개월 — 양호",
        "현금·예금이 6개월 이상의 고정비를 감당할 수 있는 안정적인 수준입니다.");
    }

    var secShare = pct(s.totals.securities || 0, s.total);
    if (secShare >= 40) {
      add("warn", "주식·펀드 비중 " + secShare.toFixed(0) + "% — 변동성 노출",
        "법인 자금의 투자 비중이 높으면 평가손익이 재무제표와 신용평가에 직접 반영됩니다. 손실 한도와 운용 원칙을 정해 두세요.",
        LINKS.risk, "리스크 관리 편 보기");
    }

    if (!s.totals.insurance) {
      add("warn", "보험 자산이 등록되어 있지 않습니다",
        "대표자 유고·배상책임 등에 대비한 보장성 자산이 없으면 사고 시 법인과 가족 모두 타격을 받습니다.",
        LINKS.insurance, "보험 리모델링 보기");
    }

    if (s.totals.real_estate && s.totals.vehicle) {
      add("info", "감가상각 자산 보유",
        "건물·차량·장비는 감가상각과 처분 시점에 따라 법인세 효과가 달라집니다. 내용연수와 처분 계획을 점검하세요.",
        LINKS.profit, "이익환원과 절세 보기");
    }

    var oldest = state.assets.filter(function (a) { return a.acquired_on; })
      .map(function (a) { return new Date(a.acquired_on).getFullYear(); })
      .sort()[0];
    if (s.total >= 3e9 || (oldest && new Date().getFullYear() - oldest >= 10)) {
      add("info", "가업승계·상속 설계 검토 시점",
        (s.total >= 3e9 ? "총자산이 " + fmtShort(s.total) + " 규모로, " : "10년 이상 보유 자산이 있어 ") +
        "주식가치 상승 전 사전 증여·가업승계 설계를 시작하면 세 부담을 크게 줄일 수 있습니다.",
        LINKS.succession, "가업승계 편 보기");
    }

    if (s.revenue > 0 && s.total > 0) {
      var turnover = s.revenue / s.total;
      if (turnover < 0.5) {
        add("info", "자산회전율 " + turnover.toFixed(2) + "회 — 자산 활용도 점검",
          "매출 대비 보유 자산이 큽니다. 영업에 쓰이지 않는 비업무용 자산이 있다면 세무상 불이익이 없는지 확인하세요.",
          LINKS.profit, "이익환원과 절세 보기");
      }
    }

    if (!out.some(function (i) { return i.level === "danger" || i.level === "warn"; })) {
      add("good", "주요 위험 신호가 없습니다", "현재 입력 기준으로 자산 구성이 균형 잡혀 있습니다. 분기마다 평가금액을 갱신해 주세요.");
    }
    var order = { danger: 0, warn: 1, info: 2, good: 3 };
    return out.sort(function (a, b) { return order[a.level] - order[b.level]; });
  }

  function scoreOf(insights) {
    if (!state.assets.length) return null;
    var penalty = { danger: 22, warn: 10, info: 2, good: 0 };
    var score = insights.reduce(function (s, i) { return s - penalty[i.level]; }, 100);
    return Math.max(0, Math.min(100, score));
  }

  // ---------- render ----------
  var chart = null;
  function renderChart(s) {
    var canvas = $("hubChart");
    var empty = !s.keys.length;
    $("chartEmpty").hidden = !empty;
    canvas.style.display = empty ? "none" : "block";

    var labels = s.keys.map(labelOf);
    var data = s.keys.map(function (k) { return s.totals[k]; });
    var colors = s.keys.map(colorOf);

    if (window.Chart) {
      if (chart) {
        chart.data.labels = labels;
        chart.data.datasets[0].data = data;
        chart.data.datasets[0].backgroundColor = colors;
        chart.update();
      } else {
        chart = new Chart(canvas.getContext("2d"), {
          type: "doughnut",
          data: { labels: labels, datasets: [{ data: data, backgroundColor: colors, borderWidth: 2, borderColor: "#fff" }] },
          options: {
            cutout: "62%",
            plugins: {
              legend: { display: false },
              tooltip: { callbacks: { label: function (ctx) {
                var sum = ctx.dataset.data.reduce(function (a, b) { return a + b; }, 0);
                return " " + ctx.label + ": " + fmtWon(ctx.parsed) + " (" + pct(ctx.parsed, sum).toFixed(1) + "%)";
              } } }
            }
          }
        });
      }
    }

    $("hubLegend").innerHTML = s.keys.map(function (k) {
      return '<li><span class="dot" style="background:' + colorOf(k) + '"></span>' +
        '<span class="name">' + esc(labelOf(k)) + '</span>' +
        '<span class="pct">' + pct(s.totals[k], s.total).toFixed(1) + '%</span>' +
        '<span class="amt">' + fmtShort(s.totals[k]) + '</span></li>';
    }).join("");
  }

  function renderStats(s, score) {
    $("statTotal").textContent = fmtWon(s.total);
    $("statLiquid").textContent = s.total > 0 ? pct(s.liquid, s.total).toFixed(1) + "%" : "-";
    $("statRunway").textContent = s.runway === null ? "고정비 입력 필요" : s.runway.toFixed(1) + "개월";
    var scoreEl = $("statScore"), bar = $("statScoreBar");
    scoreEl.classList.remove("good", "warn", "danger");
    if (score === null) {
      scoreEl.textContent = "-";
      bar.style.width = "0";
      return;
    }
    var tier = score >= 80 ? "good" : score >= 60 ? "warn" : "danger";
    scoreEl.textContent = score + "점";
    scoreEl.classList.add(tier);
    bar.className = tier;
    bar.style.width = score + "%";
  }

  function renderInsights(list) {
    var icons = { danger: "!", warn: "△", info: "i", good: "✓" };
    var issues = list.filter(function (i) { return i.level === "danger" || i.level === "warn"; }).length;
    $("hubAiCount").textContent = state.assets.length ? (issues ? "점검 필요 " + issues + "건" : "이상 없음") : "";
    $("hubInsights").innerHTML = list.map(function (i) {
      return '<li class="hub-insight ' + i.level + '">' +
        '<span class="hub-insight-icon" aria-hidden="true">' + icons[i.level] + '</span>' +
        '<div><strong>' + esc(i.title) + '</strong><p>' + esc(i.body) + '</p>' +
        (i.link ? '<a href="' + esc(i.link) + '">' + esc(i.linkLabel || "자세히 보기") + ' ↗</a>' : "") +
        '</div></li>';
    }).join("");
  }

  function renderTable() {
    var q = $("hubSearch").value.trim().toLowerCase();
    var rows = state.assets
      .filter(function (a) { return !q || a.name.toLowerCase().indexOf(q) !== -1; })
      .sort(function (a, b) { return num(b.amount) - num(a.amount); });
    $("tableEmpty").hidden = state.assets.length !== 0;
    $("hubTableBody").innerHTML = rows.map(function (a) {
      var c = colorOf(a.category);
      return "<tr><td>" + esc(a.name) + "</td>" +
        '<td><span class="asset-badge" style="background:' + c + '22;color:' + c + '">' + esc(labelOf(a.category)) + "</span></td>" +
        "<td>" + esc(a.acquired_on || "-") + "</td>" +
        '<td class="memo">' + (a.memo ? esc(a.memo) : "-") + "</td>" +
        '<td class="num">' + fmtWon(a.amount) + "</td>" +
        '<td class="actions">' +
        '<button type="button" class="asset-icon-btn" data-edit="' + a.id + '" aria-label="수정">✎</button>' +
        '<button type="button" class="asset-icon-btn danger" data-delete="' + a.id + '" aria-label="삭제">✕</button>' +
        "</td></tr>";
    }).join("");
  }

  function renderAll() {
    var s = summarize();
    var insights = diagnose(s);
    renderStats(s, scoreOf(insights));
    renderChart(s);
    renderInsights(insights);
    renderTable();
  }

  // ---------- modal ----------
  var modal = $("hubModal");
  function openModal(a) {
    $("hubModalTitle").textContent = a ? "자산 수정" : "자산 추가";
    $("f_id").value = a ? a.id : "";
    $("f_name").value = a ? a.name : "";
    $("f_category").value = a ? a.category : "real_estate";
    $("f_amount").value = a ? a.amount : "";
    $("f_acquired").value = a ? (a.acquired_on || "") : "";
    $("f_memo").value = a ? a.memo : "";
    modal.hidden = false;
    $("f_name").focus();
  }
  function closeModal() { modal.hidden = true; }

  modal.addEventListener("click", function (e) { if (e.target.hasAttribute("data-close")) closeModal(); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !modal.hidden) closeModal(); });

  $("hubForm").addEventListener("submit", function (e) {
    e.preventDefault();
    var id = $("f_id").value;
    var rec = {
      id: id ? Number(id) : state.seq++,
      name: $("f_name").value.trim(),
      category: $("f_category").value,
      amount: Math.max(0, Math.round(num($("f_amount").value))),
      acquired_on: $("f_acquired").value || null,
      memo: $("f_memo").value.trim()
    };
    if (id) {
      state.assets = state.assets.map(function (a) { return String(a.id) === id ? rec : a; });
    } else {
      state.assets.push(rec);
    }
    save();
    closeModal();
    renderAll();
  });

  // ---------- actions ----------
  $("hubAddBtn").addEventListener("click", function () { openModal(null); });

  $("hubTableBody").addEventListener("click", function (e) {
    var btn = e.target.closest("button");
    if (!btn) return;
    var editId = btn.getAttribute("data-edit"), delId = btn.getAttribute("data-delete");
    if (editId) {
      var a = state.assets.find(function (x) { return String(x.id) === editId; });
      if (a) openModal(a);
    } else if (delId && confirm("이 자산을 삭제할까요?")) {
      state.assets = state.assets.filter(function (x) { return String(x.id) !== delId; });
      save();
      renderAll();
    }
  });

  $("hubSampleBtn").addEventListener("click", function () {
    if (state.assets.length && !confirm("현재 입력한 자산을 샘플 데이터로 바꿀까요?")) return;
    state.assets = SAMPLE.map(function (a, i) { return Object.assign({ id: i + 1 }, a); });
    state.seq = SAMPLE.length + 1;
    state.monthlyCost = 45000000;
    state.revenue = 3200000000;
    $("hubMonthlyCost").value = state.monthlyCost;
    $("hubRevenue").value = state.revenue;
    save();
    renderAll();
  });

  $("hubResetBtn").addEventListener("click", function () {
    if (!confirm("입력한 자산과 설정을 모두 삭제할까요?")) return;
    state = { assets: [], monthlyCost: "", revenue: "", seq: 1 };
    $("hubMonthlyCost").value = "";
    $("hubRevenue").value = "";
    save();
    renderAll();
  });

  $("hubExportBtn").addEventListener("click", function () {
    var cell = function (v) { return '"' + String(v == null ? "" : v).replace(/"/g, '""') + '"'; };
    var lines = [["자산명", "분류", "평가금액", "취득일", "메모"].map(cell).join(",")];
    state.assets.forEach(function (a) {
      lines.push([a.name, labelOf(a.category), a.amount, a.acquired_on || "", a.memo].map(cell).join(","));
    });
    var blob = new Blob(["﻿" + lines.join("\r\n")], { type: "text/csv;charset=utf-8" });
    var link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "maxfinup-assets.csv";
    link.click();
    setTimeout(function () { URL.revokeObjectURL(link.href); }, 1000);
  });

  $("hubMonthlyCost").value = state.monthlyCost;
  $("hubRevenue").value = state.revenue;
  $("hubMonthlyCost").addEventListener("input", function (e) { state.monthlyCost = e.target.value; save(); renderAll(); });
  $("hubRevenue").addEventListener("input", function (e) { state.revenue = e.target.value; save(); renderAll(); });
  $("hubSearch").addEventListener("input", renderTable);

  renderAll();
})();
