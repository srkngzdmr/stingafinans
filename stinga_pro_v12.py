# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════╗
# ║          STINGA PRO v14.0 - ULTRA EDITION                   ║
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
    page_title="Stinga Pro v14 ⚡",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# ─── ULTRA DARK THEME CSS ─────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&family=JetBrains+Mono:wght@400;500;700&display=swap');

/* ════════════════════════════════════════════════════════
   STINGA PRO — LIGHT THEME (21st.dev inspired)
   Sidebar  : #08090c (siyah)
   Content  : #f8f9fb (açık)
   Green    : #11855B  Navy: #2F3C6E
════════════════════════════════════════════════════════ */

:root {
    --sg:        #11855B;
    --sg-hi:     #17a870;
    --sg-lo:     #0c6344;
    --sn:        #2F3C6E;
    --sn-hi:     #3d4e8a;

    /* SIDEBAR — siyah */
    --sb:        #08090c;
    --sb-s:      #0e1016;
    --sb-bdr:    rgba(17,133,91,0.16);

    /* CONTENT — açık */
    --bg:        #f4f6f8;
    --bg-2:      #eef0f3;
    --bg-card:   #ffffff;
    --bg-hover:  #f0f4f1;

    /* TEXT */
    --t1:  #0f1923;
    --t2:  #3d5260;
    --t3:  #7a96a4;

    /* ACCENTS */
    --amber: #d97706;
    --red:   #dc2626;
    --cyan:  #0891b2;

    --shadow: 0 1px 4px rgba(15,25,35,0.08), 0 4px 16px rgba(15,25,35,0.06);
    --shadow-lg: 0 4px 12px rgba(15,25,35,0.1), 0 16px 48px rgba(15,25,35,0.08);
    --bdr:   rgba(17,133,91,0.15);
    --bdr-m: rgba(17,133,91,0.3);
    --glow:  0 4px 20px rgba(17,133,91,0.15);
}

* { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background: var(--bg) !important;
    color: var(--t1) !important;
}

.stApp {
    background:
        radial-gradient(ellipse 70% 50% at 0% 0%,   rgba(17,133,91,0.05) 0%, transparent 55%),
        radial-gradient(ellipse 60% 45% at 100% 100%, rgba(47,60,110,0.06) 0%, transparent 55%),
        var(--bg) !important;
}

/* ── SIDEBAR ─────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--sb) !important;
    border-right: 1px solid rgba(17,133,91,0.14) !important;
    box-shadow: 4px 0 24px rgba(0,0,0,0.25) !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }
[data-testid="stSidebar"] * { color: inherit !important; }

[data-testid="stSidebar"] .stRadio > div { gap: 0 !important; }
[data-testid="stSidebar"] .stRadio label {
    display: flex !important; align-items: center !important;
    padding: 11px 16px !important; margin: 1px 8px !important;
    border-radius: 9px !important; border: 1px solid transparent !important;
    background: transparent !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.87rem !important; font-weight: 600 !important;
    color: #7a9a8a !important; cursor: pointer !important;
    transition: all 0.16s ease !important; letter-spacing: 0.01em !important;
    position: relative !important;
}
[data-testid="stSidebar"] .stRadio label::before {
    content: ''; position: absolute; left: 0; top: 18%; bottom: 18%;
    width: 3px; border-radius: 0 3px 3px 0;
    background: var(--sg); opacity: 0; transition: opacity 0.15s;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(17,133,91,0.1) !important;
    color: #c8e8d8 !important;
    border-color: rgba(17,133,91,0.2) !important;
    transform: translateX(4px) !important;
}
[data-testid="stSidebar"] .stRadio label:hover::before { opacity: 0.6 !important; }
[data-testid="stSidebar"] .stRadio label[data-checked="true"] {
    background: linear-gradient(90deg,rgba(17,133,91,0.18),rgba(17,133,91,0.06)) !important;
    color: #3ecf8e !important;
    border-color: rgba(17,133,91,0.3) !important; font-weight: 700 !important;
}
[data-testid="stSidebar"] .stRadio label[data-checked="true"]::before { opacity: 1 !important; }
[data-testid="stSidebar"] .stRadio input[type="radio"] { display: none !important; }
[data-testid="stSidebar"] .stRadio > div > label > div:first-child { display: none !important; }

/* ── LOGO ANIMATION ──────────────────── */
.slogo-frame {
    display: inline-block; border-radius: 50%; position: relative;
    animation: sBreath 4s ease-in-out infinite;
}
@keyframes sBreath {
    0%,100% { transform: scale(0.97); filter: drop-shadow(0 0 0px rgba(17,133,91,0)); }
    50%     { transform: scale(1.06); filter: drop-shadow(0 0 16px rgba(17,133,91,0.7)); }
}
.slogo-frame::after {
    content: ''; position: absolute; inset: -5px; border-radius: 50%;
    border: 1.5px solid rgba(17,133,91,0.5);
    animation: sRing 4s ease-in-out infinite; pointer-events: none;
}
@keyframes sRing {
    0%,100% { transform: scale(1); opacity: 0.6; }
    50%     { transform: scale(1.18); opacity: 0; }
}
.slogo-core {
    background: #08090c; border-radius: 50%; padding: 7px;
    display: flex; align-items: center; justify-content: center;
    width: 86px; height: 86px;
}
.slogo-core img { width: 70px; height: 70px; object-fit: contain; border-radius: 50%; }

