// =========================================================
// Multi-Tenant Database Engine (Cloud Firestore Multi-Building Support)
// Sandoq Building Fund Platform | نظام صناديق العمارات السكنية
// =========================================================

import { 
  db, 
  collection, 
  doc, 
  getDoc, 
  getDocs, 
  setDoc, 
  addDoc, 
  deleteDoc, 
  onSnapshot 
} from "./firebase-config.js";

export const DEFAULT_APARTMENTS_ABUADEL = [
  {"apt_no": "1", "resident_name": "أحمد خليل الرواشدة", "phone": "0795551101", "resident_type": "مالك", "monthly_fee": 25.0, "floor": "طابق تسوية"},
  {"apt_no": "2", "resident_name": "محمود إبراهيم الكردي", "phone": "0795551102", "resident_type": "مستأجر", "monthly_fee": 25.0, "floor": "طابق تسوية"},
  {"apt_no": "3", "resident_name": "المهندس أبو عادل", "phone": "0795551103", "resident_type": "مالك", "monthly_fee": 25.0, "floor": "طابق أرضي"},
  {"apt_no": "4", "resident_name": "خالد عمر النسور", "phone": "0795551104", "resident_type": "مستأجر", "monthly_fee": 25.0, "floor": "طابق أرضي"},
  {"apt_no": "5", "resident_name": "طارق زياد العبادي", "phone": "0795551105", "resident_type": "مالك", "monthly_fee": 25.0, "floor": "طابق أول"},
  {"apt_no": "6", "resident_name": "بلال سعيد الحنيطي", "phone": "0795551106", "resident_type": "مالك", "monthly_fee": 25.0, "floor": "طابق أول"},
  {"apt_no": "7", "resident_name": "يوسف عبد الله القضاة", "phone": "0795551107", "resident_type": "مستأجر", "monthly_fee": 25.0, "floor": "طابق ثاني"},
  {"apt_no": "8", "resident_name": "حمزة جمال حداد", "phone": "0795551108", "resident_type": "مالك", "monthly_fee": 25.0, "floor": "طابق ثاني"},
  {"apt_no": "9", "resident_name": "عمر حسن الزعبي", "phone": "0795551109", "resident_type": "مالك", "monthly_fee": 25.0, "floor": "طابق ثالث"},
  {"apt_no": "10", "resident_name": "سامر ناصر المجالي", "phone": "0795551110", "resident_type": "مستأجر", "monthly_fee": 25.0, "floor": "طابق ثالث (روف)"}
];

export const DEFAULT_BUILDING_ABUADEL = {
  id: "abuadel",
  name: "صندوق عمارة المهندس أبو عادل",
  username: "abuadel",
  password: "abuadel2026",
  manager_name: "المهندس أبو عادل",
  phone: "0795551103",
  default_monthly_fee: 25.0,
  address: "عمان - الأردن"
};

class MultiTenantStore {
  constructor() {
    this.currentBuilding = null;
    this.apartments = [];
    this.payments = [];
    this.expenses = [];
    this.listeners = [];
    this.unsubApts = null;
    this.unsubPays = null;
    this.unsubExps = null;
  }

