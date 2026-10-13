// =========================================================
// Main Application Logic & Interactivity
// Sandoq Building Fund | المهندس أبو عادل
// =========================================================

import { store } from "./db.js";

// Global State
let currentApartments = [];
let currentPayments = [];
let currentExpenses = [];
let flowChart = null;
let expChart = null;
let selectedResidentApt = null;

// Initialize on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  setupForms();
  setupReportsTabs();
  setupModals();
  setDefaultDates();

  // Subscribe to DB Store
  store.subscribe(handleDataUpdate);
  store.initRealtime();
});

// Toast notification helper
function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${type === 'success' ? '✅' : (type === 'danger' ? '❌' : '⚠️')}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Format Currency
function formatJOD(num) {
  return (parseFloat(num) || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " د.أ";
}

// Arabic Month Name
function getArabicMonthName(ymStr) {
  if (!ymStr) return "";
  const parts = ymStr.split("-");
  if (parts.length < 2) return ymStr;
  const year = parts[0];
  const month = parseInt(parts[1], 10);
  const monthNames = [
    "كانون الثاني (1)", "شباط (2)", "آذار (3)", "نيسان (4)",
    "أيار (5)", "حزيران (6)", "تموز (7)", "آب (8)",
    "أيلول (9)", "تشرين الأول (10)", "تشرين الثاني (11)", "كانون الأول (12)"
  ];
  return `${monthNames[month - 1] || month} ${year}`;
}

// Convert numbers to Arabic words for receipts (simple Jordan JOD format)
function numberToArabicWords(amount) {
  const intVal = Math.floor(amount);
  const wordsMap = {
    10: "عشرة دنانير أردنية",
    15: "خمسة عشر ديناراً أردنياً",
    20: "عشرون ديناراً أردنياً",
    25: "خمسة وعشرون ديناراً أردنياً",
    30: "ثلاثون ديناراً أردنياً",
    50: "خمسون ديناراً أردنياً",
    75: "خمسة وسبعون ديناراً أردنياً",
    100: "مائة دينار أردني"
  };
  return wordsMap[intVal] ? `فقط ${wordsMap[intVal]} لا غير` : `فقط ${intVal} ديناراً أردنياً لا غير`;
}

// WhatsApp URL generator
function generateWhatsAppUrl(phone, text) {
  let cleanPhone = String(phone || "").replace(/\D/g, "");
  if (cleanPhone.startsWith("07")) {
    cleanPhone = "962" + cleanPhone.substring(1);
  } else if (!cleanPhone.startsWith("962") && cleanPhone.length === 9) {
    cleanPhone = "962" + cleanPhone;
  }
  return `https://wa.me/${cleanPhone}?text=${encodeURIComponent(text)}`;
}

// Navigation Setup
function setupNavigation() {
  const navItems = document.querySelectorAll(".nav-item, .mobile-nav-item");
  navItems.forEach(item => {
    item.addEventListener("click", () => {
      const targetSec = item.dataset.section;
      if (!targetSec) return;

      // Update Active Nav
      document.querySelectorAll(".nav-item").forEach(n => n.classList.toggle("active", n.dataset.section === targetSec));
      document.querySelectorAll(".mobile-nav-item").forEach(n => n.classList.toggle("active", n.dataset.section === targetSec));

      // Show Section
      document.querySelectorAll(".app-section").forEach(s => s.classList.remove("active"));
      const activeEl = document.getElementById(`section-${targetSec}`);
      if (activeEl) activeEl.classList.add("active");

      // Update Title
      const titles = {
        dashboard: { title: "لوحة المؤشرات والقيادة", sub: "الملخص المالي والعمليات الأخيرة لصندوق خدمات العمارة" },
        payment: { title: "تسجيل مقبوضات (سند قبض)", sub: "استلام وتوثيق اشتراكات الشقق وإصدار إيصالات رسمية" },
        expense: { title: "تسجيل مصاريف (سند صرف)", sub: "توثيق نفقات الصيانة والفواتير ومشتريات مرافق العمارة" },
        apartments: { title: "دليل الشقق والسكان", sub: "قائمة الشقق، بيانات السكان، أرقام الهواتف، ومتابعة الالتزام" },
        reports: { title: "مركز الكشوفات والتقارير المالية", sub: "كشوفات تفصيلية للمقبوضات، المصروفات، كشف حساب ساكن محدد، وميزان المراجعة" }
      };
      if (titles[targetSec]) {
        document.getElementById("header-page-title").textContent = titles[targetSec].title;
        document.getElementById("header-page-sub").textContent = titles[targetSec].sub;
      }
    });
  });

  // Header quick buttons
  document.getElementById("btn-quick-receipt")?.addEventListener("click", () => {
    document.querySelector('.nav-item[data-section="payment"]')?.click();
  });
  document.getElementById("btn-goto-reports")?.addEventListener("click", () => {
    document.querySelector('.nav-item[data-section="reports"]')?.click();
  });
}

// Set default form dates
function setDefaultDates() {
  const today = new Date();
  const yyyy = today.getFullYear();
  const mm = String(today.getMonth() + 1).padStart(2, '0');
  const dd = String(today.getDate()).padStart(2, '0');
  const currentMonthStr = `${yyyy}-${mm}`;
  const currentDateStr = `${yyyy}-${mm}-${dd}`;

  const payMonth = document.getElementById("pay-month");
  if (payMonth) payMonth.value = currentMonthStr;

  const payDate = document.getElementById("pay-date");
  if (payDate) payDate.value = currentDateStr;

  const expDate = document.getElementById("exp-date");
  if (expDate) expDate.value = currentDateStr;

  const agingMonth = document.getElementById("aging-eval-month");
  if (agingMonth) agingMonth.value = currentMonthStr;
}

// Handle Data update from Firestore / Store
function handleDataUpdate({ apartments, payments, expenses }) {
  currentApartments = apartments;
  currentPayments = payments;
  currentExpenses = expenses;

  renderDashboard();
  renderApartments();
  populateDropdowns();
  renderReportsPayments();
  renderReportsExpenses();
  renderResidentStatement();
  renderTrialBalance();
  renderAgingReport();
  renderWhatsAppSummary();
}

// Populate Apartment & Month Dropdowns
function populateDropdowns() {
  // 1. Payment apartment select
  const payAptSelect = document.getElementById("pay-apt-select");
  if (payAptSelect) {
    const curVal = payAptSelect.value;
    payAptSelect.innerHTML = '<option value="">-- اختر الشقة من القائمة --</option>';
    currentApartments.forEach(apt => {
      payAptSelect.innerHTML += `<option value="${apt.apt_no}">شقة ${apt.apt_no} - ${apt.resident_name} (${apt.resident_type})</option>`;
    });
    if (curVal) payAptSelect.value = curVal;
  }

  // 2. Filter dropdowns in reports
  const filtPayApt = document.getElementById("filt-pay-apt");
  if (filtPayApt) {
    const curApt = filtPayApt.value;
    filtPayApt.innerHTML = '<option value="all">جميع الشقق</option>';
    currentApartments.forEach(apt => {
      filtPayApt.innerHTML += `<option value="${apt.apt_no}">شقة ${apt.apt_no} - ${apt.resident_name}</option>`;
    });
    if (curApt) filtPayApt.value = curApt;
  }

  // 3. Resident statement select
  const resSelect = document.getElementById("select-res-stmt");
  if (resSelect) {
    const curSel = resSelect.value;
    resSelect.innerHTML = "";
    currentApartments.forEach(apt => {
      resSelect.innerHTML += `<option value="${apt.apt_no}">شقة ${apt.apt_no} - ${apt.resident_name}</option>`;
    });
    if (curSel) resSelect.value = curSel;
    else if (currentApartments.length > 0) resSelect.value = currentApartments[0].apt_no;
  }

  // 4. Months for filters & WhatsApp report
  const monthsSet = new Set();
  const currentYm = new Date().toISOString().slice(0, 7);
  monthsSet.add(currentYm);
  currentPayments.forEach(p => { if (p.for_month) monthsSet.add(p.for_month); });
  currentExpenses.forEach(e => { if (e.expense_date) monthsSet.add(e.expense_date.slice(0, 7)); });
  const sortedMonths = Array.from(monthsSet).sort().reverse();

  const filtPayMonth = document.getElementById("filt-pay-month");
  if (filtPayMonth) {
    const curM = filtPayMonth.value;
    filtPayMonth.innerHTML = '<option value="all">جميع الأشهر</option>';
    sortedMonths.forEach(m => {
      filtPayMonth.innerHTML += `<option value="${m}">${getArabicMonthName(m)}</option>`;
    });
    if (curM) filtPayMonth.value = curM;
  }

  const filtExpMonth = document.getElementById("filt-exp-month");
  if (filtExpMonth) {
    const curM = filtExpMonth.value;
    filtExpMonth.innerHTML = '<option value="all">جميع الفترات</option>';
    sortedMonths.forEach(m => {
      filtExpMonth.innerHTML += `<option value="${m}">${getArabicMonthName(m)}</option>`;
    });
    if (curM) filtExpMonth.value = curM;
  }

  const waMonth = document.getElementById("select-wa-month");
  if (waMonth) {
    const curM = waMonth.value;
    waMonth.innerHTML = "";
    sortedMonths.forEach(m => {
      waMonth.innerHTML += `<option value="${m}">${getArabicMonthName(m)}</option>`;
    });
    if (curM) waMonth.value = curM;
  }

  // 5. Expense categories filter
  const filtExpCat = document.getElementById("filt-exp-cat");
  if (filtExpCat) {
    const catSet = new Set(currentExpenses.map(e => e.category).filter(Boolean));
    const curCat = filtExpCat.value;
    filtExpCat.innerHTML = '<option value="all">جميع البنود والتصنيفات</option>';
    catSet.forEach(c => {
      filtExpCat.innerHTML += `<option value="${c}">${c}</option>`;
    });
    if (curCat) filtExpCat.value = curCat;
  }
}

// =========================================================
// 1. DASHBOARD RENDERING
// =========================================================
function renderDashboard() {
  const totalIncome = currentPayments.reduce((acc, p) => acc + (parseFloat(p.amount) || 0), 0);
  const totalExpense = currentExpenses.reduce((acc, e) => acc + (parseFloat(e.amount) || 0), 0);
  const netBalance = totalIncome - totalExpense;

  // Unpaid dues for current month
  const currentYm = new Date().toISOString().slice(0, 7);
  let totalDues = 0;
  let unpaidAptsCount = 0;

  currentApartments.forEach(apt => {
    const isPaid = currentPayments.some(p => String(p.apt_no) === String(apt.apt_no) && p.for_month === currentYm);
    if (!isPaid) {
      totalDues += (parseFloat(apt.monthly_fee) || 25);
      unpaidAptsCount++;
    }
  });

  document.getElementById("kpi-balance").textContent = formatJOD(netBalance);
  document.getElementById("kpi-income").textContent = formatJOD(totalIncome);
  document.getElementById("kpi-income-sub").textContent = `${currentPayments.length} سندات قبض مسجلة`;
  document.getElementById("kpi-expense").textContent = formatJOD(totalExpense);
  document.getElementById("kpi-expense-sub").textContent = `${currentExpenses.length} فواتير وسندات صرف`;
  document.getElementById("kpi-dues").textContent = formatJOD(totalDues);
  document.getElementById("kpi-dues-sub").textContent = `${unpaidAptsCount} شقق متأخرة عن ${getArabicMonthName(currentYm)}`;

  // Recent Table
  const tbodyRecent = document.getElementById("tbody-recent");
  if (tbodyRecent) {
    const combinedOps = [
      ...currentPayments.map(p => ({ type: 'in', date: p.payment_date || p.created_at, label: `شقة ${p.apt_no} (${p.resident_name || ''}) - شهر ${p.for_month}`, amount: p.amount, method: p.payment_method || 'كاش', ref: p })),
      ...currentExpenses.map(e => ({ type: 'out', date: e.expense_date || e.created_at, label: `${e.category}: ${e.paid_to || ''} (${e.description || ''})`, amount: e.amount, method: e.invoice_ref || 'صرف', ref: e }))
    ];
    combinedOps.sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0));

    const top5 = combinedOps.slice(0, 6);
    if (top5.length === 0) {
      tbodyRecent.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px; color:#94a3b8;">لا توجد أي حركات مالية مسجلة حتى الآن.</td></tr>';
    } else {
      tbodyRecent.innerHTML = top5.map(op => `
        <tr>
          <td><span class="badge ${op.type === 'in' ? 'badge-success' : 'badge-danger'}">${op.type === 'in' ? '📥 قبض' : '📤 صرف'}</span></td>
          <td>${op.date ? op.date.slice(0, 10) : '--'}</td>
          <td><b>${op.label}</b></td>
          <td style="font-weight:800; color:${op.type === 'in' ? '#10b981' : '#ef4444'};">${formatJOD(op.amount)}</td>
          <td>${op.method}</td>
          <td>
            ${op.type === 'in' ? `<button class="btn btn-outline" style="padding:4px 8px; font-size:0.78rem;" onclick="window.previewReceipt('${op.ref.id || ''}')">🧾 معاينة</button>` : `<span style="color:#94a3b8; font-size:0.8rem;">سند صرف</span>`}
          </td>
        </tr>
      `).join("");
    }
  }

  // Render Charts
  renderDashboardCharts();
}

