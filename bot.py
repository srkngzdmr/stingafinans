# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════╗
║         STINGA PRO v13 — WhatsApp AI Harcama Asistanı                   ║
║  • Psikolojik harcama profili & davranış analizi                         ║
║  • Gamification: rozet, seviye, ekip yarışması                           ║
║  • Dinamik AI karakter modu (dedektif / koç / muhaseci)                  ║
║  • Çok katmanlı sahte fiş dedektifi                                      ║
║  • Harcama kehaneti & erken uyarı sistemi                                ║
║  • Kişiselleştirilmiş yaratıcı fiş yorumu                                ║
║  • Anomali tespiti, döviz, NL2Query                                       ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import json, os, re, hashlib, statistics, random
from datetime import datetime, timedelta
from io import BytesIO
from collections import defaultdict

import requests
from flask import Flask, request
from google import genai
from PIL import Image
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client as TwilioClient

app = Flask(__name__)

# ─────────────────────────────────────────────
#  YAPILANDIRMA
# ─────────────────────────────────────────────
client     = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-2.5-flash"

TWILIO_SID   = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
twilio_client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)

DB_FILE      = "stinga_v13_db.json"
DOVIZ_API_URL = "https://api.exchangerate-api.com/v4/latest/TRY"

PHONE_DIRECTORY = {
    "whatsapp:+905350328406": {"ad": "Okan",   "rol": "Saha Müdürü",  "limit": 5000,  "emoji": "🔧"},
    "whatsapp:+905322002337": {"ad": "Serkan", "rol": "Muhasebe",     "limit": 10000, "emoji": "📊"},
    "whatsapp:+905547858627": {"ad": "Zeynep", "rol": "Genel Müdür",  "limit": 50000, "emoji": "👑"},
}

KATEGORILER = {
    "yemek":     ["restoran", "kafe", "market", "manav", "kasap", "ekmek", "cafe", "burger", "pizza", "döner"],
    "ulasim":    ["akaryakıt", "benzin", "otopark", "taksi", "uber", "servis", "shell", "bp", "opet", "petrol"],
    "ofis":      ["kırtasiye", "toner", "bilgisayar", "telefon", "ekipman", "teknosa", "mediamarkt"],
    "konaklama": ["otel", "apart", "hostel", "hilton", "marriott"],
    "eglence":   ["sinema", "konser", "etkinlik", "cinemaximum"],
    "saglik":    ["eczane", "hastane", "klinik", "doktor", "ilaç"],
}

# ─────────────────────────────────────────────
#  ROZET & SEVİYE SİSTEMİ
# ─────────────────────────────────────────────
ROZETLER = {
    "ilk_fis":        {"emoji": "🎯", "ad": "İlk Adım",        "aciklama": "İlk fişini girdin!"},
    "tasarruf_5":     {"emoji": "💚", "ad": "Tutumlu",          "aciklama": "5 kez bütçe altında kaldın"},
    "hizli_giris":    {"emoji": "⚡", "ad": "Flaş Muhasebeci",  "aciklama": "1 saatte 3+ fiş girdin"},
    "risk_avcisi":    {"emoji": "🕵️", "ad": "Risk Avcısı",     "aciklama": "Yüksek riskli fiş yakaladın"},
    "hafiza_ustasi":  {"emoji": "🧠", "ad": "Hafıza Ustası",    "aciklama": "30 gün üst üste aktif oldun"},
    "dovec_kral":     {"emoji": "💱", "ad": "Döviz Kralı",      "aciklama": "5 farklı dövizde fiş girdin"},
    "dedektif":       {"emoji": "🔍", "ad": "Sahte Avcısı",     "aciklama": "Sahte fiş tespit ettin"},
    "ekonomist":      {"emoji": "📈", "ad": "Ekonomist",        "aciklama": "Bütçeni hiç aşmadın (1 ay)"},
}

SEVIYELER = [
    (0,    "🥉 Stajyer Muhasebeci"),
    (5,    "🥈 Junior Analist"),
    (15,   "🥇 Kıdemli Analist"),
    (30,   "💎 Finans Uzmanı"),
    (60,   "🏆 CFO Adayı"),
    (100,  "👑 Finans Efsanesi"),
]

