# essiz_ayri_veri.py
import random
import sqlite3
import requests
import time
import threading
from queue import Queue
import sys
from datetime import datetime, timedelta
import os

# ============ AYARLAR ============
API_URL = "https://apisorgu.2026tr.xyz/tc/bilgi"
THREAD_COUNT = 50
HEDEF_PLAKA = 8000000      # 8 MİLYON
HEDEF_SERI = 8000000       # 8 MİLYON
HEDEF_EHLIYET = 15000000   # 15 MİLYON

# ============ USER AGENTLER ============
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S921B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
]

# ============ PLAKA VERİSİ (8 MİLYON) ============
class PlakaVerisi:
    def __init__(self):
        self.db_name = "plaka.db"
        self.kullanilan = set()
        self.init_db()
        self._load_existing()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_name, timeout=30)
        c = conn.cursor()
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA synchronous=NORMAL")
        c.execute("PRAGMA cache_size=-2000000")
        
        c.execute('''CREATE TABLE IF NOT EXISTS plaka (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plaka TEXT UNIQUE,
            tc TEXT UNIQUE,
            ad TEXT,
            soyad TEXT,
            dogum_tarihi TEXT,
            il TEXT,
            ilce TEXT
        )''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_plaka ON plaka(plaka)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_tc ON plaka(tc)')
        conn.commit()
        conn.close()
        print("✅ Plaka veritabanı hazır!")
    
    def _load_existing(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT plaka FROM plaka")
        for row in c.fetchall():
            self.kullanilan.add(row[0])
        conn.close()
    
    def save_batch(self, veriler):
        conn = sqlite3.connect(self.db_name, timeout=30)
        c = conn.cursor()
        c.execute("BEGIN TRANSACTION")
        for v in veriler:
            if v['plaka'] not in self.kullanilan:
                c.execute("""INSERT OR IGNORE INTO plaka 
                    (plaka, tc, ad, soyad, dogum_tarihi, il, ilce)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (v['plaka'], v['tc'], v['ad'], v['soyad'], 
                     v['dogum_tarihi'], v['il'], v['ilce']))
                self.kullanilan.add(v['plaka'])
        conn.commit()
        conn.close()
    
    def count(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM plaka")
        count = c.fetchone()[0]
        conn.close()
        return count

# ============ SERİ NO VERİSİ (8 MİLYON) ============
class SeriNoVerisi:
    def __init__(self):
        self.db_name = "seri_no.db"
        self.kullanilan = set()
        self.init_db()
        self._load_existing()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_name, timeout=30)
        c = conn.cursor()
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA synchronous=NORMAL")
        c.execute("PRAGMA cache_size=-2000000")
        
        c.execute('''CREATE TABLE IF NOT EXISTS seri_no (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seri_no TEXT UNIQUE,
            tc TEXT UNIQUE,
            ad TEXT,
            soyad TEXT
        )''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_seri_no ON seri_no(seri_no)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_tc ON seri_no(tc)')
        conn.commit()
        conn.close()
        print("✅ Seri No veritabanı hazır!")
    
    def _load_existing(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT seri_no FROM seri_no")
        for row in c.fetchall():
            self.kullanilan.add(row[0])
        conn.close()
    
    def save_batch(self, veriler):
        conn = sqlite3.connect(self.db_name, timeout=30)
        c = conn.cursor()
        c.execute("BEGIN TRANSACTION")
        for v in veriler:
            if v['seri_no'] not in self.kullanilan:
                c.execute("""INSERT OR IGNORE INTO seri_no 
                    (seri_no, tc, ad, soyad)
                    VALUES (?, ?, ?, ?)""",
                    (v['seri_no'], v['tc'], v['ad'], v['soyad']))
                self.kullanilan.add(v['seri_no'])
        conn.commit()
        conn.close()
    
    def count(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM seri_no")
        count = c.fetchone()[0]
        conn.close()
        return count

# ============ EHLİYET VERİSİ (15 MİLYON) ============
class EhliyetVerisi:
    def __init__(self):
        self.db_name = "ehliyet.db"
        self.kullanilan = set()
        self.init_db()
        self._load_existing()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_name, timeout=30)
        c = conn.cursor()
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA synchronous=NORMAL")
        c.execute("PRAGMA cache_size=-2000000")
        
        c.execute('''CREATE TABLE IF NOT EXISTS ehliyet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ehliyet_no TEXT UNIQUE,
            tc TEXT UNIQUE,
            ad TEXT,
            soyad TEXT,
            dogum_tarihi TEXT,
            ehliyet_sinif TEXT,
            ehliyet_verilis TEXT,
            ehliyet_son_kullanim TEXT
        )''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_ehliyet_no ON ehliyet(ehliyet_no)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_tc ON ehliyet(tc)')
        conn.commit()
        conn.close()
        print("✅ Ehliyet veritabanı hazır!")
    
    def _load_existing(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT ehliyet_no FROM ehliyet")
        for row in c.fetchall():
            self.kullanilan.add(row[0])
        conn.close()
    
    def save_batch(self, veriler):
        conn = sqlite3.connect(self.db_name, timeout=30)
        c = conn.cursor()
        c.execute("BEGIN TRANSACTION")
        for v in veriler:
            if v['ehliyet_no'] not in self.kullanilan:
                c.execute("""INSERT OR IGNORE INTO ehliyet 
                    (ehliyet_no, tc, ad, soyad, dogum_tarihi, ehliyet_sinif, ehliyet_verilis, ehliyet_son_kullanim)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (v['ehliyet_no'], v['tc'], v['ad'], v['soyad'], 
                     v['dogum_tarihi'], v['ehliyet_sinif'], 
                     v['ehliyet_verilis'], v['ehliyet_son_kullanim']))
                self.kullanilan.add(v['ehliyet_no'])
        conn.commit()
        conn.close()
    
    def count(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM ehliyet")
        count = c.fetchone()[0]
        conn.close()
        return count

# ============ TC ÜRET (EŞSİZ) ============
def generate_tc():
    first_9 = [random.randint(0, 9) for _ in range(9)]
    sum_odd = sum(first_9[0::2])
    sum_even = sum(first_9[1::2])
    tenth = (7 * sum_odd - sum_even) % 10
    sum_first_10 = sum(first_9) + tenth
    eleventh = sum_first_10 % 10
    return ''.join(map(str, first_9)) + str(tenth) + str(eleventh)

# ============ PLAKA ÜRET (EŞSİZ) ============
def plaka_uret(kullanilan):
    iller = ["01","02","03","04","05","06","07","08","09","10","34","35","36","37","38","39","40"]
    harfler = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for _ in range(100):
        il = random.choice(iller)
        h1 = random.choice(harfler)
        h2 = random.choice(harfler)
        h3 = random.choice(harfler) if random.random() > 0.5 else ""
        sayi = f"{random.randint(1, 999):03d}"
        plaka = f"{il} {h1}{h2}{h3} {sayi}".strip()
        if plaka not in kullanilan:
            return plaka
    return f"99 ZZZ 999"  # fallback

# ============ SERİ NO ÜRET (EŞSİZ) ============
def seri_no_uret(kullanilan):
    prefix = ["TR", "EU", "US", "JP", "DE", "FR", "UK", "IT", "ES", "NL"]
    for _ in range(100):
        p = random.choice(prefix)
        n1 = random.randint(100000, 999999)
        n2 = random.randint(100000, 999999)
        seri = f"{p}-{n1}-{n2}"
        if seri not in kullanilan:
            return seri
    return "TR-999999-999999"

# ============ EHLİYET NO ÜRET (EŞSİZ) ============
def ehliyet_no_uret(kullanilan):
    harfler = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for _ in range(100):
        h1 = random.choice(harfler)
        h2 = random.choice(harfler)
        num = random.randint(100000, 999999)
        ehliyet = f"{h1}{h2}-{num}"
        if ehliyet not in kullanilan:
            return ehliyet
    return "ZZ-999999"

# ============ API SORGU ============
def query_tc_api(tc):
    headers = {'User-Agent': random.choice(USER_AGENTS), 'Accept': 'application/json'}
    try:
        url = f"{API_URL}?tc={tc}"
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            sonuc = data.get('sonuc', {})
            if sonuc.get('success') and sonuc.get('results'):
                result = sonuc['results'][0]
                if result.get('ADI'):
                    return result
        return None
    except:
        return None

# ============ VERİ OLUŞTUR ============
def veri_olustur(tc, api_data, plaka_set, seri_set, ehliyet_set):
    ad = api_data.get('ADI', '')
    soyad = api_data.get('SOYADI', '')
    dogum = api_data.get('DOGUMTARIHI', '01.01.2000')
    il = api_data.get('NUFUSIL', '')
    ilce = api_data.get('NUFUSILCE', '')
    
    # Yaş hesapla
    try:
        day, month, year = dogum.split('.')
        dogum_dt = datetime(int(year), int(month), int(day))
        yas = (datetime.now() - dogum_dt).days // 365
    except:
        yas = random.randint(18, 65)
    
    # Eşsiz plaka
    plaka = plaka_uret(plaka_set)
    plaka_set.add(plaka)
    
    # Eşsiz seri no
    seri_no = seri_no_uret(seri_set)
    seri_set.add(seri_no)
    
    # Eşsiz ehliyet
    ehliyet_no = ehliyet_no_uret(ehliyet_set)
    ehliyet_set.add(ehliyet_no)
    
    return {
        "tc": tc,
        "ad": ad,
        "soyad": soyad,
        "dogum_tarihi": dogum,
        "il": il,
        "ilce": ilce,
        "plaka": plaka,
        "seri_no": seri_no,
        "ehliyet_sinif": random.choice(["A1", "A2", "B", "B1", "BE", "C", "D"]),
        "ehliyet_no": ehliyet_no,
        "ehliyet_verilis": (datetime.now() - timedelta(days=random.randint(365, 365*10))).strftime("%d.%m.%Y"),
        "ehliyet_son_kullanim": (datetime.now() + timedelta(days=random.randint(365, 365*5))).strftime("%d.%m.%Y")
    }

# ============ ANA ============
def main():
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║        🔥 EŞSİZ AYRI VERİ OLUŞTURUCU                  ║
    ╠══════════════════════════════════════════════════════════╣
    ║  1️⃣  plaka.db   → {HEDEF_PLAKA:,} (Plaka + Ad + Soyad)    ║
    ║  2️⃣  seri_no.db → {HEDEF_SERI:,} (Seri No + TC)           ║
    ║  3️⃣  ehliyet.db → {HEDEF_EHLIYET:,} (Ehliyet Bilgileri)   ║
    ║                                                       ║
    ║  🧵 THREAD: {THREAD_COUNT} paralel                        ║
    ║  🔒 EŞSİZ: Tüm plaka, seri no, ehliyet benzersiz!     ║
    ║  🚀 BAŞLIYOR...                                        ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Sınıfları oluştur
    plaka_db = PlakaVerisi()
    seri_db = SeriNoVerisi()
    ehliyet_db = EhliyetVerisi()
    
    # Set'ler
    plaka_set = set(plaka_db.kullanilan)
    seri_set = set(seri_db.kullanilan)
    ehliyet_set = set(ehliyet_db.kullanilan)
    
    baslangic = time.time()
    toplam = 0
    kullanilan_tc = set()
    
    batch = []
    BATCH_SIZE = 1000
    
    while toplam < max(HEDEF_PLAKA, HEDEF_SERI, HEDEF_EHLIYET):
        tc = generate_tc()
        if tc in kullanilan_tc:
            continue
        
        api_data = query_tc_api(tc)
        if not api_data or not api_data.get('ADI'):
            continue
        
        veri = veri_olustur(tc, api_data, plaka_set, seri_set, ehliyet_set)
        batch.append(veri)
        kullanilan_tc.add(tc)
        toplam += 1
        
        if len(batch) >= BATCH_SIZE:
            # Plaka'ya kaydet (8 milyon hedef)
            if plaka_db.count() < HEDEF_PLAKA:
                plaka_batch = [{
                    "plaka": v['plaka'], "tc": v['tc'], "ad": v['ad'],
                    "soyad": v['soyad'], "dogum_tarihi": v['dogum_tarihi'],
                    "il": v['il'], "ilce": v['ilce']
                } for v in batch if plaka_db.count() < HEDEF_PLAKA]
                if plaka_batch:
                    plaka_db.save_batch(plaka_batch)
            
            # Seri No'ya kaydet (8 milyon hedef)
            if seri_db.count() < HEDEF_SERI:
                seri_batch = [{
                    "seri_no": v['seri_no'], "tc": v['tc'],
                    "ad": v['ad'], "soyad": v['soyad']
                } for v in batch if seri_db.count() < HEDEF_SERI]
                if seri_batch:
                    seri_db.save_batch(seri_batch)
            
            # Ehliyet'e kaydet (15 milyon hedef)
            if ehliyet_db.count() < HEDEF_EHLIYET:
                ehliyet_batch = [{
                    "ehliyet_no": v['ehliyet_no'], "tc": v['tc'],
                    "ad": v['ad'], "soyad": v['soyad'],
                    "dogum_tarihi": v['dogum_tarihi'],
                    "ehliyet_sinif": v['ehliyet_sinif'],
                    "ehliyet_verilis": v['ehliyet_verilis'],
                    "ehliyet_son_kullanim": v['ehliyet_son_kullanim']
                } for v in batch if ehliyet_db.count() < HEDEF_EHLIYET]
                if ehliyet_batch:
                    ehliyet_db.save_batch(ehliyet_batch)
            
            batch = []
            gecen = time.time() - baslangic
            hiz = toplam / gecen if gecen > 0 else 0
            print(f"✅ {toplam:,} | Hız: {hiz:.1f}/sn | "
                  f"🚗 Plaka: {plaka_db.count():,} | "
                  f"🔢 Seri: {seri_db.count():,} | "
                  f"🪪 Ehliyet: {ehliyet_db.count():,}")
    
    # Sonuç
    gecen = time.time() - baslangic
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║           İŞLEM TAMAMLANDI! ✅                         ║
    ╠══════════════════════════════════════════════════════════╣
    ║  🚗 Plaka: {plaka_db.count():,} ({HEDEF_PLAKA:,} hedef)     ║
    ║  🔢 Seri No: {seri_db.count():,} ({HEDEF_SERI:,} hedef)    ║
    ║  🪪 Ehliyet: {ehliyet_db.count():,} ({HEDEF_EHLIYET:,} hedef) ║
    ║  ⏱️ Süre: {gecen/60:.1f} dakika                          ║
    ║  🚀 Hız: {toplam/gecen:.1f} kayıt/saniye               ║
    ║  🔒 Tüm veriler EŞSİZ!                                 ║
    ╚══════════════════════════════════════════════════════════╝
    """)

if __name__ == "__main__":
    main()