function renderDashboardCharts() {
  // 1. Flow Chart (Monthly In vs Out)
  const ctxFlow = document.getElementById("chart-flow")?.getContext("2d");
  if (ctxFlow) {
    const monthsMap = {};
    currentPayments.forEach(p => {
      const ym = p.for_month || (p.payment_date ? p.payment_date.slice(0, 7) : '');
      if (ym) {
        if (!monthsMap[ym]) monthsMap[ym] = { in: 0, out: 0 };
        monthsMap[ym].in += (parseFloat(p.amount) || 0);
      }
    });
    currentExpenses.forEach(e => {
      const ym = e.expense_date ? e.expense_date.slice(0, 7) : '';
      if (ym) {
        if (!monthsMap[ym]) monthsMap[ym] = { in: 0, out: 0 };
        monthsMap[ym].out += (parseFloat(e.amount) || 0);
      }
    });

    const labels = Object.keys(monthsMap).sort();
    const inData = labels.map(m => monthsMap[m].in);
    const outData = labels.map(m => monthsMap[m].out);

    if (flowChart) flowChart.destroy();
    flowChart = new Chart(ctxFlow, {
      type: 'bar',
      data: {
        labels: labels.map(l => l.slice(2)),
        datasets: [
          { label: 'المقبوضات (د.أ)', data: inData, backgroundColor: '#10b981', borderRadius: 6 },
          { label: 'المصروفات (د.أ)', data: outData, backgroundColor: '#ef4444', borderRadius: 6 }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'top', labels: { font: { family: 'Tajawal' } } }
        },
        scales: {
          x: { ticks: { font: { family: 'Tajawal' } } },
          y: { ticks: { font: { family: 'Tajawal' } } }
        }
      }
    });
  }

  // 2. Expenses by category Chart
  const ctxExp = document.getElementById("chart-expenses")?.getContext("2d");
  if (ctxExp) {
    const catMap = {};
    currentExpenses.forEach(e => {
      const cat = e.category || 'عام';
      catMap[cat] = (catMap[cat] || 0) + (parseFloat(e.amount) || 0);
    });

    const catLabels = Object.keys(catMap);
    const catData = Object.values(catMap);

    if (expChart) expChart.destroy();
    expChart = new Chart(ctxExp, {
      type: 'doughnut',
      data: {
        labels: catLabels.length > 0 ? catLabels : ['لا يوجد مصاريف'],
        datasets: [{
          data: catData.length > 0 ? catData : [1],
          backgroundColor: ['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#64748b']
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom', labels: { font: { family: 'Tajawal', size: 11 } } }
        }
      }
    });
  }
}

