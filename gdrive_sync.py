# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║  STINGA PRO — Google Drive Persistent Storage Module v2      ║
║  Deploy/restart sonrası veri kaybını önler.                   ║
║                                                              ║
║  Kullanım:                                                   ║
║    from gdrive_sync import drive_save, drive_load            ║
║    drive_save(data_dict)   # Her save_data() çağrısında      ║
║    data = drive_load()     # Startup'ta (load_data içinde)   ║
║                                                              ║
║  Gerekli env var'lar:                                        ║
║    GOOGLE_SERVICE_ACCOUNT_JSON  — credential JSON içeriği    ║
║    DRIVE_DB_FILE_ID             — Drive'daki dosyanın ID'si  ║
╚══════════════════════════════════════════════════════════════╝
"""

import json
import os
import io
import threading

# ── Google Drive API kurulumu ──
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

# ─────────────────────────────────────────────
#  AYARLAR
# ─────────────────────────────────────────────

# Seçenek 1: JSON dosyası olarak (geliştirme ortamında)
_CRED_FILE = os.getenv("GOOGLE_CRED_FILE", "service_account.json")

# Seçenek 2: Environment variable olarak (Railway'de önerilen)
_CRED_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")

# Google Drive'daki hedef dosyanın ID'si (ZORUNLU)
DRIVE_FILE_ID = os.getenv("DRIVE_DB_FILE_ID", "")

# Async kaydetme için lock
_DRIVE_LOCK = threading.Lock()

# ─────────────────────────────────────────────
#  SERVICE ACCOUNT BAĞLANTISI
# ─────────────────────────────────────────────
_drive_service = None

def _get_drive_service():
    """Google Drive API service objesini oluştur ve cache'le."""
    global _drive_service
    if _drive_service is not None:
        return _drive_service

    # Geniş scope — paylaşılan dosyaları okuma/yazma için gerekli
    SCOPES = ["https://www.googleapis.com/auth/drive"]

    try:
        if _CRED_JSON:
            cred_dict = json.loads(_CRED_JSON)
            credentials = service_account.Credentials.from_service_account_info(
                cred_dict, scopes=SCOPES
            )
            print("GDrive: Credential env var'dan yüklendi.", flush=True)
        elif os.path.exists(_CRED_FILE):
            credentials = service_account.Credentials.from_service_account_file(
                _CRED_FILE, scopes=SCOPES
            )
            print(f"GDrive: Credential dosyadan yüklendi ({_CRED_FILE}).", flush=True)
        else:
            print("GDrive UYARI: Credential bulunamadı! Drive sync devre dışı.", flush=True)
            return None

        _drive_service = build("drive", "v3", credentials=credentials)
        print("GDrive: Bağlantı başarılı.", flush=True)
        return _drive_service

    except Exception as e:
        print(f"GDrive HATA: Service oluşturulamadı: {e}", flush=True)
        return None


# ─────────────────────────────────────────────
#  ANA FONKSİYONLAR
# ─────────────────────────────────────────────

def drive_save(data: dict) -> bool:
    """
    Veriyi Google Drive'daki mevcut dosyaya kaydet (üzerine yaz).
    Thread-safe.
    """
    if not DRIVE_FILE_ID:
        print("GDrive UYARI: DRIVE_DB_FILE_ID tanımlı değil, kayıt atlanıyor.", flush=True)
        return False

    service = _get_drive_service()
    if not service:
        return False

    with _DRIVE_LOCK:
        try:
            json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
            media = MediaIoBaseUpload(
                io.BytesIO(json_bytes),
                mimetype="application/json",
                resumable=True
            )

            # Mevcut dosyayı güncelle — yeni dosya OLUŞTURMUYORUZ
            service.files().update(
                fileId=DRIVE_FILE_ID,
                media_body=media
            ).execute()

            print(f"GDrive: Güncellendi ({len(data.get('expenses',[]))} fiş)", flush=True)
            return True

        except Exception as e:
            print(f"GDrive KAYIT HATASI: {e}", flush=True)
            return False


def drive_load() -> dict | None:
    """
    Google Drive'dan veriyi yükle.
    Başarısız olursa None döndürür.
    """
    if not DRIVE_FILE_ID:
        print("GDrive UYARI: DRIVE_DB_FILE_ID tanımlı değil, yükleme atlanıyor.", flush=True)
        return None

    service = _get_drive_service()
    if not service:
        return None

    try:
        request_obj = service.files().get_media(fileId=DRIVE_FILE_ID)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request_obj)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        buffer.seek(0)
        raw = buffer.read().decode("utf-8").strip()

        if not raw or raw == "{}":
            print("GDrive: Dosya boş, ilk çalıştırma olabilir.", flush=True)
            return None

        data = json.loads(raw)
        fis_count = len(data.get("expenses", []))
        print(f"GDrive: Veri yüklendi ({fis_count} fiş)", flush=True)
        return data

    except Exception as e:
        print(f"GDrive YÜKLEME HATASI: {e}", flush=True)
        return None


def drive_save_async(data: dict):
    """
    Veriyi arka planda Google Drive'a kaydet.
    Ana thread'i bloklamaz.
    """
    import copy
    data_copy = copy.deepcopy(data)
    t = threading.Thread(target=drive_save, args=(data_copy,), daemon=True)
    t.start()
