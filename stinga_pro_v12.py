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
# ────────────────────────────────────────────────────────────────
#  YENİ EKLENEN KÜTÜPHANELER
# ────────────────────────────────────────────────────────────────
from streamlit_autorefresh import st_autorefresh
from sklearn.ensemble import IsolationForest
import numpy as np

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

    /* SIDEBAR — açık tema */
    --sb:        #ffffff;
    --sb-s:      #f4f7f5;
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
    box-shadow: 4px 0 16px rgba(0,0,0,0.06) !important;
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
    color: #5a7a6a !important; cursor: pointer !important;
    transition: all 0.16s ease !important; letter-spacing: 0.01em !important;
    position: relative !important;
}
[data-testid="stSidebar"] .stRadio label::before {
    content: ''; position: absolute; left: 0; top: 18%; bottom: 18%;
    width: 3px; border-radius: 0 3px 3px 0;
    background: var(--sg); opacity: 0; transition: opacity 0.15s;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(17,133,91,0.07) !important;
    color: #11855B !important;
    border-color: rgba(17,133,91,0.15) !important;
    transform: translateX(4px) !important;
}
[data-testid="stSidebar"] .stRadio label:hover::before { opacity: 0.6 !important; }
[data-testid="stSidebar"] .stRadio label[data-checked="true"] {
    background: linear-gradient(90deg,rgba(17,133,91,0.1),rgba(17,133,91,0.03)) !important;
    color: var(--sg) !important;
    border-color: rgba(17,133,91,0.22) !important; font-weight: 700 !important;
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
    0%,100% { transform: scale(0.97); filter: drop-shadow(0 2px 8px rgba(17,133,91,0.15)); }
    50%     { transform: scale(1.06); filter: drop-shadow(0 6px 22px rgba(17,133,91,0.5)); }
}
.slogo-frame::after {
    content: ''; position: absolute; inset: -5px; border-radius: 50%;
    border: 1.5px solid rgba(17,133,91,0.4);
    animation: sRing 4s ease-in-out infinite; pointer-events: none;
}
@keyframes sRing {
    0%,100% { transform: scale(1); opacity: 0.6; }
    50%     { transform: scale(1.18); opacity: 0; }
}
.slogo-core {
    background: transparent; border-radius: 50%; padding: 4px;
    display: flex; align-items: center; justify-content: center;
    width: 96px; height: 96px;
}
.slogo-core img { width: 88px; height: 88px; object-fit: contain; border-radius: 50%; }

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
.suser-card:hover .suser-ava { transform: scale(1.08) rotate(-4deg); }
.suser-name { font-size: 0.93rem; font-weight: 700; color: #0f1923 !important; }
.suser-role { font-family: 'JetBrains Mono',monospace; font-size: 0.59rem; margin-top: 3px; letter-spacing: 0.1em; }
.sxp-row { display:flex; justify-content:space-between; font-family:'JetBrains Mono',monospace; font-size:0.58rem; color:#7a96a4 !important; margin:10px 0 4px; }
.sxp-track { height: 3px; background: rgba(0,0,0,0.08); border-radius:99px; position: relative; overflow: visible; }
.sxp-fill { height: 100%; border-radius:99px; background: linear-gradient(90deg,var(--sg-lo),var(--sg)); position: relative; }
.sxp-fill::after { content:''; position:absolute; right:-1px; top:50%; transform:translateY(-50%); width:7px; height:7px; background:var(--sg); border-radius:50%; box-shadow:0 0 6px rgba(17,133,91,0.5); }
.smeta { display:flex; justify-content:space-between; margin-top:9px; font-family:'JetBrains Mono',monospace; font-size:0.58rem; color:#7a96a4 !important; }
.ssep { height:1px; background:linear-gradient(90deg,transparent,rgba(17,133,91,0.2),transparent); margin:5px 12px; }

.snotif {
    margin:5px 10px; padding:9px 13px;
    background:rgba(220,38,38,0.06); border:1px solid rgba(220,38,38,0.18);
    border-radius:10px; display:flex; align-items:center; gap:8px;
    animation:snotifP 2.5s ease-in-out infinite;
}
.snotif:hover { background:rgba(220,38,38,0.1); border-color:rgba(220,38,38,0.3); }
@keyframes snotifP { 0%,100%{box-shadow:none;}50%{box-shadow:0 0 0 4px rgba(220,38,38,0.05);} }
.snotif-lbl { font-size:0.72rem; font-weight:600; color:#dc2626 !important; flex:1; }
.snotif-num { background:var(--red); color:#fff !important; font-size:0.58rem; font-weight:700; padding:2px 6px; border-radius:99px; font-family:'JetBrains Mono',monospace; }
.snav-hdr { font-family:'JetBrains Mono',monospace; font-size:0.51rem; color:#a0b8ae !important; letter-spacing:0.2em; padding:6px 18px 3px; text-transform:uppercase; }

.slimit { margin:5px 10px 10px; padding:13px 15px; background:var(--sb-s); border:1px solid rgba(17,133,91,0.12); border-radius:14px; transition:all 0.22s ease; }
.slimit:hover { border-color:rgba(17,133,91,0.26); }
.slimit-lbl { font-family:'JetBrains Mono',monospace; font-size:0.51rem; color:#a0b8ae !important; letter-spacing:0.16em; text-transform:uppercase; margin-bottom:6px; }
.slimit-row { display:flex; justify-content:space-between; align-items:baseline; margin-bottom:6px; }
.slimit-pct { font-size:1.3rem; font-weight:800; font-family:'Plus Jakarta Sans',sans-serif; color:#0f1923; }
.slimit-val { font-family:'JetBrains Mono',monospace; font-size:0.54rem; color:#7a96a4 !important; }
.slimit-bar { height:4px; background:rgba(0,0,0,0.07); border-radius:99px; overflow:hidden; }

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
    0%,100% { transform: scale(0.97); filter: drop-shadow(0 6px 20px rgba(17,133,91,0.2)); }
    50%     { transform: scale(1.04); filter: drop-shadow(0 10px 36px rgba(17,133,91,0.45)); }
}
.login-logo-ring {
    position: absolute; inset: -10px; border-radius: 50%;
    border: 2px solid rgba(17,133,91,0.45);
    animation: loginRing 3.5s ease-in-out infinite;
    pointer-events: none;
}
.login-logo-ring2 {
    position: absolute; inset: -20px; border-radius: 50%;
    border: 1.5px solid rgba(47,60,110,0.25);
    animation: loginRing 3.5s ease-in-out infinite 0.5s;
    pointer-events: none;
}
@keyframes loginRing {
    0%,100% { transform: scale(1); opacity: 0.7; }
    50%     { transform: scale(1.22); opacity: 0; }
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

def add_notification(target: str, message: str, notif_type: str = "info", data: dict = None):
    """d verilirse kaydetmez, sadece objeye yazar (atomic save için)."""
    _own = data is None
    if _own:
        data = load_data()
    data.setdefault("notifications", []).append({
        "user": target,
        "msg": message,
        "type": notif_type,
        "time": datetime.now().strftime("%H:%M"),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "read": False
    })
    if _own:
        save_data(data)

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

# ─────────────────────────────────────────────
#  GELİŞMİŞ YAPAY ZEKA VE ANOMALİ FONKSİYONLARI
# ─────────────────────────────────────────────

def compute_budget_forecast(project: str, data: dict) -> tuple:
    """
    Proje bazlı bütçe tahmini yapar.
    Dönüş: (tahmini_aşım_yüzdesi, uyarı_mesajı, uyarı_seviyesi)
    """
    budgets = data.get("budgets", {})
    if project not in budgets:
        return 0, "", "ok"
    
    limit = budgets[project].get("limit", 0)
    spent = budgets[project].get("spent", 0)
    
    # Bu ayki harcamaları hesapla (tüm verilerden)
    bu_ay = datetime.now().strftime("%Y-%m")
    ay_harcamalari = [
        e["Tutar"] for e in data.get("expenses", [])
        if e.get("Proje") == project and e.get("Tarih", "").startswith(bu_ay)
    ]
    ay_top = sum(ay_harcamalari)
    
    if limit == 0:
        return 0, "", "ok"
    
    gun = datetime.now().day
    if gun == 0:
        return 0, "", "ok"
    
    gunluk_ort = ay_top / gun
    kalan_gun = 30 - gun
    tahmini_bitis = ay_top + gunluk_ort * kalan_gun
    asim_yuzde = max(0, (tahmini_bitis - limit) / limit * 100)
    
    if asim_yuzde > 15:
        seviye = "high"
        mesaj = f"⚠️ **{project}** projesi bu gidişle bütçesini %{asim_yuzde:.0f} aşacak!"
    elif asim_yuzde > 5:
        seviye = "medium"
        mesaj = f"⚡ **{project}** projesi bütçe sınırına yaklaşıyor (%{asim_yuzde:.0f} aşım riski)."
    else:
        seviye = "ok"
        mesaj = ""
    
    return asim_yuzde, mesaj, seviye


def auto_approve_receipt(expense: dict, data: dict) -> bool:
    """
    Düşük riskli fişleri otomatik onaylar.
    Koşullar: risk skoru < 20, tutar < 300 TL, proje bütçesi yeterli.
    """
    risk = expense.get("Risk_Skoru", 100)
    tutar = expense.get("Tutar", 0)
    proje = expense.get("Proje", "")
    kullanici = expense.get("Kullanıcı", "")
    
    # Otomatik onay koşulları
    if risk < 20 and tutar < 300:
        # Proje bütçesi kontrolü
        proje_butce = data.get("budgets", {}).get(proje, {}).get("limit", 0)
        proje_harcanan = data.get("budgets", {}).get(proje, {}).get("spent", 0)
        if proje_butce - proje_harcanan >= tutar:
            # API'ye onay isteği gönder
            res = _api_post("/approve", {
                "ID": expense["ID"],
                "action": "approve",
                "approver": "auto_system"
            })
            if res.get("ok"):
                # Kullanıcıya bildirim ekle
                add_notification(kullanici,
                    f"✅ {expense.get('Firma','?')} (₺{tutar:,.0f}) fişiniz otomatik onaylandı (risk düşük).",
                    "success",
                    data=data
                )
                return True
    return False


def personalized_ai_tips(user_name: str, data: dict, model) -> str:
    """
    Kullanıcının harcama alışkanlıklarına göre kişiselleştirilmiş tasarruf önerileri üretir.
    """
    kullanici_harcamalari = [
        e for e in data.get("expenses", [])
        if e["Kullanıcı"] == user_name
    ]
    if len(kullanici_harcamalari) < 5:
        return "Henüz yeterli veri yok. Daha fazla fiş yükledikten sonra size özel öneriler sunabileceğiz."
    
    # Kategori bazlı analiz
    kategori_toplam = defaultdict(float)
    for e in kullanici_harcamalari:
        kategori_toplam[e.get("Kategori", "diger")] += e["Tutar"]
    
    en_cok_harcama_kat = max(kategori_toplam, key=kategori_toplam.get)
    en_cok_tutar = kategori_toplam[en_cok_harcama_kat]
    
    # Bu ayki harcama
    bu_ay = datetime.now().strftime("%Y-%m")
    ay_top = sum(e["Tutar"] for e in kullanici_harcamalari if e["Tarih"].startswith(bu_ay))
    
    prompt = f"""
    Kullanıcı: {user_name}
    Harcama verileri:
    - Toplam harcama: {sum(e['Tutar'] for e in kullanici_harcamalari):.0f} TL
    - En çok harcama yapılan kategori: {en_cok_harcama_kat} (₺{en_cok_tutar:,.0f})
    - Bu ayki harcama: ₺{ay_top:,.0f}
    
    Bu kullanıcıya 2-3 cümlelik kişisel finans tavsiyesi ver. Örneğin:
    - "Bu ay {en_cok_harcama_kat} harcamaların biraz yüksek. Belki {en_cok_harcama_kat} kategorisinde tasarruf yapabilirsin."
    - "Geçen aya göre harcaman %X arttı, dikkat et."
    - "Şu ana kadar bütçeni iyi yönetiyorsun, tebrikler!"
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "AI önerileri şu an oluşturulamıyor."


def advanced_anomaly_detection(df: pd.DataFrame) -> list:
    """
    Isolation Forest ile makine öğrenmesi tabanlı anomali tespiti.
    """
    if df.empty or len(df) < 10:
        return []
    
    # Özellik mühendisliği
    df_ml = df.copy()
    df_ml['Tarih'] = pd.to_datetime(df_ml['Tarih'], errors='coerce')
    df_ml['gun'] = df_ml['Tarih'].dt.day
    df_ml['ay'] = df_ml['Tarih'].dt.month
    df_ml['yil'] = df_ml['Tarih'].dt.year
    df_ml['hafta_sonu'] = (df_ml['Tarih'].dt.dayofweek >= 5).astype(int)
    
    # Kategorik değişkenleri one-hot encode et
    df_ml = pd.get_dummies(df_ml, columns=['Kategori', 'Proje'], drop_first=True)
    
    # Sayısal sütunları seç
    numeric_cols = ['Tutar', 'Risk_Skoru', 'gun', 'ay', 'hafta_sonu'] + \
                   [c for c in df_ml.columns if c.startswith('Kategori_') or c.startswith('Proje_')]
    
    # Eksik sütunları doldur
    X = df_ml[numeric_cols].fillna(0)
    
    # Isolation Forest modeli
    model = IsolationForest(contamination=0.05, random_state=42)
    preds = model.fit_predict(X)
    
    # Anomali olan satırlar
    anomalies = df[preds == -1]
    
    result = []
    for _, row in anomalies.iterrows():
        result.append({
            "type": "ml_anomaly",
            "severity": "high",
            "message": f"🤖 ML modeli anomali tespit etti: {row.get('Firma','?')} - ₺{row.get('Tutar',0):,.0f}",
            "details": row.to_dict()
        })
    return result


def enhanced_nl_query(question: str, df: pd.DataFrame, model) -> str:
    """
    Doğal dil sorgusunu işler ve veriye dayalı cevap üretir.
    """
    if df.empty:
        return "Veri yok."
    
    # Özet istatistikler
    toplam = df['Tutar'].sum() if 'Tutar' in df.columns else 0
    ortalama = df['Tutar'].mean() if 'Tutar' in df.columns else 0
    max_tutar = df['Tutar'].max() if 'Tutar' in df.columns else 0
    max_firma = df.loc[df['Tutar'].idxmax(), 'Firma'] if not df.empty and 'Tutar' in df.columns else "?"
    
    prompt = f"""
    Kullanıcı sorusu: "{question}"
    
    Veri özeti:
    - Toplam harcama: {toplam:,.0f} TL
    - Ortalama harcama: {ortalama:,.0f} TL
    - En yüksek harcama: {max_tutar:,.0f} TL (Firma: {max_firma})
    
    Lütfen kullanıcının sorusunu verilere dayanarak cevapla. Eğer soru belirli bir kategori, proje veya zaman dilimi istiyorsa, veriyi filtrele ve net bir sayısal cevap ver.
    Cevap kısa ve öz olsun, gereksiz bilgi ekleme.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Hata: {str(e)}"

# ─── AI FONKSİYONLARI ─────────────────────────────────────────

def ai_call(prompt: str) -> str:
    resp = client.models.generate_content(model=MODEL_NAME, contents=[prompt])
    return resp.text.strip()


def psikolojik_profil(user_name: str, data: dict) -> str:
    """Harcama verilerinden psikolojik/davranışsal profil çıkar."""
    harcamalar = [e for e in data["expenses"] if e["Kullanıcı"] == user_name]
    if len(harcamalar) < 3:
        return ""

    prompt = f"""
Sen davranışsal ekonomi uzmanısın. Aşağıdaki harcama verilerini analiz et.

Harcamalar: {json.dumps(harcamalar[-30:], ensure_ascii=False)}

Kişinin harcama psikolojisini 2-3 cümleyle analiz et. Şunlara bak:
- Harcama zamanlaması (sabah mı, akşam mı? hafta sonu mu?)
- Kategori alışkanlıkları (impulsif mi, planlı mı?)
- Tutar örüntüleri (yuvarlak mı, küsuratlı mı?)
- Genel davranış tipi (tutumluluk mu, savurganlık mı?)

Türkçe, kısa, özgün ve biraz esprili yaz. Emoji kullan.
"""
    try:
        return ai_call(prompt)
    except:
        return ""


def yaratici_yorum(fis_data: dict, user_name: str, karakter: str) -> str:
    """
    Her fişe özgü yaratıcı AI yorumu üretir.
    Karakter moduna göre ton değişir.
    """
    karakter_talimatlari = {
        "dedektif": "Sen sert bir mali dedektifsin. Fişi sorguyla, şüpheyle yaklaş, ipuçları ara.",
        "koc":      "Sen motive edici bir finansal koçsun. Pozitif, cesaretlendirici, aksiyon odaklı konuş.",
        "muhaseci": "Sen kuru ama keskin bir muhasecsin. Rakamları önemse, detaylara odaklan.",
        "yoda":     "Sen Yoda gibi konuş. Ters cümle yapısı kullan, derin ama kısa ol.",
        "hemsire":  "Sen şefkatli ama dürüst bir finansal terapistsin. Empatiyle yaklaş.",
    }

    talimat = karakter_talimatlari.get(karakter, karakter_talimatlari["koc"])

    prompt = f"""
{talimat}

Fiş bilgileri:
- Firma: {fis_data.get('firma', '?')}
- Tutar: {fis_data.get('toplam_tutar', 0)} TL
- Kategori: {fis_data.get('kategori', '?')}
- Ödeme: {fis_data.get('odeme_yontemi', '?')}
- Risk skoru: {fis_data.get('risk_skoru', 0)}/100

Kullanıcı adı: {user_name}

Bu fişe özel, 1-2 cümle yaratıcı yorum yap. Karakterine sadık kal.
Türkçe yaz, emoji kullan, klişeden kaçın.
"""
    try:
        return ai_call(prompt)
    except:
        return ""


def harcama_kehaneti(user_name: str, data: dict) -> str:
    """Mevcut harcama temposuna göre kehanetvari uyarı üretir."""
    bu_ay = datetime.now().strftime("%Y-%m")
    gun   = datetime.now().day
    ay_harcamalar = [
        e for e in data["expenses"]
        if e["Kullanıcı"] == user_name and e.get("Tarih", "").startswith(bu_ay)
    ]
    if not ay_harcamalar or gun == 0:
        return ""

    toplam  = sum(e["Tutar"] for e in ay_harcamalar)
    butce   = data.get("user_limits", {}).get(user_name, 0)
    if butce == 0:
        return ""

    gunluk_ort = toplam / gun
    kalan_gun  = 30 - gun
    tahmini_bitis = toplam + (gunluk_ort * kalan_gun)
    asim_miktari  = tahmini_bitis - butce

    if asim_miktari <= 0:
        return ""

    asim_gunu = int((butce - toplam) / gunluk_ort) if gunluk_ort > 0 else 999
    bitis_tarihi = (datetime.now() + timedelta(days=asim_gunu)).strftime("%d %B")

    prompt = f"""
Sen kıyamet habercisi bir finansal astrologlsun (ama veriye dayalı).

Durum:
- Kullanıcı: {user_name}
- Günlük harcama ortalaması: {gunluk_ort:.0f} TL
- Bu gidişle bütçe {bitis_tarihi} tarihinde biter
- Tahmini aşım: {asim_miktari:.0f} TL

Bunu dramatik ama esprili, 1 cümleyle ifade et. Türkçe. Emoji ekle.
"""
    try:
        return ai_call(prompt)
    except:
        return f"🔮 Bu gidişle bütçen {bitis_tarihi}'de tükeniyor! ({asim_miktari:.0f} ₺ aşım)"


def derin_sahtelik_analizi(fis_data: dict, image: Image.Image) -> dict:
    """
    Çok katmanlı sahtelik skoru:
    - AI görsel analizi
    - Matematiksel tutarlılık (KDV kontrolü)
    - İstatistiksel örüntü
    """
    sonuc = {
        "sahte_mi": fis_data.get("sahte_mi", False),
        "guvensizlik_skoru": fis_data.get("risk_skoru", 0),
        "bulgular": [],
    }

    # KDV matematiksel kontrol
    toplam = float(fis_data.get("toplam_tutar", 0))
    kdv    = float(fis_data.get("kdv_tutari", 0))
    if kdv > 0 and toplam > 0:
        beklenen_kdv_20 = toplam * 0.20 / 1.20
        beklenen_kdv_10 = toplam * 0.10 / 1.10
        kdv_tutarsiz = abs(kdv - beklenen_kdv_20) > 1 and abs(kdv - beklenen_kdv_10) > 1
        if kdv_tutarsiz:
            sonuc["bulgular"].append("⚠️ KDV matematiksel tutarsızlık")
            sonuc["guvensizlik_skoru"] = min(100, sonuc["guvensizlik_skoru"] + 20)

    # Yuvarlak tutar şüphesi (tam yuvarlak = elle yazılmış olabilir)
    if toplam > 0 and toplam == int(toplam) and toplam % 100 == 0:
        sonuc["bulgular"].append("🔍 Şüpheli yuvarlak tutar")
        sonuc["guvensizlik_skoru"] = min(100, sonuc["guvensizlik_skoru"] + 10)

    # AI'dan gelen risk nedenleri
    for neden in fis_data.get("risk_nedenleri", []):
        if neden and neden != "...":
            sonuc["bulgular"].append(f"• {neden}")

    return sonuc


def ekip_siralaması(data: dict) -> str:
    """Tüm ekibin bu ayki harcama sıralaması."""
    bu_ay = datetime.now().strftime("%Y-%m")
    satirlar = []
    siralama = []

    for phone, info in PHONE_DIRECTORY.items():
        user = info["ad"]
        toplam = sum(
            e["Tutar"] for e in data["expenses"]
            if e["Kullanıcı"] == user and e.get("Tarih", "").startswith(bu_ay)
        )
        butce = data.get("user_limits", {}).get(user, info.get("limit", 1))
        oran  = (toplam / butce) * 100
        fis   = data["fis_sayaci"].get(user, 0)
        siralama.append((user, toplam, oran, fis, info["emoji"]))

    siralama.sort(key=lambda x: x[1], reverse=True)
    madalyalar = ["🥇", "🥈", "🥉"]

    for i, (user, toplam, oran, fis, emoji) in enumerate(siralama):
        madalya = madalyalar[i] if i < 3 else "  "
        seviye  = seviye_hesapla(fis)
        satirlar.append(
            f"{madalya} {emoji} {user}\n"
            f"   💰 {toplam:,.0f} ₺ (%{oran:.0f} bütçe)\n"
            f"   {seviye} • {fis} fiş"
        )

    return "\n\n".join(satirlar)


def anomali_tespit(user_name: str, tutar: float, data: dict) -> list[str]:
    uyarilar = []
    kullanici_harcamalari = [
        e["Tutar"] for e in data["expenses"]
        if e["Kullanıcı"] == user_name and e["Tutar"] > 0
    ]
    user_limit = data.get("user_limits", {}).get(user_name, 0)
    if user_limit > 0 and tutar > user_limit:
        uyarilar.append(f"⚠️ Limit aşımı! ({tutar:.0f} ₺ > {user_limit:.0f} ₺)")
    if len(kullanici_harcamalari) >= 5:
        ort = statistics.mean(kullanici_harcamalari)
        std = statistics.stdev(kullanici_harcamalari)
        if std > 0 and (tutar - ort) / std > 2.5:
            uyarilar.append(f"📊 Ortalamanın çok üzerinde! (Ort: {ort:.0f} ₺)")
    bugun = datetime.now().strftime("%Y-%m-%d")
    bugun_fis = [e for e in data["expenses"] if e["Kullanıcı"] == user_name and e["Tarih"] == bugun]
    if len(bugun_fis) >= 5:
        uyarilar.append(f"⚡ Bugün {len(bugun_fis)} fiş girildi!")
    return uyarilar


def butce_durumu_str(user_name: str, data: dict) -> str:
    bu_ay    = datetime.now().strftime("%Y-%m")
    ay_top   = sum(e["Tutar"] for e in data["expenses"]
                   if e["Kullanıcı"] == user_name and e.get("Tarih","").startswith(bu_ay))
    butce    = data["budgets"].get(user_name, 0)
    if butce == 0:
        return ""
    oran     = (ay_top / butce) * 100
    bar_dolu = min(10, int(oran / 10))
    bar      = "█" * bar_dolu + "░" * (10 - bar_dolu)
    return f"[{bar}] %{oran:.1f} ({ay_top:.0f}/{butce:.0f} ₺)"


def nl_sorgu(soru: str, user_name: str, data: dict) -> str:
    harcamalar = [e for e in data["expenses"] if e["Kullanıcı"] == user_name]
    if not harcamalar:
        return "Henüz kayıtlı harcamanız yok."
    prompt = f"""
Kullanıcı sorusu: "{soru}"
Harcama verileri: {json.dumps(harcamalar[-50:], ensure_ascii=False)}
Bugün: {datetime.now().strftime('%Y-%m-%d')}
Kısa, net Türkçe yanıt ver. Sadece yanıtı yaz.
"""
    try:
        return ai_call(prompt)
    except Exception as e:
        return f"Sorgu hatası: {e}"


# ─────────────────────────────────────────────
#  ANA WEBHOOK
# ─────────────────────────────────────────────
@app.route("/whatsapp", methods=['POST'])
def whatsapp_webhook():
    incoming_msg  = request.values.get('Body', '').strip()
    sender_phone  = request.values.get('From', '')
    num_media     = int(request.values.get('NumMedia', 0))
    user_info     = PHONE_DIRECTORY.get(sender_phone, {"ad": "Bilinmeyen", "rol": "—", "limit": 0, "emoji": "👤", "yetki": "user"})
    user_name     = user_info["ad"]
    is_admin      = user_info.get("yetki") == "admin"

    resp = MessagingResponse()
    msg  = resp.message()
    data = load_data()
    mesaj_lower = incoming_msg.lower()

    # ── KOMUTLAR ────────────────────────────────────────────────

    # YARDIM
    if mesaj_lower in ["yardım", "help", "menü", "menu", "?"]:
        seviye = seviye_hesapla(data["fis_sayaci"].get(user_name, 0))
        rozetler = data["rozetler"].get(user_name, [])
        rozet_str = " ".join([ROZETLER[r]["emoji"] for r in rozetler]) if rozetler else "henüz yok"
        yetki_str = "👑 Yönetici" if is_admin else "👤 Personel"
        msg.body(
            f"🤖 *STINGA PRO v13*\n"
            f"{user_info['emoji']} {user_name} | {yetki_str} | {seviye}\n"
            f"🏅 Rozetler: {rozet_str}\n"
            f"{'─'*28}\n"
            f"📷 Fiş fotoğrafı → AI analiz\n"
            f"📊 *özet* → Aylık özet\n"
            f"🏆 *sıralama* → Ekip yarışması\n"
            f"🔮 *kehane* → Bütçe kehaneti\n"
            f"🧠 *profil* → Harcama psikolojin\n"
            f"🎭 *karakter [mod]* → Yanıt tonu\n"
            f"   Modlar: dedektif / koc / muhaseci / yoda\n"
            f"💰 *bakiye* → Cüzdan durumu\n"
            f"📋 *son5* → Son harcamalar\n"
            f"🔍 *ara [kelime]* → Fiş ara\n"
            f"❓ *soru [metin]* → AI sorgu\n"
            f"💱 *döviz [miktar] [KOD]* → Çevir\n"
            f"🏅 *rozetler* → Tüm rozetlerim"
        )
        return str(resp)

    # ÖZET
    if mesaj_lower == "özet":
        bu_ay = datetime.now().strftime("%Y-%m")
        ay_fis = [e for e in data["expenses"] if e["Kullanıcı"] == user_name and e.get("Tarih","").startswith(bu_ay)]
        toplam = sum(e["Tutar"] for e in ay_fis)
        cat_bd = defaultdict(float)
        for e in ay_fis:
            cat_bd[e.get("Kategori","diger")] += e["Tutar"]
        cat_str = "\n".join(f"  {k}: {v:,.0f} ₺" for k, v in sorted(cat_bd.items(), key=lambda x: -x[1]))
        kehane  = harcama_kehaneti(user_name, data)
        msg.body(
            f"📊 *{datetime.now().strftime('%B %Y')} Özeti*\n"
            f"{'─'*28}\n"
            f"💰 Toplam: *{toplam:,.0f} ₺*\n"
            f"🧾 Fiş: {len(ay_fis)}\n\n"
            f"📁 Kategoriler:\n{cat_str}\n\n"
            f"📉 Bütçe: {butce_durumu_str(user_name, data)}\n\n"
            + (f"{kehane}" if kehane else "")
        )
        return str(resp)

    # SIRALAMA
    if mesaj_lower == "sıralama":
        msg.body(f"🏆 *Ekip Harcama Sıralaması*\n{'─'*28}\n{ekip_siralaması(data)}")
        return str(resp)

    # KEHANE
    if mesaj_lower in ["kehane", "kehanet", "tahmin"]:
        kehane = harcama_kehaneti(user_name, data)
        if kehane:
            msg.body(f"🔮 *Harcama Kehaneti*\n{'─'*28}\n{kehane}")
        else:
            msg.body("🔮 Bütçen bu ay güvende görünüyor. Böyle devam! 💚")
        return str(resp)

    # PSİKOLOJİK PROFİL
    if mesaj_lower == "profil":
        profil = psikolojik_profil(user_name, data)
        if profil:
            msg.body(f"🧠 *Harcama Psikolojin*\n{'─'*28}\n{profil}")
        else:
            msg.body("🧠 Profil için en az 3 fiş girmen gerekiyor!")
        return str(resp)

    # KARAKTER MODU
    if mesaj_lower.startswith("karakter "):
        mod = incoming_msg[9:].strip().lower()
        gecerli_modlar = ["dedektif", "koc", "muhaseci", "yoda", "hemsire"]
        if mod in gecerli_modlar:
            data["karakter_modu"][user_name] = mod
            save_data(data)
            mod_emoji = {"dedektif": "🕵️", "koc": "💪", "muhaseci": "📒", "yoda": "🌟", "hemsire": "💚"}
            msg.body(f"{mod_emoji.get(mod,'🎭')} Karakter modu *{mod}* aktif!\nArtık fiş yorumlarım bu karakterle gelecek.")
        else:
            msg.body(f"❌ Geçersiz mod. Seçenekler:\ndedektif / koc / muhaseci / yoda / hemsire")
        return str(resp)

    # ROZETLER
    if mesaj_lower == "rozetler":
        kazanilan = data["rozetler"].get(user_name, [])
        if not kazanilan:
            msg.body("🏅 Henüz rozet kazanmadın. Fiş göndermeye devam et!")
        else:
            satirlar = [f"{ROZETLER[r]['emoji']} *{ROZETLER[r]['ad']}*\n   {ROZETLER[r]['aciklama']}" for r in kazanilan if r in ROZETLER]
            msg.body(f"🏅 *Rozetlerin*\n{'─'*28}\n" + "\n".join(satirlar))
        return str(resp)

    # BAKIYE
    if mesaj_lower == "bakiye":
        bakiye = data["wallets"].get(user_name, 0)
        limit = data.get("user_limits", {}).get(user_name, user_info.get("limit", 0))
        msg.body(f"💳 *Cüzdan*\nBakiye: *{bakiye:,.0f} ₺*\nLimit: {limit:,.0f} ₺")
        return str(resp)

    # SON 5
    if mesaj_lower == "son5":
        son5 = [e for e in data["expenses"] if e["Kullanıcı"] == user_name][-5:]
        if not son5:
            msg.body("Henüz harcama yok.")
        else:
            satirlar = [f"🏢 {e['Firma']} — {e['Tutar']:,.0f} ₺ ({e['Tarih']}) [{e.get('Durum','?')}]" for e in reversed(son5)]
            msg.body("📋 *Son 5 Harcama:*\n" + "\n".join(satirlar))
        return str(resp)

    # DÖVİZ
    doviz_match = re.match(r"döviz\s+([\d.,]+)\s+([a-zA-Z]{3})", incoming_msg, re.IGNORECASE)
    if doviz_match:
        try:
            miktar = float(doviz_match.group(1).replace(",", "."))
            kod    = doviz_match.group(2).upper()
            r      = requests.get(DOVIZ_API_URL, timeout=5).json()
            kur    = r["rates"].get(kod)
            if kur:
                tl = miktar / kur
                msg.body(f"💱 {miktar:,.2f} {kod} = *{tl:,.2f} ₺*\n(1 {kod} = {1/kur:.4f} ₺)")
            else:
                msg.body(f"❌ '{kod}' bulunamadı.")
        except Exception as e:
            msg.body(f"❌ Döviz hatası: {e}")
        return str(resp)

    # DOĞAL DİL SORGU
    if mesaj_lower.startswith("soru "):
        yanit = nl_sorgu(incoming_msg[5:].strip(), user_name, data)
        msg.body(f"🧠 *AI Yanıtı:*\n{yanit}")
        return str(resp)

    # ARAMA
    if mesaj_lower.startswith("ara "):
        kelime  = incoming_msg[4:].strip().lower()
        havuz = data["expenses"] if is_admin else [e for e in data["expenses"] if e["Kullanıcı"] == user_name]
        sonuclar = [e for e in havuz if kelime in e.get("Firma","").lower()]
        if not sonuclar:
            msg.body(f"🔍 '{kelime}' için sonuç yok.")
        else:
            toplam  = sum(e["Tutar"] for e in sonuclar)
            satirlar = [f"• {e['Firma']} — {e['Tutar']:,.0f} ₺ ({e['Tarih']})" for e in sonuclar[-10:]]
            msg.body(f"🔍 *'{kelime}'* → {len(sonuclar)} fiş | {toplam:,.0f} ₺\n\n" + "\n".join(satirlar))
        return str(resp)

    # ── FİŞ ANALİZİ ─────────────────────────────────────────────
    if num_media > 0:
        media_url = request.values.get('MediaUrl0')

        def analiz_et_gonder():
            try:
                    # Thread içinde taze veri yükle — stale data sorununu önler
                    data = load_data()
                    res = requests.get(media_url, auth=(TWILIO_SID, TWILIO_TOKEN), allow_redirects=False, timeout=15)
                    if res.status_code in [301, 302, 307, 308]:
                        res = requests.get(res.headers.get('Location'), timeout=15)

                    raw_bytes = res.content
                    img_hash  = gorsel_hash(raw_bytes)

                    if img_hash in data["duplicate_hashes"]:
                        twilio_client.messages.create(
                            body="⚠️ *Mükerrer Fiş Tespit Edildi!*\n\nBu fişi daha önce sisteme girdiniz.\nAynı fişi tekrar gönderemezsiniz.",
                            from_="whatsapp:+14155238886",
                            to=sender_phone
                        )
                        return

                    print(f"Gorsel indirildi: {len(raw_bytes)} bytes", flush=True)
                    image = Image.open(BytesIO(raw_bytes))
                    print("Gemini cagiriliyor...", flush=True)

                    # ── Firma+Tutar bazlı mükerrer fiş kontrolü (hash farklı olsa bile)
                    # Bu kontrol AI analizinden önce yapılır
                    # (hash kontrolü yukarıda yapıldı, bu ek güvenlik katmanı)

                    # ── GEMINI: Ultra detaylı analiz promptu
                    bugun = datetime.now().strftime("%Y-%m-%d")
                    prompt = f"""Sen hem mali denetçi hem adli belge uzmanısın. Fişi analiz et ve SADECE JSON döndür.

ÖNEMLİ: Bugünün tarihi {bugun}. Fişin tarihi bu tarihten ÖNCE veya bugün olmalıdır.
Fişte yazan tarihi olduğu gibi oku (DD-MM-YYYY veya DD/MM/YYYY formatını YYYY-MM-DD'ye çevir).
Tarih {bugun}'den sonraysa risk_skoru'nu artır ama tarihi yine de fişten okuduğun gibi yaz.
Tarih kontrolünü audit_notu'na koyma — sadece kısa mali özet yaz.

        {{
          "firma": "Firma adı",
          "tarih": "YYYY-MM-DD",
          "toplam_tutar": 0.0,
          "kdv_tutari": 0.0,
          "odeme_yontemi": "nakit|kredi_karti|havale",
          "kalemler": [{{"aciklama": "...", "tutar": 0.0}}],
          "para_birimi": "TRY",
          "risk_skoru": 0,
          "risk_nedenleri": ["neden1", "neden2"],
          "audit_notu": "1 cümle kısa mali özet — HTML TAG KULLANMA, düz metin yaz",
          "sahte_mi": false,
          "sahtelik_nedeni": "",
          "gorsel_kalitesi": "iyi|orta|kotu",
          "fis_turu": "restoran|market|akaryakıt|otel|diger",
          "ilginc_detay": "fişte dikkat çeken garip veya ilginç bir şey"
        }}
        Sahtelik: düzensiz font, tutarsız toplam, eksik vergi no, farklı yazı tipleri.
        audit_notu'na asla HTML, <div>, <style> gibi tag yazmayacaksın."""

                    ai_res    = client.models.generate_content(model=MODEL_NAME, contents=[prompt, image])
                    print(f"Gemini yaniti: {ai_res.text[:200]}", flush=True)

                    # Robust JSON parse — Gemini bazen açıklama metni ekleyebilir
                    raw_text  = ai_res.text
                    json_text = re.sub(r"```json?|```", "", raw_text).strip()
                    # Sadece JSON objesini çıkar
                    _m = re.search(r'\{.*\}', json_text, re.DOTALL)
                    if _m:
                        json_text = _m.group()
                    try:
                        fis = json.loads(json_text)
                    except json.JSONDecodeError:
                        # Son çare: Gemini'den tekrar iste
                        print("JSON parse hatası, retry...", flush=True)
                        retry_prompt = f"Sadece JSON döndür, başka hiçbir şey yazma:\n{prompt}"
                        ai_res2   = client.models.generate_content(model=MODEL_NAME, contents=[retry_prompt, image])
                        json_text2 = re.sub(r"```json?|```", "", ai_res2.text).strip()
                        _m2 = re.search(r'\{.*\}', json_text2, re.DOTALL)
                        fis = json.loads(_m2.group() if _m2 else json_text2)

                    # ── Tarih doğrulama: gelecek tarih uyarısı ekle ama tarihi değiştirme
                    fis_tarihi = fis.get("tarih", "")
                    try:
                        from datetime import datetime as _dt
                        fis_dt = _dt.strptime(fis_tarihi, "%Y-%m-%d")
                        bugun_dt = _dt.now().replace(hour=0, minute=0, second=0, microsecond=0)
                        if fis_dt > bugun_dt:
                            # Gelecek tarih → risk artır ama tarihi koru
                            fis["risk_skoru"] = min(100, int(fis.get("risk_skoru", 0)) + 30)
                            fis.setdefault("risk_nedenleri", []).append("⚠️ Gelecek tarihli fiş")
                            print(f"UYARI: Gelecek tarih tespit edildi: {fis_tarihi}", flush=True)
                    except:
                        pass

                    # Para birimi dönüşümü
                    tutar_try   = float(fis.get("toplam_tutar", 0))
                    para_birimi = fis.get("para_birimi", "TRY")
                    if para_birimi != "TRY":
                        try:
                            r   = requests.get(DOVIZ_API_URL, timeout=5).json()
                            kur = r["rates"].get(para_birimi)
                            if kur:
                                tutar_try = tutar_try / kur
                        except:
                            pass

                    # Derinleştirilmiş sahtelik analizi
                    sahtelik = derin_sahtelik_analizi(fis, image)

                    # Anomali
                    anomaliler = anomali_tespit(user_name, tutar_try, data)

                    # Kategori
                    kategori = kategori_tespit(fis.get("firma", ""))

                    # Aktif karakter modu
                    karakter = data["karakter_modu"].get(user_name, random.choice(["koc", "dedektif", "muhaseci"]))

                    # Yaratıcı yorum
                    fis["kategori"] = kategori
                    yorum = yaratici_yorum(fis, user_name, karakter)

                    # Fişi kaydet — eksik key'leri güvenli ekle
                    data.setdefault("fis_sayaci", {})
                    data.setdefault("expenses", [])
                    data.setdefault("duplicate_hashes", [])
                    data.setdefault("anomaly_log", [])
                    data.setdefault("xp", {})
                    data.setdefault("notifications", [])
                    data.setdefault("rozetler", {})
                    data["fis_sayaci"][user_name] = data["fis_sayaci"].get(user_name, 0) + 1
                    # Durum — dashboard ile uyumlu değerler
                    if sahtelik["sahte_mi"] or sahtelik["guvensizlik_skoru"] >= 70:
                        durum = "Sahte Şüphesi"
                    else:
                        durum = "Onay Bekliyor"

                    # Görseli THUMBNAIL olarak sıkıştır → max 50KB, JSON bozulmasın
                    import base64 as _b64mod
                    try:
                        _thumb_img = Image.open(BytesIO(raw_bytes)).convert("RGB")
                        _thumb_img.thumbnail((400, 400), Image.LANCZOS)
                        _thumb_buf = BytesIO()
                        _thumb_img.save(_thumb_buf, format="JPEG", quality=55, optimize=True)
                        _thumb_bytes = _thumb_buf.getvalue()
                        gorsel_b64_str = _b64mod.b64encode(_thumb_bytes).decode("utf-8")
                        gorsel_data_uri = f"data:image/jpeg;base64,{gorsel_b64_str}"
                        print(f"Thumbnail boyutu: {len(_thumb_bytes)//1024}KB", flush=True)
                    except Exception as _te:
                        print(f"Thumbnail hatası: {_te}", flush=True)
                        gorsel_data_uri = ""

                    new_expense = {
                        "ID"                 : datetime.now().strftime("%Y%m%d%H%M%S"),
                        "Tarih"              : fis.get("tarih", datetime.now().strftime("%Y-%m-%d")),
                        "Yukleme_Zamani"     : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Kullanıcı"          : user_name,
                        "Rol"                : user_info["rol"],
                        "Firma"              : fis.get("firma", "Bilinmiyor"),
                        "Tutar"              : tutar_try,
                        "KDV"                : float(fis.get("kdv_tutari", 0)),
                        "ParaBirimi"         : para_birimi,
                        "OdemeTipi"          : fis.get("odeme_yontemi", "bilinmiyor"),
                        "Odeme_Turu"         : fis.get("odeme_yontemi", "bilinmiyor"),
                        "Kategori"           : kategori,
                        "Durum"              : durum,
                        "Risk_Skoru"         : sahtelik["guvensizlik_skoru"],
                        "AI_Audit"           : re.sub(r'<[^>]+>', '', str(fis.get("audit_notu", ""))).strip(),
                        "AI_Anomali"         : fis.get("anomali", False),
                        "AI_Anomali_Aciklama": fis.get("anomali_aciklamasi", ""),
                        "Anomaliler"         : anomaliler,
                        "Hash"               : img_hash,
                        "Karakter"           : karakter,
                        "IlgincDetay"        : fis.get("ilginc_detay", ""),
                        "Proje"              : "Genel Merkez",
                        "Oncelik"            : "Normal",
                        "Notlar"             : "",
                        "Kaynak"             : "WhatsApp",
                        "Dosya_Yolu"         : "",
                        "Gorsel_B64"         : gorsel_data_uri,
                    }

                    # ── Firma+Tutar+Tarih bazlı mükerrer fiş kontrolü (AI sonrası, kayıttan önce)
                    firma_yeni = str(fis.get("firma", "")).strip().lower()
                    tutar_yeni = float(fis.get("toplam_tutar", 0))
                    tarih_yeni = fis.get("tarih", "")
                    mukerrer_fis = None
                    for e in data.get("expenses", []):
                        firma_eski = str(e.get("Firma", "")).strip().lower()
                        tutar_eski = float(e.get("Tutar", 0))
                        tarih_eski = str(e.get("Tarih", ""))
                        if (firma_eski == firma_yeni and
                                abs(tutar_eski - tutar_yeni) < 1.0 and
                                tarih_eski == tarih_yeni):
                            mukerrer_fis = e
                            break

                    if mukerrer_fis:
                        twilio_client.messages.create(
                            body=(
                                f"⚠️ *Mükerrer Fiş Tespit Edildi!*\n\n"
                                f"Bu fişe ait kayıt sistemde zaten mevcut:\n"
                                f"🏢 {mukerrer_fis.get('Firma','?')}\n"
                                f"💰 ₺{float(mukerrer_fis.get('Tutar',0)):,.2f}\n"
                                f"📅 {mukerrer_fis.get('Tarih','?')}\n"
                                f"👤 {mukerrer_fis.get('Kullanıcı','?')} tarafından girilmiş\n\n"
                                f"Aynı fişi tekrar gönderemezsiniz."
                            ),
                            from_="whatsapp:+14155238886",
                            to=sender_phone
                        )
                        return

                    data["expenses"].append(new_expense)
                    data["duplicate_hashes"].append(img_hash)
                    if anomaliler:
                        data["anomaly_log"].append({
                            "tarih"     : datetime.now().isoformat(),
                            "kullanici" : user_name,
                            "tutar"     : tutar_try,
                            "uyarilar"  : anomaliler,
                        })

                    # Proje bütçesini güncelle
                    proje = new_expense["Proje"]
                    if proje in data.get("budgets", {}):
                        data["budgets"][proje]["spent"] = (
                            data["budgets"][proje].get("spent", 0) + tutar_try
                        )

                    # Rozet kontrolü
                    yeni_rozetler = rozet_kontrol(user_name, data, new_expense)

                    # XP ve bildirimler — save_data'dan ÖNCE, aynı data objesi üzerinde
                    add_xp(user_name, 50, "WhatsApp fiş tarama", data=data)

                    # Admin'lere dashboard bildirimi (aynı data objesi)
                    for ukey, udata_info in PHONE_DIRECTORY.items():
                        if udata_info.get("dashboard_rol") == "admin" and udata_info["ad"] != user_name:
                            add_notification(
                                udata_info["ad"],
                                f"📋 {user_name} → {new_expense['Proje']}: {new_expense['Firma']} ₺{tutar_try:,.0f}",
                                "info",
                                data=data
                            )

                    # Tek seferde kaydet — tüm değişiklikler (expenses, xp, notifications, rozetler)
                    save_data(data)

                    # Yanıt oluştur
                    risk = sahtelik["guvensizlik_skoru"]
                    risk_emoji = "🟢" if risk < 30 else "🟡" if risk < 70 else "🔴"

                    kalemler_str = ""
                    if fis.get("kalemler"):
                        satirlar = [f"  • {k['aciklama']}: {k['tutar']:.2f} ₺" for k in fis["kalemler"][:4]]
                        kalemler_str = "\n📝 *Kalemler:*\n" + "\n".join(satirlar)

                    sahte_str = ""
                    if sahtelik["sahte_mi"] or sahtelik["guvensizlik_skoru"] >= 70:
                        bulgular = "\n".join(sahtelik["bulgular"][:3])
                        sahte_str = f"\n\n🚨 *SAHTE FİŞ ŞÜPHESİ!*\n{bulgular}"

                    anomali_str = ("\n\n" + "\n".join(anomaliler)) if anomaliler else ""

                    ilginc = fis.get("ilginc_detay", "")
                    ilginc_str = f"\n💡 _{ilginc}_" if ilginc and ilginc not in ["", "null", "None"] else ""

                    rozet_str = ""
                    if yeni_rozetler:
                        for r in yeni_rozetler:
                            if r in ROZETLER:
                                rozet_str += f"\n\n🎊 *YENİ ROZET: {ROZETLER[r]['emoji']} {ROZETLER[r]['ad']}!*\n{ROZETLER[r]['aciklama']}"

                    seviye = seviye_hesapla(data["fis_sayaci"].get(user_name, 0))

                    # Güncel kasa bakiyesi
                    kasa_bakiye = data.get("wallets", {}).get(user_name, 0)

                    yanit = (
                        f"✅ *FİŞ SİSTEME KAYDEDİLDİ — ONAYA GÖNDERİLDİ.*\n"
                        f"{'─'*13}\n"
                        f"🏢 {fis.get('firma','?')}\n"
                        f"💰 {tutar_try:,.2f} ₺"
                        + (f" ({fis['toplam_tutar']:.2f} {para_birimi})" if para_birimi != "TRY" else "")
                        + f"\n📅 {fis.get('tarih','—')}"
                        + f"\n💳 {fis.get('odeme_yontemi','—')}"
                        + f"\n🏷️ {kategori}"
                        + f"\n{risk_emoji} Risk: {risk}/100"
                        + kalemler_str
                        + ilginc_str
                        + f"\n\n💬 *{karakter.upper()} YORUMU:*\n{yorum}"
                        + f"\n\n📊 Bütçe: {butce_durumu_str(user_name, data)}"
                        + f"\n💳 Kasa Bakiyeniz: *{kasa_bakiye:,.0f} ₺*"
                        + f"\n{seviye} • #{data['fis_sayaci'].get(user_name,0)} fiş"
                        + sahte_str
                        + anomali_str
                        + rozet_str
                        + f"\n\n📨 Fişiniz yönetici onayına gönderildi."
                        + f"\n🔖 `{new_expense['ID']}`"
                    )
                    twilio_client.messages.create(
                        body=yanit,
                        from_="whatsapp:+14155238886",
                        to=sender_phone
                    )
            except json.JSONDecodeError as e:
                print(f"JSON HATA: {e}", flush=True)
                twilio_client.messages.create(
                    body="❌ Fiş okunamadı. Net fotoğraf çekip tekrar deneyin.",
                    from_="whatsapp:+14155238886",
                    to=sender_phone
                )
            except Exception as e:
                import traceback
                print(f"GENEL HATA: {traceback.format_exc()}", flush=True)
                twilio_client.messages.create(
                    body=f"❌ Hata: {str(e)}",
                    from_="whatsapp:+14155238886",
                    to=sender_phone
                )

        import threading
        # DB yazma kilidi — iki eş zamanlı fiş birbirini ezmesin
        if not hasattr(analiz_et_gonder, '_lock'):
            analiz_et_gonder._lock = threading.Lock()
        t = threading.Thread(target=analiz_et_gonder, daemon=True)
        t.start()
        msg.body("⏳ *Stinga Yapay Zeka* fişinizi analiz ediyor, lütfen bekleyin...")
        return str(resp)

    # ── VARSAYILAN
    fis_sayisi = data["fis_sayaci"].get(user_name, 0)
    seviye     = seviye_hesapla(fis_sayisi)
    msg.body(
        f"{user_info['emoji']} Merhaba *{user_name}*!\n"
        f"{seviye}\n"
        f"Fiş fotoğrafı gönder veya *yardım* yaz."
    )
    return str(resp)


# ─────────────────────────────────────────────
#  ENDPOINTLER
# ─────────────────────────────────────────────
@app.route("/rapor", methods=['GET'])
def rapor_endpoint():
    data   = load_data()
    bu_ay  = datetime.now().strftime("%Y-%m")
    ay_fis = [e for e in data["expenses"] if e.get("Tarih","").startswith(bu_ay)]
    toplam = sum(e["Tutar"] for e in ay_fis)
    k_bazli = defaultdict(float)
    c_bazli = defaultdict(float)
    for e in ay_fis:
        k_bazli[e["Kullanıcı"]] += e["Tutar"]
        c_bazli[e.get("Kategori","diger")] += e["Tutar"]
    return jsonify({
        "ay": bu_ay, "toplam": toplam,
        "fis_sayisi": len(ay_fis),
        "anomali_sayisi": len(data.get("anomaly_log",[])),
        "kullanici_bazli": dict(k_bazli),
        "kategori_bazli": dict(c_bazli),
        "ekip_rozetleri": data.get("rozetler", {}),
    }), 200


@app.route("/expenses", methods=['GET'])
def expenses_endpoint():
    """Tüm fişleri döner — Streamlit dashboard bu endpoint'i kullanır."""
    data = load_data()
    return jsonify({"expenses": data.get("expenses", [])}), 200


@app.route("/add-expense", methods=['POST'])
def add_expense_endpoint():
    """
    Streamlit dashboard'dan manuel fiş ekle.
    Dashboard'un AI analizi yapıp buraya gönderdiği fişleri DB'ye yazar.
    """
    try:
        new_e = request.get_json(force=True)
        if not new_e:
            return jsonify({"error": "Boş veri"}), 400

        data = load_data()

        # Zorunlu alanlar yoksa varsayılan ekle
        if not new_e.get("ID"):
            new_e["ID"] = datetime.now().strftime("%Y%m%d%H%M%S")
        if not new_e.get("Tarih"):
            new_e["Tarih"] = datetime.now().strftime("%Y-%m-%d")
        if not new_e.get("Durum"):
            new_e["Durum"] = "Onay Bekliyor"

        # Mükerrer kontrolü
        for e in data["expenses"]:
            if (e.get("Firma") == new_e.get("Firma") and
                abs(float(e.get("Tutar", 0)) - float(new_e.get("Tutar", 0))) < 1 and
                e.get("Tarih") == new_e.get("Tarih")):
                return jsonify({"error": "Mükerrer fiş", "duplicate": True}), 409

        # AI_Audit içindeki HTML tag'larını temizle
        if "AI_Audit" in new_e:
            new_e["AI_Audit"] = re.sub(r'<[^>]+>', '', str(new_e["AI_Audit"])).strip()
        data["expenses"].append(new_e)

        # XP ekle
        add_xp(new_e.get("Kullanıcı", ""), 50, "Dashboard fiş tarama", data=data)

        # Admin bildirimi
        for ukey, uinfo in PHONE_DIRECTORY.items():
            if uinfo.get("dashboard_rol") == "admin" and uinfo["ad"] != new_e.get("Kullanıcı", ""):
                add_notification(
                    uinfo["ad"],
                    f"📋 {new_e.get('Kullanıcı','?')} → {new_e.get('Proje','?')}: {new_e.get('Firma','?')} ₺{float(new_e.get('Tutar',0)):,.0f}",
                    "info",
                    data=data
                )

        save_data(data)
        return jsonify({"ok": True, "ID": new_e["ID"]}), 200
    except Exception as e:
        import traceback
        print(f"add-expense HATA: {traceback.format_exc()}", flush=True)
        return jsonify({"error": str(e)}), 500


@app.route("/all-data", methods=['GET'])
def all_data_endpoint():
    """Streamlit için tam veri seti: fişler, bütçeler, rozetler, anomaliler."""
    data = load_data()
    return jsonify({
        "expenses":      data.get("expenses", []),
        "budgets":       data.get("budgets", {}),
        "wallets":       data.get("wallets", {}),
        "rozetler":      data.get("rozetler", {}),
        "fis_sayaci":    data.get("fis_sayaci", {}),
        "anomaly_log":   data.get("anomaly_log", []),
        "xp":            data.get("xp", {}),
        "notifications": data.get("notifications", []),
        "ledger":        data.get("ledger", []),
    }), 200


@app.route("/haftalik-ozet", methods=["GET"])
def haftalik_ozet():
    """Cron job: her Pazartesi 09:00 → curl https://domain.com/haftalik-ozet"""
    data  = load_data()
    bu_ay = datetime.now().strftime("%Y-%m")
    for phone, info in PHONE_DIRECTORY.items():
        user   = info["ad"]
        ay_fis = [e for e in data["expenses"] if e["Kullanıcı"] == user and e.get("Tarih","").startswith(bu_ay)]
        toplam = sum(e["Tutar"] for e in ay_fis)
        butce  = data.get("user_limits", {}).get(user, info.get("limit", 0))
        oran   = (toplam / butce * 100) if butce > 0 else 0
        try:
            twilio_client.messages.create(
                body=(
                    f"📊 *Haftalık Özet — {user}*\n"
                    f"{'─'*28}\n"
                    f"💰 Bu ay: {toplam:,.0f} ₺\n"
                    f"📉 Bütçe: %{oran:.1f}\n"
                    f"🧾 Fiş: {len(ay_fis)}\n"
                    f"{butce_durumu_str(user, data)}"
                ),
                from_="whatsapp:+14155238886", to=phone
            )
        except Exception as e:
            print(f"Haftalık özet hatası ({user}): {e}", flush=True)
    return jsonify({"status": "ok", "gonderilen": len(PHONE_DIRECTORY)}), 200


@app.route("/approve", methods=['POST'])
def approve_endpoint():
    """Dashboard onay/red işlemi. Body: {ID, action: 'approve'|'reject', approver}"""
    try:
        body     = request.get_json(force=True) or {}
        fis_id   = str(body.get("ID", ""))
        action   = body.get("action", "approve")
        approver = body.get("approver", "admin")

        if not fis_id:
            return jsonify({"error": "ID gerekli"}), 400

        data = load_data()
        found = False
        kullanici = ""
        tutar = 0.0
        firma = ""

        for e in data.get("expenses", []):
            if str(e.get("ID", "")) == fis_id:
                found = True
                kullanici = e.get("Kullanıcı", "")
                tutar     = float(e.get("Tutar", 0))
                firma     = e.get("Firma", "?")
                if action == "approve":
                    e["Durum"] = "Onaylandı"
                    e["Onaylayan"] = approver
                else:
                    e["Durum"] = "Reddedildi"
                    e["Reddeden"] = approver
                break

        if not found:
            return jsonify({"error": "Fiş bulunamadı", "ID": fis_id}), 404

        if action == "approve":
            # Cüzdandan düş
            mevcut = data.get("wallets", {}).get(kullanici, 0)
            data.setdefault("wallets", {})[kullanici] = max(0, mevcut - tutar)
            # XP ekle
            add_xp(kullanici, 25, "Fiş onaylandı", data=data)
            # Bildirim
            add_notification(kullanici,
                f"✅ {firma} (₺{tutar:,.0f}) onaylandı",
                "success", data=data)
        else:
            add_notification(kullanici,
                f"❌ {firma} harcamanız reddedildi",
                "warning", data=data)

        # WhatsApp bildirimi gönder (onay veya red)
        try:
            # Kullanıcı adından telefon numarasını bul
            target_phone = None
            for phone, info in PHONE_DIRECTORY.items():
                if info.get("ad") == kullanici:
                    target_phone = phone
                    break
            if target_phone:
                if action == "approve":
                    mesaj = f"✅ {firma} (₺{tutar:,.0f}) harcamanız onaylandı."
                else:
                    mesaj = f"❌ {firma} (₺{tutar:,.0f}) harcamanız reddedildi."
                twilio_client.messages.create(
                    body=mesaj,
                    from_="whatsapp:+14155238886",
                    to=target_phone
                )
                print(f"WhatsApp bildirimi gönderildi: {kullanici} - {mesaj}", flush=True)
            else:
                print(f"Uyarı: {kullanici} için telefon numarası bulunamadı.", flush=True)
        except Exception as e:
            # WhatsApp gönderilemezse sadece logla, işlem devam etsin
            print(f"WhatsApp bildirimi gönderilemedi: {e}", flush=True)

        save_data(data)
        print(f"Fiş {action}: ID={fis_id}, kullanıcı={kullanici}", flush=True)
        return jsonify({"ok": True, "ID": fis_id, "action": action}), 200

    except Exception as e:
        import traceback
        print(f"/approve HATA: {traceback.format_exc()}", flush=True)
        return jsonify({"error": str(e)}), 500


@app.route("/transfer", methods=['POST'])
def transfer_endpoint():
    """Dashboard harcırah transferi. Body: {hedef, miktar, aciklama, gonderen}"""
    try:
        body      = request.get_json(force=True) or {}
        hedef     = body.get("hedef", "")
        miktar    = float(body.get("miktar", 0))
        aciklama  = body.get("aciklama", "Harcırah")
        gonderen  = body.get("gonderen", "admin")

        if not hedef or miktar <= 0:
            return jsonify({"error": "Hedef ve miktar gerekli"}), 400

        data = load_data()
        data.setdefault("wallets", {})[hedef] = data["wallets"].get(hedef, 0) + miktar
        data.setdefault("ledger", []).append({
            "Tarih":  datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Kaynak": gonderen,
            "Hedef":  hedef,
            "İşlem":  aciklama,
            "Miktar": miktar
        })
        add_notification(hedef,
            f"💰 Hesabınıza ₺{miktar:,.0f} transfer yapıldı. ({aciklama})",
            "success", data=data)
        add_xp(hedef, 10, "Transfer alındı", data=data)
        save_data(data)
        return jsonify({"ok": True, "hedef": hedef, "miktar": miktar}), 200

    except Exception as e:
        import traceback
        print(f"/transfer HATA: {traceback.format_exc()}", flush=True)
        return jsonify({"error": str(e)}), 500


@app.route("/gorsel/<fis_id>", methods=['GET'])
def gorsel_endpoint(fis_id):
    """Fiş görselini döndür. Base64 data URI veya 404."""
    data = load_data()
    for e in data.get("expenses", []):
        if str(e.get("ID", "")) == str(fis_id):
            b64 = e.get("Gorsel_B64", "")
            if b64:
                return jsonify({"ok": True, "gorsel": b64}), 200
            return jsonify({"ok": False, "error": "Görsel yok"}), 404
    return jsonify({"ok": False, "error": "Fiş bulunamadı"}), 404



if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)