// =========================================================
// 2. APARTMENTS DIRECTORY
// =========================================================
function renderApartments() {
  const container = document.getElementById("apartments-container");
  if (!container) return;

  const currentYm = new Date().toISOString().slice(0, 7);

  container.innerHTML = currentApartments.map(apt => {
    const isPaid = currentPayments.some(p => String(p.apt_no) === String(apt.apt_no) && p.for_month === currentYm);
    const totalPaidApt = currentPayments
      .filter(p => String(p.apt_no) === String(apt.apt_no))
      .reduce((acc, p) => acc + (parseFloat(p.amount) || 0), 0);

    return `
      <div class="apt-card">
        <div>
          <div class="apt-header">
            <span class="apt-number">شقة ${apt.apt_no}</span>
            <span class="badge ${isPaid ? 'badge-success' : 'badge-danger'}">
              ${isPaid ? 'مسدد الشهر 🟢' : 'متأخر الشهر 🔴'}
            </span>
          </div>
          <div class="apt-body">
            <div class="apt-resident">${apt.resident_name}</div>
            <div class="apt-meta">
              <span>🏠 الصفة: <b>${apt.resident_type}</b></span>
              <span>📍 الموقع: ${apt.floor || '--'}</span>
              <span>💵 الاشتراك: <b>${apt.monthly_fee} د.أ/شهر</b></span>
              <span>📞 الهاتف: <a href="tel:${apt.phone}" style="color:#2563eb; text-decoration:none;">${apt.phone}</a></span>
              <span>💰 إجمالي المسدد تاريخياً: <b>${formatJOD(totalPaidApt)}</b></span>
            </div>
          </div>
        </div>
        <div class="apt-actions">
          <a href="${generateWhatsAppUrl(apt.phone, `مرحباً جارنا العزيز ${apt.resident_name} المحترم، تحية طيبة من لجنة العمارة.`)}" target="_blank" class="btn btn-whatsapp" style="flex:1; padding:6px 10px; font-size:0.8rem;">
            📱 واتساب
          </a>
          <button class="btn btn-outline" style="flex:1; padding:6px 10px; font-size:0.8rem;" onclick="window.viewResidentReport('${apt.apt_no}')">
            📊 كشف الحساب
          </button>
          <button class="btn btn-outline" style="padding:6px 10px; font-size:0.8rem;" onclick="window.editApartment('${apt.apt_no}')">
            ✏️
          </button>
        </div>
      </div>
    `;
  }).join("");
}

