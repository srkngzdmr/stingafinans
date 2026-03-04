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

# ── Google Drive Persistent Storage ──
try:
    from gdrive_sync import drive_save_async, drive_load
    GDRIVE_ENABLED = True
    print("GDrive sync modülü yüklendi.", flush=True)
except ImportError:
    GDRIVE_ENABLED = False
    print("GDrive sync modülü bulunamadı — sadece lokal kayıt aktif.", flush=True)

import requests
from flask import Flask, request, jsonify
from google import genai
from PIL import Image

app = Flask(__name__)

# ── TWILIO — WhatsApp mesaj gönderici ──
def send_whatsapp(to: str, body: str) -> bool:
    """
    Twilio API ile WhatsApp mesajı gönderir.
    Gerekli env değişkenleri:
      TWILIO_ACCOUNT_SID     → Twilio Account SID
      TWILIO_AUTH_TOKEN      → Twilio Auth Token
      TWILIO_WHATSAPP_NUMBER → Gönderen numara (örn: whatsapp:+14155238886)
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token  = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

    if not account_sid or not auth_token:
        print("❌ TWILIO_ACCOUNT_SID veya TWILIO_AUTH_TOKEN eksik!", flush=True)
        return False

    # "905xxxxxxxxx" → "whatsapp:+905xxxxxxxxx"
    if not to.startswith("whatsapp:"):
        to = "whatsapp:+" + to.lstrip("+")

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    try:
        r = requests.post(url, auth=(account_sid, auth_token), data={
            "From": from_number,
            "To": to,
            "Body": body,
        }, timeout=10)
        if r.status_code in (200, 201):
            print(f"✅ Twilio WA gönderildi → {to}", flush=True)
            return True
        else:
            print(f"❌ Twilio WA hata {r.status_code}: {r.text}", flush=True)
            return False
    except Exception as e:
        print(f"❌ Twilio WA exception: {e}", flush=True)
        return False

# ── STARTUP: DB_JSON env var'dan geri yükle (Railway restart sonrası) ──
def _startup_restore():
    db_b64 = os.environ.get("DB_JSON_B64", "")
    if not db_b64:
        return
    if os.path.exists(DB_FILE) and os.path.getsize(DB_FILE) > 100:
        print("DB zaten mevcut, env restore atlandı.", flush=True)
        return
    try:
        import base64
        raw = base64.b64decode(db_b64).decode("utf-8")
        data = json.loads(raw)
        if "expenses" in data:
            save_data(data)
            print(f"DB env var'dan restore edildi: {len(data.get('expenses',[]))} fiş", flush=True)
    except Exception as e:
        print(f"DB restore hatası: {e}", flush=True)

# _startup_restore() aşağıda DB_FILE tanımlandıktan sonra çağrılacak

# ─────────────────────────────────────────────
#  YAPILANDIRMA
# ─────────────────────────────────────────────
client     = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-2.5-flash"

# Debug: Meta credential kontrolü
_META_PID   = os.getenv("META_PHONE_NUMBER_ID", "")
_META_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
print(f"META_PHONE_NUMBER_ID: {'SET (' + _META_PID[:6] + '...)' if _META_PID else 'YOK!'}", flush=True)
print(f"META_ACCESS_TOKEN: {'SET (' + str(len(_META_TOKEN)) + ' chars)' if _META_TOKEN else 'YOK!'}", flush=True)

def _find_writable_dir():
    candidates = [
        os.environ.get("DATA_DIR", ""),
        "/data", "/var/data", "/tmp",
        os.path.dirname(os.path.abspath(__file__)),
    ]
    for d in candidates:
        if not d: continue
        try:
            os.makedirs(d, exist_ok=True)
            test_file = os.path.join(d, ".write_test")
            with open(test_file, "w") as f: f.write("test")
            os.remove(test_file)
            print(f"DB dizini: {d}", flush=True)
            return d
        except Exception as e:
            print(f"Dizin yazılamıyor ({d}): {e}", flush=True)
            continue
    return "/tmp"

_DATA_DIR = _find_writable_dir()
DB_FILE   = os.path.join(_DATA_DIR, "stinga_v13_db.json")
DB_FILE_BACKUP2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stinga_v13_db.json")
print(f"Ana DB: {DB_FILE}", flush=True)
DOVIZ_API_URL = "https://api.exchangerate-api.com/v4/latest/TRY"

# ── Startup restore'u DB_FILE tanımlandıktan sonra çağır
_startup_restore()

PHONE_DIRECTORY = {
    "whatsapp:+905350328406": {
        "ad": "Okan İlhan",   "rol": "Saha Personeli",         "limit": 20000,
        "emoji": "🔧",  "yetki": "user",  "dashboard_key": "okan"
    },
    "whatsapp:+905322002337": {
        "ad": "Serkan Güzdemir", "rol": "İşletme Müdürü",      "limit": 50000,
        "emoji": "⚡",  "yetki": "admin", "dashboard_key": "serkan"
    },
    "whatsapp:+905447858627": {
        "ad": "Zeynep Özyaman", "rol": "Yönetim Kurulu Başkanı", "limit": 100000,
        "emoji": "👑",  "yetki": "admin", "dashboard_key": "zeynep"
    },
    "whatsapp:+905304305213": {
        "ad": "Şenol Özyaman", "rol": "Genel Müdür", "limit": 80000,
        "emoji": "🏢",  "yetki": "user", "dashboard_key": "senol",
        "dashboard_rol": "user", "dashboard_sifre": "456"
    },
}


# ─────────────────────────────────────────────
#  ÖDEME TÜRÜ TESPİTİ (WhatsApp mesajından)
# ─────────────────────────────────────────────
def detect_odeme_turu(message_text: str) -> str:
    """
    WhatsApp mesaj metninden ödeme türünü tespit eder.
    'harcırah/harcirah/HARCIRAH' → 'harcirah' (personel kasasından düşülür)
    'şirket/sirket/ŞİRKET/SİRKET' → 'sirket_karti' (genel merkezden düşülür)
    Hiçbiri yoksa → None
    """
    if not message_text:
        return None
    txt = str(message_text).lower().strip()
    txt_n = txt.replace("ı","i").replace("ş","s").replace("ğ","g").replace("ç","c").replace("ö","o").replace("ü","u")
    for kw in ["harcırah","harcirah","harcırahtan","harcirahtan"]:
        kw_n = kw.replace("ı","i").replace("ş","s")
        if kw in txt or kw_n in txt_n:
            return "harcirah"
    for kw in ["şirket","sirket","şirket kartı","sirket karti"]:
        kw_n = kw.replace("ş","s").replace("ı","i")
        if kw in txt or kw_n in txt_n:
            return "sirket_karti"
    return None

def odeme_turu_label(raw: str) -> str:
    v = str(raw).lower().strip()
    if v in ("sirket_karti","sirket karti","kredi_karti","kredi kartı","şirket","sirket"):
        return "🏦 Şirket Kredi Kartı"
    elif v in ("harcirah","harcırah","harcirahtan dus","harcırahtan düş","nakit","kisisel",
               "harcırahtan düş (nakit / kişisel kart)"):
        return "💵 Harcırah / Nakit"
    elif v:
        return raw
    return "—"


# ─────────────────────────────────────────────
#  STATE TANIMLAMALARI
# ─────────────────────────────────────────────
AI_CHAT_TRIGGER  = ["sohbet", "chat", "konuş", "konuşalım", "ai modu"]
AI_CHAT_EXIT     = ["çıkış", "exit", "kapat", "bitti", "dur"]
KONUM_BEKLE_FLAG = "konum_bekle"
AI_CHAT_FLAG     = "ai_chat"
AI_CHAT_HISTORY  = "ai_history"
ODEME_BEKLE_FLAG = "odeme_bekle"
ODEME_BEKLE_DATA = "odeme_data"

KATEGORILER = {
    "yemek":     ["restoran", "kafe", "lokanta", "manav", "kasap", "ekmek", "cafe", "burger", "pizza", "döner",
                  "köfte", "balık", "kebap", "lahmacun", "pide", "çorba", "yemek", "mutfak", "bistro", "steak"],
    "ulasim":    ["akaryakıt", "benzin", "motorin", "otopark", "taksi", "uber", "servis", "shell", "bp", "opet",
                  "petrol", "total", "enerji akaryakıt", "lukoil", "po ", "aytemiz", "turkuaz", "alpet",
                  "gas ", "yakıt", "mazot", "istasyon", "tüpraş", "moil"],
    "ofis":      ["kırtasiye", "toner", "bilgisayar", "telefon", "ekipman", "teknosa", "mediamarkt"],
    "konaklama": ["otel", "apart", "hostel", "hilton", "marriott", "pansiyon", "konaklama", "hotel"],
    "eglence":   ["sinema", "konser", "etkinlik", "cinemaximum"],
    "saglik":    ["eczane", "hastane", "klinik", "doktor", "ilaç"],
    "market":    ["market", "migros", "bim", "a101", "şok", "carrefour", "metro", "makro", "file"],
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
}

SEVIYELER = [
    (0,    "🥉 Toplam Yüklemelerin"),
    (5,    "🥈 Toplam Yüklemelerin"),
    (15,   "🥇 Toplam Yüklemelerin"),
    (30,   "💎 Toplam Yüklemelerin"),
    (60,   "🏆 Toplam Yüklemelerin"),
    (100,  "👑 Toplam Yüklemelerin"),
]

# ───────────────────────────────────────
#  VERİTABANI
# ───────────────────────────────────────
def load_data() -> dict:
    default = {
        "expenses": [],
        "wallets":  {"Zeynep Özyaman": 0, "Serkan Güzdemir": 0, "Okan İlhan": 0, "Şenol Özyaman": 0},
        "budgets": {
            "Maden Sahası":   {"limit": 100000, "spent": 0},
            "Aktif Karbon":   {"limit": 80000,  "spent": 0},
            "Enerji Hatları": {"limit": 60000,  "spent": 0},
            "Genel Merkez":   {"limit": 40000,  "spent": 0},
        },
        "user_limits": {"Zeynep Özyaman": 50000, "Serkan Güzdemir": 10000, "Okan İlhan": 5000, "Şenol Özyaman": 30000},
        "anomaly_log": [],
        "duplicate_hashes": [],
        "user_states": {},
        "rozetler": {"Zeynep Özyaman": [], "Serkan Güzdemir": [], "Okan İlhan": [], "Şenol Özyaman": []},
        "fis_sayaci": {"Zeynep Özyaman": 0, "Serkan Güzdemir": 0, "Okan İlhan": 0, "Şenol Özyaman": 0},
        "karakter_modu": {},
        "xp": {"Zeynep Özyaman": 0, "Serkan Güzdemir": 0, "Okan İlhan": 0, "Şenol Özyaman": 0},
        "notifications": [],
        "ledger": [],
    }
    all_candidates = []
    for f in [DB_FILE, DB_FILE + ".bak", DB_FILE_BACKUP2, DB_FILE_BACKUP2 + ".bak"]:
        if f not in all_candidates:
            all_candidates.append(f)
    for try_file in all_candidates:
        if not os.path.exists(try_file): continue
        try:
            with open(try_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in default.items():
                data.setdefault(k, v)
            for field in ["wallets", "user_limits", "rozetler", "fis_sayaci", "xp"]:
                if "Şenol Özyaman" not in data.get(field, {}):
                    data[field]["Şenol Özyaman"] = default[field].get("Şenol Özyaman", 0 if field != "rozetler" else [])
            budgets = data.get("budgets", {})
            if budgets and isinstance(list(budgets.values())[0], (int, float)):
                data["budgets"] = default["budgets"]
            print(f"DB yüklendi ({try_file}): {len(data.get('expenses',[]))} fiş", flush=True)
            return data
        except (json.JSONDecodeError, Exception) as e:
            print(f"DB okuma hatası ({try_file}): {e}", flush=True)
            continue
    print("UYARI: Geçerli DB bulunamadı, default döndürülüyor", flush=True)

    # ── Lokal DB yoksa Google Drive'dan restore et ──
    if GDRIVE_ENABLED:
        print("GDrive'dan restore deneniyor...", flush=True)
        try:
            gdata = drive_load()
            if gdata and "expenses" in gdata and len(gdata.get("expenses", [])) > 0:
                for k, v in default.items():
                    gdata.setdefault(k, v)
                save_data(gdata)  # Lokal dosyaya da kaydet
                print(f"GDrive'dan restore başarılı: {len(gdata.get('expenses',[]))} fiş", flush=True)
                return gdata
            else:
                print("GDrive'da geçerli veri bulunamadı.", flush=True)
        except Exception as e:
            print(f"GDrive restore hatası: {e}", flush=True)

    return default

import threading as _threading
_DB_LOCK = _threading.Lock()

def save_data(d: dict):
    os.makedirs(os.path.dirname(DB_FILE) or ".", exist_ok=True)
    tmp = DB_FILE + ".tmp"
    with _DB_LOCK:
        try:
            if os.path.exists(DB_FILE):
                try: os.replace(DB_FILE, DB_FILE + ".bak")
                except: pass
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
            os.replace(tmp, DB_FILE)
            print(f"DB kaydedildi: {len(d.get('expenses',[]))} fiş → {DB_FILE}", flush=True)
            if DB_FILE_BACKUP2 != DB_FILE:
                try:
                    os.makedirs(os.path.dirname(DB_FILE_BACKUP2) or ".", exist_ok=True)
                    with open(DB_FILE_BACKUP2, "w", encoding="utf-8") as _f2:
                        json.dump(d, _f2, ensure_ascii=False)
                except Exception as _e2:
                    print(f"Yedek yazılamadı: {_e2}", flush=True)
        except Exception as e:
            print(f"KAYIT HATASI: {e}", flush=True)
            try:
                with open(DB_FILE, "w", encoding="utf-8") as f:
                    json.dump(d, f, ensure_ascii=False, indent=2)
            except Exception as e2:
                print(f"FALLBACK KAYIT HATASI: {e2}", flush=True)

    # ── Google Drive'a arka planda yedekle ──
    if GDRIVE_ENABLED:
        try:
            drive_save_async(d)
        except Exception as e:
            print(f"GDrive async kayıt hatası: {e}", flush=True)

def load_data_safe() -> dict:
    with _DB_LOCK:
        for try_file in [DB_FILE, DB_FILE + ".bak"]:
            if os.path.exists(try_file):
                try:
                    with open(try_file, "r", encoding="utf-8") as f: return json.load(f)
                except json.JSONDecodeError:
                    print(f"JSON BOZUK: {try_file}", flush=True); continue
        return {}

def _deep_clean_html(text):
    """Bir metin alanından TÜM HTML kalıntılarını agresif şekilde temizle."""
    if not text or not isinstance(text, str):
        return text
    # HTML-escaped tag'leri geri çevir
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&quot;", '"')
    # <div ...>...</div> bloklarını kaldır (multi-line dahil)
    text = re.sub(r'<div[^>]*>.*?</div>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
    # Tüm HTML tag'lerini kaldır
    text = re.sub(r'<[^>]+>', '', text, flags=re.DOTALL)
    # CSS style kalıntıları
    text = re.sub(r'style\s*=\s*["\'][^"\']*["\']', '', text)
    # HTML entity temizle
    text = re.sub(r'&nbsp;?', ' ', text)
    text = re.sub(r'&[a-z]+;', ' ', text)
    # "Proje: ... Ödeme: ..." kalıntıları
    text = re.sub(r'Proje\s*:.*?Kaynak\s*:\s*\w+', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'Proje\s*:.*?Ödeme\s*:[^\n]*', '', text, flags=re.IGNORECASE)
    # "ŞİRKET KREDİ KARTI" / "HARCIRAHTAN DÜŞÜLECEK" kalıntıları
    text = re.sub(r'(ŞİRKET KREDİ KARTI|HARCIRAHTAN DÜŞÜLECEK|Genel merkezden düşülecek|Personel şahsi)[^\n]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Kaynak\s*:\s*\w+', '', text, flags=re.IGNORECASE)
    # Separator kalıntıları
    text = re.sub(r'[·•]+\s*', '', text)
    # Çoklu boşluk/newline
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def add_notification(target, message, notif_type="info", data=None):
    _own = data is None
    if _own: data = load_data()
    data.setdefault("notifications", [])
    data["notifications"].append({"user": target, "msg": message, "type": notif_type,
        "time": datetime.now().strftime("%H:%M"), "date": datetime.now().strftime("%Y-%m-%d"), "read": False})
    if _own: save_data(data)

def add_xp(user_name, amount, reason="", data=None):
    _own = data is None
    if _own: data = load_data()
    data.setdefault("xp", {})
    data["xp"][user_name] = data["xp"].get(user_name, 0) + amount
    if reason:
        data.setdefault("notifications", [])
        data["notifications"].append({"user": user_name, "msg": f"🏆 +{amount} XP kazandın! ({reason})",
            "type": "xp", "time": datetime.now().strftime("%H:%M"), "date": datetime.now().strftime("%Y-%m-%d"), "read": False})
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

def kategori_tespit(firma: str, fis_turu: str = "") -> str:
    """Firma adı + AI fis_turu ile kategori belirle. Yakıt istasyonları öncelikli."""
    f = firma.lower()
    ft = fis_turu.lower().strip() if fis_turu else ""

    # 1) AI fis_turu güvenilir bir değer verdiyse önce onu kullan
    _fis_turu_map = {
        "akaryakıt": "ulasim", "akaryakit": "ulasim", "benzin": "ulasim", "yakıt": "ulasim",
        "restoran": "yemek", "yemek": "yemek", "lokanta": "yemek", "cafe": "yemek", "kafe": "yemek",
        "otel": "konaklama", "konaklama": "konaklama", "hotel": "konaklama",
        "market": "market", "süpermarket": "market",
    }
    if ft in _fis_turu_map:
        return _fis_turu_map[ft]

    # 2) Yakıt istasyonları öncelikli kontrol (OPET market, Shell market vb. yakıttır)
    _yakit_firma = ["opet", "shell", "bp ", "total", "petrol", "akaryakıt", "lukoil",
                    "aytemiz", "turkuaz", "alpet", "po ", "tüpraş", "moil", "enerji akaryakıt"]
    if any(k in f for k in _yakit_firma):
        return "ulasim"

    # 3) Standart kategori eşleştirme
    for kat, kelimeler in KATEGORILER.items():
        if any(k in f for k in kelimeler):
            return kat
    return "diger"

def seviye_hesapla(fis_sayisi: int) -> str:
    seviye = SEVIYELER[0][1]
    for minimum, ad in SEVIYELER:
        if fis_sayisi >= minimum: seviye = ad
    return seviye

def rozet_kontrol(user_name, data, yeni_fis):
    kazanilanlar = []
    mevcut = data["rozetler"].get(user_name, [])
    fis_sayisi = data["fis_sayaci"].get(user_name, 0)
    tum_fisler = [e for e in data["expenses"] if e["Kullanıcı"] == user_name]
    def ekle(rozet_id):
        if rozet_id not in mevcut: mevcut.append(rozet_id); kazanilanlar.append(rozet_id)
    if fis_sayisi == 1: ekle("ilk_fis")
    if yeni_fis.get("Risk_Skoru", 0) >= 70: ekle("risk_avcisi")
    if yeni_fis.get("Durum") == "⚠️ Sahte Şüphesi": ekle("dedektif")
    bir_saat_once = datetime.now() - timedelta(hours=1)
    son_1h = [e for e in tum_fisler if datetime.strptime(e["Tarih"], "%Y-%m-%d") >= bir_saat_once.replace(hour=0, minute=0, second=0)]
    if len(son_1h) >= 3: ekle("hizli_giris")
    dovizler = set(e.get("ParaBirimi", "TRY") for e in tum_fisler if e.get("ParaBirimi") != "TRY")
    if len(dovizler) >= 5: ekle("dovec_kral")
    data["rozetler"][user_name] = mevcut
    return kazanilanlar

# ─────────────────────────────────────────────
#  AI FONKSİYONLARI
# ─────────────────────────────────────────────
def ai_call(prompt: str) -> str:
    resp = client.models.generate_content(model=MODEL_NAME, contents=[prompt])
    return resp.text.strip()

def psikolojik_profil(user_name, data):
    harcamalar = [e for e in data["expenses"] if e["Kullanıcı"] == user_name]
    if len(harcamalar) < 3: return ""
    prompt = f"""Sen davranışsal ekonomi uzmanısın. Harcamaları analiz et.
