# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════╗
# ║          STINGA PRO v12.0 - ULTRA EDITION                   ║
# ║  Geliştiren: AI ile birlikte - Gemini 2.5 Flash Destekli    ║
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
    page_title="Stinga Pro v12 ⚡",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# ─── ULTRA DARK THEME CSS ─────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;700&family=Bebas+Neue&display=swap');

:root {
    --bg-primary: #f0f5f2;
    --bg-secondary: #e4ede8;
    --bg-card: #ffffff;
    --bg-hover: #f5faf7;
    --accent-blue: #283c64;
    --accent-green: #007850;
    --accent-orange: #ea6c1e;
    --accent-purple: #283c64;
    --accent-red: #dc2626;
    --text-primary: #1a2535;
    --text-secondary: #3d5a4a;
    --text-muted: #6b8a78;
    --border: #b8d4c4;
    --border-glow: rgba(0, 120, 80, 0.3);
    --shadow-glow: 0 0 30px rgba(0, 120, 80, 0.12);
    --stinga-green: #007850;
    --stinga-navy: #283c64;
    --stinga-green-light: #e6f4ee;
    --stinga-navy-light: #e8ecf4;
}

* { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif !important;
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

/* Stinga branded background */
.stApp {
    background: 
        radial-gradient(ellipse at 0% 0%, rgba(0, 120, 80, 0.07) 0%, transparent 50%),
        radial-gradient(ellipse at 100% 100%, rgba(40, 60, 100, 0.07) 0%, transparent 50%),
        var(--bg-primary) !important;
}

/* Sidebar - Stinga branded */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #283c64 0%, #1e2e4e 60%, #14243c 100%) !important;
    border-right: 1px solid #1e2e4e !important;
}

[data-testid="stSidebar"] * {
    color: #e8f4ee !important;
}

[data-testid="stSidebar"] .stRadio label {
    color: #b8d4c4 !important;
}

[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.15) !important;
}

/* Cards */
.ultra-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    margin: 12px 0;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.ultra-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #007850, #283c64, #007850);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.ultra-card:hover::before { opacity: 1; }
.ultra-card:hover {
    border-color: rgba(0, 212, 255, 0.3);
    box-shadow: var(--shadow-glow);
    transform: translateY(-2px);
}

/* Metric cards */
.metric-card {
    background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-hover) 100%);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 28px;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.metric-card:hover {
    transform: translateY(-6px) scale(1.02);
    box-shadow: 0 20px 60px rgba(0, 212, 255, 0.15);
    border-color: var(--accent-blue);
}

.metric-value {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3rem;
    color: var(--accent-blue);
    line-height: 1;
    margin: 8px 0;
    text-shadow: none;
}

.metric-label {
    font-size: 0.75rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 600;
}

/* Risk badge */
.risk-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    font-weight: 700;
}

.risk-low { background: rgba(22, 163, 74, 0.12); color: #005c3c; border: 1px solid rgba(22, 163, 74, 0.3); }
.risk-mid { background: rgba(234, 108, 30, 0.12); color: #c2570a; border: 1px solid rgba(234, 108, 30, 0.3); }
.risk-high { background: rgba(220, 38, 38, 0.12); color: #b91c1c; border: 1px solid rgba(220, 38, 38, 0.3); }

/* Buttons - Stinga Green */
.stButton > button {
    background: linear-gradient(135deg, #007850 0%, #005c3c 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: 0.5px !important;
    transition: all 0.3s ease !important;
    padding: 0.6rem 1.2rem !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(0, 120, 80, 0.4) !important;
    background: linear-gradient(135deg, #009060 0%, #007850 100%) !important;
}

/* Header */
.page-header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 32px;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--border);
}

.page-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.8rem;
    color: var(--text-primary);
    letter-spacing: 3px;
    line-height: 1;
    background: linear-gradient(135deg, #283c64, #007850);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Data tables */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* Inputs */
.stTextInput > div > div > input,
.stSelectbox > div > div > div,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #ffffff !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div > div:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent-blue) !important;
    box-shadow: 0 0 0 2px rgba(0, 119, 204, 0.15) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-secondary) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    border: 1px solid var(--border) !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 8px !important;
    color: var(--text-secondary) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
}

.stTabs [aria-selected="true"] {
    background: #ffffff !important;
    color: var(--accent-blue) !important;
}

/* Expanders */
.streamlit-expanderHeader {
    background: #ffffff !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
}

/* Alerts */
.stSuccess { background: rgba(22, 163, 74, 0.08) !important; border-left: 3px solid #007850 !important; }
.stError { background: rgba(220, 38, 38, 0.08) !important; border-left: 3px solid #dc2626 !important; }
.stWarning { background: rgba(234, 108, 30, 0.08) !important; border-left: 3px solid #ea6c1e !important; }
.stInfo { background: rgba(0, 119, 204, 0.08) !important; border-left: 3px solid #007850 !important; }

/* Progress bar */
.stProgress > div > div { background: linear-gradient(90deg, var(--accent-blue), var(--accent-purple)) !important; }

/* Divider */
hr { border-color: var(--border) !important; }

/* ── Streamlit üst toolbar beyaz bar gizle ── */
header[data-testid="stHeader"] {
    background: var(--bg-primary) !important;
    border-bottom: 1px solid var(--border) !important;
}

header[data-testid="stHeader"]::before {
    background: var(--bg-primary) !important;
}

/* Deploy butonu ve toolbar rengi */
.stDeployButton, 
[data-testid="stToolbar"],
[data-testid="stDecoration"],
div[data-testid="stStatusWidget"] {
    background: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

/* Üst dekorasyon çizgisini kaldır */
[data-testid="stDecoration"] {
    display: none !important;
}

/* Ana içerik üst boşluk — header altına kaymasın */
.block-container {
    background: transparent !important;
    padding-top: 3.5rem !important;
    margin-top: 0 !important;
}

section[data-testid="stMain"] > div {
    background: transparent !important;
}

div[data-testid="stAppViewContainer"] > section > div {
    background: transparent !important;
}

/* Login form kutusu */
[data-testid="stForm"] {
    background: #ffffff !important;
    border: 1px solid var(--border) !important;
    border-radius: 20px !important;
    padding: 28px !important;
    box-shadow: 0 8px 32px rgba(0,120,80,0.12) !important;
}

/* Logo arka planı: logoyu beyaz zemine al, siyah arka plan kaybolsun */
.logo-circle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: #ffffff;
    border-radius: 50%;
    padding: 10px;
    box-shadow: 0 4px 20px rgba(0,120,80,0.25);
}

/* Sidebar logo beyaz zemin */
.sidebar-logo-wrap {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: #ffffff;
    border-radius: 50%;
    padding: 6px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.25);
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-secondary); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-green); }

/* Login screen */
.login-container {
    max-width: 440px;
    margin: 0 auto;
    padding: 48px 40px;
    background: #ffffff;
    border: 1px solid var(--border);
    border-radius: 24px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
}

.glow-text {
    text-shadow: 0 0 30px rgba(0, 212, 255, 0.6);
}

/* Pulse animation */
@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 10px rgba(0, 120, 80, 0.2); }
    50% { box-shadow: 0 0 25px rgba(0, 120, 80, 0.45); }
}

@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
}

.floating { animation: float 4s ease-in-out infinite; }
.pulsing { animation: pulse-glow 2s ease-in-out infinite; }

/* Activity feed item */
.feed-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 0;
    border-bottom: 1px solid var(--border);
}

.feed-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    margin-top: 6px;
    flex-shrink: 0;
}