// =========================================================
// 3. REPORTS & STATEMENTS CENTER
// =========================================================
function setupReportsTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
      const targetPane = document.getElementById(btn.dataset.tab);
      if (targetPane) targetPane.classList.add("active");
    });
  });

  // Filter Event Listeners
  ["filt-pay-month", "filt-pay-method", "filt-pay-apt", "filt-pay-kw"].forEach(id => {
    document.getElementById(id)?.addEventListener("input", renderReportsPayments);
  });
  ["filt-exp-month", "filt-exp-cat", "filt-exp-kw"].forEach(id => {
    document.getElementById(id)?.addEventListener("input", renderReportsExpenses);
  });
  document.getElementById("select-res-stmt")?.addEventListener("change", renderResidentStatement);
  document.getElementById("aging-eval-month")?.addEventListener("input", renderAgingReport);
  document.getElementById("select-wa-month")?.addEventListener("change", renderWhatsAppSummary);

  // Export Buttons
  document.getElementById("btn-export-pays-excel")?.addEventListener("click", () => exportTableToExcel("table-rep-payments", "كشف_المقبوضات"));
  document.getElementById("btn-export-exps-excel")?.addEventListener("click", () => exportTableToExcel("table-rep-expenses", "كشف_المصروفات"));
  document.getElementById("btn-export-tb-excel")?.addEventListener("click", () => exportTableToExcel("tbody-rep-tb", "ميزان_المراجعة", true));
  document.getElementById("btn-export-aging-excel")?.addEventListener("click", () => exportTableToExcel("tbody-rep-aging", "كشف_الذمم_والمتأخرات", true));
  document.getElementById("btn-export-res-excel")?.addEventListener("click", exportResidentExcel);
  document.getElementById("btn-send-res-wa")?.addEventListener("click", sendResidentWhatsApp);
  document.getElementById("btn-copy-wa-report")?.addEventListener("click", copyWhatsAppReport);
}

// TAB 1: Render Payments Report
function renderReportsPayments() {
  const mFilt = document.getElementById("filt-pay-month")?.value || "all";
  const methFilt = document.getElementById("filt-pay-method")?.value || "all";
  const aptFilt = document.getElementById("filt-pay-apt")?.value || "all";
  const kwFilt = (document.getElementById("filt-pay-kw")?.value || "").trim().toLowerCase();

  const filtered = currentPayments.filter(p => {
    if (mFilt !== "all" && p.for_month !== mFilt) return false;
    if (methFilt !== "all" && p.payment_method !== methFilt) return false;
    if (aptFilt !== "all" && String(p.apt_no) !== String(aptFilt)) return false;
    if (kwFilt) {
      const match = (p.resident_name || '').toLowerCase().includes(kwFilt) ||
                    (p.receipt_no || '').toLowerCase().includes(kwFilt) ||
                    (p.notes || '').toLowerCase().includes(kwFilt);
      if (!match) return false;
    }
    return true;
  });

  const total = filtered.reduce((acc, p) => acc + (parseFloat(p.amount) || 0), 0);
  const avg = filtered.length > 0 ? (total / filtered.length) : 0;

  document.getElementById("disp-filt-pay-total").textContent = formatJOD(total);
  document.getElementById("disp-filt-pay-count").textContent = `${filtered.length} حركة استلام`;
  document.getElementById("disp-filt-pay-avg").textContent = formatJOD(avg);

  const tbody = document.getElementById("tbody-rep-payments");
  if (!tbody) return;

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding:20px; color:#94a3b8;">لا توجد مقبوضات مطابقة للفلاتر المحددة.</td></tr>';
    return;
  }

  tbody.innerHTML = filtered.map(p => `
    <tr>
      <td>${p.payment_date || (p.created_at ? p.created_at.slice(0, 10) : '--')}</td>
      <td><b>${p.receipt_no || '--'}</b></td>
      <td>شقة ${p.apt_no}</td>
      <td>${p.resident_name || '--'}</td>
      <td>${getArabicMonthName(p.for_month)}</td>
      <td style="font-weight:800; color:#10b981;">${formatJOD(p.amount)}</td>
      <td>${p.payment_method || 'كاش'}</td>
      <td>${p.notes || '--'}</td>
      <td>
        <button class="btn btn-outline" style="padding:4px 8px; font-size:0.75rem;" onclick="window.previewReceipt('${p.id || ''}')">
          🧾 سند
        </button>
      </td>
    </tr>
  `).join("");
}

// TAB 2: Render Expenses Report
function renderReportsExpenses() {
  const mFilt = document.getElementById("filt-exp-month")?.value || "all";
  const catFilt = document.getElementById("filt-exp-cat")?.value || "all";
  const kwFilt = (document.getElementById("filt-exp-kw")?.value || "").trim().toLowerCase();

  const filtered = currentExpenses.filter(e => {
    if (mFilt !== "all" && (!e.expense_date || !e.expense_date.startsWith(mFilt))) return false;
    if (catFilt !== "all" && e.category !== catFilt) return false;
    if (kwFilt) {
      const match = (e.paid_to || '').toLowerCase().includes(kwFilt) ||
                    (e.description || '').toLowerCase().includes(kwFilt) ||
                    (e.invoice_ref || '').toLowerCase().includes(kwFilt);
      if (!match) return false;
    }
    return true;
  });

  const total = filtered.reduce((acc, e) => acc + (parseFloat(e.amount) || 0), 0);

  // Top category
  const catSum = {};
  filtered.forEach(e => { catSum[e.category] = (catSum[e.category] || 0) + (parseFloat(e.amount) || 0); });
  let topCat = "لا يوجد";
  let maxVal = 0;
  for (const c in catSum) {
    if (catSum[c] > maxVal) { maxVal = catSum[c]; topCat = c; }
  }

  document.getElementById("disp-filt-exp-total").textContent = formatJOD(total);
  document.getElementById("disp-filt-exp-count").textContent = `${filtered.length} سند صرف مسجل`;
  document.getElementById("disp-filt-exp-top").textContent = topCat;

  const tbody = document.getElementById("tbody-rep-expenses");
  if (!tbody) return;

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:20px; color:#94a3b8;">لا توجد مصروفات مطابقة للفلاتر المحددة.</td></tr>';
    return;
  }

  tbody.innerHTML = filtered.map(e => `
    <tr>
      <td>${e.expense_date || '--'}</td>
      <td><b>${e.expense_no || '--'}</b></td>
      <td><span class="badge badge-warning">${e.category || '--'}</span></td>
      <td style="font-weight:800; color:#ef4444;">${formatJOD(e.amount)}</td>
      <td>${e.paid_to || '--'}</td>
      <td>${e.description || '--'}</td>
      <td>${e.invoice_ref || '--'}</td>
    </tr>
  `).join("");
}