Harcamalar: {json.dumps(harcamalar[-30:], ensure_ascii=False)}
Kişinin harcama psikolojisini 2-3 cümleyle analiz et. Türkçe, kısa, esprili. Emoji kullan."""
    try: return ai_call(prompt)
    except: return ""

def yaratici_yorum(fis_data, user_name, karakter):
    karakter_talimatlari = {
        "dedektif": "Sen sert bir mali dedektifsin. Fişi sorguyla, şüpheyle yaklaş.",
        "koc":      "Sen motive edici bir finansal koçsun. Pozitif, cesaretlendirici konuş.",
        "muhaseci": "Sen kuru ama keskin bir muhasecsin. Rakamları önemse.",
        "yoda":     "Sen Yoda gibi konuş. Ters cümle yapısı kullan.",
        "hemsire":  "Sen şefkatli ama dürüst bir finansal terapistsin.",
    }
    talimat = karakter_talimatlari.get(karakter, karakter_talimatlari["koc"])
    prompt = f"""{talimat}
Fiş: {fis_data.get('firma','?')} - {fis_data.get('toplam_tutar',0)} TL - Risk: {fis_data.get('risk_skoru',0)}/100
Kullanıcı: {user_name}. 1-2 cümle yaratıcı yorum yap. Türkçe, emoji kullan."""
    try: return ai_call(prompt)
    except: return ""

def harcama_kehaneti(user_name, data):
    bu_ay = datetime.now().strftime("%Y-%m")
    gun = datetime.now().day
    ay_harcamalar = [e for e in data["expenses"] if e["Kullanıcı"] == user_name and e.get("Tarih","").startswith(bu_ay)]
    if not ay_harcamalar or gun == 0: return ""
    toplam = sum(e["Tutar"] for e in ay_harcamalar)
    butce = data.get("user_limits", {}).get(user_name, 0)
    if butce == 0: return ""
    gunluk_ort = toplam / gun
    kalan_gun = 30 - gun
    tahmini_bitis = toplam + (gunluk_ort * kalan_gun)
    asim_miktari = tahmini_bitis - butce
    if asim_miktari <= 0: return ""
    asim_gunu = int((butce - toplam) / gunluk_ort) if gunluk_ort > 0 else 999
    bitis_tarihi = (datetime.now() + timedelta(days=asim_gunu)).strftime("%d %B")
    prompt = f"""Sen finansal astrolog gibisin (ama veriye dayalı).
{user_name}: günlük ort {gunluk_ort:.0f} TL, bütçe {bitis_tarihi}'de biter, {asim_miktari:.0f} TL aşım.
1 cümle dramatik ama esprili. Türkçe. Emoji."""
    try: return ai_call(prompt)
    except: return f"🔮 Bu gidişle bütçen {bitis_tarihi}'de tükeniyor! ({asim_miktari:.0f} ₺ aşım)"

def derin_sahtelik_analizi(fis_data, image):
    """
    ╔══════════════════════════════════════════════════════════════╗
    ║   STINGA DERİN SAHTELİK ANALİZ MOTORU — 12 Katman          ║
    ║   Her katman bağımsız çalışır, risk skoru birikmeli artar.  ║
    ╚══════════════════════════════════════════════════════════════╝

    KATMAN 1  — Tarih Anomalisi (çok eski / gelecek / hafta sonu)
    KATMAN 2  — Para Birimi & Dönem Tutarsızlığı (YTL/TL karışımı)
    KATMAN 3  — KDV Matematik Kontrolü
    KATMAN 4  — Yuvarlak Tutar Şüphesi
    KATMAN 5  — Görsel Piksel Entropi (bitmap font tespiti)
    KATMAN 6  — Görsel Renk Homojenliği (beyaz kağıt / gri zemin)
    KATMAN 7  — Görsel Kenar Geometrisi (eğiklik / kırpılmışlık)
    KATMAN 8  — AI Sahtelik Skoru (Gemini'den gelen)
    KATMAN 9  — Metin Yapısı Anomalisi (boşluk/hizalama kalıpları)
    KATMAN 10 — Vergi Numarası Format Kontrolü
    KATMAN 11 — Fiş Sıra No / Onay Kodu Format Kontrolü
    KATMAN 12 — İşletme Adı Güvenilirlik Kontrolü
    """
    import re as _re
    import statistics as _stats

    sonuc = {
        "sahte_mi": fis_data.get("sahte_mi", False),
        "guvensizlik_skoru": int(fis_data.get("risk_skoru", 0)),
        "bulgular": [],
        "katman_sonuclari": {}
    }

    def _ekle(katman, mesaj, risk):
        sonuc["bulgular"].append(mesaj)
        sonuc["katman_sonuclari"][katman] = {"mesaj": mesaj, "risk": risk}
        sonuc["guvensizlik_skoru"] = min(100, sonuc["guvensizlik_skoru"] + risk)

    toplam  = float(fis_data.get("toplam_tutar", 0))
    kdv     = float(fis_data.get("kdv_tutari", 0))
    tarih   = str(fis_data.get("tarih", ""))
    firma   = str(fis_data.get("firma", ""))
    para    = str(fis_data.get("para_birimi", "TRY"))
    audit   = str(fis_data.get("audit_notu", ""))

    # ════════════════════════════════════════════
    # KATMAN 1 — TARİH ANOMALİSİ
    # ════════════════════════════════════════════
    try:
        fis_dt = datetime.strptime(tarih, "%Y-%m-%d")
        bugun  = datetime.now()
        yas_gun = (bugun - fis_dt).days

        if yas_gun > 365 * 3:   # 3 yıldan eski
            _ekle("K1", f"🚨 Fiş TARİHİ {fis_dt.year} yılına ait — {yas_gun // 365} yıl önce!", 40)
        elif yas_gun > 365:     # 1-3 yıl arası
            _ekle("K1", f"⚠️ Fiş tarihi {yas_gun // 365} yıl önce ({fis_dt.strftime('%d.%m.%Y')})", 25)
        elif yas_gun > 60:
            _ekle("K1", f"🔍 Fiş {yas_gun} gün öncesine ait ({fis_dt.strftime('%d.%m.%Y')})", 15)
        elif fis_dt > bugun:
            _ekle("K1", "🚨 Gelecek tarihli fiş — tarih manipülasyonu!", 35)

        # Pazar günü harcama şüphesi (bazı iş yerleri kapalı)
        if fis_dt.weekday() == 6:  # Pazar
            _ekle("K1b", "🔍 Pazar günü fişi — iş yeri açık mıydı?", 5)

        # Resmi tatil kontrolü (sabit tatiller)
        _tatiller = ["01-01","23-04","01-05","19-05","15-07","30-08","29-10"]
        ay_gun = fis_dt.strftime("%m-%d")
        if ay_gun in _tatiller:
            _ekle("K1c", f"🔍 Resmi tatil gününe ({ay_gun}) ait fiş", 8)

    except ValueError:
        _ekle("K1", "🚨 Geçersiz tarih formatı — okunamıyor", 20)

    # ════════════════════════════════════════════
    # KATMAN 2 — PARA BİRİMİ & DÖNEM TUTARSIZLIĞI
    # ════════════════════════════════════════════
    # YTL: 1 Ocak 2005 – 31 Aralık 2008 arasında kullanıldı
    _ytl_ifadeler = ["ytl", "y.t.l", "yeni türk lirası", "yeni lira"]
    _metin_birlesik = (firma + audit + str(fis_data.get("audit_notu",""))).lower()

    ytl_bulundu = any(k in _metin_birlesik for k in _ytl_ifadeler)
    if ytl_bulundu:
        try:
            fis_yil = int(tarih[:4])
            if fis_yil < 2005 or fis_yil > 2008:
                _ekle("K2", f"🚨 YTL para birimi ama fiş tarihi {fis_yil} — dönem UYUMSUZ!", 35)
            else:
                _ekle("K2", f"⚠️ YTL para birimi tespit edildi ({fis_yil}) — arşiv fişi olabilir", 20)
        except:
            _ekle("K2", "⚠️ YTL para birimi tespit edildi — eski fiş şüphesi", 20)

    # TL/₺ ama tarih 2005-2008 arası ise de şüpheli
    try:
        fis_yil2 = int(tarih[:4])
        if 2005 <= fis_yil2 <= 2008 and not ytl_bulundu and para == "TRY":
            _ekle("K2b", f"🔍 {fis_yil2} yılı fişi TL gösteriyor — o dönemde YTL kullanılıyordu", 15)
    except:
        pass

    # ════════════════════════════════════════════
    # KATMAN 3 — KDV MATEMATİK KONTROLÜ
    # ════════════════════════════════════════════
    if kdv > 0 and toplam > 0:
        oran_20 = abs(kdv - toplam * 0.20 / 1.20)
        oran_10 = abs(kdv - toplam * 0.10 / 1.10)
        oran_08 = abs(kdv - toplam * 0.08 / 1.08)
        oran_01 = abs(kdv - toplam * 0.01 / 1.01)
        min_sapma = min(oran_20, oran_10, oran_08, oran_01)
        if min_sapma > 2.0:
            _ekle("K3", f"🚨 KDV tutarı ({kdv:.2f}₺) hiçbir orana uymuyor! (Min sapma: {min_sapma:.2f}₺)", 25)
        elif min_sapma > 0.5:
            _ekle("K3", f"⚠️ KDV tutarında küçük matematiksel sapma ({min_sapma:.2f}₺)", 10)

    # ════════════════════════════════════════════
    # KATMAN 4 — YUVARLAK TUTAR ŞÜPHESİ
    # ════════════════════════════════════════════
    if toplam > 0:
        if toplam == int(toplam) and int(toplam) % 500 == 0:
            _ekle("K4", f"🚨 Çok şüpheli yuvarlak tutar: {toplam:.0f}₺ (500'ün katı)", 20)
        elif toplam == int(toplam) and int(toplam) % 100 == 0:
            _ekle("K4", f"🔍 Yuvarlak tutar: {toplam:.0f}₺ (100'ün katı)", 10)
        elif toplam == int(toplam) and int(toplam) % 50 == 0:
            _ekle("K4", f"🔍 Yuvarlak tutar: {toplam:.0f}₺ (50'nin katı)", 5)
        # Fiş türüne göre olası olmayan tutarlar
        if fis_data.get("fis_turu","") in ("akaryakıt","akaryakit") and toplam > 5000:
            _ekle("K4b", f"⚠️ Yakıt fişi için çok yüksek tutar: {toplam:.0f}₺", 15)
        if fis_data.get("fis_turu","") == "restoran" and toplam > 10000:
            _ekle("K4b", f"⚠️ Restoran fişi için çok yüksek tutar: {toplam:.0f}₺", 15)

    # ════════════════════════════════════════════
    # KATMAN 5 — GÖRSEL: PİKSEL ENTROPİ ANALİZİ
    # Gerçek termal fiş → yüksek entropi (sıcaklık gradyanı)
    # Bilgisayar çıktısı → düşük entropi (düzgün pikseller)
    # ════════════════════════════════════════════
    try:
        import numpy as _np
        img_gray = image.convert("L")  # Gri tonlama
        img_arr  = list(img_gray.tobytes())
        w, h     = img_gray.size

        # Histogram entropi hesabı
        _hist = [0] * 256
        for px in img_arr:
            _hist[px] += 1
        _total = len(img_arr)
        _entropi = 0.0
        for c in _hist:
            if c > 0:
                p = c / _total
                import math as _math
                _entropi -= p * _math.log2(p)

        sonuc["gorsel_entropi"] = round(_entropi, 3)

        # Satır bazlı varyans — gerçek termal fişte satırlar arası varyans yüksek
        satirlar = []
        for y in range(0, h, max(1, h // 20)):
            satir = img_arr[y * w: (y+1) * w]
            if satir:
                satirlar.append(sum(satir) / len(satir))

        if len(satirlar) > 3:
            satir_varyans = _stats.variance(satirlar)
            sonuc["satir_varyans"] = round(satir_varyans, 1)
            if satir_varyans < 50:
                _ekle("K5", f"🚨 Çok düşük görsel varyans ({satir_varyans:.0f}) — bilgisayar çıktısı şüphesi", 25)
            elif satir_varyans < 150:
                _ekle("K5", f"🔍 Düşük görsel varyans ({satir_varyans:.0f}) — termal yazıcı değil olabilir", 12)

        # Entropi değerlendirmesi
        if _entropi < 3.5:
            _ekle("K5b", f"🚨 Çok düşük piksel entropisi ({_entropi:.2f}) — gerçek fiş değil şüphesi", 20)
        elif _entropi < 5.0:
            _ekle("K5b", f"🔍 Düşük piksel entropisi ({_entropi:.2f}) — yazıcı kalitesi şüpheli", 8)

    except Exception as _e:
        print(f"K5 görsel analiz hatası: {_e}", flush=True)

    # ════════════════════════════════════════════
    # KATMAN 6 — GÖRSEL: RENK HOMOJENLİĞİ
    # Gerçek termal fiş → beyaza yakın, gri bantlar var
    # Taranmış sahte → çok düzgün beyaz veya çok gri
    # ════════════════════════════════════════════
    try:
        img_rgb = image.convert("RGB")
        w2, h2  = img_rgb.size
        piksel_sayisi = w2 * h2
        if piksel_sayisi > 0:
            # Ortalama renk kanalları
            r_sum = g_sum = b_sum = 0
            pikseller = list(list(img_rgb.getpixel(x, y) for y in range(h2) for x in range(w2)))
            for i in range(0, len(pikseller), 3):
                r, g, b = pikseller[i], pikseller[i+1], pikseller[i+2]
                r_sum += r; g_sum += g; b_sum += b
            r_ort = r_sum / piksel_sayisi
            g_ort = g_sum / piksel_sayisi
            b_ort = b_sum / piksel_sayisi

            # Gerçek termal fiş genellikle %85+ beyaz
            beyazlik = (r_ort + g_ort + b_ort) / 3
            sonuc["gorsel_beyazlik"] = round(beyazlik, 1)

            if beyazlik > 245:
                _ekle("K6", "🔍 Çok yüksek beyazlık — dijital olarak oluşturulmuş olabilir", 10)

            # RGB kanalları arasındaki fark (gri ölçek = düşük fark, renkli baskı = yüksek)
            kanal_fark = max(abs(r_ort - g_ort), abs(g_ort - b_ort), abs(r_ort - b_ort))
            if kanal_fark < 5 and beyazlik < 200:
                # Mükemmel gri tonlama — tarama değil, ekran görüntüsü olabilir
                _ekle("K6b", "🔍 Mükemmel gri tonlama — ekran görüntüsü şüphesi", 8)

    except Exception as _e:
        print(f"K6 renk analizi hatası: {_e}", flush=True)

    # ════════════════════════════════════════════
    # KATMAN 7 — GÖRSEL: KENAR GEOMETRİSİ
    # Gerçek fiş fotoğrafı → hafif eğik, gölge var
    # Ekran görüntüsü/dijital → tam dikdörtgen, sınırlar keskin
    # ════════════════════════════════════════════
    try:
        img_g2 = image.convert("L")
        w3, h3 = img_g2.size
        # En/boy oranı kontrolü — gerçek fiş genellikle dar ve uzun
        oran = h3 / max(w3, 1)
        sonuc["gorsel_en_boy"] = round(oran, 2)
        if oran < 1.2:
            _ekle("K7", f"🔍 En/boy oranı ({oran:.2f}) gerçek fiş için çok kısa — kırpılmış olabilir", 10)
        elif oran > 6.0:
            _ekle("K7", f"🔍 Olağandışı uzun görsel ({oran:.2f}) — birleştirilmiş fiş şüphesi", 8)

        # Köşe pikselleri analizi — dijital görüntüde köşeler saf beyaz/siyah olur
        _koseler = [
            img_g2.getpixel((0, 0)),
            img_g2.getpixel((w3-1, 0)),
            img_g2.getpixel((0, h3-1)),
            img_g2.getpixel((w3-1, h3-1))
        ]
        if all(k > 250 for k in _koseler):
            _ekle("K7b", "🔍 Tüm köşeler saf beyaz — ekran görüntüsü veya dijital kırpma şüphesi", 7)

    except Exception as _e:
        print(f"K7 geometri analizi hatası: {_e}", flush=True)

    # ════════════════════════════════════════════
    # KATMAN 8 — AI SAHTELİK SKORU (Gemini'den)
    # ════════════════════════════════════════════
    ai_risk = int(fis_data.get("risk_skoru", 0))
    ai_sahte = fis_data.get("sahte_mi", False)
    if ai_sahte:
        _ekle("K8", f"🚨 AI sahte fiş tespit etti: {fis_data.get('sahtelik_nedeni','')}", 30)
        sonuc["sahte_mi"] = True
    elif ai_risk >= 70:
        _ekle("K8", f"⚠️ AI yüksek risk skoru verdi: {ai_risk}/100", 15)

    for neden in fis_data.get("risk_nedenleri", []):
        if neden and neden not in ("...", "") and neden not in [b for b in sonuc["bulgular"]]:
            sonuc["bulgular"].append(f"• {neden}")

    # ════════════════════════════════════════════
    # KATMAN 9 — METİN YAPISI ANOMALİSİ
    # ════════════════════════════════════════════
    # AI'ın audit notundan metin kalıplarını analiz et
    _audit_lower = audit.lower()

    # Şüpheli ifadeler — gerçek POS fişlerinde bulunmayan
    _suphelikli_ifadeler = [
        ("karşılığı mal ve hizmeti aldım", "🔍 'Karşılığı mal ve hizmeti aldım' — standart POS fişi ifadesi değil", 15),
        ("teşekkür ederiz", "🔍 El yazısı teşekkür ifadesi — kurumsal fiş şüphesi", 5),
        ("lütfen tekrar gelin", "🔍 El yazısı davet ifadesi — kurumsal fiş şüphesi", 5),
    ]
    for _ifade, _mesaj, _risk in _suphelikli_ifadeler:
        if _ifade in _audit_lower or _ifade in firma.lower():
            _ekle("K9", _mesaj, _risk)

    # ════════════════════════════════════════════
    # KATMAN 10 — VERGİ NUMARASI FORMAT KONTROLÜ
    # Türkiye VKN: 10 hane | TCKN: 11 hane
    # ════════════════════════════════════════════
    _vkn_pattern = _re.compile(r'\b\d{10}\b')
    _tckn_pattern = _re.compile(r'\b[1-9]\d{10}\b')
    _audit_str = audit + firma

    vkn_eslesmeler = _vkn_pattern.findall(_audit_str)
    if not vkn_eslesmeler:
        # VKN yok ama fiş vergi gerektiriyor
        if toplam > 200:
            _ekle("K10", "🔍 500₺ üzeri fişte vergi/işyeri numarası tespit edilemedi", 10)
    else:
        # VKN checksum (Türk VKN algoritması)
        for _vkn in vkn_eslesmeler[:1]:
            try:
                _d = [int(c) for c in _vkn]
                _kalan = [((_d[i] + (9 - i)) % 10) for i in range(9)]
                _carpim = [(_kalan[i] * (2 ** (9 - i))) % 9 for i in range(9)]
                _carpim = [9 if c == 0 and _kalan[i] != 0 else c for i, c in enumerate(_carpim)]
                _kontrol = sum(_carpim) % 10
                if _kontrol != _d[9]:
                    _ekle("K10", f"🚨 Vergi numarası ({_vkn}) checksum geçersiz!", 25)
            except:
                pass

    # ════════════════════════════════════════════
    # KATMAN 11 — FİŞ SIRA NO / ONAY KODU
    # ════════════════════════════════════════════
    # Gerçek POS fişlerinde onay kodu 6 haneli rakam veya harf+rakam
    _onay_pattern = _re.compile(r'[Kk]\d{5,8}|[Oo][Nn][Aa][Yy]\s*[:]\s*\w+', _re.IGNORECASE)
    _onay_eslesmeler = _onay_pattern.findall(audit + firma)
    # Onay kodu formatı kontrolü (K09767 gibi)
    _onay_kod_raw = fis_data.get("ilginc_detay","") + audit
    if "onay kodu" in _onay_kod_raw.lower() or "onay:" in _onay_kod_raw.lower():
        pass  # Onay kodu var, iyi
    # Taksitli satış kontrolü
    if "taksitli" in (firma + audit).lower() or "taksit" in (firma + audit).lower():
        _ekle("K11", "🔍 Taksitli satış fişi — birden fazla tutarın toplamı kontrol edilmeli", 5)

    # ════════════════════════════════════════════
    # KATMAN 12 — İŞLETME ADI GÜVENİLİRLİK
    # ════════════════════════════════════════════
    if firma:
        _firma_lower = firma.lower().strip()
        # Çok kısa veya genel firma adları
        if len(_firma_lower) <= 2:
            _ekle("K12", "🚨 Firma adı çok kısa — sahte veya eksik", 15)
        elif len(_firma_lower) <= 4:
            _ekle("K12", "🔍 Firma adı çok kısa — doğrulama gerekli", 8)

        # Sadece rakam içeren firma adı
        if _firma_lower.isdigit():
            _ekle("K12", "🚨 Firma adı sadece rakamlardan oluşuyor", 20)

        # Bilinen zincirlerin yazım kontrolü (yakın ama yanlış yazım)
        _zincirler = {
            "migroz": "migros", "migrros": "migros",
            "bimm": "bim", "bi m": "bim",
            "a 101": "a101", "a-101": "a101",
            "şokk": "şok", "şok market": "şok",
            "carrefurr": "carrefour",
            "teknossa": "teknosa", "techno sa": "teknosa",
        }
        for _yanlis, _dogru in _zincirler.items():
            if _yanlis in _firma_lower:
                _ekle("K12", f"🚨 Firma adı yazım hatası: '{firma}' → muhtemelen '{_dogru}'?", 20)

    # ════════════════════════════════════════════
    # SONUÇ: Nihai karar
    # ════════════════════════════════════════════
    toplam_risk = sonuc["guvensizlik_skoru"]
    if toplam_risk >= 70 and not sonuc["sahte_mi"]:
        sonuc["sahte_mi"] = True
        sonuc["bulgular"].insert(0, f"🚨 {len(sonuc['katman_sonuclari'])} katman analizi → Risk: {toplam_risk}/100 — SAHTE ŞÜPHESİ")
    elif toplam_risk >= 40:
        sonuc["bulgular"].insert(0, f"⚠️ {len(sonuc['katman_sonuclari'])} katman analizi → Risk: {toplam_risk}/100 — DİKKATLİ İNCELENMELİ")

    return sonuc

def ekip_siralaması(data):
    bu_ay = datetime.now().strftime("%Y-%m")
    siralama = []
    for phone, info in PHONE_DIRECTORY.items():
        user = info["ad"]
        toplam = sum(e["Tutar"] for e in data["expenses"] if e["Kullanıcı"] == user and e.get("Tarih","").startswith(bu_ay))
        butce = data.get("user_limits", {}).get(user, info.get("limit", 1))
        oran = (toplam / butce) * 100
        fis = data["fis_sayaci"].get(user, 0)
        siralama.append((user, toplam, oran, fis, info["emoji"]))
    siralama.sort(key=lambda x: x[1], reverse=True)
    madalyalar = ["🥇", "🥈", "🥉"]
    satirlar = []
    for i, (user, toplam, oran, fis, emoji) in enumerate(siralama):
        madalya = madalyalar[i] if i < 3 else "  "
        seviye = seviye_hesapla(fis)
        satirlar.append(f"{madalya} {emoji} {user}\n   💰 {toplam:,.0f} ₺ (%{oran:.0f} bütçe)\n   {seviye} • {fis} fiş")
    return "\n\n".join(satirlar)

def anomali_tespit(user_name, tutar, data):
    uyarilar = []
    kullanici_harcamalari = [e["Tutar"] for e in data["expenses"] if e["Kullanıcı"] == user_name and e["Tutar"] > 0]
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

def butce_durumu_str(user_name, data):
    bu_ay = datetime.now().strftime("%Y-%m")
    ay_top = sum(e["Tutar"] for e in data["expenses"] if e["Kullanıcı"] == user_name and e.get("Tarih","").startswith(bu_ay))
    butce = data["budgets"].get(user_name, 0)
    if butce == 0: return ""
    oran = (ay_top / butce) * 100
    bar_dolu = min(10, int(oran / 10))
    bar = "█" * bar_dolu + "░" * (10 - bar_dolu)
    return f"[{bar}] %{oran:.1f} ({ay_top:.0f}/{butce:.0f} ₺)"

# ─────────────────────────────────────────────
#  📍 KONUM & ZAMAN ZEKASI — 3 YENİ ÖZELLİK
# ─────────────────────────────────────────────

def _koordinat_ara(sehir_adi: str) -> tuple:
    """
    Şehir adından koordinat döndürür.
    Yerleşik Türkiye şehir tablosu kullanır — API bağımlılığı yok, anında çalışır.
    Döner: (lat, lon) veya (None, None)
    """
    # Türkiye 81 il + büyük ilçe koordinat tablosu
    SEHIR_KOORDINAT = {
        "adana": (37.0000, 35.3213), "adıyaman": (37.7648, 38.2786),
        "afyonkarahisar": (38.7637, 30.5406), "afyon": (38.7637, 30.5406),
        "ağrı": (39.7191, 43.0503), "aksaray": (38.3687, 34.0370),
        "amasya": (40.6499, 35.8353), "ankara": (39.9208, 32.8541),
        "antalya": (36.8969, 30.7133), "ardahan": (41.1105, 42.7022),
        "artvin": (41.1828, 41.8183), "aydın": (37.8444, 27.8458),
        "balıkesir": (39.6484, 27.8826), "bartın": (41.6344, 32.3375),
        "batman": (37.8812, 41.1351), "bayburt": (40.2552, 40.2249),
        "bilecik": (40.1506, 29.9792), "bingöl": (38.8854, 40.4983),
        "bitlis": (38.3938, 42.1232), "bolu": (40.7359, 31.6061),
        "burdur": (37.7204, 30.2903), "bursa": (40.1885, 29.0610),
        "çanakkale": (40.1553, 26.4142), "çankırı": (40.6013, 33.6134),
        "çorum": (40.5506, 34.9556), "denizli": (37.7765, 29.0864),
        "diyarbakır": (37.9144, 40.2306), "düzce": (40.8438, 31.1565),
        "edirne": (41.6818, 26.5623), "elazığ": (38.6810, 39.2264),
        "erzincan": (39.7500, 39.5000), "erzurum": (39.9043, 41.2679),
        "eskişehir": (39.7767, 30.5206), "gaziantep": (37.0662, 37.3833),
        "giresun": (40.9128, 38.3895), "gümüşhane": (40.4386, 39.4814),
        "hakkari": (37.5744, 43.7408), "hatay": (36.4018, 36.3498),
        "iğdır": (39.9167, 44.0333), "isparta": (37.7648, 30.5566),
        "istanbul": (41.0082, 28.9784), "i̇stanbul": (41.0082, 28.9784),
        "izmir": (38.4189, 27.1287), "i̇zmir": (38.4189, 27.1287),
        "kahramanmaraş": (37.5858, 36.9371), "karabük": (41.2061, 32.6204),
        "karaman": (37.1759, 33.2287), "kars": (40.6013, 43.0975),
        "kastamonu": (41.3887, 33.7827), "kayseri": (38.7312, 35.4787),
        "kilis": (36.7184, 37.1212), "kırıkkale": (39.8468, 33.5153),
        "kırklareli": (41.7333, 27.2167), "kırşehir": (39.1425, 34.1709),
        "kocaeli": (40.8533, 29.8815), "izmit": (40.7654, 29.9408),
        "konya": (37.8746, 32.4932), "kütahya": (39.4167, 29.9833),
        "malatya": (38.3552, 38.3095), "manisa": (38.6191, 27.4289),
        "mardin": (37.3212, 40.7245), "mersin": (36.8000, 34.6333),
        "muğla": (37.2154, 28.3636), "muş": (38.7432, 41.4914),
        "nevşehir": (38.6939, 34.6857), "niğde": (37.9667, 34.6833),
        "ordu": (40.9862, 37.8797), "osmaniye": (37.0742, 36.2464),
        "rize": (41.0201, 40.5234), "sakarya": (40.7569, 30.3781),
        "adapazarı": (40.7896, 30.4036), "samsun": (41.2867, 36.3300),
        "siirt": (37.9333, 41.9500), "sinop": (42.0231, 35.1531),
        "sivas": (39.7477, 37.0179), "şanlıurfa": (37.1591, 38.7969),
        "urfa": (37.1591, 38.7969), "şırnak": (37.5164, 42.4611),
        "tekirdağ": (40.9833, 27.5167), "tokat": (40.3167, 36.5500),
        "trabzon": (41.0015, 39.7178), "tunceli": (39.1079, 39.5479),
        "uşak": (38.6823, 29.4082), "van": (38.4891, 43.4089),
        "yalova": (40.6500, 29.2667), "yozgat": (39.8181, 34.8147),
        "zonguldak": (41.4564, 31.7987),
        # Büyük ilçeler
        "yenimahalle": (39.9667, 32.8167), "çankaya": (39.9032, 32.8597),
        "keçiören": (39.9667, 32.8667), "etimesgut": (39.9500, 32.6667),
        "mamak": (39.9333, 32.9333), "sincan": (39.9833, 32.5833),
        "kadıköy": (40.9833, 29.0833), "üsküdar": (41.0333, 29.0167),
        "beşiktaş": (41.0422, 29.0000), "şişli": (41.0614, 28.9869),
        "bakırköy": (40.9833, 28.8667), "bağcılar": (41.0333, 28.8500),
        "esenyurt": (41.0333, 28.6667), "başakşehir": (41.0833, 28.8000),
        "pendik": (40.8667, 29.2333), "maltepe": (40.9167, 29.1500),
        "kartal": (40.9000, 29.2000), "ataşehir": (40.9833, 29.1333),
        "bornova": (38.4667, 27.2167), "buca": (38.3833, 27.1833),
        "karşıyaka": (38.4667, 27.1167), "konak": (38.4167, 27.1333),
        "çiğli": (38.4833, 27.0500), "osmangazi": (40.1833, 29.0500),
        "nilüfer": (40.2167, 28.9833), "yıldırım": (40.2000, 29.1000),
        "muratpaşa": (36.8833, 30.7000), "kepez": (36.9500, 30.7167),
        "mezitli": (36.7833, 34.5833), "toroslar": (36.8000, 34.5167),
    }

    if not sehir_adi:
        return None, None

    temiz = sehir_adi.lower().strip()
    # Türkçe karakter normalize
    temiz = (temiz.replace("ı", "i").replace("ğ", "g").replace("ş", "s")
             .replace("ç", "c").replace("ö", "o").replace("ü", "u"))

    # Direkt eşleşme
    for anahtar, koordinat in SEHIR_KOORDINAT.items():
        anahtar_n = (anahtar.lower()
                     .replace("ı", "i").replace("ğ", "g").replace("ş", "s")
                     .replace("ç", "c").replace("ö", "o").replace("ü", "u"))
        if temiz == anahtar_n or temiz in anahtar_n or anahtar_n in temiz:
            return koordinat

    return None, None

def _mesafe_km(lat1, lon1, lat2, lon2) -> float:
    """Haversine formülü ile iki koordinat arası mesafe (km)."""
    import math
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def _min_sure_saat(mesafe_km: float) -> float:
    """
    İki nokta arası minimum ulaşım süresi (saat) tahmini.
    Türkiye'de şehirlerarası ortalama 80 km/s, şehir içi 40 km/s varsayımı.
    """
    if mesafe_km < 50:
        return mesafe_km / 40
    return mesafe_km / 80

def konum_celiskisi_kontrol(fis_adresi: str, fis_sehri: str, user_name: str,
                             mesaj_zamani: datetime, fis_tarihi: str, data: dict) -> dict:
    """
    ÖZELLİK 1: Fişin adresi ile kullanıcının son bilinen konumunu karşılaştırır.
    
    Döner: {
        "celiski": bool,
        "risk_artisi": int,
        "uyari_mesaji": str,
        "fis_sehri": str,
        "son_konum_sehri": str,
        "mesafe_km": float
    }
    """
    sonuc = {"celiski": False, "risk_artisi": 0, "uyari_mesaji": "", 
             "fis_sehri": "", "son_konum_sehri": "", "mesafe_km": 0}
    
    if not fis_adresi and not fis_sehri:
        return sonuc
    
    # Kullanıcının son bilinen konumunu bul (son 3 fişten şehir bilgisi)
    kullanici_fisler = [e for e in data.get("expenses", [])
                        if e.get("Kullanıcı") == user_name and e.get("Sehir")]
    
    if not kullanici_fisler:
        return sonuc  # İlk fiş, karşılaştırılacak geçmiş yok
    
    # Son fişin şehri
    son_fis_sehri = kullanici_fisler[-1].get("Sehir", "").strip()
    
    # Yeni fişin şehrini tespit et
    yeni_fis_sehri = ""
    if fis_sehri:
        yeni_fis_sehri = fis_sehri.strip()
    elif fis_adresi:
        # Adresten şehir adını çıkar (kaba yöntem — virgülden sonrası genellikle şehirdir)
        parcalar = [p.strip() for p in fis_adresi.split(",")]
        if len(parcalar) >= 2:
            yeni_fis_sehri = parcalar[-1]
    
    if not yeni_fis_sehri or not son_fis_sehri:
        return sonuc
    
    sonuc["fis_sehri"] = yeni_fis_sehri
    sonuc["son_konum_sehri"] = son_fis_sehri
    
    # Aynı şehirse sorun yok
    if yeni_fis_sehri.lower().replace("i̇", "i") == son_fis_sehri.lower().replace("i̇", "i"):
        return sonuc
    
    # Farklı şehir — koordinat alıp mesafe hesapla
    lat1, lon1 = _koordinat_ara(son_fis_sehri)
    lat2, lon2 = _koordinat_ara(yeni_fis_sehri)
    
    if not lat1 or not lat2:
        # Koordinat bulunamadı ama şehir adları farklı — orta seviye uyarı
        sonuc["celiski"] = True
        sonuc["risk_artisi"] = 15
        sonuc["uyari_mesaji"] = (
            f"📍 *Konum Çelişkisi Tespit Edildi*\n"
            f"Bu fiş *{yeni_fis_sehri}*'dan — ama son bilinen konumun *{son_fis_sehri}*.\n"
            f"Seyahatteysen sorun değil, açıklama yazmak ister misin?"
        )
        return sonuc
    
    mesafe = _mesafe_km(lat1, lon1, lat2, lon2)
    sonuc["mesafe_km"] = round(mesafe, 0)
    
    if mesafe < 80:
        return sonuc  # Yakın şehirler, normal
    
    # Uzak şehirler — risk artır ve uyar
    sonuc["celiski"] = True
    
    if mesafe > 500:
        sonuc["risk_artisi"] = 35
        emoji = "🚨"
        yorum = "Bu mesafe uçak gerektirir."
    elif mesafe > 200:
        sonuc["risk_artisi"] = 25
        emoji = "⚠️"
        yorum = "Bu mesafeye gelmek birkaç saat sürer."
    else:
        sonuc["risk_artisi"] = 15
        emoji = "📍"
        yorum = "Kısa bir yolculuk yapmış olabilirsin."
    
    sonuc["uyari_mesaji"] = (
        f"{emoji} *Konum Çelişkisi Tespit Edildi!*\n"
        f"Bu fiş *{yeni_fis_sehri}*'dan alınmış.\n"
        f"Son bilinen konumun: *{son_fis_sehri}* (~{mesafe:.0f} km uzak)\n"
        f"_{yorum}_\n"
        f"Seyahat fişiyse 'seyahat' yazarak onaylayabilirsin — risk puanın düşer."
    )
    return sonuc


def zaman_mekan_imkansizlik_kontrol(fis_adresi: str, fis_sehri: str, fis_tarihi: str,
                                     fis_saati_tahmini: str, user_name: str, data: dict) -> dict:
    """
    ÖZELLİK 2: Aynı gün farklı şehirlerden fiş gelip gelemeyeceğini hesaplar.
    Google Maps gerekmez — Haversine + ortalama hız yeterli.
    
    Döner: {"imkansiz": bool, "risk_artisi": int, "uyari_mesaji": str}
    """
    sonuc = {"imkansiz": False, "risk_artisi": 0, "uyari_mesaji": ""}
    
    if not fis_tarihi or not fis_sehri:
        return sonuc
    
    # Aynı güne ait, farklı şehirden fişleri bul
    ayni_gun_fisler = [
        e for e in data.get("expenses", [])
        if e.get("Kullanıcı") == user_name
        and e.get("Tarih", "") == fis_tarihi
        and e.get("Sehir", "").strip()
        and e.get("Sehir", "").strip().lower() != fis_sehri.lower()
    ]
    
    if not ayni_gun_fisler:
        return sonuc
    
    # Her önceki fiş için imkansızlık kontrolü
    for onceki_fis in ayni_gun_fisler[-3:]:  # Son 3 tanesine bak
        onceki_sehir = onceki_fis.get("Sehir", "").strip()
        onceki_zaman_str = onceki_fis.get("Yukleme_Zamani", "")
        
        if not onceki_sehir or not onceki_zaman_str:
            continue
        
        lat1, lon1 = _koordinat_ara(onceki_sehir)
        lat2, lon2 = _koordinat_ara(fis_sehri)
        
        if not lat1 or not lat2:
            continue
        
        mesafe = _mesafe_km(lat1, lon1, lat2, lon2)
        
        if mesafe < 80:
            continue  # Yakın, sorun değil
        
        min_sure = _min_sure_saat(mesafe)
        
        # İki fişin zamanları arasındaki fark
        try:
            t1 = datetime.strptime(onceki_zaman_str[:16], "%Y-%m-%d %H:%M")
            # Yeni fişin yükleme zamanı = şu an (webhook'a geldiği an)
            # Fonksiyon imzasına mesaj_zamani ekleyelim — şimdilik datetime.now() güvenli
            t2 = datetime.now()
            fark_saat = abs((t2 - t1).total_seconds()) / 3600
        except:
            fark_saat = 999
        
        if fark_saat < min_sure * 0.85:  # %15 tolerans
            sonuc["imkansiz"] = True
            sonuc["risk_artisi"] = 40
            sonuc["uyari_mesaji"] = (
                f"⏱️ *Zaman-Mekan Tutarsızlığı!*\n"
                f"Bugün saat {t1.strftime('%H:%M')}'de *{onceki_sehir}*'daydın.\n"
                f"Bu fiş ise *{fis_sehri}*'dan — arası {mesafe:.0f} km.\n"
                f"Bu mesafeyi en az *{min_sure:.1f} saatte* alabilirsin, ama aradan yalnızca *{fark_saat:.1f} saat* geçmiş.\n"
                f"🚨 Risk puanı donduruldu. Açıklama yazar mısın?"
            )
            break  # İlk imkansızlık yeter
    
    return sonuc


def fis_yasi_kontrol(raw_bytes: bytes, mesaj_zamani: datetime) -> dict:
    """
    ÖZELLİK 3: Fotoğrafın EXIF'inden çekilme tarihini okur,
    yükleme zamanıyla karşılaştırır. WhatsApp bazen EXIF'i siliyor —
    o zaman sessizce geçer, hata vermez.
    
    Döner: {"yasli": bool, "gun_farki": int, "risk_artisi": int, "uyari_mesaji": str, "cekme_zamani": str}
    """
    sonuc = {"yasli": False, "gun_farki": 0, "risk_artisi": 0, 
             "uyari_mesaji": "", "cekme_zamani": ""}
    try:
        from PIL.ExifTags import TAGS
        img = Image.open(BytesIO(raw_bytes))
        exif_data = img._getexif()
        if not exif_data:
            return sonuc
        
        exif = {TAGS.get(k, k): v for k, v in exif_data.items()}
        
        # DateTimeOriginal önce, DateTime sonra
        dt_str = exif.get("DateTimeOriginal") or exif.get("DateTime")
        if not dt_str:
            return sonuc
        
        cekme_dt = datetime.strptime(str(dt_str), "%Y:%m:%d %H:%M:%S")
        sonuc["cekme_zamani"] = cekme_dt.strftime("%d.%m.%Y %H:%M")
        
        gun_farki = (mesaj_zamani - cekme_dt).days
        sonuc["gun_farki"] = gun_farki
        
        if gun_farki < 0:
            # Fotoğraf gelecekten gelmiş gibi görünüyor — saat ayarı bozuk olabilir
            sonuc["yasli"] = True
            sonuc["risk_artisi"] = 20
            sonuc["uyari_mesaji"] = (
                f"🕐 *Zaman Anomalisi!*\n"
                f"Bu fotoğraf {abs(gun_farki)} gün *sonraki* bir tarih içeriyor.\n"
                f"Telefon saat ayarın yanlış olabilir veya fiş manipüle edilmiş. +20 risk."
            )
        elif gun_farki >= 30:
            sonuc["yasli"] = True
            sonuc["risk_artisi"] = 30
            sonuc["uyari_mesaji"] = (
                f"🗓️ *Çok Eski Fiş!*\n"
                f"Bu fotoğraf *{gun_farki} gün önce* ({cekme_dt.strftime('%d.%m.%Y')}) çekilmiş!\n"
                f"Bu kadar eski bir fişi neden şimdi yüklüyorsun? Açıklama gerekiyor. +30 risk."
            )
        elif gun_farki >= 7:
            sonuc["yasli"] = True
            sonuc["risk_artisi"] = 20
            sonuc["uyari_mesaji"] = (
                f"🗓️ *Geç Yüklenen Fiş*\n"
                f"Fotoğraf {gun_farki} gün önce ({cekme_dt.strftime('%d.%m.%Y')}) çekilmiş.\n"
                f"Geç kalmışsın, anlıyoruz — ama yönetici de görecek. +20 risk."
            )
        elif gun_farki >= 3:
            sonuc["yasli"] = True
            sonuc["risk_artisi"] = 10
            sonuc["uyari_mesaji"] = (
                f"📅 Fişi {gun_farki} gün önce çekip bugün yükledin.\n"
                f"Hızlı yüklemek risk puanını düşürür — bir dahaki sefere! +10 risk."
            )
    except Exception as e:
        print(f"EXIF okuma hatası (sessiz geçildi): {e}", flush=True)
    
    return sonuc


def nl_sorgu(soru, user_name, data):
    harcamalar = [e for e in data["expenses"] if e["Kullanıcı"] == user_name]
    if not harcamalar: return "Henüz kayıtlı harcamanız yok."
    prompt = f"""Kullanıcı sorusu: "{soru}"
Harcama verileri: {json.dumps(harcamalar[-50:], ensure_ascii=False)}
Bugün: {datetime.now().strftime('%Y-%m-%d')}
Kısa, net Türkçe yanıt ver."""
    try: return ai_call(prompt)
    except Exception as e: return f"Sorgu hatası: {e}"

def konusmali_ai_yanit(user_name, mesaj, data, user_states):
    history = user_states.get(AI_CHAT_HISTORY, {}).get(user_name, [])
    harcamalar = [e for e in data["expenses"] if e["Kullanıcı"] == user_name]
    bu_ay = datetime.now().strftime("%Y-%m")
    ay_fis = [e for e in harcamalar if e.get("Tarih","").startswith(bu_ay)]
    ay_toplam = sum(e["Tutar"] for e in ay_fis)
    butce = data.get("user_limits", {}).get(user_name, 0)
    kat_ozet = defaultdict(float)
    for e in ay_fis: kat_ozet[e.get("Kategori","diger")] += e["Tutar"]
    kat_str = ", ".join(f"{k}:{v:.0f}₺" for k, v in sorted(kat_ozet.items(), key=lambda x: -x[1])[:5])
    sistem = f"""Sen STINGA PRO finans asistanısın. Kullanıcı: {user_name}
Bu ay: {ay_toplam:,.0f}₺ / Bütçe: {butce:,.0f}₺ | Kategoriler: {kat_str} | Toplam: {len(harcamalar)} fiş
Türkçe, samimi, kısa tut. Bugün: {datetime.now().strftime('%d %B %Y')}"""
    gemini_contents = [sistem]
    for turn in history[-8:]:
        gemini_contents.append(f"Kullanıcı: {turn['user']}\nAsistan: {turn['assistant']}")
    gemini_contents.append(f"Kullanıcı: {mesaj}")
    try: yanit = ai_call("\n\n".join(gemini_contents))
    except Exception as e: yanit = f"Sorun oluştu: {e}"
    history.append({"user": mesaj, "assistant": yanit})
    history = history[-10:]
    user_states.setdefault(AI_CHAT_HISTORY, {})[user_name] = history
    return yanit

def konum_isle(lat, lon, user_name, data):
    kullanici_fisler = [(i, e) for i, e in enumerate(data["expenses"]) if e["Kullanıcı"] == user_name and not e.get("Konum")]
    if not kullanici_fisler: return "📍 Konum alındı ama bağlanacak bekleyen fiş bulunamadı."
    idx, son_fis = kullanici_fisler[-1]
    adres = f"{lat:.4f}, {lon:.4f}"
    sehir = ""
    try:
        geo_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&accept-language=tr"
        geo_res = requests.get(geo_url, headers={"User-Agent": "StingaProBot/1.0"}, timeout=5).json()
        addr = geo_res.get("address", {})
        parcalar = []
        for alan in ["amenity", "road", "neighbourhood", "suburb", "town", "city", "county"]:
            if addr.get(alan): parcalar.append(addr[alan])
            if len(parcalar) >= 3: break
        if parcalar: adres = ", ".join(parcalar)
        sehir = addr.get("city") or addr.get("town") or addr.get("county") or ""
    except Exception as geo_err:
        print(f"Geocoding hatası: {geo_err}", flush=True)
    data["expenses"][idx]["Konum"] = adres
    data["expenses"][idx]["Konum_Lat"] = lat
    data["expenses"][idx]["Konum_Lon"] = lon
    if sehir: data["expenses"][idx]["Sehir"] = sehir
    save_data(data)
    firma = son_fis.get("Firma", "Son fiş")
    tutar = son_fis.get("Tutar", 0)
    return f"📍 *Konum bağlandı!*\n🏢 {firma} — {tutar:,.0f} ₺\n📌 _{adres}_\n🗺️ https://maps.google.com/?q={lat},{lon}"

def coklu_fis_isle(sender_phone, user_name, user_info, num_media, data, twilio_media_urls=None, meta_media_ids=None, mesaj_odeme_turu=None):
    """Birden fazla medya: tüm görselleri sırayla işler. mesaj_odeme_turu varsa her fişe uygulanır."""
    sonuclar = []
    media_urls = twilio_media_urls or []
    for i, media_url_item in enumerate(media_urls[:5]):
        try:
            # Twilio URL'den görsel indir
            raw_bytes = None
            try:
                account_sid = os.getenv("TWILIO_ACCOUNT_SID")
                auth_token  = os.getenv("TWILIO_AUTH_TOKEN")
                r_dl = requests.get(media_url_item, auth=(account_sid, auth_token), timeout=30)
                r_dl.raise_for_status()
                raw_bytes = r_dl.content
            except Exception as _me:
                print(f"Twilio media indirme hatası (çoklu {i}): {_me}", flush=True)
            if not raw_bytes or len(raw_bytes) < 500:
                sonuclar.append(f"⚠️ Fiş {i+1}: Görsel indirilemedi"); continue
            img_hash = gorsel_hash(raw_bytes)
            if img_hash in data["duplicate_hashes"]:
                sonuclar.append(f"⚠️ Fiş {i+1}: Mükerrer, atlandı"); continue
            try:
                image = Image.open(BytesIO(raw_bytes))
                image.verify()
                image = Image.open(BytesIO(raw_bytes))
            except:
                sonuclar.append(f"❌ Fiş {i+1}: Geçersiz görsel"); continue
            bugun = datetime.now().strftime("%Y-%m-%d")
            prompt = (
                f"Fişi dikkatli analiz et. Sadece JSON döndür. Bugün: {bugun}\n"
                'ÖNEMLİ: OPET, Shell, BP, Total gibi akaryakıt istasyonlari: fis_turu="akaryakit"\n'
                "Sigara, çikolata, kola gibi kişisel ürünler varsa kisisel_giderler listesine ekle.\n"
                '{"firma":"?","tarih":"YYYY-MM-DD","toplam_tutar":0.0,"kdv_tutari":0.0,'
                '"odeme_yontemi":"nakit|kredi_karti|havale","para_birimi":"TRY",'
                '"kisisel_giderler":[{"urun":"...","tutar":0.0}],'
                '"risk_skoru":0,"sahte_mi":false,"fis_turu":"restoran|market|akaryakıt|otel|diger",'
                '"audit_notu":"kısa özet, kişisel gider varsa belirt"}'
            )
            ai_res = client.models.generate_content(model=MODEL_NAME, contents=[prompt, image])
            raw_text = re.sub(r"```json?|```", "", ai_res.text).strip()
            _m = re.search(r'\{.*\}', raw_text, re.DOTALL)
            fis = json.loads(_m.group() if _m else raw_text)
            tutar_try = float(fis.get("toplam_tutar", 0))
            para_birimi = fis.get("para_birimi", "TRY")
            if para_birimi != "TRY":
                try:
                    r = requests.get(DOVIZ_API_URL, timeout=5).json()
                    kur = r["rates"].get(para_birimi)
                    if kur: tutar_try = tutar_try / kur
                except: pass
            kategori = kategori_tespit(fis.get("firma", ""), fis.get("fis_turu", ""))
            risk = int(fis.get("risk_skoru", 0))
            # Kişisel gider risk artışı
            _ckg = fis.get("kisisel_giderler", [])
            if _ckg:
                risk = min(100, risk + len(_ckg) * 15)
            durum = "Sahte Şüphesi" if risk >= 70 or fis.get("sahte_mi") else "Onay Bekliyor"
            # Şenol Bey otomatik onay
            if user_name in ("Şenol Özyaman", "Şenol Faik Özyaman") and durum == "Onay Bekliyor":
                durum = "Onaylandı"
            final_odeme = mesaj_odeme_turu if mesaj_odeme_turu else fis.get("odeme_yontemi", "bilinmiyor")
            new_expense = {
                "ID": datetime.now().strftime("%Y%m%d%H%M%S") + str(i),
                "Tarih": fis.get("tarih", bugun),
                "Yukleme_Zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Kullanıcı": user_name, "Rol": user_info["rol"],
                "Firma": fis.get("firma", "Bilinmiyor"),
                "Tutar": tutar_try, "KDV": float(fis.get("kdv_tutari", 0)),
                "ParaBirimi": para_birimi,
                "OdemeTipi": final_odeme, "Odeme_Turu": final_odeme,
                "Kategori": kategori, "Durum": durum, "Risk_Skoru": risk,
                "AI_Audit": re.sub(r'<[^>]+>', '', str(fis.get("audit_notu", ""))).strip(),
                "Kisisel_Giderler": _ckg,
                "Anomaliler": anomali_tespit(user_name, tutar_try, data),
                "Hash": img_hash, "Proje": "Genel Merkez",
                "Kaynak": "WhatsApp-Çoklu", "Gorsel_B64": "",
            }
            data["expenses"].append(new_expense)
            data["duplicate_hashes"].append(img_hash)
            data.setdefault("fis_sayaci", {})[user_name] = data["fis_sayaci"].get(user_name, 0) + 1
            add_xp(user_name, 50, f"Çoklu fiş #{i+1}", data=data)
            risk_emoji = "🟢" if risk < 30 else "🟡" if risk < 70 else "🔴"
            odeme_icon = "💵" if final_odeme == "harcirah" else "🏦" if final_odeme == "sirket_karti" else "💳"
            sonuclar.append(f"✅ *Fiş {i+1}:* {fis.get('firma','?')} — {tutar_try:,.0f}₺  {risk_emoji} {odeme_icon}")
        except Exception as e:
            print(f"Çoklu fiş {i} hatası: {e}", flush=True)
            sonuclar.append(f"❌ Fiş {i+1}: Okunamadı")
    save_data(data)
    toplam_tutar = sum(e["Tutar"] for e in data["expenses"]
        if e.get("Kaynak") == "WhatsApp-Çoklu" and e.get("Yukleme_Zamani","").startswith(datetime.now().strftime("%Y-%m-%d")) and e["Kullanıcı"] == user_name)
    odeme_str = f"\n💳 Ödeme: *{odeme_turu_label(mesaj_odeme_turu)}*" if mesaj_odeme_turu else ""
    return (f"📦 *{num_media} Fiş İşlendi*\n{'─'*22}\n" + "\n".join(sonuclar) +
            f"\n\n💰 Bugün eklenen: *{toplam_tutar:,.0f}₺*" + odeme_str + f"\n📨 Tümü yönetici onayına gönderildi. Harcaman Onay/Ret durumunda bilgilendirileceksin.")


# ─────────────────────────────────────────────
#  ANA WEBHOOK
# ─────────────────────────────────────────────

@app.route("/whatsapp", methods=['GET'])
def whatsapp_verify():
    """Meta, webhook URL'ini doğrulamak için bu endpoint'i çağırır."""
    verify_token = os.getenv("META_VERIFY_TOKEN", "stinga_verify")
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == verify_token:
        print("✅ Meta webhook doğrulandı!", flush=True)
        return challenge, 200
    print(f"❌ Meta webhook doğrulama başarısız. token={token}", flush=True)
    return "Forbidden", 403


def _parse_meta_message(body: dict):
    """Meta webhook payload'ından mesaj bilgilerini çıkarır."""
    try:
        entry   = body["entry"][0]
        changes = entry["changes"][0]["value"]
        msg_obj = changes["messages"][0]
        sender_phone = "whatsapp:+" + msg_obj["from"]

        msg_type = msg_obj.get("type", "text")
        incoming_msg = ""
        num_media    = 0
        media_url    = None
        media_mime   = None
        wa_lat = wa_lon = ""

        if msg_type == "text":
            incoming_msg = msg_obj["text"]["body"]
        elif msg_type in ("image", "document"):
            num_media = 1
            media_id  = msg_obj[msg_type]["id"]
            # Görseli Media ID → URL → bayt olarak çekeceğiz
            media_url = f"__meta_media_id__{media_id}"  # işaret değeri
            media_mime = msg_obj[msg_type].get("mime_type", "image/jpeg")
            # Bazen altyazı da gelir
            incoming_msg = msg_obj[msg_type].get("caption", "")
        elif msg_type == "location":
            wa_lat = str(msg_obj["location"]["latitude"])
            wa_lon = str(msg_obj["location"]["longitude"])

        return sender_phone, incoming_msg, num_media, media_url, media_mime, wa_lat, wa_lon
    except Exception as e:
        print(f"Meta payload parse hatası: {e}", flush=True)
        return None, "", 0, None, None, "", ""


def _meta_download_media(media_id: str) -> bytes:
    """Meta Media ID'den binary görsel indirir."""
    token = os.getenv("META_ACCESS_TOKEN", "")
    # Adım 1: media_id → gerçek URL al
    r = requests.get(
        f"https://graph.facebook.com/v20.0/{media_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    r.raise_for_status()
    dl_url = r.json()["url"]
    # Adım 2: URL'den içeriği indir
    r2 = requests.get(
        dl_url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    r2.raise_for_status()
    return r2.content


@app.route("/whatsapp", methods=['GET', 'POST'])
def whatsapp_webhook():
    if request.method == 'GET':
        return jsonify({"status": "ok"}), 200
    # ── Twilio payload parse ──────────────────────────────────────
    sender_phone = request.form.get("From", "")        # "whatsapp:+905xxxxxxxx"
    incoming_msg = request.form.get("Body", "").strip()
    num_media    = int(request.form.get("NumMedia", 0))
    media_url    = request.form.get("MediaUrl0", None)
    media_mime   = request.form.get("MediaContentType0", "")
    wa_lat       = request.form.get("Latitude", "")
    wa_lon       = request.form.get("Longitude", "")

    if not sender_phone:
        return jsonify({"status": "ignored"}), 200

    print(f"📩 Gelen mesaj: {sender_phone} → {incoming_msg[:50] if incoming_msg else '[medya]'}", flush=True)

    is_location = bool(wa_lat and wa_lon)

    # ── Yanıt yardımcısı: msg.body() yerine send_whatsapp() ──
    class _MsgProxy:
        def __init__(self): self._text = ""
        def body(self, t): self._text = t

    msg = _MsgProxy()
    def _reply(text=None):
        t = text or msg._text
        if t:
            send_whatsapp(sender_phone, t)
        return jsonify({"status": "ok"}), 200

    user_info = PHONE_DIRECTORY.get(sender_phone, {"ad": "Bilinmeyen", "rol": "—", "limit": 0, "emoji": "👤", "yetki": "user"})
    user_name = user_info["ad"]
    is_admin  = user_info.get("yetki") == "admin"

    data = load_data()
    data.setdefault("user_states", {})
    us = data["user_states"].setdefault(user_name, {})
    mesaj_lower = incoming_msg.lower()

    # ── Mesajdan ödeme türü tespiti
    mesaj_odeme_turu = detect_odeme_turu(incoming_msg)

    # ══════════════════════════════════════════
    # 🔄 ÖDEME TÜRÜ BEKLEME MODU — fiş analiz edildi, ödeme türü soruldu
    # ══════════════════════════════════════════
    if us.get(ODEME_BEKLE_FLAG) and not num_media and not is_location:
        odeme_secim = detect_odeme_turu(incoming_msg)
        if not odeme_secim:
            # Doğrudan "1" veya "2" ile de seçebilsin
            if mesaj_lower.strip() in ("1", "harcırah", "harcirah"):
                odeme_secim = "harcirah"
            elif mesaj_lower.strip() in ("2", "şirket", "sirket", "şirket kartı"):
                odeme_secim = "sirket_karti"
        if odeme_secim:
            # Bekleyen fiş verisini al ve kaydet
            bekleyen = us.pop(ODEME_BEKLE_DATA, None)
            us.pop(ODEME_BEKLE_FLAG, None)
            if bekleyen:
                bekleyen["OdemeTipi"] = odeme_secim
                bekleyen["Odeme_Turu"] = odeme_secim
                data["expenses"].append(bekleyen)
                data.setdefault("fis_sayaci", {})[user_name] = data["fis_sayaci"].get(user_name, 0) + 1
                add_xp(user_name, 50, "WhatsApp fiş tarama", data=data)
                # Admin bildirimi
                for ukey, udata_info in PHONE_DIRECTORY.items():
                    if udata_info.get("yetki") == "admin" and udata_info["ad"] != user_name:
                        add_notification(udata_info["ad"],
                            f"📋 {user_name}: {bekleyen['Firma']} ₺{bekleyen['Tutar']:,.0f} ({odeme_turu_label(odeme_secim)})",
                            "info", data=data)
                save_data(data)
                msg.body(
                    f"✅ *Fiş kaydedildi!*\n"
                    f"🏢 {bekleyen['Firma']} — {bekleyen['Tutar']:,.0f} ₺\n"
                    f"💳 Ödeme: *{odeme_turu_label(odeme_secim)}*\n"
                    f"{'💵 Harcırah kasanızdan düşülecek' if odeme_secim == 'harcirah' else '🏦 Genel merkezden düşülecek'}\n"
                    f"📨 Yönetici onayına gönderildi.\n"
                    f"🔖 `{bekleyen['ID']}`"
                )
            else:
                save_data(data)
                msg.body("⚠️ Bekleyen fiş verisi bulunamadı. Lütfen fişi tekrar gönderin.")
            return _reply()
        else:
            msg.body("⚠️ Lütfen ödeme türünü belirtin:\n\n*1* veya *harcırah* → Harcırahtan düşülsün\n*2* veya *şirket* → Şirket kartından düşülsün")
            return _reply()

    # ══════════════════════════════════════════
    # 📍 KONUM MESAJI
    # ══════════════════════════════════════════
    if is_location:
        try:
            lat = float(wa_lat); lon = float(wa_lon)
            yanit = konum_isle(lat, lon, user_name, data)
            us.pop(KONUM_BEKLE_FLAG, None); save_data(data)
        except Exception as _ke:
            yanit = f"📍 Konum alındı ama işlenemedi: {_ke}"
        msg.body(yanit)
        return _reply()

    # ══════════════════════════════════════════
    # 🤖 KONUŞMALI AI MODU
    # ══════════════════════════════════════════
    if us.get(AI_CHAT_FLAG) and not num_media:
        if mesaj_lower in AI_CHAT_EXIT:
            us.pop(AI_CHAT_FLAG, None); us.pop(AI_CHAT_HISTORY, None); save_data(data)
            msg.body("👋 Sohbet modu kapatıldı. İstediğin zaman tekrar *sohbet* yaz!")
            return _reply()
        yanit = konusmali_ai_yanit(user_name, incoming_msg, data, us)
        save_data(data); msg.body(f"🤖 {yanit}")
        return _reply()

    # ── KOMUTLAR ────────────────────────────────────────────────

    if mesaj_lower in ["yardım", "help", "menü", "menu", "?"]:
        seviye = seviye_hesapla(data["fis_sayaci"].get(user_name, 0))
        rozetler = data["rozetler"].get(user_name, [])
        rozet_str = " ".join([ROZETLER[r]["emoji"] for r in rozetler]) if rozetler else "henüz yok"
        yetki_str = "👑 Yönetici" if is_admin else "👤 Personel"
        msg.body(
            f"🤖 *STINGA PRO v17*\n"
            f"{user_info['emoji']} {user_name} | {yetki_str} | {seviye}\n"
            f"🏅 Rozetler: {rozet_str}\n{'─'*28}\n"
            f"📷 Fiş fotoğrafı gönder → AI analiz\n"
            f"   💵 *harcırah* + fiş → Harcırahtan düşülür\n"
            f"   🏦 *şirket* + fiş → Şirket kartından düşülür\n"
            f"   _(ödeme türü belirtilmezse sorulur)_\n"
            f"📦 Birden fazla fotoğraf → Çoklu fiş işle\n"
            f"📍 Konum pini → Son fişe bağla\n"
            f"🤖 *sohbet* → AI asistanınla konuş\n{'─'*28}\n"
            f"📊 *özet* | 🏆 *sıralama* | 🔮 *kehane*\n"
            f"🧠 *profil* | 💰 *bakiye* | 📋 *son5*\n"
            f"🔍 *ara [kelime]* | ❓ *soru [metin]*\n"
            f"💱 *döviz [miktar] [KOD]* | 🏅 *rozetler*\n"
            f"🎭 *karakter [dedektif/koc/muhaseci/yoda]*"
        )
        return _reply()

    if mesaj_lower == "özet":
        bu_ay = datetime.now().strftime("%Y-%m")
        ay_fis = [e for e in data["expenses"] if e["Kullanıcı"] == user_name and e.get("Tarih","").startswith(bu_ay)]
        toplam = sum(e["Tutar"] for e in ay_fis)
        cat_bd = defaultdict(float)
        for e in ay_fis: cat_bd[e.get("Kategori","diger")] += e["Tutar"]
        cat_str = "\n".join(f"  {k}: {v:,.0f} ₺" for k, v in sorted(cat_bd.items(), key=lambda x: -x[1]))
        harcirah_keys = ("harcirah","harcırah","harcirahtan dus","harcırahtan düş","harcırahtan düş (nakit / kişisel kart)","nakit","kisisel")
        sirket_keys = ("sirket_karti","sirket karti","kredi_karti","kredi kartı","şirket","sirket")
        harcirah_top = sum(e["Tutar"] for e in ay_fis if str(e.get("Odeme_Turu","")).lower().strip() in harcirah_keys)
        sirket_top = sum(e["Tutar"] for e in ay_fis if str(e.get("Odeme_Turu","")).lower().strip() in sirket_keys)
        kehane = harcama_kehaneti(user_name, data)
        msg.body(
            f"📊 *{datetime.now().strftime('%B %Y')} Özeti*\n{'─'*28}\n"
            f"💰 Toplam: *{toplam:,.0f} ₺*\n🧾 Fiş: {len(ay_fis)}\n\n"
            f"📁 Kategoriler:\n{cat_str}\n\n"
            f"💳 *Ödeme Dağılımı:*\n  💵 Harcırah: {harcirah_top:,.0f} ₺\n  🏦 Şirket Kartı: {sirket_top:,.0f} ₺\n\n"
            f"📉 Bütçe: {butce_durumu_str(user_name, data)}\n\n" + (kehane if kehane else "")
        )
        return _reply()

    if mesaj_lower == "sıralama":
        msg.body(f"🏆 *Ekip Harcama Sıralaması*\n{'─'*28}\n{ekip_siralaması(data)}")
        return _reply()

    if mesaj_lower in ["kehane", "kehanet", "tahmin"]:
        kehane = harcama_kehaneti(user_name, data)
        msg.body(f"🔮 *Harcama Kehaneti*\n{'─'*28}\n{kehane}" if kehane else "🔮 Bütçen güvende! 💚")
        return _reply()

    if mesaj_lower == "profil":
        profil = psikolojik_profil(user_name, data)
        msg.body(f"🧠 *Harcama Psikolojin*\n{'─'*28}\n{profil}" if profil else "🧠 Profil için en az 3 fiş gerekiyor!")
        return _reply()

    if mesaj_lower.startswith("karakter "):
        mod = incoming_msg[9:].strip().lower()
        gecerli = ["dedektif", "koc", "muhaseci", "yoda", "hemsire"]
        if mod in gecerli:
            data["karakter_modu"][user_name] = mod; save_data(data)
            mod_emoji = {"dedektif": "🕵️", "koc": "💪", "muhaseci": "📒", "yoda": "🌟", "hemsire": "💚"}
            msg.body(f"{mod_emoji.get(mod,'🎭')} Karakter modu *{mod}* aktif!")
        else: msg.body(f"❌ Geçersiz mod. Seçenekler: dedektif / koc / muhaseci / yoda / hemsire")
        return _reply()

    if mesaj_lower == "rozetler":
        kazanilan = data["rozetler"].get(user_name, [])
        if not kazanilan: msg.body("🏅 Henüz rozet kazanmadın!")
        else:
            satirlar = [f"{ROZETLER[r]['emoji']} *{ROZETLER[r]['ad']}*\n   {ROZETLER[r]['aciklama']}" for r in kazanilan if r in ROZETLER]
            msg.body(f"🏅 *Rozetlerin*\n{'─'*28}\n" + "\n".join(satirlar))
        return _reply()

    if mesaj_lower == "bakiye":
        bakiye = data["wallets"].get(user_name, 0)
        limit = data.get("user_limits", {}).get(user_name, user_info.get("limit", 0))
        msg.body(f"💳 *Cüzdan*\nBakiye: *{bakiye:,.0f} ₺*\nLimit: {limit:,.0f} ₺")
        return _reply()

    if mesaj_lower == "son5":
        son5 = [e for e in data["expenses"] if e["Kullanıcı"] == user_name][-5:]
        if not son5: msg.body("Henüz harcama yok.")
        else:
            satirlar = [f"🏢 {e['Firma']} — {e['Tutar']:,.0f} ₺ ({e['Tarih']}) [{e.get('Durum','?')}] {odeme_turu_label(e.get('Odeme_Turu',''))}" for e in reversed(son5)]
            msg.body("📋 *Son 5 Harcama:*\n" + "\n".join(satirlar))
        return _reply()

    doviz_match = re.match(r"döviz\s+([\d.,]+)\s+([a-zA-Z]{3})", incoming_msg, re.IGNORECASE)
    if doviz_match:
        try:
            miktar = float(doviz_match.group(1).replace(",",".")); kod = doviz_match.group(2).upper()
            r = requests.get(DOVIZ_API_URL, timeout=5).json(); kur = r["rates"].get(kod)
            if kur: msg.body(f"💱 {miktar:,.2f} {kod} = *{miktar/kur:,.2f} ₺*\n(1 {kod} = {1/kur:.4f} ₺)")
            else: msg.body(f"❌ '{kod}' bulunamadı.")
        except Exception as e: msg.body(f"❌ Döviz hatası: {e}")
        return _reply()

    if mesaj_lower.startswith("soru "):
        msg.body(f"🧠 *AI Yanıtı:*\n{nl_sorgu(incoming_msg[5:].strip(), user_name, data)}")
        return _reply()

    if mesaj_lower in AI_CHAT_TRIGGER:
        us[AI_CHAT_FLAG] = True; us[AI_CHAT_HISTORY] = []; save_data(data)
        msg.body(f"🤖 *Stinga AI Sohbet Modu Aktif!*\n{'─'*28}\nHarcamaların hakkında her şeyi sorabilirsin.\n_Çıkmak için: çıkış_")
        return _reply()

    if mesaj_lower in ["konum", "konum ekle", "📍"]:
        son_fisler = [e for e in data["expenses"] if e["Kullanıcı"] == user_name and not e.get("Konum")]
        if not son_fisler: msg.body("📍 Konum eklenecek bekleyen fiş yok.")
        else:
            son = son_fisler[-1]; us[KONUM_BEKLE_FLAG] = True; save_data(data)
            msg.body(f"📍 *Konum Bağlama*\nSon fişin: *{son.get('Firma','?')}* — {son.get('Tutar',0):,.0f}₺\n\nWhatsApp'tan konum pini gönder!")
        return _reply()

    if mesaj_lower.startswith("ara "):
        kelime = incoming_msg[4:].strip().lower()
        havuz = data["expenses"] if is_admin else [e for e in data["expenses"] if e["Kullanıcı"] == user_name]
        sonuclar = [e for e in havuz if kelime in e.get("Firma","").lower()]
        if not sonuclar: msg.body(f"🔍 '{kelime}' için sonuç yok.")
        else:
            toplam = sum(e["Tutar"] for e in sonuclar)
            satirlar = [f"• {e['Firma']} — {e['Tutar']:,.0f} ₺ ({e['Tarih']})" for e in sonuclar[-10:]]
            msg.body(f"🔍 *'{kelime}'* → {len(sonuclar)} fiş | {toplam:,.0f} ₺\n\n" + "\n".join(satirlar))
        return _reply()

    # ── FİŞ ANALİZİ ─────────────────────────────────────────────
    if num_media > 0:
        # ── ÇOKLU FİŞ
        if num_media >= 2:
            # Twilio'da birden fazla görsel MediaUrl0, MediaUrl1 ... şeklinde gelir
            _twilio_urls = []
            for _i in range(min(num_media, 5)):
                _u = request.form.get(f"MediaUrl{_i}", "")
                if _u: _twilio_urls.append(_u)
            def coklu_gonder():
                _data = load_data()
                _data.setdefault("user_states", {}).setdefault(user_name, {})
                yanit = coklu_fis_isle(sender_phone, user_name, user_info, num_media, _data,
                                       twilio_media_urls=_twilio_urls, mesaj_odeme_turu=mesaj_odeme_turu)
                send_whatsapp(sender_phone, yanit)
            import threading as _t2
            _t2.Thread(target=coklu_gonder, daemon=True).start()
            odeme_str = f"\n💳 Ödeme türü: *{odeme_turu_label(mesaj_odeme_turu)}*" if mesaj_odeme_turu else "\n⚠️ _Ödeme türü belirtilmedi — AI'dan tespit edilecek_"
            send_whatsapp(sender_phone, f"📦 *{num_media} fiş fotoğrafı alındı!*\n⚙️ Tümü işleniyor...{odeme_str}\n⌛ Sonuçlar birkaç saniye içinde gelecek.")
            return jsonify({"status": "ok"}), 200

        # ── TEKİL FİŞ ───────────────────────────────────────────────
        # Twilio doğrudan MediaUrl0 ile gelir
        print(f"📸 Twilio Media URL: {media_url}", flush=True)

        def analiz_et_gonder():
            try:
                    data = load_data()
                    # ── Twilio MediaUrl'den görsel indir ──
                    raw_bytes = None
                    try:
                        if media_url:
                            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
                            auth_token  = os.getenv("TWILIO_AUTH_TOKEN")
                            r = requests.get(media_url, auth=(account_sid, auth_token), timeout=30)
                            r.raise_for_status()
                            raw_bytes = r.content
                            print(f"✅ Twilio media indirildi: {len(raw_bytes)} bytes", flush=True)
                    except Exception as _tw_err:
                        print(f"Twilio media indirme hatası: {_tw_err}", flush=True)

                    if not raw_bytes or len(raw_bytes) < 500:
                        print(f"❌ Görsel indirilemedi! URL: {media_url}", flush=True)
                        send_whatsapp(sender_phone, "❌ Fiş görseli indirilemedi. Lütfen tekrar deneyin veya farklı bir fotoğraf gönderin.")
                        return

                    print(f"📸 İndirme başarılı: {len(raw_bytes)} bytes", flush=True)

                    img_hash = gorsel_hash(raw_bytes)
                    if img_hash in data["duplicate_hashes"]:
                        send_whatsapp(sender_phone, "⚠️ *Mükerrer Fiş!* Bu fişi daha önce sisteme girdiniz.")
                        return

                    # PIL ile aç — hata verirse kullanıcıya bildir
                    try:
                        image = Image.open(BytesIO(raw_bytes))
                        image.verify()  # Geçerli görsel mi kontrol et
                        image = Image.open(BytesIO(raw_bytes))  # verify sonrası tekrar aç
                    except Exception as _img_err:
                        print(f"PIL görsel açma hatası: {_img_err}", flush=True)
                        send_whatsapp(sender_phone, "❌ Gönderilen dosya geçerli bir görsel değil. Lütfen fiş *fotoğrafı* gönderin (PDF, video vb. desteklenmez).")
                        return
                    bugun = datetime.now().strftime("%Y-%m-%d")
                    prompt = (
                        f"Sen Stinga Enerji şirketinin mali denetçisisin. Fişi dikkatli analiz et ve SADECE JSON döndür.\n\n"
                        f"ÖNEMLİ: Bugün {bugun}. Fişte yazan tarihi oku (DD-MM-YYYY formatini YYYY-MM-DD'ye çevir).\n\n"
                        "=== KATEGORİ / FİŞ TÜRÜ BELİRLEME (ÇOK DİKKATLİ OL) ===\n"
                        '- Benzin istasyonu, akaryakıt, OPET, Shell, BP, Total, motorin, benzin: fis_turu="akaryakıt"\n'
                        '- Restoran, lokanta, kafe, yemek: fis_turu="restoran"\n'
                        '- Market, süpermarket (Migros, BİM, A101): fis_turu="market"\n'
                        '- Otel, konaklama: fis_turu="otel"\n'
                        'DİKKAT: "OPET MARKET" bir AKARYAKIT istasyonudur, market DEĞİLDİR. Akaryakıt satan her yer fis_turu="akaryakıt" olmalıdır.\n\n'
                        "=== KİŞİSEL GİDER TESPİTİ (ÇOK ÖNEMLİ) ===\n"
                        "Fişte şu ürünler varsa bunları kisisel_giderler listesine ekle ve risk_skoru artır:\n"
                        "- Sigara, tütün, elektronik sigara: +25 risk\n"
                        "- Çikolata, şekerleme, cips, gofret: +10 risk\n"
                        "- Kola, gazlı içecek, enerji içeceği, bira, alkol: +15 risk\n"
                        "- Sakız, dondurma: +5 risk\n"
                        "- Kişisel bakım (şampuan, deodorant, parfüm): +10 risk\n\n"
                        "=== RİSK SKORU ===\n"
                        "- Temel risk: yakıt/yemek fişi=2, diğer=5\n"
                        "- Kişisel gider varsa: her biri için yukarıdaki risk eklensin\n"
                        "- Fatura net okunmuyorsa: +15\n"
                        "- Gece 22:00-06:00 arası fiş: +10\n"
                        "- Gelecek tarihli fiş: +30\n\n"
                        "=== ADRES & ŞEHİR (YENİ — ÇOK ÖNEMLİ) ===\n"
                        "Fişte firma adresi, ilçe, il veya şehir bilgisi varsa mutlaka çıkar.\n"
                        '- adres: fişte yazan tam adres (örn: "Atatürk Cad. No:5 Yenimahalle")\n'
                        '- sehir: sadece il/şehir adı (örn: "Ankara", "İstanbul", "İzmir")\n'
                        "Adres veya şehir bilgisi yoksa boş string bırak.\n\n"
                        '{"firma":"?","tarih":"YYYY-MM-DD","toplam_tutar":0.0,"kdv_tutari":0.0,'
                        '"odeme_yontemi":"nakit|kredi_karti|havale","kalemler":[{"aciklama":"...","tutar":0.0}],'
                        '"kisisel_giderler":[{"urun":"sigara","tutar":25.0}],'
                        '"adres":"","sehir":"",'
                        '"para_birimi":"TRY","risk_skoru":0,"risk_nedenleri":["..."],'
                        '"audit_notu":"1 cümle kısa mali özet, kişisel gider varsa mutlaka belirt",'
                        '"sahte_mi":false,"sahtelik_nedeni":"","gorsel_kalitesi":"iyi|orta|kotu",'
                        '"fis_turu":"restoran|market|akaryakıt|otel|diger","ilginc_detay":"dikkat çeken şey"}'
                    )

                    ai_res = client.models.generate_content(model=MODEL_NAME, contents=[prompt, image])
                    raw_text = ai_res.text
                    json_text = re.sub(r"```json?|```", "", raw_text).strip()
                    _m = re.search(r'\{.*\}', json_text, re.DOTALL)
                    if _m: json_text = _m.group()
                    try: fis = json.loads(json_text)
                    except json.JSONDecodeError:
                        retry_prompt = f"Sadece JSON döndür:\n{prompt}"
                        ai_res2 = client.models.generate_content(model=MODEL_NAME, contents=[retry_prompt, image])
                        json_text2 = re.sub(r"```json?|```", "", ai_res2.text).strip()
                        _m2 = re.search(r'\{.*\}', json_text2, re.DOTALL)
                        fis = json.loads(_m2.group() if _m2 else json_text2)

                    # Tarih doğrulama
                    fis_tarihi = fis.get("tarih", "")
                    try:
                        from datetime import datetime as _dt
                        fis_dt = _dt.strptime(fis_tarihi, "%Y-%m-%d")
                        bugun_dt = _dt.now().replace(hour=0, minute=0, second=0, microsecond=0)
                        if fis_dt > bugun_dt:
                            fis["risk_skoru"] = min(100, int(fis.get("risk_skoru", 0)) + 30)
                            fis.setdefault("risk_nedenleri", []).append("⚠️ Gelecek tarihli fiş")
                    except: pass

                    # Para birimi dönüşümü
                    tutar_try = float(fis.get("toplam_tutar", 0))
                    para_birimi = fis.get("para_birimi", "TRY")
                    if para_birimi != "TRY":
                        try:
                            r = requests.get(DOVIZ_API_URL, timeout=5).json()
                            kur = r["rates"].get(para_birimi)
                            if kur: tutar_try = tutar_try / kur
                        except: pass

                    sahtelik = derin_sahtelik_analizi(fis, image)
                    anomaliler = anomali_tespit(user_name, tutar_try, data)
                    kategori = kategori_tespit(fis.get("firma", ""), fis.get("fis_turu", ""))

                    # ══════════════════════════════════════════════════
                    # 🧠 YENİ: KONUM & ZAMAN ZEKASI (3 Özellik)
                    # ══════════════════════════════════════════════════

                    mesaj_zamani = datetime.now()

                    # Fişin adres/şehir bilgisini AI'dan çıkarmaya çalış
                    # AI prompt'unda adres yoksa firma adından tahmin et
                    fis_adresi_ham = fis.get("adres", "") or ""
                    fis_sehri_ham  = fis.get("sehir", "") or fis.get("il", "")

                    # Şehir bulunamadıysa firma adından tahmin et (basit kelime eşleştirme)
                    if not fis_sehri_ham and fis_adresi_ham:
                        _adres_lower = fis_adresi_ham.lower()
                        _sehirler = ["ankara","istanbul","izmir","bursa","antalya","adana",
                                     "konya","gaziantep","mersin","kayseri","diyarbakır",
                                     "trabzon","erzurum","samsun","eskişehir","denizli"]
                        for _s in _sehirler:
                            if _s in _adres_lower:
                                fis_sehri_ham = _s.capitalize()
                                break

                    # ── ÖZELLİK 1: Konum Çelişkisi ──────────────────
                    konum_celiski = konum_celiskisi_kontrol(
                        fis_adresi=fis_adresi_ham,
                        fis_sehri=fis_sehri_ham,
                        user_name=user_name,
                        mesaj_zamani=mesaj_zamani,
                        fis_tarihi=fis.get("tarih", ""),
                        data=data
                    )

                    # ── ÖZELLİK 2: Zaman-Mekan İmkansızlığı ─────────
                    zaman_celiski = zaman_mekan_imkansizlik_kontrol(
                        fis_adresi=fis_adresi_ham,
                        fis_sehri=fis_sehri_ham,
                        fis_tarihi=fis.get("tarih", datetime.now().strftime("%Y-%m-%d")),
                        fis_saati_tahmini="",
                        user_name=user_name,
                        data=data
                    )

                    # ── ÖZELLİK 3: Fiş Yaşı Sensörü ─────────────────
                    yas_kontrol = fis_yasi_kontrol(raw_bytes, mesaj_zamani)

                    # Risk puanına ekle
                    _ek_risk = (
                        konum_celiski.get("risk_artisi", 0) +
                        zaman_celiski.get("risk_artisi", 0) +
                        yas_kontrol.get("risk_artisi", 0)
                    )
                    if _ek_risk > 0:
                        fis["risk_skoru"] = min(100, int(fis.get("risk_skoru", 0)) + _ek_risk)

                    # Uyarı mesajlarını birleştir
                    _zaman_konum_uyarilari = []
                    if konum_celiski.get("celiski") and konum_celiski.get("uyari_mesaji"):
                        _zaman_konum_uyarilari.append(konum_celiski["uyari_mesaji"])
                    if zaman_celiski.get("imkansiz") and zaman_celiski.get("uyari_mesaji"):
                        _zaman_konum_uyarilari.append(zaman_celiski["uyari_mesaji"])
                    if yas_kontrol.get("yasli") and yas_kontrol.get("uyari_mesaji"):
                        _zaman_konum_uyarilari.append(yas_kontrol["uyari_mesaji"])

                    _zaman_konum_str = ("\n\n" + "\n\n".join(_zaman_konum_uyarilari)) if _zaman_konum_uyarilari else ""

                    # Fişe metadata ekle (dashboard'da görünsün)
                    if fis_sehri_ham:
                        fis["_tespit_sehri"] = fis_sehri_ham
                    if yas_kontrol.get("cekme_zamani"):
                        fis["_cekme_zamani"] = yas_kontrol["cekme_zamani"]
                        fis["_gun_farki"] = yas_kontrol.get("gun_farki", 0)
                    # ══════════════════════════════════════════════════
                    karakter = data.get("karakter_modu", {}).get(user_name, random.choice(["koc", "dedektif", "muhaseci"]))
                    fis["kategori"] = kategori

                    # ── Kişisel gider tespiti ve risk artışı ──
                    kisisel_giderler = fis.get("kisisel_giderler", [])
                    kisisel_uyari = ""
                    if kisisel_giderler:
                        _kg_listesi = ", ".join([f"{kg.get('urun','?')} (₺{kg.get('tutar',0):.0f})" for kg in kisisel_giderler])
                        kisisel_uyari = f"\n\n🚨 *KİŞİSEL GİDER TESPİTİ:*\n{_kg_listesi}\n⚠️ Bu ürünler şirket gideri olarak kabul edilmez!"
                        # Risk skorunu artır
                        _mevcut_risk = int(fis.get("risk_skoru", 0))
                        _ek_risk = len(kisisel_giderler) * 15
                        fis["risk_skoru"] = min(100, _mevcut_risk + _ek_risk)

                    yorum = yaratici_yorum(fis, user_name, karakter)

                    # ── Şenol Bey otomatik onay + esprili mesaj ──
                    _is_senol = user_name in ("Şenol Özyaman", "Şenol Faik Özyaman", "senol")
                    _senol_mesaj = ""

                    data.setdefault("fis_sayaci", {})
                    data.setdefault("expenses", [])
                    data.setdefault("duplicate_hashes", [])
                    data.setdefault("anomaly_log", [])
                    data.setdefault("xp", {})
                    data.setdefault("notifications", [])
                    data.setdefault("rozetler", {})

                    if sahtelik["sahte_mi"] or sahtelik["guvensizlik_skoru"] >= 70:
                        durum = "Sahte Şüphesi"
                    else:
                        durum = "Onay Bekliyor"

                    # ── Şenol Bey: Otomatik onay ──
                    if _is_senol and durum == "Onay Bekliyor":
                        durum = "Onaylandı"
                        _senol_espri_listesi = [
                            "Sizi sizden başka kim onaylayabilir Şenol Bey? 😄 Fişiniz direkt kaydedildi!",
                            "Genel Müdür'ün fişi onay mı bekler? Tabii ki hayır! ✅ Otomatik onaylandı.",
                            "Şenol Bey, fişiniz VIP muamelesi gördü — anında onay! 🎩",
                            "Patron fişi yollamış, kim reddetmeye cesaret edebilir? 😎 Kayıt tamam!",
                            "Şenol Bey bir fiş gönderdi, sistem saygıyla selam durdu ve onayladı! 🫡",
                            "Bu fiş o kadar yetkiliydi ki kendini onayladı! 😁 Kayıtta Şenol Bey.",
                            "Genel Müdür konuştu, sistem dinledi: ONAYLI! ✨",
                            "Şenol Bey'in fişi geldi — kırmızı halı serildi, onay damgası basıldı! 🎖️",
                        ]
                        # Fiş kategorisine göre akıllı sağlık mesajları
                        _fis_turu = fis.get("fis_turu", kategori).lower()
                        if "restoran" in _fis_turu or "yemek" in _fis_turu or "market" in _fis_turu:
                            _senol_saglik_listesi = [
                                "🥗 Diyaliz hastalarının potasyum ve fosfor alımına dikkat etmesi gerekiyor — yemek seçimlerinize özen gösterin Şenol Bey!",
                                "🍽️ Yemek fişi gördüm — diyaliz diyetinize uygun seçimler yaptığınızı umuyorum Şenol Bey!",
                                "🧂 Tuz kısıtlaması önemli — bu restoranın yemeklerinin tuzu konusunda dikkatli olun Şenol Bey!",
                                "💧 Yemek sonrası sıvı alımınıza dikkat etmeyi unutmayın Şenol Bey!",
                            ]
                        elif "akaryakıt" in _fis_turu or "akaryakit" in _fis_turu:
                            _senol_saglik_listesi = [
                                "🚗 Uzun yolculuklar yorucu olabiliyor — molalar vermeyi unutmayın Şenol Bey!",
                                "⛽ Seyahatteyseniz, diyaliz randevularınızı aksatmamaya dikkat edin Şenol Bey!",
                                "🛣️ Yolda kendinize iyi bakın, güvenli sürüşler Şenol Bey!",
                            ]
                        elif "otel" in _fis_turu or "konaklama" in _fis_turu:
                            _senol_saglik_listesi = [
                                "🏨 Seyahatte diyaliz merkezi ayarlamanız gerekiyorsa önceden planlama yapın Şenol Bey!",
                                "🌙 İyi dinlenmeler Şenol Bey, uyku sağlığın temelidir!",
                                "✈️ Seyahatte de düzeninizi bozmamaya çalışın Şenol Bey!",
                            ]
                        else:
                            _senol_saglik_listesi = [
                                "💚 Bugün nasılsınız Şenol Bey? Umarım enerjiniz yerindedir!",
                                "🫀 Düzenli kan basıncı kontrolünüzü ihmal etmeyin Şenol Bey!",
                                "😴 Kaliteli uyku diyaliz hastalarında iyileşmeyi destekler — iyi geceler Şenol Bey!",
                                "🏃 Hafif yürüyüşler hem moral hem sağlık için çok iyi — fırsatınız olunca deneyin!",
                                "💪 Ekibiniz size güveniyor — ama sağlığınız her şeyden önce gelir Şenol Bey!",
                            ]
                        _senol_mesaj = random.choice(_senol_espri_listesi)
                        # Her zaman kategoriye uygun sağlık mesajı ekle
                        _senol_mesaj += "\n\n💚 " + random.choice(_senol_saglik_listesi)
                        # Diyaliz günü ise özel hatırlatma ekle
                        _bugun_gun = datetime.now().weekday()
                        _diyaliz_gunleri = {1: "Salı", 3: "Perşembe", 5: "Cumartesi"}
                        if _bugun_gun in _diyaliz_gunleri:
                            _senol_mesaj += f"\n💙 Bugün {_diyaliz_gunleri[_bugun_gun]} — diyaliz günün, umarım her şey yolunda Şenol Bey!" 

                    # Thumbnail
                    import base64 as _b64mod
                    try:
                        _thumb_img = Image.open(BytesIO(raw_bytes)).convert("RGB")
                        _thumb_img.thumbnail((400, 400), Image.LANCZOS)
                        _thumb_buf = BytesIO()
                        _thumb_img.save(_thumb_buf, format="JPEG", quality=55, optimize=True)
                        _thumb_bytes = _thumb_buf.getvalue()
                        gorsel_b64_str = _b64mod.b64encode(_thumb_bytes).decode("utf-8")
                        gorsel_data_uri = f"data:image/jpeg;base64,{gorsel_b64_str}"
                    except:
                        gorsel_data_uri = ""

                    # ══ ÖDEME TÜRÜ BELİRLEME ══
                    # mesaj_odeme_turu: WhatsApp mesajından tespit edilen ödeme türü
                    # Eğer mesajda belirtilmişse doğrudan kullan,
                    # belirtilmemişse fiş verisini hazırla ve kullanıcıya sor
                    final_odeme = mesaj_odeme_turu if mesaj_odeme_turu else None

                    # Şenol Bey için ödeme türü: harcırah (kasasından düşülür) + şirkete de işlenir
                    _senol_odeme_turu = "harcirah" if _is_senol else (final_odeme if final_odeme else fis.get("odeme_yontemi", "bilinmiyor"))

                    new_expense = {
                        "ID": datetime.now().strftime("%Y%m%d%H%M%S"),
                        "Tarih": fis.get("tarih", datetime.now().strftime("%Y-%m-%d")),
                        "Yukleme_Zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Kullanıcı": user_name, "Rol": user_info["rol"],
                        "Firma": fis.get("firma", "Bilinmiyor"),
                        "Tutar": tutar_try, "KDV": float(fis.get("kdv_tutari", 0)),
                        "ParaBirimi": para_birimi,
                        "OdemeTipi": _senol_odeme_turu if _is_senol else (final_odeme if final_odeme else fis.get("odeme_yontemi", "bilinmiyor")),
                        "Odeme_Turu": _senol_odeme_turu if _is_senol else (final_odeme if final_odeme else fis.get("odeme_yontemi", "bilinmiyor")),
                        "Sirket_Gider": True,  # Her fiş şirkete de işlenir
                        "Kategori": kategori, "Durum": durum,
                        "Risk_Skoru": max(int(fis.get("risk_skoru", 0)), sahtelik["guvensizlik_skoru"]),
                        "AI_Audit": re.sub(r'<[^>]+>', '', str(fis.get("audit_notu", ""))).strip(),
                        "AI_Anomali": fis.get("anomali", False),
                        "AI_Anomali_Aciklama": fis.get("anomali_aciklamasi", ""),
                        "Kisisel_Giderler": kisisel_giderler,
                        "Anomaliler": anomaliler, "Hash": img_hash,
                        "Karakter": karakter,
                        "IlgincDetay": fis.get("ilginc_detay", ""),
                        "Proje": "Genel Merkez", "Oncelik": "Normal", "Notlar": "",
                        "Kaynak": "WhatsApp", "Dosya_Yolu": "",
                        "Gorsel_B64": gorsel_data_uri,
                        "Konum": "", "Konum_Lat": None, "Konum_Lon": None, "Sehir": fis_sehri_ham,
                        # Yeni alanlar — konum & zaman zekası
                        "Fis_Sehri": fis_sehri_ham,
                        "Cekme_Zamani": yas_kontrol.get("cekme_zamani", ""),
                        "Gun_Farki": yas_kontrol.get("gun_farki", 0),
                        "Konum_Celiski": konum_celiski.get("celiski", False),
                        "Zaman_Celiski": zaman_celiski.get("imkansiz", False),
                    }

                    # Mükerrer kontrolü (firma+tutar+tarih)
                    firma_yeni = str(fis.get("firma","")).strip().lower()
                    tutar_yeni = float(fis.get("toplam_tutar", 0))
                    tarih_yeni = fis.get("tarih", "")
                    mukerrer_fis = None
                    for e in data.get("expenses", []):
                        if (str(e.get("Firma","")).strip().lower() == firma_yeni and
                                abs(float(e.get("Tutar", 0)) - tutar_yeni) < 1.0 and
                                str(e.get("Tarih","")) == tarih_yeni):
                            mukerrer_fis = e; break
                    if mukerrer_fis:
                        send_whatsapp(sender_phone, f"⚠️ *Mükerrer Fiş!*\n{mukerrer_fis.get('Firma','?')} ₺{float(mukerrer_fis.get('Tutar',0)):,.2f} ({mukerrer_fis.get('Tarih','?')}) — {mukerrer_fis.get('Kullanıcı','?')} tarafından girilmiş.")
                        return

                    # ══ ÖDEME TÜRÜ BELİRTİLMEMİŞSE → KULLANICIYA SOR ══
                    if not final_odeme:
                        # Fişi geçici olarak user_states'e kaydet
                        data["duplicate_hashes"].append(img_hash)
                        data.setdefault("user_states", {}).setdefault(user_name, {})
                        data["user_states"][user_name][ODEME_BEKLE_FLAG] = True
                        data["user_states"][user_name][ODEME_BEKLE_DATA] = new_expense
                        save_data(data)
                        risk = max(int(fis.get("risk_skoru", 0)), sahtelik["guvensizlik_skoru"])
                        risk_emoji = "🟢" if risk < 30 else "🟡" if risk < 70 else "🔴"

                        # Şenol Bey ödeme türü sormadan devam etsin
                        if _is_senol:
                            # Şenol Bey için default: harcırah (kasasından düşülsün)
                            new_expense["OdemeTipi"] = "harcirah"
                            new_expense["Odeme_Turu"] = "harcirah"
                            data["expenses"].append(new_expense)
                            data["duplicate_hashes"].append(img_hash)
                            data["fis_sayaci"][user_name] = data["fis_sayaci"].get(user_name, 0) + 1
                            # Kasasından düş
                            mevcut_kasa = data.get("wallets", {}).get(user_name, 0)
                            data.setdefault("wallets", {})[user_name] = mevcut_kasa - tutar_try
                            add_xp(user_name, 50, "WhatsApp fiş tarama", data=data)
                            save_data(data)
                            # Diyaliz günü kontrolü (Salı=1, Perşembe=3, Cumartesi=5)
                            _bugun_gun = datetime.now().weekday()
                            _diyaliz_gunleri = {1: "Salı", 3: "Perşembe", 5: "Cumartesi"}
                            _diyaliz_uyari = ""
                            if _bugun_gun in _diyaliz_gunleri:
                                _diyaliz_uyari = f"\n\n💙 _Bugün {_diyaliz_gunleri[_bugun_gun]} — diyaliz günün, umarım iyi geçiyor Şenol Bey. Kendinize iyi bakın!_"
                            _yeni_kasa = data.get("wallets", {}).get(user_name, 0)
                            _senol_odeme_msg = (
                                f"✅ *FİŞ KAYDEDİLDİ — OTOMATİK ONAYLI* 🎩\n{'─'*22}\n"
                                f"🏢 {fis.get('firma','?')}\n"
                                f"💰 {tutar_try:,.2f} ₺\n"
                                f"📅 {fis.get('tarih','—')}\n"
                                f"🏷️ {kategori}\n"
                                f"{risk_emoji} Risk: {risk}/100\n"
                                f"💵 Harcırah kasanızdan düşüldü\n"
                                f"💳 Kasa: *{_yeni_kasa:,.0f} ₺*"
                                + kisisel_uyari
                                + _zaman_konum_str
                                + f"\n\n🎩 _{random.choice(_senol_espri_listesi)}_"
                                + f"\n💚 _{random.choice(_senol_saglik_listesi)}_"
                                + _diyaliz_uyari
                            )
                            send_whatsapp(sender_phone, _senol_odeme_msg)
                            return

                        send_whatsapp(sender_phone,
                                f"📸 *Fiş Okundu!*\n{'─'*22}\n"
                                f"🏢 {fis.get('firma','?')}\n"
                                f"💰 {tutar_try:,.2f} ₺\n"
                                f"📅 {fis.get('tarih','—')}\n"
                                f"🏷️ {kategori}\n"
                                f"{risk_emoji} Risk: {risk}/100"
                                + kisisel_uyari +
                                f"\n\n💳 *Bu harcama nasıl ödendi?*\n\n"
                                f"*1* veya *harcırah* yazın → 💵 Harcırahtan düşülsün\n"
                                f"*2* veya *şirket* yazın → 🏦 Şirket kartından düşülsün"
                            )
                        return

                    # ══ ÖDEME TÜRÜ BELLİ — DOĞRUDAN KAYDET ══
                    data["expenses"].append(new_expense)
                    data["duplicate_hashes"].append(img_hash)
                    data["fis_sayaci"][user_name] = data["fis_sayaci"].get(user_name, 0) + 1

                    if anomaliler:
                        data["anomaly_log"].append({"tarih": datetime.now().isoformat(), "kullanici": user_name, "tutar": tutar_try, "uyarilar": anomaliler})

                    proje = new_expense["Proje"]
                    if proje in data.get("budgets", {}):
                        data["budgets"][proje]["spent"] = data["budgets"][proje].get("spent", 0) + tutar_try

                    yeni_rozetler = rozet_kontrol(user_name, data, new_expense)

                    # AI espri
                    try:
                        bugun_fisler = [e for e in data["expenses"] if e["Kullanıcı"] == user_name and e.get("Tarih","") == datetime.now().strftime("%Y-%m-%d")]
                        bu_ay_fisler = [e for e in data["expenses"] if e["Kullanıcı"] == user_name and e.get("Tarih","").startswith(datetime.now().strftime("%Y-%m"))]
                        bu_ay_toplam = sum(e["Tutar"] for e in bu_ay_fisler)
                        risk = sahtelik["guvensizlik_skoru"]
                        is_senol = user_name in ("Şenol Özyaman", "Şenol Faik Özyaman")
                        if is_senol:
                            espri_prompt = f"""Sen STINGA yapay zekasısın. Şenol Faik Özyaman için hem mali hem kişisel bir not yazıyorsun.

Fiş bilgileri:
- Firma: {fis.get('firma','?')}
- Tutar: {tutar_try:.0f} TL
- Kategori: {kategori}
- Risk: {risk}/100
- Bugün fiş sayısı: {len(bugun_fisler)}
- Bu ay toplam: {bu_ay_toplam:.0f} TL

Şenol hakkında önemli bilgiler:
- Diyaliz hastası (Salı-Perşembe-Cumartesi diyaliz günleri)
- Sıvı kısıtlaması var, fazla sıvı almaması gerekiyor
- Beslenmeye dikkat etmesi gerekiyor
- Stinga ekibi ona güveniyor ve varlığına değer veriyor

Görev: 2 cümle yaz. İlk cümle fişle ilgili esprili/samimi bir yorum. İkinci cümle Şenol'a sağlığını, diyalizini, beslenmesini ya da günlük hayatını ince bir şekilde hatırlatan, asla tıbbi tavsiye vermeyen, içten ve sıcak bir hatırlatma — her seferinde farklı ve özgün olsun, klişe olmasın.
STINGA yapay zekası olarak yaz, samimi ve kişisel ol. Türkçe. Sadece yorumu yaz."""
                        else:
                            espri_prompt = (
                                f"Sen STINGA yapay zekasısın — robotik değil, gerçekten orada olan biri gibi konuşursun.\n\n"
                                f"Kullanıcı: {user_name}\n"
                                f"Firma: {fis.get('firma','?')} | Tutar: {tutar_try:.0f} TL | Kategori: {kategori}\n"
                                f"Risk: {risk}/100 | Bugün {len(bugun_fisler)}. fiş | Bu ay toplam: {bu_ay_toplam:.0f} TL\n\n"
                                "Görev: 1-2 cümle yaz.\n"
                                "- İsmiyle hitap et, ama sadece bir kez\n"
                                "- O firmaya, o tutara, o kategoriye özel bir şey söyle — genel kalıplar yok\n"
                                "- Samimi ve sıcak ol: bu kişi sahada çalışıyor, emek veriyor — bunu hissettir\n"
                                "- İlham verici ama hafif bir kapanış: 'devam', 'yolda', 'ekip' gibi temalar kullanabilirsin\n"
                                "- 1-2 emoji, doğal yere koy\n"
                                "- Türkçe. Sadece yorumu yaz."
                            )
                        ai_espri = ai_call(espri_prompt)
                    except:
                        ai_espri = "Fiş sisteme düştü, onay bekleniyor. 📋"

                    add_xp(user_name, 50, "WhatsApp fiş tarama", data=data)
                    for ukey, udata_info in PHONE_DIRECTORY.items():
                        if udata_info.get("yetki") == "admin" and udata_info["ad"] != user_name:
                            add_notification(udata_info["ad"],
                                f"📋 {user_name}: {new_expense['Firma']} ₺{tutar_try:,.0f} ({odeme_turu_label(final_odeme)})",
                                "info", data=data)
                    save_data(data)

                    # Risk skoru: AI risk + sahtelik risk'inden büyüğünü al
                    risk = max(int(fis.get("risk_skoru", 0)), sahtelik["guvensizlik_skoru"])
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
                    seviye = seviye_hesapla(data["fis_sayaci"].get(user_name, 0))
                    kasa_bakiye = data.get("wallets", {}).get(user_name, 0)

                    odeme_bilgi = odeme_turu_label(final_odeme)
                    odeme_aciklama = "💵 Harcırah kasanızdan düşülecek" if final_odeme == "harcirah" else "🏦 Genel merkezden düşülecek"

                    # Şenol Bey için farklı başlık
                    if _is_senol:
                        _baslik = f"✅ *FİŞ KAYDEDİLDİ — OTOMATİK ONAYLI* 🎩\n{'─'*13}"
                    else:
                        _baslik = f"✅ *FİŞ KAYDEDİLDİ — ONAYA GÖNDERİLDİ*\n{'─'*13}"

                    yanit = (
                        f"{_baslik}\n"
                        f"🏢 {fis.get('firma','?')}\n"
                        f"💰 {tutar_try:,.2f} ₺" + (f" ({fis['toplam_tutar']:.2f} {para_birimi})" if para_birimi != "TRY" else "") +
                        f"\n📅 {fis.get('tarih','—')}"
                        f"\n💳 *{odeme_bilgi}*"
                        f"\n   _{odeme_aciklama}_"
                        f"\n🏷️ {kategori}"
                        f"\n{risk_emoji} Risk: {risk}/100"
                        + kalemler_str + ilginc_str
                        + kisisel_uyari
                        + _zaman_konum_str
                        + f"\n\n💬 _{ai_espri}_"
                        + (f"\n\n🎩 _{_senol_mesaj}_" if _senol_mesaj else "")
                        + f"\n\n💳 Kasa: *{kasa_bakiye:,.0f} ₺*"
                        + f"\n{seviye} • #{data['fis_sayaci'].get(user_name,0)} fiş"
                        + sahte_str + anomali_str
                        + ("" if _is_senol else f"\n\n📨 Onay sonrası bildirim alacaksınız.")
                        + f"\n📍 Konum eklemek için konum pini gönder!"
                        + f"\n🔖 `{new_expense['ID']}`"
                    )
                    send_whatsapp(sender_phone, yanit)

            except json.JSONDecodeError as e:
                print(f"JSON HATA: {e}", flush=True)
                send_whatsapp(sender_phone, "❌ Fiş okunamadı. Net fotoğraf çekip tekrar deneyin.")
            except Exception as e:
                import traceback; print(f"GENEL HATA: {traceback.format_exc()}", flush=True)
                send_whatsapp(sender_phone, f"❌ Hata: {str(e)}")

        import threading
        t = threading.Thread(target=analiz_et_gonder, daemon=True)
        t.start()
        beklemeler = [
            "📡 **STİNGA YAPAY ZEKA** fişi analiz merkezine gönderdi. Lütfen bekleyin.⌛"                
        ]
        msg.body(random.choice(beklemeler))
        return _reply()

    # ── VARSAYILAN
    fis_sayisi = data["fis_sayaci"].get(user_name, 0)
    seviye = seviye_hesapla(fis_sayisi)
    msg.body(f"{user_info['emoji']} Merhaba *{user_name}*!\n{seviye}\nFiş fotoğrafı gönder veya *yardım* yaz.\n\n💡 _Fişle birlikte *harcırah* veya *şirket* yazarak ödeme türünü belirtebilirsin!_")
    return _reply()

# ─────────────────────────────────────────────
#  ENDPOINTLER
# ─────────────────────────────────────────────
@app.route("/rapor", methods=['GET'])
def rapor_endpoint():
    data = load_data()
    bu_ay = datetime.now().strftime("%Y-%m")
    ay_fis = [e for e in data["expenses"] if e.get("Tarih","").startswith(bu_ay)]
    toplam = sum(e["Tutar"] for e in ay_fis)
    k_bazli = defaultdict(float); c_bazli = defaultdict(float)
    for e in ay_fis: k_bazli[e["Kullanıcı"]] += e["Tutar"]; c_bazli[e.get("Kategori","diger")] += e["Tutar"]
    return jsonify({"ay": bu_ay, "toplam": toplam, "fis_sayisi": len(ay_fis),
        "anomali_sayisi": len(data.get("anomaly_log",[])),
        "kullanici_bazli": dict(k_bazli), "kategori_bazli": dict(c_bazli),
        "ekip_rozetleri": data.get("rozetler", {})}), 200

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
            if (e.get("Firma") == new_e.get("Firma") and abs(float(e.get("Tutar",0)) - float(new_e.get("Tutar",0))) < 1 and e.get("Tarih") == new_e.get("Tarih")):
                return jsonify({"error": "Mükerrer fiş", "duplicate": True}), 409
        if "AI_Audit" in new_e: new_e["AI_Audit"] = _deep_clean_html(str(new_e["AI_Audit"]))
        # Tüm metin alanlarından HTML tag'lerini temizle
        _text_fields = ("AI_Audit", "Notlar", "AI_Anomali_Aciklama", "IlgincDetay", "Firma")
        for _fld in _text_fields:
            if _fld in new_e and isinstance(new_e[_fld], str):
                new_e[_fld] = _deep_clean_html(new_e[_fld])
        data["expenses"].append(new_e)
        add_xp(new_e.get("Kullanıcı", ""), 50, "Dashboard fiş tarama", data=data)
        for ukey, uinfo in PHONE_DIRECTORY.items():
            if uinfo.get("yetki") == "admin" and uinfo["ad"] != new_e.get("Kullanıcı", ""):
                add_notification(uinfo["ad"],
                    f"📋 {new_e.get('Kullanıcı','?')} → {new_e.get('Proje','?')}: {new_e.get('Firma','?')} ₺{float(new_e.get('Tutar',0)):,.0f}",
                    "info", data=data)
        save_data(data)
        return jsonify({"ok": True, "ID": new_e["ID"]}), 200
    except Exception as e:
        import traceback; print(f"add-expense HATA: {traceback.format_exc()}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/update-expense", methods=["POST"])
def update_expense():
    """Mevcut bir fişin belirli alanlarını güncelle."""
    try:
        body = request.get_json(force=True) or {}
        fis_id = str(body.pop("ID", ""))
        if not fis_id:
            return jsonify({"error": "ID gerekli"}), 400
        data = load_data()
        found = False
        for e in data.get("expenses", []):
            if str(e.get("ID", "")) == fis_id:
                for k, v in body.items():
                    e[k] = v
                found = True
                break
        if not found:
            return jsonify({"error": "Fiş bulunamadı", "ID": fis_id}), 404
        save_data(data)
        return jsonify({"ok": True, "ID": fis_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/reset-wallets", methods=["GET", "POST"])
def reset_wallets():
    """Tüm wallet bakiyelerini sıfırla. Bakiyeler bundan sonra sadece ledger transferleri ile oluşur."""
    try:
        data = load_data()
        for user in data.get("wallets", {}):
            data["wallets"][user] = 0
        save_data(data)
        return jsonify({"ok": True, "wallets": data["wallets"], "mesaj": "Tüm bakiyeler sıfırlandı. /transfer ile harcırah gönderin."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/clean-all-expenses", methods=["GET", "POST"])
def clean_all_expenses():
    """Tüm expense kayıtlarındaki metin alanlarından HTML kalıntılarını temizle."""
    try:
        data = load_data()
        cleaned = 0
        text_fields = ("AI_Audit", "Notlar", "AI_Anomali_Aciklama", "IlgincDetay", "Firma")
        for exp in data.get("expenses", []):
            for fld in text_fields:
                val = exp.get(fld, "")
                if val and isinstance(val, str) and ('<' in val or '&lt;' in val or '&nbsp' in val or 'style=' in val):
                    exp[fld] = _deep_clean_html(val)
                    cleaned += 1
        save_data(data)
        return jsonify({"ok": True, "cleaned_fields": cleaned, "total_expenses": len(data.get("expenses", []))}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/healthz", methods=["GET"])
def healthz():
    exists = os.path.exists(DB_FILE); size = os.path.getsize(DB_FILE) if exists else 0
    return jsonify({"status": "ok", "db_file": DB_FILE, "db_exists": exists, "db_size_bytes": size,
        "db_dir_writable": os.access(os.path.dirname(DB_FILE) or ".", os.W_OK)}), 200

@app.route("/backup-db", methods=["GET"])
def backup_db():
    for f in [DB_FILE, DB_FILE_BACKUP2]:
        if os.path.exists(f) and os.path.getsize(f) > 10:
            from flask import send_file
            return send_file(f, as_attachment=True, download_name="stinga_backup.json")
    return jsonify({"error": "DB bulunamadı"}), 404

@app.route("/export-b64", methods=["GET"])
def export_b64():
    import base64
    data = load_data(); raw = json.dumps(data, ensure_ascii=False)
    b64 = base64.b64encode(raw.encode("utf-8")).decode("utf-8")
    return jsonify({"ok": True, "fis_sayisi": len(data.get("expenses",[])), "b64": b64,
        "kullanim": "Bu 'b64' değerini Railway → Variables → DB_JSON_B64 olarak ekle"}), 200

@app.route("/restore-db", methods=["POST"])
def restore_db():
    try:
        data = request.get_json(force=True)
        if not data or "expenses" not in data: return jsonify({"error": "Geçersiz veri"}), 400
        save_data(data)
        return jsonify({"ok": True, "expenses": len(data.get("expenses", []))}), 200
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/all-data", methods=["GET"])
def all_data_endpoint():
    data = load_data()
    return jsonify({"expenses": data.get("expenses",[]), "budgets": data.get("budgets",{}),
        "wallets": data.get("wallets",{}), "rozetler": data.get("rozetler",{}),
        "fis_sayaci": data.get("fis_sayaci",{}), "anomaly_log": data.get("anomaly_log",[]),
        "xp": data.get("xp",{}), "notifications": data.get("notifications",[]),
        "ledger": data.get("ledger",[])}), 200

@app.route("/haftalik-ozet", methods=["GET"])
def haftalik_ozet():
    data = load_data(); bu_ay = datetime.now().strftime("%Y-%m")
    for phone, info in PHONE_DIRECTORY.items():
        user = info["ad"]
        ay_fis = [e for e in data["expenses"] if e["Kullanıcı"] == user and e.get("Tarih","").startswith(bu_ay)]
        toplam = sum(e["Tutar"] for e in ay_fis)
        butce = data.get("user_limits", {}).get(user, info.get("limit", 0))
        oran = (toplam / butce * 100) if butce > 0 else 0
        try:
            send_whatsapp(phone, f"📊 *Haftalık Özet — {user}*\n{'─'*28}\n💰 Bu ay: {toplam:,.0f} ₺\n📉 Bütçe: %{oran:.1f}\n🧾 Fiş: {len(ay_fis)}\n{butce_durumu_str(user, data)}")
        except Exception as e: print(f"Haftalık özet hatası ({user}): {e}", flush=True)
    return jsonify({"status": "ok", "gonderilen": len(PHONE_DIRECTORY)}), 200

@app.route("/approve", methods=['POST'])
def approve_endpoint():
    try:
        body = request.get_json(force=True) or {}
        fis_id = str(body.get("ID", "")); action = body.get("action", "approve"); approver = body.get("approver", "admin")
        if not fis_id: return jsonify({"error": "ID gerekli"}), 400
        data = load_data(); found = False; kullanici = ""; tutar = 0.0; firma = ""; odeme_turu_fis = ""
        for e in data.get("expenses", []):
            if str(e.get("ID", "")) == fis_id:
                found = True; kullanici = e.get("Kullanıcı",""); tutar = float(e.get("Tutar",0))
                firma = e.get("Firma","?"); odeme_turu_fis = e.get("Odeme_Turu", e.get("OdemeTipi", ""))
                if action == "approve": e["Durum"] = "Onaylandı"; e["Onaylayan"] = approver
                else: e["Durum"] = "Reddedildi"; e["Reddeden"] = approver
                break
        if not found: return jsonify({"error": "Fiş bulunamadı", "ID": fis_id}), 404

        if action == "approve":
            # Ödeme türüne göre kasadan düş
            odeme_lower = str(odeme_turu_fis).lower().strip()
            harcirah_keys = ("harcirah","harcırah","harcirahtan dus","harcırahtan düş","nakit","kisisel",
                           "harcırahtan düş (nakit / kişisel kart)")
            if odeme_lower in harcirah_keys:
                # Harcırah → personel kasasından düş
                mevcut = data.get("wallets", {}).get(kullanici, 0)
                data.setdefault("wallets", {})[kullanici] = mevcut - tutar  # Negatife gidebilir (borçlanma)
            # Şirket kartı → kasadan düşülmez, genel merkezden düşülür
            add_xp(kullanici, 25, "Fiş onaylandı", data=data)
            add_notification(kullanici, f"✅ {firma} (₺{tutar:,.0f}) onaylandı — {odeme_turu_label(odeme_turu_fis)}", "success", data=data)
        else:
            add_notification(kullanici, f"❌ {firma} harcamanız reddedildi", "warning", data=data)

        # WhatsApp bildirimi
        try:
            target_phone = None
            for phone, info in PHONE_DIRECTORY.items():
                if info.get("ad") == kullanici: target_phone = phone; break
            if target_phone:
                fis_kategori = ""
                for e in data.get("expenses", []):
                    if str(e.get("ID","")) == fis_id: fis_kategori = e.get("Kategori",""); break
                bu_ay = datetime.now().strftime("%Y-%m")
                kat_fis = [e for e in data.get("expenses",[]) if e.get("Kullanıcı")==kullanici and e.get("Kategori")==fis_kategori and e.get("Tarih","").startswith(bu_ay) and e.get("Durum")=="Onaylandı"]

                if action == "approve":
                    odeme_bilgi = odeme_turu_label(odeme_turu_fis)
                    is_senol_onay = ("şenol" in kullanici.lower() or "senol" in kullanici.lower())
                    try:
                        if is_senol_onay:
                            onay_prompt = f"""Sen STINGA yapay zekasısın. Şenol Faik Özyaman'a onay bildirimi yazıyorsun.
Firma: {firma} | Tutar: {tutar:.0f} TL | Kategori: {fis_kategori} | Ödeme: {odeme_bilgi} | Kayıt no: {fis_id}

Şenol diyaliz hastası (Salı-Perşembe-Cumartesi). Sıvı kısıtlaması var. Ekip onu çok seviyor.

Görev: 3-4 cümle yaz.
1) İsmiyle hitap et, onaylandığını bildir, ödeme türünü belirt
2) Fişle ilgili esprili yorum
3) Son cümle: sağlığını, diyalizini veya beslenmesini ince bir şekilde hatırlat (tıbbi tavsiye verme, sıcak ve samimi ol)
Muhasebe kayıt no'yu 🔖 ile belirt. Türkçe. Sadece mesajı yaz."""
                        else:
                            onay_prompt = (
                                f"Sen STINGA yapay zekasısın — sıcak, samimi, insan gibi konuşan bir finans asistanı.\n\n"
                                f"Kullanıcı: {kullanici}\n"
                                f"Firma: {firma} | Tutar: {tutar:.0f} TL | Kategori: {fis_kategori}\n"
                                f"Ödeme türü: {odeme_bilgi} | Bu kategoride daha önce {len(kat_fis)} onaylı fiş var | Kayıt no: {fis_id}\n\n"
                                "Görev: Onay bildirimi yaz. Şu kurallara uy:\n"
                                "1) İsmiyle samimice hitap et — sanki gerçekten tanıyorsun onu\n"
                                "2) Harcamanın onaylandığını ve ödeme türünü (harcırah / şirket kartı) sade ve net belirt\n"
                                "3) O kategoriye/firmaya/tutara özel içten bir yorum yap — klişe olmasın, o kişiyle o an konuşuyormuş gibi hissettir\n"
                                "4) Kısa ama ilham verici kapanış: sahaya çıkmak, işi büyütmek, emeklerinin karşılığını almak temalarından birini seç — vaaz verme, sohbet et\n"
                                "5) Mesajın sonuna kayıt numarasını 🔖 ile ekle\n"
                                "6) 3-4 cümle, fazlası değil. Emoji kullan ama abartma — 2-3 yeterli.\n"
                                "7) Türkçe. Sadece mesajı yaz, açıklama ekleme."
                            )
                        mesaj = ai_call(onay_prompt)
                    except:
                        mesaj = f"✅ *{kullanici}*! {firma} ({tutar:,.0f} ₺) harcamanız onaylandı.\n💳 {odeme_bilgi}\n🔖 `{fis_id}`"
                else:
                    try:
                        red_prompt = f"""Sen nazik muhasebe asistanısın. {kullanici}: {firma} {tutar:.0f} TL reddedildi. Reddeden: {approver}. Nazik, 2-3 cümle. Sadece mesajı yaz."""
                        mesaj = ai_call(red_prompt)
                    except:
                        mesaj = f"❌ *{kullanici}*, {firma} ({tutar:,.0f} ₺) reddedildi. {approver} ile iletişime geçin."
                send_whatsapp(target_phone, mesaj)
        except Exception as e: print(f"WhatsApp bildirimi hatası: {e}", flush=True)

        save_data(data)
        return jsonify({"ok": True, "ID": fis_id, "action": action}), 200
    except Exception as e:
        import traceback; print(f"/approve HATA: {traceback.format_exc()}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/transfer", methods=['POST'])
def transfer_endpoint():
    try:
        body = request.get_json(force=True) or {}
        hedef = body.get("hedef",""); miktar = float(body.get("miktar",0))
        aciklama = body.get("aciklama","Harcırah"); gonderen = body.get("gonderen","admin")
        if not hedef or miktar <= 0: return jsonify({"error": "Hedef ve miktar gerekli"}), 400
        data = load_data()
        data.setdefault("wallets", {})[hedef] = data["wallets"].get(hedef, 0) + miktar
        data.setdefault("ledger", []).append({"Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Kaynak": gonderen, "Hedef": hedef, "İşlem": aciklama, "Miktar": miktar})
        add_notification(hedef, f"💰 Hesabınıza ₺{miktar:,.0f} transfer yapıldı. ({aciklama})", "success", data=data)
        add_xp(hedef, 10, "Transfer alındı", data=data); save_data(data)
        return jsonify({"ok": True, "hedef": hedef, "miktar": miktar}), 200
    except Exception as e:
        import traceback; print(f"/transfer HATA: {traceback.format_exc()}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/gorsel/<fis_id>", methods=['GET'])
def gorsel_endpoint(fis_id):
    data = load_data()
    for e in data.get("expenses", []):
        if str(e.get("ID","")) == str(fis_id):
            b64 = e.get("Gorsel_B64", "")
            if b64: return jsonify({"ok": True, "gorsel": b64}), 200
            return jsonify({"ok": False, "error": "Görsel yok"}), 404
    return jsonify({"ok": False, "error": "Fiş bulunamadı"}), 404


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
