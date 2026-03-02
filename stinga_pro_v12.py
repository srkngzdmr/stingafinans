# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════╗
# ║ STINGA PRO v13.0 - ULTRA EDITION                           ║
# ║ Geliştiren: AI ile birlikte - Gemini 2.5 Flash Destekli   ║
# ╚══════════════════════════════════════════════════════════════╝
import streamlit as st
import pandas as pd
import google.generativeai as genai
from datetime import datetime, timedelta
import os
import json
import re
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PIL import Image
from fpdf import FPDF
import hashlib
import time
import random
import base64
from io import BytesIO

# ─── SAYFA YAPISI ─────────────────────────────────────────────
st.set_page_config(
    page_title="Stinga Pro v13 ⚡",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# ─── LOGO BASE64 ──────────────────────────────────────────────
import base64 as _b64

def _get_logo_b64():
    try:
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                return _b64.b64encode(f.read()).decode()
    except:
        pass
    return ""

# ─── AÇIK TEMA CSS ────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Bebas+Neue&family=JetBrains+Mono:wght@400;700&display=swap');

:root {
    --bg-primary:    #f0f4f8;
    --bg-secondary:  #ffffff;
    --bg-card:       #ffffff;
    --bg-hover:      #e8f4f0;
    --sidebar-bg:    #0f2240;
    --sidebar-card:  #1a3560;
    --sidebar-hover: #1e3d6e;
    --accent-green:  #1a9e6e;
    --accent-navy:   #2d4a8a;
    --accent-teal:   #0d7a5f;
    --accent-light:  #4cc9a0;
    --accent-orange: #e8a020;
    --accent-red:    #e05252;
    --text-primary:  #0f2240;
    --text-secondary:#2d4a6a;
    --text-muted:    #6b8caa;
    --text-sidebar:  #c8ddf0;
    --border:        #d0e4f0;
    --border-card:   #e0eeea;
    --shadow:        0 2px 12px rgba(15,34,64,0.08);
    --shadow-hover:  0 8px 30px rgba(26,158,110,0.15);
}

* { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif !important;
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

.stApp {
    background: var(--bg-primary) !important;
}

/* ── SİDEBAR ── */
[data-testid="stSidebar"] {
    background: var(--sidebar-bg) !important;
    border-right: none !important;
    box-shadow: 4px 0 20px rgba(0,0,0,0.15) !important;
}
[data-testid="stSidebar"] * {
    color: var(--text-sidebar) !important;
}
[data-testid="stSidebar"] .stRadio label {
    color: var(--text-sidebar) !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.1) !important;
}

/* ── KARTLAR ── */
.ultra-card {
    background: var(--bg-card);
    border: 1px solid var(--border-card);
    border-radius: 16px;
    padding: 24px;
    margin: 12px 0;
    box-shadow: var(--shadow);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}
.ultra-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent-green), var(--accent-navy));
    opacity: 0;
    transition: opacity 0.3s ease;
}
.ultra-card:hover::before { opacity: 1; }
.ultra-card:hover {
    box-shadow: var(--shadow-hover);
    transform: translateY(-2px);
    border-color: rgba(26,158,110,0.3);
}

.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border-card);
    border-radius: 20px;
    padding: 24px 16px;
    text-align: center;
    box-shadow: var(--shadow);
    transition: all 0.3s ease;
}
.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-hover);
    border-color: var(--accent-green);
}
.metric-value {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.5rem;
    color: var(--accent-green);
    line-height: 1.1;
    margin: 6px 0;
}
.metric-label {
    font-size: 0.7rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 600;
}