// TAB 3: Render Resident Statement (مدفوعات من شخص معين)
function renderResidentStatement() {
  const selAptNo = document.getElementById("select-res-stmt")?.value;
  if (!selAptNo && currentApartments.length > 0) return;

  const apt = currentApartments.find(a => String(a.apt_no) === String(selAptNo));
  if (!apt) return;

  selectedResidentApt = apt;

  // Filter payments for this resident
  const resPays = currentPayments.filter(p => String(p.apt_no) === String(apt.apt_no));
  const totalPaid = resPays.reduce((acc, p) => acc + (parseFloat(p.amount) || 0), 0);
  const paidMonths = Array.from(new Set(resPays.map(p => p.for_month).filter(Boolean))).sort();

  // Determine all building months
  const allMonths = new Set();
  allMonths.add(new Date().toISOString().slice(0, 7));
  currentPayments.forEach(p => { if (p.for_month) allMonths.add(p.for_month); });
  const sortedMonths = Array.from(allMonths).sort().reverse();
  const unpaidMonths = sortedMonths.filter(m => !paidMonths.includes(m));
  const dues = unpaidMonths.length * (parseFloat(apt.monthly_fee) || 25);

  document.getElementById("res-disp-apt").textContent = `شقة ${apt.apt_no}`;
  document.getElementById("res-disp-name").textContent = `${apt.resident_name} (${apt.resident_type})`;
  document.getElementById("res-disp-total-paid").textContent = formatJOD(totalPaid);
  document.getElementById("res-disp-count").textContent = `${resPays.length} دفعات مسددة`;
  document.getElementById("res-disp-fee").textContent = `${apt.monthly_fee} د.أ/شهر`;
  document.getElementById("res-disp-floor").textContent = apt.floor || '--';
  document.getElementById("res-disp-dues").textContent = formatJOD(dues);
  document.getElementById("res-disp-unpaid-count").textContent = `${unpaidMonths.length} أشهر متأخرة`;

  const cardDues = document.getElementById("card-res-dues");
  if (cardDues) {
    cardDues.className = `kpi-card ${dues > 0 ? 'danger' : 'success'}`;
  }

  // Months breakdown badges
  document.getElementById("res-disp-paid-months").innerHTML = paidMonths.length > 0
    ? paidMonths.map(m => `<span class="badge badge-success" style="margin:2px;">${m}</span>`).join(" ")
    : '<span style="color:#64748b;">لا توجد أشهر مسددة مسجلة بعد.</span>';

  document.getElementById("res-disp-unpaid-months").innerHTML = unpaidMonths.length > 0
    ? unpaidMonths.map(m => `<span class="badge badge-danger" style="margin:2px;">${m}</span>`).join(" ")
    : '<span style="color:#10b981; font-weight:700;">🎉 كافة الأشهر مسددة بالكامل حتى تاريخه!</span>';

  // Ledger Table
  const tbody = document.getElementById("tbody-res-ledger");
  if (!tbody) return;

  if (resPays.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:20px; color:#94a3b8;">لا توجد أي سندات مقبوضات مسجلة لشقة (${apt.apt_no}) حتى الآن.</td></tr>`;
    return;
  }

  tbody.innerHTML = resPays.map(p => `
    <tr>
      <td>${p.payment_date || (p.created_at ? p.created_at.slice(0, 10) : '--')}</td>
      <td><b>${p.receipt_no || '--'}</b></td>
      <td>${getArabicMonthName(p.for_month)}</td>
      <td style="font-weight:800; color:#10b981;">${formatJOD(p.amount)}</td>
      <td>${p.payment_method || 'كاش'}</td>
      <td>${p.notes || '--'}</td>
      <td>
        <button class="btn btn-outline" style="padding:4px 8px; font-size:0.75rem;" onclick="window.previewReceipt('${p.id || ''}')">
          🖨️ طباعة السند
        </button>
      </td>
    </tr>
  `).join("");
}

// Send Resident WhatsApp Statement
function sendResidentWhatsApp() {
  if (!selectedResidentApt) return;
  const apt = selectedResidentApt;
  const resPays = currentPayments.filter(p => String(p.apt_no) === String(apt.apt_no));
  const totalPaid = resPays.reduce((acc, p) => acc + (parseFloat(p.amount) || 0), 0);
  const paidMonths = Array.from(new Set(resPays.map(p => p.for_month).filter(Boolean))).sort();

  const allMonths = new Set();
  allMonths.add(new Date().toISOString().slice(0, 7));
  currentPayments.forEach(p => { if (p.for_month) allMonths.add(p.for_month); });
  const sortedMonths = Array.from(allMonths).sort().reverse();
  const unpaidMonths = sortedMonths.filter(m => !paidMonths.includes(m));
  const dues = unpaidMonths.length * (parseFloat(apt.monthly_fee) || 25);

  let msg = `مرحباً جارنا العزيز ${apt.resident_name} المحترم، تحية طيبة من لجنة العمارة (إشراف المهندس أبو عادل). 🌸\n\n`;
  msg += `📊 *كشف حساب اشتراك خدمات العمارة لشقة رقم (${apt.apt_no}):*\n`;
  msg += `▪️ إجمالي المبالغ المسددة المستلمة: ${totalPaid.toFixed(2)} دينار (${resPays.length} سندات)\n`;
  msg += `▪️ الأشهر المسددة: ${paidMonths.join(" ، ") || "لا يوجد"}\n`;
  if (unpaidMonths.length > 0) {
    msg += `▪️ الأشهر المتبقية للاشتراك: ${unpaidMonths.join(" ، ")} بقيمة إجمالية (${dues} دينار)\n`;
  } else {
    msg += `▪️ الرصيد: مسدد بالكامل حتى تاريخه بارك الله بكم.\n`;
  }
  msg += `\nشاكرين ومقدرين حسن تعاونكم الدائم وحرصكم على راحة وخدمات العمارة.`;

  window.open(generateWhatsAppUrl(apt.phone, msg), '_blank');
}

