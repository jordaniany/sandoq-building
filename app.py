import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import json
import os
import io
import urllib.parse
import re

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="صندوق العمارة السكنية | المهندس أبو عادل",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Firebase Admin SDK Initialization & Connection Handling
# ---------------------------------------------------------
FIREBASE_AVAILABLE = False
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

@st.cache_resource
def init_firestore():
    """Initializes Firebase Admin SDK and returns Firestore client."""
    if not FIREBASE_AVAILABLE:
        return None, "مكتبة firebase-admin غير مثبتة في بيئة العمل."

    try:
        if not firebase_admin._apps:
            key_filename = "serviceAccountKey.json"
            
            # 1. Try local serviceAccountKey.json file
            if os.path.exists(key_filename):
                cred = credentials.Certificate(key_filename)
                firebase_admin.initialize_app(cred)
            # 2. Try firebase_json in Secrets (Raw JSON string)
            elif "firebase_json" in st.secrets:
                raw_json = st.secrets["firebase_json"]
                cred_dict = json.loads(raw_json) if isinstance(raw_json, str) else dict(raw_json)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            # 3. Try dict in Secrets [firebase]
            elif "firebase" in st.secrets:
                cred_dict = dict(st.secrets["firebase"])
                if "private_key" in cred_dict:
                    cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            elif "gcp_service_account" in st.secrets:
                cred_dict = dict(st.secrets["gcp_service_account"])
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            else:
                return None, "لم يتم العثور على ملف الاعتماد serviceAccountKey.json أو مفاتيح Secrets."
        
        db = firestore.client()
        return db, "تم الاتصال بـ Firebase Cloud Firestore بنجاح! 🟢"
    except Exception as e:
        return None, f"خطأ في الاتصال بقاعدة البيانات: {str(e)}"

