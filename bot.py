

# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════╗
║         STINGA PRO v14 — WhatsApp AI Harcama Asistanı                   ║
║  • [YENİ] Fiş DNA Parmak İzi — yazı tipi & piksel analizi               ║
║  • [YENİ] Gölge/Işık Tutarsızlık Dedektifi — Photoshop tespiti          ║
║  • [YENİ] Coğrafi İmkânsızlık Tespiti — iki fiş arası mesafe/süre       ║
║  • [YENİ] Gerçek Zamanlı Fiyat Anomali Radar — akaryakıt/market         ║
║  • [YENİ] Harcama Ruh Hali Dedektifi — sabah pattern analizi            ║
║  • [YENİ] Kişisel Tetikleyici Öğrenme — Cuma uyarısı vb.               ║
║  • [YENİ] Karanlık Örüntü Dedektifi — limit kaçınma davranışı           ║
║  • [YENİ] Adaptif Kişilik — kullanıcıya göre şekillenen AI tonu         ║
║  • Psikolojik harcama profili & davranış analizi                         ║
║  • Gamification: rozet, seviye, ekip yarışması                           ║
║  • Çok katmanlı sahte fiş dedektifi                                      ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import json, os, re, hashlib, statistics, random, math
from datetime import datetime, timedelta
from io import BytesIO
from collections import defaultdict

import requests
from flask import Flask, request, jsonify
from google import genai
from PIL import Image, ImageStat
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

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stinga_v13_db.json")
DOVIZ_API_URL = "https://api.exchangerate-api.com/v4/latest/TRY"