/* ── USER CARD ───────────────────────── */
.suser-card {
    margin: 8px 10px 6px; padding: 14px 15px;
    background: var(--sb-s);
    border: 1px solid rgba(17,133,91,0.2); border-radius: 14px;
    transition: all 0.22s ease; position: relative; overflow: hidden;
}
.suser-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--sg-lo), var(--sg), var(--sg-lo)); opacity: 0.8;
}
.suser-card:hover { border-color: rgba(17,133,91,0.4); box-shadow: 0 4px 16px rgba(17,133,91,0.15); transform: translateY(-1px); }
.suser-top { display: flex; align-items: center; gap: 11px; }
.suser-ava {
    width: 44px; height: 44px; border-radius: 11px;
    background: linear-gradient(135deg,rgba(17,133,91,0.2),rgba(47,60,110,0.3));
    border: 1px solid rgba(17,133,91,0.3);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.4rem; transition: transform 0.25s ease;
}
.suser-card:hover .suser-ava { transform: scale(1.08) rotate(-4deg); }
.suser-name { font-size: 0.93rem; font-weight: 700; color: #f0f4f2 !important; }
.suser-role { font-family: 'JetBrains Mono',monospace; font-size: 0.59rem; margin-top: 3px; letter-spacing: 0.1em; }
.sxp-row { display:flex; justify-content:space-between; font-family:'JetBrains Mono',monospace; font-size:0.58rem; color:#4a6a5a !important; margin:10px 0 4px; }
.sxp-track { height: 3px; background: rgba(255,255,255,0.07); border-radius:99px; position: relative; overflow: visible; }
.sxp-fill { height: 100%; border-radius:99px; background: linear-gradient(90deg,var(--sg-lo),var(--sg)); position: relative; }
.sxp-fill::after { content:''; position:absolute; right:-1px; top:50%; transform:translateY(-50%); width:7px; height:7px; background:var(--sg); border-radius:50%; box-shadow:0 0 7px var(--sg); }
.smeta { display:flex; justify-content:space-between; margin-top:9px; font-family:'JetBrains Mono',monospace; font-size:0.58rem; color:#4a6a5a !important; }
.ssep { height:1px; background:linear-gradient(90deg,transparent,rgba(17,133,91,0.2),transparent); margin:5px 12px; }

.snotif {
    margin:5px 10px; padding:9px 13px;
    background:rgba(220,38,38,0.08); border:1px solid rgba(220,38,38,0.22);
    border-radius:10px; display:flex; align-items:center; gap:8px;
    animation:snotifP 2.5s ease-in-out infinite;
}
.snotif:hover { background:rgba(220,38,38,0.14); border-color:rgba(220,38,38,0.38); }
@keyframes snotifP { 0%,100%{box-shadow:none;}50%{box-shadow:0 0 0 4px rgba(220,38,38,0.07);} }
.snotif-lbl { font-size:0.72rem; font-weight:600; color:#fca5a5 !important; flex:1; }
.snotif-num { background:var(--red); color:#fff !important; font-size:0.58rem; font-weight:700; padding:2px 6px; border-radius:99px; font-family:'JetBrains Mono',monospace; }
.snav-hdr { font-family:'JetBrains Mono',monospace; font-size:0.51rem; color:#385048 !important; letter-spacing:0.2em; padding:6px 18px 3px; text-transform:uppercase; }

.slimit { margin:5px 10px 10px; padding:13px 15px; background:var(--sb-s); border:1px solid rgba(17,133,91,0.16); border-radius:14px; transition:all 0.22s ease; }
.slimit:hover { border-color:rgba(17,133,91,0.3); }
.slimit-lbl { font-family:'JetBrains Mono',monospace; font-size:0.51rem; color:#385048 !important; letter-spacing:0.16em; text-transform:uppercase; margin-bottom:6px; }
.slimit-row { display:flex; justify-content:space-between; align-items:baseline; margin-bottom:6px; }
.slimit-pct { font-size:1.3rem; font-weight:800; font-family:'Plus Jakarta Sans',sans-serif; }
.slimit-val { font-family:'JetBrains Mono',monospace; font-size:0.54rem; color:#4a6a5a !important; }
.slimit-bar { height:4px; background:rgba(255,255,255,0.07); border-radius:99px; overflow:hidden; }

/* ════════════════════════════════════════
   MAIN CONTENT — LIGHT
════════════════════════════════════════ */

.ultra-card {
    background: var(--bg-card); border: 1px solid rgba(0,0,0,0.07);
    border-radius: 16px; padding: 24px; margin: 10px 0;
    position: relative; overflow: hidden;
    transition: all 0.22s ease; box-shadow: var(--shadow);
}
.ultra-card::before {
    content: ''; position: absolute; top:0; left:0; right:0; height:2px;
    background: linear-gradient(90deg,var(--sg),var(--sn-hi),var(--sg));
    opacity:0; transition:opacity 0.22s;
}
.ultra-card:hover { border-color: var(--bdr-m); box-shadow: var(--glow); transform: translateY(-2px); }
.ultra-card:hover::before { opacity: 1; }

.metric-card {
    background: var(--bg-card); border: 1px solid rgba(0,0,0,0.07);
    border-radius: 16px; padding: 22px; text-align: center;
    position: relative; overflow: hidden;
    transition: all 0.22s ease; box-shadow: var(--shadow);
}
.metric-card:hover { transform: translateY(-4px); border-color: var(--bdr-m); box-shadow: var(--glow); }
.metric-value { font-size: 2rem; font-weight: 800; line-height:1.1; margin:6px 0 4px; color:var(--t1); }
.metric-label { font-size:0.67rem; font-weight:700; color:var(--t3); text-transform:uppercase; letter-spacing:0.13em; }

.risk-badge { display:inline-block; padding:4px 12px; border-radius:20px; font-family:'JetBrains Mono',monospace; font-size:0.72rem; font-weight:700; }
.risk-low  { background:rgba(17,133,91,0.1);  color:var(--sg);   border:1px solid rgba(17,133,91,0.25); }
.risk-mid  { background:rgba(217,119,6,0.1);  color:var(--amber);border:1px solid rgba(217,119,6,0.25); }
.risk-high { background:rgba(220,38,38,0.1);  color:var(--red);  border:1px solid rgba(220,38,38,0.25); }

.stButton > button {
    background: linear-gradient(135deg,var(--sg-lo) 0%,var(--sg) 100%) !important;
    color:#fff !important; border:none !important; border-radius:10px !important;
    font-family:'Plus Jakarta Sans',sans-serif !important; font-weight:700 !important;
    font-size:0.88rem !important; letter-spacing:0.02em !important;
    transition:all 0.2s ease !important; padding:0.58rem 1.3rem !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg,var(--sg),var(--sg-hi)) !important;
    transform:translateY(-2px) !important; box-shadow:0 8px 20px rgba(17,133,91,0.35) !important;
}

.page-header { display:flex; align-items:center; gap:16px; margin-bottom:28px; padding-bottom:16px; border-bottom:1px solid rgba(0,0,0,0.08); }
.page-title { font-size:2.4rem; font-weight:800; letter-spacing:-0.02em; line-height:1; color:var(--t1); }

[data-testid="stDataFrame"] { border:1px solid rgba(0,0,0,0.08) !important; border-radius:14px !important; overflow:hidden !important; }

.stTextInput > div > div > input,
.stSelectbox > div > div > div,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #fff !important; border:1px solid rgba(0,0,0,0.12) !important;
    border-radius:10px !important; color:var(--t1) !important;
    font-family:'Plus Jakarta Sans',sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color:var(--sg) !important; box-shadow:0 0 0 3px rgba(17,133,91,0.12) !important;
}

.stTabs [data-baseweb="tab-list"] { background:var(--bg-2) !important; border-radius:12px !important; padding:4px !important; border:1px solid rgba(0,0,0,0.07) !important; }
.stTabs [data-baseweb="tab"] { background:transparent !important; border-radius:9px !important; color:var(--t3) !important; font-family:'Plus Jakarta Sans',sans-serif !important; font-weight:600 !important; transition:all 0.18s !important; }
.stTabs [aria-selected="true"] { background:#fff !important; color:var(--sg) !important; box-shadow:var(--shadow) !important; }

.streamlit-expanderHeader { background:#fff !important; border:1px solid rgba(0,0,0,0.08) !important; border-radius:10px !important; color:var(--t1) !important; }

.stSuccess { background:rgba(17,133,91,0.08) !important; border-left:3px solid var(--sg) !important; color:var(--t1) !important; }
.stError   { background:rgba(220,38,38,0.07) !important; border-left:3px solid var(--red) !important; }
.stWarning { background:rgba(217,119,6,0.07) !important; border-left:3px solid var(--amber) !important; }
.stInfo    { background:rgba(8,145,178,0.07) !important; border-left:3px solid var(--cyan) !important; }

.stProgress > div > div { background:linear-gradient(90deg,var(--sg-lo),var(--sg)) !important; }
hr { border-color:rgba(0,0,0,0.07) !important; }

::-webkit-scrollbar { width:5px; }
::-webkit-scrollbar-track { background:var(--bg); }
::-webkit-scrollbar-thumb { background:rgba(17,133,91,0.2); border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background:rgba(17,133,91,0.4); }

header[data-testid="stHeader"] { background:var(--bg) !important; border-bottom:1px solid rgba(0,0,0,0.07) !important; box-shadow:0 1px 4px rgba(0,0,0,0.05) !important; }
[data-testid="stDecoration"] { display:none !important; }
.block-container { background:transparent !important; padding-top:3rem !important; }
section[data-testid="stMain"] > div { background:transparent !important; }

[data-testid="stForm"] { background:#fff !important; border:1px solid rgba(0,0,0,0.09) !important; border-radius:20px !important; padding:28px !important; box-shadow:var(--shadow-lg) !important; }
.login-container { max-width:440px; margin:0 auto; padding:48px 40px; background:#fff; border:1px solid rgba(0,0,0,0.08); border-radius:24px; box-shadow:var(--shadow-lg); }
.logo-circle { display:inline-flex; align-items:center; justify-content:center; background:#fff; border-radius:50%; padding:10px; box-shadow:0 4px 20px rgba(17,133,91,0.25); }
.sidebar-logo-wrap { display:inline-flex; align-items:center; justify-content:center; background:#fff; border-radius:50%; padding:6px; }

/* LOGIN PAGE — animated gradient mesh background */
.login-bg {
    position: fixed; inset: 0; z-index: -1; overflow: hidden;
    background: linear-gradient(135deg, #f0f7f4 0%, #e8eef7 50%, #f4f0f7 100%);
}
.login-bg::before {
    content: ''; position: absolute; inset: -50%;
    background:
        radial-gradient(ellipse 80% 60% at 20% 20%, rgba(17,133,91,0.12) 0%, transparent 60%),
        radial-gradient(ellipse 70% 50% at 80% 80%, rgba(47,60,110,0.1) 0%, transparent 60%),
        radial-gradient(ellipse 60% 70% at 60% 10%, rgba(17,133,91,0.06) 0%, transparent 50%);
    animation: meshMove 12s ease-in-out infinite alternate;
}
@keyframes meshMove {
    0%   { transform: translate(0%, 0%) rotate(0deg); }
    33%  { transform: translate(3%, 2%) rotate(2deg); }
    66%  { transform: translate(-2%, 3%) rotate(-1deg); }
    100% { transform: translate(1%, -2%) rotate(1deg); }
}
.login-bg::after {
    content: ''; position: absolute; inset: 0;
    background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%2311855B' fill-opacity='0.03'%3E%3Ccircle cx='30' cy='30' r='1'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}

/* LOGIN LOGO — büyük ve animasyonlu */
.login-logo-wrap {
    display: inline-block; position: relative;
    animation: loginBreath 3.5s ease-in-out infinite;
}
@keyframes loginBreath {
    0%,100% { transform: scale(0.97); filter: drop-shadow(0 8px 24px rgba(17,133,91,0.15)); }
    50%     { transform: scale(1.03); filter: drop-shadow(0 12px 40px rgba(17,133,91,0.35)); }
}
.login-logo-ring {
    position: absolute; inset: -8px; border-radius: 50%;
    border: 2px solid rgba(17,133,91,0.4);
    animation: loginRing 3.5s ease-in-out infinite;
}
.login-logo-ring2 {
    position: absolute; inset: -16px; border-radius: 50%;
    border: 1px solid rgba(47,60,110,0.2);
    animation: loginRing 3.5s ease-in-out infinite 0.4s;
}
@keyframes loginRing {
    0%,100% { transform: scale(1); opacity: 0.6; }
    50%     { transform: scale(1.2); opacity: 0; }
}

/* FLOATING PARTICLES on login */
.particle {
    position: absolute; border-radius: 50%;
    background: radial-gradient(circle, rgba(17,133,91,0.15), transparent);
    animation: floatP linear infinite;
    pointer-events: none;
}
@keyframes floatP {
    0%   { transform: translateY(100vh) scale(0); opacity:0; }
    10%  { opacity: 1; }
    90%  { opacity: 1; }
    100% { transform: translateY(-10vh) scale(1); opacity:0; }
}

@keyframes pulse-glow { 0%,100%{box-shadow:0 0 10px rgba(17,133,91,0.15);}50%{box-shadow:0 0 25px rgba(17,133,91,0.4);} }
@keyframes float { 0%,100%{transform:translateY(0);}50%{transform:translateY(-10px);} }
.floating{animation:float 4s ease-in-out infinite;}
.pulsing{animation:pulse-glow 2s ease-in-out infinite;}
.glow-text{text-shadow:0 0 30px rgba(17,133,91,0.5);}

.feed-item{display:flex;align-items:flex-start;gap:12px;padding:12px 0;border-bottom:1px solid rgba(0,0,0,0.06);}
.feed-dot{width:8px;height:8px;border-radius:50%;margin-top:5px;flex-shrink:0;}

.status-pill{display:inline-block;padding:3px 10px;border-radius:20px;font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;}
.pill-approved{background:rgba(17,133,91,0.1);color:var(--sg);border:1px solid rgba(17,133,91,0.2);}
.pill-pending{background:rgba(217,119,6,0.1);color:var(--amber);border:1px solid rgba(217,119,6,0.2);}
.pill-rejected{background:rgba(220,38,38,0.1);color:var(--red);border:1px solid rgba(220,38,38,0.2);}

.nav-item{padding:10px 16px;border-radius:10px;margin:2px 0;cursor:pointer;transition:all 0.18s;font-weight:500;}
.nav-item:hover{background:var(--bg-hover);}
.nav-item.active{background:rgba(17,133,91,0.1);color:var(--sg);border-left:3px solid var(--sg);}

.ai-bubble{background:linear-gradient(135deg,rgba(17,133,91,0.06),rgba(47,60,110,0.06));border:1px solid rgba(17,133,91,0.14);border-radius:14px;padding:18px 20px;margin:12px 0;position:relative;}
.ai-bubble::before{content:'⚡ AI';position:absolute;top:-10px;left:16px;background:linear-gradient(135deg,var(--sg-lo),var(--sn));color:#fff;font-size:0.62rem;font-weight:700;padding:2px 9px;border-radius:99px;letter-spacing:1.5px;}

.voice-note{background:rgba(17,133,91,0.07);border:1px solid rgba(17,133,91,0.18);border-radius:12px;padding:12px 16px;font-family:'JetBrains Mono',monospace;font-size:0.85rem;color:var(--sg);}
.anomaly-alert{background:linear-gradient(135deg,rgba(220,38,38,0.06),rgba(217,119,6,0.06));border:1px solid rgba(220,38,38,0.15);border-radius:12px;padding:16px;margin:8px 0;}
.budget-track{background:rgba(0,0,0,0.06);border-radius:8px;height:8px;overflow:hidden;margin:6px 0;}
.budget-fill{height:100%;border-radius:8px;transition:width 0.8s ease;}

.lb-item{display:flex;align-items:center;gap:12px;padding:13px 16px;border-radius:12px;margin:4px 0;background:#fff;border:1px solid rgba(0,0,0,0.07);transition:all 0.18s ease;box-shadow:var(--shadow);}
.lb-item:hover{border-color:var(--bdr-m);transform:translateX(3px);}
.lb-rank{font-family:'Plus Jakarta Sans';font-weight:900;font-size:1.3rem;color:var(--t3);width:30px;}
.lb-rank.gold{color:#d97706;text-shadow:0 0 12px rgba(217,119,6,0.4);}
.lb-rank.silver{color:#64748b;}
.lb-rank.bronze{color:#92400e;}

.heat-cell{display:inline-block;width:14px;height:14px;border-radius:3px;margin:1px;}
.info-tooltip{background:var(--bg-hover);border:1px solid rgba(0,0,0,0.08);border-radius:8px;padding:8px 12px;font-size:0.8rem;color:var(--t2);}
.empty-state{text-align:center;padding:60px 20px;color:var(--t3);}
.empty-icon{font-size:3rem;margin-bottom:12px;opacity:0.35;}
.upload-zone{border:2px dashed rgba(0,0,0,0.1);border-radius:16px;padding:40px;text-align:center;transition:all 0.3s;cursor:pointer;}
.upload-zone:hover{border-color:var(--sg);background:rgba(17,133,91,0.03);}
.spark-container{display:flex;align-items:flex-end;gap:2px;height:30px;}
.spark-bar{background:linear-gradient(180deg,var(--sg),var(--sg-lo));border-radius:2px;min-width:4px;opacity:0.6;}

@keyframes sdotBlink{0%,100%{opacity:1;}50%{opacity:0.2;}}
.sactive-dot{width:5px;height:5px;background:var(--sg);border-radius:50%;box-shadow:0 0 6px var(--sg);animation:sdotBlink 2s ease-in-out infinite;display:inline-block;margin-left:auto;}

</style>
""", unsafe_allow_html=True)

# ─── KULLANICI SİSTEMİ ────────────────────────────────────────
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# ── Kullanıcı Sistemi ─────────────────────────────────────────
# role: "admin"   → tüm fişleri görür + onaylayabilir (Zeynep, Serkan)
# role: "user"    → sadece kendi fişlerini görür (Okan, Şenol)
#
# Şifre → WhatsApp bot sifre alanıyla eşleşiyor:
#   Zeynep: 789 | Serkan: 123 | Okan: 321 | Şenol: 456
USERS = {
    "zeynep": {
        "name": "Zeynep",
        "password": hash_password("789"),
        "role": "admin",
        "avatar": "👑",
        "department": "Yönetim Kurulu",
        "monthly_limit": 50000,
        "xp": 1250
    },
    "serkan": {
        "name": "Serkan",
        "password": hash_password("123"),
        "role": "admin",
        "avatar": "📊",
        "department": "İşletme Müdürlüğü",
        "monthly_limit": 25000,
        "xp": 890
    },
    "okan": {
        "name": "Okan",
        "password": hash_password("321"),
        "role": "user",
        "avatar": "🔧",
        "department": "Saha",
        "monthly_limit": 5000,
        "xp": 430
    },
    "senol": {
        "name": "Şenol",
        "password": hash_password("456"),
        "role": "user",
        "avatar": "🏢",
        "department": "Genel Müdürlük",
        "monthly_limit": 30000,
        "xp": 600
    }
}

# ─── SESSION STATE ────────────────────────────────────────────
defaults = {
    'authenticated': False,
    'user_info': None,
    'splash_done': False,
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

# ─── RAILWAY API BAĞLANTISI ──────────────────────────────────
# Bot Railway'de çalışıyor. Dashboard oradan okur/yazar.
import requests as _req

RAILWAY_URL = st.secrets.get("BOT_API_URL", "https://stingafinans-production.up.railway.app")
_API_TIMEOUT = 12

def init_db():
    """API hazır mı kontrol et, session_state'i hazırla."""
    pass  # Veri Railway'den geliyor, lokal init gerekmiyor


@st.cache_data(ttl=15)
def load_data():
    """Railway API'den tüm veriyi çek. 15 sn cache."""
    try:
        r = _req.get(f"{RAILWAY_URL}/all-data", timeout=_API_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"⚠️ Railway bağlantı hatası: {e}")
        return {
            "expenses": [], "wallets": {}, "budgets": {}, "ledger": [],
            "notifications": [], "xp": {}, "fis_sayaci": {}, "badges": [],
            "ai_insights": [], "anomaly_log": []
        }


def save_data(d):
    """Lokal kayıt yok — Railway API üzerinden yazılıyor. Bu fonksiyon artık kullanılmıyor."""
    pass


def _api_post(endpoint: str, payload: dict) -> dict:
    """Railway API'ye POST atar, sonucu döndürür."""
    try:
        r = _req.post(f"{RAILWAY_URL}{endpoint}", json=payload, timeout=_API_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API Hatası ({endpoint}): {e}")
        return {"ok": False, "error": str(e)}


def api_approve(fis_id: str, action: str, approver: str) -> bool:
    """Fişi onayla veya reddet."""
    res = _api_post("/approve", {"ID": fis_id, "action": action, "approver": approver})
    if res.get("ok"):
        st.cache_data.clear()
        return True
    return False


def api_transfer(hedef: str, miktar: float, aciklama: str, gonderen: str) -> bool:
    """Harcırah transferi."""
    res = _api_post("/transfer", {"hedef": hedef, "miktar": miktar,
                                   "aciklama": aciklama, "gonderen": gonderen})
    if res.get("ok"):
        st.cache_data.clear()
        return True
    return False


def api_add_expense(expense: dict) -> bool:
    """Dashboard'dan fiş ekle."""
    res = _api_post("/add-expense", expense)
    if res.get("ok"):
        st.cache_data.clear()
        return True
    return False


def add_notify(target, message, notif_type="info", d=None):
    """Eski uyumluluk shim — artık API üzerinden çalışıyor."""
    pass


def add_xp(user_name, amount, reason="", d=None):
    """Eski uyumluluk shim — artık API üzerinden çalışıyor."""
    pass



    """d verilirse kaydetmez, sadece objeye yazar (atomic save için)."""
    _own = d is None
    if _own:
        d = load_data()
    d.setdefault("notifications", []).append({
        "user": target,
        "msg": message,
        "type": notif_type,
        "time": datetime.now().strftime("%H:%M"),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "read": False
    })
    if _own:
        save_data(d)

def add_xp(user_name, amount, reason="", d=None):
    """d verilirse kaydetmez, sadece objeye yazar (atomic save için)."""
    _own = d is None
    if _own:
        d = load_data()
    d.setdefault("xp", {})[user_name] = d["xp"].get(user_name, 0) + amount
    if reason:
        d.setdefault("notifications", []).append({
            "user": user_name,
            "msg": f"🏆 +{amount} XP kazandın! ({reason})",
            "type": "xp",
            "time": datetime.now().strftime("%H:%M"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "read": False
        })
    if _own:
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
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_fill_color(0, 120, 80)
        pdf.rect(0, 0, 210, 38, 'F')
        pdf.set_font("Arial", "B", 18)
        pdf.set_text_color(255, 255, 255)
        pdf.set_y(8)
        pdf.cell(0, 10, tr_fix(f"STINGA ENERJI - {tr_fix(title.upper())} ({tr_fix(ay_bilgisi)})"), align='C', new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(200, 240, 220)
        pdf.cell(0, 8, tr_fix(f"Uretim Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')} | Stinga Pro v14.0"), align='C', new_x="LMARGIN", new_y="NEXT")
        pdf.ln(12)
        
        if df_export.empty:
            pdf.set_text_color(100, 100, 100)
            pdf.set_font("Arial", "", 11)
            pdf.cell(0, 10, tr_fix("Bu doneme ait veri bulunmamaktadir."), new_x="LMARGIN", new_y="NEXT")
            return bytes(pdf.output())
        
        # Summary
        total    = df_export['Tutar'].sum() if 'Tutar' in df_export.columns else 0
        approved = df_export[df_export['Durum']=='Onaylandı']['Tutar'].sum() if 'Durum' in df_export.columns else 0
        pending  = df_export[df_export['Durum']=='Onay Bekliyor']['Tutar'].sum() if 'Durum' in df_export.columns else 0
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, tr_fix("OZET"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Arial", "", 9)
        pdf.cell(0, 6, tr_fix(f"Toplam: {total:,.2f} TL  |  Onaylanan: {approved:,.2f} TL  |  Bekleyen: {pending:,.2f} TL"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
        
        # Table header
        pdf.set_fill_color(40, 60, 100)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 7)
        cols = [
            ("ID", 18), ("Fiş Tarihi", 20), ("Yükleme Zamanı", 30), ("Personel", 22),
            ("Firma", 35), ("Tutar", 20), ("Kategori", 22), ("Durum", 20), ("Risk%", 13)
        ]
        for col, w in cols:
            pdf.cell(w, 8, tr_fix(col), border=1, fill=True, align='C')
        pdf.ln()
        
        # Rows
        for i, (_, row) in enumerate(df_export.iterrows()):
            fill = i % 2 == 0
            if fill:
                pdf.set_fill_color(240, 248, 244)
            else:
                pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", "", 6)
            risk = row.get('Risk_Skoru', 0)
            
            # Risk rengini belirle
            if risk >= 70:
                pdf.set_text_color(180, 0, 0)
            elif risk >= 30:
                pdf.set_text_color(150, 80, 0)
            else:
                pdf.set_text_color(0, 100, 50)
            
            yukleme = str(row.get('Yukleme_Zamani', row.get('Tarih', '')))
            kisisel = row.get('Kisisel_Giderler', [])
            kisisel_str = ", ".join(kisisel) if isinstance(kisisel, list) and kisisel else ""
            
            values = [
                (str(row.get('ID', ''))[-8:], 18),
                (str(row.get('Tarih', '')), 20),
                (yukleme[:16], 30),
                (str(row.get('Kullanıcı', '')), 22),
                (str(row.get('Firma', ''))[:18], 35),
                (f"{float(row.get('Tutar', 0)):,.0f} TL", 20),
                (str(row.get('Kategori', ''))[:12], 22),
                (tr_fix(str(row.get('Durum', ''))), 20),
                (f"%{risk}", 13)
            ]
            
            pdf.set_text_color(0, 0, 0)
            for j, (val, w) in enumerate(values):
                if j == 8:  # Risk sütunu renkli
                    if risk >= 70: pdf.set_text_color(180, 0, 0)
                    elif risk >= 30: pdf.set_text_color(150, 80, 0)
                    else: pdf.set_text_color(0, 120, 60)
                else:
                    pdf.set_text_color(0, 0, 0)
                pdf.cell(w, 6, tr_fix(val), border=1, fill=fill, align='C')
            pdf.ln()
            
            # Kişisel gider varsa alt satırda göster
            if kisisel_str:
                pdf.set_font("Arial", "I", 6)
                pdf.set_text_color(180, 0, 0)
                pdf.cell(18, 5, "", border=0)
                pdf.cell(162, 5, tr_fix(f"  ⚠ Kisisel Gider: {kisisel_str}"), border=0)
                pdf.ln()
                pdf.set_text_color(0, 0, 0)
        
        pdf.ln(8)
        pdf.set_font("Arial", "I", 7)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 5, tr_fix("Bu rapor Stinga Pro v14.0 AI Finans Sistemi tarafindan otomatik uretilmistir."), align='C')
        
        return bytes(pdf.output())
    except Exception as e:
        # PDF oluşturulamadıysa boş bytes dön
        return b"%PDF-1.4\n"

# ─── AI FONKSİYONLARI ─────────────────────────────────────────
def analyze_receipt_pro(image, model):
    bugun = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""Sen Stinga Enerji şirketinin kıdemli mali denetçisisin. Fişi tara ve iş kurallarına göre risk skoru belirle.

Bugünün tarihi: {bugun}. Fişteki tarih bu tarihten ÖNCE olmalı. Sonraki tarihse anomali=true.
Yılı dikkatli oku: 2025 ve 2026 karıştırma. Tarih formatı: YYYY-MM-DD

=== RİSK SKORLAMA KURALLARI ===
YEMEK:
- Fişte yemek/restoran/kafe kategorisiyse başlangıç risk skoru: 2
- (Günlük kaçıncı yemek fişi olduğu Python tarafında hesaplanacak, burada sadece kategoriyi belirle)

KONAKLAMA:
- Otel/konaklama kategorisi: maksimum risk skoru 2 olsun

YAKIT:
- Akaryakıt/benzin/motorin: başlangıç risk skoru 1
- (Günlük birden fazla yakıt fişi Python tarafında kontrol edilecek)

KİŞİSEL GİDERLER (ÇOK ÖNEMLİ):
- Fişte şu ürünler varsa mutlaka belirt ve risk skoru 40+ yap:
  çikolata, şeker, şekerleme, sigara, alkol, bira, içki, kozmetik, parfüm, oyuncak,
  kişisel bakım, şampuan, dizi/film aboneliği, oyun, müzik aleti
- Bu ürünler tespit edilirse anomali=true yap ve anomali_aciklamasi'nda hangi ürünler olduğunu yaz
- kisisel_giderler listesine bu ürünleri ekle

GENEL KURALLAR:
- Tutar makul görünüyorsa düşük risk, şüpheli yüksekse risk artır
- Fatura net okunmuyorsa risk +15
- Gece yarısı saatli fiş (22:00-06:00 arası) risk +10

SADECE aşağıdaki JSON formatını döndür, başka hiçbir şey yazma:
{{
    "firma": "Firma Adı",
    "tarih": "YYYY-MM-DD",
    "saat": "HH:MM",
    "toplam_tutar": 0.0,
    "kategori": "Yemek/Yakıt/Konaklama/Ekipman/Kişisel/Diğer",
    "risk_skoru": 2,
    "audit_ozeti": "1 cümlelik denetim özeti",
    "kalemler": ["kalem1", "kalem2"],
    "kisisel_giderler": [],
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

def apply_business_rules(data_ai, data_store, user_name):
    """
    Şirket iş kurallarına göre risk skorunu Python tarafında hesaplar.
    AI'ın verdiği skoru bu kurallarla günceller.
    """
    kategori    = str(data_ai.get("kategori", "")).lower()
    tarih       = data_ai.get("tarih", datetime.now().strftime("%Y-%m-%d"))
    risk        = int(data_ai.get("risk_skoru", 5))
    anomali     = data_ai.get("anomali", False)
    anomali_msg = data_ai.get("anomali_aciklamasi", "")
    audit       = data_ai.get("audit_ozeti", "")
    kisisel     = data_ai.get("kisisel_giderler", [])
    uyarilar    = []

    # ── Aynı gün aynı kullanıcının fişlerini say ──────────────────
    bugun_fisleri = [
        e for e in data_store.get("expenses", [])
        if e.get("Kullanıcı") == user_name and e.get("Tarih") == tarih
    ]
    bugun_yemek = [e for e in bugun_fisleri if "yemek" in str(e.get("Kategori","")).lower()]
    bugun_yakit = [e for e in bugun_fisleri if "yakıt" in str(e.get("Kategori","")).lower() or "yakit" in str(e.get("Kategori","")).lower()]

    # ── YEMEK KURALLARI ────────────────────────────────────────────
    if "yemek" in kategori:
        kac_inci = len(bugun_yemek) + 1  # Bu fiş kaçıncı olacak
        if kac_inci == 1:
            risk = max(risk, 2)
            audit += " | Günün 1. yemek fişi."
        elif kac_inci == 2:
            risk = max(risk, 6)
            audit += " | Günün 2. yemek fişi."
        elif kac_inci == 3:
            risk = max(risk, 5)
            audit += " | Günün 3. yemek fişi."
        else:
            risk = max(risk, 75)
            anomali = True
            uyari = f"🍽️ Günde {kac_inci}. yemek fişi! Aşırı yemek harcaması tespit edildi."
            anomali_msg = (anomali_msg + " | " + uyari).strip(" | ")
            audit += f" | ⚠️ Günde {kac_inci}. yemek fişi — yüksek risk."
            uyarilar.append(uyari)

    # ── KONAKLAMA KURALLARI ────────────────────────────────────────
    elif "konaklama" in kategori or "otel" in kategori:
        risk = min(risk, 2)
        audit += " | Konaklama fişi — standart risk uygulandı."

    # ── YAKIT KURALLARI ───────────────────────────────────────────
    elif "yakıt" in kategori or "yakit" in kategori or "akaryakıt" in kategori:
        kac_yakit = len(bugun_yakit) + 1
        if kac_yakit == 1:
            risk = max(risk, 1)
            audit += " | Günün ilk yakıt fişi."
        else:
            risk = min(max(risk, kac_yakit * 10), 20)
            uyari = f"⛽ Aynı gün {kac_yakit}. yakıt fişi!"
            anomali_msg = (anomali_msg + " | " + uyari).strip(" | ")
            audit += f" | ⚠️ Günde {kac_yakit}. yakıt fişi."
            uyarilar.append(uyari)
            if kac_yakit >= 3:
                anomali = True

    # ── KİŞİSEL GİDER KURALLARI ───────────────────────────────────
    kisisel_keywords = [
        "çikolata","cikolata","şeker","sekerleme","sigara","alkol","bira","içki","icki",
        "kozmetik","parfüm","parfum","oyuncak","şampuan","sampuan","dizi","film",
        "abonelik","oyun","müzik","muzik","kişisel","kisisel","atıştırmalık","cips",
        "snack","fast food","energy drink","kahve kapsül"
    ]
    
    # AI'ın tespit ettiklerine ek olarak kalemlerden de kontrol et
    tüm_kalemler = " ".join([str(k).lower() for k in data_ai.get("kalemler", [])])
    bulunan_kisisel = list(kisisel) if kisisel else []
    
    for kw in kisisel_keywords:
        if kw in tüm_kalemler and kw not in " ".join(bulunan_kisisel).lower():
            bulunan_kisisel.append(kw)

    if bulunan_kisisel:
        risk = max(risk, 45)
        anomali = True
        kisisel_str = ", ".join(bulunan_kisisel)
        uyari = f"🚫 Kişisel gider tespiti: {kisisel_str}"
        anomali_msg = (anomali_msg + " | " + uyari).strip(" | ")
        audit += f" | ⚠️ Kişisel gider içeriyor: {kisisel_str}"
        uyarilar.append(uyari)
        data_ai["kisisel_giderler"] = bulunan_kisisel

    # Güncellenmiş değerleri yaz
    data_ai["risk_skoru"]         = min(risk, 100)
    data_ai["anomali"]            = anomali
    data_ai["anomali_aciklamasi"] = anomali_msg
    data_ai["audit_ozeti"]        = audit
    data_ai["_uyarilar"]          = uyarilar  # UI'da göstermek için

    return data_ai


import re as _re
import html as _html

def clean_audit(text: str) -> str:
    """AI_Audit metnindeki HTML tag'larını kaldır, tırnak işaretlerini escape et."""
    if not text:
        return "Analiz tamamlandı."
    # HTML tag'larını kaldır
    text = _re.sub(r'<[^>]+>', '', str(text))
    # Birden fazla boşluğu tek boşluğa indir
    text = _re.sub(r'\s+', ' ', text).strip()
    # HTML escape (tırnak sorununu önler)
    text = _html.escape(text, quote=False)
    return text if text else "Analiz tamamlandı."


def detect_anomalies(df, model=None):
    """DataFrame üzerinde kural tabanlı anomali tespiti."""
    if df is None or df.empty or len(df) < 2:
        return []

    anomalies = []

    # Mükerrer fiş (aynı firma + tutar)
    if 'Firma' in df.columns and 'Tutar' in df.columns:
        dups = df[df.duplicated(subset=['Firma', 'Tutar'], keep=False)]
        if not dups.empty:
            anomalies.append({
                "type": "duplicate",
                "severity": "high",
                "message": f"⚠️ Mükerrer fiş: {dups['Firma'].iloc[0]} — ₺{dups['Tutar'].iloc[0]:,.0f} ({len(dups)} kayıt)",
                "count": len(dups)
            })

    # Hafta sonu harcamaları
    if 'Tarih' in df.columns:
        try:
            df_t = df.copy()
            df_t['_dt'] = pd.to_datetime(df_t['Tarih'], errors='coerce')
            weekend = df_t[df_t['_dt'].dt.dayofweek >= 5]
            if not weekend.empty:
                anomalies.append({
                    "type": "weekend",
                    "severity": "medium",
                    "message": f"📅 Hafta sonu harcaması: {len(weekend)} adet işlem",
                    "count": len(weekend)
                })
        except:
            pass

    # Kritik risk skoru (>70)
    if 'Risk_Skoru' in df.columns:
        high_risk = df[df['Risk_Skoru'] > 70]
        if not high_risk.empty:
            anomalies.append({
                "type": "high_risk",
                "severity": "high",
                "message": f"🔴 {len(high_risk)} adet kritik riskli işlem (risk > 70)",
                "count": len(high_risk)
            })

    # İstatistiksel aykırı tutarlar (ortalama + 2σ)
    if 'Tutar' in df.columns and len(df) > 3:
        mean_t = df['Tutar'].mean()
        std_t  = df['Tutar'].std()
        if std_t > 0:
            outliers = df[df['Tutar'] > mean_t + 2 * std_t]
            if not outliers.empty:
                anomalies.append({
                    "type": "outlier",
                    "severity": "medium",
                    "message": f"📈 Ortalamadan 2σ sapan {len(outliers)} anormal tutar (ort: ₺{mean_t:,.0f})",
                    "count": len(outliers)
                })

    # Sahte şüphesi durumundaki fişler
    if 'Durum' in df.columns:
        sahte = df[df['Durum'] == 'Sahte Şüphesi']
        if not sahte.empty:
            anomalies.append({
                "type": "sahte",
                "severity": "high",
                "message": f"🚨 {len(sahte)} adet sahte fiş şüphesi tespit edildi",
                "count": len(sahte)
            })

    return anomalies

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
    # Embedded logo (PNG base64)
    _LOGO_B64 = "/9j/4AAQSkZJRgABAQAAAQABAAD/4gHYSUNDX1BST0ZJTEUAAQEAAAHIAAAAAAQwAABtbnRyUkdCIFhZWiAH4AABAAEAAAAAAABhY3NwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAA9tYAAQAAAADTLQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAlkZXNjAAAA8AAAACRyWFlaAAABFAAAABRnWFlaAAABKAAAABRiWFlaAAABPAAAABR3dHB0AAABUAAAABRyVFJDAAABZAAAAChnVFJDAAABZAAAAChiVFJDAAABZAAAAChjcHJ0AAABjAAAADxtbHVjAAAAAAAAAAEAAAAMZW5VUwAAAAgAAAAcAHMAUgBHAEJYWVogAAAAAAAAb6IAADj1AAADkFhZWiAAAAAAAABimQAAt4UAABjaWFlaIAAAAAAAACSgAAAPhAAAts9YWVogAAAAAAAA9tYAAQAAAADTLXBhcmEAAAAAAAQAAAACZmYAAPKnAAANWQAAE9AAAApbAAAAAAAAAABtbHVjAAAAAAAAAAEAAAAMZW5VUwAAACAAAAAcAEcAbwBvAGcAbABlACAASQBuAGMALgAgADIAMAAxADb/2wBDAAUDBAQEAwUEBAQFBQUGBwwIBwcHBw8LCwkMEQ8SEhEPERETFhwXExQaFRERGCEYGh0dHx8fExciJCIeJBweHx7/2wBDAQUFBQcGBw4ICA4eFBEUHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh7/wAARCAWGB9ADASIAAhEBAxEB/8QAHQABAAIDAQEBAQAAAAAAAAAAAAcIBAYJBQMCAf/EAGEQAQABAgMCCAcLBgsFBgQEBwABAgMEBQYHERIYIVVWlNHSCBYXMUGT0xMUFSJRVGFxgZKVMjdSU5GzI0JicnR1gqGjpLEJM3OiwiQ0NkOywTVjhMMlZIO04iZFRlfwOP/EABsBAQACAwEBAAAAAAAAAAAAAAACBAEDBQYH/8QAQBEBAAEBBAUKBAUEAQUBAAMAAAECAwQRURMUFVJhBRIWITFTkaGx4TJBcdEGYmOBoiIzQsE0I0NygvDxRJKy/9oADAMBAAIRAxEAPwCmQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA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3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn3LfYcXXT/P8Amn3LfYYSbAvuUeMK1iynF10/z/mn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Ws/2eWzr4X1fj9omYWIqweTROFwEzu3VYqun487v5Fur9tyJjzAuBsh0TgdnmzrJ9I4CYrpwNjdeuxG6b16qeFcrn66pnd8kbo9Dz9uer/FHQ1+5hrnAzHHb8NhN07ppmY+NXH82OXf8vBb4p/t51d4167xHve5wsuy/fhcLumd1W6fj1/bV6fkiliZcrli+6rd5mn4p6o+/7NM+F815zxvr6u0+F815zxvr6u1hCLwGkqzZvwvmvOeN9fV2nwvmvOeN9fV2sIDSVZs34XzXnPG+vq7T4XzXnPG+vq7WEBpKs2b8L5rznjfX1dp8L5rznjfX1drCA0lWbN+F815zxvr6u0+F815zxvr6u1hAaSrNm/C+a854319XafC+a854319XawgNJVmzfhfNec8b6+rtPhfNec8b6+rtYQGkqzZvwvmvOeN9fV2nwvmvOeN9fV2sIDSVZs34XzXnPG+vq7T4XzXnPG+vq7WEBpKs2b8L5rznjfX1dp8L5rznjfX1drCA0lWbN+F815zxvr6u0+F815zxvr6u1hAaSrNm/C+a854319XafC+a854319XawgNJVmzfhfNec8b6+rtPhfNec8b6+rtYQGkqzZvwvmvOeN9fV2nwvmvOeN9fV2sIDSVZs34XzXnPG+vq7T4XzXnPG+vq7WEBpKs2b8L5rznjfX1dp8L5rznjfX1drCA0lWbN+F815zxvr6u0+F815zxvr6u1hAaSrNm/C+a854319XafC+a854319XawgNJVmzfhfNec8b6+rtPhfNec8b6+rtYQGkqzZvwvmvOeN9fV2nwvmvOeN9fV2sIDSVZs34XzXnPG+vq7T4XzXnPG+vq7WEBpKs2b8L5rznjfX1dp8L5rznjfX1drCA0lWbN+F815zxvr6u0+F815zxvr6u1hAaSrNm/C+a854319XafC+a854319XawgNJVmzfhfNec8b6+rtPhfNec8b6+rtYQGkqzZvwvmvOeN9fV2nwvmvOeN9fV2sIDSVZs34XzXnPG+vq7T4XzXnPG+vq7WEBpKs2b8L5rznjfX1dp8L5rznjfX1drCA0lWbN+F815zxvr6u0+F815zxvr6u1hAaSrNm/C+a854319XafC+a854319XawgNJVmzfhfNec8b6+rtPhfNec8b6+rtYQGkqzZvwvmvOeN9fV2nwvmvOeN9fV2s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xFFNUenliZfPxgyHnvLOtUdrPNnJRr5NuldU1VURMyjHi9aN5zz311r2ZxetG85576617NJ3jBkPPeWdao7TxgyHnvLOtUdpzJyR2Vc+7hGPF60bznnvrrXs3t6H2Q6e0hqKzneV5lnFV+3TVRNu7dtzbrpqjdMVRFETMeafP54hufjBkPPeWdao7TxgyHnvLOtUdpzJySo5NutnVFVNERMPSHm+MGQ895b1qjtekTEwvADAAAAAAAAAAAAANa1/ojIdbZbRg85sVxXanfZxNmYpvWuXl4MzE8k+aYmJj7YiY2UELSzptKZorjGJQ/xetG85576617M4vWjec899da9ml2/dtWLNd69cotW6I31V11RFNMfLMz5mB4wZDz3lnWqO0inFS2Vc+7hGPF60bznnvrrXszi9aN5zz311r2aTvGDIee8s61R2njBkPPeWdao7WeZORsq593CMeL1o3nPPfXWvZnF60bznnvrrXs0neMGQ895Z1qjtPGDIee8s61R2nMnI2Vc+7hGPF60bznnvrrXszi9aN5zz311r2aTvGDIee8s61R2njBkPPeWdao7TmTkbKufdwjHi9aN5zz311r2ZxetG85576617NJ3jBkPPeWdao7TxgyHnvLOtUdpzJyNlXPu4RjxetG85576617NJmk8jwmmtO4PI8DcvXMNhKJpt1Xpia5iapnlmIiPT8j9eMGQ895Z1qjtZ2Gv2MTYpv4e9bvWq+Wmu3VFVM/VMMc3BusLlYWFXOsqYiX0AFoAB4OvNK5frLIKslzO9ibOHqu03Jqw9VNNe+nzcsxMf3I94vWjec899da9mlrGYrC4Oz7ti8TZw9rfu4d2uKad/1yw/GDIee8s61R2nNmVS2uN3t6udaURMox4vWjec899da9mcXrRvOee+utezSd4wZDz3lnWqO08YMh57yzrVHazzJyatlXPu4RjxetG85576617M4vWjec899da9mk7xgyHnvLOtUdp4wZDz3lnWqO05k5Gyrn3cIx4vWjec899da9mcXrRvOee+utezSd4wZDz3lnWqO08YMh57yzrVHacycjZVz7uEY8XrRvOee+utezOL1o3nPPfXWvZpO8YMh57yzrVHaeMGQ895Z1qjtOZORsq593DVtnmy3IND5xezTKsZmV69ew82KqcTcoqpimaqat8cGmOXfTDe2Jgs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XZfYqv36/PO6PREemqZ3REemZiHNvl609XV2Q32VnzI60I+G3tZjQWz2dNZRi+BqHP7dVqiaK91eGw3muXeSd8TP5FM/Lwpj8lzqbdtg13mm0jaDmerM1mqirFXODh7HC4UYexTyUW4+qPPPJvmZn0tRU20AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAASJ4Pe03HbK9pGC1Da91u5dcmLGZ4ajl92w9Uxwt0b4ia6fyqd8xyxu80yjsB2MyTM8BnWT4PN8rxVvFYHGWab+HvW5303KKo3xMfZLMmYiJmZiIjlmZUl8AjbJ7xxkbK9RYuIwuJrmvJLtyr/AHd2d814ffM7t1U/Gpj9LhRy8KN12ga/48aK6Yae/ErPePHnRXTDT34lZ7yq/hTbMZ0pqGdT5Ph4pyPM7nx6KI5MLiJ3zNO7duimrz0/Two5N0b4SdWyuFna0xVTUr1W00zhMOivjzorphp78Ss948edFdMNPfiVnvOdQ2bLp3mNY4Oivjzorphp78Ss948edFdMNPfiVnvOdQbLp3jWODor486K6Yae/ErPePHnRXTDT34lZ7znUGy6d41jg6K+POiumGnvxKz3jx50V0w09+JWe851BsuneNY4Oivjzorphp78Ss948edFdMNPfiVnvOdQbLp3jWODor486K6Yae/ErPePHnRXTDT34lZ7znUGy6d41jg6K+POiumGnvxKz3jx50V0w09+JWe851BsuneNY4Oivjzorphp78Ss948edFdMNPfiVnvOdQbLp3jWODor486K6Yae/ErPePHnRXTDT34lZ7znUGy6d41jg6K+POiumGnvxKz3jx50V0w09+JWe851BsuneNY4Oivjzorphp78Ss948edFdMNPfiVnvOdQbLp3jWODor486K6Yae/ErPePHnRXTDT34lZ7znUGy6d41jg6K+POiumGnvxKz3jx50V0w09+JWe851BsuneNY4Oivjzorphp78Ss948edFdMNPfiVnvOdQbLp3jWODor486K6Yae/ErPePHnRXTDT34lZ7znUGy6d41jg6K+POiumGnvxKz3jx50V0w09+JWe851BsuneNY4Oivjzorphp78Ss948edFdMNPfiVnvOdQbLp3jWODor486K6Yae/ErPePHnRXTDT34lZ7znUGy6d41jg6K+POiumGnvxKz3jx50V0w09+JWe851BsuneNY4Oivjzorphp78Ss948edFdMNPfiVnvOdQbLp3jWODor486K6Yae/ErPePHnRXTDT34lZ7znUGy6d41jg6K+POiumGnvxKz3jx50V0w09+JWe851BsuneNY4Oivjzorphp78Ss948edFdMNPfiVnvOdQbLp3jWODor486K6Yae/ErPePHnRXTDT34lZ7znUGy6d41jg6K+POiumGnvxKz3jx50V0w09+JWe851BsuneNY4Oivjzorphp78Ss948edFdMNPfiVnvOdQbLp3jWODor486K6Yae/ErPePHnRXTDT34lZ7znUGy6d41jg6K+POiumGnvxKz3jx50V0w09+JWe851BsuneNY4Oivjzorphp78Ss948edFdMNPfiVnvOdQbLp3jWODor486K6Yae/ErPePHnRXTDT34lZ7znUGy6d41jg6K+POiumGnvxKz3jx50V0w09+JWe851BsuneNY4Oivjzorphp78Ss948edFdMNPfiVnvOdQbLp3jWODor486K6Yae/ErPePHnRXTDT34lZ7znUGy6d41jg6K+POiumGnvxKz3jx50V0w09+JWe851BsuneNY4Oivjzorphp78Ss948edFdMNPfiVnvOdQbLp3jWODor486K6Yae/ErPePHnRXTDT34lZ7znUGy6d41jg6K+POiumGnvxKz3jx50V0w09+JWe851BsuneNY4Oivjzorphp78Ss948edFdMNPfiVnvOdQbLp3jWODor486K6Yae/ErPePHnRXTDT34lZ7znUGy6d41jg6K+POiumGnvxKz3jx50V0w09+JWe851BsuneNY4Oivjzorphp78Ss948edFdMNPfiVnvOdQbLp3jWODor486K6Yae/ErPePHnRXTDT34lZ7znUGy6d41jg6K+POiumGnvxKz3jx50V0w09+JWe851BsuneNY4Oivjzorphp78Ss948edFdMNPfiVnvOdQbLp3jWODor486K6Yae/ErPePHnRXTDT34lZ7znUGy6d41jg6K+POiumGnvxKz3jx50V0w09+JWe851BsuneNY4Oivjzorphp78Ss948edFdMNP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aFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34rWkukWef4XdOK1pLpFnn+F3TaFhmaGtUgW34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AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH/9k="
    if _LOGO_B64:
        return _LOGO_B64
    logo_paths = ["logo.png", "/mnt/user-data/uploads/logo.png"]
    for p in logo_paths:
        if os.path.exists(p):
            with open(p, "rb") as fh:
                return base64.b64encode(fh.read()).decode()
    return ""

def login():
    logo_b64 = get_logo_b64()
    logo_img = f'<img src="data:image/png;base64,{logo_b64}" style="width:130px;height:130px;object-fit:contain;border-radius:50%;">' if logo_b64 else '<div style="font-size:5rem;">⚡</div>'

    # Animated background + floating particles
    st.markdown("""
    <div class="login-bg"></div>
    <div style="position:fixed;inset:0;pointer-events:none;z-index:0;overflow:hidden;">
        <div class="particle" style="width:180px;height:180px;left:5%;animation-duration:18s;animation-delay:0s;"></div>
        <div class="particle" style="width:120px;height:120px;left:25%;animation-duration:22s;animation-delay:3s;"></div>
        <div class="particle" style="width:200px;height:200px;left:55%;animation-duration:16s;animation-delay:6s;"></div>
        <div class="particle" style="width:90px;height:90px;left:75%;animation-duration:20s;animation-delay:1s;"></div>
        <div class="particle" style="width:150px;height:150px;left:88%;animation-duration:24s;animation-delay:8s;"></div>
    </div>
    """, unsafe_allow_html=True)

    # Logo bölümü - büyük ve animasyonlu
    st.markdown(f"""
    <div style="text-align:center; padding: 48px 0 28px 0; position:relative; z-index:1;">
        <div class="login-logo-wrap" style="display:inline-block;">
            <div class="login-logo-ring"></div>
            <div class="login-logo-ring2"></div>
            {logo_img}
        </div>
        <div style="margin-top:20px;">
            <div style="font-family:'Plus Jakarta Sans',sans-serif; font-size:2rem; font-weight:900;
                        letter-spacing:0.08em; color:#0f1923; text-transform:uppercase;">
                STINGA <span style="color:#11855B;">PRO</span>
            </div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.65rem; color:#7a96a4;
                        letter-spacing:0.2em; margin-top:5px; text-transform:uppercase;">
                STİNGA ENERJİ A.Ş. · YÖNETİM PANELİ
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.1, 1])
    with col2:
        # Dekoratif üst çubuk
        st.markdown("""
        <div style="height:3px; background:linear-gradient(90deg,#11855B,#2F3C6E,#11855B);
                    border-radius:99px; margin-bottom:0;"></div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            st.markdown("""
            <div style="text-align:center; padding:16px 0 8px 0;">
                <div style="font-family:'Plus Jakarta Sans',sans-serif; font-size:1rem; font-weight:700;
                            color:#0f1923; letter-spacing:0.02em;">Hesabınıza Giriş Yapın</div>
                <div style="font-size:0.75rem; color:#7a96a4; margin-top:3px;">
                    Yetkili personel girişi
                </div>
            </div>
            """, unsafe_allow_html=True)

            username = st.text_input("Kullanıcı Adı", placeholder="kullanıcı adınız").lower()
            password = st.text_input("Şifre", type="password", placeholder="••••••••")
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            submit = st.form_submit_button("GİRİŞ YAP  →", use_container_width=True)

            if submit:
                if username in USERS and USERS[username]["password"] == hash_password(password):
                    st.session_state.authenticated = True
                    st.session_state.user_info = USERS[username]
                    st.session_state.user_info['username'] = username
                    st.session_state.splash_done = False
                    st.rerun()
                else:
                    st.error("⚠️ Hatalı kullanıcı adı veya şifre")

        st.markdown("""
        <div style="text-align:center; margin-top:20px; color:#7a96a4; font-size:0.72rem;
                    font-family:'JetBrains Mono',monospace; letter-spacing:0.05em;">
            🔒 256-BIT AES · ZERO-KNOWLEDGE AUTH · GEMINI AI
        </div>
        """, unsafe_allow_html=True)




def show_splash():
    """Şifre sonrası tam ekran WebGL giriş animasyonu."""
    import streamlit.components.v1 as components
    
    user_info = st.session_state.user_info
    user_name = user_info.get("name", "")
    avatar    = user_info.get("avatar", "⚡")

    # Tüm Streamlit UI'ı gizle — sadece splash görünsün
    st.markdown("""
    <style>
        header[data-testid="stHeader"] { display:none !important; }
        #MainMenu { display:none !important; }
        footer { display:none !important; }
        .block-container { padding:0 !important; max-width:100% !important; }
        [data-testid="stAppViewContainer"] { background:#000 !important; }
        [data-testid="stVerticalBlock"] { gap:0 !important; }
    </style>
    """, unsafe_allow_html=True)

    # JS → Python köprüsü: splash bitince query param set eder
    splash_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#000; overflow:hidden; font-family:'Space Grotesk',sans-serif; }}
  @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Space+Grotesk:wght@300;600&display=swap');

  #c {{ position:fixed; inset:0; width:100%; height:100%; }}

  #ui {{
    position:fixed; inset:0;
    display:flex; flex-direction:column;
    align-items:center; justify-content:center;
    pointer-events:none; z-index:10;
  }}

  .logo-wrap {{
    display:flex; flex-direction:column; align-items:center; gap:14px;
    opacity:0; transform:translateY(24px);
    animation: rise 1.1s cubic-bezier(0.16,1,0.3,1) 0.4s forwards;
  }}

  .brand {{
    font-family:'Bebas Neue',sans-serif;
    font-size: min(11vw, 88px);
    letter-spacing:.18em;
    background:linear-gradient(135deg,#00e896 0%,#1a9e6e 50%,#2d4a8a 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
    filter:drop-shadow(0 0 32px rgba(0,200,120,.6));
    line-height:1;
  }}
  .sub {{
    font-size:11px; letter-spacing:.42em;
    color:rgba(0,200,140,.55); text-transform:uppercase; font-weight:300;
  }}
  .welcome {{
    font-size:13px; letter-spacing:.25em;
    color:rgba(255,255,255,.35); text-transform:uppercase;
    margin-top:4px;
  }}

  .divider {{
    width:1px; height:44px;
    background:linear-gradient(to bottom,transparent,rgba(0,200,120,.35),transparent);
    margin:24px 0 20px;
    opacity:0; animation:rise .7s ease 1.3s forwards;
  }}

  .prog-wrap {{
    display:flex; flex-direction:column; align-items:center; gap:10px;
    opacity:0; animation:rise .7s ease 1.5s forwards;
  }}
  .prog-bar {{
    width:220px; height:1px;
    background:rgba(255,255,255,.07); position:relative; overflow:hidden;
  }}
  .prog-fill {{
    position:absolute; left:0; top:0; height:100%;
    background:linear-gradient(90deg,#00e896,#2d4a8a);
    width:0%; transition:width .12s linear;
    box-shadow:0 0 10px rgba(0,232,150,.9);
  }}
  .prog-lbl {{
    font-size:10px; letter-spacing:.32em;
    color:rgba(255,255,255,.28); text-transform:uppercase;
  }}

  .corner {{ position:fixed; width:36px; height:36px; opacity:0; animation:fade .5s ease 1.9s forwards; }}
  .tl {{ top:22px; left:22px; border-top:1px solid rgba(0,200,120,.25); border-left:1px solid rgba(0,200,120,.25); }}
  .tr {{ top:22px; right:22px; border-top:1px solid rgba(0,200,120,.25); border-right:1px solid rgba(0,200,120,.25); }}
  .bl {{ bottom:22px; left:22px; border-bottom:1px solid rgba(0,200,120,.25); border-left:1px solid rgba(0,200,120,.25); }}
  .br {{ bottom:22px; right:22px; border-bottom:1px solid rgba(0,200,120,.25); border-right:1px solid rgba(0,200,120,.25); }}

  .scan {{
    position:fixed; left:0; right:0; height:1px; top:-1px;
    background:linear-gradient(90deg,transparent,rgba(0,200,120,.12),transparent);
    animation:scan 4s linear 1.4s infinite;
  }}

  #flash {{
    position:fixed; inset:0;
    background:#fff; opacity:0; pointer-events:none; z-index:99;
  }}

  @keyframes rise {{ to {{ opacity:1; transform:translateY(0); }} }}
  @keyframes fade {{ to {{ opacity:1; }} }}
  @keyframes scan {{ 0% {{ top:-1px; }} 100% {{ top:100vh; }} }}
</style>
</head>
<body>
<canvas id="c"></canvas>

<div id="ui">
  <div class="logo-wrap">
    <svg width="82" height="82" viewBox="0 0 100 100" fill="none">
      <defs>
        <radialGradient id="g1" cx="50%" cy="30%" r="70%">
          <stop offset="0%" stop-color="#00e896"/>
          <stop offset="60%" stop-color="#1a9e6e"/>
          <stop offset="100%" stop-color="#0f2240"/>
        </radialGradient>
        <filter id="glow"><feGaussianBlur stdDeviation="1.5" result="b"/>
          <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
      </defs>
      <circle cx="50" cy="50" r="47" stroke="url(#g1)" stroke-width="1" fill="none" opacity=".5"/>
      <circle cx="50" cy="50" r="42" stroke="rgba(0,200,120,.15)" stroke-width=".5"
              stroke-dasharray="4 8" fill="none">
        <animateTransform attributeName="transform" type="rotate"
          from="0 50 50" to="360 50 50" dur="12s" repeatCount="indefinite"/>
      </circle>
      <circle cx="50" cy="50" r="37" fill="url(#g1)" opacity=".9"/>
      <path filter="url(#glow)"
        d="M36 28 C36 28,54 28,56 35 C58 42,44 44,44 44 C44 44,62 46,64 54
           C66 62,48 72,44 72 L36 72 L42 72 C42 72,58 70,56 63
           C54 56,38 54,38 54 C38 54,56 52,54 44 C52 36,36 36,36 36 Z"
        fill="none" stroke="rgba(0,232,150,.9)" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="50" cy="50" r="47" fill="none" stroke="rgba(0,200,120,.12)" stroke-width="2">
        <animate attributeName="r" values="47;53;47" dur="3s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values=".12;0;.12" dur="3s" repeatCount="indefinite"/>
      </circle>
    </svg>
    <div class="brand">STINGA</div>
    <div class="sub">AI Finans Platformu · v15.0</div>
    <div class="welcome">{avatar} Hoş geldin, {user_name}</div>
  </div>

  <div class="divider"></div>

  <div class="prog-wrap">
    <div class="prog-bar"><div class="prog-fill" id="pf"></div></div>
    <div class="prog-lbl" id="pl">Sistem başlatılıyor</div>
  </div>
</div>

<div class="corner tl"></div>
<div class="corner tr"></div>
<div class="corner bl"></div>
<div class="corner br"></div>
<div class="scan"></div>
<div id="flash"></div>

<script>
// ── WEBGL SHADER ─────────────────────────────────
const cv = document.getElementById('c');
const gl = cv.getContext('webgl');
function rsz() {{
  cv.width  = window.innerWidth  * devicePixelRatio;
  cv.height = window.innerHeight * devicePixelRatio;
  cv.style.width  = window.innerWidth  + 'px';
  cv.style.height = window.innerHeight + 'px';
  gl.viewport(0,0,cv.width,cv.height);
}}
window.addEventListener('resize',rsz); rsz();

const vs = `attribute vec2 p; void main(){{gl_Position=vec4(p,0,1);}}`;
const fs = `
precision highp float;
uniform vec2 uR; uniform float uT;
#define TAU 6.2831853
vec2 warp(vec2 p,float t){{
  float a=atan(p.y,p.x),r=length(p);
  a+=.3*sin(r*3.-t*.8)+.15*cos(r*5.+t*.5);
  return vec2(cos(a),sin(a))*r;
}}
float ring(vec2 uv,float r,float w){{return smoothstep(w,.0,abs(length(uv)-r));}}
void main(){{
  vec2 uv=(gl_FragCoord.xy*2.-uR)/min(uR.x,uR.y);
  float t=uT*.4;
  float v=1.-smoothstep(.3,1.4,length(uv));
  vec3 col=mix(vec3(0.),vec3(.02,.05,.12),v);

  vec2 wp=warp(uv,t), wp2=warp(uv*.8,t*1.3+1.);
  float aur=0.;
  for(int i=0;i<5;i++){{
    float fi=float(i);
    float ph=fi*1.2+t*(.6+fi*.1);
    float b=sin(wp.x*(2.5+fi*.8)+ph)*.5+.5;
    b*=sin(wp2.y*(1.75+fi*.56)+ph*1.1)*.5+.5;
    aur+=b*(.18-fi*.025);
  }}
  aur=pow(aur,1.4);
  vec3 g1=vec3(0.,.91,.59),g2=vec3(.1,.62,.43),nav=vec3(.11,.19,.36);
  col+=mix(g2,g1,aur)*aur*1.8;

  float tp=mod(t*.7,1.);
  for(int k=0;k<6;k++){{
    float fk=float(k)/6.,ph=mod(fk+tp,1.);
    float al=(1.-ph)*(1.-ph);
    col+=ring(uv,ph*1.6,mix(.018,.004,ph))*al*mix(g1,nav,smoothstep(0.,1.6,length(uv)))*.9;
  }}
  col+=ring(uv,.35,.004)*g1*.45;

  float ang=atan(uv.y,uv.x),bm=0.;
  for(int b=0;b<8;b++){{
    float fb=float(b),ao=fb*TAU/8.+t*(.15+fb*.02);
    bm+=smoothstep(.06,.0,mod(ang-ao,TAU)/TAU)*.07;
  }}
  col+=bm*smoothstep(1.5,.1,length(uv))*g1*.6;
  col+=clamp(.06/(length(uv*.9)+.01)*.18,0.,.5)*mix(g1,vec3(1.),.3);
  float gr=fract(sin(dot(gl_FragCoord.xy,vec2(127.1+uT*.01,311.7+uT*.01)))*43758.5);
  col+=pow(max(col+(gr-.5)*.022,0.),vec3(.88));
  col=mix(col,col*vec3(.85,1.,.9),.25);
  gl_FragColor=vec4(col,1.);
}}`;

function sh(type,src){{const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);return s;}}
const pr=gl.createProgram();
gl.attachShader(pr,sh(gl.VERTEX_SHADER,vs));
gl.attachShader(pr,sh(gl.FRAGMENT_SHADER,fs));
gl.linkProgram(pr); gl.useProgram(pr);
const buf=gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER,buf);
gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
const ap=gl.getAttribLocation(pr,'p');
gl.enableVertexAttribArray(ap);
gl.vertexAttribPointer(ap,2,gl.FLOAT,false,0,0);
const uR=gl.getUniformLocation(pr,'uR'),uT=gl.getUniformLocation(pr,'uT');
let t0=null;
(function loop(ts){{
  if(!t0)t0=ts;
  gl.uniform2f(uR,cv.width,cv.height);
  gl.uniform1f(uT,(ts-t0)/1000);
  gl.drawArrays(gl.TRIANGLE_STRIP,0,4);
  requestAnimationFrame(loop);
}})(0);

// ── PROGRESS ─────────────────────────────────────
const pf=document.getElementById('pf'),pl=document.getElementById('pl');
const steps=[[15,'Güvenlik protokolleri'],[35,'AI motoru yükleniyor'],
             [55,'Gemini bağlantısı kuruldu'],[72,'Finans verileri çekiliyor'],
             [88,'Dashboard hazırlanıyor'],[100,'Giriş yapılıyor...']];
let si=0;
function tick(){{
  if(si>=steps.length)return;
  const[p,m]=steps[si++];
  pf.style.width=p+'%'; pl.textContent=m;
  if(si<steps.length){{setTimeout(tick,260+Math.random()*200);}}
  else{{
    setTimeout(()=>{{
      const fl=document.getElementById('flash');
      fl.style.transition='opacity .2s ease';
      fl.style.opacity='1';
      // Streamlit parent'a sinyal gönder
      setTimeout(()=>{{
        try{{window.parent.postMessage({{type:'splash_done'}},  '*');}}catch(e){{}}
        // Fallback: URL hash değiştir
        try{{window.parent.location.hash='splash_done';}}catch(e){{}}
      }},150);
    }},500);
  }}
}}
setTimeout(tick, 1600);
</script>
</body>
</html>
"""

    # Tam ekran component render et
    components.html(splash_html, height=800, scrolling=False)

    # Streamlit tarafı: belirli süre sonra splash_done=True yapıp rerun
    import time
    
    # Progress süresi ~3.5sn + 0.5sn flash = 4sn
    # st.empty() placeholder ile bekle
    placeholder = st.empty()
    
    with placeholder:
        time.sleep(4.2)
    
    placeholder.empty()
    st.session_state.splash_done = True
    st.rerun()


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
elif not st.session_state.splash_done:
    show_splash()
else:
    data_store = load_data()
    model = configure_ai()
    user_info = st.session_state.user_info
    user_name = user_info["name"]
    role = user_info["role"]

    # ── ROL BAZLI FİLTRELEME ──────────────────────────────────
    # admin (Zeynep, Serkan) → tüm fişleri görür + onaylayabilir
    # user  (Okan, Şenol)   → sadece kendi fişlerini görür
    df_full = pd.DataFrame(data_store.get("expenses", []))
    if role == "user" and not df_full.empty and "Kullanıcı" in df_full.columns:
        df = df_full[df_full["Kullanıcı"] == user_name].copy()
    else:
        df = df_full.copy()
    
    # ── SIDEBAR ──────────────────────────────────────────────
    with st.sidebar:
        logo_b64 = get_logo_b64()
        user_xp = data_store.get("xp", {}).get(user_name, 0)
        level = user_xp // 500 + 1
        xp_progress = (user_xp % 500) / 500
        my_notifs = [n for n in data_store.get("notifications", [])
                     if (n["user"] == user_name or n["user"] == "Hepsi") and not n.get("read", False)]
        notif_count = len(my_notifs)

        if not df_full.empty and 'Tutar' in df_full.columns:
            my_total = df_full[df_full['Kullanıcı'] == user_name]['Tutar'].sum() if 'Kullanıcı' in df_full.columns else 0
            monthly_limit = user_info.get('monthly_limit', 15000)
            usage_pct = min(my_total / monthly_limit * 100, 100) if monthly_limit > 0 else 0
        else:
            my_total = 0
            monthly_limit = user_info.get('monthly_limit', 15000)
            usage_pct = 0
        usage_color = "#3ecf8e" if usage_pct < 60 else ("#f0a500" if usage_pct < 85 else "#e03a48")
        role_labels = {"admin": "YÖNETİCİ", "user": "PERSONEL"}
        role_colors = {"admin": "#3ecf8e", "user": "#7eb8d4"}
        role_label = role_labels.get(role, role.upper())
        role_color = role_colors.get(role, "#00d4ff")

        # ── 1. LOGO
        logo_img_html = f'<img src="data:image/png;base64,{logo_b64}">' if logo_b64 else '<span style="font-size:2rem;">⚡</span>'
        st.markdown(f"""
        <div style="text-align:center; padding:28px 10px 12px;">
            <div class="slogo-frame" style="display:inline-block;">
                <div class="slogo-core">{logo_img_html}</div>
            </div>
            <div style="font-family:'Plus Jakarta Sans',sans-serif; font-size:0.88rem; font-weight:900;
                        letter-spacing:0.3em; color:#e8f2ec; margin-top:13px; text-transform:uppercase;">
                STINGA PRO
            </div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.51rem; color:rgba(122,154,138,0.55);
                        letter-spacing:0.18em; margin-top:4px; text-transform:uppercase;">
                STİNGA ENERJİ A.Ş.
            </div>
        </div>
        <div class="ssep"></div>
        """, unsafe_allow_html=True)

        # ── 2. USER CARD
        st.markdown(f"""
        <div class="suser-card">
            <div class="suser-top">
                <div class="suser-ava">{user_info['avatar']}</div>
                <div>
                    <div class="suser-name">{user_name}</div>
                    <div class="suser-role" style="color:{role_color};">{role_label} · LV.{level}</div>
                </div>
            </div>
            <div class="sxp-row">
                <span>⚡ {user_xp} XP</span>
                <span>→ {level * 500} XP</span>
            </div>
            <div class="sxp-track">
                <div class="sxp-fill" style="width:{xp_progress*100:.1f}%;"></div>
            </div>
            <div class="smeta">
                <span>{user_info.get('department','—')}</span>
                <span style="color:{usage_color}; font-weight:700;">%{usage_pct:.0f} limit</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── 3. NOTIFICATION
        if notif_count > 0:
            st.markdown(f"""
            <div class="snotif">
                <span>🔔</span>
                <span class="snotif-lbl">{notif_count} yeni bildirim</span>
                <span class="snotif-num">{notif_count}</span>
            </div>
            """, unsafe_allow_html=True)
            with st.expander("Bildirimleri Gör"):
                for n in reversed(my_notifs[-5:]):
                    icon = {"xp": "🏆", "info": "ℹ️", "warning": "⚠️", "success": "✅"}.get(n.get("type", "info"), "📌")
                    st.markdown(f"""
                    <div style="padding:7px 0; border-bottom:1px solid rgba(255,255,255,0.06);
                                display:flex; gap:9px; align-items:flex-start;">
                        <span>{icon}</span>
                        <div>
                            <div style="font-size:0.77rem; color:rgba(255,255,255,0.7);">{n['msg']}</div>
                            <div style="font-size:0.63rem; color:rgba(255,255,255,0.28); font-family:'JetBrains Mono',monospace; margin-top:1px;">{n.get('date','')} {n['time']}</div>
                        </div>
                    </div>""", unsafe_allow_html=True)

        # ── 4. SEPARATOR + NAV HEADER
        st.markdown('<div class="ssep" style="margin-top:6px;"></div><div class="snav-hdr">Navigasyon</div>', unsafe_allow_html=True)

        # ── 5. NAVIGATION (native Streamlit radio — styled via CSS)
        if role == "admin":
            pages_keys = [
                "🏠 Dashboard", "📑 Fiş Tarama", "💰 Finans & Kasa",
                "⚖️ Onay Merkezi", "🔬 Anomali Dedektörü", "📊 Analitik Merkezi",
                "🤖 AI Asistan", "🏆 Leaderboard", "🗄️ Arşiv & Rapor"
            ]
        else:
            pages_keys = [
                "🏠 Dashboard", "📑 Fiş Tarama", "💰 Finans & Kasa",
                "🤖 AI Asistan", "🏆 Leaderboard", "🗄️ Arşiv & Rapor"
            ]

        selected = st.radio("", pages_keys,
                           index=pages_keys.index(st.session_state.selected_page)
                           if st.session_state.selected_page in pages_keys else 0,
                           label_visibility="collapsed")
        st.session_state.selected_page = selected

        # ── 6. LIMIT BAR
        st.markdown(f"""
        <div class="ssep" style="margin-bottom:6px;"></div>
        <div class="slimit">
            <div class="slimit-lbl">Aylık Limit Kullanımı</div>
            <div class="slimit-row">
                <span class="slimit-pct" style="color:{usage_color};">{usage_pct:.0f}%</span>
                <span class="slimit-val">{my_total:,.0f} / {monthly_limit:,.0f} ₺</span>
            </div>
            <div class="slimit-bar">
                <div style="height:100%; width:{usage_pct:.0f}%; background:{usage_color};
                            box-shadow:0 0 8px {usage_color}99; border-radius:99px;
                            transition:width 1s ease;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── 7. LOGOUT
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⏻  Oturumu Kapat", use_container_width=True):
            logout()

    # ══════════════════════════════════════════════════════════
    # SAYFA: DASHBOARD
    # ══════════════════════════════════════════════════════════
    if selected == "🏠 Dashboard":
        st.markdown('<div class="page-header"><div class="page-title">OPERASYON MERKEZİ</div></div>', unsafe_allow_html=True)
        
        # KPI Row
        # Admin → tüm ekip verisi; user → sadece kendi
        _kpi_df = df_full if role == "admin" else df
        total_approved = _kpi_df[_kpi_df['Durum']=='Onaylandı']['Tutar'].sum() if not _kpi_df.empty and 'Durum' in _kpi_df.columns else 0
        total_pending  = _kpi_df[_kpi_df['Durum']=='Onay Bekliyor']['Tutar'].sum() if not _kpi_df.empty and 'Durum' in _kpi_df.columns else 0
        crit_risks     = len(_kpi_df[_kpi_df['Risk_Skoru'] > 70]) if not _kpi_df.empty and 'Risk_Skoru' in _kpi_df.columns else 0
        my_wallet      = data_store['wallets'].get(user_name, 0)
        total_tx       = len(_kpi_df) if not _kpi_df.empty else 0
        avg_risk       = _kpi_df['Risk_Skoru'].mean() if not _kpi_df.empty and 'Risk_Skoru' in _kpi_df.columns else 0
        
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
        if model and not df_full.empty:
            with st.expander("🤖 Günlük AI Finansal Brifingi", expanded=True):
                if st.button("⚡ Günlük Analizi Oluştur"):
                    with st.spinner("Gemini AI verilerini işliyor..."):
                        insight = generate_ai_insight(df_full if role == "admin" else df, model)
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

                                    # ── İş Kuralı Motoru Uygula ──
                                    data_ai = apply_business_rules(data_ai, data_store, user_name)
                                    uyarilar = data_ai.pop("_uyarilar", [])

                                    # Görseli hem lokal hem base64 olarak kaydet
                                    # base64 → bot'tan gelen WhatsApp fişlerinde de görsel görünsün
                                    yukleme_zamani = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    path = f"arsiv/{datetime.now().strftime('%Y_%m')}"
                                    os.makedirs(path, exist_ok=True)
                                    f_path = os.path.join(path, f"{datetime.now().strftime('%H%M%S')}_{f.name}")
                                    img_bytes = f.getbuffer()
                                    with open(f_path, "wb") as fp:
                                        fp.write(img_bytes)
                                    # base64 — DB'ye gömülü, server bağımsız görüntüleme
                                    gorsel_b64 = base64.b64encode(img_bytes).decode("utf-8")
                                    # mime type
                                    ext = f.name.rsplit(".", 1)[-1].lower()
                                    mime = {"jpg":"image/jpeg","jpeg":"image/jpeg","png":"image/png","webp":"image/webp"}.get(ext,"image/jpeg")
                                    gorsel_data_uri = f"data:{mime};base64,{gorsel_b64}"

                                    new_e = {
                                        "ID": datetime.now().strftime("%Y%m%d%H%M%S"),
                                        "Tarih": data_ai.get("tarih", datetime.now().strftime("%Y-%m-%d")),
                                        "Saat": data_ai.get("saat", ""),
                                        "Yukleme_Zamani": yukleme_zamani,
                                        "Kullanıcı": user_name,
                                        "Rol": user_info.get("role", "user"),
                                        "Firma": data_ai.get("firma", "Bilinmiyor"),
                                        "Kategori": data_ai.get("kategori", "Diğer"),
                                        "Tutar": float(data_ai.get("toplam_tutar", 0)),
                                        "KDV": float(data_ai.get("kdv_tutari", 0)),
                                        "Odeme_Turu": data_ai.get("odeme_turu", "Bilinmiyor"),
                                        "Kalemler": data_ai.get("kalemler", []),
                                        "Kisisel_Giderler": data_ai.get("kisisel_giderler", []),
                                        "Durum": "Onay Bekliyor",
                                        "Dosya_Yolu": f_path,
                                        "Gorsel_B64": gorsel_data_uri,
                                        "Risk_Skoru": int(data_ai.get("risk_skoru", 0)),
                                        "AI_Audit": data_ai.get("audit_ozeti", ""),
                                        "AI_Anomali": data_ai.get("anomali", False),
                                        "AI_Anomali_Aciklama": data_ai.get("anomali_aciklamasi", ""),
                                        "Proje": proje,
                                        "Oncelik": oncelik,
                                        "Notlar": notlar
                                    }
                                    
                                    # ── Railway API'ye gönder ──────────────────
                                    with st.spinner("Railway'e gönderiliyor..."):
                                        ok = api_add_expense(new_e)
                                    
                                    if not ok:
                                        st.error("❌ Fiş API'ye gönderilemedi. Railway bağlantısını kontrol edin.")
                                    else:
                                        # Show result
                                        risk = int(data_ai.get("risk_skoru", 0))
                                        anomali = data_ai.get("anomali", False)
                                        
                                        if role != "admin":
                                            st.success("✅ Fiş sisteme eklendi! +50 XP · ⏳ Onay için yönetici bildirildi.")
                                        else:
                                            st.success("✅ Fiş başarıyla işlendi! +50 XP kazandın!")
                                    
                                    # İş kuralı uyarıları
                                    for uyari in uyarilar:
                                        st.warning(uyari)
                                    
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
                                    {clean_audit(row.get('AI_Audit',''))[:80]}{'...' if len(clean_audit(row.get('AI_Audit',''))) > 80 else ''}
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
    # SAYFA: ONAY MERKEZİ (sadece admin)
    # ══════════════════════════════════════════════════════════
    elif selected == "⚖️ Onay Merkezi":
        st.markdown('<div class="page-header"><div class="page-title">ONAY MERKEZİ</div></div>', unsafe_allow_html=True)

        if role != "admin":
            st.warning("Bu sayfaya erişim yetkiniz bulunmamaktadır.")
        else:
            pending = df_full[df_full["Durum"] == "Onay Bekliyor"] if not df_full.empty and 'Durum' in df_full.columns else pd.DataFrame()
            sahte_s = df_full[df_full["Durum"] == "Sahte Şüphesi"] if not df_full.empty and 'Durum' in df_full.columns else pd.DataFrame()

            col_om1, col_om2 = st.columns(2)
            col_om1.metric("⏳ Onay Bekleyen", len(pending), f"₺{pending['Tutar'].sum():,.0f}" if not pending.empty else "₺0")
            col_om2.metric("🚨 Sahte Şüphesi", len(sahte_s))
            st.markdown("<br>", unsafe_allow_html=True)

            if pending.empty and sahte_s.empty:
                st.markdown("""
                <div class="ultra-card" style="text-align:center; padding:48px;">
                    <div style="font-size:3rem;">✅</div>
                    <div style="font-size:1.3rem; font-weight:700; color:#007850; margin:12px 0;">Onay Bekleyen İşlem Yok</div>
                    <div style="color:var(--text-muted);">Tüm fişler işlenmiş.</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                tum_bekleyen = pd.concat([pending, sahte_s]).drop_duplicates("ID") if not pending.empty or not sahte_s.empty else pd.DataFrame()
                for idx_r, row in tum_bekleyen.sort_values("Tutar", ascending=False).iterrows():
                    risk = row.get('Risk_Skoru', 0)
                    kaynak_icon = "📱" if row.get("Kaynak") == "WhatsApp" else "💻"
                    with st.expander(f"{'🔴' if risk > 70 else '🟡'} {kaynak_icon} {row.get('Kullanıcı','?')} · {row.get('Firma','?')} · ₺{float(row.get('Tutar',0)):,.0f} · {row.get('Proje','?')}"):
                        ca, cb = st.columns([2, 1])
                        with ca:
                            st.markdown(f"""
                            <div class="ultra-card">
                                <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
                                    <div>
                                        <div style="font-size:1.1rem; font-weight:700;">{row.get('Firma','?')}</div>
                                        <div style="font-size:0.8rem; color:var(--text-muted);">{row.get('Tarih','?')} · {row.get('Kategori','?')} · {kaynak_icon} {row.get('Kaynak','Dashboard')}</div>
                                    </div>
                                    <div style="text-align:right;">
                                        <div style="font-family:'Bebas Neue'; font-size:2rem; color:var(--accent-blue);">₺{float(row.get('Tutar',0)):,.0f}</div>
                                        {get_risk_html(risk)}
                                        {get_status_html(row.get('Durum','?'))}
                                    </div>
                                </div>
                                <div class="ai-bubble">🤖 {clean_audit(row.get('AI_Audit',''))}</div>
                                {"<div class='anomaly-alert' style='margin-top:8px;'>⚠️ " + str(row.get('AI_Anomali_Aciklama','')) + "</div>" if row.get('AI_Anomali') else ""}
                                <div style="margin-top:8px; font-size:0.75rem; color:var(--text-muted);">
                                    Proje: {row.get('Proje','?')} · Öncelik: {row.get('Oncelik','Normal')} · Ödeme: {row.get('Odeme_Turu', row.get('OdemeTipi','?'))}
                                </div>
                                {f"<div style='margin-top:6px; font-size:0.75rem;'>📝 {row.get('Notlar','')}</div>" if row.get('Notlar') else ""}
                            </div>
                            """, unsafe_allow_html=True)

                            btn1, btn2 = st.columns(2)
                            if btn1.button("✅ Onayla", key=f"omcent_on_{row['ID']}", use_container_width=True):
                                with st.spinner("Onaylanıyor..."):
                                    if api_approve(str(row['ID']), "approve", user_name):
                                        st.success("✅ Onaylandı!")
                                        time.sleep(0.5)
                                        st.rerun()
                                    else:
                                        st.error("API hatası, tekrar deneyin")

                            if btn2.button("❌ Reddet", key=f"omcent_ret_{row['ID']}", use_container_width=True):
                                with st.spinner("Reddediliyor..."):
                                    if api_approve(str(row['ID']), "reject", user_name):
                                        st.warning("❌ Reddedildi!")
                                        time.sleep(0.5)
                                        st.rerun()
                                    else:
                                        st.error("API hatası, tekrar deneyin")

                        with cb:
                            dosya   = row.get('Dosya_Yolu', '')
                            b64_uri = row.get('Gorsel_B64', '')
                            if dosya and os.path.exists(str(dosya)):
                                st.image(str(dosya), caption="Orijinal Fiş", use_container_width=True)
                            elif b64_uri:
                                try:
                                    header, b64_data = b64_uri.split(",", 1) if "," in b64_uri else ("", b64_uri)
                                    img_bytes = base64.b64decode(b64_data)
                                    st.image(img_bytes, caption="📱 WhatsApp'tan gönderildi", use_container_width=True)
                                except Exception:
                                    st.markdown("""<div style="height:150px;background:var(--bg-secondary);border-radius:10px;
                                        display:flex;align-items:center;justify-content:center;color:var(--text-muted);">📷 Görsel Yüklenemedi</div>""",
                                        unsafe_allow_html=True)
                            else:
                                st.markdown("""<div style="height:150px;background:var(--bg-secondary);border-radius:10px;
                                    display:flex;align-items:center;justify-content:center;color:var(--text-muted);">📷 Görsel Yok</div>""",
                                    unsafe_allow_html=True)

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
                    # "Şenol" → "senol" key ile USERS'dan bul
                    _ukey = person.lower().replace("ş","s").replace("ı","i").replace("ö","o").replace("ü","u").replace("ğ","g").replace("ç","c")
                    person_limit = USERS.get(_ukey, USERS.get(person.lower(), {})).get("monthly_limit", 15000)
                    bal_pct = min(bal / person_limit * 100, 100) if person_limit > 0 else 0
                    avatar = USERS.get(_ukey, USERS.get(person.lower(), {})).get("avatar", "👤")
                    
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
                        with st.spinner("Transfer yapılıyor..."):
                            if api_transfer(target, amt, aciklama, user_name):
                                st.success(f"✅ {target}'e ₺{amt:,.0f} transfer edildi!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("Transfer başarısız, tekrar deneyin")
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
            
            # Admin tüm bekleyen fişleri görür
            pending = df_full[df_full["Durum"] == "Onay Bekliyor"] if not df_full.empty and 'Durum' in df_full.columns else pd.DataFrame()
            
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
                                    🤖 {clean_audit(row.get('AI_Audit',''))}
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
                                with st.spinner("Onaylanıyor..."):
                                    if api_approve(str(row['ID']), "approve", user_name):
                                        st.success("✅ Onaylandı!")
                                        time.sleep(0.5)
                                        st.rerun()
                            
                            if btn2.button("❌ Reddet", key=f"ret_{row['ID']}", use_container_width=True):
                                with st.spinner("Reddediliyor..."):
                                    if api_approve(str(row['ID']), "reject", user_name):
                                        st.warning("❌ Reddedildi!")
                                        time.sleep(0.5)
                                        st.rerun()
                        
                        with cb:
                            # Önce lokal dosyayı dene, sonra base64 (WhatsApp fişleri için)
                            dosya   = row.get('Dosya_Yolu', '')
                            b64_uri = row.get('Gorsel_B64', '')
                            if dosya and os.path.exists(dosya):
                                st.image(dosya, caption="Orijinal Fiş", use_container_width=True)
                            elif b64_uri:
                                try:
                                    header, b64_data = b64_uri.split(",", 1) if "," in b64_uri else ("", b64_uri)
                                    img_bytes = base64.b64decode(b64_data)
                                    st.image(img_bytes, caption="📱 WhatsApp'tan gönderilen fiş", use_container_width=True)
                                except Exception:
                                    st.markdown("""
                                    <div style="height:150px; background:var(--bg-secondary); border-radius:10px; 
                                                display:flex; align-items:center; justify-content:center; color:var(--text-muted);">
                                        📷 Görsel Yüklenemedi
                                    </div>
                                    """, unsafe_allow_html=True)
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
        
        if not df_full.empty:
            anomalies = detect_anomalies(df_full if role == "admin" else df, model)
            
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
                        
                        # AI insight sadece session'da tut (Railway'e yazmıyoruz)
                        if "ai_insights" not in st.session_state:
                            st.session_state.ai_insights = []
                        st.session_state.ai_insights.append({
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "type": "anomaly_scan",
                            "content": response.text
                        })
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
        
        xp_data = data_store.get("xp", {"Zeynep": 1250, "Serkan": 890, "Okan": 430, "Şenol": 600})
        sorted_users = sorted(xp_data.items(), key=lambda x: x[1], reverse=True)
        
        rank_icons = ["🥇", "🥈", "🥉"]
        rank_classes = ["gold", "silver", "bronze"]
        
        st.markdown("### 🏆 XP Sıralaması")
        
        for i, (uname, xp) in enumerate(sorted_users):
            _lb_key = uname.lower().replace("ş","s").replace("ı","i").replace("ö","o").replace("ü","u").replace("ğ","g").replace("ç","c")
            user_data = USERS.get(_lb_key, USERS.get(uname.lower(), {}))
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
                                {clean_audit(satir.get('AI_Audit',''))}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_img:
                        dosya   = satir.get('Dosya_Yolu', '')
                        b64_uri = satir.get('Gorsel_B64', '')
                        if dosya and os.path.exists(dosya):
                            st.image(dosya, caption=f"Orijinal Fiş — {islem_id}", use_container_width=True)
                        elif b64_uri:
                            try:
                                header, b64_data = b64_uri.split(",", 1) if "," in b64_uri else ("", b64_uri)
                                img_bytes = base64.b64decode(b64_data)
                                st.image(img_bytes, caption=f"📱 WhatsApp Fişi — {islem_id}", use_container_width=True)
                            except Exception:
                                st.markdown(f"""
                                <div style="height:300px; background:var(--bg-secondary); border-radius:16px; 
                                            display:flex; flex-direction:column; align-items:center; justify-content:center;
                                            color:var(--text-muted); border:2px dashed var(--border);">
                                    <div style="font-size:3rem; opacity:0.3;">📷</div>
                                    <div style="font-size:0.85rem; margin-top:8px;">Görsel yüklenemedi</div>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style="height:300px; background:var(--bg-secondary); border-radius:16px; 
                                        display:flex; flex-direction:column; align-items:center; justify-content:center;
                                        color:var(--text-muted); border:2px dashed var(--border);">
                                <div style="font-size:3rem; opacity:0.3;">📷</div>
                                <div style="font-size:0.85rem; margin-top:8px;">Görsel bulunamadı</div>
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