# ---------------------------------------------------------
# Custom CSS for Professional Arabic UI/UX (RTL & Modern Theme)
# ---------------------------------------------------------
def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800;900&display=swap');

        /* Global Font & RTL Layout */
        html, body, [class*="css"], .stApp {
            font-family: 'Tajawal', sans-serif !important;
            direction: rtl !important;
            text-align: right !important;
            background-color: #f8fafc;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
            color: #ffffff !important;
        }
        [data-testid="stSidebar"] * {
            color: #f1f5f9 !important;
        }
        [data-testid="stSidebarNav"] {
            padding-top: 1rem;
        }

        /* Main Container Padding */
        .main .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Tajawal', sans-serif !important;
            font-weight: 800 !important;
            color: #0f172a;
        }

        /* KPI Cards */
        .kpi-card {
            background-color: #ffffff;
            border-radius: 14px;
            padding: 22px 24px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            border: 1px solid #e2e8f0;
            border-right: 6px solid #2563eb;
            transition: all 0.3s ease;
            margin-bottom: 12px;
        }
        .kpi-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
        }
        .kpi-card.success { border-right-color: #10b981; }
        .kpi-card.warning { border-right-color: #f59e0b; }
        .kpi-card.danger { border-right-color: #ef4444; }
        .kpi-card.info { border-right-color: #3b82f6; }

        .kpi-title {
            font-size: 0.95rem;
            color: #64748b;
            font-weight: 700;
            margin-bottom: 6px;
        }
        .kpi-value {
            font-size: 1.9rem;
            font-weight: 900;
            color: #0f172a;
            letter-spacing: -0.5px;
        }
        .kpi-sub {
            font-size: 0.82rem;
            color: #94a3b8;
            margin-top: 4px;
            font-weight: 500;
        }

        /* Login Card */
        .login-box {
            background: #ffffff;
            border-radius: 18px;
            padding: 36px 32px;
            max-width: 440px;
            margin: 50px auto;
            box-shadow: 0 15px 35px rgba(15, 23, 42, 0.1);
            border: 1px solid #e2e8f0;
            border-top: 6px solid #2563eb;
            text-align: center;
        }
        .login-title {
            font-size: 1.6rem;
            font-weight: 900;
            color: #0f172a;
            margin-bottom: 6px;
        }
        .login-sub {
            font-size: 0.9rem;
            color: #64748b;
            margin-bottom: 24px;
        }

        /* Form Controls & Inputs */
        div[data-baseweb="select"] > div, input, textarea {
            border-radius: 10px !important;
            border: 1px solid #cbd5e1 !important;
            background-color: #ffffff !important;
            font-family: 'Tajawal', sans-serif !important;
        }

        /* Custom Buttons */
        .stButton > button {
            border-radius: 10px !important;
            font-family: 'Tajawal', sans-serif !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
            padding: 0.5rem 1.25rem !important;
            transition: all 0.25s ease !important;
            border: none !important;
            background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%) !important;
            color: #ffffff !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 18px rgba(37, 99, 235, 0.35) !important;
            background: linear-gradient(135deg, #1e40af 0%, #1d4ed8 100%) !important;
        }

        /* WhatsApp Button styling */
        .whatsapp-link {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background-color: #25D366;
            color: white !important;
            padding: 8px 16px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 700;
            font-size: 0.88rem;
            box-shadow: 0 3px 10px rgba(37, 211, 102, 0.3);
            transition: all 0.2s ease;
        }
        .whatsapp-link:hover {
            background-color: #1da851;
            transform: scale(1.03);
            box-shadow: 0 5px 15px rgba(37, 211, 102, 0.4);
            color: white !important;
        }

        /* Digital Receipt Container */
        .receipt-box {
            background: #ffffff;
            border: 2px solid #e2e8f0;
            border-top: 8px solid #1e3a8a;
            border-radius: 16px;
            padding: 28px;
            max-width: 650px;
            margin: 20px auto;
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            position: relative;
        }
        .receipt-header {
            text-align: center;
            border-bottom: 2px dashed #cbd5e1;
            padding-bottom: 16px;
            margin-bottom: 20px;
        }
        .receipt-row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #f1f5f9;
            font-size: 1rem;
        }
        .receipt-label {
            color: #64748b;
            font-weight: 700;
        }
        .receipt-val {
            color: #0f172a;
            font-weight: 800;
        }
        .receipt-total {
            background-color: #eff6ff;
            border-radius: 10px;
            padding: 14px;
            margin-top: 18px;
            text-align: center;
            border: 1px solid #bfdbfe;
        }
        .receipt-footer {
            margin-top: 24px;
            text-align: center;
            font-size: 0.85rem;
            color: #64748b;
            border-top: 1px solid #e2e8f0;
            padding-top: 14px;
        }

        /* Status Badge */
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.82rem;
            font-weight: 700;
        }
        .badge-success { background-color: #d1fae5; color: #065f46; }
        .badge-danger { background-color: #fee2e2; color: #991b1b; }
        .badge-warning { background-color: #fef3c7; color: #92400e; }

        /* Hide Streamlit default elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# Session State & Data Manager (Firestore / Local Fallback)
# ---------------------------------------------------------
def get_default_seed_data():
    """Initial realistic dataset for Jordanian building fund."""
    apartments = [
        {"apt_no": "101", "floor": "الطابق الأول", "resident_name": "أبو أحمد العبادي", "resident_type": "مالك", "phone": "962791234567", "monthly_fee": 25.0, "notes": "شقة أمامية"},
        {"apt_no": "102", "floor": "الطابق الأول", "resident_name": "المهندس محمود الفاعوري", "resident_type": "مالك", "phone": "962788765432", "monthly_fee": 25.0, "notes": "شقة خلفية"},
        {"apt_no": "201", "floor": "الطابق الثاني", "resident_name": "المهندس أبو عادل", "resident_type": "مالك", "phone": "962795551122", "monthly_fee": 25.0, "notes": "مسؤول لجنة العمارة"},
        {"apt_no": "202", "floor": "الطابق الثاني", "resident_name": "الدكتور يوسف المجالي", "resident_type": "مالك", "phone": "962799887766", "monthly_fee": 25.0, "notes": ""},
        {"apt_no": "301", "floor": "الطابق الثالث", "resident_name": "السيد عمر الشوابكة", "resident_type": "مستأجر", "phone": "962776655443", "monthly_fee": 25.0, "notes": "عقد سنوي"},
        {"apt_no": "302", "floor": "الطابق الثالث", "resident_name": "الأستاذ خالد النجار", "resident_type": "مالك", "phone": "962790112233", "monthly_fee": 25.0, "notes": ""},
        {"apt_no": "401", "floor": "الطابق الرابع", "resident_name": "السيد طارق الزعبي", "resident_type": "مستأجر", "phone": "962781122334", "monthly_fee": 25.0, "notes": ""},
        {"apt_no": "402", "floor": "الطابق الرابع", "resident_name": "المهندس زياد حداد", "resident_type": "مالك", "phone": "962793344556", "monthly_fee": 25.0, "notes": ""},
        {"apt_no": "G1", "floor": "التسوية / الأرضي", "resident_name": "السيد سامر الكردي", "resident_type": "مالك", "phone": "962794455667", "monthly_fee": 20.0, "notes": "حديقة خاصة"},
        {"apt_no": "G2", "floor": "التسوية / الأرضي", "resident_name": "السيد خليل حدادين", "resident_type": "مالك", "phone": "962785566778", "monthly_fee": 20.0, "notes": ""}
    ]

    current_month = date.today().strftime("%Y-%m")

    payments = [
        {"receipt_no": "REC-202609-101-101", "apt_no": "101", "resident_name": "أبو أحمد العبادي", "amount": 25.0, "for_month": "2026-09", "payment_method": "كاش", "payment_date": "2026-09-02 10:30", "notes": "تم السداد"},
        {"receipt_no": "REC-202609-201-102", "apt_no": "201", "resident_name": "المهندس أبو عادل", "amount": 25.0, "for_month": "2026-09", "payment_method": "CliQ", "payment_date": "2026-09-01 14:00", "notes": "حوالة كليك"},
        {"receipt_no": "REC-202609-202-103", "apt_no": "202", "resident_name": "الدكتور يوسف المجالي", "amount": 25.0, "for_month": "2026-09", "payment_method": "تحويل بنكي", "payment_date": "2026-09-05 09:15", "notes": ""},
        {"receipt_no": "REC-202609-301-104", "apt_no": "301", "resident_name": "السيد عمر الشوابكة", "amount": 25.0, "for_month": "2026-09", "payment_method": "كاش", "payment_date": "2026-09-07 18:00", "notes": ""},
        {"receipt_no": f"REC-{current_month.replace('-','')}-101-105", "apt_no": "101", "resident_name": "أبو أحمد العبادي", "amount": 25.0, "for_month": current_month, "payment_method": "كاش", "payment_date": f"{current_month}-02 11:00", "notes": "اشتراك الشهر"},
        {"receipt_no": f"REC-{current_month.replace('-','')}-201-106", "apt_no": "201", "resident_name": "المهندس أبو عادل", "amount": 25.0, "for_month": current_month, "payment_method": "CliQ", "payment_date": f"{current_month}-01 09:00", "notes": "سداد مبكر"},
        {"receipt_no": f"REC-{current_month.replace('-','')}-302-107", "apt_no": "302", "resident_name": "الأستاذ خالد النجار", "amount": 25.0, "for_month": current_month, "payment_method": "كاش", "payment_date": f"{current_month}-04 16:30", "notes": ""}
    ]

    expenses = [
        {"category": "صيانة المصعد الدورية", "amount": 40.0, "expense_date": f"{current_month}-03", "paid_to": "شركة المصاعد الذهبية", "description": "الصيانة الشهرية الشاملة للمصعد", "invoice_ref": "INV-9921"},
        {"category": "كهرباء الخدمات والدرج", "amount": 38.5, "expense_date": f"{current_month}-05", "paid_to": "شركة الكهرباء الأردنية", "description": "فاتورة كهرباء خدمات العمارة والمصعد", "invoice_ref": "ELEC-4412"},
        {"category": "أجرة الحارس / التنظيف", "amount": 50.0, "expense_date": f"{current_month}-01", "paid_to": "الحارس أبو محمد", "description": "راتب ومستحقات نظافة الدرج والخدمات", "invoice_ref": "REC-H-01"},
        {"category": "مياه الخدمات / صهريج", "amount": 15.0, "expense_date": "2026-09-12", "paid_to": "أبو علي للماء", "description": "تعبئة خزان الخدمات السفلي صهريج ماء", "invoice_ref": "W-12"}
    ]

    return apartments, payments, expenses

class BuildingFundDB:
    """Unified Database Interface supporting Firestore and SessionState Fallback."""
    def __init__(self, db_client):
        self.db = db_client
        self.use_firestore = (db_client is not None)

        if "local_apartments" not in st.session_state:
            apts, pays, exps = get_default_seed_data()
            st.session_state["local_apartments"] = apts
            st.session_state["local_payments"] = pays
            st.session_state["local_expenses"] = exps

    def _show_api_disabled_warning(self):
        st.warning("""
            ⚠️ **تنبيه:** خدمة Cloud Firestore غير مفعلة بعد في مشروع Firebase الخاص بك (`sandoq-building-2026`).
            يرجى تفعيلها بنقرة واحدة من لوحة التحكم:
            👉 [اضغط هنا لتفعيل Firestore Database](https://console.firebase.google.com/project/sandoq-building-2026/firestore)
            (اضغط على Create Database ثم اختر Test Mode).
        """)

    # --- Apartments ---
    def get_apartments(self):
        if self.use_firestore:
            try:
                docs = self.db.collection("apartments").stream()
                apts = []
                for doc in docs:
                    d = doc.to_dict()
                    d["doc_id"] = doc.id
                    apts.append(d)
                return sorted(apts, key=lambda x: str(x.get("apt_no", "")))
            except Exception as e:
                if "403" in str(e) or "disabled" in str(e):
                    self._show_api_disabled_warning()
                else:
                    st.error(f"خطأ عند قراءة الشقق من Firestore: {e}")
                return st.session_state["local_apartments"]
        else:
            return sorted(st.session_state["local_apartments"], key=lambda x: str(x.get("apt_no", "")))

    def save_apartment(self, apt_data):
        apt_no = str(apt_data["apt_no"]).strip()
        if self.use_firestore:
            try:
                self.db.collection("apartments").document(apt_no).set(apt_data, merge=True)
                st.success(f"تم حفظ بيانات الشقة ({apt_no}) - {apt_data['resident_name']} بنجاح! 🟢")
            except Exception as e:
                if "403" in str(e) or "disabled" in str(e):
                    self._show_api_disabled_warning()
                else:
                    st.error(f"فشل الحفظ في Firestore: {e}")
        
        local_apts = st.session_state["local_apartments"]
        idx = next((i for i, a in enumerate(local_apts) if str(a["apt_no"]) == apt_no), None)
        if idx is not None:
            local_apts[idx] = apt_data
        else:
            local_apts.append(apt_data)
        st.session_state["local_apartments"] = local_apts

    def delete_apartment(self, apt_no):
        apt_no_str = str(apt_no).strip()
        if self.use_firestore:
            try:
                self.db.collection("apartments").document(apt_no_str).delete()
                st.success(f"تم حذف الشقة ({apt_no_str}) بنجاح من Firestore! 🗑️")
            except Exception as e:
                st.error(f"فشل الحذف من Firestore: {e}")

        st.session_state["local_apartments"] = [
            a for a in st.session_state["local_apartments"] if str(a["apt_no"]) != apt_no_str
        ]

    # --- Payments ---
    def get_payments(self):
        if self.use_firestore:
            try:
                docs = self.db.collection("payments").stream()
                pays = [doc.to_dict() for doc in docs]
                return sorted(pays, key=lambda x: str(x.get("payment_date", "")), reverse=True)
            except Exception as e:
                if "403" in str(e) or "disabled" in str(e):
                    pass
                else:
                    st.error(f"خطأ عند قراءة المقبوضات من Firestore: {e}")
                return st.session_state["local_payments"]
        else:
            return sorted(st.session_state["local_payments"], key=lambda x: str(x.get("payment_date", "")), reverse=True)

    def add_payment(self, payment_data):
        if self.use_firestore:
            try:
                self.db.collection("payments").add(payment_data)
                st.success("تم تسجيل سند القبض في Firestore بنجاح! 🟢")
            except Exception as e:
                if "403" in str(e) or "disabled" in str(e):
                    self._show_api_disabled_warning()
                else:
                    st.error(f"فشل الحفظ في Firestore: {e}")
        
        st.session_state["local_payments"].insert(0, payment_data)

    # --- Expenses ---
    def get_expenses(self):
        if self.use_firestore:
            try:
                docs = self.db.collection("expenses").stream()
                exps = [doc.to_dict() for doc in docs]
                return sorted(exps, key=lambda x: str(x.get("expense_date", "")), reverse=True)
            except Exception as e:
                if "403" in str(e) or "disabled" in str(e):
                    pass
                else:
                    st.error(f"خطأ عند قراءة المصروفات من Firestore: {e}")
                return st.session_state["local_expenses"]
        else:
            return sorted(st.session_state["local_expenses"], key=lambda x: str(x.get("expense_date", "")), reverse=True)

    def add_expense(self, expense_data):
        if self.use_firestore:
            try:
                self.db.collection("expenses").add(expense_data)
                st.success("تم تسجيل سند الصرف في Firestore بنجاح! 🟢")
            except Exception as e:
                if "403" in str(e) or "disabled" in str(e):
                    self._show_api_disabled_warning()
                else:
                    st.error(f"فشل الحفظ في Firestore: {e}")

        st.session_state["local_expenses"].insert(0, expense_data)

    def clear_all_data(self, clear_apartments=False):
        """Wipes payments, expenses, and optionally apartments from Firestore and local state."""
        if self.use_firestore:
            try:
                # Delete all payments
                pay_docs = self.db.collection("payments").stream()
                for doc in pay_docs:
                    doc.reference.delete()

                # Delete all expenses
                exp_docs = self.db.collection("expenses").stream()
                for doc in exp_docs:
                    doc.reference.delete()

                # Delete apartments if requested
                if clear_apartments:
                    apt_docs = self.db.collection("apartments").stream()
                    for doc in apt_docs:
                        doc.reference.delete()

                st.success("تم تفريغ وتصفير بيانات قاعدة البيانات في Cloud Firestore بنجاح! 🧹")
            except Exception as err:
                st.error(f"حدث خطأ أثناء تفريغ البيانات من Firestore: {err}")

        # Always clear local state
        st.session_state["local_payments"] = []
        st.session_state["local_expenses"] = []
        if clear_apartments:
            st.session_state["local_apartments"] = []

# ---------------------------------------------------------
# Helper Functions (Formatting, WhatsApp URLs, Downloads)
# ---------------------------------------------------------
def generate_whatsapp_link(phone: str, message: str) -> str:
    """Formats international Jordanian phone number and encodes message for WhatsApp URL."""
    clean_phone = re.sub(r"[^\d]", "", str(phone))
    encoded_msg = urllib.parse.quote(message)
    return f"https://wa.me/{clean_phone}?text={encoded_msg}"

def get_arabic_month_name(month_str: str) -> str:
    """Translates YYYY-MM into a friendly Arabic month string (e.g. أكتوبـر 2026)."""
    try:
        dt = datetime.strptime(month_str, "%Y-%m")
        months_ar = [
            "كانون الثاني (1)", "شباط (2)", "آذار (3)", "نيسان (4)", 
            "أيار (5)", "حزيران (6)", "تموز (7)", "آب (8)", 
            "أيلول (9)", "تشرين الأول (10)", "تشرين الثاني (11)", "كانون الأول (12)"
        ]
        return f"{months_ar[dt.month - 1]} {dt.year}"
    except Exception:
        return month_str

def create_excel_download(df: pd.DataFrame, filename: str) -> bytes:
    """Exports DataFrame into Excel bytes buffer."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='التقرير_المالي')
    return output.getvalue()

# ---------------------------------------------------------
# AUTHENTICATION & LOGIN SCREEN
# ---------------------------------------------------------
def get_master_password():
    """Retrieves master password from secrets or environment or default."""
    if "APP_PASSWORD" in st.secrets:
        return str(st.secrets["APP_PASSWORD"])
    return os.getenv("APP_PASSWORD", "abuadel2026")

def render_login_screen():
    inject_custom_css()
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("""
            <div class="login-box">
                <div style="font-size:3rem; margin-bottom:10px;">🏛️</div>
                <div class="login-title">صندوق العمارة السكنية</div>
                <div class="login-sub">لوحة التحكّم بمسؤولية المهندس أبو عادل</div>
                <p style="color:#64748b; font-size:0.9rem; margin-bottom:15px;">يرجى إدخال كلمة المرور لتأمين النظام والولوج</p>
            </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            password_input = st.text_input("🔑 كلمة المرور:", type="password", placeholder="أدخل كلمة المرور...")
            submit_login = st.form_submit_button("🔓 تسجيل الدخول")

            if submit_login:
                master_pwd = get_master_password()
                if password_input.strip() == master_pwd:
                    st.session_state["authenticated"] = True
                    st.success("تم تسجيل الدخول بنجاح! 🟢")
                    st.experimental_rerun() if hasattr(st, 'experimental_rerun') else st.rerun()
                else:
                    st.error("❌ كلمة المرور غير صحيحة، يرجى المحاولة مجدداً.")

        st.info("💡 كلمة المرور الافتراضية للتجربة: `abuadel2026` (يمكنك تخصيصها عبر `st.secrets`).")

# ---------------------------------------------------------
# PAGE 1: Dashboard & KPIs (لوحة المؤشرات والقيادة)
# ---------------------------------------------------------
def render_dashboard_page(db_engine: BuildingFundDB):
    st.markdown("## 📊 لوحة المؤشرات والقيادة المالية")
    st.markdown("نظرة عامة شمولية ومباشرة على وضع صندوق العمارة السكنية - إشراف المهندس أبو عادل.")
    st.markdown("---")

    apartments = db_engine.get_apartments()
    payments = db_engine.get_payments()
    expenses = db_engine.get_expenses()

    df_apts = pd.DataFrame(apartments) if apartments else pd.DataFrame()
    df_pays = pd.DataFrame(payments) if payments else pd.DataFrame()
    df_exps = pd.DataFrame(expenses) if expenses else pd.DataFrame()

    total_payments_all_time = df_pays["amount"].sum() if not df_pays.empty and "amount" in df_pays.columns else 0.0
    total_expenses_all_time = df_exps["amount"].sum() if not df_exps.empty and "amount" in df_exps.columns else 0.0
    current_fund_balance = total_payments_all_time - total_expenses_all_time

    current_ym = date.today().strftime("%Y-%m")
    
    available_months = sorted(list(set(
        (df_pays["for_month"].tolist() if not df_pays.empty and "for_month" in df_pays.columns else []) + [current_ym]
    )), reverse=True)

    col_filter1, col_filter2 = st.columns([2, 2])
    with col_filter1:
        selected_month = st.selectbox("📅 اختر شهر المتابعة والتحصيل:", available_months, index=0)

    if not df_pays.empty and "for_month" in df_pays.columns and "amount" in df_pays.columns:
        month_pays_df = df_pays[df_pays["for_month"] == selected_month]
        month_collections = month_pays_df["amount"].sum()
    else:
        month_collections = 0.0

    expected_monthly_total = df_apts["monthly_fee"].sum() if not df_apts.empty and "monthly_fee" in df_apts.columns else 250.0
    collection_percentage = (month_collections / expected_monthly_total * 100) if expected_monthly_total > 0 else 0.0

    if not df_exps.empty and "expense_date" in df_exps.columns and "amount" in df_exps.columns:
        df_exps["ym"] = df_exps["expense_date"].astype(str).str.slice(0, 7)
        month_exps_df = df_exps[df_exps["ym"] == selected_month]
        month_expenses = month_exps_df["amount"].sum()
    else:
        month_expenses = 0.0

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        card_color = "success" if current_fund_balance >= 0 else "danger"
        st.markdown(f"""
            <div class="kpi-card {card_color}">
                <div class="kpi-title">💵 الرصيد الحالي الفعلي في الصندوق</div>
                <div class="kpi-value">{current_fund_balance:,.2f} د.أ</div>
                <div class="kpi-sub">المقبوضات الكلية - المصروفات الكلية</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_col2:
        st.markdown(f"""
            <div class="kpi-card info">
                <div class="kpi-title">📥 تحصيلات شهر ({selected_month})</div>
                <div class="kpi-value">{month_collections:,.2f} د.أ</div>
                <div class="kpi-sub">من أصل المتوقع: {expected_monthly_total:,.2f} د.أ</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_col3:
        perc_color = "success" if collection_percentage >= 80 else ("warning" if collection_percentage >= 50 else "danger")
        st.markdown(f"""
            <div class="kpi-card {perc_color}">
                <div class="kpi-title">📈 نسبة التحصيل الشهرية</div>
                <div class="kpi-value">{collection_percentage:.1f}%</div>
                <div class="kpi-sub">مستوى التزام الشقق بالسداد</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_col4:
        st.markdown(f"""
            <div class="kpi-card danger">
                <div class="kpi-title">📤 مصروفات شهر ({selected_month})</div>
                <div class="kpi-value">{month_expenses:,.2f} د.أ</div>
                <div class="kpi-sub">فواتير وصيانة مرافق العمارة</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Defaulters Table
    st.markdown(f"### ⚠️ جدول المتابعة الفوري والمتأخرات لشهر ({get_arabic_month_name(selected_month)})")
    
    paid_apts = set()
    if not df_pays.empty and "for_month" in df_pays.columns:
        paid_apts = set(df_pays[df_pays["for_month"] == selected_month]["apt_no"].astype(str).unique())

    unpaid_list = []
    if not df_apts.empty:
        for _, apt in df_apts.iterrows():
            apt_no = str(apt["apt_no"])
            if apt_no not in paid_apts:
                unpaid_list.append(apt)

    if unpaid_list:
        st.info(f"يوجد حالياً ({len(unpaid_list)}) شقق لم تسدد اشتراك شهر {selected_month}. يمكنك الضغط على زر التذكير لإرسال رسالة واتساب مباشرة للساكن.")
        
        df_unpaid = pd.DataFrame(unpaid_list)
        
        for idx, row in df_unpaid.iterrows():
            apt_no = str(row.get("apt_no", ""))
            resident = str(row.get("resident_name", "جارنا العزيز"))
            phone = str(row.get("phone", ""))
            fee = float(row.get("monthly_fee", 25.0))
            floor = str(row.get("floor", ""))
            rtype = str(row.get("resident_type", "مالك"))

            msg_text = (
                f"مرحباً جارنا العزيز {resident}، تحية طيبة من لجنة العمارة (إشراف المهندس أبو عادل). "
                f"نود تذكيركم بلطف باشتراك خدمات العمارة لشهر {selected_month} بقيمة {fee:g} دينار. "
                f"شاكرين ومقدرين حسن تعاونكم وحرصكم الدائم على العمارة. 🌸"
            )
            
            wa_url = generate_whatsapp_link(phone, msg_text)

            col_a, col_b, col_c, col_d, col_e = st.columns([1.2, 2.5, 1.5, 1.5, 2.5])
            with col_a:
                st.markdown(f"**شقة {apt_no}** <br><small>{floor}</small>", unsafe_allow_html=True)
            with col_b:
                st.markdown(f"**{resident}** <br><small>الصفة: {rtype}</small>", unsafe_allow_html=True)
            with col_c:
                st.markdown(f"**{fee:g} د.أ**", unsafe_allow_html=True)
            with col_d:
                st.markdown("<span class='badge badge-danger'>لم يتم السداد</span>", unsafe_allow_html=True)
            with col_e:
                st.markdown(f"""
                    <a href="{wa_url}" target="_blank" class="whatsapp-link">
                        📱 تذكير عبر واتساب
                    </a>
                """, unsafe_allow_html=True)
            st.markdown("<hr style='margin: 8px 0; border-color: #f1f5f9;'>", unsafe_allow_html=True)
    else:
        st.success(f"🎉 ما شاء الله! جميع الشقق مسددة بالكامل لشهر {selected_month}.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Plotly Financial Flow Chart
    st.markdown("### 📉 التغير والتدفق المالي (المقبوضات مقابل المصروفات)")
    
    months_data = []
    today = date.today()
    for i in range(5, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        ym_key = f"{y:04d}-{m:02d}"
        
        p_val = 0.0
        if not df_pays.empty and "for_month" in df_pays.columns and "amount" in df_pays.columns:
            p_val = df_pays[df_pays["for_month"] == ym_key]["amount"].sum()
            
        e_val = 0.0
        if not df_exps.empty and "expense_date" in df_exps.columns and "amount" in df_exps.columns:
            e_val = df_exps[df_exps["expense_date"].astype(str).str.slice(0, 7) == ym_key]["amount"].sum()

        months_data.append({
            "الشهر": ym_key,
            "إجمالي المقبوضات (د.أ)": p_val,
            "إجمالي المصروفات (د.أ)": e_val,
            "الصافي (د.أ)": p_val - e_val
        })

    df_chart = pd.DataFrame(months_data)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_chart["الشهر"],
        y=df_chart["إجمالي المقبوضات (د.أ)"],
        name="المقبوضات",
        marker_color="#10b981"
    ))
    fig.add_trace(go.Bar(
        x=df_chart["الشهر"],
        y=df_chart["إجمالي المصروفات (د.أ)"],
        name="المصروفات",
        marker_color="#ef4444"
    ))
    fig.add_trace(go.Scatter(
        x=df_chart["الشهر"],
        y=df_chart["الصافي (د.أ)"],
        name="الصافي المتبقي",
        mode="lines+markers",
        line=dict(color="#2563eb", width=3)
    ))

    fig.update_layout(
        barmode='group',
        title="مقارنة المقبوضات والمصروفات الشهرية (آخر 6 أشهر)",
        xaxis_title="الشهر المستحق",
        yaxis_title="المبلغ (بالدينار الأردني JOD)",
        font=dict(family="Tajawal, sans-serif", size=13),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# PAGE 2: Digital Payment Receipt (تسجيل مقبوضات جديدة)
# ---------------------------------------------------------
def render_payment_page(db_engine: BuildingFundDB):
    st.markdown("## 🧾 إصدار سند قبض رقمي وتسجيل الدفعات")
    st.markdown("قم باختيار الشقة وتسجيل قيمة الاشتراك الشهري لإصدار وصل استلام رسمي فوري.")
    st.markdown("---")

    apartments = db_engine.get_apartments()
    if not apartments:
        st.warning("⚠️ لا توجد شقق مسجلة في النظام بعد. يرجى إضافة الشقق أولاً من شاشة دليل الشقق.")
        return

    df_apts = pd.DataFrame(apartments)
    apt_options = {f"شقة {row['apt_no']} - {row['resident_name']}": row for _, row in df_apts.iterrows()}

    c1, c2 = st.columns([1.5, 1])

    with c1:
        st.markdown("#### 📝 بيانات سند القبض")
        with st.form("payment_form", clear_on_submit=False):
            selected_apt_label = st.selectbox("اختر الشقة والساكن:", list(apt_options.keys()))
            selected_apt_data = apt_options[selected_apt_label]

            apt_no = str(selected_apt_data["apt_no"])
            resident_name = str(selected_apt_data["resident_name"])
            default_fee = float(selected_apt_data.get("monthly_fee", 25.0))
            resident_phone = str(selected_apt_data.get("phone", ""))

            col_form1, col_form2 = st.columns(2)
            with col_form1:
                st.text_input("اسم الساكن / رب الأسرة:", value=resident_name, disabled=True)
                amount = st.number_input("المبلغ المدفوع (د.أ):", value=default_fee, min_value=1.0, step=5.0)
            
            with col_form2:
                current_ym = date.today().strftime("%Y-%m")
                for_month = st.text_input("عن شهر (YYYY-MM):", value=current_ym)
                payment_method = st.selectbox("طريقة الدفع:", ["كاش", "CliQ", "تحويل بنكي"])

            notes = st.text_area("ملاحظات الدفعة (إن وجدت):", placeholder="مثلاً: سداد مبكر / سداد جزء من المتأخرات...")
            
            submit_payment = st.form_submit_button("💾 حفظ وتأكيد الاستلام وإصدار الوصل")

    if submit_payment:
        receipt_no = f"REC-{for_month.replace('-', '')}-{apt_no}-{int(datetime.now().timestamp()) % 10000:04d}"
        payment_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")

        payment_record = {
            "receipt_no": receipt_no,
            "apt_no": apt_no,
            "resident_name": resident_name,
            "amount": float(amount),
            "for_month": for_month.strip(),
            "payment_method": payment_method,
            "payment_date": payment_datetime,
            "notes": notes.strip(),
            "created_at": datetime.now().isoformat()
        }

        db_engine.add_payment(payment_record)
        st.session_state["last_receipt"] = payment_record
        st.session_state["last_phone"] = resident_phone

    if "last_receipt" in st.session_state:
        rec = st.session_state["last_receipt"]
        phone = st.session_state.get("last_phone", "")

        with c2:
            st.markdown("#### 📄 المعاينة الرقمية لسند القبض")
            st.markdown(f"""
                <div class="receipt-box" id="printableReceipt">
                    <div class="receipt-header">
                        <h3 style="margin:0; color:#1e3a8a;">🏛️ لجنة إدارة العمارة السكنية</h3>
                        <p style="margin:4px 0 0 0; font-size:0.9rem; color:#64748b;">إشراف المهندس أبو عادل - سند قبض رقمي</p>
                        <span style="font-size:0.8rem; background:#e2e8f0; padding:2px 8px; border-radius:4px; margin-top:6px; display:inline-block;">
                            رقم السند: {rec['receipt_no']}
                        </span>
                    </div>
                    <div class="receipt-row">
                        <span class="receipt-label">رقم الشقة:</span>
                        <span class="receipt-val">شقة ({rec['apt_no']})</span>
                    </div>
                    <div class="receipt-row">
                        <span class="receipt-label">استلمنا من السيد/ة:</span>
                        <span class="receipt-val">{rec['resident_name']}</span>
                    </div>
                    <div class="receipt-row">
                        <span class="receipt-label">بدل اشتراك شهر:</span>
                        <span class="receipt-val">{rec['for_month']}</span>
                    </div>
                    <div class="receipt-row">
                        <span class="receipt-label">طريقة الدفع:</span>
                        <span class="receipt-val">{rec['payment_method']}</span>
                    </div>
                    <div class="receipt-row">
                        <span class="receipt-label">تاريخ الاستلام:</span>
                        <span class="receipt-val">{rec['payment_date']}</span>
                    </div>
                    <div class="receipt-total">
                        <div style="font-size:0.9rem; color:#1e40af; font-weight:700;">إجمالي المبلغ المقبوض</div>
                        <div style="font-size:2rem; font-weight:900; color:#1e3a8a;">{rec['amount']:,.2f} دينار أردني</div>
                    </div>
                    <div class="receipt-footer">
                        شاكرين ومقدرين حسن تعاونكم وحرصكم الدائم على العمارة 🌸<br>
                        <strong>توقيع واعتتماد: المهندس أبو عادل</strong>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            wa_msg = (
                f"تم بحمد الله استلام مبلغ ({rec['amount']:g} دينار) لقاء اشتراك خدمات العمارة لشهر {rec['for_month']} "
                f"للشقة رقم ({rec['apt_no']}) - {rec['resident_name']}.\n"
                f"رقم السند الرقمي: {rec['receipt_no']}\n"
                f"تاريخ الحركة: {rec['payment_date']}\n\n"
                f"شاكرين تعاونكم العاطر. لجنة العمارة - المهندس أبو عادل 🌸"
            )
            wa_url = generate_whatsapp_link(phone, wa_msg)

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                st.markdown(f"""
                    <a href="{wa_url}" target="_blank" class="whatsapp-link" style="width:100%; text-align:center;">
                        📱 إرسال وصل الاستلام عبر واتساب
                    </a>
                """, unsafe_allow_html=True)
            with col_btn2:
                st.button("🖨️ طباعة السند / حفظ PDF", on_click=lambda: st.components.v1.html("<script>window.print();</script>", height=0))

# ---------------------------------------------------------
# PAGE 3: Expense Voucher & Maintenance (سند صرف ومصاريف)
# ---------------------------------------------------------
def render_expense_page(db_engine: BuildingFundDB):
    st.markdown("## 💸 تسجيل المصروفات وأعمال الصيانة (سند صرف)")
    st.markdown("إدخال وتوثيق كافة الفواتير، أعمال الصيانة الدورية والطارئة، وأجور الخدمات بكل شفافية.")
    st.markdown("---")

    col_form, col_list = st.columns([1.3, 2])

    with col_form:
        st.markdown("#### 📥 نموذج سند صرف جديد")
        with st.form("expense_form", clear_on_submit=True):
            category = st.selectbox("تصنيف المصروف:", [
                "صيانة المصعد الدورية",
                "كهرباء الخدمات والدرج",
                "مياه الخدمات / صهريج",
                "أجرة الحارس / التنظيف",
                "صيانة مضخات وتمديدات طارئة",
                "أدوات ومواد نظافة",
                "متفرقات"
            ])

            amount = st.number_input("المبلغ المصروف (د.أ):", min_value=0.5, step=5.0, value=25.0)
            expense_date = st.date_input("تاريخ الدفع والصرف:", value=date.today())
            paid_to = st.text_input("الجهة / الفني / المستلم:", placeholder="مثال: شركة الكهرباء / شركة المصاعد / الحارس...")
            description = st.text_area("تفاصيل العمل / العطل المصُلح:", placeholder="اكتب وصف دقيق ومفصل للمصروف...")
            invoice_ref = st.text_input("رقم الفاتورة أو السند الورقي (إن وجد):", placeholder="مثلاً: INV-1092")

            submit_exp = st.form_submit_button("💾 حفظ سند الصرف في الصندوق")

        if submit_exp:
            exp_record = {
                "category": category,
                "amount": float(amount),
                "expense_date": expense_date.strftime("%Y-%m-%d"),
                "paid_to": paid_to.strip(),
                "description": description.strip(),
                "invoice_ref": invoice_ref.strip(),
                "created_at": datetime.now().isoformat()
            }
            db_engine.add_expense(exp_record)

    with col_list:
        st.markdown("#### 📋 سجل الحركة المالية للمصروفات")
        expenses = db_engine.get_expenses()

        if expenses:
            df_exp = pd.DataFrame(expenses)
            
            search_query = st.text_input("🔍 بحث في المصروفات (بالتصنيف، الجهة المستلمة، أو تفاصيل العمل):")
            
            if search_query:
                mask = (
                    df_exp["category"].str.contains(search_query, case=False, na=False) |
                    df_exp["paid_to"].str.contains(search_query, case=False, na=False) |
                    df_exp["description"].str.contains(search_query, case=False, na=False)
                )
                df_exp = df_exp[mask]

            df_display = df_exp[["expense_date", "category", "amount", "paid_to", "description", "invoice_ref"]].copy()
            df_display.columns = ["التاريخ", "البند / التصنيف", "المبلغ (د.أ)", "الجهة المستلمة", "التفاصيل", "رقم الفاتورة"]
            
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True
            )

            total_filtered = df_display["المبلغ (د.أ)"].sum()
            st.markdown(f"**إجمالي المصروفات المعروضة:** `{total_filtered:,.2f} د.أ`")
        else:
            st.info("لا توجد مصروفات مسجلة حتى الآن.")

# ---------------------------------------------------------
# PAGE 4: Apartment & Resident Directory (دليل الشقق والسكان)
# ---------------------------------------------------------
def render_apartments_page(db_engine: BuildingFundDB):
    st.markdown("## 🏢 دليل الشقق والسكان وإدارة الاشتراكات")
    st.markdown("إدارة بيانات الشقق، أسماء الساكنين، إضافة سكان جدد، وتغيير البيانات بنقرة واحدة.")
    st.markdown("---")

    tab_view, tab_manage = st.tabs(["📋 دليل الشقق الحالي", "➕ إضافة / تعديل بيانات شقة"])

    apartments = db_engine.get_apartments()
    df_apts = pd.DataFrame(apartments) if apartments else pd.DataFrame()

    # Pre-selection logic for quick inline edit button
    if "editing_apt_no" not in st.session_state:
        st.session_state["editing_apt_no"] = None

    with tab_view:
        if not df_apts.empty:
            c_srch, c_stat = st.columns([2, 1])
            with c_srch:
                search_apt = st.text_input("🔍 بحث برقم الشقة أو اسم الساكن:")
            
            df_filtered = df_apts.copy()
            if search_apt:
                mask = (
                    df_filtered["apt_no"].astype(str).str.contains(search_apt, case=False, na=False) |
                    df_filtered["resident_name"].astype(str).str.contains(search_apt, case=False, na=False)
                )
                df_filtered = df_filtered[mask]

            for _, apt in df_filtered.iterrows():
                apt_no = str(apt.get("apt_no", ""))
                resident = str(apt.get("resident_name", ""))
                rtype = str(apt.get("resident_type", "مالك"))
                phone = str(apt.get("phone", ""))
                fee = float(apt.get("monthly_fee", 25.0))
                floor = str(apt.get("floor", ""))

                c1, c2, c3, c4, c5, c6 = st.columns([1.2, 2.2, 1.3, 1.5, 1.8, 1.5])
                with c1:
                    st.markdown(f"**🏢 شقة {apt_no}**<br><small style='color:#64748b;'>{floor}</small>", unsafe_allow_html=True)
                with c2:
                    badge_cls = "badge-success" if rtype == "مالك" else "badge-warning"
                    st.markdown(f"**{resident}**<br><span class='badge {badge_cls}'>{rtype}</span>", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"**{fee:g} د.أ / شهرياً**", unsafe_allow_html=True)
                with c4:
                    st.markdown(f"<small>{phone}</small>", unsafe_allow_html=True)
                with c5:
                    wa_url = generate_whatsapp_link(phone, f"مرحباً جارنا العزيز {resident}، تحية طيبة من لجنة العمارة.")
                    st.markdown(f"""
                        <a href="{wa_url}" target="_blank" class="whatsapp-link" style="padding: 4px 10px; font-size:0.8rem;">
                            📱 تواصل واتساب
                        </a>
                    """, unsafe_allow_html=True)
                with c6:
                    if st.button(f"✏️ تعديل", key=f"btn_edit_{apt_no}"):
                        st.session_state["editing_apt_no"] = apt_no
                        st.experimental_rerun() if hasattr(st, 'experimental_rerun') else st.rerun()

                st.markdown("<hr style='margin:6px 0; border-color:#e2e8f0;'>", unsafe_allow_html=True)
        else:
            st.info("لا توجد شقق مسجلة بعد. يمكنك إضافة شقق وسكان جدد من التبويب المالي الجانبي.")

    with tab_manage:
        st.markdown("#### ✏️ إضافة شقة جديدة أو تعديل بيانات ساكن حالي")
        
        edit_mode = st.radio("نوع العملية:", ["إضافة شقة / ساكن جديد", "تعديل بيانات شقة حالية"], horizontal=True)

        selected_existing = None
        if edit_mode == "تعديل بيانات شقة حالية" and not df_apts.empty:
            apt_map = {f"شقة {r['apt_no']} - {r['resident_name']}": r for _, r in df_apts.iterrows()}
            
            # Auto-select if clicked edit from list
            default_index = 0
            if st.session_state.get("editing_apt_no"):
                target_no = st.session_state["editing_apt_no"]
                matching_keys = [k for k in apt_map.keys() if f"شقة {target_no} " in k]
                if matching_keys:
                    default_index = list(apt_map.keys()).index(matching_keys[0])

            selected_key = st.selectbox("اختر الشقة المراد تعديل بياناتها:", list(apt_map.keys()), index=default_index)
            selected_existing = apt_map[selected_key]

        with st.form("apartment_form"):
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                default_apt_no = str(selected_existing["apt_no"]) if selected_existing is not None else ""
                apt_no_in = st.text_input("رقم الشقة (المعرف الفريد):", value=default_apt_no, placeholder="مثال: 101, 202, G1")
                
                default_res = str(selected_existing["resident_name"]) if selected_existing is not None else ""
                resident_name_in = st.text_input("اسم الساكن / رب الأسرة:", value=default_res, placeholder="مثال: أبو أحمد العبادي")
                
                default_floor = str(selected_existing["floor"]) if selected_existing is not None else "الطابق الأول"
                floor_in = st.text_input("الطابق:", value=default_floor)

            with col_a2:
                default_rtype = str(selected_existing["resident_type"]) if selected_existing is not None else "مالك"
                rtype_idx = 0 if default_rtype == "مالك" else 1
                resident_type_in = st.selectbox("صفة الساكن:", ["مالك", "مستأجر"], index=rtype_idx)
                
                default_phone = str(selected_existing["phone"]) if selected_existing is not None else "9627"
                phone_in = st.text_input("رقم الهاتف (بالصيغة الدولية):", value=default_phone, placeholder="962791234567")
                
                default_fee = float(selected_existing["monthly_fee"]) if selected_existing is not None else 25.0
                monthly_fee_in = st.number_input("قيمة الاشتراك الشهري المقررة (د.أ):", value=default_fee, min_value=0.0, step=5.0)

            notes_in = st.text_area("ملاحظات خاصة بالشقة:", value=str(selected_existing.get("notes", "")) if selected_existing is not None else "")

            c_sub1, c_sub2 = st.columns([2, 1])
            with c_sub1:
                submit_apt = st.form_submit_button("💾 حفظ وتحديث بيانات الشقة")

        if submit_apt:
            if not apt_no_in.strip() or not resident_name_in.strip():
                st.error("يرجى تعبئة رقم الشقة واسم الساكن بشكل صحيح.")
            else:
                apt_record = {
                    "apt_no": apt_no_in.strip(),
                    "floor": floor_in.strip(),
                    "resident_name": resident_name_in.strip(),
                    "resident_type": resident_type_in,
                    "phone": phone_in.strip(),
                    "monthly_fee": float(monthly_fee_in),
                    "notes": notes_in.strip()
                }
                db_engine.save_apartment(apt_record)
                st.session_state["editing_apt_no"] = None
                st.experimental_rerun() if hasattr(st, 'experimental_rerun') else st.rerun()

        # Delete apartment option if editing existing
        if selected_existing is not None:
            st.markdown("---")
            with st.expander("🗑️ حذف هذه الشقة من النظام"):
                st.warning(f"هل أنت تأكد من رغبتك في حذف بيانات الشقة ({selected_existing['apt_no']})؟")
                if st.button("نعم، احذف الشقة نهائياً"):
                    db_engine.delete_apartment(selected_existing['apt_no'])
                    st.session_state["editing_apt_no"] = None
                    st.experimental_rerun() if hasattr(st, 'experimental_rerun') else st.rerun()

# ---------------------------------------------------------
# PAGE 5: Financial Reports, Exports & Transparency (الكشوفات والتقارير)
# ---------------------------------------------------------
def render_reports_page(db_engine: BuildingFundDB):
    st.markdown("## 📈 كشوفات الحساب والتقارير والشفافية")
    st.markdown("ميزان المراجعة، تصدير التقارير المالية لإكسل، وإعادة تهيئة السجلات وتصفير الصندوق.")
    st.markdown("---")

    payments = db_engine.get_payments()
    expenses = db_engine.get_expenses()

    df_pays = pd.DataFrame(payments) if payments else pd.DataFrame()
    df_exps = pd.DataFrame(expenses) if expenses else pd.DataFrame()

    available_months = ["جميع الفترات (كشف كامل)"]
    if not df_pays.empty and "for_month" in df_pays.columns:
        available_months += sorted(list(df_pays["for_month"].unique()), reverse=True)

    filter_period = st.selectbox("📅 اختر فترة التقرير وكشف الحساب:", available_months)

    if filter_period != "جميع الفترات (كشف كامل)":
        filtered_pays = df_pays[df_pays["for_month"] == filter_period] if not df_pays.empty else pd.DataFrame()
        filtered_exps = df_exps[df_exps["expense_date"].astype(str).str.slice(0, 7) == filter_period] if not df_exps.empty else pd.DataFrame()
    else:
        filtered_pays = df_pays
        filtered_exps = df_exps

    total_in = filtered_pays["amount"].sum() if not filtered_pays.empty and "amount" in filtered_pays.columns else 0.0
    total_out = filtered_exps["amount"].sum() if not filtered_exps.empty and "amount" in filtered_exps.columns else 0.0
    net_balance = total_in - total_out

    c_sum1, c_sum2, c_sum3 = st.columns(3)
    with c_sum1:
        st.markdown(f"""
            <div class="kpi-card success">
                <div class="kpi-title">📥 إجمالي المقبوضات ({filter_period})</div>
                <div class="kpi-value">{total_in:,.2f} د.أ</div>
            </div>
        """, unsafe_allow_html=True)
    with c_sum2:
        st.markdown(f"""
            <div class="kpi-card danger">
                <div class="kpi-title">📤 إجمالي المصروفات ({filter_period})</div>
                <div class="kpi-value">{total_out:,.2f} د.أ</div>
            </div>
        """, unsafe_allow_html=True)
    with c_sum3:
        n_cls = "info" if net_balance >= 0 else "warning"
        st.markdown(f"""
            <div class="kpi-card {n_cls}">
                <div class="kpi-title">⚖️ صافي الفارق / المتبقي</div>
                <div class="kpi-value">{net_balance:,.2f} د.أ</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### 📥 تصدير كشوفات البيانات إلى Excel / CSV")
    col_exp1, col_exp2 = st.columns(2)

    with col_exp1:
        if not filtered_pays.empty:
            excel_pays = create_excel_download(filtered_pays, "payments.xlsx")
            csv_pays = filtered_pays.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')

            st.download_button(
                label="📊 تحميل كشف المقبوضات (Excel)",
                data=excel_pays,
                file_name=f"مقبوضات_صندوق_العمارة_{filter_period}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.download_button(
                label="📄 تحميل كشف المقبوضات (CSV)",
                data=csv_pays,
                file_name=f"مقبوضات_صندوق_العمارة_{filter_period}.csv",
                mime="text/csv"
            )

    with col_exp2:
        if not filtered_exps.empty:
            excel_exps = create_excel_download(filtered_exps, "expenses.xlsx")
            csv_exps = filtered_exps.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')

            st.download_button(
                label="📊 تحميل كشف المصروفات (Excel)",
                data=excel_exps,
                file_name=f"مصروفات_صندوق_العمارة_{filter_period}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.download_button(
                label="📄 تحميل كشف المصروفات (CSV)",
                data=csv_exps,
                file_name=f"مصروفات_صندوق_العمارة_{filter_period}.csv",
                mime="text/csv"
            )

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### 📱 مولّد التقرير الشهري الجاهز للنشر في جروب واتساب العمارة")
    st.markdown("ينشئ نصاً منسقاً واحترافياً يوضح الرصيد الافتتاحي، المقبوضات، تفاصيل المصاريف، والرصيد المتبقي بلمسة واحدة.")

    report_month = filter_period if filter_period != "جميع الفترات (كشف كامل)" else date.today().strftime("%Y-%m")

    exp_details_str = ""
    if not filtered_exps.empty and "category" in filtered_exps.columns:
        for idx, row in filtered_exps.iterrows():
            cat = row.get("category", "مصروف")
            amt = float(row.get("amount", 0.0))
            desc = row.get("description", "")
            exp_details_str += f"▫️ {cat}: {amt:g} د.أ ({desc})\n"
    else:
        exp_details_str = "▫️ لا توجد مصروفات مسجلة خلال هذا الشهر.\n"

    wa_group_report = (
        f"🏛️ *التقرير المالي الشهري لصندوق العمارة السكنية*\n"
        f"🗓️ *عن شهر:* {get_arabic_month_name(report_month)}\n"
        f"إشراف: المهندس أبو عادل\n"
        f"---------------------------------\n"
        f"💰 *الملخص المالي:* \n"
        f"▪️ إجمالي التحصيلات والمقبوضات: {total_in:,.2f} دينار\n"
        f"▪️ إجمالي المصروفات والصيانة: {total_out:,.2f} دينار\n"
        f"---------------------------------\n"
        f"🔹 *الرصيد الصافي المتبقي بالصندوق:* {net_balance:,.2f} دينار\n\n"
        f"📋 *تفاصيل البنود والمصروفات:* \n"
        f"{exp_details_str}\n"
        f"أتقدم بجزيل الشكر لكافة الجيران الأفاضل الملتزمين بالسداد في الموعد المحدد لضمان جودة الخدمات واستمرار الصيانة.\n"
        f"مع خالص التحية، لجنة العمارة - المهندس أبو عادل 🌸"
    )

    st.text_area("انسخ النص أدناه وانشره مباشرة في مجموعات الواتساب:", value=wa_group_report, height=250)

    st.markdown("<br><hr>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # RESET / WIPE DATABASE SECTION (تفريغ وتصفير البيانات)
    # ---------------------------------------------------------
    st.markdown("### 🧹 أدوات إدارة الصندوق وإعادة التهيئة")
    with st.expander("⚠️ تصفير وتفريغ بيانات الصندوق للبدء بسجلات جديدة"):
        st.warning("⚠️ **تحذير:** عملية التصفير تقوم بتفريغ كافة المقبوضات والمصروفات المسجلة للبدء بسجل جديد خالٍ من البيانات الافتراضية.")
        
        reset_option = st.radio(
            "اختر مستوى التصفير المطلوب:",
            [
                "تفريغ المقبوضات والمصروفات فقط (مع الإبقاء على قائمة الشقق والسكان)",
                "تفريغ شامل وجذري (تصفير المقبوضات والمصروفات + حذف جميع الشقق للسماح بإدخالها من جديد)"
            ]
        )

        confirm_reset = st.checkbox("أنا متأكد من رغبتي في تصفير وتفريغ قاعدة البيانات")

        if st.button("🚨 تنفيذ تصفير وتفريغ قاعدة البيانات الآن"):
            if confirm_reset:
                wipe_apts = ("تفريغ شامل" in reset_option)
                db_engine.clear_all_data(clear_apartments=wipe_apts)
                st.experimental_rerun() if hasattr(st, 'experimental_rerun') else st.rerun()
            else:
                st.error("يرجى وضع علامة صح على مربع التأكيد قبل الضغط على زر التصفير.")

# ---------------------------------------------------------
# MAIN APP ENTRY POINT & SIDEBAR NAVIGATION
# ---------------------------------------------------------
def main():
    inject_custom_css()

    # Check Authentication First
    if not st.session_state.get("authenticated", False):
        render_login_screen()
        return

    # Initialize Firestore Database
    db_client, db_status_msg = init_firestore()
    db_engine = BuildingFundDB(db_client)

    # Sidebar Header & Branding
    st.sidebar.markdown("""
        <div style="text-align:center; padding:10px 0;">
            <h2 style="color:#ffffff; margin:0; font-size:1.4rem;">🏛️ صندوق العمارة</h2>
            <p style="color:#94a3b8; margin:2px 0 0 0; font-size:0.85rem;">إشراف المهندس أبو عادل</p>
        </div>
        <hr style="border-color:#334155; margin:10px 0 15px 0;">
    """, unsafe_allow_html=True)

    st.sidebar.markdown("👤 **المستخدم الحالي:** المهندس أبو عادل")
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state["authenticated"] = False
        st.experimental_rerun() if hasattr(st, 'experimental_rerun') else st.rerun()

    st.sidebar.markdown("<hr style='border-color:#334155; margin:15px 0;'>", unsafe_allow_html=True)

    # Navigation Menu
    menu_choice = st.sidebar.radio(
        "القائمة الرئيسية:",
        [
            "📊 لوحة المؤشرات والقيادة",
            "🧾 تسجيل مقبوضات (سند قبض)",
            "💸 تسجيل مصاريف (سند صرف)",
            "🏢 دليل الشقق والسكان",
            "📈 كشوفات الحساب والتقارير"
        ]
    )

    st.sidebar.markdown("<hr style='border-color:#334155; margin:20px 0;'>", unsafe_allow_html=True)

    # Connection Status Indicator in Sidebar
    st.sidebar.markdown("##### 🔌 حالة قاعدة البيانات:")
    if db_engine.use_firestore:
        st.sidebar.success("متصل مباشر بـ Cloud Firestore 🟢")
    else:
        st.sidebar.warning("الوضع التجريبي (Demo Mode) 🟡")
        st.sidebar.caption("للاتصال بـ Firestore الحقيقي، يرجى إضافة مفاتيح الاعتماد في Streamlit Secrets.")

    # Render Active Page based on menu choice
    if menu_choice == "📊 لوحة المؤشرات والقيادة":
        render_dashboard_page(db_engine)
    elif menu_choice == "🧾 تسجيل مقبوضات (سند قبض)":
        render_payment_page(db_engine)
    elif menu_choice == "💸 تسجيل مصاريف (سند صرف)":
        render_expense_page(db_engine)
    elif menu_choice == "🏢 دليل الشقق والسكان":
        render_apartments_page(db_engine)
    elif menu_choice == "📈 كشوفات الحساب والتقارير":
        render_reports_page(db_engine)

if __name__ == "__main__":
    main()