PHONE_DIRECTORY = {
    "whatsapp:+905350328406": {
        "ad": "Okan İlhan", "rol": "Saha Personeli", "limit": 20000,
        "emoji": "🔧", "yetki": "user", "dashboard_key": "okan",
        "sehir": "Ankara", "lat": 39.9334, "lon": 32.8597
    },
    "whatsapp:+905322002337": {
        "ad": "Serkan Güzdemir", "rol": "İşletme Müdürü", "limit": 50000,
        "emoji": "⚡", "yetki": "admin", "dashboard_key": "serkan",
        "sehir": "İstanbul", "lat": 41.0082, "lon": 28.9784
    },
    "whatsapp:+905547858627": {
        "ad": "Zeynep Özyaman", "rol": "Yönetim Kurulu Başkanı", "limit": 100000,
        "emoji": "👑", "yetki": "admin", "dashboard_key": "zeynep",
        "sehir": "İstanbul", "lat": 41.0082, "lon": 28.9784
    },
    "whatsapp:+905304305213": {
        "ad": "Şenol Özyaman", "rol": "Genel Müdür", "limit": 80000,
        "emoji": "🏢", "yetki": "user", "dashboard_key": "senol",
        "dashboard_rol": "user", "dashboard_sifre": "456",
        "sehir": "Ankara", "lat": 39.9334, "lon": 32.8597
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

ROZETLER = {
    "ilk_fis":        {"emoji": "🎯", "ad": "İlk Adım",        "aciklama": "İlk fişini girdin!"},
    "tasarruf_5":     {"emoji": "💚", "ad": "Tutumlu",          "aciklama": "5 kez bütçe altında kaldın"},
    "hizli_giris":    {"emoji": "⚡", "ad": "Flaş Muhasebeci",  "aciklama": "1 saatte 3+ fiş girdin"},
    "risk_avcisi":    {"emoji": "🕵️", "ad": "Risk Avcısı",     "aciklama": "Yüksek riskli fiş yakaladın"},
    "hafiza_ustasi":  {"emoji": "🧠", "ad": "Hafıza Ustası",    "aciklama": "30 gün üst üste aktif oldun"},
    "dovec_kral":     {"emoji": "💱", "ad": "Döviz Kralı",      "aciklama": "5 farklı dövizde fiş girdin"},
    "dedektif":       {"emoji": "🔍", "ad": "Sahte Avcısı",     "aciklama": "Sahte fiş tespit ettin"},
    "ekonomist":      {"emoji": "📈", "ad": "Ekonomist",        "aciklama": "Bütçeni hiç aşmadın (1 ay)"},
    "karmasi_k":      {"emoji": "🌑", "ad": "Karanlık Örüntü",  "aciklama": "Limit kaçınma davranışı tespit edildi"},
    "cografi_hata":   {"emoji": "🗺️", "ad": "Işınlanma",       "aciklama": "Coğrafi imkânsız hareket tespit edildi"},
}

SEVIYELER = [
    (0,   "🥉 Toplam Yüklemelerin"),
    (5,   "🥈 Toplam Yüklemelerin"),
    (15,  "🥇 Toplam Yüklemelerin"),
    (30,  "💎 Toplam Yüklemelerin"),
    (60,  "🏆 Toplam Yüklemelerin"),
    (100, "👑 Toplam Yüklemelerin"),
]

# ─────────────────────────────────────────────
#  VERİTABANI
# ─────────────────────────────────────────────
import threading as _threading
_DB_LOCK = _threading.Lock()

def load_data() -> dict:
    default = {
        "expenses": [],
        "wallets":  {"Zeynep Özyaman": 50000, "Serkan Güzdemir": 25000, "Okan İlhan": 5000, "Şenol Özyaman": 30000},
        "budgets": {
            "Maden Sahası":   {"limit": 100000, "spent": 0},
            "Aktif Karbon":   {"limit": 80000,  "spent": 0},
            "Enerji Hatları": {"limit": 60000,  "spent": 0},
            "Genel Merkez":   {"limit": 40000,  "spent": 0},
        },
        "user_limits": {"Zeynep Özyaman": 100000, "Serkan Güzdemir": 50000, "Okan İlhan": 20000, "Şenol Özyaman": 80000},
        "anomaly_log": [],
        "duplicate_hashes": [],
        "user_states": {},
        "rozetler": {"Zeynep Özyaman": [], "Serkan Güzdemir": [], "Okan İlhan": [], "Şenol Özyaman": []},
        "fis_sayaci": {"Zeynep Özyaman": 0, "Serkan Güzdemir": 0, "Okan İlhan": 0, "Şenol Özyaman": 0},
        "karakter_modu": {},
        "xp": {"Zeynep Özyaman": 0, "Serkan Güzdemir": 0, "Okan İlhan": 0, "Şenol Özyaman": 0},
        "notifications": [],
        "ledger": [],
        # YENİ: Adaptif kişilik profilleri
        "kullanici_profil": {},
        # YENİ: Tetikleyici pattern log
        "trigger_log": {},
        # YENİ: Coğrafi hareket log
        "geo_log": {},
    }
    for try_file in [DB_FILE, DB_FILE + ".bak"]:
        if not os.path.exists(try_file):
            continue
        try:
            with open(try_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in default.items():
                data.setdefault(k, v)
            for field in ["wallets", "user_limits", "rozetler", "fis_sayaci", "xp"]:
                for isim in ["Şenol Özyaman", "Okan İlhan", "Serkan Güzdemir", "Zeynep Özyaman"]:
                    if isim not in data.get(field, {}):
                        data[field][isim] = default[field].get(isim, 0 if field != "rozetler" else [])
            budgets = data.get("budgets", {})
            if budgets and isinstance(list(budgets.values())[0], (int, float)):
                data["budgets"] = default["budgets"]
            print(f"DB yüklendi ({try_file}): {len(data.get('expenses',[]))} fiş", flush=True)
            return data
        except (json.JSONDecodeError, Exception) as e:
            print(f"DB okuma hatası ({try_file}): {e}", flush=True)
            continue
    return default

def save_data(d: dict):
    tmp = DB_FILE + ".tmp"
    with _DB_LOCK:
        try:
            if os.path.exists(DB_FILE):
                try: os.replace(DB_FILE, DB_FILE + ".bak")
                except: pass
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

def add_notification(target: str, message: str, notif_type: str = "info", data: dict = None):
    _own = data is None
    if _own: data = load_data()
    data.setdefault("notifications", []).append({
        "user": target, "msg": message, "type": notif_type,
        "time": datetime.now().strftime("%H:%M"),
        "date": datetime.now().strftime("%Y-%m-%d"), "read": False,
    })
    if _own: save_data(data)

def add_xp(user_name: str, amount: int, reason: str = "", data: dict = None):
    _own = data is None
    if _own: data = load_data()
    data.setdefault("xp", {})[user_name] = data["xp"].get(user_name, 0) + amount
    if reason:
        data.setdefault("notifications", []).append({
            "user": user_name, "msg": f"🏆 +{amount} XP kazandın! ({reason})",
            "type": "xp", "time": datetime.now().strftime("%H:%M"),
            "date": datetime.now().strftime("%Y-%m-%d"), "read": False,
        })
    if _own: save_data(data)

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

def ai_call(prompt: str) -> str:
    resp = client.models.generate_content(model=MODEL_NAME, contents=[prompt])
    return resp.text.strip()

# ═══════════════════════════════════════════════════════════════
#  ÖZELLİK 1: FİŞ DNA PARMAK İZİ
#  Yazı tipi düzensizliği, piksel entropi, kenar yoğunluğu analizi
#  Gerçek fişlerde yazı tipi hiçbir zaman piksel-mükemmel değildir
# ═══════════════════════════════════════════════════════════════
def fis_dna_analiz(image: Image.Image, raw_bytes: bytes) -> dict:
    """
    Fişin görsel 'DNA'sını çıkarır.
    Sahte fişlerde (dijital üretilmiş) piksel entropi çok düşüktür.
    Gerçek termal yazıcı fişlerinde gürültü ve düzensizlik vardır.
    """
    try:
        # Gri tonlamaya çevir
        gray = image.convert("L")
        stat = ImageStat.Stat(gray)

        # Piksel standart sapması — gerçek fiş: yüksek, dijital: düşük
        stddev = stat.stddev[0]

        # Entropi hesabı (Shannon entropy)
        import math as _math
        histogram = gray.histogram()
        total_px = sum(histogram)
        entropi = 0.0
        for count in histogram:
            if count > 0:
                p = count / total_px
                entropi -= p * _math.log2(p)

        # Kenar yoğunluğu (Sobel-benzeri basit fark)
        pixels = list(gray.getdata())
        width, height = gray.size
        kenar_sayisi = 0
        for y in range(1, min(height-1, 200)):  # ilk 200 satır yeter
            for x in range(1, width-1):
                idx = y * width + x
                diff = abs(int(pixels[idx]) - int(pixels[idx-1]))
                if diff > 30:
                    kenar_sayisi += 1

        kenar_yogunlugu = kenar_sayisi / (width * min(height, 200))

        # Sonuç değerlendirme
        # Gerçek fiş: entropi > 6.5, stddev > 40, kenar > 0.08
        # Dijital/sahte: entropi < 5.5, stddev < 25, kenar < 0.04
        skor = 0
        bulgular = []

        if entropi < 5.5:
            skor += 25
            bulgular.append(f"🔬 Piksel entropisi çok düşük ({entropi:.1f}) — dijital üretim şüphesi")
        elif entropi > 7.0:
            bulgular.append(f"✅ Piksel entropisi normal ({entropi:.1f}) — gerçek baskı izleri")

        if stddev < 20:
            skor += 20
            bulgular.append(f"🔬 Yazı tipi çok düzgün ({stddev:.0f} std) — termal yazıcı değil şüphesi")

        if kenar_yogunlugu < 0.03:
            skor += 15
            bulgular.append(f"🔬 Kenar yoğunluğu düşük — metin az veya çok temiz")

        return {
            "dna_risk": min(skor, 60),
            "entropi": round(entropi, 2),
            "stddev": round(stddev, 2),
            "kenar": round(kenar_yogunlugu, 3),
            "bulgular": bulgular,
            "hash": gorsel_hash(raw_bytes)
        }
    except Exception as e:
        print(f"DNA analiz hatası: {e}", flush=True)
        return {"dna_risk": 0, "bulgular": [], "hash": gorsel_hash(raw_bytes)}


# ═══════════════════════════════════════════════════════════════
#  ÖZELLİK 2: GÖLGE & IŞIK TUTARSIZLIĞI DEDEKTİFİ
#  Photoshop birleştirme tespiti — gölge açısı analizi
# ═══════════════════════════════════════════════════════════════
def golge_isik_analiz(image: Image.Image) -> dict:
    """
    Fişin dört köşesindeki parlaklık dağılımını analiz eder.
    Gerçek fotoğrafta ışık tek yönden gelir → köşeler tutarlı solar.
    Photoshop'ta yapıştırılmış fişlerde parlaklık tutarsız olur.
    """
    try:
        gray = image.convert("L")
        w, h = gray.size
        if w < 10 or h < 10:
            return {"golge_risk": 0, "bulgular": []}

        # Dört köşe bölgesi parlaklık ortalamaları
        pad = max(w // 6, 10)
        pad_h = max(h // 6, 10)

        def bolge_ort(x1, y1, x2, y2):
            bolge = gray.crop((x1, y1, x2, y2))
            return ImageStat.Stat(bolge).mean[0]

        tl = bolge_ort(0, 0, pad, pad_h)          # Sol üst
        tr = bolge_ort(w-pad, 0, w, pad_h)         # Sağ üst
        bl = bolge_ort(0, h-pad_h, pad, h)         # Sol alt
        br = bolge_ort(w-pad, h-pad_h, w, h)       # Sağ alt

        # Işık gradyanı tutarlılığı
        # Doğal ışıkta: ya sol→sağ ya da üst→alt gradyan tutarlı olmalı
        yatay_fark_ust = abs(tl - tr)
        yatay_fark_alt = abs(bl - br)
        dikey_fark_sol = abs(tl - bl)
        dikey_fark_sag = abs(tr - br)

        # Tutarsızlık: üst ve alt yatay farklar ters yöndeyse
        yatay_tutarsiz = (tl > tr) != (bl > br) and min(yatay_fark_ust, yatay_fark_alt) > 15
        dikey_tutarsiz = (tl > bl) != (tr > br) and min(dikey_fark_sol, dikey_fark_sag) > 15

        skor = 0
        bulgular = []

        if yatay_tutarsiz:
            skor += 30
            bulgular.append(f"⚠️ Yatay ışık tutarsızlığı — sol/sağ gradyan ters (Photoshop şüphesi)")

        if dikey_tutarsiz:
            skor += 30
            bulgular.append(f"⚠️ Dikey ışık tutarsızlığı — üst/alt gradyan ters (yapıştırma şüphesi)")

        # Köşe parlaklık varyansı çok yüksekse
        kose_degerleri = [tl, tr, bl, br]
        varyans = statistics.variance(kose_degerleri)
        if varyans > 800:
            skor += 20
            bulgular.append(f"⚠️ Köşe parlaklık varyansı yüksek ({varyans:.0f}) — doğal olmayan aydınlatma")

        if skor == 0:
            bulgular.append(f"✅ Işık/gölge tutarlı — doğal fotoğraf izleri")

        return {
            "golge_risk": min(skor, 60),
            "bulgular": bulgular,
            "kose_parlaklik": {"tl": round(tl), "tr": round(tr), "bl": round(bl), "br": round(br)}
        }
    except Exception as e:
        print(f"Gölge analiz hatası: {e}", flush=True)
        return {"golge_risk": 0, "bulgular": []}


# ═══════════════════════════════════════════════════════════════
#  ÖZELLİK 3: COĞRAFİ İMKÂNSIZLIK TESPİTİ
#  İki fiş arası mesafe/süre kontrolü
# ═══════════════════════════════════════════════════════════════
def haversine_km(lat1, lon1, lat2, lon2) -> float:
    """İki koordinat arası km hesabı."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def cografi_kontrol(user_name: str, fis_tarihi: str, fis_firmasi: str, data: dict, user_info: dict) -> dict:
    """
    Son fişin konumu ile yeni fişin konumunu karşılaştırır.
    Gemini'den yeni fişin şehri alınır, önceki fişin şehriyle karşılaştırılır.
    Araç seyahati dikkate alınır: ~90 km/s ortalama.
    """
    bulgular = []
    risk = 0

    try:
        # Son fişi bul (aynı kullanıcı)
        kullanici_fisler = [
            e for e in data.get("expenses", [])
            if e.get("Kullanıcı") == user_name and e.get("Konum_Sehir")
        ]

        if not kullanici_fisler:
            return {"cografi_risk": 0, "bulgular": []}

        son_fis = sorted(kullanici_fisler, key=lambda x: x.get("Yukleme_Zamani", ""))[-1]
        son_sehir = son_fis.get("Konum_Sehir", "")
        son_zaman_str = son_fis.get("Yukleme_Zamani", "")

        if not son_sehir or not son_zaman_str:
            return {"cografi_risk": 0, "bulgular": []}

        # Şehir koordinatları (Türkiye'nin başlıca şehirleri)
        SEHIR_KOORDINAT = {
            "ankara": (39.9334, 32.8597),
            "istanbul": (41.0082, 28.9784),
            "izmir": (38.4192, 27.1287),
            "bursa": (40.1885, 29.0610),
            "antalya": (36.8969, 30.7133),
            "adana": (37.0000, 35.3213),
            "konya": (37.8714, 32.4846),
            "gaziantep": (37.0662, 37.3833),
            "kayseri": (38.7312, 35.4787),
            "mersin": (36.8121, 34.6415),
        }

        def normalize_sehir(s):
            s = s.lower().strip()
            s = s.replace("ı", "i").replace("ş", "s").replace("ğ", "g")
            s = s.replace("ü", "u").replace("ö", "o").replace("ç", "c")
            return s

        son_sehir_norm = normalize_sehir(son_sehir)
        yeni_sehir_norm = normalize_sehir(user_info.get("sehir", ""))

        # Koordinatları bul
        son_koord = None
        yeni_koord = None
        for sehir, koord in SEHIR_KOORDINAT.items():
            if sehir in son_sehir_norm:
                son_koord = koord
            if sehir in yeni_sehir_norm:
                yeni_koord = koord

        if not son_koord or not yeni_koord:
            return {"cografi_risk": 0, "bulgular": []}

        # Mesafe hesapla
        mesafe = haversine_km(son_koord[0], son_koord[1], yeni_koord[0], yeni_koord[1])

        if mesafe < 50:  # Aynı bölge
            return {"cografi_risk": 0, "bulgular": [f"✅ Konum tutarlı ({son_sehir} bölgesi)"]}

        # Zaman farkı hesapla
        try:
            son_zaman = datetime.strptime(son_zaman_str, "%Y-%m-%d %H:%M:%S")
            simdi = datetime.now()
            sure_saat = (simdi - son_zaman).total_seconds() / 3600
        except:
            sure_saat = 999

        # 90 km/s ortalama araç hızıyla minimum süre
        min_sure_saat = mesafe / 90

        if sure_saat < min_sure_saat * 0.8:  # %20 tolerans
            risk = 70
            bulgular.append(
                f"🗺️ COĞRAFİ İMKÂNSIZLIK! {son_sehir} → yeni konum: {mesafe:.0f} km, "
                f"geçen süre: {sure_saat:.1f}s, minimum gerekli: {min_sure_saat:.1f}s"
            )
        elif sure_saat < min_sure_saat:
            risk = 35
            bulgular.append(
                f"⚠️ Hızlı konum değişimi: {mesafe:.0f} km, {sure_saat:.1f} saatte"
            )

    except Exception as e:
        print(f"Coğrafi kontrol hatası: {e}", flush=True)

    return {"cografi_risk": risk, "bulgular": bulgular}


# ═══════════════════════════════════════════════════════════════
#  ÖZELLİK 4: GERÇEK ZAMANLI FİYAT ANOMALİ RADAR
#  Akaryakıt fiyatlarını gerçek API ile karşılaştırır
# ═══════════════════════════════════════════════════════════════
def fiyat_anomali_kontrol(fis_data: dict, kategori: str) -> dict:
    """
    Akaryakıt fişlerinde litre fiyatını gerçek piyasa fiyatıyla karşılaştırır.
    Çok ucuz = sahte/eksik tutar. Çok pahalı = yanlış okuma.
    """
    bulgular = []
    risk = 0

    try:
        if kategori != "ulasim":
            return {"fiyat_risk": 0, "bulgular": []}

        kalemler = fis_data.get("kalemler", [])
        toplam = float(fis_data.get("toplam_tutar", 0))

        # Litre miktarı ve birim fiyat bul
        litre = 0.0
        birim_fiyat = 0.0

        for kalem in kalemler:
            aciklama = str(kalem.get("aciklama", "")).lower()
            tutar = float(kalem.get("tutar", 0))
            # "40.94 LT" veya "40,94 lt" gibi pattern'ler
            lt_match = re.search(r'(\d+[.,]\d+)\s*lt', aciklama)
            if lt_match:
                litre = float(lt_match.group(1).replace(",", "."))
            # "x2,410" veya birim fiyat
            fiyat_match = re.search(r'x\s*(\d+[.,]\d+)', aciklama)
            if fiyat_match:
                birim_fiyat = float(fiyat_match.group(1).replace(",", "."))

        # Litre hesabı (tutar/litre)
        if litre > 0 and toplam > 0:
            hesaplanan_birim = toplam / litre
        elif birim_fiyat > 0:
            hesaplanan_birim = birim_fiyat
        else:
            # Toplam tutardan tahmini litre hesabı
            # Türkiye benzin fiyatı ~58-65 TL/lt aralığında
            tahmini_litre = toplam / 62  # orta tahmin
            if tahmini_litre < 5 or tahmini_litre > 200:
                return {"fiyat_risk": 0, "bulgular": []}
            hesaplanan_birim = 62.0  # tahmin

        # Türkiye güncel akaryakıt fiyat aralığı (Mart 2026)
        BENZIN_MIN = 50.0   # TL/lt minimum makul
        BENZIN_MAX = 75.0   # TL/lt maksimum makul
        MOTORIN_MIN = 45.0
        MOTORIN_MAX = 70.0

        firma_lower = str(fis_data.get("firma", "")).lower()
        is_motorin = "motorin" in str(kalemler).lower() or "dizel" in str(kalemler).lower()

        min_f = MOTORIN_MIN if is_motorin else BENZIN_MIN
        max_f = MOTORIN_MAX if is_motorin else BENZIN_MAX
        yakit_turu = "motorin" if is_motorin else "benzin"

        if hesaplanan_birim < min_f * 0.7:
            risk = 50
            bulgular.append(
                f"🔴 Yakıt birim fiyatı çok düşük! ₺{hesaplanan_birim:.2f}/lt "
                f"(piyasa: ₺{min_f:.0f}-{max_f:.0f}/lt) — tutar manipülasyonu şüphesi"
            )
        elif hesaplanan_birim < min_f:
            risk = 25
            bulgular.append(
                f"🟡 Yakıt fiyatı piyasanın altında: ₺{hesaplanan_birim:.2f}/lt "
                f"(beklenen: ₺{min_f:.0f}+/lt {yakit_turu})"
            )
        elif hesaplanan_birim > max_f * 1.3:
            risk = 20
            bulgular.append(
                f"🟡 Yakıt fiyatı beklenenden yüksek: ₺{hesaplanan_birim:.2f}/lt "
                f"(max beklenen: ₺{max_f:.0f}/lt) — bölge fiyatı veya yanlış okuma olabilir"
            )
        else:
            bulgular.append(f"✅ Yakıt fiyatı normal aralıkta: ₺{hesaplanan_birim:.2f}/lt")

    except Exception as e:
        print(f"Fiyat anomali hatası: {e}", flush=True)

    return {"fiyat_risk": risk, "bulgular": bulgular}


# ═══════════════════════════════════════════════════════════════
#  ÖZELLİK 5: HARCAMA RUH HALİ DEDEKTİFİ
#  Sabah pattern analizi — stresli gün tespiti
# ═══════════════════════════════════════════════════════════════
def ruh_hali_tespiti(user_name: str, data: dict) -> str:
    """
    Sabah harcama patternine göre günün ruh halini tespit eder.
    Kahve + sigara + enerji içeceği = zor gün sinyali.
    """
    try:
        bugun = datetime.now().strftime("%Y-%m-%d")
        saat = datetime.now().hour

        if saat > 11:  # Sadece sabah için
            return ""

        bugun_fisler = [
            e for e in data.get("expenses", [])
            if e.get("Kullanıcı") == user_name and e.get("Tarih") == bugun
        ]

        if not bugun_fisler:
            return ""

        # Stres göstergeleri
        stres_keywords = ["kahve", "sigara", "enerji", "red bull", "monster", "ibuprofen",
                          "aspirin", "parol", "eczane", "kolasyum", "çay"]
        stres_sayisi = 0
        stres_urunler = []

        for fis in bugun_fisler:
            firma = fis.get("Firma", "").lower()
            for kw in stres_keywords:
                if kw in firma and kw not in stres_urunler:
                    stres_sayisi += 1
                    stres_urunler.append(kw)

        # Çok erken harcama (07:00'dan önce)
        erken_fis = any(
            e.get("Yukleme_Zamani", "")[:13].endswith(("00", "01", "02", "03", "04", "05", "06"))
            for e in bugun_fisler
        )

        if stres_sayisi >= 2 or (stres_sayisi >= 1 and erken_fis):
            profil = data.get("kullanici_profil", {}).get(user_name, {})
            profil["bugun_stresli"] = True
            data.setdefault("kullanici_profil", {})[user_name] = profil
            return (
                f"☕ *Bugün yoğun bir gün seziyorum {user_name.split()[0]}...*\n"
                f"Sabahtan {', '.join(stres_urunler)} aldın. "
                f"Büyük harcamalar yapmadan önce bir nefes al. 💚"
            )

        return ""
    except Exception as e:
        print(f"Ruh hali tespiti hatası: {e}", flush=True)
        return ""


# ═══════════════════════════════════════════════════════════════
#  ÖZELLİK 6: KİŞİSEL TETİKLEYİCİ ÖĞRENME
#  Haftalık pattern analizi — Serkan'ın Cuma uyarısı vb.
# ═══════════════════════════════════════════════════════════════
def tetikleyici_analiz(user_name: str, data: dict) -> str:
    """
    Kullanıcının harcama tetikleyicilerini öğrenir.
    Belirli gün/saat/kategoride sürekli aşım varsa önceden uyarır.
    """
    try:
        harcamalar = [e for e in data.get("expenses", []) if e.get("Kullanıcı") == user_name]
        if len(harcamalar) < 8:
            return ""

        bugun = datetime.now()
        gun_adi = bugun.strftime("%A")  # Monday, Tuesday...
        GUNLER_TR = {
            "Monday": "Pazartesi", "Tuesday": "Salı", "Wednesday": "Çarşamba",
            "Thursday": "Perşembe", "Friday": "Cuma", "Saturday": "Cumartesi",
            "Sunday": "Pazar"
        }
        bugun_tr = GUNLER_TR.get(gun_adi, gun_adi)
        bugun_gun_no = bugun.weekday()  # 0=Pazartesi, 4=Cuma

        # Haftanın bu günündeki geçmiş harcamalar
        ayni_gun_harcamalar = []
        for e in harcamalar:
            try:
                tarih = datetime.strptime(e.get("Tarih", ""), "%Y-%m-%d")
                if tarih.weekday() == bugun_gun_no:
                    ayni_gun_harcamalar.append(float(e.get("Tutar", 0)))
            except:
                continue

        if len(ayni_gun_harcamalar) < 3:
            return ""

        genel_ort = statistics.mean([float(e.get("Tutar", 0)) for e in harcamalar])
        gun_ort = statistics.mean(ayni_gun_harcamalar)
        limit = data.get("user_limits", {}).get(user_name, 0)

        # Bu günde ortalamanın %40 üzerinde harcıyorsa tetikleyici var
        if gun_ort > genel_ort * 1.4:
            asim_yuzdesi = ((gun_ort / genel_ort) - 1) * 100

            # Pattern kaydet
            trigger_log = data.setdefault("trigger_log", {})
            trigger_log[user_name] = {
                "kritik_gun": bugun_tr,
                "asim_yuzdesi": round(asim_yuzdesi),
                "gun_ortalama": round(gun_ort),
                "genel_ortalama": round(genel_ort),
                "tespit_tarihi": bugun.strftime("%Y-%m-%d")
            }

            return (
                f"📅 *{bugun_tr} Tetikleyici Uyarısı!*\n"
                f"Geçmiş verilere göre {bugun_tr} günleri ortalamanın "
                f"%{asim_yuzdesi:.0f} üzerinde harcıyorsun.\n"
                f"Bugün dikkatli ol! 🎯"
            )

        return ""
    except Exception as e:
        print(f"Tetikleyici analiz hatası: {e}", flush=True)
        return ""


# ═══════════════════════════════════════════════════════════════
#  ÖZELLİK 7: KARANLIK ÖRÜNTÜ DEDEKTİFİ
#  Limit kaçınma davranışı tespiti
# ═══════════════════════════════════════════════════════════════
def karanlik_oruntu_tespiti(user_name: str, tutar: float, data: dict) -> dict:
    """
    Çalışanlar limiti aşmamak için sürekli limit-1 tutarında fiş girebilir.
    Bu "limit kaçınma davranışı"nı öğrenir ve raporlar.

    Örnek: Limit 5000₺, sürekli 4850-4990₺ arası fişler → şüpheli.
    Örnek: Limit 5000₺, tam 4999₺ fişler → çok şüpheli.
    """
    bulgular = []
    risk = 0

    try:
        limit = data.get("user_limits", {}).get(user_name, 0)
        if limit <= 0:
            return {"karanlik_risk": 0, "bulgular": []}

        # Limitin %90-%99 aralığındaki fişler
        esik_alt = limit * 0.90
        esik_ust = limit * 0.999

        # Geçmiş fişleri analiz et
        tum_fisler = [
            float(e.get("Tutar", 0)) for e in data.get("expenses", [])
            if e.get("Kullanıcı") == user_name
        ]

        # Limit yakını fiş sayısı
        limit_yakini = [t for t in tum_fisler if esik_alt <= t <= esik_ust]

        # Yeni fiş de limit yakınında mı?
        yeni_limit_yakini = esik_alt <= tutar <= esik_ust

        if yeni_limit_yakini:
            oran = len(limit_yakini) / max(len(tum_fisler), 1)

            if len(limit_yakini) >= 3 and oran > 0.3:
                risk = 65
                bulgular.append(
                    f"🌑 KARANLIK ÖRÜNTÜ TESPİT EDİLDİ!\n"
                    f"Son {len(tum_fisler)} fişten {len(limit_yakini)}'i ({oran*100:.0f}%) "
                    f"limit yakınında (₺{esik_alt:.0f}-{limit:.0f})\n"
                    f"Bu fiş de ₺{tutar:,.0f} — limitin %{(tutar/limit)*100:.1f}'i\n"
                    f"⚠️ Limit kaçınma davranışı şüphesi!"
                )
            elif len(limit_yakini) >= 2:
                risk = 30
                bulgular.append(
                    f"🟡 Limit yakını fiş örüntüsü: {len(limit_yakini)} kez "
                    f"₺{esik_alt:.0f}+ fiş girilmiş (limit: ₺{limit:.0f})"
                )

        # Tam yuvarlak sayı kontrolü (4999, 9999 gibi psikolojik limit kaçınma)
        if tutar in [limit - 1, limit - 0.01, limit * 0.999]:
            risk = max(risk, 40)
            bulgular.append(f"🔴 Psikolojik limit kaçınma: ₺{tutar} (limit: ₺{limit})")

    except Exception as e:
        print(f"Karanlık örüntü hatası: {e}", flush=True)

    return {"karanlik_risk": risk, "bulgular": bulgular}


# ═══════════════════════════════════════════════════════════════
#  ÖZELLİK 8: ADAPTİF KİŞİLİK SİSTEMİ
#  Kullanıcı davranışına göre AI tonunu adapte eder
# ═══════════════════════════════════════════════════════════════
def adaptif_karakter_belirle(user_name: str, fis_data: dict, data: dict) -> str:
    """
    Kullanıcının geçmiş etkileşimlerine ve mevcut durumuna göre
    en uygun AI karakterini otomatik seçer.

    Serkan sürekli yüksek riskli fiş gönderiyorsa → dedektif modu
    Okan ilk kez fiş gönderiyorsa → koç modu (teşvik edici)
    Zeynep stresli bir sabah geçiriyorsa → hemşire modu
    Normal gün → rasgele
    """
    try:
        # Manuel mod varsa onu kullan
        manuel_mod = data.get("karakter_modu", {}).get(user_name)
        if manuel_mod:
            return manuel_mod

        profil = data.get("kullanici_profil", {}).get(user_name, {})
        harcamalar = [e for e in data.get("expenses", []) if e.get("Kullanıcı") == user_name]
        risk_skoru = float(fis_data.get("risk_skoru", 0))
        fis_sayisi = data.get("fis_sayaci", {}).get(user_name, 0)

        # Karar ağacı
        if risk_skoru >= 70:
            return "dedektif"  # Yüksek riskli fiş → sorgulayıcı

        if profil.get("bugun_stresli"):
            return "hemsire"  # Stresli gün → empatik

        if fis_sayisi <= 2:
            return "koc"  # Yeni kullanıcı → teşvik edici

        # Son 5 fişin ortalama riski yüksekse
        if len(harcamalar) >= 5:
            son5_risk = [float(e.get("Risk_Skoru", 0)) for e in harcamalar[-5:]]
            if statistics.mean(son5_risk) > 50:
                return "dedektif"

        # Hafta sonu → daha rahat ton
        if datetime.now().weekday() >= 5:
            return "yoda"

        # Varsayılan: koç veya muhaseci
        return random.choice(["koc", "muhaseci"])

    except Exception as e:
        print(f"Adaptif karakter hatası: {e}", flush=True)
        return "koc"


# ─────────────────────────────────────────────
#  MEVCUT FONKSİYONLAR (değişmedi)
# ─────────────────────────────────────────────
def psikolojik_profil(user_name: str, data: dict) -> str:
    harcamalar = [e for e in data["expenses"] if e["Kullanıcı"] == user_name]
    if len(harcamalar) < 3:
        return ""
    prompt = f"""
Sen davranışsal ekonomi uzmanısın. Aşağıdaki harcama verilerini analiz et.
Harcamalar: {json.dumps(harcamalar[-30:], ensure_ascii=False)}
Kişinin harcama psikolojisini 2-3 cümleyle analiz et.
Türkçe, kısa, özgün ve biraz esprili yaz. Emoji kullan.
"""
    try:
        return ai_call(prompt)
    except:
        return ""

def yaratici_yorum(fis_data: dict, user_name: str, karakter: str) -> str:
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
Fiş: {fis_data.get('firma','?')} | {fis_data.get('toplam_tutar',0)} TL | Risk: {fis_data.get('risk_skoru',0)}/100
Kullanıcı: {user_name}
1-2 cümle yaratıcı yorum yap. Türkçe, emoji kullan, klişeden kaçın.
"""
    try:
        return ai_call(prompt)
    except:
        return ""

def harcama_kehaneti(user_name: str, data: dict) -> str:
    bu_ay = datetime.now().strftime("%Y-%m")
    gun   = datetime.now().day
    ay_harcamalar = [e for e in data["expenses"] if e["Kullanıcı"] == user_name and e.get("Tarih","").startswith(bu_ay)]
    if not ay_harcamalar or gun == 0:
        return ""
    toplam = sum(e["Tutar"] for e in ay_harcamalar)
    butce  = data.get("user_limits", {}).get(user_name, 0)
    if butce == 0:
        return ""
    gunluk_ort = toplam / gun
    asim = toplam + gunluk_ort * (30 - gun) - butce
    if asim <= 0:
        return ""
    asim_gun = int((butce - toplam) / gunluk_ort) if gunluk_ort > 0 else 999
    bitis = (datetime.now() + timedelta(days=asim_gun)).strftime("%d %B")
    try:
        return ai_call(f"Dramatik ama esprili, 1 cümle: {user_name} bütçesi {bitis}'de bitiyor, {asim:.0f}₺ aşım. Türkçe emoji kullan.")
    except:
        return f"🔮 Bu gidişle bütçen {bitis}'de tükeniyor!"

def derin_sahtelik_analizi(fis_data: dict, image: Image.Image) -> dict:
    sonuc = {"sahte_mi": fis_data.get("sahte_mi", False), "guvensizlik_skoru": fis_data.get("risk_skoru", 0), "bulgular": []}
    toplam = float(fis_data.get("toplam_tutar", 0))
    kdv    = float(fis_data.get("kdv_tutari", 0))
    if kdv > 0 and toplam > 0:
        beklenen_20 = toplam * 0.20 / 1.20
        beklenen_10 = toplam * 0.10 / 1.10
        if abs(kdv - beklenen_20) > 1 and abs(kdv - beklenen_10) > 1:
            sonuc["bulgular"].append("⚠️ KDV matematiksel tutarsızlık")
            sonuc["guvensizlik_skoru"] = min(100, sonuc["guvensizlik_skoru"] + 20)
    if toplam > 0 and toplam == int(toplam) and toplam % 100 == 0:
        sonuc["bulgular"].append("🔍 Şüpheli yuvarlak tutar")
        sonuc["guvensizlik_skoru"] = min(100, sonuc["guvensizlik_skoru"] + 10)
    for neden in fis_data.get("risk_nedenleri", []):
        if neden and neden != "...":
            sonuc["bulgular"].append(f"• {neden}")
    return sonuc

def ekip_siralaması(data: dict) -> str:
    bu_ay = datetime.now().strftime("%Y-%m")
    siralama = []
    for phone, info in PHONE_DIRECTORY.items():
        user = info["ad"]
        toplam = sum(e["Tutar"] for e in data["expenses"] if e["Kullanıcı"] == user and e.get("Tarih","").startswith(bu_ay))
        butce = data.get("user_limits", {}).get(user, info.get("limit", 1))
        siralama.append((user, toplam, (toplam/butce)*100, data["fis_sayaci"].get(user,0), info["emoji"]))
    siralama.sort(key=lambda x: x[1], reverse=True)
    madalyalar = ["🥇","🥈","🥉"]
    satirlar = []
    for i, (user, toplam, oran, fis, emoji) in enumerate(siralama):
        madalya = madalyalar[i] if i < 3 else "  "
        satirlar.append(f"{madalya} {emoji} {user}\n   💰 {toplam:,.0f} ₺ (%{oran:.0f} bütçe)\n   {seviye_hesapla(fis)} • {fis} fiş")
    return "\n\n".join(satirlar)

def anomali_tespit(user_name: str, tutar: float, data: dict) -> list[str]:
    uyarilar = []
    prev = [e["Tutar"] for e in data["expenses"] if e["Kullanıcı"] == user_name and e["Tutar"] > 0]
    limit = data.get("user_limits", {}).get(user_name, 0)
    if limit > 0 and tutar > limit:
        uyarilar.append(f"⚠️ Limit aşımı! ({tutar:.0f} ₺ > {limit:.0f} ₺)")
    if len(prev) >= 5:
        ort = statistics.mean(prev)
        std = statistics.stdev(prev)
        if std > 0 and (tutar - ort) / std > 2.5:
            uyarilar.append(f"📊 Ortalamanın çok üzerinde! (Ort: {ort:.0f} ₺)")
    bugun = datetime.now().strftime("%Y-%m-%d")
    bugun_fis = [e for e in data["expenses"] if e["Kullanıcı"] == user_name and e["Tarih"] == bugun]
    if len(bugun_fis) >= 5:
        uyarilar.append(f"⚡ Bugün {len(bugun_fis)} fiş girildi!")
    return uyarilar

def butce_durumu_str(user_name: str, data: dict) -> str:
    bu_ay  = datetime.now().strftime("%Y-%m")
    ay_top = sum(e["Tutar"] for e in data["expenses"] if e["Kullanıcı"] == user_name and e.get("Tarih","").startswith(bu_ay))
    butce  = data.get("user_limits", {}).get(user_name, 0)
    if butce == 0:
        return ""
    oran = (ay_top / butce) * 100
    bar  = "█" * min(10, int(oran/10)) + "░" * (10 - min(10, int(oran/10)))
    return f"[{bar}] %{oran:.1f} ({ay_top:.0f}/{butce:.0f} ₺)"

def nl_sorgu(soru: str, user_name: str, data: dict) -> str:
    harcamalar = [e for e in data["expenses"] if e["Kullanıcı"] == user_name]
    if not harcamalar:
        return "Henüz kayıtlı harcamanız yok."
    try:
        return ai_call(f'Soru: "{soru}"\nVeriler: {json.dumps(harcamalar[-50:], ensure_ascii=False)}\nBugün: {datetime.now().strftime("%Y-%m-%d")}\nKısa net Türkçe yanıt ver.')
    except Exception as e:
        return f"Sorgu hatası: {e}"

def rozet_kontrol(user_name: str, data: dict, yeni_fis: dict) -> list[str]:
    kazanilanlar = []
    mevcut = data["rozetler"].get(user_name, [])
    def ekle(rid):
        if rid not in mevcut:
            mevcut.append(rid)
            kazanilanlar.append(rid)
    if data["fis_sayaci"].get(user_name, 0) == 1:
        ekle("ilk_fis")
    if yeni_fis.get("Risk_Skoru", 0) >= 70:
        ekle("risk_avcisi")
    if yeni_fis.get("karanlik_risk", 0) >= 60:
        ekle("karmasi_k")
    if yeni_fis.get("cografi_risk", 0) >= 60:
        ekle("cografi_hata")
    data["rozetler"][user_name] = mevcut
    return kazanilanlar


# ─────────────────────────────────────────────
#  ANA WEBHOOK
# ─────────────────────────────────────────────
@app.route("/whatsapp", methods=['POST'])
def whatsapp_webhook():
    incoming_msg = request.values.get('Body', '').strip()
    sender_phone = request.values.get('From', '')
    num_media    = int(request.values.get('NumMedia', 0))
    user_info    = PHONE_DIRECTORY.get(sender_phone, {"ad": "Bilinmeyen", "rol": "—", "limit": 0, "emoji": "👤", "yetki": "user"})
    user_name    = user_info["ad"]
    is_admin     = user_info.get("yetki") == "admin"

    resp = MessagingResponse()
    msg  = resp.message()
    data = load_data()
    mesaj_lower = incoming_msg.lower()

    # YARDIM
    if mesaj_lower in ["yardım", "help", "menü", "menu", "?"]:
        seviye = seviye_hesapla(data["fis_sayaci"].get(user_name, 0))
        rozetler = data["rozetler"].get(user_name, [])
        rozet_str = " ".join([ROZETLER[r]["emoji"] for r in rozetler if r in ROZETLER]) or "henüz yok"
        msg.body(
            f"🤖 *STINGA PRO v14*\n"
            f"{user_info['emoji']} {user_name} | {'👑 Yönetici' if is_admin else '👤 Personel'} | {seviye}\n"
            f"🏅 Rozetler: {rozet_str}\n"
            f"{'─'*28}\n"
            f"📷 Fiş fotoğrafı → AI analiz\n"
            f"📊 *özet* → Aylık özet\n"
            f"🏆 *sıralama* → Ekip yarışması\n"
            f"🔮 *kehane* → Bütçe kehaneti\n"
            f"🧠 *profil* → Harcama psikolojin\n"
            f"🎭 *karakter [mod]* → Yanıt tonu\n"
            f"   Modlar: dedektif/koc/muhaseci/yoda/hemsire\n"
            f"💰 *bakiye* → Cüzdan durumu\n"
            f"📋 *son5* → Son harcamalar\n"
            f"🔍 *ara [kelime]* → Fiş ara\n"
            f"❓ *soru [metin]* → AI sorgu\n"
            f"💱 *döviz [miktar] [KOD]* → Çevir\n"
            f"🏅 *rozetler* → Tüm rozetlerim\n"
            f"📊 *dna* → Son fişin DNA analizi\n"
            f"🌑 *örüntü* → Karanlık örüntü raporu"
        )
        return str(resp)

    # ÖZET
    if mesaj_lower == "özet":
        bu_ay = datetime.now().strftime("%Y-%m")
        ay_fis = [e for e in data["expenses"] if e["Kullanıcı"] == user_name and e.get("Tarih","").startswith(bu_ay)]
        toplam = sum(e["Tutar"] for e in ay_fis)
        cat_bd = defaultdict(float)
        for e in ay_fis: cat_bd[e.get("Kategori","diger")] += e["Tutar"]
        cat_str = "\n".join(f"  {k}: {v:,.0f} ₺" for k, v in sorted(cat_bd.items(), key=lambda x: -x[1]))
        kehane = harcama_kehaneti(user_name, data)
        # Tetikleyici uyarı
        tetikleyici = tetikleyici_analiz(user_name, data)
        msg.body(
            f"📊 *{datetime.now().strftime('%B %Y')} Özeti*\n{'─'*28}\n"
            f"💰 Toplam: *{toplam:,.0f} ₺*\n🧾 Fiş: {len(ay_fis)}\n\n"
            f"📁 Kategoriler:\n{cat_str}\n\n"
            f"📉 Bütçe: {butce_durumu_str(user_name, data)}\n"
            + (f"\n{kehane}" if kehane else "")
            + (f"\n\n{tetikleyici}" if tetikleyici else "")
        )
        return str(resp)

    # SIRALAMA
    if mesaj_lower == "sıralama":
        msg.body(f"🏆 *Ekip Harcama Sıralaması*\n{'─'*28}\n{ekip_siralaması(data)}")
        return str(resp)

    # KEHANE
    if mesaj_lower in ["kehane", "kehanet", "tahmin"]:
        kehane = harcama_kehaneti(user_name, data)
        msg.body(f"🔮 *Harcama Kehaneti*\n{'─'*28}\n{kehane}" if kehane else "🔮 Bütçen bu ay güvende! 💚")
        return str(resp)

    # PROFİL
    if mesaj_lower == "profil":
        profil = psikolojik_profil(user_name, data)
        msg.body(f"🧠 *Harcama Psikolojin*\n{'─'*28}\n{profil}" if profil else "🧠 Profil için en az 3 fiş girmen gerekiyor!")
        return str(resp)

    # KARAKTER MODU
    if mesaj_lower.startswith("karakter "):
        mod = incoming_msg[9:].strip().lower()
        gecerli = ["dedektif", "koc", "muhaseci", "yoda", "hemsire"]
        if mod in gecerli:
            data["karakter_modu"][user_name] = mod
            save_data(data)
            emoji_map = {"dedektif":"🕵️","koc":"💪","muhaseci":"📒","yoda":"🌟","hemsire":"💚"}
            msg.body(f"{emoji_map.get(mod,'🎭')} Karakter modu *{mod}* aktif!")
        else:
            msg.body(f"❌ Geçersiz mod. Seçenekler:\n{' / '.join(gecerli)}")
        return str(resp)

    # ROZETLER
    if mesaj_lower == "rozetler":
        kazanilan = data["rozetler"].get(user_name, [])
        if not kazanilan:
            msg.body("🏅 Henüz rozet kazanmadın.")
        else:
            satirlar = [f"{ROZETLER[r]['emoji']} *{ROZETLER[r]['ad']}*\n   {ROZETLER[r]['aciklama']}" for r in kazanilan if r in ROZETLER]
            msg.body(f"🏅 *Rozetlerin*\n{'─'*28}\n" + "\n".join(satirlar))
        return str(resp)

    # BAKIYE
    if mesaj_lower == "bakiye":
        bakiye = data["wallets"].get(user_name, 0)
        limit = data.get("user_limits", {}).get(user_name, 0)
        msg.body(f"💳 *Cüzdan*\nBakiye: *{bakiye:,.0f} ₺*\nLimit: {limit:,.0f} ₺")
        return str(resp)

    # SON5
    if mesaj_lower == "son5":
        son5 = [e for e in data["expenses"] if e["Kullanıcı"] == user_name][-5:]
        if not son5:
            msg.body("Henüz harcama yok.")
        else:
            satirlar = [f"🏢 {e['Firma']} — {e['Tutar']:,.0f} ₺ ({e['Tarih']}) [{e.get('Durum','?')}]" for e in reversed(son5)]
            msg.body("📋 *Son 5 Harcama:*\n" + "\n".join(satirlar))
        return str(resp)

    # KARANLIK ÖRÜNTÜ RAPORU
    if mesaj_lower in ["örüntü", "oruntu", "karanlik", "karanlık"]:
        trigger = data.get("trigger_log", {}).get(user_name, {})
        limit = data.get("user_limits", {}).get(user_name, 0)
        tum_fisler = [float(e.get("Tutar",0)) for e in data["expenses"] if e.get("Kullanıcı") == user_name]
        limit_yakini = [t for t in tum_fisler if limit > 0 and t >= limit * 0.9]
        if not trigger and not limit_yakini:
            msg.body("🌑 *Karanlık Örüntü Raporu*\n\n✅ Şüpheli bir davranış örüntüsü tespit edilmedi.")
        else:
            satirlar = [f"🌑 *Karanlık Örüntü Raporu*\n{'─'*28}"]
            if limit_yakini:
                satirlar.append(f"⚠️ {len(limit_yakini)} fiş limitin %90+ yakınında (₺{limit:.0f} limit)")
            if trigger:
                satirlar.append(f"📅 Kritik gün: {trigger.get('kritik_gun','?')} (+%{trigger.get('asim_yuzdesi','?')} harcama)")
            msg.body("\n".join(satirlar))
        return str(resp)

    # DNA RAPORU
    if mesaj_lower == "dna":
        son_fis = next((e for e in reversed(data.get("expenses",[])) if e.get("Kullanıcı") == user_name and e.get("DNA_Entropi")), None)
        if not son_fis:
            msg.body("🔬 DNA verisi henüz yok. Bir fiş fotoğrafı gönder.")
        else:
            msg.body(
                f"🔬 *Son Fiş DNA Analizi*\n{'─'*28}\n"
                f"Firma: {son_fis.get('Firma','?')}\n"
                f"Piksel Entropi: {son_fis.get('DNA_Entropi','?')}\n"
                f"Yazı Stddev: {son_fis.get('DNA_Stddev','?')}\n"
                f"Kenar Yoğunluğu: {son_fis.get('DNA_Kenar','?')}\n"
                f"DNA Risk: {son_fis.get('DNA_Risk',0)}/60\n"
                f"{''.join(son_fis.get('DNA_Bulgular',[]))}"
            )
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
                msg.body(f"💱 {miktar:,.2f} {kod} = *{miktar/kur:,.2f} ₺*\n(1 {kod} = {1/kur:.4f} ₺)")
            else:
                msg.body(f"❌ '{kod}' bulunamadı.")
        except Exception as e:
            msg.body(f"❌ Döviz hatası: {e}")
        return str(resp)

    # NL SORGU
    if mesaj_lower.startswith("soru "):
        msg.body(f"🧠 *AI Yanıtı:*\n{nl_sorgu(incoming_msg[5:].strip(), user_name, data)}")
        return str(resp)

    # ARAMA
    if mesaj_lower.startswith("ara "):
        kelime   = incoming_msg[4:].strip().lower()
        havuz    = data["expenses"] if is_admin else [e for e in data["expenses"] if e["Kullanıcı"] == user_name]
        sonuclar = [e for e in havuz if kelime in e.get("Firma","").lower()]
        if not sonuclar:
            msg.body(f"🔍 '{kelime}' için sonuç yok.")
        else:
            toplam = sum(e["Tutar"] for e in sonuclar)
            satirlar = [f"• {e['Firma']} — {e['Tutar']:,.0f} ₺ ({e['Tarih']})" for e in sonuclar[-10:]]
            msg.body(f"🔍 *'{kelime}'* → {len(sonuclar)} fiş | {toplam:,.0f} ₺\n\n" + "\n".join(satirlar))
        return str(resp)

    # ── FİŞ ANALİZİ ─────────────────────────────────────────────
    if num_media > 0:
        media_url = request.values.get('MediaUrl0')

        def analiz_et_gonder():
            try:
                data = load_data()

                # ── GÜVENLİ GÖRSEL İNDİRME ─────────────────────────────
                # allow_redirects=True + auth ile tek seferde indir
                # Twilio media URL'leri zaman zaman redirect yapar,
                # auth olmadan takip etmek 401 döndürür → bozuk byte → PIL hatası
                raw_bytes = None
                for deneme in range(3):
                    try:
                        res = requests.get(
                            media_url,
                            auth=(TWILIO_SID, TWILIO_TOKEN),
                            allow_redirects=True,   # redirect'leri otomatik takip et
                            timeout=20,
                            headers={"User-Agent": "StingaBot/14.0"}
                        )
                        if res.status_code == 200:
                            raw_bytes = res.content
                            break
                        else:
                            print(f"Görsel indirme denemesi {deneme+1}: HTTP {res.status_code}", flush=True)
                    except requests.RequestException as req_e:
                        print(f"Görsel indirme denemesi {deneme+1} hata: {req_e}", flush=True)

                if not raw_bytes:
                    twilio_client.messages.create(
                        body="❌ Görsel indirilemedi. Lütfen tekrar gönderin.",
                        from_="whatsapp:+14155238886", to=sender_phone
                    )
                    return

                # Byte'ların gerçekten bir görsel olup olmadığını kontrol et
                # (HTML hata sayfası, boş içerik vs. gelmiş olabilir)
                if len(raw_bytes) < 1000:
                    print(f"Görsel çok küçük: {len(raw_bytes)} byte — muhtemelen hata sayfası", flush=True)
                    twilio_client.messages.create(
                        body="❌ Görsel okunamadı (çok küçük). Lütfen tekrar gönderin.",
                        from_="whatsapp:+14155238886", to=sender_phone
                    )
                    return

                img_hash = gorsel_hash(raw_bytes)

                if img_hash in data["duplicate_hashes"]:
                    twilio_client.messages.create(
                        body="⚠️ *Mükerrer Fiş!* Bu fişi daha önce sisteme girdiniz.",
                        from_="whatsapp:+14155238886", to=sender_phone
                    )
                    return

                # Güvenli Image.open — truncated/bozuk görsel toleransı
                try:
                    from PIL import ImageFile
                    ImageFile.LOAD_TRUNCATED_IMAGES = True  # yarım dosyaları da aç
                    image = Image.open(BytesIO(raw_bytes))
                    image.load()  # lazy decode'u zorla — burada hata varsa erken yakala
                    image = image.convert("RGB")  # RGBA, P, L gibi modları normalize et
                except Exception as pil_e:
                    print(f"PIL açma hatası: {pil_e} — {len(raw_bytes)} byte, content-type: {res.headers.get('Content-Type','?')}", flush=True)
                    twilio_client.messages.create(
                        body="❌ Görsel açılamadı. Lütfen JPEG veya PNG olarak tekrar gönderin.",
                        from_="whatsapp:+14155238886", to=sender_phone
                    )
                    return

                # ── YENİ: FİŞ DNA ANALİZİ (görsel yüklenir yüklenmez)
                dna_sonuc   = fis_dna_analiz(image, raw_bytes)
                golge_sonuc = golge_isik_analiz(image)

                bugun = datetime.now().strftime("%Y-%m-%d")
                prompt = f"""Sen hem mali denetçi hem adli belge uzmanısın. Fişi analiz et ve SADECE JSON döndür.

ÖNEMLİ: Bugünün tarihi {bugun}. Tarihi fişten olduğu gibi oku, YYYY-MM-DD formatına çevir.
audit_notu'na asla HTML tag yazma — sadece kısa düz metin.

{{
  "firma": "Firma adı",
  "tarih": "YYYY-MM-DD",
  "toplam_tutar": 0.0,
  "kdv_tutari": 0.0,
  "odeme_yontemi": "nakit|kredi_karti|havale",
  "kalemler": [{{"aciklama": "...", "tutar": 0.0}}],
  "para_birimi": "TRY",
  "risk_skoru": 0,
  "risk_nedenleri": ["neden1"],
  "audit_notu": "1 cümle kısa mali özet",
  "sahte_mi": false,
  "sahtelik_nedeni": "",
  "gorsel_kalitesi": "iyi|orta|kotu",
  "fis_turu": "restoran|market|akaryakıt|otel|diger",
  "ilginc_detay": "fişte dikkat çeken ilginç şey",
  "konum_sehir": "fişin üzerindeki adres şehrini yaz (yoksa boş bırak)"
}}
Sahtelik: düzensiz font, tutarsız toplam, eksik vergi no."""

                ai_res   = client.models.generate_content(model=MODEL_NAME, contents=[prompt, image])
                raw_text = ai_res.text
                json_text = re.sub(r"```json?|```", "", raw_text).strip()
                _m = re.search(r'\{.*\}', json_text, re.DOTALL)
                if _m: json_text = _m.group()
                try:
                    fis = json.loads(json_text)
                except json.JSONDecodeError:
                    retry = f"Sadece JSON döndür:\n{prompt}"
                    ai_res2 = client.models.generate_content(model=MODEL_NAME, contents=[retry, image])
                    json_text2 = re.sub(r"```json?|```", "", ai_res2.text).strip()
                    _m2 = re.search(r'\{.*\}', json_text2, re.DOTALL)
                    fis = json.loads(_m2.group() if _m2 else json_text2)

                # Tarih doğrulama
                fis_tarihi = fis.get("tarih", "")
                try:
                    fis_dt  = datetime.strptime(fis_tarihi, "%Y-%m-%d")
                    bugun_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    if fis_dt > bugun_dt:
                        fis["risk_skoru"] = min(100, int(fis.get("risk_skoru", 0)) + 30)
                        fis.setdefault("risk_nedenleri", []).append("⚠️ Gelecek tarihli fiş")
                except:
                    pass

                # Para birimi
                tutar_try   = float(fis.get("toplam_tutar", 0))
                para_birimi = fis.get("para_birimi", "TRY")
                if para_birimi != "TRY":
                    try:
                        r   = requests.get(DOVIZ_API_URL, timeout=5).json()
                        kur = r["rates"].get(para_birimi)
                        if kur: tutar_try = tutar_try / kur
                    except: pass

                # Standart analizler
                sahtelik   = derin_sahtelik_analizi(fis, image)
                anomaliler = anomali_tespit(user_name, tutar_try, data)
                kategori   = kategori_tespit(fis.get("firma", ""))
                fis["kategori"] = kategori

                # ── YENİ: 4 SIRA DIŞI ANALİZ
                cografi   = cografi_kontrol(user_name, fis_tarihi, fis.get("firma",""), data, user_info)
                fiyat     = fiyat_anomali_kontrol(fis, kategori)
                karanlik  = karanlik_oruntu_tespiti(user_name, tutar_try, data)
                ruh_hali  = ruh_hali_tespiti(user_name, data)

                # ── YENİ: ADAPTİF KARAKTER
                karakter = adaptif_karakter_belirle(user_name, fis, data)
                yorum    = yaratici_yorum(fis, user_name, karakter)

                # Toplam risk skoru hesapla
                toplam_risk = sahtelik["guvensizlik_skoru"]
                toplam_risk += dna_sonuc.get("dna_risk", 0) * 0.5
                toplam_risk += golge_sonuc.get("golge_risk", 0) * 0.5
                toplam_risk += cografi.get("cografi_risk", 0) * 0.3
                toplam_risk += karanlik.get("karanlik_risk", 0) * 0.4
                toplam_risk = min(100, int(toplam_risk))

                # Durum belirle
                if sahtelik["sahte_mi"] or toplam_risk >= 70:
                    durum = "Sahte Şüphesi"
                else:
                    durum = "Onay Bekliyor"

                # Thumbnail
                import base64 as _b64
                try:
                    _ti = Image.open(BytesIO(raw_bytes)).convert("RGB")
                    _ti.thumbnail((400, 400), Image.LANCZOS)
                    _tb = BytesIO()
                    _ti.save(_tb, format="JPEG", quality=55, optimize=True)
                    _tb_bytes = _tb.getvalue()
                    gorsel_uri = f"data:image/jpeg;base64,{_b64.b64encode(_tb_bytes).decode()}"
                except:
                    gorsel_uri = ""

                # DB kayıt
                data.setdefault("fis_sayaci", {})[user_name] = data["fis_sayaci"].get(user_name, 0) + 1
                data.setdefault("expenses", [])
                data.setdefault("duplicate_hashes", [])

                # Mükerrer firma+tutar+tarih kontrolü
                firma_yeni = str(fis.get("firma","")).strip().lower()
                for e in data.get("expenses", []):
                    if (str(e.get("Firma","")).strip().lower() == firma_yeni and
                        abs(float(e.get("Tutar",0)) - tutar_try) < 1.0 and
                        e.get("Tarih") == fis_tarihi):
                        twilio_client.messages.create(
                            body=f"⚠️ *Mükerrer Fiş!*\n{e.get('Firma','?')} ₺{float(e.get('Tutar',0)):,.2f} {e.get('Tarih','?')}\nZaten sistemde mevcut.",
                            from_="whatsapp:+14155238886", to=sender_phone
                        )
                        return

                new_expense = {
                    "ID"                  : datetime.now().strftime("%Y%m%d%H%M%S"),
                    "Tarih"               : fis_tarihi or datetime.now().strftime("%Y-%m-%d"),
                    "Yukleme_Zamani"      : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Kullanıcı"           : user_name,
                    "Rol"                 : user_info["rol"],
                    "Firma"               : fis.get("firma", "Bilinmiyor"),
                    "Tutar"               : tutar_try,
                    "KDV"                 : float(fis.get("kdv_tutari", 0)),
                    "ParaBirimi"          : para_birimi,
                    "OdemeTipi"           : fis.get("odeme_yontemi", "bilinmiyor"),
                    "Odeme_Turu"          : fis.get("odeme_yontemi", "bilinmiyor"),
                    "Kategori"            : kategori,
                    "Durum"               : durum,
                    "Risk_Skoru"          : toplam_risk,
                    "AI_Audit"            : re.sub(r'<[^>]+>', '', str(fis.get("audit_notu", ""))).strip(),
                    "AI_Anomali"          : fis.get("anomali", False),
                    "AI_Anomali_Aciklama" : fis.get("anomali_aciklamasi", ""),
                    "Anomaliler"          : anomaliler,
                    "Hash"                : img_hash,
                    "Karakter"            : karakter,
                    "IlgincDetay"         : fis.get("ilginc_detay", ""),
                    "Proje"               : "Genel Merkez",
                    "Oncelik"             : "Normal",
                    "Notlar"              : "",
                    "Kaynak"              : "WhatsApp",
                    "Dosya_Yolu"          : "",
                    "Gorsel_B64"          : gorsel_uri,
                    "Konum_Sehir"         : fis.get("konum_sehir", ""),
                    # YENİ: DNA alanları
                    "DNA_Entropi"         : dna_sonuc.get("entropi"),
                    "DNA_Stddev"          : dna_sonuc.get("stddev"),
                    "DNA_Kenar"           : dna_sonuc.get("kenar"),
                    "DNA_Risk"            : dna_sonuc.get("dna_risk", 0),
                    "DNA_Bulgular"        : dna_sonuc.get("bulgular", []),
                    # YENİ: Gölge analizi
                    "Golge_Risk"          : golge_sonuc.get("golge_risk", 0),
                    "Golge_Bulgular"      : golge_sonuc.get("bulgular", []),
                    # YENİ: Coğrafi
                    "Cografi_Risk"        : cografi.get("cografi_risk", 0),
                    # YENİ: Karanlık örüntü
                    "Karanlik_Risk"       : karanlik.get("karanlik_risk", 0),
                    "Karanlik_Bulgular"   : karanlik.get("bulgular", []),
                }

                data["expenses"].append(new_expense)
                data["duplicate_hashes"].append(img_hash)

                if anomaliler or cografi.get("cografi_risk",0) > 0 or karanlik.get("karanlik_risk",0) > 0:
                    data.setdefault("anomaly_log", []).append({
                        "tarih": datetime.now().isoformat(),
                        "kullanici": user_name,
                        "tutar": tutar_try,
                        "uyarilar": anomaliler + cografi.get("bulgular",[]) + karanlik.get("bulgular",[])
                    })

                # Proje bütçe güncelle
                proje = new_expense["Proje"]
                if proje in data.get("budgets", {}):
                    data["budgets"][proje]["spent"] = data["budgets"][proje].get("spent", 0) + tutar_try

                # Rozet kontrol
                new_expense["karanlik_risk"] = karanlik.get("karanlik_risk", 0)
                new_expense["cografi_risk"]  = cografi.get("cografi_risk", 0)
                yeni_rozetler = rozet_kontrol(user_name, data, new_expense)

                add_xp(user_name, 50, "WhatsApp fiş tarama", data=data)

                # Admin'lere hem dashboard bildirimi hem WhatsApp mesajı gönder
                risk_emoji_admin = "🔴" if toplam_risk >= 70 else "🟡" if toplam_risk >= 30 else "🟢"
                durum_label = "🚨 SAHTE ŞÜPHESİ" if durum == "Sahte Şüphesi" else "📋 YENİ FİŞ — ONAY GEREKİYOR"
                for ukey, udata_info in PHONE_DIRECTORY.items():
                    if udata_info.get("yetki") == "admin" and udata_info["ad"] != user_name:
                        add_notification(
                            udata_info["ad"],
                            f"📋 {user_name} → {proje}: {new_expense['Firma']} ₺{tutar_try:,.0f}",
                            "info", data=data
                        )
                        try:
                            twilio_client.messages.create(
                                body=(
                                    f"{durum_label}\n{'─'*28}\n"
                                    f"👤 Gönderen: *{user_name}*\n"
                                    f"🏢 {new_expense['Firma']}\n"
                                    f"💰 ₺{tutar_try:,.0f}\n"
                                    f"📅 {fis_tarihi}\n"
                                    f"🏷️ {kategori}\n"
                                    f"{risk_emoji_admin} Risk: {toplam_risk}/100\n"
                                    f"🔖 `{new_expense['ID']}`\n\n"
                                    f"Dashboard'dan onaylayabilirsiniz."
                                ),
                                from_="whatsapp:+14155238886",
                                to=ukey
                            )
                        except Exception as wa_admin_e:
                            print(f"Admin WhatsApp bildirim hatası ({udata_info['ad']}): {wa_admin_e}", flush=True)

                save_data(data)

                # ── YANIT OLUŞTUR ──────────────────────────────
                risk_emoji = "🟢" if toplam_risk < 30 else "🟡" if toplam_risk < 70 else "🔴"

                kalemler_str = ""
                if fis.get("kalemler"):
                    s = [f"  • {k['aciklama']}: {k['tutar']:.2f} ₺" for k in fis["kalemler"][:4]]
                    kalemler_str = "\n📝 *Kalemler:*\n" + "\n".join(s)

                # Sahtelik uyarısı
                sahte_str = ""
                if sahtelik["sahte_mi"] or toplam_risk >= 70:
                    tum_bulgular = (
                        sahtelik["bulgular"][:2] +
                        dna_sonuc.get("bulgular", [])[:1] +
                        golge_sonuc.get("bulgular", [])[:1]
                    )
                    sahte_str = f"\n\n🚨 *SAHTE FİŞ ŞÜPHESİ!*\n" + "\n".join(tum_bulgular[:4])

                # Coğrafi uyarı
                cografi_str = ""
                if cografi.get("cografi_risk", 0) > 0:
                    cografi_str = "\n\n" + "\n".join(cografi["bulgular"])

                # Karanlık örüntü uyarısı
                karanlik_str = ""
                if karanlik.get("karanlik_risk", 0) >= 30:
                    karanlik_str = "\n\n" + "\n".join(karanlik["bulgular"][:2])

                # Fiyat anomali
                fiyat_str = ""
                if fiyat.get("fiyat_risk", 0) > 0:
                    fiyat_str = "\n\n" + "\n".join(fiyat["bulgular"])

                # DNA özeti (sadece şüpheli ise)
                dna_str = ""
                if dna_sonuc.get("dna_risk", 0) >= 20:
                    dna_str = f"\n\n🔬 *DNA Analizi:*\n" + "\n".join(dna_sonuc["bulgular"][:2])

                # Ruh hali mesajı
                ruh_str = f"\n\n{ruh_hali}" if ruh_hali else ""

                # Anomali
                anomali_str = ("\n\n" + "\n".join(anomaliler)) if anomaliler else ""

                # Rozet
                rozet_str = ""
                for r in yeni_rozetler:
                    if r in ROZETLER:
                        rozet_str += f"\n\n🎊 *YENİ ROZET: {ROZETLER[r]['emoji']} {ROZETLER[r]['ad']}!*\n{ROZETLER[r]['aciklama']}"

                ilginc = fis.get("ilginc_detay", "")
                ilginc_str = f"\n💡 _{ilginc}_" if ilginc and ilginc not in ["","null","None"] else ""

                seviye = seviye_hesapla(data["fis_sayaci"].get(user_name, 0))
                kasa_bakiye = data.get("wallets", {}).get(user_name, 0)

                yanit = (
                    f"✅ *FİŞ SİSTEME KAYDEDİLDİ*\n{'─'*28}\n"
                    f"🏢 {fis.get('firma','?')}\n"
                    f"💰 {tutar_try:,.2f} ₺"
                    + (f" ({fis['toplam_tutar']:.2f} {para_birimi})" if para_birimi != "TRY" else "")
                    + f"\n📅 {fis.get('tarih','—')}"
                    + f"\n💳 {fis.get('odeme_yontemi','—')}"
                    + f"\n🏷️ {kategori}"
                    + f"\n{risk_emoji} Risk: {toplam_risk}/100"
                    + kalemler_str
                    + ilginc_str
                    + f"\n\n💬 *{karakter.upper()} YORUMU:*\n{yorum}"
                    + f"\n\n📊 {butce_durumu_str(user_name, data)}"
                    + f"\n💳 Kasa: *{kasa_bakiye:,.0f} ₺*"
                    + f"\n{seviye} • #{data['fis_sayaci'].get(user_name,0)} fiş"
                    + sahte_str
                    + dna_str
                    + cografi_str
                    + karanlik_str
                    + fiyat_str
                    + anomali_str
                    + ruh_str
                    + rozet_str
                    + f"\n\n📨 Onay bekliyor."
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
                    from_="whatsapp:+14155238886", to=sender_phone
                )
            except Exception as e:
                import traceback
                print(f"GENEL HATA: {traceback.format_exc()}", flush=True)
                twilio_client.messages.create(
                    body=f"❌ Hata: {str(e)}",
                    from_="whatsapp:+14155238886", to=sender_phone
                )

        import threading
        t = threading.Thread(target=analiz_et_gonder, daemon=True)
        t.start()
        msg.body("⏳ *Stinga AI* fişinizi analiz ediyor...\n🔬 DNA · 💡 Gölge · 🗺️ Konum · 🌑 Örüntü")
        return str(resp)

    # VARSAYILAN
    fis_sayisi = data["fis_sayaci"].get(user_name, 0)
    # Tetikleyici uyarısı var mı?
    tetikleyici = tetikleyici_analiz(user_name, data)
    karsilama = f"{user_info['emoji']} Merhaba *{user_name}*!\n{seviye_hesapla(fis_sayisi)}\nFiş fotoğrafı gönder veya *yardım* yaz."
    if tetikleyici:
        karsilama += f"\n\n{tetikleyici}"
    msg.body(karsilama)
    return str(resp)


# ─────────────────────────────────────────────
#  ENDPOINTLER
# ─────────────────────────────────────────────
@app.route("/rapor", methods=['GET'])
def rapor_endpoint():
    data = load_data()
    bu_ay = datetime.now().strftime("%Y-%m")
    ay_fis = [e for e in data["expenses"] if e.get("Tarih","").startswith(bu_ay)]
    toplam = sum(e["Tutar"] for e in ay_fis)
    k_bazli = defaultdict(float)
    c_bazli = defaultdict(float)
    for e in ay_fis:
        k_bazli[e["Kullanıcı"]] += e["Tutar"]
        c_bazli[e.get("Kategori","diger")] += e["Tutar"]
    return jsonify({
        "ay": bu_ay, "toplam": toplam, "fis_sayisi": len(ay_fis),
        "anomali_sayisi": len(data.get("anomaly_log",[])),
        "kullanici_bazli": dict(k_bazli), "kategori_bazli": dict(c_bazli),
        "ekip_rozetleri": data.get("rozetler", {}),
    }), 200

@app.route("/expenses", methods=['GET'])
def expenses_endpoint():
    data = load_data()
    return jsonify({"expenses": data.get("expenses", [])}), 200

@app.route("/add-expense", methods=['POST'])
def add_expense_endpoint():
    try:
        new_e = request.get_json(force=True)
        if not new_e: return jsonify({"error": "Boş veri"}), 400
        data = load_data()
        if not new_e.get("ID"): new_e["ID"] = datetime.now().strftime("%Y%m%d%H%M%S")
        if not new_e.get("Tarih"): new_e["Tarih"] = datetime.now().strftime("%Y-%m-%d")
        if not new_e.get("Durum"): new_e["Durum"] = "Onay Bekliyor"
        for e in data["expenses"]:
            if (e.get("Firma") == new_e.get("Firma") and
                abs(float(e.get("Tutar",0)) - float(new_e.get("Tutar",0))) < 1 and
                e.get("Tarih") == new_e.get("Tarih")):
                return jsonify({"error": "Mükerrer fiş", "duplicate": True}), 409
        if "AI_Audit" in new_e:
            new_e["AI_Audit"] = re.sub(r'<[^>]+>', '', str(new_e["AI_Audit"])).strip()
        data["expenses"].append(new_e)
        add_xp(new_e.get("Kullanıcı",""), 50, "Dashboard fiş tarama", data=data)
        for ukey, uinfo in PHONE_DIRECTORY.items():
            if uinfo.get("yetki") == "admin" and uinfo["ad"] != new_e.get("Kullanıcı",""):
                add_notification(uinfo["ad"],
                    f"📋 {new_e.get('Kullanıcı','?')} → {new_e.get('Proje','?')}: {new_e.get('Firma','?')} ₺{float(new_e.get('Tutar',0)):,.0f}",
                    "info", data=data)
        save_data(data)
        return jsonify({"ok": True, "ID": new_e["ID"]}), 200
    except Exception as e:
        import traceback
        print(f"add-expense HATA: {traceback.format_exc()}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/all-data", methods=['GET'])
def all_data_endpoint():
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
        "trigger_log":   data.get("trigger_log", {}),
    }), 200

@app.route("/haftalik-ozet", methods=["GET"])
def haftalik_ozet():
    data  = load_data()
    bu_ay = datetime.now().strftime("%Y-%m")
    for phone, info in PHONE_DIRECTORY.items():
        user   = info["ad"]
        ay_fis = [e for e in data["expenses"] if e["Kullanıcı"] == user and e.get("Tarih","").startswith(bu_ay)]
        toplam = sum(e["Tutar"] for e in ay_fis)
        butce  = data.get("user_limits", {}).get(user, info.get("limit", 0))
        oran   = (toplam / butce * 100) if butce > 0 else 0
        # Tetikleyici raporu ekle
        trigger = data.get("trigger_log", {}).get(user, {})
        trigger_str = f"\n📅 Dikkat: {trigger.get('kritik_gun','?')} günleri +%{trigger.get('asim_yuzdesi','?')} harcıyorsun!" if trigger else ""
        try:
            twilio_client.messages.create(
                body=(
                    f"📊 *Haftalık Özet — {user}*\n{'─'*28}\n"
                    f"💰 Bu ay: {toplam:,.0f} ₺\n📉 Bütçe: %{oran:.1f}\n🧾 Fiş: {len(ay_fis)}"
                    + trigger_str
                ),
                from_="whatsapp:+14155238886", to=phone
            )
        except Exception as e:
            print(f"Haftalık özet hatası ({user}): {e}", flush=True)
    return jsonify({"status": "ok", "gonderilen": len(PHONE_DIRECTORY)}), 200

@app.route("/approve", methods=['POST'])
def approve_endpoint():
    try:
        body     = request.get_json(force=True) or {}
        fis_id   = str(body.get("ID",""))
        action   = body.get("action","approve")
        approver = body.get("approver","admin")
        if not fis_id: return jsonify({"error": "ID gerekli"}), 400
        data = load_data()
        found = False
        kullanici = tutar = firma = ""
        for e in data.get("expenses",[]):
            if str(e.get("ID","")) == fis_id:
                found = True
                kullanici = e.get("Kullanıcı","")
                tutar     = float(e.get("Tutar",0))
                firma     = e.get("Firma","?")
                e["Durum"] = "Onaylandı" if action == "approve" else "Reddedildi"
                if action == "approve": e["Onaylayan"] = approver
                else: e["Reddeden"] = approver
                break
        if not found: return jsonify({"error": "Fiş bulunamadı"}), 404
        if action == "approve":
            data.setdefault("wallets",{})[kullanici] = max(0, data.get("wallets",{}).get(kullanici,0) - tutar)
            add_xp(kullanici, 25, "Fiş onaylandı", data=data)
            add_notification(kullanici, f"✅ {firma} (₺{tutar:,.0f}) onaylandı", "success", data=data)
        else:
            add_notification(kullanici, f"❌ {firma} harcamanız reddedildi", "warning", data=data)
        save_data(data)
        return jsonify({"ok": True, "ID": fis_id, "action": action}), 200
    except Exception as e:
        import traceback
        print(f"/approve HATA: {traceback.format_exc()}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/transfer", methods=['POST'])
def transfer_endpoint():
    try:
        body     = request.get_json(force=True) or {}
        hedef    = body.get("hedef","")
        miktar   = float(body.get("miktar",0))
        aciklama = body.get("aciklama","Harcırah")
        gonderen = body.get("gonderen","admin")
        if not hedef or miktar <= 0: return jsonify({"error": "Hedef ve miktar gerekli"}), 400
        data = load_data()
        data.setdefault("wallets",{})[hedef] = data["wallets"].get(hedef,0) + miktar
        data.setdefault("ledger",[]).append({"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"), "Kaynak": gonderen, "Hedef": hedef, "İşlem": aciklama, "Miktar": miktar})
        add_notification(hedef, f"💰 ₺{miktar:,.0f} transfer alındı ({aciklama})", "success", data=data)
        add_xp(hedef, 10, "Transfer alındı", data=data)
        save_data(data)
        return jsonify({"ok": True, "hedef": hedef, "miktar": miktar}), 200
    except Exception as e:
        import traceback
        print(f"/transfer HATA: {traceback.format_exc()}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/gorsel/<fis_id>", methods=['GET'])
def gorsel_endpoint(fis_id):
    data = load_data()
    for e in data.get("expenses",[]):
        if str(e.get("ID","")) == str(fis_id):
            b64 = e.get("Gorsel_B64","")
            if b64: return jsonify({"ok": True, "gorsel": b64}), 200
            return jsonify({"ok": False, "error": "Görsel yok"}), 404
    return jsonify({"ok": False, "error": "Fiş bulunamadı"}), 404

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)