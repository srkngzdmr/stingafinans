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
from flask import Flask, request, jsonify
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

# DB_FILE mutlak yol — Railway'de çalışma dizini kaymaları için
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stinga_v13_db.json")
DOVIZ_API_URL = "https://api.exchangerate-api.com/v4/latest/TRY"

PHONE_DIRECTORY = {
    "whatsapp:+905350328406": {
        "ad": "Okan İlhan",   "rol": "Saha Personeli",         "limit": 20000,
        "emoji": "🔧",  "yetki": "user",  "dashboard_key": "okan"
    },
    "whatsapp:+905322002337": {
        "ad": "Serkan Güzdemir", "rol": "İşletme Müdürü",      "limit": 50000,
        "emoji": "⚡",  "yetki": "admin", "dashboard_key": "serkan"
    },
    "whatsapp:+905547858627": {
        "ad": "Zeynep Özyaman", "rol": "Yönetim Kurulu Başkanı", "limit": 100000,
        "emoji": "👑",  "yetki": "admin", "dashboard_key": "zeynep"
    },
    "whatsapp:+905304305213": {
        "ad": "Şenol Özyaman", "rol": "Genel Müdür", "limit": 80000,
        "emoji": "🏢",  "yetki": "user", "dashboard_key": "senol",
        "dashboard_rol": "user", "dashboard_sifre": "456"
    },
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
    (0,    "🥉 Toplam Yüklemelerin"),
    (5,    "🥈 Toplam Yüklemelerin"),
    (15,   "🥇 Toplam Yüklemelerin"),
    (30,   "💎 Toplam Yüklemelerin"),
    (60,   "🏆 Toplam Yüklemelerin"),
    (100,  "👑 Toplam Yüklemelerin"),
]

# ───────────────────────────────────
#  VERİTABANI
# ───────────────────────────────────
def load_data() -> dict:
    default = {
        "expenses": [],
        # Harcırah bakiyeleri (dashboard Finans&Kasa bölümü)
        "wallets":  {"Zeynep Özyaman": 50000, "Serkan Güzdemir": 25000, "Okan İlhan": 5000, "Şenol Özyaman": 30000},
        # Proje bazlı bütçe (dashboard ultra-card göstergeleri)
        "budgets": {
            "Maden Sahası":   {"limit": 100000, "spent": 0},
            "Aktif Karbon":   {"limit": 80000,  "spent": 0},
            "Enerji Hatları": {"limit": 60000,  "spent": 0},
            "Genel Merkez":   {"limit": 40000,  "spent": 0},
        },
        # WhatsApp uyarıları için kişi limitleri
        "user_limits": {"Zeynep Özyaman": 50000, "Serkan Güzdemir": 10000, "Okan İlhan": 5000, "Şenol Özyaman": 30000},
        "anomaly_log": [],
        "duplicate_hashes": [],
        "user_states": {},
        "rozetler": {"Zeynep Özyaman": [], "Serkan Güzdemir": [], "Okan İlhan": [], "Şenol Özyaman": []},
        "fis_sayaci": {"Zeynep Özyaman": 0, "Serkan Güzdemir": 0, "Okan İlhan": 0, "Şenol Özyaman": 0},
        "karakter_modu": {},
        # Dashboard ek alanları
        "xp": {"Zeynep Özyaman": 0, "Serkan Güzdemir": 0, "Okan İlhan": 0, "Şenol Özyaman": 0},
        "notifications": [],
        "ledger": [],
    }
    # Önce ana, bozuksa backup dene
    for try_file in [DB_FILE, DB_FILE + ".bak"]:
        if not os.path.exists(try_file):
            continue
        try:
            with open(try_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in default.items():
                data.setdefault(k, v)
            # Yeni tam isimlerle eksik alt-alanlara ekle
            for field in ["wallets", "user_limits", "rozetler", "fis_sayaci", "xp"]:
                if "Şenol Özyaman" not in data.get(field, {}):
                    data[field]["Şenol Özyaman"] = default[field].get("Şenol Özyaman", 0 if field != "rozetler" else [])
            # budgets eski flat formattan migrate et
            budgets = data.get("budgets", {})
            if budgets and isinstance(list(budgets.values())[0], (int, float)):
                data["budgets"] = default["budgets"]
            print(f"DB yüklendi ({try_file}): {len(data.get('expenses',[]))} fiş", flush=True)
            return data
        except (json.JSONDecodeError, Exception) as e:
            print(f"DB okuma hatası ({try_file}): {e}", flush=True)
            continue
    print("UYARI: Geçerli DB bulunamadı, default döndürülüyor", flush=True)
    return default

import threading as _threading
_DB_LOCK = _threading.Lock()

def save_data(d: dict):
    """Thread-safe atomik kayıt. Lock + tmp dosya → veri bozulmasını önler."""
    tmp = DB_FILE + ".tmp"
    with _DB_LOCK:
        try:
            # Mevcut dosyayı backup al
            if os.path.exists(DB_FILE):
                try:
                    os.replace(DB_FILE, DB_FILE + ".bak")
                except:
                    pass
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
            os.replace(tmp, DB_FILE)
            print(f"DB kaydedildi: {len(d.get('expenses',[]))} fiş", flush=True)
        except Exception as e:
            print(f"KAYIT HATASI: {e}", flush=True)
            try:
                with open(DB_FILE, "w", encoding="utf-8") as f:
                    json.dump(d, f, ensure_ascii=False, indent=2)
            except Exception as e2:
                print(f"FALLBACK KAYIT HATASI: {e2}", flush=True)

def load_data_safe() -> dict:
    """Thread-safe okuma. Bozuk JSON'a karşı .bak dosyasından restore."""
    with _DB_LOCK:
        # Önce ana dosyayı dene
        for try_file in [DB_FILE, DB_FILE + ".bak"]:
            if os.path.exists(try_file):
                try:
                    with open(try_file, "r", encoding="utf-8") as f:
                        return json.load(f)
                except json.JSONDecodeError:
                    print(f"JSON BOZUK: {try_file}", flush=True)
                    continue
        # Hiçbiri yoksa boş DB döndür
        print("UYARI: DB dosyası bulunamadı, boş başlatılıyor", flush=True)
        return {}


def add_notification(target: str, message: str, notif_type: str = "info", data: dict = None):
    """Dashboard bildirim kuyruğuna ekle. data verilirse mevcut objeye yazar (kaydetmez)."""
    _own = data is None
    if _own:
        data = load_data()
    data.setdefault("notifications", [])
    data["notifications"].append({
        "user":  target,
        "msg":   message,
        "type":  notif_type,
        "time":  datetime.now().strftime("%H:%M"),
        "date":  datetime.now().strftime("%Y-%m-%d"),
        "read":  False,
    })
    if _own:
        save_data(data)


def add_xp(user_name: str, amount: int, reason: str = "", data: dict = None):
    """Dashboard XP sistemine puan ekle. data verilirse mevcut objeye yazar (kaydetmez)."""
    _own = data is None
    if _own:
        data = load_data()
    data.setdefault("xp", {})
    data["xp"][user_name] = data["xp"].get(user_name, 0) + amount
    if reason:
        data.setdefault("notifications", [])
        data["notifications"].append({
            "user":  user_name,
            "msg":   f"🏆 +{amount} XP kazandın! ({reason})",
            "type":  "xp",
            "time":  datetime.now().strftime("%H:%M"),
            "date":  datetime.now().strftime("%Y-%m-%d"),
            "read":  False,
        })
    if _own:
        save_data(data)

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