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
            else:
                secrets_found = False
                try:
                    # 2. Try firebase_json in Secrets (Raw JSON string)
                    if "firebase_json" in st.secrets:
                        raw_json = st.secrets["firebase_json"]
                        cred_dict = json.loads(raw_json) if isinstance(raw_json, str) else dict(raw_json)
                        cred = credentials.Certificate(cred_dict)
                        firebase_admin.initialize_app(cred)
                        secrets_found = True
                    # 3. Try dict in Secrets [firebase]
                    elif "firebase" in st.secrets:
                        cred_dict = dict(st.secrets["firebase"])
                        if "private_key" in cred_dict:
                            cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
                        cred = credentials.Certificate(cred_dict)
                        firebase_admin.initialize_app(cred)
                        secrets_found = True
                    elif "gcp_service_account" in st.secrets:
                        cred_dict = dict(st.secrets["gcp_service_account"])
                        cred = credentials.Certificate(cred_dict)
                        firebase_admin.initialize_app(cred)
                        secrets_found = True
                except Exception:
                    pass

                if not secrets_found:
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
    try:
        if "APP_PASSWORD" in st.secrets:
            return str(st.secrets["APP_PASSWORD"])
    except Exception:
        pass
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
            apt_map = {f"شقة {r['apt_no']} - {r['resident_name']}": r.to_dict() for _, r in df_apts.iterrows()}
            
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
# ---------------------------------------------------------
# PAGE 5: Financial Reports, Exports & Transparency (الكشوفات والتقارير)
# ---------------------------------------------------------
def render_reports_page(db_engine: BuildingFundDB):
    st.markdown("## 📈 مركز الكشوفات والتقارير المالية والشفافية")
    st.markdown("كشوفات تفصيلية للمقبوضات، المصروفات، كشف حساب ساكن محدد، ميزان المراجعة، وحصر الذمم والمتأخرات.")
    st.markdown("---")

    apartments = db_engine.get_apartments()
    payments = db_engine.get_payments()
    expenses = db_engine.get_expenses()

    df_apts = pd.DataFrame(apartments) if apartments else pd.DataFrame()
    df_pays = pd.DataFrame(payments) if payments else pd.DataFrame()
    df_exps = pd.DataFrame(expenses) if expenses else pd.DataFrame()

    # Pre-process columns
    if not df_pays.empty and "amount" in df_pays.columns:
        df_pays["amount"] = pd.to_numeric(df_pays["amount"], errors="coerce").fillna(0.0)
    if not df_exps.empty and "amount" in df_exps.columns:
        df_exps["amount"] = pd.to_numeric(df_exps["amount"], errors="coerce").fillna(0.0)
    if not df_apts.empty and "monthly_fee" in df_apts.columns:
        df_apts["monthly_fee"] = pd.to_numeric(df_apts["monthly_fee"], errors="coerce").fillna(25.0)

    # Top Information Banner to clearly outline all requested financial statements
    st.markdown("""
        <div style="background:#f8fafc; border:1px solid #cbd5e1; border-right:5px solid #2563eb; padding:12px 18px; border-radius:10px; margin-bottom:18px;">
            <div style="font-weight:700; color:#1e293b; font-size:1.05rem; margin-bottom:4px;">
                📑 خيارات كشوفات الحساب والتقارير المالية المتاحة:
            </div>
            <div style="color:#475569; font-size:0.9rem; line-height:1.8;">
                • <b>كشف المدفوعات (المقبوضات):</b> رصد المقبوضات حسب الفترة، طريقة الدفع، أو الشقة مع تحليل بياني وتصدير إكسل.<br>
                • <b>كشف المصروفات (النفقات والصيانة):</b> تفريغ كامل لجميع مصاريف العمارة حسب البند والفترة والفواتير وتصدير إكسل.<br>
                • <b>مدفوعات من شخص معين:</b> كشف حساب تفصيلي لشقة أو ساكن محدد (المدفوع والمتأخر وسندات القبض وإرسال واتساب).<br>
                • <b>خيارات كشوفات أخرى:</b> ميزان المراجعة والتدفق المالي، كشف ذمم الشقق، ومولّد تقرير واتساب الشهري العام.
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 6 Specialized Reporting Tabs
    tab_payments, tab_expenses, tab_resident, tab_balance, tab_aging, tab_other = st.tabs([
        "📥 كشف المدفوعات (المقبوضات)",
        "📤 كشف المصروفات (النفقات والصيانة)",
        "👤 مدفوعات من شخص معين (كشف حساب ساكن)",
        "⚖️ ميزان المراجعة والتدفق المالي",
        "⚠️ كشف الذمم والمتأخرات",
        "📱 كشوفات وتقارير أخرى"
    ])
    # ---------------------------------------------------------
    # TAB 2: كشف المقبوضات التفصيلي (مدفوعات)
    # ---------------------------------------------------------
    with tab_payments:
        st.markdown("### 📥 كشف المقبوضات والتحصيلات الشامل")
        st.caption("فلترة مقبوضات الصندوق حسب الفترة، طريقة الدفع، أو رقم الشقة مع إمكانية التصدير والتحليل.")

        if df_pays.empty:
            st.info("لا توجد مقبوضات مسجلة في الصندوق حتى الآن.")
        else:
            col_pf1, col_pf2, col_pf3, col_pf4 = st.columns(4)
            with col_pf1:
                pay_months_opts = ["جميع الأشهر"] + sorted(list(set(df_pays["for_month"].dropna().astype(str).tolist())), reverse=True)
                sel_pay_month = st.selectbox("📅 فلترة بالشهر المستحق:", pay_months_opts, key="pay_filter_month")
            with col_pf2:
                pay_methods_opts = ["جميع طرق الدفع"] + sorted(list(set(df_pays["payment_method"].dropna().astype(str).tolist()))) if "payment_method" in df_pays.columns else ["جميع طرق الدفع"]
                sel_pay_method = st.selectbox("💳 فلترة بطريقة الدفع:", pay_methods_opts, key="pay_filter_method")
            with col_pf3:
                apt_filter_opts = ["جميع الشقق"] + sorted(list(set(df_pays["apt_no"].dropna().astype(str).tolist()))) if "apt_no" in df_pays.columns else ["جميع الشقق"]
                sel_pay_apt = st.selectbox("🏢 فلترة برقم الشقة:", apt_filter_opts, key="pay_filter_apt")
            with col_pf4:
                search_pay_kw = st.text_input("🔍 بحث نصي (اسم / إيصال):", key="pay_filter_search")

            # Apply filters
            filtered_p = df_pays.copy()
            if sel_pay_month != "جميع الأشهر" and "for_month" in filtered_p.columns:
                filtered_p = filtered_p[filtered_p["for_month"].astype(str) == sel_pay_month]
            if sel_pay_method != "جميع طرق الدفع" and "payment_method" in filtered_p.columns:
                filtered_p = filtered_p[filtered_p["payment_method"].astype(str) == sel_pay_method]
            if sel_pay_apt != "جميع الشقق" and "apt_no" in filtered_p.columns:
                filtered_p = filtered_p[filtered_p["apt_no"].astype(str) == sel_pay_apt]
            if search_pay_kw:
                mask_p = (
                    filtered_p["resident_name"].astype(str).str.contains(search_pay_kw, case=False, na=False) |
                    filtered_p["receipt_no"].astype(str).str.contains(search_pay_kw, case=False, na=False) |
                    filtered_p["notes"].astype(str).str.contains(search_pay_kw, case=False, na=False)
                )
                filtered_p = filtered_p[mask_p]

            tot_filt_p = filtered_p["amount"].sum() if not filtered_p.empty else 0.0
            count_filt_p = len(filtered_p)
            avg_filt_p = (tot_filt_p / count_filt_p) if count_filt_p > 0 else 0.0

            # Summary Cards
            pk1, pk2, pk3 = st.columns(3)
            with pk1:
                st.markdown(f"""
                    <div class="kpi-card success">
                        <div class="kpi-title">📥 إجمالي المقبوضات المعروضة</div>
                        <div class="kpi-value">{tot_filt_p:,.2f} د.أ</div>
                        <div class="kpi-sub">{count_filt_p} حركة استلام</div>
                    </div>
                """, unsafe_allow_html=True)
            with pk2:
                st.markdown(f"""
                    <div class="kpi-card info">
                        <div class="kpi-title">📊 متوسط قيمة الدفعة</div>
                        <div class="kpi-value">{avg_filt_p:,.2f} د.أ</div>
                        <div class="kpi-sub">معدل التحصيل لكل سند</div>
                    </div>
                """, unsafe_allow_html=True)
            with pk3:
                st.markdown(f"""
                    <div class="kpi-card warning">
                        <div class="kpi-title">🧾 عدد السندات المصدرة</div>
                        <div class="kpi-value">{count_filt_p}</div>
                        <div class="kpi-sub">إيصال قبض مسجل</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Table display
            cols_p_show = ["payment_date", "receipt_no", "apt_no", "resident_name", "for_month", "amount", "payment_method", "notes"]
            p_exist = [c for c in cols_p_show if c in filtered_p.columns]
            df_disp_p = filtered_p[p_exist].copy().rename(columns={
                "payment_date": "تاريخ الاستلام",
                "receipt_no": "رقم السند",
                "apt_no": "الشقة",
                "resident_name": "اسم الساكن",
                "for_month": "عن شهر",
                "amount": "المبلغ (د.أ)",
                "payment_method": "طريقة الدفع",
                "notes": "الملاحظات"
            })
            st.dataframe(df_disp_p, use_container_width=True, hide_index=True)

            # Payment Breakdown by Method Chart
            if not filtered_p.empty and "payment_method" in filtered_p.columns:
                c_p_chart, c_p_dl = st.columns([2, 1])
                with c_p_chart:
                    fig_pm = px.pie(
                        filtered_p,
                        names="payment_method",
                        values="amount",
                        title="توزيع المقبوضات حسب طريقة الدفع",
                        color_discrete_sequence=["#10b981", "#3b82f6", "#f59e0b"]
                    )
                    fig_pm.update_layout(font=dict(family="Tajawal, sans-serif"))
                    st.plotly_chart(fig_pm, use_container_width=True)

                with c_p_dl:
                    st.markdown("##### 📥 تصدير كشف المقبوضات:")
                    excel_all_p = create_excel_download(df_disp_p, "كشف_المقبوضات.xlsx")
                    st.download_button(
                        label="📊 تحميل كشف المقبوضات (Excel)",
                        data=excel_all_p,
                        file_name="كشف_المقبوضات_المفلتر.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="dl_all_p_excel"
                    )
                    csv_all_p = df_disp_p.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                    st.download_button(
                        label="📄 تحميل كشف المقبوضات (CSV)",
                        data=csv_all_p,
                        file_name="كشف_المقبوضات_المفلتر.csv",
                        mime="text/csv",
                        key="dl_all_p_csv"
                    )

    # ---------------------------------------------------------
    # TAB 3: كشف المصروفات والصيانة (مصروفات)
    # ---------------------------------------------------------
    with tab_expenses:
        st.markdown("### 📤 كشف المصروفات والصيانة والفواتير")
        st.caption("فلترة كافة مصاريف العمارة وصيانة المرافق حسب البند، التاريخ، أو الجهة المستلمة.")

        if df_exps.empty:
            st.info("لا توجد مصروفات مسجلة في الصندوق حتى الآن.")
        else:
            col_ef1, col_ef2, col_ef3 = st.columns(3)
            with col_ef1:
                df_exps["exp_ym"] = df_exps["expense_date"].astype(str).str.slice(0, 7) if "expense_date" in df_exps.columns else ""
                exp_month_opts = ["جميع الفترات"] + sorted(list(set(df_exps["exp_ym"].dropna().tolist())), reverse=True)
                sel_exp_month = st.selectbox("📅 فلترة بالشهر:", exp_month_opts, key="exp_filter_month")
            with col_ef2:
                cat_opts = ["جميع البنود والتصنيفات"] + sorted(list(set(df_exps["category"].dropna().astype(str).tolist()))) if "category" in df_exps.columns else ["جميع البنود والتصنيفات"]
                sel_exp_cat = st.selectbox("🏷️ فلترة بالبند / التصنيف:", cat_opts, key="exp_filter_cat")
            with col_ef3:
                search_exp_kw = st.text_input("🔍 بحث (الجهة / التفاصيل / الفاتورة):", key="exp_filter_search")

            # Apply filters
            filtered_e = df_exps.copy()
            if sel_exp_month != "جميع الفترات":
                filtered_e = filtered_e[filtered_e["exp_ym"] == sel_exp_month]
            if sel_exp_cat != "جميع البنود والتصنيفات":
                filtered_e = filtered_e[filtered_e["category"].astype(str) == sel_exp_cat]
            if search_exp_kw:
                mask_e = (
                    filtered_e["paid_to"].astype(str).str.contains(search_exp_kw, case=False, na=False) |
                    filtered_e["description"].astype(str).str.contains(search_exp_kw, case=False, na=False) |
                    filtered_e["invoice_ref"].astype(str).str.contains(search_exp_kw, case=False, na=False)
                )
                filtered_e = filtered_e[mask_e]

            tot_filt_e = filtered_e["amount"].sum() if not filtered_e.empty else 0.0
            count_filt_e = len(filtered_e)
            top_cat = filtered_e.groupby("category")["amount"].sum().idxmax() if not filtered_e.empty and "category" in filtered_e.columns else "لا يوجد"

            ek1, ek2, ek3 = st.columns(3)
            with ek1:
                st.markdown(f"""
                    <div class="kpi-card danger">
                        <div class="kpi-title">📤 إجمالي المصروفات المعروضة</div>
                        <div class="kpi-value">{tot_filt_e:,.2f} د.أ</div>
                        <div class="kpi-sub">{count_filt_e} حركة صرف</div>
                    </div>
                """, unsafe_allow_html=True)
            with ek2:
                st.markdown(f"""
                    <div class="kpi-card info">
                        <div class="kpi-title">📑 عدد سندات الصرف</div>
                        <div class="kpi-value">{count_filt_e}</div>
                        <div class="kpi-sub">فاتورة وسند مسجل</div>
                    </div>
                """, unsafe_allow_html=True)
            with ek3:
                st.markdown(f"""
                    <div class="kpi-card warning">
                        <div class="kpi-title">🏆 أعلى بند إنفاق</div>
                        <div class="kpi-value" style="font-size:1.3rem;">{top_cat}</div>
                        <div class="kpi-sub">البند الأكثر استهلاكاً</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Table display
            cols_e_show = ["expense_date", "category", "amount", "paid_to", "description", "invoice_ref"]
            e_exist = [c for c in cols_e_show if c in filtered_e.columns]
            df_disp_e = filtered_e[e_exist].copy().rename(columns={
                "expense_date": "تاريخ الصرف",
                "category": "البند / التصنيف",
                "amount": "المبلغ (د.أ)",
                "paid_to": "الجهة المستلمة",
                "description": "تفاصيل العمل / العطل",
                "invoice_ref": "رقم الفاتورة / السند"
            })
            st.dataframe(df_disp_e, use_container_width=True, hide_index=True)

            # Expense Breakdown Chart
            if not filtered_e.empty and "category" in filtered_e.columns:
                c_e_chart, c_e_dl = st.columns([2, 1])
                with c_e_chart:
                    cat_summary = filtered_e.groupby("category")["amount"].sum().reset_index()
                    fig_ecat = px.pie(
                        cat_summary,
                        names="category",
                        values="amount",
                        hole=0.4,
                        title="توزيع المصروفات حسب التصنيف والبند",
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    fig_ecat.update_layout(font=dict(family="Tajawal, sans-serif"))
                    st.plotly_chart(fig_ecat, use_container_width=True)

                with c_e_dl:
                    st.markdown("##### 📥 تصدير كشف المصروفات:")
                    excel_all_e = create_excel_download(df_disp_e, "كشف_المصروفات.xlsx")
                    st.download_button(
                        label="📊 تحميل كشف المصروفات (Excel)",
                        data=excel_all_e,
                        file_name="كشف_المصروفات_المفلتر.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="dl_all_e_excel"
                    )
                    csv_all_e = df_disp_e.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                    st.download_button(
                        label="📄 تحميل كشف المصروفات (CSV)",
                        data=csv_all_e,
                        file_name="كشف_المصروفات_المفلتر.csv",
                        mime="text/csv",
                        key="dl_all_e_csv"
                    )

    # ---------------------------------------------------------
    # TAB 1: كشف حساب ساكن / شقة معينة (مدفوعات من شخص معين)
    # ---------------------------------------------------------
    with tab_resident:
        st.markdown("### 👤 كشف حساب تفصيلي لشقة / ساكن معين")
        st.caption("عرض سجل المقبوضات الخاصة بساكن محدد، مراجعة الأشهر المسددة والمتأخرة، وتصدير كشف الحساب أو إرساله عبر واتساب.")

        if df_apts.empty:
            st.warning("⚠️ لا توجد شقق مسجلة في النظام لاستخراج كشف الحساب.")
        else:
            apt_map = {f"شقة {r['apt_no']} - {r['resident_name']}": r.to_dict() for _, r in df_apts.iterrows()}
            selected_label = st.selectbox("اختر الشقة أو الساكن المراد استخراج كشف حسابه:", list(apt_map.keys()), key="res_stmt_select")
            apt_info = apt_map[selected_label]
            apt_no = str(apt_info.get("apt_no", ""))
            resident_name = str(apt_info.get("resident_name", ""))
            resident_phone = str(apt_info.get("phone", ""))
            monthly_fee = float(apt_info.get("monthly_fee", 25.0))
            resident_type = str(apt_info.get("resident_type", "مالك"))
            floor = str(apt_info.get("floor", ""))

            # Filter payments for this resident
            res_pays = df_pays[df_pays["apt_no"].astype(str) == apt_no].copy() if not df_pays.empty and "apt_no" in df_pays.columns else pd.DataFrame()
            
            total_paid_res = res_pays["amount"].sum() if not res_pays.empty else 0.0
            num_receipts = len(res_pays)
            paid_months = sorted(list(set(res_pays["for_month"].dropna().astype(str).tolist()))) if not res_pays.empty and "for_month" in res_pays.columns else []

            # Determine all relevant building months
            all_bld_months = sorted(list(set(df_pays["for_month"].dropna().astype(str).tolist() + [date.today().strftime("%Y-%m")])), reverse=True) if not df_pays.empty and "for_month" in df_pays.columns else [date.today().strftime("%Y-%m")]
            unpaid_months = [m for m in all_bld_months if m not in paid_months]
            estimated_dues = len(unpaid_months) * monthly_fee

            # KPI Cards for this resident
            rc1, rc2, rc3, rc4 = st.columns(4)
            with rc1:
                st.markdown(f"""
                    <div class="kpi-card info">
                        <div class="kpi-title">🏢 بيانات الشقة</div>
                        <div class="kpi-value" style="font-size:1.4rem;">شقة {apt_no}</div>
                        <div class="kpi-sub">{resident_name} ({resident_type})</div>
                    </div>
                """, unsafe_allow_html=True)
            with rc2:
                st.markdown(f"""
                    <div class="kpi-card success">
                        <div class="kpi-title">💵 إجمالي المدفوعات المستلمة</div>
                        <div class="kpi-value">{total_paid_res:,.2f} د.أ</div>
                        <div class="kpi-sub">من أصل {num_receipts} سندات قبض</div>
                    </div>
                """, unsafe_allow_html=True)
            with rc3:
                st.markdown(f"""
                    <div class="kpi-card warning">
                        <div class="kpi-title">📅 الاشتراك الشهري المقرر</div>
                        <div class="kpi-value">{monthly_fee:g} د.أ</div>
                        <div class="kpi-sub">{floor}</div>
                    </div>
                """, unsafe_allow_html=True)
            with rc4:
                d_color = "danger" if estimated_dues > 0 else "success"
                st.markdown(f"""
                    <div class="kpi-card {d_color}">
                        <div class="kpi-title">⚠️ المتأخرات المترتبة</div>
                        <div class="kpi-value">{estimated_dues:g} د.أ</div>
                        <div class="kpi-sub">{len(unpaid_months)} أشهر غير مسددة</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Month Status Summary
            col_pm, col_um = st.columns(2)
            with col_pm:
                st.markdown("##### ✅ الأشهر المسددة:")
                if paid_months:
                    st.write(" ، ".join([f"`{m}`" for m in paid_months]))
                else:
                    st.info("لا توجد أشهر مسددة مسجلة بعد.")

            with col_um:
                st.markdown("##### ⚠️ الأشهر المتأخرة / غير المسددة:")
                if unpaid_months:
                    st.write(" ، ".join([f"`{m}`" for m in unpaid_months]))
                else:
                    st.success("🎉 كافة الأشهر مسددة بالكامل حتى الآن!")

            st.markdown("<br>", unsafe_allow_html=True)

            # Detail Table
            st.markdown(f"##### 📋 سجل الدفعات وسندات القبض لشقة ({apt_no}) - {resident_name}:")
            if not res_pays.empty:
                cols_to_show = ["payment_date", "receipt_no", "for_month", "amount", "payment_method", "notes"]
                existing_cols = [c for c in cols_to_show if c in res_pays.columns]
                df_disp_res = res_pays[existing_cols].copy()
                col_rename = {
                    "payment_date": "تاريخ الاستلام",
                    "receipt_no": "رقم السند",
                    "for_month": "عن شهر",
                    "amount": "المبلغ (د.أ)",
                    "payment_method": "طريقة الدفع",
                    "notes": "الملاحظات"
                }
                df_disp_res = df_disp_res.rename(columns=col_rename)
                st.dataframe(df_disp_res, use_container_width=True, hide_index=True)

                # Export & WhatsApp
                c_act1, c_act2, c_act3 = st.columns([1.5, 1.5, 2.5])
                with c_act1:
                    excel_res = create_excel_download(df_disp_res, f"كشف_حساب_شقة_{apt_no}.xlsx")
                    st.download_button(
                        label="📊 تصدير كشف الحساب (Excel)",
                        data=excel_res,
                        file_name=f"كشف_حساب_شقة_{apt_no}_{resident_name}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="btn_dl_res_excel"
                    )
                with c_act2:
                    csv_res = df_disp_res.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                    st.download_button(
                        label="📄 تصدير كشف الحساب (CSV)",
                        data=csv_res,
                        file_name=f"كشف_حساب_شقة_{apt_no}_{resident_name}.csv",
                        mime="text/csv",
                        key="btn_dl_res_csv"
                    )
                with c_act3:
                    wa_res_text = (
                        f"مرحباً جارنا العزيز {resident_name} المحترم، تحية طيبة من لجنة العمارة (إشراف المهندس أبو عادل). 🌸\n\n"
                        f"📊 *كشف حساب اشتراك خدمات العمارة لشقة رقم ({apt_no}):*\n"
                        f"▪️ إجمالي المبالغ المسددة المستلمة: {total_paid_res:,.2f} دينار ({num_receipts} دفعات)\n"
                        f"▪️ الأشهر المسددة: {', '.join(paid_months) if paid_months else 'لا يوجد'}\n"
                    )
                    if unpaid_months:
                        wa_res_text += f"▪️ الأشهر المتبقية للاشتراك: {', '.join(unpaid_months)} بقيمة إجمالية ({estimated_dues:g} دينار)\n"
                    else:
                        wa_res_text += "▪️ الرصيد: مسدد بالكامل حتى تاريخه بارك الله بكم.\n"
                    wa_res_text += "\nشاكرين ومقدرين حسن تعاونكم الدائم وحرصكم على راحة وخدمات العمارة."
                    wa_res_url = generate_whatsapp_link(resident_phone, wa_res_text)
                    st.markdown(f"""
                        <a href="{wa_res_url}" target="_blank" class="whatsapp-link" style="width:100%; text-align:center;">
                            📱 إرسال كشف الحساب للساكن عبر واتساب
                        </a>
                    """, unsafe_allow_html=True)
            else:
                st.info(f"لا توجد أي سندات مقبوضات مسجلة لشقة ({apt_no}) حتى الآن.")

    # ---------------------------------------------------------
    # TAB 4: ميزان المراجعة والتدفق المالي (تقرير سنوي وشهري)
    # ---------------------------------------------------------
    with tab_balance:
        st.markdown("### ⚖️ ميزان المراجعة والتدفق المالي الشهري والسنوي")
        st.caption("مقارنة تحليلية دقيقة بين المقبوضات والمصروفات لكل شهر لمعرفة الفائض أو العجز المتراكم.")

        # Aggregate monthly
        all_months_set = set()
        if not df_pays.empty and "for_month" in df_pays.columns:
            all_months_set.update(df_pays["for_month"].dropna().astype(str).tolist())
        if not df_exps.empty and "expense_date" in df_exps.columns:
            all_months_set.update(df_exps["expense_date"].astype(str).str.slice(0, 7).dropna().tolist())
        all_months_set.add(date.today().strftime("%Y-%m"))

        months_list = sorted(list(all_months_set), reverse=True)

        tb_records = []
        for ym in sorted(list(all_months_set)):
            p_val = df_pays[df_pays["for_month"].astype(str) == ym]["amount"].sum() if not df_pays.empty and "for_month" in df_pays.columns else 0.0
            e_val = df_exps[df_exps["expense_date"].astype(str).str.slice(0, 7) == ym]["amount"].sum() if not df_exps.empty and "expense_date" in df_exps.columns else 0.0
            net_val = p_val - e_val
            tb_records.append({
                "الشهر": ym,
                "إجمالي المقبوضات (د.أ)": p_val,
                "إجمالي المصروفات (د.أ)": e_val,
                "الصافي / الفارق (د.أ)": net_val,
                "الحالة": "فائض 🟢" if net_val > 0 else ("عجز 🔴" if net_val < 0 else "متعادل ⚪")
            })

        df_tb = pd.DataFrame(tb_records)

        tot_in_all = df_tb["إجمالي المقبوضات (د.أ)"].sum() if not df_tb.empty else 0.0
        tot_out_all = df_tb["إجمالي المصروفات (د.أ)"].sum() if not df_tb.empty else 0.0
        cum_balance = tot_in_all - tot_out_all

        tb1, tb2, tb3 = st.columns(3)
        with tb1:
            st.markdown(f"""
                <div class="kpi-card success">
                    <div class="kpi-title">📥 إجمالي المقبوضات التراكمية</div>
                    <div class="kpi-value">{tot_in_all:,.2f} د.أ</div>
                </div>
            """, unsafe_allow_html=True)
        with tb2:
            st.markdown(f"""
                <div class="kpi-card danger">
                    <div class="kpi-title">📤 إجمالي المصروفات التراكمية</div>
                    <div class="kpi-value">{tot_out_all:,.2f} د.أ</div>
                </div>
            """, unsafe_allow_html=True)
        with tb3:
            bal_cls = "success" if cum_balance >= 0 else "danger"
            st.markdown(f"""
                <div class="kpi-card {bal_cls}">
                    <div class="kpi-title">💵 الرصيد الصافي الفعلي في الصندوق</div>
                    <div class="kpi-value">{cum_balance:,.2f} د.أ</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if not df_tb.empty:
            st.dataframe(df_tb.sort_values(by="الشهر", ascending=False), use_container_width=True, hide_index=True)

            excel_tb = create_excel_download(df_tb, "ميزان_المراجعة.xlsx")
            st.download_button(
                label="📊 تحميل ميزان المراجعة كاملاً (Excel)",
                data=excel_tb,
                file_name="ميزان_المراجعة_والتدفق_المالي.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="btn_dl_tb"
            )

    # ---------------------------------------------------------
    # TAB 5: كشف الذمم والمتأخرات التراكمية (كشف ديون الشقق)
    # ---------------------------------------------------------
    with tab_aging:
        st.markdown("### ⚠️ كشف الذمم والمتأخرات التراكمية للشقق")
        st.caption("كشف شامل يرصد التزام كل شقة، حصر المبالغ المتأخرة، وإمكانية إرسال تذكيرات فورية عبر واتساب.")

        if df_apts.empty:
            st.info("لا توجد شقق مسجلة في النظام.")
        else:
            sel_aging_month = st.selectbox("📅 تقييم المتأخرات حتى شهر:", months_list, index=0, key="aging_eval_month")

            aging_records = []
            for _, apt in df_apts.iterrows():
                ano = str(apt.get("apt_no", ""))
                rname = str(apt.get("resident_name", ""))
                rphone = str(apt.get("phone", ""))
                mfee = float(apt.get("monthly_fee", 25.0))
                rtype = str(apt.get("resident_type", "مالك"))

                # Check payments for this apt
                apt_p = df_pays[df_pays["apt_no"].astype(str) == ano] if not df_pays.empty and "apt_no" in df_pays.columns else pd.DataFrame()
                p_months = set(apt_p["for_month"].dropna().astype(str).tolist()) if not apt_p.empty and "for_month" in apt_p.columns else set()

                is_paid_current = (sel_aging_month in p_months)
                
                # Check how many months unpaid up to selected month
                # Consider relevant months
                eval_unpaid = [m for m in months_list if m not in p_months and m <= sel_aging_month]
                total_due = len(eval_unpaid) * mfee

                aging_records.append({
                    "رقم الشقة": ano,
                    "اسم الساكن": rname,
                    "الصفة": rtype,
                    "رقم الهاتف": rphone,
                    "الاشتراك الشهري (د.أ)": mfee,
                    "حالة الشهر المحدد": "مسدد 🟢" if is_paid_current else "غير مسدد 🔴",
                    "عدد الأشهر المتأخرة": len(eval_unpaid),
                    "إجمالي الذمة المستحقة (د.أ)": total_due,
                    "الأشهر غير المسددة": " ، ".join(eval_unpaid) if eval_unpaid else "مسدد بالكامل"
                })

            df_aging = pd.DataFrame(aging_records)

            tot_aging_dues = df_aging["إجمالي الذمة المستحقة (د.أ)"].sum()
            unpaid_apts_count = len(df_aging[df_aging["عدد الأشهر المتأخرة"] > 0])
            fully_paid_count = len(df_aging) - unpaid_apts_count

            ak1, ak2, ak3 = st.columns(3)
            with ak1:
                st.markdown(f"""
                    <div class="kpi-card danger">
                        <div class="kpi-title">⚠️ إجمالي الذمم والمتأخرات غير المحصلة</div>
                        <div class="kpi-value">{tot_aging_dues:,.2f} د.أ</div>
                        <div class="kpi-sub">مستحقات واجبة التحصيل</div>
                    </div>
                """, unsafe_allow_html=True)
            with ak2:
                st.markdown(f"""
                    <div class="kpi-card warning">
                        <div class="kpi-title">🏢 عدد الشقق المتأخرة</div>
                        <div class="kpi-value">{unpaid_apts_count} شقق</div>
                        <div class="kpi-sub">من أصل {len(df_apts)} شقة</div>
                    </div>
                """, unsafe_allow_html=True)
            with ak3:
                st.markdown(f"""
                    <div class="kpi-card success">
                        <div class="kpi-title">✅ الشقق المسددة بالكامل</div>
                        <div class="kpi-value">{fully_paid_count} شقق</div>
                        <div class="kpi-sub">التزام تام بالسداد</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Display interactive list with action buttons
            st.markdown("##### 📋 جدول المتابعة ومطالبات الشقق:")
            for idx, a_row in df_aging.iterrows():
                c_ag1, c_ag2, c_ag3, c_ag4, c_ag5 = st.columns([1.2, 2.5, 1.5, 1.5, 2.5])
                with c_ag1:
                    st.markdown(f"**شقة {a_row['رقم الشقة']}**<br><small>{a_row['الصفة']}</small>", unsafe_allow_html=True)
                with c_ag2:
                    st.markdown(f"**{a_row['اسم الساكن']}**<br><small>{a_row['رقم الهاتف']}</small>", unsafe_allow_html=True)
                with c_ag3:
                    if a_row["عدد الأشهر المتأخرة"] == 0:
                        st.markdown("<span class='badge badge-success'>مسدد بالكامل 🟢</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span class='badge badge-danger'>متأخر ({a_row['عدد الأشهر المتأخرة']}) شهر</span>", unsafe_allow_html=True)
                with c_ag4:
                    st.markdown(f"**{a_row['إجمالي الذمة المستحقة (د.أ)']:g} د.أ**", unsafe_allow_html=True)
                with c_ag5:
                    if a_row["عدد الأشهر المتأخرة"] > 0:
                        wa_ag_msg = (
                            f"مرحباً جارنا العزيز {a_row['اسم الساكن']} المحترم، تحية طيبة من لجنة العمارة (إشراف المهندس أبو عادل). 🌸\n"
                            f"نود تذكيركم بلطف بوجود ذمة اشتراك خدمات عمارة مترتبة لشقة رقم ({a_row['رقم الشقة']}) بقيمة إجمالية ({a_row['إجمالي الذمة المستحقة (د.أ)']:g} دينار) "
                            f"عن الأشهر ({a_row['الأشهر غير المسددة']}).\n"
                            f"شاكرين ومقدرين حسن تعاونكم الدائم في الحفاظ على خدمات وصيانة العمارة."
                        )
                        wa_ag_url = generate_whatsapp_link(a_row["رقم الهاتف"], wa_ag_msg)
                        st.markdown(f"""
                            <a href="{wa_ag_url}" target="_blank" class="whatsapp-link" style="padding:5px 12px; font-size:0.83rem;">
                                📱 مطالبة عبر واتساب
                            </a>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("<small style='color:#10b981;'>لا توجد متأخرات 🌸</small>", unsafe_allow_html=True)
                st.markdown("<hr style='margin:6px 0; border-color:#f1f5f9;'>", unsafe_allow_html=True)

            # Export Aging Table
            st.markdown("<br>", unsafe_allow_html=True)
            excel_aging = create_excel_download(df_aging, "كشف_المتأخرات_والذمم.xlsx")
            st.download_button(
                label="📊 تحميل كشف المتأخرات والذمم كاملاً (Excel)",
                data=excel_aging,
                file_name=f"كشف_المتأخرات_حتى_شهر_{sel_aging_month}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="btn_dl_aging"
            )

    # ---------------------------------------------------------
    # TAB 6: تقرير الواتساب الشهري وإعادة التهيئة
    # ---------------------------------------------------------
    with tab_other:
        st.markdown("### 📱 مولّد التقرير الشهري الجاهز لجروب واتساب العمارة")
        st.caption("توليد نص مالي رسمي منسق وجاهز للنشر المباشر في مجموعة الجيران لتحقيق الشفافية المطلقة.")

        rep_month_sel = st.selectbox("📅 اختر شهر التقرير للنشر:", months_list, index=0, key="wa_rep_month_select")

        # Calculate month figures
        m_in = df_pays[df_pays["for_month"].astype(str) == rep_month_sel]["amount"].sum() if not df_pays.empty and "for_month" in df_pays.columns else 0.0
        m_out = df_exps[df_exps["expense_date"].astype(str).str.slice(0, 7) == rep_month_sel]["amount"].sum() if not df_exps.empty and "expense_date" in df_exps.columns else 0.0
        m_net = m_in - m_out

        exp_m_df = df_exps[df_exps["expense_date"].astype(str).str.slice(0, 7) == rep_month_sel] if not df_exps.empty and "expense_date" in df_exps.columns else pd.DataFrame()
        exp_details_str = ""
        if not exp_m_df.empty and "category" in exp_m_df.columns:
            for _, row in exp_m_df.iterrows():
                cat = row.get("category", "مصروف")
                amt = float(row.get("amount", 0.0))
                desc = row.get("description", "")
                exp_details_str += f"▫️ {cat}: {amt:g} د.أ ({desc})\n"
        else:
            exp_details_str = "▫️ لا توجد مصروفات مسجلة خلال هذا الشهر.\n"

        wa_group_report = (
            f"🏛️ *التقرير المالي الشهري لصندوق العمارة السكنية*\n"
            f"🗓️ *عن شهر:* {get_arabic_month_name(rep_month_sel)}\n"
            f"إشراف: المهندس أبو عادل\n"
            f"---------------------------------\n"
            f"💰 *الملخص المالي:* \n"
            f"▪️ إجمالي التحصيلات والمقبوضات: {m_in:,.2f} دينار\n"
            f"▪️ إجمالي المصروفات والصيانة: {m_out:,.2f} دينار\n"
            f"---------------------------------\n"
            f"🔹 *الرصيد الصافي المتبقي بالصندوق:* {m_net:,.2f} دينار\n\n"
            f"📋 *تفاصيل البنود والمصروفات:* \n"
            f"{exp_details_str}\n"
            f"أتقدم بجزيل الشكر لكافة الجيران الأفاضل الملتزمين بالسداد في الموعد المحدد لضمان جودة الخدمات واستمرار الصيانة.\n"
            f"مع خالص التحية، لجنة العمارة - المهندس أبو عادل 🌸"
        )

        st.text_area("انسخ النص أدناه وانشره مباشرة في مجموعات الواتساب:", value=wa_group_report, height=260)

        st.markdown("<br><hr>", unsafe_allow_html=True)

        # Database Reset Tool
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
