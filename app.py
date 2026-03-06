import os
import sqlite3
import hashlib
import secrets
from datetime import datetime
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify, abort)
from werkzeug.utils import secure_filename
from PIL import Image

# ── Cloudinary ───────────────────────────────────────────
try:
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = True
    cloudinary.config(
        cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME', 'dfopdpnbe'),
        api_key    = os.environ.get('CLOUDINARY_API_KEY',    '497882758483117'),
        api_secret = os.environ.get('CLOUDINARY_API_SECRET', 'PQaOzi5QQizOyt7LuJFsx8ka-_U'),
        secure     = True
    )
except ImportError:
    CLOUDINARY_AVAILABLE = False

app = Flask(__name__)
app.secret_key = "stinga_lang_secret_2024"

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
DB_PATH      = os.path.join(INSTANCE_DIR, 'stinga.db')
UPLOAD_DIR   = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_IMG  = {'png','jpg','jpeg','gif','webp'}
ALLOWED_VID  = {'mp4','webm','mov','avi'}

os.makedirs(INSTANCE_DIR,            exist_ok=True)
os.makedirs(UPLOAD_DIR + '/images',  exist_ok=True)
os.makedirs(UPLOAD_DIR + '/videos',  exist_ok=True)
os.makedirs(UPLOAD_DIR + '/albums',  exist_ok=True)
os.makedirs(UPLOAD_DIR + '/docs',    exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY, value TEXT
    );
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        title TEXT NOT NULL,
        slug TEXT UNIQUE,
        body TEXT, excerpt TEXT, image TEXT, video TEXT,
        published INTEGER DEFAULT 1,
        created TEXT DEFAULT (datetime('now')),
        updated TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS gallery (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL, caption TEXT,
        type TEXT DEFAULT 'image',
        created TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS albums (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, description TEXT,
        cover TEXT, year INTEGER, month INTEGER,
        published INTEGER DEFAULT 1,
        created TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS album_photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        album_id INTEGER NOT NULL,
        filename TEXT NOT NULL, caption TEXT,
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY(album_id) REFERENCES albums(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, description TEXT,
        filename TEXT, youtube_url TEXT, thumb TEXT,
        published INTEGER DEFAULT 1,
        created TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS faqs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL, answer TEXT NOT NULL,
        sort_order INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, email TEXT, subject TEXT, message TEXT,
        read INTEGER DEFAULT 0,
        created TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS tech_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        icon TEXT DEFAULT '⚙️',
        title TEXT NOT NULL,
        sort_order INTEGER DEFAULT 0,
        published INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS about_cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        icon TEXT DEFAULT '⭐',
        title TEXT NOT NULL,
        body TEXT,
        sort_order INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS ticker_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL,
        sort_order INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS nav_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        label TEXT NOT NULL,
        url TEXT NOT NULL,
        sort_order INTEGER DEFAULT 0,
        is_external INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS footer_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        column_name TEXT NOT NULL,
        label TEXT NOT NULL,
        url TEXT NOT NULL,
        sort_order INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        body TEXT,
        excerpt TEXT,
        image TEXT,
        page_type TEXT DEFAULT 'genel',
        sort_order INTEGER DEFAULT 0,
        published INTEGER DEFAULT 1,
        created TEXT DEFAULT (datetime('now')),
        updated TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS page_media (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        page_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        media_type TEXT DEFAULT 'image',
        caption TEXT,
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY(page_id) REFERENCES pages(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS certificates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        image TEXT,
        cert_type TEXT DEFAULT 'patent',
        country TEXT,
        year INTEGER,
        sort_order INTEGER DEFAULT 0,
        published INTEGER DEFAULT 1,
        created TEXT DEFAULT (datetime('now'))
    );
    """)
    pw = hashlib.sha256('stinga2024'.encode()).hexdigest()
    try:
        db.execute("INSERT INTO users (username,password) VALUES (?,?)", ('admin', pw))
    except: pass
    defaults = {
        'site_title':'Stinga Enerji A.Ş.','site_desc':'Yerli ve Milli Teknoloji',
        'phone':'+90 212 872 23 57','email':'info@stinga.biz',
        'address':'Cumhuriyet Mh. D-100 Karayolu Cd. İstanbul Outlet Park AVM No:374/63 Büyükçekmece/İstanbul',
        'twitter':'https://x.com/StingaEnerji','youtube':'https://www.youtube.com/watch?v=pUauMTvTRXM',
        'hero_title':'Enerjinin Geleceğini Yazıyoruz',
        'hero_desc':"Kurucu Şenol Faik Özyaman'ın 15 yıllık Ar-Ge çalışmasıyla geliştirilen emisyonsuz yanma teknolojisi — %100 yerli, 134 ülkede tescilli.",
        'about_text':'Ülkemizin enerji sektöründe dışa bağımlılığı azaltmak, yerli kaynakları daha etkin kullanmak ve istihdamı artırmak amacıyla yola çıkan Stinga Enerji, yerli makine üretiminde üstün bir başarıya imza atmıştır.',
        'stat_patent':'134','stat_arge':'15+','stat_yerli':'%100','stat_emisyon':'0',
        'hero_video':'',
    }
    for k,v in defaults.items():
        try: db.execute("INSERT INTO settings (key,value) VALUES (?,?)", (k,v))
        except: pass
    faqs = [
        ("Stinga Teknolojisi Nedir?","Şenol Faik Özyaman tarafından 15 yıllık Ar-Ge çalışması sonucu geliştirilen 'Yeni Teknoloji Yüksek Verimli Isı Jeneratörü', emisyonsuz yanma sağlayan devrimci bir sistemdir.",1),
        ("Stinga Aktif Karbon Nedir?","Karbonun Stinga Teknolojileri ile aktifleştirilmesiyle elde edilen yüksek emici güçlü bir üründür. Su arıtma, hava filtrasyonu ve endüstriyel alanlarda kullanılır.",2),
        ("134 Ülkede Patent Nasıl Alındı?","Özgün buluş niteliği taşıyan teknolojiler için uluslararası patent başvuruları yapılmıştır. Bugün 134 farklı ülkede tescilli patentlerle korunmaktadır.",3),
        ("Karbon Ayak İzi İçin Ne Yapılıyor?","Emisyonsuz yanma teknolojisi sera gazı salımını köklü biçimde azaltır. Yanma sürecinde tüm zehirli gazlar tekrar yakılarak atmosfere salınım engellenir.",4),
    ]
    for q,a,s in faqs:
        try: db.execute("INSERT INTO faqs (question,answer,sort_order) VALUES (?,?,?)", (q,a,s))
        except: pass

    tech_items = [
        ('💧','Arıtma Çamuru Kurutma',1),
        ('🐄','Hayvansal Atık Kurutma',2),
        ('⚫','Kömür Kurutma & Zenginleştirme',3),
        ('🌊','Buhar Üretim Kazanları',4),
        ('🌡️','Sıcak Su Üretim Kazanları',5),
        ('💨','Sıcak Hava Üretim Kazanları',6),
        ('♻️','Arıtma Çamuru Bertarafı & Enerji',7),
        ('⚡','Termik Santraller için Kömür Kurutma',8),
    ]
    for ico,title,s in tech_items:
        try: db.execute("INSERT INTO tech_items (icon,title,sort_order) VALUES (?,?,?)", (ico,title,s))
        except: pass

    about_cards = [
        ('🏆','Misyonumuz','Enerji sektöründe yerli ve milli teknolojilerle sürdürülebilir bir gelecek inşa etmek',1),
        ('🔭','Vizyonumuz','Uluslararası arenada Türk mühendisliğini temsil eden öncü bir enerji şirketi olmak',2),
        ('🔬','Ar-Ge Merkezimiz','Sürekli gelişim ve inovasyon odaklı araştırma-geliştirme faaliyetleri',3),
        ('📜','Sertifikalarımız','RDM yeterlilik belgeleri, emisyon raporları ve uluslararası teknoloji sertifikaları',4),
    ]
    for ico,title,body,s in about_cards:
        try: db.execute("INSERT INTO about_cards (icon,title,body,sort_order) VALUES (?,?,?,?)", (ico,title,body,s))
        except: pass

    ticker_items = [
        ('Kazan Teknolojileri',1),('Emisyonsuz Yanma',2),('Madencilik Faaliyetleri',3),
        ('Aktif Karbon Üretimi',4),('Endüstriyel Makine',5),('Kurutma Teknolojisi',6),
        ('134 Ülke Patent',7),('Stinga Teknolojileri',8),
    ]
    for text,s in ticker_items:
        try: db.execute("INSERT INTO ticker_items (text,sort_order) VALUES (?,?)", (text,s))
        except: pass

    nav_links = [
        ('Ana Sayfa','/#top',1,0),('Hakkımızda','/#hakkimizda',2,0),
        ('Hizmetler','/#hizmetler',3,0),('Teknoloji','/#teknoloji',4,0),
        ('Projeler','/#projeler',5,0),('SSS','/#sss',6,0),
        ('Galeri','/galeri',7,0),('Videolar','/videolar',8,0),
        ('İletişim','/#iletisim',9,0),
    ]
    for label,url,s,ext in nav_links:
        try: db.execute("INSERT INTO nav_links (label,url,sort_order,is_external) VALUES (?,?,?,?)", (label,url,s,ext))
        except: pass

    footer_links = [
        ('Hizmetler','Endüstriyel Makine','/#hizmetler',1),
        ('Hizmetler','Madencilik','/#hizmetler',2),
        ('Hizmetler','Aktif Karbon','/#hizmetler',3),
        ('Kurumsal','Hakkımızda','/#hakkimizda',1),
        ('Kurumsal','Teknoloji','/#teknoloji',2),
        ('Kurumsal','Projeler','/#projeler',3),
        ('Kurumsal','İletişim','/#iletisim',4),
        ('Yasal','Gizlilik Politikası','#',1),
        ('Yasal','Kullanım Koşulları','#',2),
    ]
    for col,label,url,s in footer_links:
        try: db.execute("INSERT INTO footer_links (column_name,label,url,sort_order) VALUES (?,?,?,?)", (col,label,url,s))
        except: pass

    # Default pages
    default_pages = [
        ('Endüstriyel Makine Üretimi', 'endustiriyel-makine-uretimi-55',
         '''<h2>Endüstriyel Makine Üretimi</h2>
<p>Stinga Enerji, 15 yıllık Ar-Ge birikimi ve özgün mühendislik anlayışıyla endüstriyel makine üretiminde fark yaratmaktadır. Yerli ve milli teknolojilerle geliştirilen makinelerimiz, enerji verimliliğini en üst düzeye taşımaktadır.</p>
<h3>Ürün Gruplarımız</h3>
<ul>
<li>Yüksek Verimli Isı Jeneratörleri</li>
<li>Buhar Üretim Kazanları</li>
<li>Sıcak Su ve Sıcak Hava Kazanları</li>
<li>Arıtma Çamuru Kurutma Sistemleri</li>
<li>Kömür Kurutma ve Zenginleştirme Tesisleri</li>
</ul>
<p>Tüm makinelerimiz 134 ülkede tescilli patentli teknolojilerimizle üretilmekte; emisyonsuz yanma prensibiyle çevreye duyarlı bir üretim anlayışını benimsemektedir.</p>''',
         'Stinga Enerji endüstriyel makine üretiminde yerli ve milli teknolojilerle öncü çözümler sunmaktadır.',
         '', 'endustri', 1, 1),
        ('Kurucu', 'kurucu-12',
         '''<h2>Şenol Faik Özyaman — Kurucu</h2>
<p>Stinga Enerji'nin kurucusu Şenol Faik Özyaman, 15 yılı aşkın Ar-Ge çalışmasının ardından "Yeni Teknoloji Yüksek Verimli Isı Jeneratörü"nü geliştirmiştir. Bu buluş; emisyonsuz yanma sağlayan, %100 yerli ve 134 ülkede tescilli devrimci bir enerji teknolojisidir.</p>
<h3>Vizyon</h3>
<p>Türkiye'nin enerji sektöründe dışa bağımlılığını azaltmak, yerli kaynakları daha verimli kullanmak ve ulusal istihdama katkı sağlamak amacıyla yola çıkan Özyaman, mühendislik disiplinini girişimcilik ruhuyla birleştirmiştir.</p>
<h3>Başarılar</h3>
<ul>
<li>134 ülkede uluslararası patent tescili</li>
<li>15+ yıl özgün Ar-Ge çalışması</li>
<li>%100 yerli teknoloji geliştirme</li>
<li>Sıfır emisyon yanma teknolojisi</li>
</ul>''',
         'Stinga Enerji kurucusu Şenol Faik Özyaman ve 15 yıllık Ar-Ge yolculuğu.',
         '', 'kurucu', 2, 1),
    ]
    for title, slug, body, excerpt, image, ptype, sort_order, pub in default_pages:
        try: db.execute(
            "INSERT INTO pages (title,slug,body,excerpt,image,page_type,sort_order,published) VALUES (?,?,?,?,?,?,?,?)",
            (title, slug, body, excerpt, image, ptype, sort_order, pub))
        except: pass

    # Default certificates / patents
    default_certs = [
        ('Uluslararası Patent – PCT', 'PCT kapsamında 134 ülkede tescilli buluş patenti. Yüksek Verimli Isı Jeneratörü teknolojisi.', '', 'patent', 'Uluslararası', 2018, 1),
        ('RDM Yeterlilik Belgesi', 'Araştırma ve Geliştirme Merkezi yeterlilik belgesi.', '', 'sertifika', 'Türkiye', 2019, 2),
        ('Emisyon Test Raporu', 'Bağımsız akredite laboratuvar tarafından düzenlenen emisyon testi raporu.', '', 'rapor', 'Türkiye', 2020, 3),
        ('ISO 9001:2015', 'Kalite Yönetim Sistemi sertifikası.', '', 'sertifika', 'Uluslararası', 2021, 4),
        ('Yerli Malı Belgesi', 'Sanayi ve Teknoloji Bakanlığı onaylı yerli malı belgesi.', '', 'belge', 'Türkiye', 2022, 5),
    ]
    for title,desc,img,ctype,country,year,sort_order in default_certs:
        try: db.execute(
            "INSERT INTO certificates (title,description,image,cert_type,country,year,sort_order,published) VALUES (?,?,?,?,?,?,?,1)",
            (title,desc,img,ctype,country,year,sort_order))
        except: pass

    db.commit(); db.close()

def get_all_settings():
    db   = get_db()
    rows = db.execute("SELECT key,value FROM settings").fetchall()
    db.close()
    return {r['key']: r['value'] for r in rows}

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def slugify(text):
    import re
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text[:80]

def save_upload(file, ftype='img'):
    """Upload to Cloudinary (production) or local (development)."""
    if not file or file.filename == '': return None

    if CLOUDINARY_AVAILABLE:
        try:
            resource_type = 'video' if ftype == 'vid' else 'image'
            folder = 'stinga/' + ('videos' if ftype == 'vid' else ('albums' if ftype == 'album' else 'images'))
            result = cloudinary.uploader.upload(
                file,
                folder=folder,
                resource_type=resource_type,
                quality='auto',
                fetch_format='auto'
            )
            return result['secure_url']
        except Exception as e:
            print(f'Cloudinary upload error: {e}')
            # fallback to local

    # Local fallback
    fname  = secure_filename(file.filename)
    ts     = datetime.now().strftime('%Y%m%d_%H%M%S_')
    fname  = ts + fname
    subdir = 'images' if ftype == 'img' else ('videos' if ftype == 'vid' else 'albums')
    path   = os.path.join(UPLOAD_DIR, subdir, fname)
    file.seek(0)
    file.save(path)
    if ftype in ('img', 'album'):
        try:
            img = Image.open(path)
            img.thumbnail((1600, 1200), Image.LANCZOS)
            img.save(path, optimize=True, quality=88)
        except: pass
    return f'uploads/{subdir}/{fname}'

def yt_embed(url):
    """Convert YouTube URL to embed URL."""
    import re
    if not url: return None
    m = re.search(r'(?:v=|youtu\.be/)([^&\?/]+)', url)
    return f"https://www.youtube.com/embed/{m.group(1)}" if m else None

app.jinja_env.globals['yt_embed'] = yt_embed

@app.context_processor
def inject_globals():
    """Inject nav/footer data into all templates."""
    db = get_db()
    nav_links    = db.execute("SELECT * FROM nav_links ORDER BY sort_order").fetchall()
    footer_links = db.execute("SELECT * FROM footer_links ORDER BY column_name, sort_order").fetchall()
    ticker_items = db.execute("SELECT * FROM ticker_items ORDER BY sort_order").fetchall()
    db.close()
    footer_cols = {}
    for fl in footer_links:
        footer_cols.setdefault(fl['column_name'], []).append(fl)
    return dict(g_nav=nav_links, g_footer_cols=footer_cols, g_ticker=ticker_items)

def media_url(path):
    """Return full URL for media - handles both Cloudinary URLs and local paths."""
    if not path: return ''
    if path.startswith('http'): return path  # Cloudinary URL
    return '/static/' + path  # local path

app.jinja_env.globals['media_url'] = media_url

# ═══════════════════════════════════════════════
# PUBLIC
# ═══════════════════════════════════════════════


# ═══ DİL SİSTEMİ ═══
LANGS = {
    'tr': {'flag':'🇹🇷','name':'Türkçe'},
    'en': {'flag':'🇬🇧','name':'English'},
    'de': {'flag':'🇩🇪','name':'Deutsch'},
    'zh': {'flag':'🇨🇳','name':'中文'},
    'ar': {'flag':'🇸🇦','name':'العربية'},
    'es': {'flag':'🇪🇸','name':'Español'},
    'fr': {'flag':'🇫🇷','name':'Français'},
    'ru': {'flag':'🇷🇺','name':'Русский'},
}

TRANSLATIONS = {
    'hero_title1': {'tr':'Enerjinin','en':'Writing the','de':'Die Zukunft','zh':'书写能源','ar':'نكتب','es':'Escribiendo',"fr":"Écrivons",'ru':'Пишем'},
    'hero_title2': {'tr':'Geleceğini','en':'Future of','de':'der Energie','zh':'的未来','ar':'مستقبل','es':'el Futuro',"fr":"le Futur",'ru':'Будущее'},
    'hero_title3': {'tr':'Yazıyoruz','en':'Energy','de':'schreiben','zh':'','ar':'الطاقة','es':'de la Energía',"fr":"de l'Énergie",'ru':'Энергии'},
    'hero_desc':   {"tr":"Kurucu Şenol Faik Özyaman'ın 15 yıllık Ar-Ge çalışmasıyla geliştirilen emisyonsuz yanma teknolojisi — %100 yerli, 134 ülkede tescilli.",
                    'en':'Zero-emission combustion technology developed by founder Şenol Faik Özyaman through 15 years of R&D — 100% domestic, registered in 134 countries.',
                    'de':'Emissionsfreie Verbrennungstechnologie, entwickelt durch 15 Jahre F&E — 100% einheimisch, in 134 Ländern registriert.',
                    'zh':'由创始人Şenol Faik Özyaman经过15年研发开发的零排放燃烧技术——100%国产，已在134个国家注册。',
                    'ar':'تقنية الاحتراق الخالية من الانبعاثات التي طورها المؤسس شنول فائق أوزيامان خلال 15 عامًا من البحث والتطوير.',
                    'es':'Tecnología de combustión de cero emisiones desarrollada por el fundador Şenol Faik Özyaman en 15 años de I+D — 100% nacional, registrada en 134 países.',
                    "fr":"Technologie de combustion zéro émission développée par le fondateur Şenol Faik Özyaman après 15 ans de R&D — 100% nationale, enregistrée dans 134 pays.",
                    'ru':'Технология сгорания без выбросов, разработанная основателем Шенолом Файком Озьяманом за 15 лет исследований — 100% отечественная, зарегистрирована в 134 странах.'},
    'btn_explore': {'tr':'Teknolojiyi Keşfet →','en':'Explore Technology →','de':'Technologie Entdecken →','zh':'探索技术 →','ar':'استكشف التكنولوجيا →','es':'Explorar Tecnología →','fr':'Explorer la Technologie →','ru':'Исследовать →'},
    'btn_contact': {'tr':'İletişime Geç','en':'Contact Us','de':'Kontakt','zh':'联系我们','ar':'تواصل معنا','es':'Contáctenos','fr':'Nous Contacter','ru':'Связаться'},
    'stat_patent': {'tr':'Ülke Patenti','en':'Country Patents','de':'Länder-Patente','zh':'国家专利','ar':'براءة اختراع دولية','es':'Patentes Mundiales','fr':'Brevets Mondiaux','ru':'Патентов стран'},
    'stat_rnd':    {'tr':'Yıl Ar-Ge','en':'Years R&D','de':'Jahre F&E','zh':'年研发','ar':'سنة بحث','es':'Años I+D','fr':'Ans R&D','ru':'Лет НИОКР'},
    'stat_local':  {'tr':'Yerli Üretim','en':'Local Production','de':'Inlandsproduktion','zh':'国内生产','ar':'إنتاج محلي','es':'Producción Local','fr':'Production Locale','ru':'Местное производство'},
    'stat_emission':{'tr':'Emisyon','en':'Emission','de':'Emission','zh':'排放','ar':'انبعاثات','es':'Emisión','fr':'Émission','ru':'Выброс'},
    'nav_about':   {'tr':'Hakkımızda','en':'About','de':'Über uns','zh':'关于','ar':'عنا','es':'Nosotros','fr':'À propos','ru':'О нас'},
    'nav_services':{'tr':'Hizmetler','en':'Services','de':'Dienste','zh':'服务','ar':'خدمات','es':'Servicios','fr':'Services','ru':'Услуги'},
    'nav_tech':    {'tr':'Teknoloji','en':'Technology','de':'Technologie','zh':'技术','ar':'التكنولوجيا','es':'Tecnología','fr':'Technologie','ru':'Технология'},
    'nav_projects':{'tr':'Projeler','en':'Projects','de':'Projekte','zh':'项目','ar':'مشاريع','es':'Proyectos','fr':'Projets','ru':'Проекты'},
    'nav_news':    {'tr':'Haberler','en':'News','de':'Nachrichten','zh':'新闻','ar':'أخبار','es':'Noticias','fr':'Actualités','ru':'Новости'},
    'nav_founder': {'tr':'Kurucu','en':'Founder','de':'Gründer','zh':'创始人','ar':'المؤسس','es':'Fundador','fr':'Fondateur','ru':'Основатель'},
    'nav_certs':   {'tr':'Sertifikalar','en':'Certificates','de':'Zertifikate','zh':'证书','ar':'شهادات','es':'Certificados','fr':'Certificats','ru':'Сертификаты'},
    'nav_gallery': {'tr':'Galeri','en':'Gallery','de':'Galerie','zh':'画廊','ar':'معرض','es':'Galería','fr':'Galerie','ru':'Галерея'},
    'nav_contact': {'tr':'İletişim','en':'Contact','de':'Kontakt','zh':'联系','ar':'اتصال','es':'Contacto','fr':'Contact','ru':'Контакт'},
}

def get_lang():
    return session.get('lang', 'tr')

def t(key):
    lang = get_lang()
    d = TRANSLATIONS.get(key, {})
    return d.get(lang, d.get('tr', key))

@app.route('/set-lang/<lang>')
def set_lang(lang):
    if lang in LANGS:
        session['lang'] = lang
    return redirect(request.referrer or '/')

@app.context_processor
def inject_lang():
    try:
        lang = session.get('lang', 'tr')
        if lang not in LANGS:
            lang = 'tr'
    except Exception:
        lang = 'tr'
    
    def translate(key):
        d = TRANSLATIONS.get(key, {})
        return d.get(lang, d.get('tr', key))
    
    return dict(
        current_lang=lang,
        langs=LANGS,
        t=translate,
        is_rtl=(lang=='ar')
    )

@app.route('/')
def index():
    db  = get_db()
    cfg = get_all_settings()
    news        = db.execute("SELECT * FROM posts WHERE type='haber' AND published=1 ORDER BY created DESC LIMIT 6").fetchall()
    projects    = db.execute("SELECT * FROM posts WHERE type='proje' AND published=1 ORDER BY created DESC LIMIT 4").fetchall()
    services    = db.execute("SELECT * FROM posts WHERE type='servis' AND published=1 ORDER BY created DESC LIMIT 3").fetchall()
    faqs        = db.execute("SELECT * FROM faqs ORDER BY sort_order LIMIT 6").fetchall()
    tech_items  = db.execute("SELECT * FROM tech_items WHERE published=1 ORDER BY sort_order").fetchall()
    about_cards = db.execute("SELECT * FROM about_cards ORDER BY sort_order").fetchall()
    ticker_items= db.execute("SELECT * FROM ticker_items ORDER BY sort_order").fetchall()
    nav_links   = db.execute("SELECT * FROM nav_links ORDER BY sort_order").fetchall()
    footer_links= db.execute("SELECT * FROM footer_links ORDER BY column_name, sort_order").fetchall()
    db.close()
    # Group footer links by column
    footer_cols = {}
    for fl in footer_links:
        footer_cols.setdefault(fl['column_name'], []).append(fl)
    return render_template('index.html', cfg=cfg, news=news, projects=projects,
        services=services, faqs=faqs, tech_items=tech_items, about_cards=about_cards,
        ticker_items=ticker_items, nav_links=nav_links, footer_cols=footer_cols)

@app.route('/galeri')
def galeri():
    db  = get_db()
    cfg = get_all_settings()
    albums = db.execute("""
        SELECT a.*, COUNT(ap.id) as photo_count
        FROM albums a LEFT JOIN album_photos ap ON a.id=ap.album_id
        WHERE a.published=1 GROUP BY a.id
        ORDER BY a.year DESC, a.month DESC, a.created DESC
    """).fetchall()
    db.close()
    timeline = {}
    for album in albums:
        year = str(album['year']) if album['year'] else 'Tarihsiz'
        timeline.setdefault(year, []).append(album)
    return render_template('galeri.html', cfg=cfg, timeline=timeline)

@app.route('/galeri/album/<int:album_id>')
def album_detail(album_id):
    db    = get_db()
    cfg   = get_all_settings()
    album = db.execute("SELECT * FROM albums WHERE id=? AND published=1", (album_id,)).fetchone()
    if not album: db.close(); abort(404)
    photos = db.execute("SELECT * FROM album_photos WHERE album_id=? ORDER BY sort_order, id", (album_id,)).fetchall()
    db.close()
    return render_template('album_detail.html', cfg=cfg, album=album, photos=photos)

@app.route('/videolar')
def videolar():
    db  = get_db()
    cfg = get_all_settings()
    vids = db.execute("SELECT * FROM videos WHERE published=1 ORDER BY created DESC").fetchall()
    db.close()
    return render_template('videolar.html', cfg=cfg, videos=vids)

@app.route('/haber/<slug>')
def post_detail(slug):
    db   = get_db()
    cfg  = get_all_settings()
    post = db.execute("SELECT * FROM posts WHERE slug=? AND published=1", (slug,)).fetchone()
    db.close()
    if not post: abort(404)
    return render_template('post.html', cfg=cfg, post=post)

@app.route('/iletisim', methods=['POST'])
def contact_submit():
    db = get_db()
    db.execute("INSERT INTO contacts (name,email,subject,message) VALUES (?,?,?,?)",
               (request.form.get('name'), request.form.get('email'),
                request.form.get('subject'), request.form.get('message')))
    db.commit(); db.close()
    return jsonify({'ok': True})

# ═══════════════════════════════════════════════
# PUBLIC — SAYFALAR (Pages)
# ═══════════════════════════════════════════════

@app.route('/sayfa/<slug>')
@app.route('/tr/sayfa/<slug>')
def page_detail(slug):
    db   = get_db()
    cfg  = get_all_settings()
    page = db.execute("SELECT * FROM pages WHERE slug=? AND published=1", (slug,)).fetchone()
    if not page: db.close(); abort(404)
    media = db.execute(
        "SELECT * FROM page_media WHERE page_id=? ORDER BY sort_order, id", (page['id'],)
    ).fetchall()
    db.close()
    return render_template('page_detail.html', cfg=cfg, page=page, media=media)

# ═══════════════════════════════════════════════
# PUBLIC — SERTİFİKALAR & PATENTLER
# ═══════════════════════════════════════════════

@app.route('/sertifikalar')
@app.route('/tr/sertifikalar')
def sertifikalar():
    db   = get_db()
    cfg  = get_all_settings()
    certs = db.execute(
        "SELECT * FROM certificates WHERE published=1 ORDER BY sort_order, year DESC"
    ).fetchall()
    db.close()
    # Group by type
    by_type = {}
    for c in certs:
        by_type.setdefault(c['cert_type'], []).append(c)
    return render_template('sertifikalar.html', cfg=cfg, certs=certs, by_type=by_type)

# ═══════════════════════════════════════════════
# ADMIN AUTH
# ═══════════════════════════════════════════════

@app.route('/admin', methods=['GET','POST'])
@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if session.get('admin'): return redirect(url_for('admin_dashboard'))
    error = None
    if request.method == 'POST':
        uname = request.form.get('username','').strip()
        pw    = request.form.get('password','')
        db    = get_db()
        user  = db.execute("SELECT * FROM users WHERE username=? AND password=?", (uname, hash_pw(pw))).fetchone()
        db.close()
        if user:
            session['admin'] = True; session['username'] = uname
            return redirect(url_for('admin_dashboard'))
        error = 'Kullanıcı adı veya şifre hatalı.'
    return render_template('admin/login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

# ═══════════════════════════════════════════════
# ADMIN DASHBOARD
# ═══════════════════════════════════════════════

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    db = get_db()
    stats = {
        'haberler': db.execute("SELECT COUNT(*) FROM posts WHERE type='haber'").fetchone()[0],
        'projeler': db.execute("SELECT COUNT(*) FROM posts WHERE type='proje'").fetchone()[0],
        'albumler': db.execute("SELECT COUNT(*) FROM albums").fetchone()[0],
        'videolar': db.execute("SELECT COUNT(*) FROM videos").fetchone()[0],
        'galeri':   db.execute("SELECT COUNT(*) FROM gallery").fetchone()[0],
        'mesajlar': db.execute("SELECT COUNT(*) FROM contacts WHERE read=0").fetchone()[0],
    }
    recent   = db.execute("SELECT * FROM posts ORDER BY created DESC LIMIT 5").fetchall()
    messages = db.execute("SELECT * FROM contacts WHERE read=0 ORDER BY created DESC LIMIT 5").fetchall()
    db.close()
    return render_template('admin/dashboard.html', stats=stats, recent=recent, messages=messages)

# ═══════════════════════════════════════════════
# ADMIN POSTS
# ═══════════════════════════════════════════════

@app.route('/admin/posts')
@app.route('/admin/posts/<ptype>')
@login_required
def admin_posts(ptype='haber'):
    db = get_db()
    posts = db.execute("SELECT * FROM posts WHERE type=? ORDER BY created DESC", (ptype,)).fetchall()
    db.close()
    return render_template('admin/posts.html', posts=posts, ptype=ptype)

@app.route('/admin/posts/new', methods=['GET','POST'])
@app.route('/admin/posts/new/<ptype>', methods=['GET','POST'])
@login_required
def admin_post_new(ptype='haber'):
    if request.method == 'POST':
        title=request.form.get('title','').strip(); body=request.form.get('body','')
        excerpt=request.form.get('excerpt',''); pub=1 if request.form.get('published') else 0
        ptype=request.form.get('ptype',ptype); slug=slugify(title)
        image=save_upload(request.files.get('image'),'img')
        video=save_upload(request.files.get('video'),'vid')
        db=get_db(); base,i=slug,1
        while db.execute("SELECT id FROM posts WHERE slug=?", (slug,)).fetchone():
            slug=f"{base}-{i}"; i+=1
        db.execute("INSERT INTO posts (type,title,slug,body,excerpt,image,video,published) VALUES (?,?,?,?,?,?,?,?)",
                   (ptype,title,slug,body,excerpt,image,video,pub))
        db.commit(); db.close()
        flash(f'"{title}" başarıyla eklendi.', 'success')
        return redirect(url_for('admin_posts', ptype=ptype))
    return render_template('admin/post_form.html', post=None, ptype=ptype)

@app.route('/admin/posts/edit/<int:pid>', methods=['GET','POST'])
@login_required
def admin_post_edit(pid):
    db=get_db(); post=db.execute("SELECT * FROM posts WHERE id=?", (pid,)).fetchone()
    if not post: db.close(); abort(404)
    if request.method == 'POST':
        title=request.form.get('title','').strip(); body=request.form.get('body','')
        excerpt=request.form.get('excerpt',''); pub=1 if request.form.get('published') else 0
        image=post['image']; video=post['video']
        new_img=request.files.get('image'); new_vid=request.files.get('video')
        if new_img and new_img.filename: image=save_upload(new_img,'img') or image
        if new_vid and new_vid.filename: video=save_upload(new_vid,'vid') or video
        db.execute("UPDATE posts SET title=?,body=?,excerpt=?,image=?,video=?,published=?,updated=datetime('now') WHERE id=?",
                   (title,body,excerpt,image,video,pub,pid))
        db.commit(); db.close()
        flash('Güncellendi.', 'success')
        return redirect(url_for('admin_posts', ptype=post['type']))
    db.close()
    return render_template('admin/post_form.html', post=post, ptype=post['type'])

@app.route('/admin/posts/delete/<int:pid>', methods=['POST'])
@login_required
def admin_post_delete(pid):
    db=get_db(); post=db.execute("SELECT * FROM posts WHERE id=?", (pid,)).fetchone()
    ptype=post['type'] if post else 'haber'
    db.execute("DELETE FROM posts WHERE id=?", (pid,)); db.commit(); db.close()
    flash('Silindi.', 'info')
    return redirect(url_for('admin_posts', ptype=ptype))

# ═══════════════════════════════════════════════
# ADMIN ALBUMS
# ═══════════════════════════════════════════════

@app.route('/admin/albumler')
@login_required
def admin_albums():
    db = get_db()
    albums = db.execute("""
        SELECT a.*, COUNT(ap.id) as photo_count FROM albums a
        LEFT JOIN album_photos ap ON a.id=ap.album_id
        GROUP BY a.id ORDER BY a.year DESC, a.created DESC
    """).fetchall()
    db.close()
    return render_template('admin/albums.html', albums=albums)

@app.route('/admin/albumler/new', methods=['GET','POST'])
@login_required
def admin_album_new():
    if request.method == 'POST':
        title=request.form.get('title','').strip(); desc=request.form.get('description','')
        year=request.form.get('year') or datetime.now().year
        month=request.form.get('month') or datetime.now().month
        pub=1 if request.form.get('published') else 0
        cover=save_upload(request.files.get('cover'),'img')
        db=get_db()
        cur=db.execute("INSERT INTO albums (title,description,cover,year,month,published) VALUES (?,?,?,?,?,?)",
                       (title,desc,cover,year,month,pub))
        album_id=cur.lastrowid
        for i,f in enumerate(request.files.getlist('photos')):
            if f and f.filename:
                path=save_upload(f,'album')
                if path: db.execute("INSERT INTO album_photos (album_id,filename,sort_order) VALUES (?,?,?)", (album_id,path,i))
        db.commit(); db.close()
        flash(f'"{title}" albümü oluşturuldu.', 'success')
        return redirect(url_for('admin_albums'))
    return render_template('admin/album_form.html', album=None, photos=[])

@app.route('/admin/albumler/edit/<int:aid>', methods=['GET','POST'])
@login_required
def admin_album_edit(aid):
    db=get_db(); album=db.execute("SELECT * FROM albums WHERE id=?", (aid,)).fetchone()
    if not album: db.close(); abort(404)
    photos=db.execute("SELECT * FROM album_photos WHERE album_id=? ORDER BY sort_order,id", (aid,)).fetchall()
    if request.method == 'POST':
        title=request.form.get('title','').strip(); desc=request.form.get('description','')
        year=request.form.get('year') or datetime.now().year
        month=request.form.get('month') or datetime.now().month
        pub=1 if request.form.get('published') else 0
        cover=album['cover']; new_cov=request.files.get('cover')
        if new_cov and new_cov.filename: cover=save_upload(new_cov,'img') or cover
        db.execute("UPDATE albums SET title=?,description=?,cover=?,year=?,month=?,published=? WHERE id=?",
                   (title,desc,cover,year,month,pub,aid))
        max_o=db.execute("SELECT MAX(sort_order) FROM album_photos WHERE album_id=?", (aid,)).fetchone()[0] or 0
        for i,f in enumerate(request.files.getlist('photos')):
            if f and f.filename:
                path=save_upload(f,'album')
                if path: db.execute("INSERT INTO album_photos (album_id,filename,sort_order) VALUES (?,?,?)", (aid,path,max_o+i+1))
        db.commit(); db.close()
        flash('Albüm güncellendi.', 'success')
        return redirect(url_for('admin_albums'))
    db.close()
    return render_template('admin/album_form.html', album=album, photos=photos)

@app.route('/admin/albumler/delete/<int:aid>', methods=['POST'])
@login_required
def admin_album_delete(aid):
    db=get_db()
    db.execute("DELETE FROM albums WHERE id=?", (aid,))
    db.execute("DELETE FROM album_photos WHERE album_id=?", (aid,))
    db.commit(); db.close()
    flash('Albüm silindi.', 'info')
    return redirect(url_for('admin_albums'))

@app.route('/admin/albumler/photo/delete/<int:pid>', methods=['POST'])
@login_required
def admin_photo_delete(pid):
    db=get_db(); photo=db.execute("SELECT * FROM album_photos WHERE id=?", (pid,)).fetchone()
    aid=request.form.get('album_id')
    if photo:
        try: os.remove(os.path.join(BASE_DIR,'static',photo['filename']))
        except: pass
        db.execute("DELETE FROM album_photos WHERE id=?", (pid,)); db.commit()
    db.close()
    return redirect(url_for('admin_album_edit', aid=aid))

# ═══════════════════════════════════════════════
# ADMIN VIDEOS
# ═══════════════════════════════════════════════

@app.route('/admin/videolar')
@login_required
def admin_videos():
    db=get_db(); vids=db.execute("SELECT * FROM videos ORDER BY created DESC").fetchall(); db.close()
    return render_template('admin/videos.html', videos=vids)

@app.route('/admin/videolar/new', methods=['GET','POST'])
@login_required
def admin_video_new():
    if request.method == 'POST':
        title=request.form.get('title','').strip(); desc=request.form.get('description','')
        yt_url=request.form.get('youtube_url','').strip(); pub=1 if request.form.get('published') else 0
        vid_file=save_upload(request.files.get('filename'),'vid')
        thumb=save_upload(request.files.get('thumb'),'img')
        db=get_db()
        db.execute("INSERT INTO videos (title,description,filename,youtube_url,thumb,published) VALUES (?,?,?,?,?,?)",
                   (title,desc,vid_file,yt_url,thumb,pub))
        db.commit(); db.close()
        flash(f'"{title}" videosu eklendi.', 'success')
        return redirect(url_for('admin_videos'))
    return render_template('admin/video_form.html', video=None)

@app.route('/admin/videolar/edit/<int:vid>', methods=['GET','POST'])
@login_required
def admin_video_edit(vid):
    db=get_db(); video=db.execute("SELECT * FROM videos WHERE id=?", (vid,)).fetchone()
    if not video: db.close(); abort(404)
    if request.method == 'POST':
        title=request.form.get('title','').strip(); desc=request.form.get('description','')
        yt_url=request.form.get('youtube_url','').strip(); pub=1 if request.form.get('published') else 0
        fname=video['filename']; thumb=video['thumb']
        new_vid=request.files.get('filename'); new_th=request.files.get('thumb')
        if new_vid and new_vid.filename: fname=save_upload(new_vid,'vid') or fname
        if new_th  and new_th.filename:  thumb=save_upload(new_th,'img') or thumb
        db.execute("UPDATE videos SET title=?,description=?,filename=?,youtube_url=?,thumb=?,published=? WHERE id=?",
                   (title,desc,fname,yt_url,thumb,pub,vid))
        db.commit(); db.close()
        flash('Video güncellendi.', 'success')
        return redirect(url_for('admin_videos'))
    db.close()
    return render_template('admin/video_form.html', video=video)

@app.route('/admin/videolar/delete/<int:vid>', methods=['POST'])
@login_required
def admin_video_delete(vid):
    db=get_db(); db.execute("DELETE FROM videos WHERE id=?", (vid,)); db.commit(); db.close()
    flash('Video silindi.', 'info')
    return redirect(url_for('admin_videos'))

# ═══════════════════════════════════════════════
# ADMIN GALLERY / FAQ / MESSAGES / SETTINGS
# ═══════════════════════════════════════════════

@app.route('/admin/galeri')
@login_required
def admin_gallery():
    db=get_db(); items=db.execute("SELECT * FROM gallery ORDER BY created DESC").fetchall(); db.close()
    return render_template('admin/gallery.html', items=items)

@app.route('/admin/galeri/upload', methods=['POST'])
@login_required
def admin_gallery_upload():
    files=request.files.getlist('files'); caption=request.form.get('caption','')
    db=get_db(); count=0
    for f in files:
        if f and f.filename:
            path=save_upload(f,'img')
            if path: db.execute("INSERT INTO gallery (filename,caption,type) VALUES (?,?,?)", (path,caption,'image')); count+=1
    db.commit(); db.close()
    flash(f'{count} dosya yüklendi.', 'success')
    return redirect(url_for('admin_gallery'))

@app.route('/admin/galeri/delete/<int:gid>', methods=['POST'])
@login_required
def admin_gallery_delete(gid):
    db=get_db(); item=db.execute("SELECT * FROM gallery WHERE id=?", (gid,)).fetchone()
    if item:
        try: os.remove(os.path.join(BASE_DIR,'static',item['filename']))
        except: pass
        db.execute("DELETE FROM gallery WHERE id=?", (gid,)); db.commit()
    db.close(); flash('Silindi.', 'info')
    return redirect(url_for('admin_gallery'))

@app.route('/admin/faqs', methods=['GET','POST'])
@login_required
def admin_faqs():
    db=get_db()
    if request.method=='POST':
        action=request.form.get('action')
        if action=='add':
            db.execute("INSERT INTO faqs (question,answer,sort_order) VALUES (?,?,?)",
                       (request.form['question'],request.form['answer'],request.form.get('sort_order',0)))
            flash('SSS eklendi.','success')
        elif action=='delete':
            db.execute("DELETE FROM faqs WHERE id=?", (request.form['id'],)); flash('Silindi.','info')
        elif action=='edit':
            db.execute("UPDATE faqs SET question=?,answer=?,sort_order=? WHERE id=?",
                       (request.form['question'],request.form['answer'],request.form.get('sort_order',0),request.form['id']))
            flash('Güncellendi.','success')
        db.commit()
    faqs=db.execute("SELECT * FROM faqs ORDER BY sort_order").fetchall(); db.close()
    return render_template('admin/faqs.html', faqs=faqs)

@app.route('/admin/mesajlar')
@login_required
def admin_messages():
    db=get_db(); msgs=db.execute("SELECT * FROM contacts ORDER BY created DESC").fetchall()
    db.execute("UPDATE contacts SET read=1"); db.commit(); db.close()
    return render_template('admin/messages.html', msgs=msgs)

@app.route('/admin/mesajlar/delete/<int:mid>', methods=['POST'])
@login_required
def admin_message_delete(mid):
    db=get_db(); db.execute("DELETE FROM contacts WHERE id=?", (mid,)); db.commit(); db.close()
    return redirect(url_for('admin_messages'))

@app.route('/admin/ayarlar', methods=['GET','POST'])
@login_required
def admin_settings():
    if request.method=='POST':
        db=get_db()
        for key in request.form:
            db.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (key,request.form[key]))
        # Hero video: YouTube URL takes priority, then file upload
        hero_yt = request.form.get('hero_video_youtube','').strip()
        if hero_yt:
            db.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", ('hero_video_youtube', hero_yt))
            db.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", ('hero_video', ''))
        else:
            hero_vid=request.files.get('hero_video_file')
            if hero_vid and hero_vid.filename:
                path=save_upload(hero_vid,'vid')
                if path: db.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", ('hero_video',path))
        logo=request.files.get('logo')
        if logo and logo.filename: logo.save(os.path.join(BASE_DIR,'static','logo.png'))
        db.commit(); db.close()
        flash('Ayarlar kaydedildi.','success')
    cfg=get_all_settings()
    return render_template('admin/settings.html', cfg=cfg)

@app.route('/admin/sifre', methods=['GET','POST'])
@login_required
def admin_change_password():
    error=None
    if request.method=='POST':
        old=request.form.get('old_password',''); new=request.form.get('new_password','')
        db=get_db()
        user=db.execute("SELECT * FROM users WHERE username=? AND password=?", (session['username'],hash_pw(old))).fetchone()
        if user:
            db.execute("UPDATE users SET password=? WHERE username=?", (hash_pw(new),session['username']))
            db.commit(); db.close()
            flash('Şifre güncellendi.','success')
            return redirect(url_for('admin_dashboard'))
        db.close(); error='Mevcut şifre hatalı.'
    return render_template('admin/change_password.html', error=error)

# ═══════════════════════════════════════════════
# ADMIN — TEKNOLOJİ SATIRLARI
# ═══════════════════════════════════════════════

@app.route('/admin/teknoloji', methods=['GET','POST'])
@login_required
def admin_tech():
    db = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            db.execute("INSERT INTO tech_items (icon,title,sort_order,published) VALUES (?,?,?,1)",
                       (request.form['icon'], request.form['title'], request.form.get('sort_order',0)))
            flash('Teknoloji satırı eklendi.','success')
        elif action == 'edit':
            db.execute("UPDATE tech_items SET icon=?,title=?,sort_order=?,published=? WHERE id=?",
                       (request.form['icon'], request.form['title'],
                        request.form.get('sort_order',0), 1 if request.form.get('published') else 0,
                        request.form['id']))
            flash('Güncellendi.','success')
        elif action == 'delete':
            db.execute("DELETE FROM tech_items WHERE id=?", (request.form['id'],))
            flash('Silindi.','info')
        db.commit()
    items = db.execute("SELECT * FROM tech_items ORDER BY sort_order").fetchall()
    db.close()
    return render_template('admin/tech_items.html', items=items)

# ═══════════════════════════════════════════════
# ADMIN — HAKKIMIZDA KARTLARI
# ═══════════════════════════════════════════════

@app.route('/admin/hakkimizda', methods=['GET','POST'])
@login_required
def admin_about():
    db = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            db.execute("INSERT INTO about_cards (icon,title,body,sort_order) VALUES (?,?,?,?)",
                       (request.form['icon'], request.form['title'],
                        request.form['body'], request.form.get('sort_order',0)))
            flash('Kart eklendi.','success')
        elif action == 'edit':
            db.execute("UPDATE about_cards SET icon=?,title=?,body=?,sort_order=? WHERE id=?",
                       (request.form['icon'], request.form['title'],
                        request.form['body'], request.form.get('sort_order',0), request.form['id']))
            flash('Güncellendi.','success')
        elif action == 'delete':
            db.execute("DELETE FROM about_cards WHERE id=?", (request.form['id'],))
            flash('Silindi.','info')
        db.commit()
    cards = db.execute("SELECT * FROM about_cards ORDER BY sort_order").fetchall()
    db.close()
    return render_template('admin/about_cards.html', cards=cards)

# ═══════════════════════════════════════════════
# ADMIN — TICKER YAZILARI
# ═══════════════════════════════════════════════

@app.route('/admin/ticker', methods=['GET','POST'])
@login_required
def admin_ticker():
    db = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            db.execute("INSERT INTO ticker_items (text,sort_order) VALUES (?,?)",
                       (request.form['text'], request.form.get('sort_order',0)))
            flash('Ticker yazısı eklendi.','success')
        elif action == 'edit':
            db.execute("UPDATE ticker_items SET text=?,sort_order=? WHERE id=?",
                       (request.form['text'], request.form.get('sort_order',0), request.form['id']))
            flash('Güncellendi.','success')
        elif action == 'delete':
            db.execute("DELETE FROM ticker_items WHERE id=?", (request.form['id'],))
            flash('Silindi.','info')
        db.commit()
    items = db.execute("SELECT * FROM ticker_items ORDER BY sort_order").fetchall()
    db.close()
    return render_template('admin/ticker.html', items=items)

# ═══════════════════════════════════════════════
# ADMIN — NAVİGASYON
# ═══════════════════════════════════════════════

@app.route('/admin/navigasyon', methods=['GET','POST'])
@login_required
def admin_nav():
    db = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            db.execute("INSERT INTO nav_links (label,url,sort_order,is_external) VALUES (?,?,?,?)",
                       (request.form['label'], request.form['url'],
                        request.form.get('sort_order',0), 1 if request.form.get('is_external') else 0))
            flash('Menü linki eklendi.','success')
        elif action == 'edit':
            db.execute("UPDATE nav_links SET label=?,url=?,sort_order=?,is_external=? WHERE id=?",
                       (request.form['label'], request.form['url'],
                        request.form.get('sort_order',0), 1 if request.form.get('is_external') else 0,
                        request.form['id']))
            flash('Güncellendi.','success')
        elif action == 'delete':
            db.execute("DELETE FROM nav_links WHERE id=?", (request.form['id'],))
            flash('Silindi.','info')
        db.commit()
    links = db.execute("SELECT * FROM nav_links ORDER BY sort_order").fetchall()
    db.close()
    return render_template('admin/nav_links.html', links=links)

# ═══════════════════════════════════════════════
# ADMIN — FOOTER LİNKLERİ
# ═══════════════════════════════════════════════

@app.route('/admin/footer', methods=['GET','POST'])
@login_required
def admin_footer():
    db = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            db.execute("INSERT INTO footer_links (column_name,label,url,sort_order) VALUES (?,?,?,?)",
                       (request.form['column_name'], request.form['label'],
                        request.form['url'], request.form.get('sort_order',0)))
            flash('Footer linki eklendi.','success')
        elif action == 'edit':
            db.execute("UPDATE footer_links SET column_name=?,label=?,url=?,sort_order=? WHERE id=?",
                       (request.form['column_name'], request.form['label'],
                        request.form['url'], request.form.get('sort_order',0), request.form['id']))
            flash('Güncellendi.','success')
        elif action == 'delete':
            db.execute("DELETE FROM footer_links WHERE id=?", (request.form['id'],))
            flash('Silindi.','info')
        db.commit()
    links = db.execute("SELECT * FROM footer_links ORDER BY column_name, sort_order").fetchall()
    db.close()
    cols = {}
    for l in links:
        cols.setdefault(l['column_name'], []).append(l)
    return render_template('admin/footer_links.html', cols=cols, links=links)


# ═══════════════════════════════════════════════
# ADMIN — SAYFALAR (Pages)
# ═══════════════════════════════════════════════

@app.route('/admin/sayfalar')
@login_required
def admin_pages():
    db = get_db()
    pages = db.execute("SELECT * FROM pages ORDER BY sort_order, created DESC").fetchall()
    db.close()
    return render_template('admin/pages.html', pages=pages)

@app.route('/admin/sayfalar/new', methods=['GET','POST'])
@login_required
def admin_page_new():
    if request.method == 'POST':
        title   = request.form.get('title','').strip()
        body    = request.form.get('body','')
        excerpt = request.form.get('excerpt','')
        ptype   = request.form.get('page_type','genel')
        sort    = request.form.get('sort_order', 0)
        pub     = 1 if request.form.get('published') else 0
        slug    = slugify(title)
        image   = save_upload(request.files.get('image'), 'img')
        db      = get_db()
        base, i = slug, 1
        while db.execute("SELECT id FROM pages WHERE slug=?", (slug,)).fetchone():
            slug = f"{base}-{i}"; i += 1
        cur = db.execute(
            "INSERT INTO pages (title,slug,body,excerpt,image,page_type,sort_order,published) VALUES (?,?,?,?,?,?,?,?)",
            (title, slug, body, excerpt, image, ptype, sort, pub))
        page_id = cur.lastrowid
        for idx, f in enumerate(request.files.getlist('media_files')):
            if f and f.filename:
                ext = f.filename.rsplit('.',1)[-1].lower()
                mtype = 'video' if ext in ALLOWED_VID else 'image'
                ftype = 'vid' if mtype == 'video' else 'img'
                path  = save_upload(f, ftype)
                if path:
                    db.execute("INSERT INTO page_media (page_id,filename,media_type,sort_order) VALUES (?,?,?,?)",
                               (page_id, path, mtype, idx))
        db.commit(); db.close()
        flash(f'"{title}" sayfası oluşturuldu.', 'success')
        return redirect(url_for('admin_pages'))
    return render_template('admin/page_form.html', page=None, media=[])

@app.route('/admin/sayfalar/edit/<int:pid>', methods=['GET','POST'])
@login_required
def admin_page_edit(pid):
    db   = get_db()
    page = db.execute("SELECT * FROM pages WHERE id=?", (pid,)).fetchone()
    if not page: db.close(); abort(404)
    media = db.execute("SELECT * FROM page_media WHERE page_id=? ORDER BY sort_order,id", (pid,)).fetchall()
    if request.method == 'POST':
        title   = request.form.get('title','').strip()
        body    = request.form.get('body','')
        excerpt = request.form.get('excerpt','')
        ptype   = request.form.get('page_type','genel')
        sort    = request.form.get('sort_order', 0)
        pub     = 1 if request.form.get('published') else 0
        image   = page['image']
        new_img = request.files.get('image')
        if new_img and new_img.filename: image = save_upload(new_img,'img') or image
        db.execute(
            "UPDATE pages SET title=?,body=?,excerpt=?,image=?,page_type=?,sort_order=?,published=?,updated=datetime('now') WHERE id=?",
            (title, body, excerpt, image, ptype, sort, pub, pid))
        max_o = db.execute("SELECT MAX(sort_order) FROM page_media WHERE page_id=?", (pid,)).fetchone()[0] or 0
        for idx, f in enumerate(request.files.getlist('media_files')):
            if f and f.filename:
                ext = f.filename.rsplit('.',1)[-1].lower()
                mtype = 'video' if ext in ALLOWED_VID else 'image'
                ftype = 'vid' if mtype == 'video' else 'img'
                path  = save_upload(f, ftype)
                if path:
                    db.execute("INSERT INTO page_media (page_id,filename,media_type,sort_order) VALUES (?,?,?,?)",
                               (pid, path, mtype, max_o+idx+1))
        db.commit(); db.close()
        flash('Sayfa güncellendi.', 'success')
        return redirect(url_for('admin_pages'))
    db.close()
    return render_template('admin/page_form.html', page=page, media=media)

@app.route('/admin/sayfalar/delete/<int:pid>', methods=['POST'])
@login_required
def admin_page_delete(pid):
    db = get_db()
    db.execute("DELETE FROM pages WHERE id=?", (pid,))
    db.execute("DELETE FROM page_media WHERE page_id=?", (pid,))
    db.commit(); db.close()
    flash('Sayfa silindi.', 'info')
    return redirect(url_for('admin_pages'))

@app.route('/admin/sayfalar/media/delete/<int:mid>', methods=['POST'])
@login_required
def admin_page_media_delete(mid):
    db    = get_db()
    item  = db.execute("SELECT * FROM page_media WHERE id=?", (mid,)).fetchone()
    pid   = request.form.get('page_id')
    if item:
        if not item['filename'].startswith('http'):
            try: os.remove(os.path.join(BASE_DIR,'static',item['filename']))
            except: pass
        db.execute("DELETE FROM page_media WHERE id=?", (mid,)); db.commit()
    db.close()
    return redirect(url_for('admin_page_edit', pid=pid))

# ═══════════════════════════════════════════════
# ADMIN — SERTİFİKALAR & PATENTLER
# ═══════════════════════════════════════════════

@app.route('/admin/sertifikalar', methods=['GET','POST'])
@login_required
def admin_certificates():
    db = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            image = save_upload(request.files.get('image'), 'img')
            db.execute(
                "INSERT INTO certificates (title,description,image,cert_type,country,year,sort_order,published) VALUES (?,?,?,?,?,?,?,?)",
                (request.form['title'], request.form.get('description',''), image or '',
                 request.form.get('cert_type','patent'), request.form.get('country',''),
                 request.form.get('year') or None, request.form.get('sort_order',0),
                 1 if request.form.get('published') else 0))
            flash('Sertifika/Patent eklendi.','success')
        elif action == 'edit':
            item  = db.execute("SELECT * FROM certificates WHERE id=?", (request.form['id'],)).fetchone()
            image = item['image'] if item else ''
            new_img = request.files.get('image')
            if new_img and new_img.filename: image = save_upload(new_img,'img') or image
            db.execute(
                "UPDATE certificates SET title=?,description=?,image=?,cert_type=?,country=?,year=?,sort_order=?,published=? WHERE id=?",
                (request.form['title'], request.form.get('description',''), image,
                 request.form.get('cert_type','patent'), request.form.get('country',''),
                 request.form.get('year') or None, request.form.get('sort_order',0),
                 1 if request.form.get('published') else 0, request.form['id']))
            flash('Güncellendi.','success')
        elif action == 'delete':
            db.execute("DELETE FROM certificates WHERE id=?", (request.form['id'],))
            flash('Silindi.','info')
        db.commit()
    certs = db.execute("SELECT * FROM certificates ORDER BY sort_order, year DESC").fetchall()
    db.close()
    return render_template('admin/certificates.html', certs=certs)


init_db()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