# ─────────────────────────────────────────────
#  VERİTABANI
# ─────────────────────────────────────────────
def load_data() -> dict:
    default = {
        "expenses": [],
        "wallets":  {"Zeynep": 0, "Serkan": 0, "Okan": 0},
        "budgets":  {"Zeynep": 50000, "Serkan": 10000, "Okan": 5000},
        "anomaly_log": [],
        "duplicate_hashes": [],
        "user_states": {},
        "rozetler": {"Zeynep": [], "Serkan": [], "Okan": []},
        "fis_sayaci": {"Zeynep": 0, "Serkan": 0, "Okan": 0},
        "karakter_modu": {},   # kullanıcı → aktif karakter
    }
    if not os.path.exists(DB_FILE):
        return default
    with open(DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for k, v in default.items():
        data.setdefault(k, v)
    return data

def save_data(d: dict):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

# ─────────────────────────────────────────────
#  YARDIMCI
# ─────────────────────────────────────────────
@app.after_request
def add_header(response):
    response.headers['ngrok-skip-browser-warning'] = 'true'
    return response

def gorsel_hash(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()

def kategori_tespit(firma: str) -> str:
    f = firma.lower()
    for kat, kelimeler in KATEGORILER.items():
        if any(k in f for k in kelimeler):
            return kat
    return "diger"

def seviye_hesapla(fis_sayisi: int) -> str:
    seviye = SEVIYELER[0][1]
    for minimum, ad in SEVIYELER:
        if fis_sayisi >= minimum:
            seviye = ad
    return seviye

def rozet_kontrol(user_name: str, data: dict, yeni_fis: dict) -> list[str]:
    """Rozet kazanımlarını kontrol et, yeni kazanılanları döndür."""
    kazanilanlar = []
    mevcut = data["rozetler"].get(user_name, [])
    fis_sayisi = data["fis_sayaci"].get(user_name, 0)
    tum_fisler = [e for e in data["expenses"] if e["Kullanıcı"] == user_name]

    def ekle(rozet_id):
        if rozet_id not in mevcut:
            mevcut.append(rozet_id)
            kazanilanlar.append(rozet_id)

    if fis_sayisi == 1:
        ekle("ilk_fis")
    if yeni_fis.get("Risk_Skoru", 0) >= 70:
        ekle("risk_avcisi")
    if yeni_fis.get("Durum") == "⚠️ Sahte Şüphesi":
        ekle("dedektif")

    # Son 1 saatte 3+ fiş
    bir_saat_once = datetime.now() - timedelta(hours=1)
    son_1h = [e for e in tum_fisler if datetime.strptime(e["Tarih"], "%Y-%m-%d") >= bir_saat_once.replace(hour=0, minute=0, second=0)]
    if len(son_1h) >= 3:
        ekle("hizli_giris")

    # Farklı döviz sayısı
    dovizler = set(e.get("ParaBirimi", "TRY") for e in tum_fisler if e.get("ParaBirimi") != "TRY")
    if len(dovizler) >= 5:
        ekle("dovec_kral")

    data["rozetler"][user_name] = mevcut
    return kazanilanlar

# ─────────────────────────────────────────────
#  AI FONKSİYONLARI
# ─────────────────────────────────────────────

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
    butce   = data["budgets"].get(user_name, 0)
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
        butce = data["budgets"].get(user, 1)
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
    kullanici = next((v for k, v in PHONE_DIRECTORY.items() if v["ad"] == user_name), None)
    if kullanici and tutar > kullanici["limit"]:
        uyarilar.append(f"⚠️ Limit aşımı! ({tutar:.0f} ₺ > {kullanici['limit']:.0f} ₺)")
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


def butce_durumu(user_name: str, data: dict) -> str:
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
    user_info     = PHONE_DIRECTORY.get(sender_phone, {"ad": "Bilinmeyen", "rol": "—", "limit": 0, "emoji": "👤"})
    user_name     = user_info["ad"]

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
        msg.body(
            f"🤖 *STINGA PRO v13*\n"
            f"{user_info['emoji']} {user_name} | {seviye}\n"
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
            f"📉 Bütçe: {butce_durumu(user_name, data)}\n\n"
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
        msg.body(f"💳 *Cüzdan*\nBakiye: *{bakiye:,.0f} ₺*\nLimit: {user_info['limit']:,.0f} ₺")
        return str(resp)

    # SON 5
    if mesaj_lower == "son5":
        son5 = [e for e in data["expenses"] if e["Kullanıcı"] == user_name][-5:]
        if not son5:
            msg.body("Henüz harcama yok.")
        else:
            satirlar = [f"🏢 {e['Firma']} — {e['Tutar']:,.0f} ₺ ({e['Tarih']})" for e in reversed(son5)]
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
        sonuclar = [e for e in data["expenses"] if e["Kullanıcı"] == user_name and kelime in e.get("Firma","").lower()]
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
        try:
            res = requests.get(media_url, auth=(TWILIO_SID, TWILIO_TOKEN), allow_redirects=False, timeout=15)
            if res.status_code in [301, 302, 307, 308]:
                res = requests.get(res.headers.get('Location'), timeout=15)

            raw_bytes = res.content
            img_hash  = gorsel_hash(raw_bytes)

            if img_hash in data["duplicate_hashes"]:
                msg.body("⚠️ *Mükerrer Fiş!*\nBu fişi daha önce girdiniz. Farklı bir fiş gönderin.")
                return str(resp)

            image = Image.open(BytesIO(raw_bytes))

            # ── GEMINI: Ultra detaylı analiz promptu
            prompt = """Sen hem mali denetçi hem adli belge uzmanısın. Fişi analiz et ve SADECE JSON döndür:
{
  "firma": "Firma adı",
  "tarih": "YYYY-MM-DD",
  "toplam_tutar": 0.0,
  "kdv_tutari": 0.0,
  "odeme_yontemi": "nakit|kredi_karti|havale",
  "kalemler": [{"aciklama": "...", "tutar": 0.0}],
  "para_birimi": "TRY",
  "risk_skoru": 0,
  "risk_nedenleri": ["neden1", "neden2"],
  "audit_notu": "kısa özet",
  "sahte_mi": false,
  "sahtelik_nedeni": "",
  "gorsel_kalitesi": "iyi|orta|kotu",
  "fis_turu": "restoran|market|akaryakıt|otel|diger",
  "ilginc_detay": "fişte dikkat çeken garip veya ilginç bir şey"
}
Sahtelik: düzensiz font, tutarsız toplam, eksik vergi no, farklı yazı tipleri."""

            ai_res    = client.models.generate_content(model=MODEL_NAME, contents=[prompt, image])
            json_text = re.sub(r"```json?|```", "", ai_res.text).strip()
            fis       = json.loads(json_text)

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

            # Fişi kaydet
            data["fis_sayaci"][user_name] = data["fis_sayaci"].get(user_name, 0) + 1
            new_expense = {
                "ID"          : datetime.now().strftime("%Y%m%d%H%M%S"),
                "Tarih"       : fis.get("tarih", datetime.now().strftime("%Y-%m-%d")),
                "Kullanıcı"   : user_name,
                "Rol"         : user_info["rol"],
                "Firma"       : fis.get("firma", "Bilinmiyor"),
                "Tutar"       : tutar_try,
                "KDV"         : float(fis.get("kdv_tutari", 0)),
                "ParaBirimi"  : para_birimi,
                "OdemeTipi"   : fis.get("odeme_yontemi", "bilinmiyor"),
                "Kategori"    : kategori,
                "Durum"       : "⚠️ Sahte Şüphesi" if sahtelik["sahte_mi"] else "Onay Bekliyor",
                "Risk_Skoru"  : sahtelik["guvensizlik_skoru"],
                "AI_Audit"    : fis.get("audit_notu", ""),
                "Anomaliler"  : anomaliler,
                "Hash"        : img_hash,
                "Karakter"    : karakter,
                "IlgincDetay" : fis.get("ilginc_detay", ""),
            }

            data["expenses"].append(new_expense)
            data["duplicate_hashes"].append(img_hash)
            if anomaliler:
                data["anomaly_log"].append({
                    "tarih"     : datetime.now().isoformat(),
                    "kullanici" : user_name,
                    "tutar"     : tutar_try,
                    "uyarilar"  : anomaliler,
                })

            # Rozet kontrolü
            yeni_rozetler = rozet_kontrol(user_name, data, new_expense)
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

            yanit = (
                f"✅ *FİŞ ALINDI*\n"
                f"{'─'*28}\n"
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
                + f"\n\n📊 Bütçe: {butce_durumu(user_name, data)}"
                + f"\n{seviye} • #{data['fis_sayaci'].get(user_name,0)} fiş"
                + sahte_str
                + anomali_str
                + rozet_str
                + f"\n\n🔖 `{new_expense['ID']}`"
            )
            msg.body(yanit)

        except json.JSONDecodeError:
            msg.body("❌ Fiş okunamadı. Daha net bir fotoğraf çekip tekrar deneyin.")
        except Exception as e:
            msg.body(f"❌ Hata: {str(e)}")

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
    return {
        "ay": bu_ay, "toplam": toplam,
        "fis_sayisi": len(ay_fis),
        "anomali_sayisi": len(data.get("anomaly_log",[])),
        "kullanici_bazli": dict(k_bazli),
        "kategori_bazli": dict(c_bazli),
        "ekip_rozetleri": data.get("rozetler", {}),
    }, 200


if __name__ == "__main__":
    app.run(port=5000, debug=False)
