// =========================================================
// Database Engine (Cloud Firestore + Local Cache Fallback)
// Sandoq Building Fund | المهندس أبو عادل
// =========================================================

import { 
  db, 
  collection, 
  doc, 
  getDocs, 
  setDoc, 
  addDoc, 
  deleteDoc, 
  onSnapshot, 
  query, 
  writeBatch 
} from "./firebase-config.js";

export const DEFAULT_APARTMENTS = [
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

class BuildingFundStore {
  constructor() {
    this.apartments = [];
    this.payments = [];
    this.expenses = [];
    this.listeners = [];
    this.isSyncing = false;
  }

  subscribe(listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  notify() {
    this.listeners.forEach(cb => cb({
      apartments: this.apartments,
      payments: this.payments,
      expenses: this.expenses
    }));
  }

  async initRealtime() {
    // 1. Initial Local Cache
    try {
      const cachedApts = localStorage.getItem("sandoq_apartments");
      const cachedPays = localStorage.getItem("sandoq_payments");
      const cachedExps = localStorage.getItem("sandoq_expenses");
      
      this.apartments = cachedApts ? JSON.parse(cachedApts) : [...DEFAULT_APARTMENTS];
      this.payments = cachedPays ? JSON.parse(cachedPays) : [];
      this.expenses = cachedExps ? JSON.parse(cachedExps) : [];
      this.notify();
    } catch (e) {
      this.apartments = [...DEFAULT_APARTMENTS];
    }

    if (!db) {
      console.warn("Firestore not available, using local store.");
      return;
    }

    // 2. Listen to Apartments
    try {
      onSnapshot(collection(db, "apartments"), async (snapshot) => {
        if (snapshot.empty) {
          // If Firestore is empty, seed with defaults
          console.log("Firestore apartments empty, seeding defaults...");
          for (const apt of DEFAULT_APARTMENTS) {
            await setDoc(doc(db, "apartments", String(apt.apt_no)), apt);
          }
        } else {
          this.apartments = snapshot.docs.map(d => ({ id: d.id, ...d.data() }));
          this.apartments.sort((a, b) => parseInt(a.apt_no || 0) - parseInt(b.apt_no || 0));
          localStorage.setItem("sandoq_apartments", JSON.stringify(this.apartments));
          this.notify();
        }
      }, (err) => console.error("Apartments listen error:", err));

      // 3. Listen to Payments
      onSnapshot(collection(db, "payments"), (snapshot) => {
        this.payments = snapshot.docs.map(d => ({ id: d.id, ...d.data() }));
        this.payments.sort((a, b) => new Date(b.created_at || b.payment_date || 0) - new Date(a.created_at || a.payment_date || 0));
        localStorage.setItem("sandoq_payments", JSON.stringify(this.payments));
        this.notify();
      }, (err) => console.error("Payments listen error:", err));

      // 4. Listen to Expenses
      onSnapshot(collection(db, "expenses"), (snapshot) => {
        this.expenses = snapshot.docs.map(d => ({ id: d.id, ...d.data() }));
        this.expenses.sort((a, b) => new Date(b.created_at || b.expense_date || 0) - new Date(a.created_at || a.expense_date || 0));
        localStorage.setItem("sandoq_expenses", JSON.stringify(this.expenses));
        this.notify();
      }, (err) => console.error("Expenses listen error:", err));
    } catch (err) {
      console.error("Firestore setup error:", err);
    }
  }

  // Save / Update Apartment
  async saveApartment(aptData) {
    const key = String(aptData.apt_no);
    if (db) {
      await setDoc(doc(db, "apartments", key), aptData, { merge: true });
    } else {
      const idx = this.apartments.findIndex(a => String(a.apt_no) === key);
      if (idx >= 0) this.apartments[idx] = aptData;
      else this.apartments.push(aptData);
      localStorage.setItem("sandoq_apartments", JSON.stringify(this.apartments));
      this.notify();
    }
    return true;
  }

  // Delete Apartment
  async deleteApartment(aptNo) {
    const key = String(aptNo);
    if (db) {
      await deleteDoc(doc(db, "apartments", key));
    } else {
      this.apartments = this.apartments.filter(a => String(a.apt_no) !== key);
      localStorage.setItem("sandoq_apartments", JSON.stringify(this.apartments));
      this.notify();
    }
    return true;
  }

  // Add Payment
  async addPayment(paymentData) {
    paymentData.created_at = new Date().toISOString();
    if (!paymentData.receipt_no) {
      const year = new Date().getFullYear();
      const num = this.payments.length + 1;
      paymentData.receipt_no = `REC-${year}-${String(num).padStart(3, '0')}`;
    }
    paymentData.amount = parseFloat(paymentData.amount) || 0;

    if (db) {
      const res = await addDoc(collection(db, "payments"), paymentData);
      paymentData.id = res.id;
    } else {
      paymentData.id = "pay_" + Date.now();
      this.payments.unshift(paymentData);
      localStorage.setItem("sandoq_payments", JSON.stringify(this.payments));
      this.notify();
    }
    return paymentData;
  }

  // Delete Payment
  async deletePayment(id) {
    if (db) {
      await deleteDoc(doc(db, "payments", id));
    } else {
      this.payments = this.payments.filter(p => p.id !== id);
      localStorage.setItem("sandoq_payments", JSON.stringify(this.payments));
      this.notify();
    }
    return true;
  }

  // Add Expense
  async addExpense(expenseData) {
    expenseData.created_at = new Date().toISOString();
    if (!expenseData.expense_no) {
      const year = new Date().getFullYear();
      const num = this.expenses.length + 1;
      expenseData.expense_no = `EXP-${year}-${String(num).padStart(3, '0')}`;
    }
    expenseData.amount = parseFloat(expenseData.amount) || 0;

    if (db) {
      const res = await addDoc(collection(db, "expenses"), expenseData);
      expenseData.id = res.id;
    } else {
      expenseData.id = "exp_" + Date.now();
      this.expenses.unshift(expenseData);
      localStorage.setItem("sandoq_expenses", JSON.stringify(this.expenses));
      this.notify();
    }
    return expenseData;
  }

  // Delete Expense
  async deleteExpense(id) {
    if (db) {
      await deleteDoc(doc(db, "expenses", id));
    } else {
      this.expenses = this.expenses.filter(e => e.id !== id);
      localStorage.setItem("sandoq_expenses", JSON.stringify(this.expenses));
      this.notify();
    }
    return true;
  }

  // Clear / Reset Database
  async clearAllData(clearApartments = false) {
    if (db) {
      const pSnap = await getDocs(collection(db, "payments"));
      for (const d of pSnap.docs) {
        await deleteDoc(doc(db, "payments", d.id));
      }
      const eSnap = await getDocs(collection(db, "expenses"));
      for (const d of eSnap.docs) {
        await deleteDoc(doc(db, "expenses", d.id));
      }
      if (clearApartments) {
        const aSnap = await getDocs(collection(db, "apartments"));
        for (const d of aSnap.docs) {
          await deleteDoc(doc(db, "apartments", d.id));
        }
      }
    }
    this.payments = [];
    this.expenses = [];
    if (clearApartments) this.apartments = [];
    localStorage.removeItem("sandoq_payments");
    localStorage.removeItem("sandoq_expenses");
    if (clearApartments) localStorage.removeItem("sandoq_apartments");
    this.notify();
    return true;
  }
}

export const store = new BuildingFundStore();
