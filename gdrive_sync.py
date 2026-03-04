# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║  STINGA PRO — Google Drive Persistent Storage Module         ║
║  Deploy/restart sonrası veri kaybını önler.                   ║
║                                                              ║
║  Kullanım:                                                   ║
║    from gdrive_sync import drive_save, drive_load            ║
║    drive_save(data_dict)   # Her save_data() çağrısında      ║
║    data = drive_load()     # Startup'ta (load_data içinde)   ║
╚══════════════════════════════════════════════════════════════╝
"""

import json
import os
import io
import threading
import time

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

# Google Drive'da yedek dosyanın adı
DRIVE_FILENAME = os.getenv("DRIVE_DB_FILENAME", "stinga_v13_db.json")

# Google Drive klasör ID'si (opsiyonel — belirtilmezse root'a kaydeder)
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID", "")

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

    SCOPES = ["https://www.googleapis.com/auth/drive.file"]

    try:
        if _CRED_JSON:
            # Railway / production: env var'dan credential
            import json as _json
            cred_dict = _json.loads(_CRED_JSON)
            credentials = service_account.Credentials.from_service_account_info(
                cred_dict, scopes=SCOPES
            )
            print("GDrive: Credential env var'dan yüklendi.", flush=True)
        elif os.path.exists(_CRED_FILE):
            # Lokal geliştirme: dosyadan credential
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
#  YARDIMCI FONKSİYONLAR
# ─────────────────────────────────────────────

def _find_file_id(service, filename):
    """Drive'da dosyayı adına göre bul, file_id döndür."""
    try:
        query = f"name = '{filename}' and trashed = false"
        if DRIVE_FOLDER_ID:
            query += f" and '{DRIVE_FOLDER_ID}' in parents"

        results = service.files().list(
            q=query,
            spaces="drive",
            fields="files(id, name, modifiedTime)",
            orderBy="modifiedTime desc",
            pageSize=1
        ).execute()

        files = results.get("files", [])
        if files:
            return files[0]["id"]
        return None
    except Exception as e:
        print(f"GDrive: Dosya arama hatası: {e}", flush=True)
        return None


# ─────────────────────────────────────────────
#  ANA FONKSİYONLAR
# ─────────────────────────────────────────────

def drive_save(data: dict) -> bool:
    """
    Veriyi Google Drive'a JSON olarak kaydet.
    Dosya varsa günceller, yoksa yeni oluşturur.
    Thread-safe.
    """
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

            file_id = _find_file_id(service, DRIVE_FILENAME)

            if file_id:
                # Mevcut dosyayı güncelle
                service.files().update(
                    fileId=file_id,
                    media_body=media
                ).execute()
                print(f"GDrive: Güncellendi ({len(data.get('expenses',[]))} fiş)", flush=True)
            else:
                # Yeni dosya oluştur
                file_metadata = {"name": DRIVE_FILENAME}
                if DRIVE_FOLDER_ID:
                    file_metadata["parents"] = [DRIVE_FOLDER_ID]

                service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields="id"
                ).execute()
                print(f"GDrive: Yeni dosya oluşturuldu ({len(data.get('expenses',[]))} fiş)", flush=True)

            return True

        except Exception as e:
            print(f"GDrive KAYIT HATASI: {e}", flush=True)
            return False


def drive_load() -> dict | None:
    """
    Google Drive'dan en güncel veriyi yükle.
    Başarısız olursa None döndürür (lokal dosyadan devam edilmeli).
    """
    service = _get_drive_service()
    if not service:
        return None

    try:
        file_id = _find_file_id(service, DRIVE_FILENAME)
        if not file_id:
            print("GDrive: Yedek dosya bulunamadı, ilk çalıştırma olabilir.", flush=True)
            return None

        request_obj = service.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request_obj)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        buffer.seek(0)
        data = json.loads(buffer.read().decode("utf-8"))
        fis_count = len(data.get("expenses", []))
        print(f"GDrive: Veri yüklendi ({fis_count} fiş)", flush=True)
        return data

    except Exception as e:
        print(f"GDrive YÜKLEME HATASI: {e}", flush=True)
        return None


def drive_save_async(data: dict):
    """
    Veriyi arka planda Google Drive'a kaydet.
    Ana thread'i bloklamaz — save_data() içinde kullanılır.
    """
    # Deep copy yaparak thread safety sağla
    import copy
    data_copy = copy.deepcopy(data)
    t = threading.Thread(target=drive_save, args=(data_copy,), daemon=True)
    t.start()