// Export Resident Statement to Excel
function exportResidentExcel() {
  if (!selectedResidentApt) return;
  const apt = selectedResidentApt;
  const resPays = currentPayments.filter(p => String(p.apt_no) === String(apt.apt_no));
  
  const data = resPays.map(p => ({
    "تاريخ الاستلام": p.payment_date || p.created_at,
    "رقم السند": p.receipt_no,
    "الشقة": `شقة ${apt.apt_no}`,
    "الساكن": apt.resident_name,
    "عن شهر": p.for_month,
    "المبلغ (د.أ)": p.amount,
    "طريقة الدفع": p.payment_method,
    "الملاحظات": p.notes || ""
  }));

  const ws = XLSX.utils.json_to_sheet(data);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "كشف_الحساب");
  XLSX.writeFile(wb, `كشف_حساب_شقة_${apt.apt_no}_${apt.resident_name}.xlsx`);
}

// TAB 4: Render Trial Balance (ميزان المراجعة والتدفق المالي)
function renderTrialBalance() {
  const monthsSet = new Set();
  monthsSet.add(new Date().toISOString().slice(0, 7));
  currentPayments.forEach(p => { if (p.for_month) monthsSet.add(p.for_month); });
  currentExpenses.forEach(e => { if (e.expense_date) monthsSet.add(e.expense_date.slice(0, 7)); });

  const sortedMonths = Array.from(monthsSet).sort().reverse();

  let cumIn = 0;
  let cumOut = 0;

  const rowsHtml = sortedMonths.map(ym => {
    const mIn = currentPayments
      .filter(p => p.for_month === ym)
      .reduce((acc, p) => acc + (parseFloat(p.amount) || 0), 0);
    const mOut = currentExpenses
      .filter(e => e.expense_date && e.expense_date.startsWith(ym))
      .reduce((acc, e) => acc + (parseFloat(e.amount) || 0), 0);
    const net = mIn - mOut;

    cumIn += mIn;
    cumOut += mOut;

    let badgeClass = "badge-info";
    let badgeText = "متعادل ⚪";
    if (net > 0) { badgeClass = "badge-success"; badgeText = "فائض 🟢"; }
    else if (net < 0) { badgeClass = "badge-danger"; badgeText = "عجز 🔴"; }

    return `
      <tr>
        <td><b>${getArabicMonthName(ym)}</b></td>
        <td style="color:#10b981; font-weight:700;">${formatJOD(mIn)}</td>
        <td style="color:#ef4444; font-weight:700;">${formatJOD(mOut)}</td>
        <td style="font-weight:800; color:${net >= 0 ? '#10b981' : '#ef4444'};">${formatJOD(net)}</td>
        <td><span class="badge ${badgeClass}">${badgeText}</span></td>
      </tr>
    `;
  }).join("");

  document.getElementById("tb-tot-in").textContent = formatJOD(cumIn);
  document.getElementById("tb-tot-out").textContent = formatJOD(cumOut);
  document.getElementById("tb-tot-net").textContent = formatJOD(cumIn - cumOut);

  const tbody = document.getElementById("tbody-rep-tb");
  if (tbody) tbody.innerHTML = rowsHtml;
}

// TAB 5: Render Aging Report (كشف الذمم والمتأخرات)
function renderAgingReport() {
  const evalMonth = document.getElementById("aging-eval-month")?.value || new Date().toISOString().slice(0, 7);

  const monthsSet = new Set();
  monthsSet.add(new Date().toISOString().slice(0, 7));
  currentPayments.forEach(p => { if (p.for_month) monthsSet.add(p.for_month); });
  const allMonths = Array.from(monthsSet).sort();

  // Evaluate for each apartment
  let totalDues = 0;
  let unpaidCount = 0;

  const rows = currentApartments.map(apt => {
    const aptPays = currentPayments.filter(p => String(p.apt_no) === String(apt.apt_no));
    const paidMonths = aptPays.map(p => p.for_month);
    const isCurrentMonthPaid = paidMonths.includes(evalMonth);

    // Unpaid up to eval month
    const unpaidList = allMonths.filter(m => m <= evalMonth && !paidMonths.includes(m));
    const dueAmt = unpaidList.length * (parseFloat(apt.monthly_fee) || 25);

    if (unpaidList.length > 0) {
      totalDues += dueAmt;
      unpaidCount++;
    }

    const waMsg = `مرحباً جارنا العزيز ${apt.resident_name} المحترم، تحية طيبة من لجنة العمارة (إشراف المهندس أبو عادل). 🌸\nنود تذكيركم بلطف بوجود ذمة اشتراك خدمات عمارة مترتبة لشقة رقم (${apt.apt_no}) بقيمة (${dueAmt} دينار) عن الأشهر (${unpaidList.join(" ، ")}).\nشاكرين ومقدرين حسن تعاونكم الدائم.`;

    return `
      <tr>
        <td><b>شقة ${apt.apt_no}</b></td>
        <td>${apt.resident_name} (${apt.resident_type})</td>
        <td><a href="tel:${apt.phone}" style="color:#2563eb; text-decoration:none;">${apt.phone}</a></td>
        <td>${apt.monthly_fee} د.أ</td>
        <td><span class="badge ${isCurrentMonthPaid ? 'badge-success' : 'badge-danger'}">${isCurrentMonthPaid ? 'مسدد 🟢' : 'غير مسدد 🔴'}</span></td>
        <td>${unpaidList.length > 0 ? `<b style="color:#ef4444;">${unpaidList.length} أشهر</b> (${unpaidList.join("، ")})` : '<span style="color:#10b981;">مسدد بالكامل</span>'}</td>
        <td style="font-weight:800; color:${dueAmt > 0 ? '#ef4444' : '#10b981'};">${formatJOD(dueAmt)}</td>
        <td>
          ${dueAmt > 0 ? `
            <a href="${generateWhatsAppUrl(apt.phone, waMsg)}" target="_blank" class="btn btn-whatsapp" style="padding:4px 10px; font-size:0.75rem;">
              📱 مطالبة عبر واتساب
            </a>
          ` : `<span style="color:#10b981; font-size:0.8rem;">لا توجد متأخرات 🌸</span>`}
        </td>
      </tr>
    `;
  }).join("");

  document.getElementById("aging-tot-dues").textContent = formatJOD(totalDues);
  document.getElementById("aging-unpaid-count").textContent = `${unpaidCount} شقق`;
  document.getElementById("aging-apts-ratio").textContent = `من أصل ${currentApartments.length} شقة`;
  document.getElementById("aging-paid-count").textContent = `${currentApartments.length - unpaidCount} شقق`;

  const tbody = document.getElementById("tbody-rep-aging");
  if (tbody) tbody.innerHTML = rows;
}