  subscribe(listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  notify() {
    this.listeners.forEach(cb => cb({
      building: this.currentBuilding,
      apartments: this.apartments,
      payments: this.payments,
      expenses: this.expenses
    }));
  }

  // Load active session from localStorage
  getActiveSession() {
    try {
      const saved = localStorage.getItem("sandoq_active_building");
      return saved ? JSON.parse(saved) : null;
    } catch (e) {
      return null;
    }
  }

  // Set active session
  setActiveSession(buildingData) {
    this.currentBuilding = buildingData;
    localStorage.setItem("sandoq_active_building", JSON.stringify(buildingData));
  }

  // Logout
  logout() {
    if (this.unsubApts) this.unsubApts();
    if (this.unsubPays) this.unsubPays();
    if (this.unsubExps) this.unsubExps();
    this.currentBuilding = null;
    this.apartments = [];
    this.payments = [];
    this.expenses = [];
    localStorage.removeItem("sandoq_active_building");
    this.notify();
  }

  // Login checking
  async login(username, password) {
    const cleanUser = String(username || "").trim().toLowerCase();
    const cleanPass = String(password || "").trim();

    // 1. Check default building Abu Adel
    if (cleanUser === "abuadel" && cleanPass === "abuadel2026") {
      this.setActiveSession(DEFAULT_BUILDING_ABUADEL);
      await this.initRealtime(DEFAULT_BUILDING_ABUADEL.id);
      return { success: true, building: DEFAULT_BUILDING_ABUADEL };
    }

    // 2. Check Firestore buildings
    if (db) {
      try {
        const bDoc = await getDoc(doc(db, "buildings", cleanUser));
        if (bDoc.exists()) {
          const bData = bDoc.data();
          if (bData.password === cleanPass) {
            this.setActiveSession(bData);
            await this.initRealtime(bData.id);
            return { success: true, building: bData };
          } else {
            return { success: false, error: "كلمة المرور غير صحيحة" };
          }
        }
      } catch (err) {
        console.error("Login fetch error:", err);
      }
    }

    // 3. Check local storage custom buildings
    try {
      const localBuildings = JSON.parse(localStorage.getItem("sandoq_all_buildings") || "{}");
      if (localBuildings[cleanUser]) {
        const bData = localBuildings[cleanUser];
        if (bData.password === cleanPass) {
          this.setActiveSession(bData);
          await this.initRealtime(bData.id);
          return { success: true, building: bData };
        }
      }
    } catch (e) {}

    return { success: false, error: "اسم المستخدم أو كلمة المرور غير صحيحة" };
  }

  // Register New Building
  async registerBuilding({ name, username, password, manager_name, phone, default_monthly_fee, apt_count }) {
    const cleanUser = String(username || "").trim().toLowerCase().replace(/[^a-z0-9_-]/g, "");
    if (!cleanUser) throw new Error("يرجى إدخال اسم مستخدم صالح باللغة الإنجليزية أو الأرقام");
    if (!password) throw new Error("يرجى إدخال كلمة مرور");

    const buildingData = {
      id: cleanUser,
      name: name || `صندوق عمارة ${cleanUser}`,
      username: cleanUser,
      password: password,
      manager_name: manager_name || "مشرف الصندوق",
      phone: phone || "",
      default_monthly_fee: parseFloat(default_monthly_fee) || 25.0,
      created_at: new Date().toISOString()
    };

    // Save Building
    if (db) {
      await setDoc(doc(db, "buildings", cleanUser), buildingData);
    }

    // Save in local cache
    try {
      const allB = JSON.parse(localStorage.getItem("sandoq_all_buildings") || "{}");
      allB[cleanUser] = buildingData;
      localStorage.setItem("sandoq_all_buildings", JSON.stringify(allB));
    } catch (e) {}

    // Generate starter apartments for this new building
    const count = parseInt(apt_count, 10) || 8;
    const starterApts = [];
    for (let i = 1; i <= count; i++) {
      const floorNames = ["طابق أرضي", "طابق أول", "طابق ثاني", "طابق ثالث", "طابق رابع"];
      const floor = floorNames[Math.floor((i - 1) / 4)] || "طابق سكني";
      starterApts.push({
        apt_no: String(i),
        resident_name: `ساكن شقة ${i}`,
        phone: "",
        resident_type: (i % 2 === 0) ? "مستأجر" : "مالك",
        monthly_fee: buildingData.default_monthly_fee,
        floor: floor
      });
    }

    // Seed starter apartments into Firestore
    if (db) {
      for (const apt of starterApts) {
        await setDoc(doc(db, "buildings", cleanUser, "apartments", String(apt.apt_no)), apt);
      }
    } else {
      localStorage.setItem(`sandoq_${cleanUser}_apartments`, JSON.stringify(starterApts));
    }

    this.setActiveSession(buildingData);
    await this.initRealtime(cleanUser);
    return buildingData;
  }

  // Initialize Realtime Sync for specific building
  async initRealtime(buildingId) {
    if (!buildingId) return;

    // Unsubscribe previous listeners
    if (this.unsubApts) this.unsubApts();
    if (this.unsubPays) this.unsubPays();
    if (this.unsubExps) this.unsubExps();

    // 1. Initial Local Cache for this building
    try {
      const cApts = localStorage.getItem(`sandoq_${buildingId}_apartments`);
      const cPays = localStorage.getItem(`sandoq_${buildingId}_payments`);
      const cExps = localStorage.getItem(`sandoq_${buildingId}_expenses`);

      if (cApts) this.apartments = JSON.parse(cApts);
      else if (buildingId === "abuadel") this.apartments = [...DEFAULT_APARTMENTS_ABUADEL];
      else this.apartments = [];

      this.payments = cPays ? JSON.parse(cPays) : [];
      this.expenses = cExps ? JSON.parse(cExps) : [];
      this.notify();
    } catch (e) {}

    if (!db) {
      console.warn("Firestore not connected, using local store for building:", buildingId);
      return;
    }

    // Ensure building doc exists for abuadel
    if (buildingId === "abuadel") {
      try {
        await setDoc(doc(db, "buildings", "abuadel"), DEFAULT_BUILDING_ABUADEL, { merge: true });
      } catch (e) {}
    }

    // 2. Listen to this building's Apartments
    try {
      const aptsCol = collection(db, "buildings", buildingId, "apartments");
      this.unsubApts = onSnapshot(aptsCol, async (snapshot) => {
        if (snapshot.empty && buildingId === "abuadel") {
          console.log("Seeding Abu Adel apartments into subcollection...");
          for (const apt of DEFAULT_APARTMENTS_ABUADEL) {
            await setDoc(doc(db, "buildings", "abuadel", "apartments", String(apt.apt_no)), apt);
          }
        } else {
          this.apartments = snapshot.docs.map(d => ({ id: d.id, ...d.data() }));
          this.apartments.sort((a, b) => parseInt(a.apt_no || 0) - parseInt(b.apt_no || 0));
          localStorage.setItem(`sandoq_${buildingId}_apartments`, JSON.stringify(this.apartments));
          this.notify();
        }
      }, err => console.error("Apts listen error:", err));

      // 3. Listen to this building's Payments
      const paysCol = collection(db, "buildings", buildingId, "payments");
      this.unsubPays = onSnapshot(paysCol, (snapshot) => {
        this.payments = snapshot.docs.map(d => ({ id: d.id, ...d.data() }));
        this.payments.sort((a, b) => new Date(b.created_at || b.payment_date || 0) - new Date(a.created_at || a.payment_date || 0));
        localStorage.setItem(`sandoq_${buildingId}_payments`, JSON.stringify(this.payments));
        this.notify();
      }, err => console.error("Pays listen error:", err));

      // 4. Listen to this building's Expenses
      const expsCol = collection(db, "buildings", buildingId, "expenses");
      this.unsubExps = onSnapshot(expsCol, (snapshot) => {
        this.expenses = snapshot.docs.map(d => ({ id: d.id, ...d.data() }));
        this.expenses.sort((a, b) => new Date(b.created_at || b.expense_date || 0) - new Date(a.created_at || a.expense_date || 0));
        localStorage.setItem(`sandoq_${buildingId}_expenses`, JSON.stringify(this.expenses));
        this.notify();
      }, err => console.error("Exps listen error:", err));

    } catch (err) {
      console.error("Firestore setup error for building:", buildingId, err);
    }
  }

  // Apartment CRUD
  async saveApartment(aptData) {
    if (!this.currentBuilding) throw new Error("يرجى تسجيل الدخول أولاً");
    const bId = this.currentBuilding.id;
    const key = String(aptData.apt_no);

    if (db) {
      await setDoc(doc(db, "buildings", bId, "apartments", key), aptData, { merge: true });
    } else {
      const idx = this.apartments.findIndex(a => String(a.apt_no) === key);
      if (idx >= 0) this.apartments[idx] = aptData;
      else this.apartments.push(aptData);
      localStorage.setItem(`sandoq_${bId}_apartments`, JSON.stringify(this.apartments));
      this.notify();
    }
    return true;
  }

  async deleteApartment(aptNo) {
    if (!this.currentBuilding) return;
    const bId = this.currentBuilding.id;
    const key = String(aptNo);

    if (db) {
      await deleteDoc(doc(db, "buildings", bId, "apartments", key));
    } else {
      this.apartments = this.apartments.filter(a => String(a.apt_no) !== key);
      localStorage.setItem(`sandoq_${bId}_apartments`, JSON.stringify(this.apartments));
      this.notify();
    }
    return true;
  }

  // Payment CRUD
  async addPayment(paymentData) {
    if (!this.currentBuilding) throw new Error("يرجى تسجيل الدخول أولاً");
    const bId = this.currentBuilding.id;

    paymentData.created_at = new Date().toISOString();
    if (!paymentData.receipt_no) {
      const year = new Date().getFullYear();
      const num = this.payments.length + 1;
      paymentData.receipt_no = `REC-${year}-${String(num).padStart(3, '0')}`;
    }
    paymentData.amount = parseFloat(paymentData.amount) || 0;

    if (db) {
      const res = await addDoc(collection(db, "buildings", bId, "payments"), paymentData);
      paymentData.id = res.id;
    } else {
      paymentData.id = "pay_" + Date.now();
      this.payments.unshift(paymentData);
      localStorage.setItem(`sandoq_${bId}_payments`, JSON.stringify(this.payments));
      this.notify();
    }
    return paymentData;
  }

  async deletePayment(id) {
    if (!this.currentBuilding) return;
    const bId = this.currentBuilding.id;

    if (db) {
      await deleteDoc(doc(db, "buildings", bId, "payments", id));
    } else {
      this.payments = this.payments.filter(p => p.id !== id);
      localStorage.setItem(`sandoq_${bId}_payments`, JSON.stringify(this.payments));
      this.notify();
    }
    return true;
  }

  // Expense CRUD
  async addExpense(expenseData) {
    if (!this.currentBuilding) throw new Error("يرجى تسجيل الدخول أولاً");
    const bId = this.currentBuilding.id;

    expenseData.created_at = new Date().toISOString();
    if (!expenseData.expense_no) {
      const year = new Date().getFullYear();
      const num = this.expenses.length + 1;
      expenseData.expense_no = `EXP-${year}-${String(num).padStart(3, '0')}`;
    }
    expenseData.amount = parseFloat(expenseData.amount) || 0;

    if (db) {
      const res = await addDoc(collection(db, "buildings", bId, "expenses"), expenseData);
      expenseData.id = res.id;
    } else {
      expenseData.id = "exp_" + Date.now();
      this.expenses.unshift(expenseData);
      localStorage.setItem(`sandoq_${bId}_expenses`, JSON.stringify(this.expenses));
      this.notify();
    }
    return expenseData;
  }

  async deleteExpense(id) {
    if (!this.currentBuilding) return;
    const bId = this.currentBuilding.id;

    if (db) {
      await deleteDoc(doc(db, "buildings", bId, "expenses", id));
    } else {
      this.expenses = this.expenses.filter(e => e.id !== id);
      localStorage.setItem(`sandoq_${bId}_expenses`, JSON.stringify(this.expenses));
      this.notify();
    }
    return true;
  }

  // Clear / Reset Database for current building only
  async clearAllData(clearApartments = false) {
    if (!this.currentBuilding) return;
    const bId = this.currentBuilding.id;

    if (db) {
      const pSnap = await getDocs(collection(db, "buildings", bId, "payments"));
      for (const d of pSnap.docs) {
        await deleteDoc(doc(db, "buildings", bId, "payments", d.id));
      }
      const eSnap = await getDocs(collection(db, "buildings", bId, "expenses"));
      for (const d of eSnap.docs) {
        await deleteDoc(doc(db, "buildings", bId, "expenses", d.id));
      }
      if (clearApartments) {
        const aSnap = await getDocs(collection(db, "buildings", bId, "apartments"));
        for (const d of aSnap.docs) {
          await deleteDoc(doc(db, "buildings", bId, "apartments", d.id));
        }
      }
    }
    this.payments = [];
    this.expenses = [];
    if (clearApartments) this.apartments = [];
    localStorage.removeItem(`sandoq_${bId}_payments`);
    localStorage.removeItem(`sandoq_${bId}_expenses`);
    if (clearApartments) localStorage.removeItem(`sandoq_${bId}_apartments`);
    this.notify();
    return true;
  }
}

export const store = new MultiTenantStore();