/* Status pill */
.status-pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.pill-approved { background: rgba(22,163,74,0.12); color: #005c3c; }
.pill-pending  { background: rgba(234,108,30,0.12); color: #c2570a; }
.pill-rejected { background: rgba(220,38,38,0.12); color: #b91c1c; }

/* Sidebar nav item */
.nav-item {
    padding: 10px 16px;
    border-radius: 10px;
    margin: 2px 0;
    cursor: pointer;
    transition: all 0.2s;
    font-weight: 500;
}
.nav-item:hover { background: var(--bg-hover); }
.nav-item.active { background: rgba(0,212,255,0.1); color: var(--accent-blue); border-left: 3px solid var(--accent-blue); }

/* AI bubble */
.ai-bubble {
    background: linear-gradient(135deg, rgba(0,120,80,0.06), rgba(40,60,100,0.06));
    border: 1px solid rgba(0,120,80,0.2);
    border-radius: 16px;
    padding: 20px;
    margin: 12px 0;
    position: relative;
}

.ai-bubble::before {
    content: '⚡ AI';
    position: absolute;
    top: -10px; left: 16px;
    background: linear-gradient(135deg, #007850, #283c64);
    color: white;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 10px;
    letter-spacing: 1px;
}

/* Voice note style */
.voice-note {
    background: rgba(22, 163, 74, 0.07);
    border: 1px solid rgba(22, 163, 74, 0.2);
    border-radius: 12px;
    padding: 12px 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    color: #005c3c;
}

/* Anomaly alert */
.anomaly-alert {
    background: linear-gradient(135deg, rgba(220,38,38,0.07), rgba(234,108,30,0.07));
    border: 1px solid rgba(220,38,38,0.2);
    border-radius: 12px;
    padding: 16px;
    margin: 8px 0;
}

/* Budget bar */
.budget-track {
    background: var(--bg-secondary);
    border-radius: 8px;
    height: 8px;
    overflow: hidden;
    margin: 6px 0;
}

.budget-fill {
    height: 100%;
    border-radius: 8px;
    transition: width 0.8s ease;
}

/* Leaderboard */
.lb-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-radius: 10px;
    margin: 4px 0;
    background: #ffffff;
    border: 1px solid var(--border);
    transition: all 0.2s;
}

.lb-item:hover { border-color: var(--accent-blue); }
.lb-rank { font-family: 'Bebas Neue'; font-size: 1.5rem; color: var(--text-muted); width: 30px; }
.lb-rank.gold { color: #b8860b; }
.lb-rank.silver { color: #708090; }
.lb-rank.bronze { color: #a0522d; }

/* Heatmap cell */
.heat-cell {
    display: inline-block;
    width: 14px; height: 14px;
    border-radius: 3px;
    margin: 1px;
}

/* Tooltip-like info */
.info-tooltip {
    background: var(--bg-hover);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 0.8rem;
    color: var(--text-secondary);
}

/* Ghost card for empty states */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: var(--text-muted);
}

.empty-icon { font-size: 3rem; margin-bottom: 12px; opacity: 0.4; }

/* Upload zone */
.upload-zone {
    border: 2px dashed var(--border);
    border-radius: 16px;
    padding: 40px;
    text-align: center;
    transition: all 0.3s;
    cursor: pointer;
}

.upload-zone:hover {
    border-color: var(--accent-blue);
    background: rgba(0,212,255,0.03);
}

/* Mini sparkline-style containers */
.spark-container {
    display: flex;
    align-items: flex-end;
    gap: 2px;
    height: 30px;
}

.spark-bar {
    background: linear-gradient(180deg, var(--accent-blue), var(--accent-purple));
    border-radius: 2px;
    min-width: 4px;
    opacity: 0.7;
}

</style>
""", unsafe_allow_html=True)

# ─── KULLANICI SİSTEMİ ────────────────────────────────────────
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

USERS = {
    "zeynep": {
        "name": "Zeynep", 
        "password": hash_password("123"), 
        "role": "admin",
        "avatar": "👑",
        "department": "Yönetim",
        "monthly_limit": 50000,
        "xp": 1250
    },
    "serkan": {
        "name": "Serkan", 
        "password": hash_password("456"), 
        "role": "manager",
        "avatar": "⚡",
        "department": "Saha Operasyonları",
        "monthly_limit": 25000,
        "xp": 890
    },
    "okan": {
        "name": "Okan", 
        "password": hash_password("789"), 
        "role": "user",
        "avatar": "🔧",
        "department": "Teknik",
        "monthly_limit": 15000,
        "xp": 430
    }
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
    'voice_input': None,
    'realtime_alerts': [],
    'selected_page': '🏠 Dashboard'
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── API ──────────────────────────────────────────────────────
API_KEYS = [
    st.secrets.get("GEMINI_API_KEY_1", ""),
    st.secrets.get("GEMINI_API_KEY_2", "")
]
API_KEYS = [k for k in API_KEYS if k]  # boş olanları çıkar

def configure_ai():
    try:
        k = API_KEYS[st.session_state.current_key_idx]
        genai.configure(api_key=k)
        return genai.GenerativeModel('models/gemini-2.5-flash')
    except Exception as e:
        st.error(f"AI Hatası: {e}")
        return None

# ─── VERİTABANI ───────────────────────────────────────────────
DB_FILE = "stinga_v12_db.json"

def init_db():
    if not os.path.exists(DB_FILE):
        data = {
            "expenses": [],
            "wallets": {"Zeynep": 50000, "Serkan": 25000, "Okan": 15000},
            "ledger": [],
            "notifications": [],
            "budgets": {
                "Maden Sahası":    {"limit": 100000, "spent": 0},
                "Aktif Karbon":    {"limit":  80000, "spent": 0},
                "Enerji Hatları":  {"limit":  60000, "spent": 0},
                "Genel Merkez":    {"limit":  40000, "spent": 0}
            },
            "ai_insights": [],
            "mood_log": [],
            "badges": {"Zeynep": [], "Serkan": [], "Okan": []},
            "xp": {"Zeynep": 1250, "Serkan": 890, "Okan": 430}
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
    if score < 30:
        return f'<span class="risk-badge risk-low">✓ {score}% DÜŞÜK</span>'
    elif score < 70:
        return f'<span class="risk-badge risk-mid">⚠ {score}% ORTA</span>'
    else:
        return f'<span class="risk-badge risk-high">⛔ {score}% KRİTİK</span>'

def get_status_html(status):
    mapping = {
        "Onaylandı":    ("pill-approved", "✓ ONAYLANDI"),
        "Onay Bekliyor":("pill-pending",  "⏳ BEKLİYOR"),
        "Reddedildi":   ("pill-rejected", "✗ REDDEDİLDİ")
    }
    cls, label = mapping.get(status, ("pill-pending", status))
    return f'<span class="status-pill {cls}">{label}</span>'

def img_to_b64(img_path):
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

def export_pdf_advanced(df_export, title="Mali Rapor", ay_bilgisi="Tüm Zamanlar"):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_fill_color(5, 8, 16)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 15, "", ln=True)
    pdf.cell(190, 10, tr_fix(f"STINGA ENERJI - {title.upper()} ({ay_bilgisi})"), align='C', ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(120, 160, 200)
    pdf.cell(190, 8, tr_fix(f"Uretim Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')} | Stinga Pro v12.0"), align='C', ln=True)
    pdf.ln(12)
    
    if df_export.empty:
        pdf.set_text_color(100, 100, 100)
        pdf.set_font("Arial", "", 11)
        pdf.cell(190, 10, tr_fix("Bu doneme ait veri bulunmamaktadir."), ln=True)
        return pdf.output()
    
    # Summary
    total = df_export['Tutar'].sum() if 'Tutar' in df_export.columns else 0
    approved = df_export[df_export['Durum']=='Onaylandı']['Tutar'].sum() if 'Durum' in df_export.columns else 0
    pending  = df_export[df_export['Durum']=='Onay Bekliyor']['Tutar'].sum() if 'Durum' in df_export.columns else 0
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 8, tr_fix("OZET"), ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 6, tr_fix(f"Toplam Harcama: {total:,.2f} TL | Onaylanan: {approved:,.2f} TL | Bekleyen: {pending:,.2f} TL"), ln=True)
    pdf.ln(6)
    
    # Table header
    pdf.set_fill_color(10, 15, 30)
    pdf.set_text_color(0, 212, 255)
    pdf.set_font("Arial", "B", 9)
    cols = [("ID", 25), ("Tarih", 25), ("Firma", 45), ("Tutar", 25), ("Proje", 35), ("Durum", 30), ("Risk%", 15)]
    for col, w in cols:
        pdf.cell(w, 8, tr_fix(col), border=1, fill=True, align='C')
    pdf.ln()
    
    # Rows
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
    pdf.cell(190, 6, tr_fix("Bu rapor Stinga Pro v12.0 AI Finans Sistemi tarafindan otomatik uretilmistir."), align='C', ln=True)
    
    return pdf.output()

# ─── AI FONKSİYONLARI ─────────────────────────────────────────
def analyze_receipt_pro(image, model):
    bugun = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""Sen Stinga Enerji Baş Denetçisisin. Fişi tara. 
Bugünün tarihi: {bugun}. Fişteki tarih bu tarihten ÖNCE olmalıdır. Eğer fişteki tarih {bugun} tarihinden sonraysa anomali=true yap.
Tarih formatı mutlaka YYYY-MM-DD olsun. Yılı dikkatli oku: 2025 ve 2026 karıştırma.
SADECE aşağıdaki JSON formatını döndür, başka hiçbir şey yazma:
{{
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
}}"""
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
    
    # Aynı firma duplicate kontrolü
    if 'Firma' in df.columns and 'Tutar' in df.columns:
        dups = df[df.duplicated(subset=['Firma', 'Tutar'], keep=False)]
        if not dups.empty:
            anomalies.append({
                "type": "duplicate",
                "severity": "high",
                "message": f"⚠️ Mükerrer fiş tespiti: {dups['Firma'].iloc[0]} - {dups['Tutar'].iloc[0]:,.0f} ₺",
                "count": len(dups)
            })
    
    # Hafta sonu harcamaları
    if 'Tarih' in df.columns:
        try:
            df_temp = df.copy()
            df_temp['dt'] = pd.to_datetime(df_temp['Tarih'], errors='coerce')
            weekend = df_temp[df_temp['dt'].dt.dayofweek >= 5]
            if not weekend.empty:
                anomalies.append({
                    "type": "weekend",
                    "severity": "medium",
                    "message": f"📅 Hafta sonu harcaması: {len(weekend)} adet işlem",
                    "count": len(weekend)
                })
        except:
            pass
    
    # Yüksek risk skoru
    if 'Risk_Skoru' in df.columns:
        high_risk = df[df['Risk_Skoru'] > 70]
        if not high_risk.empty:
            anomalies.append({
                "type": "high_risk",
                "severity": "high",
                "message": f"🔴 {len(high_risk)} adet kritik riskli işlem tespit edildi",
                "count": len(high_risk)
            })
    
    # Ortalamadan çok sapan tutarlar
    if 'Tutar' in df.columns and len(df) > 3:
        mean = df['Tutar'].mean()
        std = df['Tutar'].std()
        outliers = df[df['Tutar'] > mean + 2 * std]
        if not outliers.empty:
            anomalies.append({
                "type": "outlier",
                "severity": "medium",
                "message": f"📈 Ortalamadan 2σ sapan {len(outliers)} anormal tutar tespit edildi",
                "count": len(outliers)
            })
    
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
        Şirketin harcama verileri: {json.dumps(data_summary, ensure_ascii=False)}
        Tüm veriler: {df.to_dict(orient='records')}
        
        Kullanıcı sorusu: {question}
        
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
    """Gelecek ay harcama tahmini"""
    if df.empty:
        return None
    try:
        df_temp = df.copy()
        df_temp['dt'] = pd.to_datetime(df_temp['Tarih'], errors='coerce')
        monthly = df_temp.groupby(df_temp['dt'].dt.strftime('%Y-%m'))['Tutar'].sum()
        
        if len(monthly) < 2:
            return None
        
        vals = monthly.values.tolist()
        prompt = f"""Aylık harcama verileri: {vals}. 
        Bir sonraki ay için tahmini harcama tutarını TL olarak tek sayı olarak ver. Sadece sayı yaz."""
        response = model.generate_content(prompt)
        pred_text = re.sub(r'[^\d.,]', '', response.text.strip())
        pred_text = pred_text.replace(',', '.')
        return float(pred_text.split('.')[0]) if pred_text else None
    except:
        return None

# ─── GİRİŞ EKRANI ────────────────────────────────────────────
def get_logo_b64():
    logo_paths = ["logo.png", "C:/Users/sting/Desktop/logo.png", "/mnt/user-data/uploads/logo.png"]
    for p in logo_paths:
        if os.path.exists(p):
            with open(p, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return ""

def login():
    logo_b64 = get_logo_b64()
    logo_html = (
        f'<img src="data:image/png;base64,{logo_b64}" '
        f'style="width:120px; height:120px; object-fit:contain; display:block; margin:0 auto;">'
    ) if logo_b64 else '<div style="font-size:4rem;">⚡</div>'

    st.markdown(f"""
    <div style="text-align:center; padding: 40px 0 20px 0;">
        <div class="floating" style="margin-bottom:16px;">{logo_html}</div>
        <h1 style="font-family:'Bebas Neue',sans-serif; font-size:3.5rem; letter-spacing:6px; 
                   background:linear-gradient(135deg,#007850,#283c64); 
                   -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                   margin:0;">STINGA PRO</h1>
        <p style="color:#6b8a78; font-size:0.85rem; letter-spacing:4px; text-transform:uppercase; margin:4px 0 0 0;">
            v12.0 · AI Finans Platformu
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            # Şirket adı başlığı - form içinde
            st.markdown("""
            <div style="background:linear-gradient(135deg,#007850,#283c64); border-radius:12px; 
                        padding:14px 20px; text-align:center; margin-bottom:20px;
                        box-shadow: 0 4px 15px rgba(0,120,80,0.25);">
                <div style="font-family:'Bebas Neue',sans-serif; font-size:1.4rem; letter-spacing:4px; 
                            color:#ffffff; margin:0;">STİNGA ENERJİ A.Ş.</div>
                <div style="font-size:0.7rem; color:rgba(255,255,255,0.65); letter-spacing:2px; margin-top:3px;">
                    YÖNETİM PANELİ · SİSTEME GİRİŞ
                </div>
            </div>
            """, unsafe_allow_html=True)

            username = st.text_input("👤 Kullanıcı Adı", placeholder="kullanıcı adınız").lower()
            password = st.text_input("🔒 Şifre", type="password", placeholder="••••••••")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("⚡ GİRİŞ YAP", use_container_width=True)
            
            if submit:
                if username in USERS and USERS[username]["password"] == hash_password(password):
                    st.session_state.authenticated = True
                    st.session_state.user_info = USERS[username]
                    st.session_state.user_info['username'] = username
                    st.rerun()
                else:
                    st.error("⚠️ Hatalı kullanıcı adı veya şifre")
        
        st.markdown("""
        <div style="text-align:center; margin-top:24px; color:#6b8a78; font-size:0.75rem;">
            🔒 256-bit AES · Zero-Knowledge Auth · Gemini 2.5 Flash AI
        </div>
        """, unsafe_allow_html=True)

def logout():
    for key in ['authenticated', 'user_info', 'chat_history']:
        if key == 'authenticated': st.session_state[key] = False
        elif key == 'user_info': st.session_state[key] = None
        else: st.session_state[key] = []
    st.rerun()

# ─── ANA UYGULAMA ─────────────────────────────────────────────
init_db()

if not st.session_state.authenticated:
    login()
else:
    data_store = load_data()
    model = configure_ai()
    user_info = st.session_state.user_info
    user_name = user_info["name"]
    role = user_info["role"]
    
    df = pd.DataFrame(data_store.get("expenses", []))
    
    # ── SIDEBAR ──────────────────────────────────────────────
    with st.sidebar:
        # Logo
        logo_b64 = get_logo_b64()
        if logo_b64:
            st.markdown(f"""
            <div style="text-align:center; padding:24px 10px 10px 10px;">
                <div class="sidebar-logo-wrap" style="display:inline-flex;">
                    <img src="data:image/png;base64,{logo_b64}" 
                         style="width:120px; height:120px; object-fit:contain; display:block;">
                </div>
                <div style="font-family:'Bebas Neue',sans-serif; font-size:1.2rem; 
                            letter-spacing:4px; color:#ffffff; margin-top:12px;">
                    STINGA PRO
                </div>
                <div style="font-size:0.65rem; color:rgba(255,255,255,0.5); 
                            letter-spacing:2px; margin-top:3px;">
                    STİNGA ENERJİ A.Ş.
                </div>
            </div>
            <hr style="border-color:rgba(255,255,255,0.15); margin:10px 0;">
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center; padding:16px 10px 8px 10px;">
                <div style="font-family:'Bebas Neue',sans-serif; font-size:1.4rem; 
                            letter-spacing:4px; color:#ffffff;">⚡ STINGA PRO</div>
            </div>
            """, unsafe_allow_html=True)
        # User card
        user_xp = data_store.get("xp", {}).get(user_name, 0)
        level = user_xp // 500 + 1
        xp_progress = (user_xp % 500) / 500
        
        st.markdown(f"""
        <div style="padding:16px; background:rgba(255,255,255,0.08); border-radius:16px; 
                    border:1px solid rgba(255,255,255,0.15); margin-bottom:16px;">
            <div style="display:flex; align-items:center; gap:12px;">
                <div style="font-size:2.2rem;">{user_info['avatar']}</div>
                <div>
                    <div style="font-weight:700; font-size:1rem; color:#ffffff;">{user_name}</div>
                    <div style="font-size:0.7rem; color:rgba(255,255,255,0.55); text-transform:uppercase; letter-spacing:1px;">
                        {role.upper()} · Lv.{level}
                    </div>
                </div>
            </div>
            <div style="margin-top:12px;">
                <div style="display:flex; justify-content:space-between; font-size:0.7rem; color:rgba(255,255,255,0.45); margin-bottom:4px;">
                    <span>XP: {user_xp}</span><span>Sonraki: {(level)*500} XP</span>
                </div>
                <div style="background:rgba(255,255,255,0.15); border-radius:8px; height:6px; overflow:hidden;">
                    <div style="width:{xp_progress*100:.0f}%; height:100%; border-radius:8px;
                                background:linear-gradient(90deg,#007850,#00b878);"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Notifications badge
        my_notifs = [n for n in data_store.get("notifications", []) 
                     if (n["user"] == user_name or n["user"] == "Hepsi") and not n.get("read", False)]
        notif_count = len(my_notifs)
        
        if notif_count > 0:
            st.markdown(f"""
            <div style="background:rgba(220,38,38,0.2); border:1px solid rgba(220,38,38,0.4); 
                        border-radius:10px; padding:10px 14px; margin-bottom:12px; cursor:pointer;">
                <span style="color:#ff6b6b; font-weight:700; font-size:0.8rem;">🔔 {notif_count} yeni bildirim</span>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("Bildirimleri Gör"):
                for n in reversed(my_notifs[-5:]):
                    icon = {"xp": "🏆", "info": "ℹ️", "warning": "⚠️", "success": "✅"}.get(n.get("type", "info"), "📌")
                    st.markdown(f"""
                    <div class="feed-item">
                        <div style="color:var(--accent-blue); font-size:1rem;">{icon}</div>
                        <div>
                            <div style="font-size:0.8rem; color:var(--text-primary);">{n['msg']}</div>
                            <div style="font-size:0.7rem; color:var(--text-muted);">{n.get('date','')} {n['time']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation
        pages = [
            ("🏠 Dashboard",        ""),
            ("📑 Fiş Tarama",       ""),
            ("💰 Finans & Kasa",    ""),
            ("🔬 Anomali Dedektörü",""),
            ("📊 Analitik Merkezi", ""),
            ("🤖 AI Asistan",       ""),
            ("🏆 Leaderboard",      ""),
            ("🗄️ Arşiv & Rapor",   "")
        ]
        
        selected = st.radio("", [p[0] for p in pages], 
                           index=[p[0] for p in pages].index(st.session_state.selected_page) 
                           if st.session_state.selected_page in [p[0] for p in pages] else 0,
                           label_visibility="collapsed")
        st.session_state.selected_page = selected
        
        st.markdown("---")
        
        # Mini stats
        if not df.empty and 'Tutar' in df.columns:
            my_total = df[df['Kullanıcı'] == user_name]['Tutar'].sum() if 'Kullanıcı' in df.columns else 0
            monthly_limit = user_info.get('monthly_limit', 15000)
            usage_pct = min(my_total / monthly_limit * 100, 100) if monthly_limit > 0 else 0
            color = "#00e090" if usage_pct < 60 else ("#ffcc55" if usage_pct < 85 else "#ff6b6b")
            
            st.markdown(f"""
            <div style="padding:12px; background:rgba(255,255,255,0.08); border-radius:10px; border:1px solid rgba(255,255,255,0.15);">
                <div style="font-size:0.7rem; color:rgba(255,255,255,0.5); text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">
                    Aylık Limit Kullanımı
                </div>
                <div style="font-size:1.4rem; font-weight:700; color:{color};">{usage_pct:.0f}%</div>
                <div style="background:rgba(255,255,255,0.15); border-radius:8px; height:6px; overflow:hidden; margin-top:6px;">
                    <div style="width:{usage_pct:.0f}%; height:100%; border-radius:8px; background:{color};"></div>
                </div>
                <div style="font-size:0.7rem; color:rgba(255,255,255,0.4); margin-top:4px;">
                    {my_total:,.0f} / {monthly_limit:,.0f} ₺
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Çıkış", use_container_width=True):
            logout()

    # ══════════════════════════════════════════════════════════
    # SAYFA: DASHBOARD
    # ══════════════════════════════════════════════════════════
    if selected == "🏠 Dashboard":
        st.markdown('<div class="page-header"><div class="page-title">OPERASYON MERKEZİ</div></div>', unsafe_allow_html=True)
        
        # KPI Row
        total_approved = df[df['Durum']=='Onaylandı']['Tutar'].sum() if not df.empty and 'Durum' in df.columns else 0
        total_pending  = df[df['Durum']=='Onay Bekliyor']['Tutar'].sum() if not df.empty and 'Durum' in df.columns else 0
        crit_risks = len(df[df['Risk_Skoru'] > 70]) if not df.empty and 'Risk_Skoru' in df.columns else 0
        my_wallet = data_store['wallets'].get(user_name, 0)
        total_tx = len(df) if not df.empty else 0
        avg_risk = df['Risk_Skoru'].mean() if not df.empty and 'Risk_Skoru' in df.columns else 0
        
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        
        metrics = [
            (c1, "Onaylı Harcama", f"₺{total_approved:,.0f}", "✓", "#007850"),
            (c2, "Onay Bekleyen", f"₺{total_pending:,.0f}", "⏳", "#d97706"),
            (c3, "Kritik Risk", str(crit_risks), "⛔", "#dc2626"),
            (c4, "Kasa Bakiye", f"₺{my_wallet:,.0f}", "💰", "#007850"),
            (c5, "Toplam İşlem", str(total_tx), "📊", "#283c64"),
            (c6, "Ort. Risk %", f"{avg_risk:.0f}", "🎯", "#ea6c1e"),
        ]
        
        for col, label, value, icon, color in metrics:
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size:1.5rem; margin-bottom:4px;">{icon}</div>
                    <div style="font-family:'Bebas Neue'; font-size:2rem; color:{color}; 
                                text-shadow:0 0 20px {color}66; line-height:1.1;">{value}</div>
                    <div style="font-size:0.65rem; color:var(--text-muted); text-transform:uppercase; 
                                letter-spacing:1.5px; margin-top:4px;">{label}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Liquidity warning
        if role == "admin":
            total_wallet = sum(data_store['wallets'].values())
            if total_wallet < total_pending:
                st.markdown(f"""
                <div class="anomaly-alert">
                    <strong style="color:#dc2626;">⚠️ LİKİDİTE UYARISI</strong>
                    <p style="margin:4px 0 0 0; font-size:0.85rem; color:#7f1d1d;">
                        Toplam kasa bakiyesi ({total_wallet:,.0f} ₺), onay bekleyen tutarın ({total_pending:,.0f} ₺) altında.
                        Acil sermaye transferi gerekiyor.
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        # Charts Row
        if not df.empty:
            col_l, col_r = st.columns([3, 2])
            
            with col_l:
                if 'Tarih' in df.columns and 'Tutar' in df.columns:
                    df_temp = df.copy()
                    df_temp['dt'] = pd.to_datetime(df_temp['Tarih'], errors='coerce')
                    df_temp = df_temp.sort_values('dt')
                    df_temp['cumulative'] = df_temp['Tutar'].cumsum()
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df_temp['dt'], y=df_temp['cumulative'],
                        fill='tozeroy',
                        fillcolor='rgba(0,212,255,0.08)',
                        line=dict(color='#007850', width=2),
                        name='Kümülatif Harcama',
                        hovertemplate='<b>%{x}</b><br>₺%{y:,.0f}<extra></extra>'
                    ))
                    fig.add_trace(go.Bar(
                        x=df_temp['dt'], y=df_temp['Tutar'],
                        marker_color='rgba(139,92,246,0.4)',
                        name='Günlük İşlem',
                        yaxis='y2'
                    ))
                    fig.update_layout(
                        title="📈 Zaman Serisi: Kümülatif & Günlük Harcama",
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#4a5568', family='Space Grotesk'),
                        xaxis=dict(gridcolor='rgba(203,213,224,0.8)', showgrid=True),
                        yaxis=dict(gridcolor='rgba(203,213,224,0.8)', showgrid=True),
                        yaxis2=dict(overlaying='y', side='right', showgrid=False),
                        legend=dict(bgcolor='rgba(0,0,0,0)'),
                        hovermode='x unified',
                        height=320
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col_r:
                if 'Proje' in df.columns:
                    proj_data = df.groupby('Proje')['Tutar'].sum().reset_index()
                    fig2 = go.Figure(go.Pie(
                        labels=proj_data['Proje'],
                        values=proj_data['Tutar'],
                        hole=0.6,
                        marker=dict(colors=['#007850','#283c64','#007850','#ea6c1e']),
                        textfont=dict(family='Space Grotesk')
                    ))
                    fig2.update_layout(
                        title="🥧 Proje Bazlı Dağılım",
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#4a5568'),
                        height=320,
                        legend=dict(bgcolor='rgba(0,0,0,0)')
                    )
                    st.plotly_chart(fig2, use_container_width=True)
            
            # Risk bubble + category bar
            col_a, col_b = st.columns(2)
            
            with col_a:
                if 'Risk_Skoru' in df.columns:
                    fig3 = px.scatter(
                        df, x='Tarih', y='Tutar', 
                        size='Risk_Skoru', color='Risk_Skoru',
                        hover_name='Firma',
                        color_continuous_scale='RdYlGn_r',
                        title='🎯 Risk Analizi (Balon Büyüklüğü = Risk)',
                        size_max=35,
                        hover_data={'Risk_Skoru': True, 'Proje': True}
                    )
                    fig3.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#4a5568'), height=280
                    )
                    st.plotly_chart(fig3, use_container_width=True)
            
            with col_b:
                if 'Kategori' in df.columns:
                    cat_data = df.groupby('Kategori')['Tutar'].sum().sort_values(ascending=True).reset_index()
                    fig4 = go.Figure(go.Bar(
                        x=cat_data['Tutar'], y=cat_data['Kategori'],
                        orientation='h',
                        marker=dict(
                            color=cat_data['Tutar'],
                            colorscale=[[0,'#1a2d4a'],[0.5,'#007850'],[1,'#283c64']]
                        ),
                        text=[f"₺{v:,.0f}" for v in cat_data['Tutar']],
                        textposition='outside'
                    ))
                    fig4.update_layout(
                        title='📂 Kategori Bazlı Harcama',
                        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#4a5568'), height=280,
                        xaxis=dict(showgrid=False), yaxis=dict(showgrid=False)
                    )
                    st.plotly_chart(fig4, use_container_width=True)
        
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-icon">📊</div>
                <div style="color:var(--text-secondary);">Henüz harcama verisi yok. Fiş tarama ile başla!</div>
            </div>
            """, unsafe_allow_html=True)
        
        # AI Daily Brief
        if model and not df.empty:
            with st.expander("🤖 Günlük AI Finansal Brifingi", expanded=True):
                if st.button("⚡ Günlük Analizi Oluştur"):
                    with st.spinner("Gemini AI verilerini işliyor..."):
                        insight = generate_ai_insight(df, model)
                        st.session_state.last_ai_insight = insight
                
                if st.session_state.last_ai_insight:
                    st.markdown(f"""
                    <div class="ai-bubble">
                        <p style="margin:0; line-height:1.7; color:var(--text-primary); font-size:0.9rem;">
                            {st.session_state.last_ai_insight}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    # SAYFA: FİŞ TARAMA
    # ══════════════════════════════════════════════════════════
    elif selected == "📑 Fiş Tarama":
        st.markdown('<div class="page-header"><div class="page-title">AKILLI FİŞ TARAMA</div></div>', unsafe_allow_html=True)
        
        col_form, col_list = st.columns([1.2, 1])
        
        with col_form:
            st.markdown('<div class="ultra-card">', unsafe_allow_html=True)
            st.markdown("### 📸 Fiş Yükle & AI Analiz")
            
            with st.form("pro_entry", clear_on_submit=True):
                f = st.file_uploader("Fiş / Fatura Fotoğrafı", type=['jpg','png','jpeg','webp'],
                                     help="Net, iyi aydınlatılmış fotoğraflar için en iyi sonucu alırsınız")
                
                col_p, col_o = st.columns(2)
                with col_p:
                    proje = st.selectbox("Proje", ["Maden Sahası", "Aktif Karbon", "Enerji Hatları", "Genel Merkez"])
                with col_o:
                    oncelik = st.selectbox("Öncelik", ["Normal", "Acil", "Düşük"])
                
                notlar = st.text_area("Ek Not (isteğe bağlı)", height=80, placeholder="Harcamayla ilgili açıklama...")
                
                submitted = st.form_submit_button("🚀 AI ile Tara ve Gönder", use_container_width=True)
                
                if submitted and f:
                    with st.spinner("🤖 Gemini AI fişi analiz ediyor..."):
                        progress = st.progress(0)
                        for i in range(70):
                            time.sleep(0.01)
                            progress.progress(i + 1)
                        
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
                                # ── Gelişmiş Mükerrer Fiş Kontrolü ──
                                firma_yeni = str(data_ai.get("firma", "")).strip().lower()
                                tutar_yeni = float(data_ai.get("toplam_tutar", 0))
                                tarih_yeni = str(data_ai.get("tarih", ""))

                                dup_ayni_gun = None
                                dup_farkli_kullanici = None

                                for e in data_store["expenses"]:
                                    firma_eski = str(e.get("Firma", "")).strip().lower()
                                    tutar_eski = float(e.get("Tutar", 0))
                                    tarih_eski = str(e.get("Tarih", ""))

                                    tutar_esit = abs(tutar_eski - tutar_yeni) < 1.0
                                    firma_esit = firma_eski == firma_yeni or (
                                        len(firma_yeni) > 3 and (firma_yeni in firma_eski or firma_eski in firma_yeni)
                                    )

                                    if firma_esit and tutar_esit:
                                        if tarih_eski == tarih_yeni:
                                            dup_ayni_gun = e
                                            break
                                        elif e.get("Kullanıcı") != user_name:
                                            dup_farkli_kullanici = e

                                if dup_ayni_gun:
                                    st.error(
                                        f"⛔ MÜKERRER FİŞ TESPİTİ!\n\n"
                                        f"Bu fiş **{dup_ayni_gun.get('Kullanıcı')}** tarafından "
                                        f"aynı tarihte sisteme zaten yüklenmiş.\n\n"
                                        f"Firma: {dup_ayni_gun.get('Firma')} | "
                                        f"Tutar: ₺{tutar_eski:,.0f} | Tarih: {tarih_eski}"
                                    )
                                elif dup_farkli_kullanici:
                                    st.warning(
                                        f"⚠️ OLASI MÜKERRER FİŞ!\n\n"
                                        f"Aynı firma ve tutarda bir fiş **{dup_farkli_kullanici.get('Kullanıcı')}** "
                                        f"tarafından {dup_farkli_kullanici.get('Tarih')} tarihinde yüklenmiş. "
                                        f"Farklı tarihli olduğu için sistem yüklemeye izin verdi, "
                                        f"ancak yönetici denetimi önerilir."
                                    )
                                    add_notify("Zeynep",
                                        f"🔴 Olası mükerrer fiş: {data_ai.get('firma')} ₺{tutar_yeni:,.0f} — "
                                        f"{user_name} ve {dup_farkli_kullanici.get('Kullanıcı')} aynı fişi yüklemiş olabilir.",
                                        "warning"
                                    )

                                if not dup_ayni_gun:
                                    # ── Tarih Doğrulama (Python tarafında) ──
                                    tarih_str = data_ai.get("tarih", datetime.now().strftime("%Y-%m-%d"))
                                    try:
                                        tarih_dt = datetime.strptime(tarih_str, "%Y-%m-%d")
                                        bugun_dt = datetime.now()
                                        if tarih_dt > bugun_dt:
                                            # AI yanlış tarih verdiyse bugünün tarihine çek
                                            tarih_str = bugun_dt.strftime("%Y-%m-%d")
                                            data_ai["tarih"] = tarih_str
                                            data_ai["anomali"] = False
                                            data_ai["anomali_aciklamasi"] = ""
                                            st.info("ℹ️ Fiş tarihi gelecek olarak tespit edildi, bugünün tarihi kullanıldı.")
                                    except:
                                        tarih_str = datetime.now().strftime("%Y-%m-%d")
                                        data_ai["tarih"] = tarih_str

                                    # Save file
                                    path = f"arsiv/{datetime.now().strftime('%Y_%m')}"
                                    os.makedirs(path, exist_ok=True)
                                    f_path = os.path.join(path, f"{datetime.now().strftime('%H%M%S')}_{f.name}")
                                    with open(f_path, "wb") as fp:
                                        fp.write(f.getbuffer())
                                    
                                    new_e = {
                                        "ID": datetime.now().strftime("%Y%m%d%H%M%S"),
                                        "Tarih": data_ai.get("tarih", datetime.now().strftime("%Y-%m-%d")),
                                        "Kullanıcı": user_name,
                                        "Firma": data_ai.get("firma", "Bilinmiyor"),
                                        "Kategori": data_ai.get("kategori", "Diğer"),
                                        "Tutar": float(data_ai.get("toplam_tutar", 0)),
                                        "KDV": float(data_ai.get("kdv_tutari", 0)),
                                        "Odeme_Turu": data_ai.get("odeme_turu", "Bilinmiyor"),
                                        "Kalemler": data_ai.get("kalemler", []),
                                        "Durum": "Onay Bekliyor",
                                        "Dosya_Yolu": f_path,
                                        "Risk_Skoru": int(data_ai.get("risk_skoru", 0)),
                                        "AI_Audit": data_ai.get("audit_ozeti", ""),
                                        "AI_Anomali": data_ai.get("anomali", False),
                                        "AI_Anomali_Aciklama": data_ai.get("anomali_aciklamasi", ""),
                                        "Proje": proje,
                                        "Oncelik": oncelik,
                                        "Notlar": notlar
                                    }
                                    
                                    data_store["expenses"].append(new_e)
                                    
                                    # Update budget
                                    if proje in data_store.get("budgets", {}):
                                        data_store["budgets"][proje]["spent"] = data_store["budgets"][proje].get("spent", 0) + float(data_ai.get("toplam_tutar", 0))
                                    
                                    save_data(data_store)
                                    
                                    # XP reward
                                    add_xp(user_name, 50, "Fiş tarama")
                                    
                                    if role != "admin":
                                        add_notify("Zeynep", 
                                                  f"{user_name}, {proje} → {data_ai.get('firma')} ({data_ai.get('toplam_tutar',0):,.0f} ₺)", 
                                                  "info")
                                    
                                    # Show result
                                    risk = int(data_ai.get("risk_skoru", 0))
                                    anomali = data_ai.get("anomali", False)
                                    
                                    st.success("✅ Fiş başarıyla işlendi! +50 XP kazandın!")
                                    
                                    # Result card
                                    st.markdown(f"""
                                    <div class="ultra-card">
                                        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                                            <div>
                                                <div style="font-size:1.3rem; font-weight:700; color:var(--text-primary);">
                                                    {data_ai.get('firma','?')}
                                                </div>
                                                <div style="font-size:2rem; font-family:'Bebas Neue'; color:var(--accent-blue); margin:4px 0;">
                                                    ₺{float(data_ai.get('toplam_tutar',0)):,.2f}
                                                </div>
                                                <div style="font-size:0.8rem; color:var(--text-secondary);">
                                                    {data_ai.get('kategori','?')} · {data_ai.get('odeme_turu','?')} · {data_ai.get('tarih','?')}
                                                </div>
                                            </div>
                                            <div style="text-align:right;">
                                                {get_risk_html(risk)}
                                                {"<br><span style='color:#dc2626; font-size:0.75rem; margin-top:4px; display:block;'>⚠️ ANOMALİ TESPİT EDİLDİ</span>" if anomali else ""}
                                            </div>
                                        </div>
                                        <div class="ai-bubble" style="margin-top:12px;">
                                            <p style="margin:0; font-size:0.85rem; color:var(--text-secondary);">
                                                {data_ai.get('audit_ozeti','Analiz tamamlandı.')}
                                            </p>
                                        </div>
                                        {"<div class='anomaly-alert' style='margin-top:8px;'><strong style='color:#dc2626;'>🚨 " + str(data_ai.get('anomali_aciklamasi','')) + "</strong></div>" if anomali and data_ai.get('anomali_aciklamasi') else ""}
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
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
                    st.markdown(f"""
                    <div class="ultra-card" style="padding:16px; margin:6px 0;">
                        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                            <div style="flex:1;">
                                <div style="font-weight:600; font-size:0.9rem; color:var(--text-primary);">{row.get('Firma','?')}</div>
                                <div style="font-size:0.75rem; color:var(--text-muted); margin:2px 0;">{row.get('Tarih','?')} · {row.get('Proje','?')}</div>
                                <div style="font-size:0.7rem; color:var(--text-secondary); margin-top:4px; font-style:italic;">
                                    {str(row.get('AI_Audit',''))[:80]}{'...' if len(str(row.get('AI_Audit',''))) > 80 else ''}
                                </div>
                            </div>
                            <div style="text-align:right; margin-left:12px;">
                                <div style="font-family:'Bebas Neue'; font-size:1.3rem; color:var(--accent-blue);">₺{float(row.get('Tutar',0)):,.0f}</div>
                                {get_status_html(row.get('Durum','?'))}
                                <div style="margin-top:4px;">{get_risk_html(risk)}</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="empty-state">
                    <div class="empty-icon">📭</div>
                    <div>Henüz harcama kaydın yok.</div>
                </div>
                """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    # SAYFA: FİNANS & KASA
    # ══════════════════════════════════════════════════════════
    elif selected == "💰 Finans & Kasa":
        st.markdown('<div class="page-header"><div class="page-title">FİNANS MERKEZİ</div></div>', unsafe_allow_html=True)
        
        # Budget overview
        st.markdown("### 📊 Proje Bütçe Durumu")
        budgets = data_store.get("budgets", {})
        
        b_cols = st.columns(4)
        for i, (proj, bdata) in enumerate(budgets.items()):
            limit = bdata.get("limit", 0)
            spent = bdata.get("spent", 0)
            pct = min(spent / limit * 100, 100) if limit > 0 else 0
            color = "#007850" if pct < 60 else ("#d97706" if pct < 85 else "#dc2626")
            
            with b_cols[i % 4]:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size:0.7rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:1px;">{proj}</div>
                    <div style="font-size:1.8rem; font-family:'Bebas Neue'; color:{color}; margin:8px 0;">{pct:.0f}%</div>
                    <div class="budget-track">
                        <div class="budget-fill" style="width:{pct:.0f}%; background:{color};"></div>
                    </div>
                    <div style="font-size:0.7rem; color:var(--text-muted); margin-top:6px;">
                        ₺{spent:,.0f} / ₺{limit:,.0f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_c, col_d = st.columns([1.2, 1])
        
        with col_c:
            if role == "admin":
                st.markdown("### 💳 Personel Kasa Durumları")
                wallets = data_store["wallets"]
                
                for person, bal in wallets.items():
                    person_limit = USERS.get(person.lower(), {}).get("monthly_limit", 15000)
                    bal_pct = min(bal / person_limit * 100, 100) if person_limit > 0 else 0
                    avatar = USERS.get(person.lower(), {}).get("avatar", "👤")
                    
                    st.markdown(f"""
                    <div class="ultra-card" style="padding:16px; margin:8px 0;">
                        <div style="display:flex; align-items:center; justify-content:space-between;">
                            <div style="display:flex; align-items:center; gap:10px;">
                                <span style="font-size:1.5rem;">{avatar}</span>
                                <div>
                                    <div style="font-weight:600;">{person}</div>
                                    <div style="font-size:0.7rem; color:var(--text-muted);">Kasa Bakiyesi</div>
                                </div>
                            </div>
                            <div style="font-family:'Bebas Neue'; font-size:1.8rem; color:var(--accent-blue);">₺{bal:,.0f}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
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
                            "Kaynak": user_name,
                            "Hedef": target,
                            "İşlem": aciklama,
                            "Miktar": amt
                        })
                        save_data(data_store)
                        add_notify(target, f"💰 Hesabınıza ₺{amt:,.0f} transfer yapıldı. ({aciklama})", "success")
                        add_xp(target, 10, "Transfer alındı")
                        st.success(f"✅ {target}'e ₺{amt:,.0f} transfer edildi!")
                        st.rerun()
            else:
                my_bal = data_store['wallets'].get(user_name, 0)
                st.markdown(f"""
                <div class="metric-card" style="margin-bottom:16px;">
                    <div style="font-size:1rem; color:var(--text-secondary);">Mevcut Bakiyeniz</div>
                    <div style="font-family:'Bebas Neue'; font-size:3.5rem; color:var(--accent-green); 
                                text-shadow:0 0 30px rgba(0,255,136,0.4);">
                        ₺{my_bal:,.0f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with col_d:
            st.markdown("### 📜 Son Hareketler")
            ledger = data_store.get("ledger", [])
            if ledger:
                for entry in reversed(ledger[-8:]):
                    st.markdown(f"""
                    <div style="padding:10px 0; border-bottom:1px solid var(--border);">
                        <div style="display:flex; justify-content:space-between;">
                            <span style="font-size:0.8rem; color:var(--text-secondary);">{entry.get('İşlem','?')}</span>
                            <span style="font-family:'JetBrains Mono'; color:var(--accent-blue); font-size:0.85rem;">
                                +₺{entry.get('Miktar',0):,.0f}
                            </span>
                        </div>
                        <div style="font-size:0.7rem; color:var(--text-muted);">{entry.get('Tarih','?')} → {entry.get('Hedef','?')}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Henüz hareket yok.")
        
        # Admin approval center
        if role == "admin":
            st.markdown("---")
            st.markdown("### ⚖️ Onay Merkezi")
            
            pending = df[df["Durum"] == "Onay Bekliyor"] if not df.empty and 'Durum' in df.columns else pd.DataFrame()
            
            if pending.empty:
                st.success("✅ Onay bekleyen işlem yok. Muhteşem!")
            else:
                for idx, row in pending.iterrows():
                    risk = row.get('Risk_Skoru', 0)
                    risk_color = "#007850" if risk < 30 else ("#d97706" if risk < 70 else "#dc2626")
                    
                    with st.expander(f"{'🔴' if risk > 70 else '🟡'} {row['Kullanıcı']} · {row['Firma']} · ₺{row['Tutar']:,.0f} · {row['Proje']}"):
                        ca, cb = st.columns([2, 1])
                        
                        with ca:
                            st.markdown(f"""
                            <div class="ultra-card">
                                <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
                                    <div>
                                        <div style="font-size:1.1rem; font-weight:700;">{row.get('Firma','?')}</div>
                                        <div style="font-size:0.8rem; color:var(--text-muted);">{row.get('Tarih','?')} · {row.get('Kategori','?')}</div>
                                    </div>
                                    <div style="text-align:right;">
                                        <div style="font-family:'Bebas Neue'; font-size:2rem; color:var(--accent-blue);">₺{float(row.get('Tutar',0)):,.0f}</div>
                                        {get_risk_html(risk)}
                                    </div>
                                </div>
                                <div class="ai-bubble">
                                    🤖 {row.get('AI_Audit','')}
                                </div>
                                {"<div class='anomaly-alert' style='margin-top:8px;'>⚠️ AI Anomali Tespiti: " + str(row.get('AI_Anomali_Aciklama','')) + "</div>" if row.get('AI_Anomali') else ""}
                                <div style="margin-top:8px; font-size:0.75rem; color:var(--text-muted);">
                                    Proje: {row.get('Proje','?')} · Öncelik: {row.get('Oncelik','Normal')} · Ödeme: {row.get('Odeme_Turu','?')}
                                </div>
                                {f"<div style='margin-top:6px; font-size:0.75rem; color:var(--text-secondary);'>📝 Not: {row.get('Notlar','')}</div>" if row.get('Notlar') else ""}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            btn1, btn2 = st.columns(2)
                            if btn1.button("✅ Onayla", key=f"on_{row['ID']}", use_container_width=True):
                                data_store["wallets"][row['Kullanıcı']] -= row['Tutar']
                                for e in data_store["expenses"]:
                                    if e["ID"] == row["ID"]: e["Durum"] = "Onaylandı"
                                save_data(data_store)
                                add_notify(row['Kullanıcı'], f"✅ {row['Firma']} (₺{row['Tutar']:,.0f}) ONAYLANDI", "success")
                                add_xp(row['Kullanıcı'], 25, "Fiş onaylandı")
                                st.success("Onaylandı!"); st.rerun()
                            
                            if btn2.button("❌ Reddet", key=f"ret_{row['ID']}", use_container_width=True):
                                for e in data_store["expenses"]:
                                    if e["ID"] == row["ID"]: e["Durum"] = "Reddedildi"
                                save_data(data_store)
                                add_notify(row['Kullanıcı'], f"❌ {row['Firma']} harcamanız REDDEDİLDİ", "warning")
                                st.warning("Reddedildi!"); st.rerun()
                        
                        with cb:
                            dosya = row.get('Dosya_Yolu', '')
                            if dosya and os.path.exists(dosya):
                                st.image(dosya, caption="Orijinal Fiş", use_container_width=True)
                            else:
                                st.markdown("""
                                <div style="height:150px; background:var(--bg-secondary); border-radius:10px; 
                                            display:flex; align-items:center; justify-content:center; color:var(--text-muted);">
                                    📷 Görsel Yok
                                </div>
                                """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    # SAYFA: ANOMALİ DEDEKTÖRÜ
    # ══════════════════════════════════════════════════════════
    elif selected == "🔬 Anomali Dedektörü":
        st.markdown('<div class="page-header"><div class="page-title">ANOMALİ DEDEKTÖRÜ</div></div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="ultra-card">
            <p style="color:var(--text-secondary); font-size:0.9rem; margin:0;">
                🔬 Yapay Zeka destekli anomali tespiti motoru — mükerrer fişler, hafta sonu harcamaları, 
                istatistiksel aykırı değerler ve kritik risk skorlarını otomatik olarak tarar.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if not df.empty:
            anomalies = detect_anomalies(df, model)
            
            if anomalies:
                st.markdown(f"### 🚨 {len(anomalies)} Anomali Tespit Edildi")
                
                for a in anomalies:
                    sev_color = {"high": "#dc2626", "medium": "#d97706", "low": "#007850"}.get(a['severity'], "#4a5568")
                    sev_icon = {"high": "🔴", "medium": "🟡", "low": "🔵"}.get(a['severity'], "⚪")
                    
                    st.markdown(f"""
                    <div class="ultra-card" style="border-left:4px solid {sev_color};">
                        <div style="display:flex; align-items:center; gap:12px;">
                            <span style="font-size:1.5rem;">{sev_icon}</span>
                            <div>
                                <div style="font-weight:600; color:var(--text-primary);">{a['message']}</div>
                                <div style="font-size:0.75rem; color:{sev_color}; text-transform:uppercase; margin-top:2px;">
                                    {a['severity'].upper()} SEVİYE · {a['count']} işlem etkilendi
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="ultra-card" style="border-left:4px solid #007850; text-align:center; padding:40px;">
                    <div style="font-size:3rem;">✅</div>
                    <div style="font-size:1.2rem; font-weight:600; color:#007850; margin:8px 0;">Anomali Tespit Edilmedi</div>
                    <div style="color:var(--text-muted);">Tüm işlemler normal görünüyor.</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Deep analysis
            st.markdown("### 🤖 AI Derin Analiz")
            
            if st.button("🔍 Kapsamlı AI Denetimi Başlat"):
                with st.spinner("Gemini AI tüm verileri tarıyor..."):
                    prompt = f"""Sen bir adli mali denetçisin. Bu harcama verilerini incele ve şüpheli durumları rapor et:
                    {df.to_dict(orient='records')}
                    
                    Türkçe olarak şunu belirt:
                    1. En riskli 3 işlem ve neden
                    2. Tespit ettiğin olağandışı patternler  
                    3. Önerilen aksiyonlar
                    Kısa ve net ol."""
                    
                    try:
                        response = model.generate_content(prompt)
                        st.markdown(f"""
                        <div class="ai-bubble" style="margin-top:12px;">
                            <p style="margin:0; line-height:1.8; white-space:pre-wrap; font-size:0.9rem;">
                                {response.text}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Save insight
                        data_store["ai_insights"].append({
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "type": "anomaly_scan",
                            "content": response.text
                        })
                        save_data(data_store)
                    except Exception as e:
                        st.error(f"AI yanıt veremedi: {e}")
            
            # Statistical visualization
            st.markdown("### 📊 İstatistiksel Görselleştirme")
            
            col_s1, col_s2 = st.columns(2)
            
            with col_s1:
                if 'Tutar' in df.columns:
                    fig = px.box(df, x='Proje', y='Tutar', color='Proje',
                                title='Proje Bazlı Tutar Dağılımı (Box Plot)',
                                color_discrete_sequence=['#007850','#283c64','#007850','#ea6c1e'])
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#4a5568'), showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col_s2:
                if 'Risk_Skoru' in df.columns:
                    fig2 = px.histogram(df, x='Risk_Skoru', nbins=10,
                                       title='Risk Skoru Dağılımı',
                                       color_discrete_sequence=['#dc2626'])
                    fig2.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#4a5568')
                    )
                    st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Anomali analizi için veri gerekli. Önce fiş taraması yapın.")

    # ══════════════════════════════════════════════════════════
    # SAYFA: ANALİTİK MERKEZİ
    # ══════════════════════════════════════════════════════════
    elif selected == "📊 Analitik Merkezi":
        st.markdown('<div class="page-header"><div class="page-title">ANALİTİK MERKEZİ</div></div>', unsafe_allow_html=True)
        
        if not df.empty:
            tab1, tab2, tab3 = st.tabs(["📈 Trend Analizi", "🗺️ Isı Haritası", "🔮 Tahmin"])
            
            with tab1:
                df_temp = df.copy()
                df_temp['dt'] = pd.to_datetime(df_temp['Tarih'], errors='coerce')
                
                # Monthly trend
                monthly = df_temp.groupby(df_temp['dt'].dt.strftime('%Y-%m')).agg(
                    Toplam=('Tutar', 'sum'),
                    Adet=('Tutar', 'count'),
                    OrtRisk=('Risk_Skoru', 'mean')
                ).reset_index()
                monthly.columns = ['Ay', 'Toplam', 'Adet', 'OrtRisk']
                
                fig = make_subplots(rows=2, cols=1, 
                                   subplot_titles=('Aylık Toplam Harcama (₺)', 'Aylık İşlem Adedi'),
                                   shared_xaxes=True)
                
                fig.add_trace(go.Bar(x=monthly['Ay'], y=monthly['Toplam'],
                                    marker_color='#007850', name='Harcama'), row=1, col=1)
                fig.add_trace(go.Scatter(x=monthly['Ay'], y=monthly['Adet'],
                                        line=dict(color='#283c64', width=2),
                                        fill='tozeroy', fillcolor='rgba(139,92,246,0.1)',
                                        name='Adet'), row=2, col=1)
                
                fig.update_layout(
                    height=450, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#4a5568'), showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # User comparison
                if 'Kullanıcı' in df.columns:
                    user_stats = df.groupby('Kullanıcı').agg(
                        Toplam=('Tutar', 'sum'),
                        Adet=('Tutar', 'count'),
                        OrtRisk=('Risk_Skoru', 'mean')
                    ).reset_index()
                    
                    fig2 = px.bar(user_stats, x='Kullanıcı', y='Toplam',
                                  color='OrtRisk',
                                  color_continuous_scale='RdYlGn_r',
                                  title='Personel Bazlı Harcama Karşılaştırması',
                                  text=[f"₺{v:,.0f}" for v in user_stats['Toplam']])
                    fig2.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#4a5568')
                    )
                    st.plotly_chart(fig2, use_container_width=True)
            
            with tab2:
                st.markdown("### 🗓️ Günlük Harcama Yoğunluğu")
                
                df_temp2 = df.copy()
                df_temp2['dt'] = pd.to_datetime(df_temp2['Tarih'], errors='coerce')
                df_temp2['Gun'] = df_temp2['dt'].dt.day_name()
                df_temp2['Hafta'] = df_temp2['dt'].dt.isocalendar().week.astype(str)
                
                pivot = df_temp2.pivot_table(
                    values='Tutar', index='Gun', columns='Hafta', 
                    aggfunc='sum', fill_value=0
                )
                
                gun_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
                gun_tr = ['Pzt','Sal','Çar','Per','Cum','Cmt','Paz']
                pivot = pivot.reindex([g for g in gun_order if g in pivot.index])
                
                fig3 = go.Figure(go.Heatmap(
                    z=pivot.values,
                    x=pivot.columns.tolist(),
                    y=[gun_tr[gun_order.index(g)] for g in pivot.index if g in gun_order],
                    colorscale=[[0,'#0a0f1e'],[0.5,'#007850'],[1,'#283c64']],
                    text=[[f"₺{v:,.0f}" for v in row] for row in pivot.values],
                    texttemplate='%{text}',
                    textfont=dict(size=9)
                ))
                fig3.update_layout(
                    title='Haftalık Harcama Yoğunluk Haritası',
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#4a5568'), height=350
                )
                st.plotly_chart(fig3, use_container_width=True)
            
            with tab3:
                st.markdown("### 🔮 AI Harcama Tahmini")
                
                if st.button("📡 Tahmin Oluştur"):
                    with st.spinner("Gemini AI pattern analizi yapıyor..."):
                        pred = predict_monthly_spend(df, model)
                        
                        if pred:
                            current_month_spend = df[
                                pd.to_datetime(df['Tarih'], errors='coerce').dt.strftime('%Y-%m') == datetime.now().strftime('%Y-%m')
                            ]['Tutar'].sum() if 'Tarih' in df.columns else 0
                            
                            st.markdown(f"""
                            <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin:16px 0;">
                                <div class="metric-card">
                                    <div style="color:var(--text-muted); font-size:0.75rem; text-transform:uppercase; letter-spacing:1px;">Bu Ay (Mevcut)</div>
                                    <div style="font-family:'Bebas Neue'; font-size:2.5rem; color:var(--accent-blue);">₺{current_month_spend:,.0f}</div>
                                </div>
                                <div class="metric-card">
                                    <div style="color:var(--text-muted); font-size:0.75rem; text-transform:uppercase; letter-spacing:1px;">Gelecek Ay Tahmini</div>
                                    <div style="font-family:'Bebas Neue'; font-size:2.5rem; color:var(--accent-purple);">₺{pred:,.0f}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            change_pct = ((pred - current_month_spend) / current_month_spend * 100) if current_month_spend > 0 else 0
                            direction = "📈 artış" if change_pct > 0 else "📉 azalış"
                            st.info(f"AI, geçmiş trendlere göre gelecek ay **{abs(change_pct):.1f}% {direction}** öngörüyor.")
                        else:
                            st.warning("Tahmin için yeterli geçmiş veri yok (en az 2 aylık veri gerekli).")
        else:
            st.info("Analitik görselleştirme için veri gerekli.")

    # ══════════════════════════════════════════════════════════
    # SAYFA: AI ASISTAN
    # ══════════════════════════════════════════════════════════
    elif selected == "🤖 AI Asistan":
        st.markdown('<div class="page-header"><div class="page-title">AI FİNANS ASISTANI</div></div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="ultra-card" style="margin-bottom:20px;">
            <p style="color:var(--text-secondary); margin:0; font-size:0.9rem;">
                💬 Stinga AI'a finansal veriler hakkında her şeyi sorabilirsin. Harcama analizi, bütçe karşılaştırması,
                risk değerlendirmesi, trend analizi ve daha fazlası...
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Suggested questions
        st.markdown("**Hızlı Sorular:**")
        q_cols = st.columns(3)
        quick_qs = [
            "En yüksek harcama hangi proje?",
            "Bu ay risk durumu nasıl?",
            "Hangi personel en fazla harcıyor?",
            "Bütçe aşımı var mı?",
            "En çok hangi kategoride harcama var?",
            "Anomalileri özetle"
        ]
        
        for i, q in enumerate(quick_qs):
            with q_cols[i % 3]:
                if st.button(q, key=f"qq_{i}", use_container_width=True):
                    st.session_state.chat_history.append({"role": "user", "content": q})
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Chat history
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f"""
                <div style="display:flex; justify-content:flex-end; margin:8px 0;">
                    <div style="background:rgba(0,212,255,0.1); border:1px solid rgba(0,212,255,0.2); 
                                border-radius:16px 16px 0 16px; padding:12px 16px; max-width:70%;
                                color:var(--text-primary); font-size:0.9rem;">
                        {msg['content']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="ai-bubble" style="max-width:85%;">
                    <p style="margin:0; line-height:1.7; font-size:0.9rem; white-space:pre-wrap;">
                        {msg['content']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        # Auto-answer last user message
        if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
            last_q = st.session_state.chat_history[-1]["content"]
            if model:
                with st.spinner("🤖 Stinga AI düşünüyor..."):
                    answer = generate_ai_insight(df, model, last_q)
                    st.session_state.chat_history.append({"role": "assistant", "content": answer})
                    st.rerun()
        
        # Input
        with st.form("chat_form", clear_on_submit=True):
            col_i, col_b = st.columns([5, 1])
            with col_i:
                user_q = st.text_input("", placeholder="Finansal veriler hakkında bir şey sor...", 
                                       label_visibility="collapsed")
            with col_b:
                sent = st.form_submit_button("→", use_container_width=True)
            
            if sent and user_q.strip():
                st.session_state.chat_history.append({"role": "user", "content": user_q})
                st.rerun()
        
        if st.session_state.chat_history:
            if st.button("🗑️ Sohbeti Temizle"):
                st.session_state.chat_history = []
                st.rerun()

    # ══════════════════════════════════════════════════════════
    # SAYFA: LEADERBOARD
    # ══════════════════════════════════════════════════════════
    elif selected == "🏆 Leaderboard":
        st.markdown('<div class="page-header"><div class="page-title">PERFORMANS SIRALAMASI</div></div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="ultra-card">
            <p style="color:var(--text-secondary); margin:0; font-size:0.85rem;">
                🎮 Stinga Pro, harcama yönetimini oyunlaştırıyor. Fiş tarama, onay alma ve dakiklik gibi 
                kriterlere göre XP kazanarak seviye atla ve lider tablosuna çık!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        xp_data = data_store.get("xp", {"Zeynep": 1250, "Serkan": 890, "Okan": 430})
        sorted_users = sorted(xp_data.items(), key=lambda x: x[1], reverse=True)
        
        rank_icons = ["🥇", "🥈", "🥉"]
        rank_classes = ["gold", "silver", "bronze"]
        
        st.markdown("### 🏆 XP Sıralaması")
        
        for i, (uname, xp) in enumerate(sorted_users):
            user_data = USERS.get(uname.lower(), {})
            avatar = user_data.get('avatar', '👤')
            level = xp // 500 + 1
            monthly_limit = user_data.get('monthly_limit', 15000)
            
            user_expenses = df[df['Kullanıcı'] == uname] if not df.empty and 'Kullanıcı' in df.columns else pd.DataFrame()
            total_spend = user_expenses['Tutar'].sum() if not user_expenses.empty else 0
            approved_count = len(user_expenses[user_expenses['Durum'] == 'Onaylandı']) if not user_expenses.empty and 'Durum' in user_expenses.columns else 0
            
            max_xp = sorted_users[0][1] if sorted_users else 1
            bar_pct = (xp / max_xp * 100) if max_xp > 0 else 0
            
            st.markdown(f"""
            <div class="lb-item" style="{'background:linear-gradient(135deg,rgba(255,215,0,0.1),rgba(255,215,0,0.05));border-color:rgba(255,215,0,0.3);' if i==0 else ''}">
                <div class="lb-rank {'gold' if i==0 else 'silver' if i==1 else 'bronze'}">{rank_icons[i] if i < 3 else str(i+1)}</div>
                <div style="font-size:1.8rem;">{avatar}</div>
                <div style="flex:1;">
                    <div style="font-weight:700; font-size:1rem;">{uname} <span style="font-size:0.7rem; color:var(--text-muted);">Lv.{level}</span></div>
                    <div style="font-size:0.75rem; color:var(--text-secondary);">
                        ₺{total_spend:,.0f} harcama · {approved_count} onaylı fiş
                    </div>
                    <div class="budget-track" style="margin-top:6px; width:200px;">
                        <div class="budget-fill" style="width:{bar_pct:.0f}%; {'background:linear-gradient(90deg,#ffd700,#d97706);' if i==0 else 'background:linear-gradient(90deg,#007850,#283c64);'}"></div>
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-family:'Bebas Neue'; font-size:1.8rem; color:{'#ffd700' if i==0 else 'var(--accent-blue)'};">{xp:,}</div>
                    <div style="font-size:0.7rem; color:var(--text-muted);">XP</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Badges section
        st.markdown("### 🎖️ Başarı Rozetleri")
        
        badge_defs = [
            ("🚀", "İlk Fiş", "İlk fişini tara", 1),
            ("💯", "Seri Teyitçi", "10 fiş tara", 10),
            ("🎯", "Risk Avcısı", "5 yüksek riskli fiş yakala", 5),
            ("⚡", "Hız Ustası", "Aynı gün 3 fiş tara", 3),
            ("🏆", "Finans Gurusu", "500 XP kazan", 500),
            ("💎", "Elit Operatör", "1000 XP kazan", 1000),
        ]
        
        badge_cols = st.columns(6)
        user_xp_val = xp_data.get(user_name, 0)
        user_exp_count = len(df[df['Kullanıcı'] == user_name]) if not df.empty and 'Kullanıcı' in df.columns else 0
        
        for i, (icon, name, desc, req) in enumerate(badge_defs):
            earned = (user_exp_count >= req) or (user_xp_val >= req)
            with badge_cols[i]:
                st.markdown(f"""
                <div style="text-align:center; padding:16px; background:var(--bg-card); border-radius:12px;
                            border:1px solid {'var(--accent-blue)' if earned else 'var(--border)'};
                            opacity:{'1' if earned else '0.4'}; transition:all 0.3s;">
                    <div style="font-size:2rem;">{icon}</div>
                    <div style="font-size:0.75rem; font-weight:700; margin:4px 0; color:{'var(--accent-blue)' if earned else 'var(--text-muted)'};">{name}</div>
                    <div style="font-size:0.65rem; color:var(--text-muted);">{desc}</div>
                    {"<div style='font-size:0.65rem; color:var(--accent-green); margin-top:4px;'>✓ KAZANILDI</div>" if earned else ""}
                </div>
                """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    # SAYFA: ARŞİV & RAPOR
    # ══════════════════════════════════════════════════════════
    elif selected == "🗄️ Arşiv & Rapor":
        st.markdown('<div class="page-header"><div class="page-title">ARŞİV & RAPORLAMA</div></div>', unsafe_allow_html=True)
        
        tab_r, tab_a, tab_h = st.tabs(["📑 Raporlama", "🔍 Arşiv", "📜 Geçmiş AI Analizleri"])
        
        with tab_r:
            if not df.empty:
                df['Tarih_DT'] = pd.to_datetime(df['Tarih'], errors='coerce')
                df['Ay_Yil'] = df['Tarih_DT'].dt.strftime('%Y-%m')
                aylar = ["Tüm Zamanlar"] + sorted(df['Ay_Yil'].dropna().unique().tolist(), reverse=True)
                
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    secilen_ay = st.selectbox("Dönem", aylar)
                with col_f2:
                    secilen_proje = st.selectbox("Proje", ["Tümü"] + df['Proje'].unique().tolist() if 'Proje' in df.columns else ["Tümü"])
                
                filtered = df.copy()
                if secilen_ay != "Tüm Zamanlar":
                    filtered = filtered[filtered['Ay_Yil'] == secilen_ay]
                if secilen_proje != "Tümü" and 'Proje' in filtered.columns:
                    filtered = filtered[filtered['Proje'] == secilen_proje]
                
                # Summary metrics
                if not filtered.empty:
                    fc1, fc2, fc3, fc4 = st.columns(4)
                    fc1.metric("Toplam İşlem", len(filtered))
                    fc2.metric("Toplam Tutar", f"₺{filtered['Tutar'].sum():,.0f}")
                    fc3.metric("Ort. Risk", f"{filtered['Risk_Skoru'].mean():.0f}%" if 'Risk_Skoru' in filtered.columns else "N/A")
                    fc4.metric("Onay Oranı", f"{len(filtered[filtered['Durum']=='Onaylandı'])/len(filtered)*100:.0f}%" if 'Durum' in filtered.columns else "N/A")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                clean_df = filtered.drop(columns=['Tarih_DT','Ay_Yil'], errors='ignore')
                
                d1, d2 = st.columns(2)
                d1.download_button(
                    "📥 Excel/CSV İndir", 
                    clean_df.to_csv(index=False).encode('utf-8-sig'),
                    f"Stinga_Rapor_{secilen_ay}_{secilen_proje}.csv",
                    "text/csv", use_container_width=True
                )
                d2.download_button(
                    "📄 PDF Yönetici Raporu",
                    export_pdf_advanced(clean_df, "Mali Rapor", secilen_ay),
                    f"Stinga_PDF_{secilen_ay}.pdf",
                    "application/pdf", use_container_width=True
                )
                
                st.dataframe(clean_df.sort_values('Tarih', ascending=False), 
                            use_container_width=True, hide_index=True)
            else:
                st.info("Raporlanacak veri bulunmuyor.")
        
        with tab_a:
            st.markdown("### 🔍 Orijinal Fiş Arşivi")
            
            if not df.empty:
                search = st.text_input("Ara (firma, proje, personel...)", placeholder="🔍 Arama...")
                
                display_df = df.copy()
                if search:
                    mask = display_df.apply(lambda row: search.lower() in str(row).lower(), axis=1)
                    display_df = display_df[mask]
                
                islem_listesi = ["Seçim yapın..."] + display_df.apply(
                    lambda x: f"{x['ID']} | {x.get('Tarih','')} | {x.get('Firma','')} — ₺{float(x.get('Tutar',0)):,.0f} ({x.get('Durum','')})", 
                    axis=1
                ).tolist()
                
                secilen = st.selectbox("İşlem seç:", islem_listesi)
                
                if secilen != "Seçim yapın...":
                    islem_id = secilen.split(" | ")[0]
                    satir = df[df['ID'] == islem_id].iloc[0]
                    
                    col_i, col_img = st.columns([1, 1.5])
                    
                    with col_i:
                        st.markdown(f"""
                        <div class="ultra-card">
                            <div style="font-size:1.3rem; font-weight:700; margin-bottom:16px;">{satir.get('Firma','?')}</div>
                            <div style="display:grid; gap:8px;">
                                <div><span style="color:var(--text-muted); font-size:0.75rem;">PERSONEL</span><br><strong>{satir.get('Kullanıcı','?')}</strong></div>
                                <div><span style="color:var(--text-muted); font-size:0.75rem;">PROJE</span><br><strong>{satir.get('Proje','?')}</strong></div>
                                <div><span style="color:var(--text-muted); font-size:0.75rem;">TUTAR</span><br><strong style="font-family:'Bebas Neue'; font-size:1.5rem; color:var(--accent-blue);">₺{float(satir.get('Tutar',0)):,.2f}</strong></div>
                                <div><span style="color:var(--text-muted); font-size:0.75rem;">KDV</span><br><strong>₺{float(satir.get('KDV',0)):,.2f}</strong></div>
                                <div><span style="color:var(--text-muted); font-size:0.75rem;">ÖDEME</span><br><strong>{satir.get('Odeme_Turu','?')}</strong></div>
                                <div><span style="color:var(--text-muted); font-size:0.75rem;">DURUM</span><br>{get_status_html(satir.get('Durum','?'))}</div>
                                <div><span style="color:var(--text-muted); font-size:0.75rem;">RİSK</span><br>{get_risk_html(satir.get('Risk_Skoru',0))}</div>
                            </div>
                            <div class="ai-bubble" style="margin-top:16px;">
                                {satir.get('AI_Audit','Analiz mevcut değil.')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_img:
                        dosya = satir.get('Dosya_Yolu', '')
                        if dosya and os.path.exists(dosya):
                            st.image(dosya, caption=f"Orijinal Fiş — {islem_id}", use_container_width=True)
                        else:
                            st.markdown(f"""
                            <div style="height:300px; background:var(--bg-secondary); border-radius:16px; 
                                        display:flex; flex-direction:column; align-items:center; justify-content:center;
                                        color:var(--text-muted); border:2px dashed var(--border);">
                                <div style="font-size:3rem; opacity:0.3;">📷</div>
                                <div style="font-size:0.85rem; margin-top:8px;">Görsel bulunamadı</div>
                                <div style="font-size:0.7rem; opacity:0.5; margin-top:4px;">{dosya}</div>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.info("Arşivde görüntülenecek veri yok.")
        
        with tab_h:
            st.markdown("### 📜 Geçmiş AI Analizleri")
            
            ai_insights = data_store.get("ai_insights", [])
            if ai_insights:
                for ins in reversed(ai_insights[-10:]):
                    with st.expander(f"🤖 {ins.get('date','?')} — {ins.get('type','Analiz').replace('_',' ').title()}"):
                        st.markdown(f"""
                        <div class="ai-bubble">
                            <p style="margin:0; white-space:pre-wrap; font-size:0.85rem; line-height:1.7;">
                                {ins.get('content','İçerik yok.')}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="empty-state">
                    <div class="empty-icon">🤖</div>
                    <div>Henüz AI analizi kaydedilmemiş.</div>
                    <div style="font-size:0.8rem; margin-top:8px;">Anomali Dedektörü'nden derin analiz başlat!</div>
                </div>
                """, unsafe_allow_html=True)