// TAB 6: Render WhatsApp Group Summary
function renderWhatsAppSummary() {
  const ym = document.getElementById("select-wa-month")?.value || new Date().toISOString().slice(0, 7);

  const mIn = currentPayments.filter(p => p.for_month === ym).reduce((acc, p) => acc + (parseFloat(p.amount) || 0), 0);
  const mExps = currentExpenses.filter(e => e.expense_date && e.expense_date.startsWith(ym));
  const mOut = mExps.reduce((acc, e) => acc + (parseFloat(e.amount) || 0), 0);
  const net = mIn - mOut;

  let expDetails = "";
  if (mExps.length > 0) {
    mExps.forEach(e => {
      expDetails += `▫️ ${e.category}: ${e.amount} د.أ (${e.description || e.paid_to || ''})\n`;
    });
  } else {
    expDetails = "▫️ لا توجد مصروفات مسجلة خلال هذا الشهر.\n";
  }

  const reportText = 
`🏛️ *التقرير المالي الشهري لصندوق العمارة السكنية*
🗓️ *عن شهر:* ${getArabicMonthName(ym)}
إشراف: المهندس أبو عادل
---------------------------------
💰 *الملخص المالي:* 
▪️ إجمالي التحصيلات والمقبوضات: ${mIn.toFixed(2)} دينار
▪️ إجمالي المصروفات والصيانة: ${mOut.toFixed(2)} دينار
---------------------------------
🔹 *الرصيد الصافي المتبقي بالصندوق:* ${net.toFixed(2)} دينار

📋 *تفاصيل البنود والمصروفات:* 
${expDetails}
أتقدم بجزيل الشكر لكافة الجيران الأفاضل الملتزمين بالسداد في الموعد المحدد لضمان جودة الخدمات واستمرار الصيانة.
مع خالص التحية، لجنة العمارة - المهندس أبو عادل 🌸`;

  const txtArea = document.getElementById("txt-wa-report-body");
  if (txtArea) txtArea.value = reportText;
}

function copyWhatsAppReport() {
  const txtArea = document.getElementById("txt-wa-report-body");
  if (!txtArea) return;
  txtArea.select();
  navigator.clipboard.writeText(txtArea.value).then(() => {
    showToast("تم نسخ التقرير المالي بنجاح! يمكنك لصقه الآن في واتساب.");
  });
}

// Generic Table to Excel Exporter via SheetJS
function exportTableToExcel(tableId, filename, isTbodyOnly = false) {
  let tableEl = document.getElementById(tableId);
  if (!tableEl) return;
  if (isTbodyOnly) {
    tableEl = tableEl.closest("table");
  }
  const wb = XLSX.utils.table_to_book(tableEl, { sheet: "التقرير" });
  XLSX.writeFile(wb, `${filename}.xlsx`);
}