/* ── RİSK BADGELERİ ── */
.risk-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 700;
}
.risk-low  { background: #e6faf3; color: #1a9e6e; border: 1px solid #a8e6cf; }
.risk-mid  { background: #fff8e6; color: #b87800; border: 1px solid #ffd580; }
.risk-high { background: #fdeaea; color: #c0392b; border: 1px solid #f5b5b5; }

/* ── BUTONLAR ── */
.stButton > button {
    background: linear-gradient(135deg, var(--accent-green) 0%, var(--accent-teal) 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: 0.3px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 12px rgba(26,158,110,0.25) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(26,158,110,0.35) !important;
    background: linear-gradient(135deg, #20b880 0%, #0f8a6a 100%) !important;
}

/* ── SAYFA BAŞLIĞI ── */
.page-header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 28px;
    padding-bottom: 16px;
    border-bottom: 2px solid var(--border-card);
}
.page-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.6rem;
    letter-spacing: 3px;
    line-height: 1;
    color: var(--text-primary);
}

/* ── TABLO ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: var(--shadow) !important;
}

/* ── INPUT ── */
.stTextInput > div > div > input,
.stSelectbox > div > div > div,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-family: 'Space Grotesk', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent-green) !important;
    box-shadow: 0 0 0 3px rgba(26,158,110,0.1) !important;
}

/* ── TAB ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-secondary) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow) !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 8px !important;
    color: var(--text-muted) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
}
.stTabs [aria-selected="true"] {
    background: var(--accent-green) !important;
    color: white !important;
}

/* ── ALERT ── */
.stSuccess { background: #e6faf3 !important; border-left: 3px solid var(--accent-green) !important; color: #0f5132 !important; }
.stError   { background: #fdeaea !important; border-left: 3px solid #e05252 !important; color: #842029 !important; }
.stWarning { background: #fff8e6 !important; border-left: 3px solid #e8a020 !important; color: #664d00 !important; }
.stInfo    { background: #e8f4ff !important; border-left: 3px solid var(--accent-navy) !important; color: #0a3060 !important; }
.stProgress > div > div { background: linear-gradient(90deg, var(--accent-green), var(--accent-navy)) !important; }

/* ── SIDEBAR İÇİ KARTLAR ── */
.sidebar-card {
    background: var(--sidebar-card);
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 12px;
    border: 1px solid rgba(255,255,255,0.08);
}
.sidebar-card:hover { background: var(--sidebar-hover); }

/* ── STATUS PILL ── */
.status-pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.pill-approved { background: #e6faf3; color: #1a9e6e; }
.pill-pending  { background: #fff8e6; color: #b87800; }
.pill-rejected { background: #fdeaea; color: #c0392b; }

/* ── ANOMALİ ALERT ── */
.anomaly-alert {
    background: linear-gradient(135deg, #fdeaea, #fff0f0);
    border: 1px solid #f5b5b5;
    border-radius: 12px;
    padding: 16px;
    margin: 8px 0;
}

/* ── BÜTÇE BAR ── */
.budget-track {
    background: #e8f0f8;
    border-radius: 8px;
    height: 6px;
    overflow: hidden;
    margin: 6px 0;
}
.budget-fill {
    height: 100%;
    border-radius: 8px;
    transition: width 0.8s ease;
}

/* ── LEADERBOARD ── */
.lb-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-radius: 10px;
    margin: 6px 0;
    background: var(--bg-card);
    border: 1px solid var(--border-card);
    box-shadow: var(--shadow);
    transition: all 0.2s;
}
.lb-item:hover { border-color: var(--accent-green); box-shadow: var(--shadow-hover); }
.lb-rank { font-family: 'Bebas Neue'; font-size: 1.5rem; color: var(--text-muted); width: 30px; }
.lb-rank.gold   { color: #f0a500; }
.lb-rank.silver { color: #888; }
.lb-rank.bronze { color: #a06030; }

/* ── AI BUBBLE ── */
.ai-bubble {
    background: linear-gradient(135deg, #eefaf6, #e8f4ff);
    border: 1px solid rgba(26,158,110,0.25);
    border-radius: 12px;
    padding: 14px 18px;
    margin: 10px 0;
    position: relative;
    color: var(--text-primary);
}
.ai-bubble::before {
    content: '⚡ AI';
    position: absolute;
    top: -10px; left: 14px;
    background: linear-gradient(135deg, var(--accent-green), var(--accent-navy));
    color: white;
    font-size: 0.62rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 10px;
    letter-spacing: 1px;
}

/* ── EMPTY STATE ── */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: var(--text-muted);
}
.empty-icon { font-size: 3rem; margin-bottom: 12px; opacity: 0.5; }

/* ── FEED ITEM ── */
.feed-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 10px 0;
    border-bottom: 1px solid var(--border);
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-green); }

/* ── ANİMASYON ── */
@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-8px); }
}
@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 8px rgba(26,158,110,0.2); }
    50% { box-shadow: 0 0 20px rgba(26,158,110,0.5); }
}
.floating { animation: float 4s ease-in-out infinite; }
.pulsing  { animation: pulse-glow 2s ease-in-out infinite; }

hr { border-color: var(--border) !important; }
</style>
""", unsafe_allow_html=True)

# ─── KULLANICI SİSTEMİ ────────────────────────────────────────
# YETKİ YAPISI:
#   admin   → tüm verileri görür + onaylayabilir (Serkan, Zeynep)
#   user    → sadece kendi fişlerini görür, onaylayamaz (Okan, Şenol)

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

USERS = {
    "zeynep": {
        "name": "Zeynep",
        "password": hash_password("789"),
        "role": "admin",       # ← onay yetkisi VAR, tüm verileri görür
        "avatar": "👑",
        "department": "Yönetim Kurulu",
        "monthly_limit": 50000,
        "xp": 1250
    },
    "serkan": {
        "name": "Serkan",
        "password": hash_password("123"),
        "role": "admin",       # ← onay yetkisi VAR, tüm verileri görür
        "avatar": "⚡",
        "department": "İşletme Müdürü",
        "monthly_limit": 25000,
        "xp": 890
    },
    "okan": {
        "name": "Okan",
        "password": hash_password("321"),
        "role": "user",        # ← sadece kendi fişlerini görür
        "avatar": "🔧",
        "department": "Saha Personeli",
        "monthly_limit": 5000,
        "xp": 430
    },
    "senol": {
        "name": "Şenol",
        "password": hash_password("456"),
        "role": "user",        # ← sadece kendi fişlerini görür
        "avatar": "🏢",
        "department": "Genel Müdür",
        "monthly_limit": 30000,
        "xp": 600
    },
}

# ─── SESSION STATE ────────────────────────────────────────────
defaults = {
    'authenticated': False,
    'user_info': None,
    'current_key_idx': 0,
    'chat_history': [],
    'dark_mode': True,
    'last_ai_insight': None,
    'tour_done': False,
    'realtime_alerts': [],
    'selected_page': '🏠 Dashboard'
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── API ──────────────────────────────────────────────────────
API_KEYS = [
    "AIzaSyDVP0ki4yOaEKq1B_kEmMR8M0vuDeEpVsY",
    "AIzaSyCyJNBT-3-K1P_Ylebj4rCSzqwOkF31KLg"
]

def configure_ai():
    try:
        k = API_KEYS[st.session_state.current_key_idx]
        genai.configure(api_key=k)
        return genai.GenerativeModel('models/gemini-2.5-flash')
    except Exception as e:
        st.error(f"AI Hatası: {e}")
        return None

# ─── VERİTABANI ───────────────────────────────────────────────
DB_FILE = "stinga_v13_db.json"

def init_db():
    if not os.path.exists(DB_FILE):
        data = {
            "expenses": [],
            "wallets": {"Zeynep": 50000, "Serkan": 25000, "Okan": 5000, "Şenol": 30000},
            "ledger": [],
            "notifications": [],
            "budgets": {
                "Maden Sahası":  {"limit": 100000, "spent": 0},
                "Aktif Karbon":  {"limit": 80000,  "spent": 0},
                "Enerji Hatları":{"limit": 60000,  "spent": 0},
                "Genel Merkez":  {"limit": 40000,  "spent": 0}
            },
            "ai_insights": [],
            "mood_log": [],
            "badges": {"Zeynep": [], "Serkan": [], "Okan": [], "Şenol": []},
            "xp": {"Zeynep": 1250, "Serkan": 890, "Okan": 430, "Şenol": 600}
        }
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    else:
        d = load_data()
        changed = False
        for field in ["budgets", "ai_insights", "mood_log", "badges", "xp", "notifications"]:
            if field not in d:
                d[field] = {} if field in ["budgets","badges","xp"] else []
                changed = True
        # Şenol için wallet yoksa ekle
        if "Şenol" not in d.get("wallets", {}):
            d["wallets"]["Şenol"] = 30000
            changed = True
        if "Şenol" not in d.get("xp", {}):
            d["xp"]["Şenol"] = 600
            changed = True
        if changed:
            save_data(d)

def load_data():
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(d):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=4)

def add_notify(target, message, notif_type="info"):
    d = load_data()
    d["notifications"].append({
        "user": target,
        "msg": message,
        "type": notif_type,
        "time": datetime.now().strftime("%H:%M"),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "read": False
    })
    save_data(d)

def add_xp(user_name, amount, reason=""):
    d = load_data()
    if "xp" not in d:
        d["xp"] = {}
    d["xp"][user_name] = d["xp"].get(user_name, 0) + amount
    if reason:
        d["notifications"].append({
            "user": user_name,
            "msg": f"🏆 +{amount} XP kazandın! ({reason})",
            "type": "xp",
            "time": datetime.now().strftime("%H:%M"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "read": False
        })
    save_data(d)

# ─── YARDIMCI ─────────────────────────────────────────────────
def extract_json(text):
    try:
        text = text.replace("```json", "").replace("```", "").strip()
        m = re.search(r'\{.*\}', text, re.DOTALL)
        return json.loads(m.group()) if m else json.loads(text)
    except:
        return None

def tr_fix(text):
    if not isinstance(text, str): return str(text)
    chars = {"İ":"I","ı":"i","Ş":"S","ş":"s","Ğ":"G","ğ":"g","Ç":"C","ç":"c","Ö":"O","ö":"o","Ü":"U","ü":"u"}
    for t, e in chars.items(): text = text.replace(t, e)
    return text

def get_risk_html(score):
    try:
        score = int(score)
    except:
        score = 0
    if score < 30:
        return f'<span class="risk-badge risk-low">✓ {score}% DÜŞÜK</span>'
    elif score < 70:
        return f'<span class="risk-badge risk-mid">⚠ {score}% ORTA</span>'
    else:
        return f'<span class="risk-badge risk-high">🔴 {score}% KRİTİK</span>'

def get_status_html(status):
    mapping = {
        "Onaylandı":     ("pill-approved", "✓ ONAYLANDI"),
        "Onay Bekliyor": ("pill-pending",  "⏳ BEKLİYOR"),
        "Reddedildi":    ("pill-rejected", "✗ REDDEDİLDİ")
    }
    cls, label = mapping.get(status, ("pill-pending", status))
    return f'<span class="status-pill {cls}">{label}</span>'

def export_pdf_advanced(df_export, title="Mali Rapor", ay_bilgisi="Tüm Zamanlar"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(5, 8, 16)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 15, "", ln=True)
    pdf.cell(190, 10, tr_fix(f"STINGA - {title.upper()} ({ay_bilgisi})"), align='C', ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(120, 160, 200)
    pdf.cell(190, 8, tr_fix(f"Uretim: {datetime.now().strftime('%d.%m.%Y %H:%M')} | Stinga Pro v13"), align='C', ln=True)
    pdf.ln(12)
    if df_export.empty:
        pdf.set_text_color(100, 100, 100)
        pdf.set_font("Arial", "", 11)
        pdf.cell(190, 10, tr_fix("Bu doneme ait veri bulunmamaktadir."), ln=True)
        return bytes(pdf.output())
    total    = df_export['Tutar'].sum() if 'Tutar' in df_export.columns else 0
    approved = df_export[df_export['Durum']=='Onaylandı']['Tutar'].sum() if 'Durum' in df_export.columns else 0
    pending  = df_export[df_export['Durum']=='Onay Bekliyor']['Tutar'].sum() if 'Durum' in df_export.columns else 0
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 8, tr_fix("OZET"), ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 6, tr_fix(f"Toplam: {total:,.2f} TL | Onaylanan: {approved:,.2f} TL | Bekleyen: {pending:,.2f} TL"), ln=True)
    pdf.ln(6)
    pdf.set_fill_color(10, 15, 30)
    pdf.set_text_color(0, 212, 255)
    pdf.set_font("Arial", "B", 9)
    cols = [("ID",25),("Tarih",25),("Firma",45),("Tutar",25),("Proje",35),("Durum",30),("Risk%",15)]
    for col, w in cols:
        pdf.cell(w, 8, tr_fix(col), border=1, fill=True, align='C')
    pdf.ln()
    for i, (_, row) in enumerate(df_export.iterrows()):
        fill = i % 2 == 0
        pdf.set_fill_color(240, 245, 255) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "", 8)
        risk = row.get('Risk_Skoru', 0)
        values = [
            (str(row.get('ID', ''))[:12], 25),
            (str(row.get('Tarih', '')), 25),
            (str(row.get('Firma', ''))[:20], 45),
            (f"{float(row.get('Tutar',0)):,.0f} TL", 25),
            (str(row.get('Proje', ''))[:18], 35),
            (str(row.get('Durum', '')), 30),
            (f"%{risk}", 15)
        ]
        for val, w in values:
            pdf.cell(w, 7, tr_fix(val), border=1, fill=fill, align='C')
        pdf.ln()
    pdf.ln(10)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(190, 6, tr_fix("Bu rapor Stinga Pro v13 AI Finans Sistemi tarafindan otomatik uretilmistir."), ln=True)
    return bytes(pdf.output())

# ─── AI FONKSİYONLARI ─────────────────────────────────────────
def analyze_receipt_pro(image, model):
    prompt = """Sen Stinga Enerji Baş Denetçisisin. Fişi tara. SADECE aşağıdaki JSON formatında yanıt ver:
{
  "firma": "Firma Adı",
  "tarih": "YYYY-MM-DD",
  "toplam_tutar": 0.0,
  "kategori": "Yemek/Yakıt/Konaklama/Ekipman/Diğer",
  "risk_skoru": 10,
  "audit_ozeti": "1 cümlelik denetim özeti",
  "kalemler": ["kalem1", "kalem2"],
  "kdv_tutari": 0.0,
  "odeme_turu": "Nakit/Kredi Kartı/Havale",
  "anomali": false,
  "anomali_aciklamasi": ""
}"""
    try:
        response = model.generate_content([prompt, image])
        return response.text
    except Exception as e:
        if "429" in str(e).lower() or "quota" in str(e).lower():
            st.session_state.current_key_idx = (st.session_state.current_key_idx + 1) % len(API_KEYS)
            return "ANAHTAR_DEGISIMI"
        return f"HATA: {str(e)}"

def detect_anomalies(df, model):
    if df.empty or len(df) < 3:
        return []
    anomalies = []
    if 'Firma' in df.columns and 'Tutar' in df.columns:
        dups = df[df.duplicated(subset=['Firma', 'Tutar'], keep=False)]
        if not dups.empty:
            anomalies.append({"type":"duplicate","severity":"high",
                "message":f"⚠️ Mükerrer fiş: {dups['Firma'].iloc[0]} - {dups['Tutar'].iloc[0]:,.0f} ₺","count":len(dups)})
    if 'Tarih' in df.columns:
        try:
            df_temp = df.copy()
            df_temp['dt'] = pd.to_datetime(df_temp['Tarih'], errors='coerce')
            weekend = df_temp[df_temp['dt'].dt.dayofweek >= 5]
            if not weekend.empty:
                anomalies.append({"type":"weekend","severity":"medium",
                    "message":f"📅 Hafta sonu harcaması: {len(weekend)} adet işlem","count":len(weekend)})
        except: pass
    if 'Risk_Skoru' in df.columns:
        high_risk = df[df['Risk_Skoru'] > 70]
        if not high_risk.empty:
            anomalies.append({"type":"high_risk","severity":"high",
                "message":f"🔴 {len(high_risk)} adet kritik riskli işlem","count":len(high_risk)})
    if 'Tutar' in df.columns and len(df) > 3:
        mean = df['Tutar'].mean()
        std  = df['Tutar'].std()
        outliers = df[df['Tutar'] > mean + 2 * std]
        if not outliers.empty:
            anomalies.append({"type":"outlier","severity":"medium",
                "message":f"📊 Ortalamadan 2σ sapan {len(outliers)} anormal tutar","count":len(outliers)})
    return anomalies

def generate_ai_insight(df, model, question=None):
    if df.empty:
        return "Henüz analiz edilecek veri yok."
    data_summary = {
        "toplam_islem": len(df),
        "toplam_tutar": df['Tutar'].sum() if 'Tutar' in df.columns else 0,
        "ortalama_tutar": df['Tutar'].mean() if 'Tutar' in df.columns else 0,
        "en_yuksek": df['Tutar'].max() if 'Tutar' in df.columns else 0,
        "projeler": df['Proje'].value_counts().to_dict() if 'Proje' in df.columns else {},
        "kategoriler": df['Kategori'].value_counts().to_dict() if 'Kategori' in df.columns else {},
        "durum_ozeti": df['Durum'].value_counts().to_dict() if 'Durum' in df.columns else {},
        "ortalama_risk": df['Risk_Skoru'].mean() if 'Risk_Skoru' in df.columns else 0
    }
    if question:
        prompt = f"""Sen Stinga Enerji'nin üst düzey finansal analistinin yapay zekasısın.
Veriler: {json.dumps(data_summary, ensure_ascii=False)}
Tüm veriler: {df.to_dict(orient='records')}
Soru: {question}
Türkçe, kısa ve profesyonel yanıt ver. Sayısal analizler ekle."""
    else:
        prompt = f"""Sen Stinga Enerji'nin yapay zeka finansal analistinin.
Veriler: {json.dumps(data_summary, ensure_ascii=False)}
3-4 cümleyle en önemli finansal içgörüyü ver. Türkçe, net, analitik."""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI şu an yanıt veremiyor: {str(e)}"

def predict_monthly_spend(df, model):
    if df.empty: return None
    try:
        df_temp = df.copy()
        df_temp['dt'] = pd.to_datetime(df_temp['Tarih'], errors='coerce')
        monthly = df_temp.groupby(df_temp['dt'].dt.strftime('%Y-%m'))['Tutar'].sum()
        if len(monthly) < 2: return None
        vals = monthly.values.tolist()
        prompt = f"Aylık harcama verileri: {vals}. Bir sonraki ay için tahmini harcama tutarını TL olarak tek sayı olarak ver. Sadece sayı yaz."
        response = model.generate_content(prompt)
        pred_text = re.sub(r'[^\d.,]', '', response.text.strip()).replace(',', '.')
        return float(pred_text.split('.')[0]) if pred_text else None
    except: return None

# ─── GİRİŞ EKRANI ────────────────────────────────────────────
def login():
    # Logo yükle
    logo_b64 = ""
    try:
        import base64 as _b64
        _lp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
        if os.path.exists(_lp):
            with open(_lp, "rb") as _lf:
                logo_b64 = _b64.b64encode(_lf.read()).decode()
    except:
        pass

    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width:110px; height:110px; border-radius:50%; object-fit:cover; box-shadow:0 4px 20px rgba(26,158,110,0.3); margin-bottom:12px;">' if logo_b64 else '<div style="font-size:4rem;" class="floating">⚡</div>'

    st.markdown(f"""
    <div style="text-align:center; padding: 50px 0 24px 0;">
        {logo_html}
        <h1 style="font-family:'Bebas Neue',sans-serif; font-size:3.2rem; letter-spacing:6px;
                   color:#0f2240; margin:8px 0 0 0;">STINGA PRO</h1>
        <p style="color:#6b8caa; font-size:0.82rem; letter-spacing:4px; text-transform:uppercase; margin-top:6px;">
            v13.0 · AI Finans Platformu
        </p>
        <p style="color:#1a9e6e; font-size:0.78rem; letter-spacing:2px; margin-top:2px;">
            STİNGA ENERJİ A.Ş.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<div class="ultra-card pulsing">', unsafe_allow_html=True)
        with st.form("login_form"):
            st.markdown("<p style='color:#2d4a6a; font-size:0.85rem; text-transform:uppercase; letter-spacing:2px; margin-bottom:16px; font-weight:600;'>🔐 Güvenli Giriş</p>", unsafe_allow_html=True)
            username = st.text_input("Kullanıcı Adı", placeholder="kullanıcı adınız").lower().strip()
            password = st.text_input("Şifre", type="password", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("GİRİŞ YAP", use_container_width=True)
            if submit:
                if username in USERS and USERS[username]["password"] == hash_password(password):
                    st.session_state.authenticated = True
                    st.session_state.user_info = dict(USERS[username])
                    st.session_state.user_info['username'] = username
                    st.rerun()
                else:
                    st.error("⚠️ Hatalı kullanıcı adı veya şifre")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center; margin-top:20px; color:#6b8caa; font-size:0.72rem;">
            🔒 256-bit AES · Gemini 2.5 Flash AI
        </div>
        """, unsafe_allow_html=True)

def logout():
    for key in ['authenticated','user_info','chat_history']:
        if key == 'authenticated': st.session_state[key] = False
        elif key == 'user_info':   st.session_state[key] = None
        else:                      st.session_state[key] = []
    st.rerun()

# ─── ANA UYGULAMA ─────────────────────────────────────────────
init_db()

if not st.session_state.authenticated:
    login()
else:
    data_store = load_data()
    model      = configure_ai()
    user_info  = st.session_state.user_info
    user_name  = user_info["name"]
    role       = user_info["role"]   # "admin" veya "user"

    df_full = pd.DataFrame(data_store.get("expenses", []))

    # ── ROL BAZLI VERİ FİLTRESİ ──────────────────────────────
    # admin → tüm verileri görür
    # user  → sadece kendi fişlerini görür
    if role == "user" and not df_full.empty and 'Kullanıcı' in df_full.columns:
        df = df_full[df_full['Kullanıcı'] == user_name].copy()
    else:
        df = df_full.copy()

    # ── SIDEBAR ──────────────────────────────────────────────
    with st.sidebar:
        # ── Logo
        try:
            import base64 as _b64
            _lp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
            if os.path.exists(_lp):
                with open(_lp, "rb") as _lf:
                    _lb64 = _b64.b64encode(_lf.read()).decode()
                st.markdown(f'''
                <div style="text-align:center; padding:20px 0 8px 0;">
                    <img src="data:image/png;base64,{_lb64}"
                         style="width:80px; height:80px; border-radius:50%; object-fit:cover;
                                box-shadow:0 2px 12px rgba(0,0,0,0.3);">
                    <div style="color:#c8ddf0; font-family:'Bebas Neue',sans-serif; font-size:1.2rem;
                                letter-spacing:4px; margin-top:8px;">STINGA PRO</div>
                    <div style="color:#4cc9a0; font-size:0.65rem; letter-spacing:2px; margin-top:2px;">
                        STİNGA ENERJİ A.Ş.
                    </div>
                </div>
                <hr style="border-color:rgba(255,255,255,0.1); margin:0 0 12px 0;">
                ''', unsafe_allow_html=True)
        except:
            st.markdown('<div style="text-align:center; padding:20px 0; color:#c8ddf0; font-family:Bebas Neue; font-size:1.3rem; letter-spacing:4px;">⚡ STINGA PRO</div>', unsafe_allow_html=True)

        user_xp  = data_store.get("xp", {}).get(user_name, 0)
        level    = user_xp // 500 + 1
        xp_progress = (user_xp % 500) / 500

        st.markdown(f"""
        <div style="padding:14px; background:rgba(255,255,255,0.07); border-radius:12px;
                    border:1px solid rgba(255,255,255,0.1); margin-bottom:12px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <div style="font-size:2rem;">{user_info['avatar']}</div>
                <div>
                    <div style="font-weight:700; font-size:0.95rem; color:#e8f4fd;">{user_name}</div>
                    <div style="font-size:0.65rem; color:#4cc9a0; text-transform:uppercase; letter-spacing:1px;">
                        {role.upper()} · Lv.{level}
                    </div>
                </div>
            </div>
            <div style="margin-top:10px;">
                <div style="display:flex; justify-content:space-between; font-size:0.65rem; color:#7aa8c8;">
                    <span>XP: {user_xp}</span><span>Sonraki: {level*500}</span>
                </div>
                <div class="budget-track" style="background:rgba(255,255,255,0.1);">
                    <div class="budget-fill" style="width:{xp_progress*100:.0f}%; background:linear-gradient(90deg,#1a9e6e,#4cc9a0);"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Rol etiketi
        if role == "admin":
            st.markdown("""<div style="background:rgba(26,158,110,0.2); border:1px solid rgba(26,158,110,0.4);
                border-radius:8px; padding:6px 12px; font-size:0.72rem; color:#4cc9a0; text-align:center; margin-bottom:12px;">
                ✅ YÖNETİCİ · Tüm veriler + Onay yetkisi</div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div style="background:rgba(232,160,32,0.15); border:1px solid rgba(232,160,32,0.3);
                border-radius:8px; padding:6px 12px; font-size:0.72rem; color:#f0c060; text-align:center; margin-bottom:12px;">
                👤 PERSONEL · Sadece kendi fişlerin</div>""", unsafe_allow_html=True)

        # Bildirimler
        my_notifs = [n for n in data_store.get("notifications", [])
                     if (n["user"] == user_name or n["user"] == "Hepsi") and not n.get("read")]
        notif_count = len(my_notifs)
        if notif_count > 0:
            st.markdown(f"""<div style="background:rgba(224,82,82,0.15); border:1px solid rgba(224,82,82,0.35);
                border-radius:10px; padding:10px 14px; margin-bottom:12px;">
                <span style="color:#f08080; font-weight:700; font-size:0.8rem;">🔔 {notif_count} yeni bildirim</span>
                </div>""", unsafe_allow_html=True)
            with st.expander("Bildirimleri Gör"):
                for n in reversed(my_notifs[-5:]):
                    icon = {"xp":"🏆","info":"ℹ️","warning":"⚠️","success":"✅"}.get(n.get("type","info"),"📌")
                    st.markdown(f"""<div class="feed-item">
                        <div style="color:#4cc9a0;">{icon}</div>
                        <div>
                            <div style="font-size:0.8rem; color:#e8f4fd;">{n['msg']}</div>
                            <div style="font-size:0.68rem; color:#7aa8c8;">{n.get('date','')} {n.get('time','')}</div>
                        </div></div>""", unsafe_allow_html=True)

        st.markdown("---")

        # Navigasyon — role göre sayfa listesi
        if role == "admin":
            pages = [
                "🏠 Dashboard",
                "📷 Fiş Tarama",
                "💰 Finans & Kasa",
                "🔍 Anomali Dedektörü",
                "📊 Analitik Merkezi",
                "🤖 AI Asistan",
                "🏆 Leaderboard",
                "📁 Arşiv & Rapor"
            ]
        else:
            # Personel → onay merkezi ve tam finans yok
            pages = [
                "🏠 Dashboard",
                "📷 Fiş Tarama",
                "💰 Bakiyem",
                "🏆 Leaderboard",
                "📁 Fişlerim"
            ]

        selected = st.radio("", pages,
            index=pages.index(st.session_state.selected_page)
                  if st.session_state.selected_page in pages else 0,
            label_visibility="collapsed")
        st.session_state.selected_page = selected

        st.markdown("---")

        # Mini limit göstergesi
        if not df.empty and 'Tutar' in df.columns:
            my_total      = df['Tutar'].sum()
            monthly_limit = user_info.get('monthly_limit', 15000)
            usage_pct     = min(my_total / monthly_limit * 100, 100) if monthly_limit > 0 else 0
            color = "#4cc9a0" if usage_pct < 60 else ("#e8a020" if usage_pct < 85 else "#e05252")
            st.markdown(f"""<div style="padding:12px; background:rgba(255,255,255,0.07); border-radius:10px; border:1px solid rgba(255,255,255,0.1);">
                <div style="font-size:0.7rem; color:var(--text-muted); text-transform:uppercase;">Aylık Limit</div>
                <div style="font-size:1.4rem; font-weight:700; color:{color};">{usage_pct:.0f}%</div>
                <div class="budget-track">
                    <div class="budget-fill" style="width:{usage_pct:.0f}%; background:{color};"></div>
                </div>
                <div style="font-size:0.7rem; color:var(--text-muted); margin-top:4px;">{my_total:,.0f} / {monthly_limit:,.0f} ₺</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Çıkış", use_container_width=True):
            logout()

    # ══════════════════════════════════════════════════════════
    # SAYFA: DASHBOARD (admin ve user için ortak ama farklı içerik)
    # ══════════════════════════════════════════════════════════
    if selected == "🏠 Dashboard":
        st.markdown('<div class="page-header"><div class="page-title">OPERASYON MERKEZİ</div></div>', unsafe_allow_html=True)

        if role == "user":
            st.info(f"👤 **{user_name}**, sadece kendi harcamalarını görüyorsun.")

        total_approved = df[df['Durum']=='Onaylandı']['Tutar'].sum() if not df.empty and 'Durum' in df.columns else 0
        total_pending  = df[df['Durum']=='Onay Bekliyor']['Tutar'].sum() if not df.empty and 'Durum' in df.columns else 0
        crit_risks     = len(df[df['Risk_Skoru'] > 70]) if not df.empty and 'Risk_Skoru' in df.columns else 0
        my_wallet      = data_store['wallets'].get(user_name, 0)
        total_tx       = len(df) if not df.empty else 0
        avg_risk       = df['Risk_Skoru'].mean() if not df.empty and 'Risk_Skoru' in df.columns else 0

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        metrics = [
            (c1, "Onaylı Harcama",  f"₺{total_approved:,.0f}", "✓",  "#00ff88"),
            (c2, "Onay Bekleyen",   f"₺{total_pending:,.0f}",  "⏳", "#ffab00"),
            (c3, "Kritik Risk",     str(crit_risks),            "🔴", "#ff3b5c"),
            (c4, "Kasa Bakiye",     f"₺{my_wallet:,.0f}",      "💰", "#00d4ff"),
            (c5, "Toplam İşlem",    str(total_tx),              "📋", "#8b5cf6"),
            (c6, "Ort. Risk %",     f"{avg_risk:.0f}",          "🎯", "#ff6b35"),
        ]
        for col, label, value, icon, color in metrics:
            with col:
                st.markdown(f"""<div class="metric-card">
                    <div style="font-size:1.5rem;">{icon}</div>
                    <div style="font-family:'Bebas Neue'; font-size:2rem; color:{color};
                                text-shadow:0 0 20px {color}66; line-height:1.1;">{value}</div>
                    <div style="font-size:0.65rem; color:var(--text-muted); text-transform:uppercase;
                                letter-spacing:1.5px; margin-top:4px;">{label}</div>
                    </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Likidite uyarısı (sadece admin)
        if role == "admin":
            total_wallet = sum(data_store['wallets'].values())
            if total_wallet < total_pending:
                st.markdown(f"""<div class="anomaly-alert">
                    <strong style="color:#c0392b;">⚠️ LİKİDİTE UYARISI</strong>
                    <p style="margin:4px 0 0 0; font-size:0.85rem; color:#842029;">
                    Toplam kasa ({total_wallet:,.0f} ₺) onay bekleyen tutarın ({total_pending:,.0f} ₺) altında.
                    </p></div>""", unsafe_allow_html=True)

        if not df.empty:
            col_l, col_r = st.columns([3, 2])
            with col_l:
                if 'Tarih' in df.columns and 'Tutar' in df.columns:
                    df_temp = df.copy()
                    df_temp['dt'] = pd.to_datetime(df_temp['Tarih'], errors='coerce')
                    df_temp = df_temp.sort_values('dt')
                    df_temp['cumulative'] = df_temp['Tutar'].cumsum()
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=df_temp['dt'], y=df_temp['cumulative'],
                        fill='tozeroy', fillcolor='rgba(26,158,110,0.1)',
                        line=dict(color='#1a9e6e', width=2), name='Kümülatif'))
                    fig.add_trace(go.Bar(x=df_temp['dt'], y=df_temp['Tutar'],
                        marker_color='rgba(26,158,110,0.4)', name='Günlük', yaxis='y2'))
                    fig.update_layout(title="📈 Kümülatif & Günlük Harcama",
                        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#7a9bbf'), height=320,
                        yaxis2=dict(overlaying='y', side='right', showgrid=False),
                        legend=dict(bgcolor='rgba(0,0,0,0)'), hovermode='x unified')
                    st.plotly_chart(fig, use_container_width=True)

            with col_r:
                if 'Proje' in df.columns:
                    proj_data = df.groupby('Proje')['Tutar'].sum().reset_index()
                    fig2 = go.Figure(go.Pie(
                        labels=proj_data['Proje'], values=proj_data['Tutar'], hole=0.6,
                        marker=dict(colors=['#1a9e6e','#2d4a8a','#4cc9a0','#e8a020'])))
                    fig2.update_layout(title="🗂️ Proje Dağılımı",
                        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#7a9bbf'), height=320)
                    st.plotly_chart(fig2, use_container_width=True)

            # Risk bubble + kategori
            col_a, col_b = st.columns(2)
            with col_a:
                if 'Risk_Skoru' in df.columns:
                    fig3 = px.scatter(df, x='Tarih', y='Tutar', size='Risk_Skoru',
                        color='Risk_Skoru', hover_name='Firma',
                        color_continuous_scale='RdYlGn_r',
                        title='🎯 Risk Analizi', size_max=35)
                    fig3.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#7a9bbf'), height=280)
                    st.plotly_chart(fig3, use_container_width=True)
            with col_b:
                if 'Kategori' in df.columns:
                    cat_data = df.groupby('Kategori')['Tutar'].sum().sort_values().reset_index()
                    fig4 = go.Figure(go.Bar(x=cat_data['Tutar'], y=cat_data['Kategori'],
                        orientation='h',
                        marker=dict(color=cat_data['Tutar'],
                            colorscale=[[0,'#e8f4f0'],[0.5,'#1a9e6e'],[1,'#2d4a8a']]),
                        text=[f"₺{v:,.0f}" for v in cat_data['Tutar']], textposition='outside'))
                    fig4.update_layout(title='🏷️ Kategoriler',
                        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#7a9bbf'), height=280)
                    st.plotly_chart(fig4, use_container_width=True)
        else:
            st.markdown("""<div class="empty-state">
                <div class="empty-icon">📊</div>
                <div>Henüz harcama verisi yok. Fiş taraması ile başla!</div>
                </div>""", unsafe_allow_html=True)

        # AI Günlük Brifing (admin için)
        if role == "admin" and model and not df.empty:
            with st.expander("🤖 Günlük AI Finansal Brifingi", expanded=False):
                if st.button("⚡ Günlük Analizi Oluştur"):
                    with st.spinner("Gemini AI verilerini işliyor..."):
                        insight = generate_ai_insight(df, model)
                        st.session_state.last_ai_insight = insight
                if st.session_state.last_ai_insight:
                    st.markdown(f"""<div class="ai-bubble">
                        <p style="margin:0; line-height:1.7; color:var(--text-primary);">
                        {st.session_state.last_ai_insight}</p></div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    # SAYFA: FİŞ TARAMA (tüm kullanıcılar)
    # ══════════════════════════════════════════════════════════
    elif selected == "📷 Fiş Tarama":
        st.markdown('<div class="page-header"><div class="page-title">AKILLI FİŞ TARAMA</div></div>', unsafe_allow_html=True)

        col_form, col_list = st.columns([1.2, 1])

        with col_form:
            st.markdown('<div class="ultra-card">', unsafe_allow_html=True)
            st.markdown("### 📷 Fiş Yükle & AI Analiz")
            with st.form("pro_entry", clear_on_submit=True):
                f = st.file_uploader("Fiş / Fatura Fotoğrafı", type=['jpg','png','jpeg','webp'],
                    help="Net, iyi aydınlatılmış fotoğraflar için en iyi sonuç")
                col_p, col_o = st.columns(2)
                with col_p:
                    proje = st.selectbox("Proje", ["Maden Sahası","Aktif Karbon","Enerji Hatları","Genel Merkez"])
                with col_o:
                    oncelik = st.selectbox("Öncelik", ["Normal","Acil","Düşük"])
                notlar = st.text_area("Ek Not", height=80, placeholder="Harcama hakkında not...")
                submitted = st.form_submit_button("🤖 AI ile Tara ve Gönder", use_container_width=True)

                if submitted and f:
                    with st.spinner("🤖 Gemini AI fişi analiz ediyor..."):
                        progress = st.progress(0)
                        for i in range(70):
                            time.sleep(0.01)
                            progress.progress(i+1)
                        img = Image.open(f)
                        res_raw = analyze_receipt_pro(img, model)
                        progress.progress(100)

                    if res_raw == "ANAHTAR_DEGISIMI":
                        st.warning("API kotası doldu, yedek anahtara geçildi. Tekrar deneyin.")
                    elif res_raw.startswith("HATA"):
                        st.error(f"Hata: {res_raw}")
                    else:
                        data_ai = extract_json(res_raw)
                        if data_ai:
                            is_dup = any(
                                e for e in data_store["expenses"]
                                if e.get("Firma") == data_ai.get("firma")
                                and abs(float(e.get("Tutar",0)) - float(data_ai.get("toplam_tutar",0))) < 1
                            )
                            if is_dup:
                                st.error("⚠️ MÜKERRER FİŞ: Bu fiş daha önce sisteme yüklendi!")
                            else:
                                path = f"arsiv/{datetime.now().strftime('%Y_%m')}"
                                os.makedirs(path, exist_ok=True)
                                f_path = os.path.join(path, f"{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
                                with open(f_path, "wb") as fp:
                                    fp.write(f.getbuffer())

                                new_e = {
                                    "ID": datetime.now().strftime("%Y%m%d%H%M%S"),
                                    "Tarih": data_ai.get("tarih", datetime.now().strftime("%Y-%m-%d")),
                                    "Kullanıcı": user_name,
                                    "Firma": data_ai.get("firma","Bilinmiyor"),
                                    "Kategori": data_ai.get("kategori","Diğer"),
                                    "Tutar": float(data_ai.get("toplam_tutar",0)),
                                    "KDV": float(data_ai.get("kdv_tutari",0)),
                                    "Odeme_Turu": data_ai.get("odeme_turu","Bilinmiyor"),
                                    "Kalemler": data_ai.get("kalemler",[]),
                                    "Durum": "Onay Bekliyor",
                                    "Dosya_Yolu": f_path,
                                    "Risk_Skoru": int(data_ai.get("risk_skoru",0)),
                                    "AI_Audit": data_ai.get("audit_ozeti",""),
                                    "AI_Anomali": data_ai.get("anomali",False),
                                    "AI_Anomali_Aciklama": data_ai.get("anomali_aciklamasi",""),
                                    "Proje": proje,
                                    "Oncelik": oncelik,
                                    "Notlar": notlar
                                }
                                data_store["expenses"].append(new_e)
                                if proje in data_store.get("budgets",{}):
                                    data_store["budgets"][proje]["spent"] = data_store["budgets"][proje].get("spent",0) + new_e["Tutar"]
                                save_data(data_store)
                                add_xp(user_name, 50, "Fiş tarama")

                                # Yöneticilere bildirim gönder
                                for ukey, udata in USERS.items():
                                    if udata["role"] == "admin" and udata["name"] != user_name:
                                        add_notify(udata["name"],
                                            f"📋 {user_name} → {proje}: {data_ai.get('firma','?')} ₺{float(data_ai.get('toplam_tutar',0)):,.0f}",
                                            "info")

                                risk = int(data_ai.get("risk_skoru",0))
                                st.success("✅ Fiş başarıyla işlendi! +50 XP kazandın!")
                                st.markdown(f"""<div class="ultra-card">
                                    <div style="display:flex; justify-content:space-between; align-items:start;">
                                        <div>
                                            <div style="font-size:1.3rem; font-weight:700;">{data_ai.get('firma','?')}</div>
                                            <div style="font-size:2rem; font-family:'Bebas Neue'; color:var(--accent-green);">
                                                ₺{float(data_ai.get('toplam_tutar',0)):,.2f}</div>
                                            <div style="font-size:0.8rem; color:var(--text-muted);">
                                                {data_ai.get('kategori','?')} · {data_ai.get('odeme_turu','?')}</div>
                                        </div>
                                        <div style="text-align:right;">{get_risk_html(risk)}</div>
                                    </div>
                                    <div class="ai-bubble" style="margin-top:12px;">
                                        <p style="margin:0; font-size:0.85rem;">{data_ai.get('audit_ozeti','')}</p>
                                    </div>
                                    </div>""", unsafe_allow_html=True)
                                st.rerun()
                        else:
                            st.error("AI fişi okuyamadı. Daha net bir fotoğraf deneyin.")
                elif submitted and not f:
                    st.warning("Lütfen bir fiş fotoğrafı yükleyin.")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_list:
            st.markdown("### 📋 Harcamalarım")
            my_exp = df[df['Kullanıcı'] == user_name] if not df.empty and 'Kullanıcı' in df.columns else pd.DataFrame()
            if not my_exp.empty:
                for _, row in my_exp.sort_values('Tarih', ascending=False).head(8).iterrows():
                    risk = row.get('Risk_Skoru', 0)
                    st.markdown(f"""<div class="ultra-card" style="padding:16px; margin:6px 0;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div style="flex:1;">
                                <div style="font-weight:600; font-size:0.9rem;">{row.get('Firma','?')} — ₺{float(row.get('Tutar',0)):,.0f}</div>
                                <div style="font-size:0.75rem; color:var(--text-muted);">{row.get('Tarih','?')} · {row.get('Proje','?')}</div>
                                <div style="font-size:0.7rem; color:var(--text-secondary); margin-top:2px;">
                                    {str(row.get('AI_Audit',''))[:80]}{'...' if len(str(row.get('AI_Audit',''))) > 80 else ''}</div>
                            </div>
                            <div style="text-align:right; margin-left:12px;">
                                {get_status_html(row.get('Durum','?'))}
                                <div style="margin-top:4px;">{get_risk_html(risk)}</div>
                            </div>
                        </div></div>""", unsafe_allow_html=True)
            else:
                st.markdown("""<div class="empty-state"><div class="empty-icon">📋</div>
                    <div>Henüz harcama kaydın yok.</div></div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    # SAYFA: FİNANS & KASA (sadece admin)
    # ══════════════════════════════════════════════════════════
    elif selected == "💰 Finans & Kasa":
        st.markdown('<div class="page-header"><div class="page-title">FİNANS MERKEZİ</div></div>', unsafe_allow_html=True)

        # Proje bütçeleri
        st.markdown("### 📊 Proje Bütçe Durumu")
        budgets = data_store.get("budgets", {})
        b_cols = st.columns(4)
        for i, (proj, bdata) in enumerate(budgets.items()):
            limit = bdata.get("limit",0)
            spent = bdata.get("spent",0)
            pct   = min(spent/limit*100, 100) if limit > 0 else 0
            color = "#1a9e6e" if pct < 60 else ("#e8a020" if pct < 85 else "#e05252")
            with b_cols[i % 4]:
                st.markdown(f"""<div class="metric-card">
                    <div style="font-size:0.7rem; color:var(--text-muted); text-transform:uppercase;">{proj}</div>
                    <div style="font-size:1.8rem; font-family:'Bebas Neue'; color:{color};">{pct:.0f}%</div>
                    <div class="budget-track">
                        <div class="budget-fill" style="width:{pct:.0f}%; background:{color};"></div>
                    </div>
                    <div style="font-size:0.7rem; color:#7aa8c8;">₺{spent:,.0f} / ₺{limit:,.0f}</div>
                    </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_c, col_d = st.columns([1.2, 1])

        with col_c:
            st.markdown("### 👥 Personel Kasa Durumları")
            wallets = data_store["wallets"]
            for person, bal in wallets.items():
                u_key = next((k for k,v in USERS.items() if v["name"]==person), None)
                avatar = USERS[u_key]["avatar"] if u_key else "👤"
                person_limit = USERS[u_key]["monthly_limit"] if u_key else 15000
                st.markdown(f"""<div class="ultra-card" style="padding:16px; margin:8px 0;">
                    <div style="display:flex; align-items:center; justify-content:space-between;">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <span style="font-size:1.5rem;">{avatar}</span>
                            <div>
                                <div style="font-weight:600;">{person}</div>
                                <div style="font-size:0.7rem; color:#7aa8c8;">Limit: ₺{person_limit:,.0f}</div>
                            </div>
                        </div>
                        <div style="font-family:'Bebas Neue'; font-size:1.8rem; color:var(--accent-green);">₺{bal:,.0f}</div>
                    </div></div>""", unsafe_allow_html=True)

            st.markdown("### 💸 Harcırah Transfer")
            with st.form("harcirah_form"):
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    target = st.selectbox("Personel", list(wallets.keys()))
                with col_t2:
                    amt = st.number_input("Tutar (₺)", min_value=0, step=500, value=1000)
                aciklama = st.text_input("Açıklama", value="Aylık harcırah")
                if st.form_submit_button("⚡ Transfer Et", use_container_width=True):
                    data_store["wallets"][target] += amt
                    data_store["ledger"].append({
                        "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Kaynak": user_name, "Hedef": target,
                        "İşlem": aciklama, "Miktar": amt
                    })
                    save_data(data_store)
                    add_notify(target, f"💰 ₺{amt:,.0f} hesabınıza transfer edildi. ({aciklama})", "success")
                    add_xp(target, 10, "Transfer alındı")
                    st.success(f"✅ {target}'e ₺{amt:,.0f} transfer edildi!")
                    st.rerun()

        with col_d:
            st.markdown("### 📋 Son Hareketler")
            ledger = data_store.get("ledger", [])
            if ledger:
                for entry in reversed(ledger[-8:]):
                    st.markdown(f"""<div style="padding:10px 0; border-bottom:1px solid var(--border);">
                        <div style="display:flex; justify-content:space-between;">
                            <span style="font-size:0.8rem; color:var(--text-secondary);">{entry.get('Hedef','?')} ← {entry.get('Kaynak','?')}</span>
                            <span style="font-family:'JetBrains Mono'; color:var(--accent-green);">+₺{entry.get('Miktar',0):,.0f}</span>
                        </div>
                        <div style="font-size:0.7rem; color:#7aa8c8;">{entry.get('Tarih','?')} · {entry.get('İşlem','')}</div>
                        </div>""", unsafe_allow_html=True)
            else:
                st.info("Henüz hareket yok.")

        # Onay merkezi (admin)
        st.markdown("---")
        st.markdown("### ⚖️ Onay Merkezi")
        pending = df_full[df_full["Durum"] == "Onay Bekliyor"] if not df_full.empty and 'Durum' in df_full.columns else pd.DataFrame()
        if pending.empty:
            st.success("✅ Onay bekleyen işlem yok!")
        else:
            for idx, row in pending.iterrows():
                risk = row.get('Risk_Skoru', 0)
                with st.expander(f"{'🔴' if risk>70 else '🟡'} {row['Kullanıcı']} · {row.get('Firma','?')} · ₺{float(row.get('Tutar',0)):,.0f}"):
                    ca, cb = st.columns([2, 1])
                    with ca:
                        st.markdown(f"""<div class="ultra-card">
                            <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
                                <div>
                                    <div style="font-size:1.1rem; font-weight:700;">{row.get('Firma','?')}</div>
                                    <div style="font-size:0.8rem; color:var(--text-muted);">{row.get('Tarih','?')} · {row.get('Kategori','?')}</div>
                                </div>
                                <div style="text-align:right;">
                                    <div style="font-family:'Bebas Neue'; font-size:2rem; color:var(--accent-green);">₺{float(row.get('Tutar',0)):,.0f}</div>
                                    {get_risk_html(risk)}
                                </div>
                            </div>
                            <div class="ai-bubble">{row.get('AI_Audit','')}</div>
                            <div style="margin-top:8px; font-size:0.75rem; color:var(--text-muted);">
                                Proje: {row.get('Proje','?')} · Öncelik: {row.get('Oncelik','?')}
                            </div></div>""", unsafe_allow_html=True)
                        btn1, btn2 = st.columns(2)
                        if btn1.button("✅ Onayla", key=f"on_{row['ID']}", use_container_width=True):
                            data_store["wallets"][row['Kullanıcı']] = data_store["wallets"].get(row['Kullanıcı'],0) - row['Tutar']
                            for e in data_store["expenses"]:
                                if e["ID"] == row["ID"]: e["Durum"] = "Onaylandı"
                            save_data(data_store)
                            add_notify(row['Kullanıcı'], f"✅ {row.get('Firma','?')} fişin onaylandı!", "success")
                            add_xp(row['Kullanıcı'], 25, "Fiş onaylandı")
                            st.success("Onaylandı!"); st.rerun()
                        if btn2.button("❌ Reddet", key=f"ret_{row['ID']}", use_container_width=True):
                            for e in data_store["expenses"]:
                                if e["ID"] == row["ID"]: e["Durum"] = "Reddedildi"
                            save_data(data_store)
                            add_notify(row['Kullanıcı'], f"❌ {row.get('Firma','?')} fişin reddedildi.", "warning")
                            st.warning("Reddedildi!"); st.rerun()
                    with cb:
                        dosya = row.get('Dosya_Yolu','')
                        if dosya and os.path.exists(dosya):
                            st.image(dosya, caption="Orijinal Fiş", use_container_width=True)
                        else:
                            st.markdown("""<div style="height:150px; background:var(--bg-secondary); border-radius:8px;
                                display:flex; align-items:center; justify-content:center; color:var(--text-muted);">
                                📷 Görsel Yok</div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    # SAYFA: BAKİYEM (sadece user / personel)
    # ══════════════════════════════════════════════════════════
    elif selected == "💰 Bakiyem":
        st.markdown('<div class="page-header"><div class="page-title">BAKİYEM</div></div>', unsafe_allow_html=True)
        my_bal = data_store['wallets'].get(user_name, 0)
        monthly_limit = user_info.get('monthly_limit', 5000)
        my_spend = df['Tutar'].sum() if not df.empty else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""<div class="metric-card">
                <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase;">Mevcut Bakiye</div>
                <div style="font-family:'Bebas Neue'; font-size:3rem; color:var(--accent-green);">₺{my_bal:,.0f}</div>
                </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="metric-card">
                <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase;">Toplam Harcamam</div>
                <div style="font-family:'Bebas Neue'; font-size:3rem; color:var(--accent-green);">₺{my_spend:,.0f}</div>
                </div>""", unsafe_allow_html=True)
        with col3:
            kalan = monthly_limit - my_spend
            color = "#1a9e6e" if kalan > 0 else "#e05252"
            st.markdown(f"""<div class="metric-card">
                <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase;">Kalan Limit</div>
                <div style="font-family:'Bebas Neue'; font-size:3rem; color:{color};">₺{kalan:,.0f}</div>
                </div>""", unsafe_allow_html=True)

        if not df.empty:
            st.markdown("### 📋 Son Harcamalarım")
            display_cols = [c for c in ['Tarih','Firma','Tutar','Kategori','Proje','Durum','Risk_Skoru'] if c in df.columns]
            st.dataframe(df[display_cols].sort_values('Tarih', ascending=False), use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("⬇️ CSV İndir", data=csv, file_name=f"fisllerim_{user_name}.csv", mime="text/csv")

    # ══════════════════════════════════════════════════════════
    # SAYFA: ANOMALİ DEDEKTÖRÜ (sadece admin)
    # ══════════════════════════════════════════════════════════
    elif selected == "🔍 Anomali Dedektörü":
        st.markdown('<div class="page-header"><div class="page-title">ANOMALİ DEDEKTÖRÜ</div></div>', unsafe_allow_html=True)
        if not df_full.empty:
            anomalies = detect_anomalies(df_full, model)
            if anomalies:
                st.markdown(f"### 🔴 {len(anomalies)} Anomali Tespit Edildi")
                for a in anomalies:
                    sev_color = {"high":"#e05252","medium":"#e8a020","low":"#1a9e6e"}.get(a['severity'],"#00d4ff")
                    st.markdown(f"""<div class="ultra-card" style="border-left:4px solid {sev_color};">
                        <div style="display:flex; align-items:center; gap:12px;">
                            <div>
                                <div style="font-weight:600;">{a['message']}</div>
                                <div style="font-size:0.75rem; color:{sev_color}; text-transform:uppercase;">
                                    {a['severity'].upper()} SEVİYE · {a['count']} işlem</div>
                            </div></div></div>""", unsafe_allow_html=True)
            else:
                st.markdown("""<div class="ultra-card" style="border-left:4px solid #00ff88; text-align:center;">
                    <div style="font-size:3rem;">✅</div>
                    <div style="color:#00ff88; font-size:1.2rem; font-weight:600;">Anomali Tespit Edilmedi</div>
                    </div>""", unsafe_allow_html=True)

            st.markdown("### 🤖 AI Derin Analiz")
            if st.button("🔍 Kapsamlı AI Denetimi Başlat"):
                with st.spinner("Gemini AI tüm verileri tarıyor..."):
                    prompt = f"""Sen bir adli mali denetçisin. Bu harcama verilerini incele:
{df_full.to_dict(orient='records')}
Türkçe olarak: 1. En riskli 3 işlem ve neden 2. Olağandışı patternler 3. Önerilen aksiyonlar. Kısa ve net ol."""
                    try:
                        response = model.generate_content(prompt)
                        st.markdown(f"""<div class="ai-bubble">
                            <p style="margin:0; line-height:1.8; white-space:pre-wrap;">{response.text}</p>
                            </div>""", unsafe_allow_html=True)
                        data_store["ai_insights"].append({"date":datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "type":"anomaly_scan","content":response.text})
                        save_data(data_store)
                    except Exception as e:
                        st.error(f"AI yanıt veremedi: {e}")

            col_s1, col_s2 = st.columns(2)
            with col_s1:
                if 'Tutar' in df_full.columns and 'Proje' in df_full.columns:
                    fig = px.box(df_full, x='Proje', y='Tutar', color='Proje',
                        title='Proje Bazlı Tutar Dağılımı',
                        color_discrete_sequence=['#1a9e6e','#2d4a8a','#4cc9a0','#e8a020'])
                    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#7a9bbf'), showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
            with col_s2:
                if 'Risk_Skoru' in df_full.columns:
                    fig2 = px.histogram(df_full, x='Risk_Skoru', nbins=10,
                        title='Risk Skoru Dağılımı', color_discrete_sequence=['#e05252'])
                    fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#7a9bbf'))
                    st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Anomali analizi için veri gerekli.")

    # ══════════════════════════════════════════════════════════
    # SAYFA: ANALİTİK MERKEZİ (sadece admin)
    # ══════════════════════════════════════════════════════════
    elif selected == "📊 Analitik Merkezi":
        st.markdown('<div class="page-header"><div class="page-title">ANALİTİK MERKEZİ</div></div>', unsafe_allow_html=True)
        if not df_full.empty:
            tab1, tab2, tab3 = st.tabs(["📈 Trend Analizi","🗓️ Isı Haritası","🔮 Tahmin"])
            with tab1:
                df_temp = df_full.copy()
                df_temp['dt'] = pd.to_datetime(df_temp['Tarih'], errors='coerce')
                monthly = df_temp.groupby(df_temp['dt'].dt.strftime('%Y-%m')).agg(
                    Toplam=('Tutar','sum'), Adet=('Tutar','count')).reset_index()
                monthly.columns = ['Ay','Toplam','Adet']
                fig = make_subplots(rows=2, cols=1, subplot_titles=('Aylık Harcama','İşlem Adedi'), shared_xaxes=True)
                fig.add_trace(go.Bar(x=monthly['Ay'], y=monthly['Toplam'], marker_color='#1a9e6e', name='Harcama'), row=1, col=1)
                fig.add_trace(go.Scatter(x=monthly['Ay'], y=monthly['Adet'],
                    line=dict(color='#2d4a8a',width=2), fill='tozeroy', fillcolor='rgba(45,74,138,0.1)', name='Adet'), row=2, col=1)
                fig.update_layout(height=450, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#7a9bbf'), showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
                if 'Kullanıcı' in df_full.columns:
                    user_stats = df_full.groupby('Kullanıcı').agg(
                        Toplam=('Tutar','sum'), Adet=('Tutar','count'), OrtRisk=('Risk_Skoru','mean')).reset_index()
                    fig2 = px.bar(user_stats, x='Kullanıcı', y='Toplam', color='OrtRisk',
                        color_continuous_scale='RdYlGn_r',
                        title='Personel Bazlı Harcama', text=[f"₺{v:,.0f}" for v in user_stats['Toplam']])
                    fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#7a9bbf'))
                    st.plotly_chart(fig2, use_container_width=True)

            with tab2:
                df_temp2 = df_full.copy()
                df_temp2['dt'] = pd.to_datetime(df_temp2['Tarih'], errors='coerce')
                df_temp2['Gun'] = df_temp2['dt'].dt.day_name()
                df_temp2['Hafta'] = df_temp2['dt'].dt.isocalendar().week.astype(str)
                pivot = df_temp2.pivot_table(values='Tutar', index='Gun', columns='Hafta', aggfunc='sum', fill_value=0)
                gun_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
                gun_tr    = ['Pzt','Sal','Çar','Per','Cum','Cmt','Paz']
                pivot = pivot.reindex([g for g in gun_order if g in pivot.index])
                fig3 = go.Figure(go.Heatmap(z=pivot.values, x=pivot.columns.tolist(),
                    y=[gun_tr[gun_order.index(g)] for g in pivot.index if g in gun_order],
                    colorscale=[[0,'#0a0f1e'],[0.5,'#00d4ff'],[1,'#8b5cf6']],
                    text=[[f"₺{v:,.0f}" for v in row] for row in pivot.values],
                    texttemplate='%{text}', textfont=dict(size=9)))
                fig3.update_layout(title='Haftalık Harcama Yoğunluğu',
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#7a9bbf'), height=350)
                st.plotly_chart(fig3, use_container_width=True)

            with tab3:
                if st.button("🔮 Tahmin Oluştur"):
                    with st.spinner("AI pattern analizi..."):
                        pred = predict_monthly_spend(df_full, model)
                        if pred:
                            current = df_full[
                                pd.to_datetime(df_full['Tarih'], errors='coerce').dt.strftime('%Y-%m') == datetime.now().strftime('%Y-%m')
                            ]['Tutar'].sum()
                            col_x, col_y = st.columns(2)
                            with col_x:
                                st.markdown(f"""<div class="metric-card">
                                    <div style="color:var(--text-muted); font-size:0.75rem; text-transform:uppercase;">Bu Ay</div>
                                    <div style="font-family:'Bebas Neue'; font-size:2.5rem; color:var(--accent-green);">₺{current:,.0f}</div>
                                    </div>""", unsafe_allow_html=True)
                            with col_y:
                                st.markdown(f"""<div class="metric-card">
                                    <div style="color:var(--text-muted); font-size:0.75rem; text-transform:uppercase;">AI Tahmini</div>
                                    <div style="font-family:'Bebas Neue'; font-size:2.5rem; color:var(--accent-purple);">₺{pred:,.0f}</div>
                                    </div>""", unsafe_allow_html=True)
                        else:
                            st.warning("Tahmin için en az 2 aylık veri gerekli.")
        else:
            st.info("Analitik için veri gerekli.")

    # ══════════════════════════════════════════════════════════
    # SAYFA: AI ASISTAN (sadece admin)
    # ══════════════════════════════════════════════════════════
    elif selected == "🤖 AI Asistan":
        st.markdown('<div class="page-header"><div class="page-title">AI FİNANS ASISTANI</div></div>', unsafe_allow_html=True)
        quick_qs = ["En yüksek harcama hangi proje?","Bu ay risk durumu nasıl?",
                    "Hangi personel en fazla harcıyor?","Bütçe aşımı var mı?",
                    "En çok hangi kategoride harcama var?","Anomalileri özetle"]
        st.markdown("**Hızlı Sorular:**")
        q_cols = st.columns(3)
        for i, q in enumerate(quick_qs):
            with q_cols[i % 3]:
                if st.button(q, key=f"qq_{i}", use_container_width=True):
                    st.session_state.chat_history.append({"role":"user","content":q})
        st.markdown("<br>", unsafe_allow_html=True)
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f"""<div style="display:flex; justify-content:flex-end; margin:8px 0;">
                    <div style="background:rgba(0,212,255,0.1); border:1px solid rgba(0,212,255,0.2);
                        border-radius:16px 16px 0 16px; padding:12px 16px; max-width:70%;
                        color:var(--text-primary); font-size:0.9rem;">{msg['content']}</div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="ai-bubble" style="max-width:85%;">
                    <p style="margin:0; line-height:1.7; font-size:0.9rem; white-space:pre-wrap;">
                    {msg['content']}</p></div>""", unsafe_allow_html=True)
        if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
            last_q = st.session_state.chat_history[-1]["content"]
            if model:
                with st.spinner("🤖 Stinga AI düşünüyor..."):
                    answer = generate_ai_insight(df_full, model, last_q)
                    st.session_state.chat_history.append({"role":"assistant","content":answer})
                    st.rerun()
        with st.form("chat_form", clear_on_submit=True):
            col_i, col_b = st.columns([5,1])
            with col_i:
                user_q = st.text_input("", placeholder="Finansal veriler hakkında bir şey sor...", label_visibility="collapsed")
            with col_b:
                sent = st.form_submit_button("→", use_container_width=True)
            if sent and user_q.strip():
                st.session_state.chat_history.append({"role":"user","content":user_q})
                st.rerun()
        if st.session_state.chat_history:
            if st.button("🗑️ Sohbeti Temizle"):
                st.session_state.chat_history = []
                st.rerun()

    # ══════════════════════════════════════════════════════════
    # SAYFA: LEADERBOARD (tüm kullanıcılar)
    # ══════════════════════════════════════════════════════════
    elif selected == "🏆 Leaderboard":
        st.markdown('<div class="page-header"><div class="page-title">PERFORMANS SIRALAMASI</div></div>', unsafe_allow_html=True)
        xp_data = data_store.get("xp", {})
        sorted_users = sorted(xp_data.items(), key=lambda x: x[1], reverse=True)
        rank_icons = ["🥇","🥈","🥉","4️⃣"]
        for i, (uname, xp) in enumerate(sorted_users):
            u_key = next((k for k,v in USERS.items() if v["name"]==uname), None)
            avatar = USERS[u_key]["avatar"] if u_key else "👤"
            level  = xp // 500 + 1
            u_exp  = df_full[df_full['Kullanıcı']==uname] if not df_full.empty and 'Kullanıcı' in df_full.columns else pd.DataFrame()
            total_spend   = u_exp['Tutar'].sum() if not u_exp.empty else 0
            approved_count= len(u_exp[u_exp['Durum']=='Onaylandı']) if not u_exp.empty and 'Durum' in u_exp.columns else 0
            max_xp  = sorted_users[0][1] if sorted_users else 1
            bar_pct = (xp / max_xp * 100) if max_xp > 0 else 0
            rank_icon = rank_icons[i] if i < len(rank_icons) else "•"
            rank_cls  = ["gold","silver","bronze",""][min(i,3)]
            st.markdown(f"""<div class="lb-item">
                <div class="lb-rank {rank_cls}">{rank_icon}</div>
                <div style="font-size:1.8rem;">{avatar}</div>
                <div style="flex:1;">
                    <div style="font-weight:700;">{uname} <span style="font-size:0.75rem; color:var(--text-muted);">Lv.{level}</span></div>
                    <div style="font-size:0.75rem; color:var(--text-secondary);">₺{total_spend:,.0f} · {approved_count} onaylı fiş</div>
                    <div class="budget-track" style="margin-top:6px; width:200px;">
                        <div class="budget-fill" style="width:{bar_pct:.0f}%; background:{'linear-gradient(90deg,#f0a500,#e8c040)' if i==0 else 'linear-gradient(90deg,#1a9e6e,#2d4a8a)'};"></div>
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-family:'Bebas Neue'; font-size:1.8rem; color:{'#f0a500' if i==0 else '#1a9e6e'};">{xp}</div>
                    <div style="font-size:0.7rem; color:#7aa8c8;">XP</div>
                </div></div>""", unsafe_allow_html=True)

        st.markdown("<br>")
        st.markdown("### 🏅 Başarı Rozetleri")
        badge_defs = [("🚀","İlk Fiş","İlk fişini tara",1),
                      ("💯","Seri Teyitçi","10 fiş tara",10),
                      ("🎯","Risk Avcısı","5 yüksek riskli fiş",5),
                      ("⚡","Hız Ustası","Aynı gün 3 fiş",3),
                      ("🏆","Finans Gurusu","500 XP kazan",500),
                      ("💎","Elit Operatör","1000 XP kazan",1000)]
        badge_cols = st.columns(6)
        user_xp_val    = xp_data.get(user_name, 0)
        user_exp_count = len(df) if not df.empty else 0
        for i, (icon, name, desc, req) in enumerate(badge_defs):
            earned = (user_exp_count >= req) or (user_xp_val >= req)
            with badge_cols[i]:
                st.markdown(f"""<div style="text-align:center; padding:16px; background:var(--bg-card);
                    border-radius:12px; border:1px solid {'var(--accent-blue)' if earned else 'var(--border)'};
                    opacity:{'1' if earned else '0.4'};">
                    <div style="font-size:2rem;">{icon}</div>
                    <div style="font-size:0.75rem; font-weight:700; color:{'var(--accent-blue)' if earned else 'var(--text-muted)'};">{name}</div>
                    <div style="font-size:0.65rem; color:var(--text-muted);">{desc}</div>
                    {'<div style="font-size:0.65rem; color:var(--accent-green);">✓ KAZANILDI</div>' if earned else ''}
                    </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    # SAYFA: ARŞİV & RAPOR (sadece admin)
    # ══════════════════════════════════════════════════════════
    elif selected in ("📁 Arşiv & Rapor", "📁 Fişlerim"):
        is_admin = (selected == "📁 Arşiv & Rapor")
        title_txt = "ARŞİV & RAPORLAMA" if is_admin else "FİŞLERİM"
        st.markdown(f'<div class="page-header"><div class="page-title">{title_txt}</div></div>', unsafe_allow_html=True)

        work_df = df_full.copy() if is_admin else df.copy()

        tab_r, tab_a = st.tabs(["📊 Raporlama","🔍 Arşiv"])

        with tab_r:
            if not work_df.empty:
                work_df['Tarih_DT'] = pd.to_datetime(work_df['Tarih'], errors='coerce')
                work_df['Ay_Yil']   = work_df['Tarih_DT'].dt.strftime('%Y-%m')
                aylar = ["Tüm Zamanlar"] + sorted(work_df['Ay_Yil'].dropna().unique().tolist(), reverse=True)
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    secilen_ay = st.selectbox("Dönem", aylar)
                with col_f2:
                    if is_admin and 'Proje' in work_df.columns:
                        secilen_proje = st.selectbox("Proje", ["Tümü"] + work_df['Proje'].unique().tolist())
                    else:
                        secilen_proje = "Tümü"

                filtered = work_df.copy()
                if secilen_ay != "Tüm Zamanlar":
                    filtered = filtered[filtered['Ay_Yil'] == secilen_ay]
                if secilen_proje != "Tümü" and 'Proje' in filtered.columns:
                    filtered = filtered[filtered['Proje'] == secilen_proje]

                if not filtered.empty:
                    fc1, fc2, fc3, fc4 = st.columns(4)
                    fc1.metric("Toplam İşlem", len(filtered))
                    fc2.metric("Toplam Tutar",  f"₺{filtered['Tutar'].sum():,.0f}")
                    fc3.metric("Ort. Risk",      f"{filtered['Risk_Skoru'].mean():.0f}%" if 'Risk_Skoru' in filtered.columns else "—")
                    fc4.metric("Onay Oranı",     f"%{len(filtered[filtered['Durum']=='Onaylandı'])/len(filtered)*100:.0f}" if 'Durum' in filtered.columns else "—")

                    clean_df = filtered.drop(columns=['Tarih_DT','Ay_Yil'], errors='ignore')
                    d1, d2 = st.columns(2)
                    d1.download_button("📥 CSV İndir", clean_df.to_csv(index=False).encode('utf-8-sig'),
                        f"Stinga_{secilen_ay}.csv", "text/csv", use_container_width=True)
                    d2.download_button("📄 PDF Raporu", export_pdf_advanced(clean_df,"Mali Rapor",secilen_ay),
                        f"Stinga_PDF_{secilen_ay}.pdf", "application/pdf", use_container_width=True)
                    st.dataframe(clean_df.sort_values('Tarih', ascending=False), use_container_width=True, hide_index=True)
                else:
                    st.info("Bu kriterlere ait veri yok.")
            else:
                st.info("Raporlanacak veri yok.")

        with tab_a:
            if not work_df.empty:
                search = st.text_input("🔍 Ara", placeholder="firma, proje, personel...")
                display_df = work_df.copy()
                if search:
                    mask = display_df.apply(lambda row: search.lower() in str(row).lower(), axis=1)
                    display_df = display_df[mask]
                if not display_df.empty:
                    islem_listesi = ["Seçim yapın..."] + display_df.apply(
                        lambda x: f"{x['ID']} | {x.get('Tarih','')} | {x.get('Firma','')} — ₺{float(x.get('Tutar',0)):,.0f}", axis=1).tolist()
                    secilen = st.selectbox("İşlem seç:", islem_listesi)
                    if secilen != "Seçim yapın...":
                        islem_id = secilen.split(" | ")[0]
                        satir = work_df[work_df['ID'] == islem_id].iloc[0]
                        col_i, col_img = st.columns([1, 1.5])
                        with col_i:
                            st.markdown(f"""<div class="ultra-card">
                                <div style="font-size:1.3rem; font-weight:700; margin-bottom:16px;">{satir.get('Firma','?')}</div>
                                <div style="display:grid; gap:8px;">
                                    <div><span style="color:var(--text-muted); font-size:0.75rem;">Tutar:</span> ₺{float(satir.get('Tutar',0)):,.2f}</div>
                                    <div><span style="color:var(--text-muted); font-size:0.75rem;">Tarih:</span> {satir.get('Tarih','?')}</div>
                                    <div><span style="color:var(--text-muted); font-size:0.75rem;">Kategori:</span> {satir.get('Kategori','?')}</div>
                                    <div><span style="color:var(--text-muted); font-size:0.75rem;">Proje:</span> {satir.get('Proje','?')}</div>
                                    <div><span style="color:var(--text-muted); font-size:0.75rem;">Durum:</span> {get_status_html(satir.get('Durum','?'))}</div>
                                    <div><span style="color:var(--text-muted); font-size:0.75rem;">Risk:</span> {get_risk_html(satir.get('Risk_Skoru',0))}</div>
                                </div>
                                <div class="ai-bubble" style="margin-top:16px;">{satir.get('AI_Audit','Analiz mevcut değil.')}</div>
                                </div>""", unsafe_allow_html=True)
                        with col_img:
                            dosya = satir.get('Dosya_Yolu','')
                            if dosya and os.path.exists(dosya):
                                st.image(dosya, caption=f"Orijinal Fiş", use_container_width=True)
                            else:
                                st.markdown("""<div style="height:300px; background:var(--bg-secondary); border-radius:8px;
                                    display:flex; flex-direction:column; align-items:center; justify-content:center;
                                    color:var(--text-muted); border:2px dashed var(--border);">
                                    <div style="font-size:3rem; opacity:0.3;">📷</div>
                                    <div>Görsel bulunamadı</div></div>""", unsafe_allow_html=True)
            else:
                st.info("Arşivde veri yok.")

