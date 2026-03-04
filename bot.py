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

_startup_restore()

# ─────────────────────────────────────────────
#  YAPILANDIRMA
# ─────────────────────────────────────────────
client     = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-2.5-flash"

TWILIO_SID   = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
twilio_client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)

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
        "wallets":  {"Zeynep Özyaman": 50000, "Serkan Güzdemir": 25000, "Okan İlhan": 5000, "Şenol Özyaman": 30000},
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

def load_data_safe() -> dict:
    with _DB_LOCK:
        for try_file in [DB_FILE, DB_FILE + ".bak"]:
            if os.path.exists(try_file):
                try:
                    with open(try_file, "r", encoding="utf-8") as f: return json.load(f)
                except json.JSONDecodeError:
                    print(f"JSON BOZUK: {try_file}", flush=True); continue
        return {}

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

def kategori_tespit(firma: str) -> str:
    f = firma.lower()
    for kat, kelimeler in KATEGORILER.items():
        if any(k in f for k in kelimeler): return kat
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
    sonuc = {"sahte_mi": fis_data.get("sahte_mi", False), "guvensizlik_skoru": fis_data.get("risk_skoru", 0), "bulgular": []}
    toplam = float(fis_data.get("toplam_tutar", 0))
    kdv = float(fis_data.get("kdv_tutari", 0))
    if kdv > 0 and toplam > 0:
        beklenen_kdv_20 = toplam * 0.20 / 1.20
        beklenen_kdv_10 = toplam * 0.10 / 1.10
        if abs(kdv - beklenen_kdv_20) > 1 and abs(kdv - beklenen_kdv_10) > 1:
            sonuc["bulgular"].append("⚠️ KDV matematiksel tutarsızlık")
            sonuc["guvensizlik_skoru"] = min(100, sonuc["guvensizlik_skoru"] + 20)
    if toplam > 0 and toplam == int(toplam) and toplam % 100 == 0:
        sonuc["bulgular"].append("🔍 Şüpheli yuvarlak tutar")
        sonuc["guvensizlik_skoru"] = min(100, sonuc["guvensizlik_skoru"] + 10)
    for neden in fis_data.get("risk_nedenleri", []):
        if neden and neden != "...": sonuc["bulgular"].append(f"• {neden}")
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

def coklu_fis_isle(sender_phone, user_name, user_info, num_media, data, mesaj_odeme_turu=None):
    """Birden fazla medya: tüm görselleri sırayla işler. mesaj_odeme_turu varsa her fişe uygulanır."""
    sonuclar = []
    for i in range(min(num_media, 5)):
        media_url = request.values.get(f'MediaUrl{i}')
        if not media_url: continue
        try:
            res = requests.get(media_url, auth=(TWILIO_SID, TWILIO_TOKEN), allow_redirects=False, timeout=15)
            if res.status_code in [301, 302, 307, 308]:
                res = requests.get(res.headers.get('Location'), timeout=15)
            raw_bytes = res.content
            img_hash = gorsel_hash(raw_bytes)
            if img_hash in data["duplicate_hashes"]:
                sonuclar.append(f"⚠️ Fiş {i+1}: Mükerrer, atlandı"); continue
            image = Image.open(BytesIO(raw_bytes))
            bugun = datetime.now().strftime("%Y-%m-%d")
            prompt = f"""Fişi analiz et. Sadece JSON döndür. Bugün: {bugun}
{{"firma":"?","tarih":"YYYY-MM-DD","toplam_tutar":0.0,"kdv_tutari":0.0,
"odeme_yontemi":"nakit|kredi_karti|havale","para_birimi":"TRY",
"risk_skoru":0,"sahte_mi":false,"fis_turu":"diger","audit_notu":"kısa özet"}}"""
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
            kategori = kategori_tespit(fis.get("firma", ""))
            risk = int(fis.get("risk_skoru", 0))
            durum = "Sahte Şüphesi" if risk >= 70 or fis.get("sahte_mi") else "Onay Bekliyor"
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
            f"\n\n💰 Bugün eklenen: *{toplam_tutar:,.0f}₺*" + odeme_str + f"\n📨 Tümü onay kuyruğuna gönderildi.")