// =========================================================
// 4. FORMS & MODALS LOGIC
// =========================================================
function setupForms() {
  // 1. Payment Form Submit
  const payForm = document.getElementById("form-payment");
  payForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const aptNo = document.getElementById("pay-apt-select").value;
    const forMonth = document.getElementById("pay-month").value;
    const amount = parseFloat(document.getElementById("pay-amount").value);
    const method = document.getElementById("pay-method").value;
    const payDate = document.getElementById("pay-date").value;
    const notes = document.getElementById("pay-notes").value;

    const apt = currentApartments.find(a => String(a.apt_no) === String(aptNo));
    if (!apt) {
      showToast("يرجى اختيار الشقة", "danger");
      return;
    }

    // Check duplicate
    const exists = currentPayments.some(p => String(p.apt_no) === String(aptNo) && p.for_month === forMonth);
    if (exists) {
      if (!confirm(`⚠️ تم تسجيل دفعة سابقة لشقة (${aptNo}) عن شهر (${forMonth}). هل تود المتابعة وحفظ دفعة إضافية؟`)) {
        return;
      }
    }

    try {
      const newPay = await store.addPayment({
        apt_no: aptNo,
        resident_name: apt.resident_name,
        for_month: forMonth,
        amount: amount,
        payment_method: method,
        payment_date: payDate,
        notes: notes
      });

      showToast(`تم حفظ سند القبض رقم ${newPay.receipt_no} بنجاح! 🟢`);
      payForm.reset();
      setDefaultDates();

      // Show receipt modal immediately for convenience
      window.previewReceipt(newPay.id);
    } catch (err) {
      showToast("حدث خطأ أثناء الحفظ: " + err.message, "danger");
    }
  });

  // 2. Expense Form Submit
  const expForm = document.getElementById("form-expense");
  expForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const category = document.getElementById("exp-category").value;
    const amount = parseFloat(document.getElementById("exp-amount").value);
    const expDate = document.getElementById("exp-date").value;
    const paidTo = document.getElementById("exp-paid-to").value;
    const invoice = document.getElementById("exp-invoice").value;
    const desc = document.getElementById("exp-desc").value;

    try {
      const newExp = await store.addExpense({
        category: category,
        amount: amount,
        expense_date: expDate,
        paidTo: paidTo,
        invoice_ref: invoice,
        description: desc
      });

      showToast(`تم تسجيل سند الصرف رقم ${newExp.expense_no} بنجاح! 💸`);
      expForm.reset();
      setDefaultDates();
      document.querySelector('.nav-item[data-section="dashboard"]')?.click();
    } catch (err) {
      showToast("حدث خطأ أثناء حفظ المصروف: " + err.message, "danger");
    }
  });

  // 3. Apartment Form Submit
  const aptForm = document.getElementById("form-apartment");
  aptForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const aptNo = document.getElementById("modal-apt-no").value;
    const name = document.getElementById("modal-apt-name").value;
    const phone = document.getElementById("modal-apt-phone").value;
    const type = document.getElementById("modal-apt-type").value;
    const fee = parseFloat(document.getElementById("modal-apt-fee").value) || 25;
    const floor = document.getElementById("modal-apt-floor").value;

    try {
      await store.saveApartment({
        apt_no: aptNo,
        resident_name: name,
        phone: phone,
        resident_type: type,
        monthly_fee: fee,
        floor: floor
      });

      showToast(`تم حفظ بيانات شقة (${aptNo}) بنجاح!`);
      closeModal("modal-apartment");
    } catch (err) {
      showToast("خطأ أثناء الحفظ: " + err.message, "danger");
    }
  });

  // 4. Reset Database Execution
  document.getElementById("btn-execute-reset")?.addEventListener("click", async () => {
    const chk = document.getElementById("chk-confirm-reset");
    if (!chk || !chk.checked) {
      showToast("يرجى تأكيد الرغبة في التصفير بوضع علامة صح.", "warning");
      return;
    }
    const scope = document.querySelector('input[name="reset-scope"]:checked')?.value;
    const clearApts = (scope === "all");

    try {
      await store.clearAllData(clearApts);
      showToast("تم تصفير وتفريغ قاعدة البيانات بنجاح.");
      closeModal("modal-reset");
    } catch (err) {
      showToast("حدث خطأ أثناء التصفير: " + err.message, "danger");
    }
  });
}

function setupModals() {
  document.getElementById("btn-add-apartment")?.addEventListener("click", () => {
    document.getElementById("form-apartment").reset();
    document.getElementById("modal-apt-title").textContent = "إضافة شقة جديدة";
    document.getElementById("modal-apt-no").removeAttribute("readonly");
    openModal("modal-apartment");
  });

  document.getElementById("btn-trigger-reset")?.addEventListener("click", () => {
    openModal("modal-reset");
  });
}

function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("active");
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("active");
}

// Global modal helpers attached to window
window.previewReceipt = function(id) {
  const pay = currentPayments.find(p => p.id === id);
  if (!pay) return;

  document.getElementById("rcpt-badge-no").textContent = `سند قبض رقم: ${pay.receipt_no || '--'}`;
  document.getElementById("rcpt-date").textContent = pay.payment_date || pay.created_at?.slice(0, 10) || '--';
  document.getElementById("rcpt-resident").textContent = pay.resident_name || '--';
  document.getElementById("rcpt-apt").textContent = `شقة ${pay.apt_no}`;
  document.getElementById("rcpt-month").textContent = getArabicMonthName(pay.for_month);
  document.getElementById("rcpt-method").textContent = pay.payment_method || 'كاش';
  document.getElementById("rcpt-notes").textContent = pay.notes || 'اشتراك خدمات وصيانة المبنى';
  document.getElementById("rcpt-amount").textContent = formatJOD(pay.amount);
  document.getElementById("rcpt-amount-words").textContent = numberToArabicWords(pay.amount);

  // WhatsApp Button
  const apt = currentApartments.find(a => String(a.apt_no) === String(pay.apt_no));
  const phone = apt ? apt.phone : '';
  const btnWa = document.getElementById("btn-modal-rcpt-wa");
  if (btnWa) {
    const waText = `مرحباً جارنا العزيز ${pay.resident_name} المحترم، تحية طيبة من لجنة العمارة (المهندس أبو عادل). 🌸\nنود إعلامكم باستلام مبلغ (${pay.amount} دينار) بدل اشتراك خدمات وصيانة عن شهر (${pay.for_month}) بموجب سند قبض رقم (${pay.receipt_no}). شاكرين ومقدرين تعاونكم الدائم.`;
    btnWa.onclick = () => window.open(generateWhatsAppUrl(phone, waText), '_blank');
  }

  openModal("modal-receipt");
};

window.viewResidentReport = function(aptNo) {
  document.querySelector('.nav-item[data-section="reports"]')?.click();
  document.querySelector('.tab-btn[data-tab="tab-rep-resident"]')?.click();
  const select = document.getElementById("select-res-stmt");
  if (select) {
    select.value = aptNo;
    renderResidentStatement();
  }
};

window.editApartment = function(aptNo) {
  const apt = currentApartments.find(a => String(a.apt_no) === String(aptNo));
  if (!apt) return;

  document.getElementById("modal-apt-title").textContent = `تعديل بيانات شقة ${apt.apt_no}`;
  document.getElementById("modal-apt-no").value = apt.apt_no;
  document.getElementById("modal-apt-no").setAttribute("readonly", true);
  document.getElementById("modal-apt-name").value = apt.resident_name || "";
  document.getElementById("modal-apt-phone").value = apt.phone || "";
  document.getElementById("modal-apt-type").value = apt.resident_type || "مالك";
  document.getElementById("modal-apt-fee").value = apt.monthly_fee || 25;
  document.getElementById("modal-apt-floor").value = apt.floor || "";

  openModal("modal-apartment");
};
