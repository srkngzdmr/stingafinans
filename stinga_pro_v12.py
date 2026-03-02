# -*- coding: utf-8 -*-
"""
STINGA FİNANS — Streamlit Dashboard v13
Giriş ekranı + rol bazlı erişim + Railway API entegrasyonu
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Stinga Finans",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

BOT_API_URL = st.secrets.get("BOT_API_URL", "https://stingafinans-production.up.railway.app")

KULLANICILAR = {
    "serkan": {"sifre": "123",  "ad": "Serkan", "rol": "İşletme Müdürü",         "emoji": "📊", "limit": 10000, "yetki": "yonetici"},
    "zeynep": {"sifre": "789",  "ad": "Zeynep", "rol": "Yönetim Kurulu Başkanı", "emoji": "👑", "limit": 50000, "yetki": "yonetici"},
    "okan":   {"sifre": "321",  "ad": "Okan",   "rol": "Saha Personeli",          "emoji": "🔧", "limit": 5000,  "yetki": "personel"},
    "senol":  {"sifre": "456",  "ad": "Şenol",  "rol": "Genel Müdür",             "emoji": "🏢", "limit": 30000, "yetki": "yonetici"},
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

st.markdown("""
<style>
.login-title { text-align:center; font-size:2rem; font-weight:700; margin-bottom:4px; }
.login-sub   { text-align:center; color:#888; font-size:0.95rem; margin-bottom:24px; }
div[data-testid="stMetricValue"] { font-size:1.8rem; }
</style>
""", unsafe_allow_html=True)

if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False
if "aktif_kullanici" not in st.session_state:
    st.session_state.aktif_kullanici = None


def giris_ekrani():
    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        try:
            st.image("logo.png", width=140)
        except:
            pass
        st.markdown('<div class="login-title">💰 Stinga Finans</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub">Harcama Yönetim Paneli</div>', unsafe_allow_html=True)
        st.markdown("---")
        kullanici_adi = st.text_input("👤 Kullanıcı Adı", placeholder="kullanıcı adınızı girin").strip().lower()
        sifre = st.text_input("🔒 Şifre", type="password", placeholder="şifrenizi girin")
        if st.button("🚀 Giriş Yap", use_container_width=True, type="primary"):
            if kullanici_adi in KULLANICILAR and sifre == KULLANICILAR[kullanici_adi]["sifre"]:
                st.session_state.giris_yapildi = True
                st.session_state.aktif_kullanici = kullanici_adi
                st.rerun()
            else:
                st.error("❌ Kullanıcı adı veya şifre hatalı!")
        st.markdown("---")
        st.caption("© 2026 Stinga Finans · Tüm hakları saklıdır")


@st.cache_data(ttl=30)
def fetch_data():
    try:
        r = requests.get(f"{BOT_API_URL}/all-data", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"❌ API bağlantı hatası: {e}")
        return None


def risk_emoji(score):
    try:
        score = float(score)
        if score >= 70: return f"🔴 {int(score)}"
        if score >= 30: return f"🟡 {int(score)}"
        return f"🟢 {int(score)}"
    except:
        return str(score)


def dashboard():
    kkey     = st.session_state.aktif_kullanici
    kinfo    = KULLANICILAR[kkey]
    yetki    = kinfo["yetki"]
    aktif_ad = kinfo["ad"]

    # ── SIDEBAR ──────────────────────────────────────────────────────────
    with st.sidebar:
        try:
            st.image("logo.png", width=160)
        except:
            st.markdown("## 💰 Stinga Finans")
        st.markdown("---")
        st.markdown(f"### {kinfo['emoji']} {aktif_ad}")
        st.caption(kinfo["rol"])
        st.markdown("---")

        if yetki == "yonetici":
            tum_adlar = ["Tümü"] + [v["ad"] for v in KULLANICILAR.values()]
            filtre_kullanici = st.selectbox("👤 Kullanıcı Filtresi", tum_adlar)
        else:
            filtre_kullanici = aktif_ad
            st.info("👤 Sadece kendi fişlerinizi görüyorsunuz.")

        filtre_kategori = st.selectbox("🏷️ Kategori",
            ["Tümü", "yemek", "ulasim", "ofis", "konaklama", "eglence", "saglik", "diger"])
        filtre_ay = st.text_input("📅 Ay (YYYY-MM)", value=datetime.now().strftime("%Y-%m"))

        st.markdown("---")
        if st.button("🔄 Yenile", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        if st.button("🚪 Çıkış Yap", use_container_width=True):
            st.session_state.giris_yapildi = False
            st.session_state.aktif_kullanici = None
            st.rerun()
        st.caption(f"Son güncelleme: {datetime.now().strftime('%H:%M:%S')}")

    # ── VERİ ─────────────────────────────────────────────────────────────
    data = fetch_data()
    if not data:
        st.stop()

    expenses   = data.get("expenses", [])
    budgets    = data.get("budgets", {})
    rozetler   = data.get("rozetler", {})
    fis_sayac  = data.get("fis_sayaci", {})
    anomaliler = data.get("anomaly_log", [])

    df_full = pd.DataFrame(expenses) if expenses else pd.DataFrame()
    df = df_full.copy()

    if not df.empty:
        if yetki == "personel":
            df = df[df["Kullanıcı"] == aktif_ad]
        elif filtre_kullanici != "Tümü":
            df = df[df["Kullanıcı"] == filtre_kullanici]
        if filtre_kategori != "Tümü" and "Kategori" in df.columns:
            df = df[df["Kategori"] == filtre_kategori]
        if filtre_ay and "Tarih" in df.columns:
            df = df[df["Tarih"].str.startswith(filtre_ay)]

    # ── BAŞLIK ───────────────────────────────────────────────────────────
    st.title("💰 Stinga Finans Dashboard")
    st.markdown(f"**{filtre_ay}** dönemi · {len(df)} fiş")
    st.markdown("---")

    # ── SEKME YAPISI ─────────────────────────────────────────────────────
    tabs = ["📊 Genel Bakış", "🧾 Fişler", "📈 Grafikler", "👥 Ekip & Rozetler"]
    if yetki == "yonetici":
        tabs.append("⚠️ Anomaliler")
    tab_list = st.tabs(tabs)

    # ════════════════════════════════════════════
    # SEKME 1 — GENEL BAKIŞ
    # ════════════════════════════════════════════
    with tab_list[0]:
        toplam_tutar = df["Tutar"].sum() if not df.empty else 0
        ortalama     = df["Tutar"].mean() if not df.empty else 0
        yuksek_risk  = len(df[df["Risk_Skoru"] >= 70]) if not df.empty and "Risk_Skoru" in df.columns else 0
        anomali_say  = len(anomaliler)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Toplam Harcama", f"{toplam_tutar:,.0f} ₺")
        col2.metric("📊 Ortalama Fiş",   f"{ortalama:,.0f} ₺")
        col3.metric("🔴 Yüksek Riskli",  f"{yuksek_risk} fiş")
        col4.metric("⚠️ Anomali",        f"{anomali_say} adet")

        st.markdown("---")
        st.subheader("📊 Bütçe Durumu")

        goster_kullanicilar = (
            list(KULLANICILAR.values()) if yetki == "yonetici" else [kinfo]
        )
        budget_cols = st.columns(len(goster_kullanicilar))

        for i, uinfo in enumerate(goster_kullanicilar):
            with budget_cols[i]:
                uad = uinfo["ad"]
                if not df_full.empty and "Kullanıcı" in df_full.columns and "Tarih" in df_full.columns:
                    u_df = df_full[
                        (df_full["Kullanıcı"] == uad) &
                        (df_full["Tarih"].str.startswith(filtre_ay))
                    ]
                    harcanan = u_df["Tutar"].sum()
                else:
                    harcanan = 0

                butce = budgets.get(uad, uinfo.get("limit", 0))
                oran  = (harcanan / butce * 100) if butce > 0 else 0
                fis   = fis_sayac.get(uad, 0)

                st.markdown(f"### {uinfo['emoji']} {uad}")
                st.markdown(f"*{uinfo['rol']}*")
                st.metric("Harcanan", f"{harcanan:,.0f} ₺", f"%{oran:.1f} bütçe")
                st.progress(min(oran / 100, 1.0))
                st.caption(f"Bütçe: {butce:,.0f} ₺ · {fis} fiş")

                user_rozetler = rozetler.get(uad, [])
                if user_rozetler:
                    rozet_str = " ".join(ROZETLER[r]["emoji"] for r in user_rozetler if r in ROZETLER)
                    st.markdown(f"**Rozetler:** {rozet_str}")

    # ════════════════════════════════════════════
    # SEKME 2 — FİŞLER
    # ════════════════════════════════════════════
    with tab_list[1]:
        st.subheader("🧾 Fiş Listesi")
        if df.empty:
            st.info("Bu dönemde fiş bulunamadı.")
        else:
            display_df = df.copy()
            cols_order = ["Tarih", "Kullanıcı", "Firma", "Tutar", "Kategori", "OdemeTipi", "Risk_Skoru", "Durum"]
            cols_exist = [c for c in cols_order if c in display_df.columns]
            display_df = display_df[cols_exist].sort_values("Tarih", ascending=False)
            if "Risk_Skoru" in display_df.columns:
                display_df["Risk_Skoru"] = display_df["Risk_Skoru"].apply(risk_emoji)

            st.dataframe(display_df, use_container_width=True, hide_index=True)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ CSV İndir", data=csv,
                file_name=f"stinga_{filtre_ay}.csv", mime="text/csv")

            # Yüksek riskli fişler ayrıca göster
            if "Risk_Skoru" in df.columns:
                riskli = df[pd.to_numeric(df["Risk_Skoru"], errors="coerce") >= 70]
                if not riskli.empty:
                    st.markdown("---")
                    st.subheader("🚨 Yüksek Riskli Fişler")
                    st.dataframe(riskli[cols_exist].sort_values("Tarih", ascending=False),
                        use_container_width=True, hide_index=True)

    # ════════════════════════════════════════════
    # SEKME 3 — GRAFİKLER
    # ════════════════════════════════════════════
    with tab_list[2]:
        if df.empty:
            st.info("Grafik için yeterli veri yok.")
        else:
            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                st.subheader("🏷️ Kategoriye Göre")
                if "Kategori" in df.columns:
                    kat_data = df.groupby("Kategori")["Tutar"].sum().sort_values(ascending=False)
                    st.bar_chart(kat_data)
            with chart_col2:
                st.subheader("👤 Kişiye Göre")
                if "Kullanıcı" in df.columns:
                    kisi_data = df.groupby("Kullanıcı")["Tutar"].sum().sort_values(ascending=False)
                    st.bar_chart(kisi_data)

            if "Tarih" in df.columns:
                st.subheader("📈 Günlük Harcama Trendi")
                trend = df.groupby("Tarih")["Tutar"].sum()
                st.line_chart(trend)

            if "OdemeTipi" in df.columns:
                st.subheader("💳 Ödeme Yöntemine Göre")
                odeme_data = df.groupby("OdemeTipi")["Tutar"].sum().sort_values(ascending=False)
                st.bar_chart(odeme_data)

    # ════════════════════════════════════════════
    # SEKME 4 — EKİP & ROZETLER
    # ════════════════════════════════════════════
    with tab_list[3]:
        st.subheader("👥 Ekip Sıralaması")

        siralama = []
        for uinfo in KULLANICILAR.values():
            uad = uinfo["ad"]
            if not df_full.empty and "Kullanıcı" in df_full.columns:
                u_df = df_full[
                    (df_full["Kullanıcı"] == uad) &
                    (df_full["Tarih"].str.startswith(filtre_ay))
                ]
                harcanan = u_df["Tutar"].sum()
                fis_say  = len(u_df)
            else:
                harcanan = 0
                fis_say  = 0
            butce = budgets.get(uad, uinfo.get("limit", 1))
            oran  = (harcanan / butce * 100) if butce > 0 else 0
            siralama.append({"ad": uad, "rol": uinfo["rol"], "emoji": uinfo["emoji"],
                             "harcanan": harcanan, "butce": butce, "oran": oran, "fis": fis_say})

        siralama.sort(key=lambda x: x["harcanan"], reverse=True)
        madalyalar = ["🥇", "🥈", "🥉", "4️⃣"]

        for i, s in enumerate(siralama):
            madalya = madalyalar[i] if i < len(madalyalar) else "•"
            col_a, col_b, col_c = st.columns([0.1, 0.5, 0.4])
            with col_a:
                st.markdown(f"## {madalya}")
            with col_b:
                st.markdown(f"**{s['emoji']} {s['ad']}** — *{s['rol']}*")
                st.progress(min(s["oran"] / 100, 1.0))
                st.caption(f"{s['harcanan']:,.0f} ₺ / {s['butce']:,.0f} ₺  •  {s['fis']} fiş")
            with col_c:
                user_rozetler = rozetler.get(s["ad"], [])
                if user_rozetler:
                    for r in user_rozetler:
                        if r in ROZETLER:
                            st.markdown(f"{ROZETLER[r]['emoji']} {ROZETLER[r]['ad']}")
                else:
                    st.caption("Henüz rozet yok")
            st.markdown("---")

    # ════════════════════════════════════════════
    # SEKME 5 — ANOMALİLER (sadece yönetici)
    # ════════════════════════════════════════════
    if yetki == "yonetici":
        with tab_list[4]:
            st.subheader("⚠️ Anomali Geçmişi")
            if anomaliler:
                anom_df = pd.DataFrame(anomaliler)
                st.dataframe(anom_df, use_container_width=True, hide_index=True)
            else:
                st.success("✅ Henüz anomali kaydı yok.")

    st.markdown("---")
    st.caption("Stinga Finans Pro · WhatsApp + AI Harcama Takip Sistemi")


# ── ROUTER ───────────────────────────────────────────────────────────────────
if not st.session_state.giris_yapildi:
    giris_ekrani()
else:
    dashboard()
