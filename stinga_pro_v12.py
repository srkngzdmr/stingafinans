# -*- coding: utf-8 -*-
"""
STINGA FİNANS — Streamlit Dashboard v12
Railway'deki bot API'sinden veri çeker.
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from collections import defaultdict

# ─────────────────────────────────────────────
#  YAPILANDIRMA
# ─────────────────────────────────────────────
# Railway bot URL'ini buraya gir (Railway > Settings > Domains)
BOT_API_URL = st.secrets.get("BOT_API_URL", "https://YOUR-RAILWAY-URL.railway.app")

PHONE_DIRECTORY = {
    "Okan":   {"rol": "Saha Müdürü",  "limit": 5000,  "emoji": "🔧"},
    "Serkan": {"rol": "Muhasebe",     "limit": 10000, "emoji": "📊"},
    "Zeynep": {"rol": "Genel Müdür",  "limit": 50000, "emoji": "👑"},
}

ROZETLER = {
    "ilk_fis":       {"emoji": "🎯", "ad": "İlk Adım"},
    "tasarruf_5":    {"emoji": "💚", "ad": "Tutumlu"},
    "hizli_giris":   {"emoji": "⚡", "ad": "Flaş Muhasebeci"},
    "risk_avcisi":   {"emoji": "🕵️", "ad": "Risk Avcısı"},
    "hafiza_ustasi": {"emoji": "🧠", "ad": "Hafıza Ustası"},
    "dovec_kral":    {"emoji": "💱", "ad": "Döviz Kralı"},
    "dedektif":      {"emoji": "🔍", "ad": "Sahte Avcısı"},
    "ekonomist":     {"emoji": "📈", "ad": "Ekonomist"},
}

# ─────────────────────────────────────────────
#  VERİ ÇEKME
# ─────────────────────────────────────────────
@st.cache_data(ttl=30)  # 30 saniyede bir yenile
def fetch_data():
    try:
        r = requests.get(f"{BOT_API_URL}/all-data", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"❌ API bağlantı hatası: {e}\n\nBot URL'ini kontrol et: `{BOT_API_URL}`")
        return None

# ─────────────────────────────────────────────
#  SAYFA AYARLARI
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Stinga Finans",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e1e2e, #2a2a3e);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #3a3a5c;
        margin-bottom: 10px;
    }
    .risk-high   { color: #ff4b4b; font-weight: bold; }
    .risk-medium { color: #ffa500; font-weight: bold; }
    .risk-low    { color: #00cc66; font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    try:
        st.image("logo.png", width=180)
    except:
        st.title("💰 Stinga Finans")

    st.markdown("---")
    filtre_kullanici = st.selectbox("👤 Kullanıcı", ["Tümü", "Okan", "Serkan", "Zeynep"])
    filtre_kategori  = st.selectbox("🏷️ Kategori",  ["Tümü", "yemek", "ulasim", "ofis", "konaklama", "eglence", "saglik", "diger"])
    filtre_ay        = st.text_input("📅 Ay (YYYY-MM)", value=datetime.now().strftime("%Y-%m"))

    st.markdown("---")
    if st.button("🔄 Yenile"):
        st.cache_data.clear()
        st.rerun()

    st.caption(f"Son güncelleme: {datetime.now().strftime('%H:%M:%S')}")

# ─────────────────────────────────────────────
#  VERİ YÜKLEMESİ
# ─────────────────────────────────────────────
data = fetch_data()

if not data:
    st.stop()

expenses  = data.get("expenses", [])
budgets   = data.get("budgets", {})
rozetler  = data.get("rozetler", {})
fis_sayac = data.get("fis_sayaci", {})
anomaliler = data.get("anomaly_log", [])

# DataFrame oluştur
df = pd.DataFrame(expenses) if expenses else pd.DataFrame()

# Filtrele
if not df.empty:
    if filtre_kullanici != "Tümü":
        df = df[df["Kullanıcı"] == filtre_kullanici]
    if filtre_kategori != "Tümü":
        df = df[df["Kategori"] == filtre_kategori]
    if filtre_ay:
        df = df[df["Tarih"].str.startswith(filtre_ay)]

# ─────────────────────────────────────────────
#  BAŞLIK
# ─────────────────────────────────────────────
st.title("💰 Stinga Finans Dashboard")
st.markdown(f"**{filtre_ay}** dönemi · {len(df)} fiş")
st.markdown("---")

# ─────────────────────────────────────────────
#  ÖZET METRİKLER
# ─────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

toplam_tutar  = df["Tutar"].sum() if not df.empty else 0
ortalama      = df["Tutar"].mean() if not df.empty else 0
yuksek_risk   = len(df[df["Risk_Skoru"] >= 70]) if not df.empty and "Risk_Skoru" in df.columns else 0
anomali_say   = len(anomaliler)

col1.metric("💰 Toplam Harcama",   f"{toplam_tutar:,.0f} ₺")
col2.metric("📊 Ortalama Fiş",     f"{ortalama:,.0f} ₺")
col3.metric("🔴 Yüksek Riskli",    f"{yuksek_risk} fiş")
col4.metric("⚠️ Anomali",          f"{anomali_say} adet")

st.markdown("---")

# ─────────────────────────────────────────────
#  BÜTÇE DURUMU
# ─────────────────────────────────────────────
st.subheader("📊 Bütçe Durumu")
budget_cols = st.columns(3)

for i, (user, info) in enumerate(PHONE_DIRECTORY.items()):
    with budget_cols[i]:
        kullanici_df = pd.DataFrame(expenses)
        if not kullanici_df.empty:
            kullanici_df = kullanici_df[
                (kullanici_df["Kullanıcı"] == user) &
                (kullanici_df["Tarih"].str.startswith(filtre_ay))
            ]
            harcanan = kullanici_df["Tutar"].sum()
        else:
            harcanan = 0

        butce = budgets.get(user, 0)
        oran  = (harcanan / butce * 100) if butce > 0 else 0
        fis   = fis_sayac.get(user, 0)
        renk  = "normal" if oran < 70 else "off" if oran < 90 else "inverse"

        st.markdown(f"### {info['emoji']} {user}")
        st.markdown(f"*{info['rol']}*")
        st.metric("Harcanan", f"{harcanan:,.0f} ₺", f"%{oran:.1f} bütçe")
        st.progress(min(oran / 100, 1.0))
        st.caption(f"Bütçe: {butce:,.0f} ₺ · {fis} fiş")

        # Rozetler
        user_rozetler = rozetler.get(user, [])
        if user_rozetler:
            rozet_str = " ".join(
                ROZETLER[r]["emoji"] for r in user_rozetler if r in ROZETLER
            )
            st.markdown(f"**Rozetler:** {rozet_str}")

st.markdown("---")

# ─────────────────────────────────────────────
#  GRAFİKLER
# ─────────────────────────────────────────────
if not df.empty:
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("🏷️ Kategoriye Göre Harcama")
        if "Kategori" in df.columns:
            kat_data = df.groupby("Kategori")["Tutar"].sum().sort_values(ascending=False)
            st.bar_chart(kat_data)

    with chart_col2:
        st.subheader("👤 Kişiye Göre Harcama")
        if "Kullanıcı" in df.columns:
            kisi_data = df.groupby("Kullanıcı")["Tutar"].sum().sort_values(ascending=False)
            st.bar_chart(kisi_data)

    # Zaman serisi
    if "Tarih" in df.columns:
        st.subheader("📈 Günlük Harcama Trendi")
        trend = df.groupby("Tarih")["Tutar"].sum()
        st.line_chart(trend)

    st.markdown("---")

# ─────────────────────────────────────────────
#  FİŞ TABLOSU
# ─────────────────────────────────────────────
st.subheader("🧾 Fiş Listesi")

if df.empty:
    st.info("Bu dönemde fiş bulunamadı.")
else:
    # Risk renklendirme için
    def risk_emoji(score):
        if score >= 70: return f"🔴 {score}"
        if score >= 30: return f"🟡 {score}"
        return f"🟢 {score}"

    display_df = df.copy()

    # Gösterilecek kolonlar
    cols_order = ["Tarih", "Kullanıcı", "Firma", "Tutar", "Kategori", "OdemeTipi", "Risk_Skoru", "Durum"]
    cols_exist = [c for c in cols_order if c in display_df.columns]
    display_df = display_df[cols_exist].sort_values("Tarih", ascending=False)

    if "Risk_Skoru" in display_df.columns:
        display_df["Risk_Skoru"] = display_df["Risk_Skoru"].apply(risk_emoji)

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # CSV indir
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ CSV İndir",
        data=csv,
        file_name=f"stinga_{filtre_ay}.csv",
        mime="text/csv",
    )

st.markdown("---")

# ─────────────────────────────────────────────
#  ANOMALİ LOGU
# ─────────────────────────────────────────────
if anomaliler:
    st.subheader("⚠️ Anomali Geçmişi")
    anom_df = pd.DataFrame(anomaliler)
    st.dataframe(anom_df, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.caption("Stinga Finans Pro · WhatsApp + AI Harcama Takip Sistemi")
