# Stinga Enerji — Web Sitesi & Admin Panel

Flask tabanlı tam CMS sistemi.

## Kurulum (Lokal)

```bash
pip install -r requirements.txt
python app.py
```

Tarayıcıda: http://localhost:5000
Admin Panel: http://localhost:5000/admin

**Varsayılan giriş:**
- Kullanıcı: `admin`
- Şifre: `stinga2024`

> ⚠️ Yayına almadan önce şifrenizi değiştirin!

## Railway Deployment

1. Bu klasörü GitHub'a push edin
2. railway.com → New Project → GitHub repo seçin
3. Otomatik deploy olur

## Klasör Yapısı

```
stinga/
├── app.py              ← Ana uygulama
├── requirements.txt
├── Procfile            ← Railway için
├── instance/
│   └── stinga.db       ← SQLite veritabanı (otomatik oluşur)
├── static/
│   ├── logo.png
│   └── uploads/
│       ├── images/     ← Yüklenen görseller
│       └── videos/     ← Yüklenen videolar
└── templates/
    ├── base.html
    ├── index.html
    ├── post.html
    └── admin/
        ├── base_admin.html
        ├── login.html
        ├── dashboard.html
        ├── posts.html
        ├── post_form.html
        ├── gallery.html
        ├── messages.html
        ├── faqs.html
        ├── settings.html
        └── change_password.html
```

## Admin Panel Özellikleri

- 📰 Haber / Makale / Proje / Hizmet ekleme, düzenleme, silme
- 🖼️ Galeri yönetimi (çoklu yükleme, önizleme)
- ❓ SSS yönetimi (sıralama, düzenleme)
- ✉️ İletişim mesajları görüntüleme
- ⚙️ Site ayarları (başlık, istatistikler, iletişim bilgileri)
- 🔑 Şifre değiştirme
- 🌐 Siteyi önizleme butonu