# ─────────────────────────────────────────────
#  ANA WEBHOOK
# ─────────────────────────────────────────────
@app.route("/whatsapp", methods=['POST'])
def whatsapp_webhook():
    incoming_msg  = request.values.get('Body', '').strip()
    sender_phone  = request.values.get('From', '')
    num_media     = int(request.values.get('NumMedia', 0))
    wa_lat        = request.values.get('Latitude', '')
    wa_lon        = request.values.get('Longitude', '')
    is_location   = bool(wa_lat and wa_lon)

    user_info     = PHONE_DIRECTORY.get(sender_phone, {"ad": "Bilinmeyen", "rol": "—", "limit": 0, "emoji": "👤", "yetki": "user"})
    user_name     = user_info["ad"]
    is_admin      = user_info.get("yetki") == "admin"

    resp = MessagingResponse()
    msg  = resp.message()
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
                    f"📨 Onay kuyruğuna gönderildi.\n"
                    f"🔖 `{bekleyen['ID']}`"
                )
            else:
                save_data(data)
                msg.body("⚠️ Bekleyen fiş verisi bulunamadı. Lütfen fişi tekrar gönderin.")
            return str(resp)
        else:
            msg.body("⚠️ Lütfen ödeme türünü belirtin:\n\n*1* veya *harcırah* → Harcırahtan düşülsün\n*2* veya *şirket* → Şirket kartından düşülsün")
            return str(resp)

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
        msg.body(yanit); return str(resp)

    # ══════════════════════════════════════════
    # 🤖 KONUŞMALI AI MODU
    # ══════════════════════════════════════════
    if us.get(AI_CHAT_FLAG) and not num_media:
        if mesaj_lower in AI_CHAT_EXIT:
            us.pop(AI_CHAT_FLAG, None); us.pop(AI_CHAT_HISTORY, None); save_data(data)
            msg.body("👋 Sohbet modu kapatıldı. İstediğin zaman tekrar *sohbet* yaz!")
            return str(resp)
        yanit = konusmali_ai_yanit(user_name, incoming_msg, data, us)
        save_data(data); msg.body(f"🤖 {yanit}"); return str(resp)

    # ── KOMUTLAR ────────────────────────────────────────────────

    if mesaj_lower in ["yardım", "help", "menü", "menu", "?"]:
        seviye = seviye_hesapla(data["fis_sayaci"].get(user_name, 0))
        rozetler = data["rozetler"].get(user_name, [])
        rozet_str = " ".join([ROZETLER[r]["emoji"] for r in rozetler]) if rozetler else "henüz yok"
        yetki_str = "👑 Yönetici" if is_admin else "👤 Personel"
        msg.body(
            f"🤖 *STINGA PRO v14*\n"
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
        return str(resp)

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
        return str(resp)

    if mesaj_lower == "sıralama":
        msg.body(f"🏆 *Ekip Harcama Sıralaması*\n{'─'*28}\n{ekip_siralaması(data)}"); return str(resp)

    if mesaj_lower in ["kehane", "kehanet", "tahmin"]:
        kehane = harcama_kehaneti(user_name, data)
        msg.body(f"🔮 *Harcama Kehaneti*\n{'─'*28}\n{kehane}" if kehane else "🔮 Bütçen güvende! 💚")
        return str(resp)

    if mesaj_lower == "profil":
        profil = psikolojik_profil(user_name, data)
        msg.body(f"🧠 *Harcama Psikolojin*\n{'─'*28}\n{profil}" if profil else "🧠 Profil için en az 3 fiş gerekiyor!")
        return str(resp)

    if mesaj_lower.startswith("karakter "):
        mod = incoming_msg[9:].strip().lower()
        gecerli = ["dedektif", "koc", "muhaseci", "yoda", "hemsire"]
        if mod in gecerli:
            data["karakter_modu"][user_name] = mod; save_data(data)
            mod_emoji = {"dedektif": "🕵️", "koc": "💪", "muhaseci": "📒", "yoda": "🌟", "hemsire": "💚"}
            msg.body(f"{mod_emoji.get(mod,'🎭')} Karakter modu *{mod}* aktif!")
        else: msg.body(f"❌ Geçersiz mod. Seçenekler: dedektif / koc / muhaseci / yoda / hemsire")
        return str(resp)

    if mesaj_lower == "rozetler":
        kazanilan = data["rozetler"].get(user_name, [])
        if not kazanilan: msg.body("🏅 Henüz rozet kazanmadın!")
        else:
            satirlar = [f"{ROZETLER[r]['emoji']} *{ROZETLER[r]['ad']}*\n   {ROZETLER[r]['aciklama']}" for r in kazanilan if r in ROZETLER]
            msg.body(f"🏅 *Rozetlerin*\n{'─'*28}\n" + "\n".join(satirlar))
        return str(resp)

    if mesaj_lower == "bakiye":
        bakiye = data["wallets"].get(user_name, 0)
        limit = data.get("user_limits", {}).get(user_name, user_info.get("limit", 0))
        msg.body(f"💳 *Cüzdan*\nBakiye: *{bakiye:,.0f} ₺*\nLimit: {limit:,.0f} ₺"); return str(resp)

    if mesaj_lower == "son5":
        son5 = [e for e in data["expenses"] if e["Kullanıcı"] == user_name][-5:]
        if not son5: msg.body("Henüz harcama yok.")
        else:
            satirlar = [f"🏢 {e['Firma']} — {e['Tutar']:,.0f} ₺ ({e['Tarih']}) [{e.get('Durum','?')}] {odeme_turu_label(e.get('Odeme_Turu',''))}" for e in reversed(son5)]
            msg.body("📋 *Son 5 Harcama:*\n" + "\n".join(satirlar))
        return str(resp)

    doviz_match = re.match(r"döviz\s+([\d.,]+)\s+([a-zA-Z]{3})", incoming_msg, re.IGNORECASE)
    if doviz_match:
        try:
            miktar = float(doviz_match.group(1).replace(",",".")); kod = doviz_match.group(2).upper()
            r = requests.get(DOVIZ_API_URL, timeout=5).json(); kur = r["rates"].get(kod)
            if kur: msg.body(f"💱 {miktar:,.2f} {kod} = *{miktar/kur:,.2f} ₺*\n(1 {kod} = {1/kur:.4f} ₺)")
            else: msg.body(f"❌ '{kod}' bulunamadı.")
        except Exception as e: msg.body(f"❌ Döviz hatası: {e}")
        return str(resp)

    if mesaj_lower.startswith("soru "):
        msg.body(f"🧠 *AI Yanıtı:*\n{nl_sorgu(incoming_msg[5:].strip(), user_name, data)}"); return str(resp)

    if mesaj_lower in AI_CHAT_TRIGGER:
        us[AI_CHAT_FLAG] = True; us[AI_CHAT_HISTORY] = []; save_data(data)
        msg.body(f"🤖 *Stinga AI Sohbet Modu Aktif!*\n{'─'*28}\nHarcamaların hakkında her şeyi sorabilirsin.\n_Çıkmak için: çıkış_")
        return str(resp)

    if mesaj_lower in ["konum", "konum ekle", "📍"]:
        son_fisler = [e for e in data["expenses"] if e["Kullanıcı"] == user_name and not e.get("Konum")]
        if not son_fisler: msg.body("📍 Konum eklenecek bekleyen fiş yok.")
        else:
            son = son_fisler[-1]; us[KONUM_BEKLE_FLAG] = True; save_data(data)
            msg.body(f"📍 *Konum Bağlama*\nSon fişin: *{son.get('Firma','?')}* — {son.get('Tutar',0):,.0f}₺\n\nWhatsApp'tan konum pini gönder!")
        return str(resp)

    if mesaj_lower.startswith("ara "):
        kelime = incoming_msg[4:].strip().lower()
        havuz = data["expenses"] if is_admin else [e for e in data["expenses"] if e["Kullanıcı"] == user_name]
        sonuclar = [e for e in havuz if kelime in e.get("Firma","").lower()]
        if not sonuclar: msg.body(f"🔍 '{kelime}' için sonuç yok.")
        else:
            toplam = sum(e["Tutar"] for e in sonuclar)
            satirlar = [f"• {e['Firma']} — {e['Tutar']:,.0f} ₺ ({e['Tarih']})" for e in sonuclar[-10:]]
            msg.body(f"🔍 *'{kelime}'* → {len(sonuclar)} fiş | {toplam:,.0f} ₺\n\n" + "\n".join(satirlar))
        return str(resp)

    # ── FİŞ ANALİZİ ─────────────────────────────────────────────
    if num_media > 0:
        # ── ÇOKLU FİŞ
        if num_media >= 2:
            def coklu_gonder():
                _data = load_data()
                _data.setdefault("user_states", {}).setdefault(user_name, {})
                yanit = coklu_fis_isle(sender_phone, user_name, user_info, num_media, _data, mesaj_odeme_turu)
                twilio_client.messages.create(body=yanit, from_="whatsapp:+14155238886", to=sender_phone)
            import threading as _t2
            _t2.Thread(target=coklu_gonder, daemon=True).start()
            odeme_str = f"\n💳 Ödeme türü: *{odeme_turu_label(mesaj_odeme_turu)}*" if mesaj_odeme_turu else "\n⚠️ _Ödeme türü belirtilmedi — AI'dan tespit edilecek_"
            msg.body(f"📦 *{num_media} fiş fotoğrafı alındı!*\n⚙️ Tümü işleniyor...{odeme_str}\n⌛ Sonuçlar birkaç saniye içinde gelecek.")
            return str(resp)

        # ── TEKİL FİŞ ───────────────────────────────────────────────
        media_url = request.values.get('MediaUrl0')

        def analiz_et_gonder():
            try:
                    data = load_data()
                    res = requests.get(media_url, auth=(TWILIO_SID, TWILIO_TOKEN), allow_redirects=False, timeout=15)
                    if res.status_code in [301, 302, 307, 308]:
                        res = requests.get(res.headers.get('Location'), timeout=15)
                    raw_bytes = res.content
                    img_hash = gorsel_hash(raw_bytes)
                    if img_hash in data["duplicate_hashes"]:
                        twilio_client.messages.create(
                            body="⚠️ *Mükerrer Fiş!* Bu fişi daha önce sisteme girdiniz.",
                            from_="whatsapp:+14155238886", to=sender_phone)
                        return
                    image = Image.open(BytesIO(raw_bytes))
                    bugun = datetime.now().strftime("%Y-%m-%d")
                    prompt = f"""Sen mali denetçi ve adli belge uzmanısın. Fişi analiz et ve SADECE JSON döndür.
ÖNEMLİ: Bugün {bugun}. Fişte yazan tarihi oku (DD-MM-YYYY → YYYY-MM-DD).
{{"firma":"?","tarih":"YYYY-MM-DD","toplam_tutar":0.0,"kdv_tutari":0.0,
"odeme_yontemi":"nakit|kredi_karti|havale","kalemler":[{{"aciklama":"...","tutar":0.0}}],
"para_birimi":"TRY","risk_skoru":0,"risk_nedenleri":["..."],
"audit_notu":"1 cümle kısa mali özet — HTML TAG KULLANMA",
"sahte_mi":false,"sahtelik_nedeni":"","gorsel_kalitesi":"iyi|orta|kotu",
"fis_turu":"restoran|market|akaryakıt|otel|diger","ilginc_detay":"dikkat çeken şey"}}"""

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
                    kategori = kategori_tespit(fis.get("firma", ""))
                    karakter = data.get("karakter_modu", {}).get(user_name, random.choice(["koc", "dedektif", "muhaseci"]))
                    fis["kategori"] = kategori
                    yorum = yaratici_yorum(fis, user_name, karakter)

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

                    new_expense = {
                        "ID": datetime.now().strftime("%Y%m%d%H%M%S"),
                        "Tarih": fis.get("tarih", datetime.now().strftime("%Y-%m-%d")),
                        "Yukleme_Zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Kullanıcı": user_name, "Rol": user_info["rol"],
                        "Firma": fis.get("firma", "Bilinmiyor"),
                        "Tutar": tutar_try, "KDV": float(fis.get("kdv_tutari", 0)),
                        "ParaBirimi": para_birimi,
                        "OdemeTipi": final_odeme if final_odeme else fis.get("odeme_yontemi", "bilinmiyor"),
                        "Odeme_Turu": final_odeme if final_odeme else fis.get("odeme_yontemi", "bilinmiyor"),
                        "Kategori": kategori, "Durum": durum,
                        "Risk_Skoru": sahtelik["guvensizlik_skoru"],
                        "AI_Audit": re.sub(r'<[^>]+>', '', str(fis.get("audit_notu", ""))).strip(),
                        "AI_Anomali": fis.get("anomali", False),
                        "AI_Anomali_Aciklama": fis.get("anomali_aciklamasi", ""),
                        "Anomaliler": anomaliler, "Hash": img_hash,
                        "Karakter": karakter,
                        "IlgincDetay": fis.get("ilginc_detay", ""),
                        "Proje": "Genel Merkez", "Oncelik": "Normal", "Notlar": "",
                        "Kaynak": "WhatsApp", "Dosya_Yolu": "",
                        "Gorsel_B64": gorsel_data_uri,
                        "Konum": "", "Konum_Lat": None, "Konum_Lon": None, "Sehir": "",
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
                        twilio_client.messages.create(
                            body=f"⚠️ *Mükerrer Fiş!*\n{mukerrer_fis.get('Firma','?')} ₺{float(mukerrer_fis.get('Tutar',0)):,.2f} ({mukerrer_fis.get('Tarih','?')}) — {mukerrer_fis.get('Kullanıcı','?')} tarafından girilmiş.",
                            from_="whatsapp:+14155238886", to=sender_phone)
                        return

                    # ══ ÖDEME TÜRÜ BELİRTİLMEMİŞSE → KULLANICIYA SOR ══
                    if not final_odeme:
                        # Fişi geçici olarak user_states'e kaydet
                        data["duplicate_hashes"].append(img_hash)
                        data.setdefault("user_states", {}).setdefault(user_name, {})
                        data["user_states"][user_name][ODEME_BEKLE_FLAG] = True
                        data["user_states"][user_name][ODEME_BEKLE_DATA] = new_expense
                        save_data(data)
                        risk = sahtelik["guvensizlik_skoru"]
                        risk_emoji = "🟢" if risk < 30 else "🟡" if risk < 70 else "🔴"
                        twilio_client.messages.create(
                            body=(
                                f"📸 *Fiş Okundu!*\n{'─'*22}\n"
                                f"🏢 {fis.get('firma','?')}\n"
                                f"💰 {tutar_try:,.2f} ₺\n"
                                f"📅 {fis.get('tarih','—')}\n"
                                f"🏷️ {kategori}\n"
                                f"{risk_emoji} Risk: {risk}/100\n\n"
                                f"💳 *Bu harcama nasıl ödendi?*\n\n"
                                f"*1* veya *harcırah* yazın → 💵 Harcırahtan düşülsün\n"
                                f"*2* veya *şirket* yazın → 🏦 Şirket kartından düşülsün"
                            ),
                            from_="whatsapp:+14155238886", to=sender_phone)
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
                        is_senol = (user_name == "Şenol Özyaman")
                        if is_senol:
                            espri_prompt = f"""Sen STINGA yapay zekasısın. Şenol Özyaman için not yazıyorsun.
Firma: {fis.get('firma','?')} - {tutar_try:.0f} TL - {kategori} - Bugün {len(bugun_fisler)} fiş - Bu ay {bu_ay_toplam:.0f} TL
Şenol diyaliz hastası (Salı-Perşembe-Cumartesi). 2 cümle: 1) fişle ilgili esprili yorum 2) sağlık hatırlatma. Samimi, Türkçe."""
                        else:
                            espri_prompt = f"""Sen STINGA yapay zekasısın. Kullanıcı: {user_name}
Firma: {fis.get('firma','?')} - {tutar_try:.0f} TL - {kategori} - Risk: {risk}/100 - Bugün {len(bugun_fisler)} fiş - Bu ay {bu_ay_toplam:.0f} TL
1-2 cümle Türkçe, eğlenceli, enerjik yorum. İsim kullan, klişe olma."""
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
                    seviye = seviye_hesapla(data["fis_sayaci"].get(user_name, 0))
                    kasa_bakiye = data.get("wallets", {}).get(user_name, 0)

                    odeme_bilgi = odeme_turu_label(final_odeme)
                    odeme_aciklama = "💵 Harcırah kasanızdan düşülecek" if final_odeme == "harcirah" else "🏦 Genel merkezden düşülecek"

                    yanit = (
                        f"✅ *FİŞ KAYDEDİLDİ — ONAYA GÖNDERİLDİ*\n{'─'*13}\n"
                        f"🏢 {fis.get('firma','?')}\n"
                        f"💰 {tutar_try:,.2f} ₺" + (f" ({fis['toplam_tutar']:.2f} {para_birimi})" if para_birimi != "TRY" else "") +
                        f"\n📅 {fis.get('tarih','—')}"
                        f"\n💳 *{odeme_bilgi}*"
                        f"\n   _{odeme_aciklama}_"
                        f"\n🏷️ {kategori}"
                        f"\n{risk_emoji} Risk: {risk}/100"
                        + kalemler_str + ilginc_str
                        + f"\n\n💬 _{ai_espri}_"
                        + f"\n\n💳 Kasa: *{kasa_bakiye:,.0f} ₺*"
                        + f"\n{seviye} • #{data['fis_sayaci'].get(user_name,0)} fiş"
                        + sahte_str + anomali_str
                        + f"\n\n📨 Onay sonrası bildirim alacaksınız."
                        + f"\n📍 Konum eklemek için konum pini gönder!"
                        + f"\n🔖 `{new_expense['ID']}`"
                    )
                    twilio_client.messages.create(body=yanit, from_="whatsapp:+14155238886", to=sender_phone)

            except json.JSONDecodeError as e:
                print(f"JSON HATA: {e}", flush=True)
                twilio_client.messages.create(body="❌ Fiş okunamadı. Net fotoğraf çekip tekrar deneyin.",
                    from_="whatsapp:+14155238886", to=sender_phone)
            except Exception as e:
                import traceback; print(f"GENEL HATA: {traceback.format_exc()}", flush=True)
                twilio_client.messages.create(body=f"❌ Hata: {str(e)}", from_="whatsapp:+14155238886", to=sender_phone)

        import threading
        t = threading.Thread(target=analiz_et_gonder, daemon=True)
        t.start()
        beklemeler = [
            "📡 **STİNGA YAPAY ZEKA** fişi analiz merkezine gönderdi. Lütfen bekleyin.⌛",
            "🏢 **STINGA YAPAY ZEKA** fişinizi dijital dünyaya aktarıyor. ⌛",
            "🛰️ **STINGA YAPAY ZEKA** fişi işliyor, sonuçlar yükleniyor. ⌛",
        ]
        msg.body(random.choice(beklemeler))
        return str(resp)

    # ── VARSAYILAN
    fis_sayisi = data["fis_sayaci"].get(user_name, 0)
    seviye = seviye_hesapla(fis_sayisi)
    msg.body(f"{user_info['emoji']} Merhaba *{user_name}*!\n{seviye}\nFiş fotoğrafı gönder veya *yardım* yaz.\n\n💡 _Fişle birlikte *harcırah* veya *şirket* yazarak ödeme türünü belirtebilirsin!_")
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
        if "AI_Audit" in new_e: new_e["AI_Audit"] = re.sub(r'<[^>]+>', '', str(new_e["AI_Audit"])).strip()
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
            twilio_client.messages.create(
                body=f"📊 *Haftalık Özet — {user}*\n{'─'*28}\n💰 Bu ay: {toplam:,.0f} ₺\n📉 Bütçe: %{oran:.1f}\n🧾 Fiş: {len(ay_fis)}\n{butce_durumu_str(user, data)}",
                from_="whatsapp:+14155238886", to=phone)
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
                    try:
                        onay_prompt = f"""Sen esprili muhasebe asistanısın.
Kullanıcı: {kullanici} | Firma: {firma} | Tutar: {tutar:.0f} TL | Kategori: {fis_kategori}
Ödeme: {odeme_bilgi} | Bu kategoride {len(kat_fis)} onaylı fiş | Kayıt no: {fis_id}
Onay bildirimi yaz: ismiyle hitap et, ödeme türünü belirt (harcırah mı şirket kartı mı), esprili, 3-4 cümle. Sadece mesajı yaz."""
                        mesaj = ai_call(onay_prompt)
                    except:
                        mesaj = f"✅ *{kullanici}*! {firma} ({tutar:,.0f} ₺) harcamanız onaylandı.\n💳 {odeme_bilgi}\n🔖 `{fis_id}`"
                else:
                    try:
                        red_prompt = f"""Sen nazik muhasebe asistanısın. {kullanici}: {firma} {tutar:.0f} TL reddedildi. Reddeden: {approver}. Nazik, 2-3 cümle. Sadece mesajı yaz."""
                        mesaj = ai_call(red_prompt)
                    except:
                        mesaj = f"❌ *{kullanici}*, {firma} ({tutar:,.0f} ₺) reddedildi. {approver} ile iletişime geçin."
                twilio_client.messages.create(body=mesaj, from_="whatsapp:+14155238886", to=target_phone)
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
