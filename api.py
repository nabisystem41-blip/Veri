# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import requests
import json
import os
import time
from datetime import datetime
from collections import defaultdict
import threading

app = Flask(__name__)

# ============ KONFİG ============
app.config['JSON_AS_ASCII'] = False

# ============ RATE LIMITING ============
class RateLimiter:
    def __init__(self, max_requests=3, time_window=1):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)
        self.lock = threading.Lock()
    
    def is_allowed(self, client_id):
        with self.lock:
            now = time.time()
            cutoff = now - 60
            self.requests[client_id] = [t for t in self.requests[client_id] if t > cutoff]
            recent = [t for t in self.requests[client_id] if t > now - self.time_window]
            if len(recent) >= self.max_requests:
                return False, len(recent)
            self.requests[client_id].append(now)
            return True, len(recent) + 1

rate_limiter = RateLimiter(max_requests=3, time_window=1)

def rate_limit(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_id = request.remote_addr
        if request.headers.get('X-Forwarded-For'):
            client_id = request.headers.get('X-Forwarded-For').split(',')[0]
        
        allowed, count = rate_limiter.is_allowed(client_id)
        if not allowed:
            return jsonify({
                'hata': 'Rate limit aşıldı',
                'mesaj': 'Saniyede maksimum 3 sorgu yapabilirsiniz',
                'limit': 3
            }), 429
        return f(*args, **kwargs)
    return decorated_function

# ============ PUNISHER BASE ============
PUNISHER_BASE = "https://punisherservices.alwaysdata.net/apiservices"

def punisher_request(endpoint, params=None):
    try:
        url = f"{PUNISHER_BASE}/{endpoint}"
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            try:
                return response.json()
            except:
                return {'raw': response.text}
        else:
            return {'hata': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'hata': str(e)}

# ============================================================
# TC SORGULAMA
# ============================================================

@app.route("/tc/bilgi", methods=["GET"])
@rate_limit
def tc_bilgi():
    tc = request.args.get('tc')
    if not tc or len(tc) != 11:
        return jsonify({'hata': '11 haneli TC zorunlu'}), 400
    return jsonify(punisher_request('tc.php', {'tc': tc}))

@app.route("/tc/pro", methods=["GET"])
@rate_limit
def tc_pro():
    tc = request.args.get('tc')
    if not tc or len(tc) != 11:
        return jsonify({'hata': '11 haneli TC zorunlu'}), 400
    return jsonify(punisher_request('tcpro.php', {'tc': tc}))

@app.route("/tc/tum", methods=["GET"])
@rate_limit
def tc_tum():
    tc = request.args.get('tc')
    if not tc or len(tc) != 11:
        return jsonify({'hata': '11 haneli TC zorunlu'}), 400
    
    sonuc = {'tc': tc, 'zaman': datetime.now().isoformat()}
    endpoints = {
        'tc': f'tc.php?tc={tc}',
        'aile': f'aile.php?tc={tc}',
        'adres': f'adres.php?tc={tc}',
        'isyeri': f'isyeri.php?tc={tc}',
        'tcgsm': f'tcgsm.php?tc={tc}'
    }
    for name, endpoint in endpoints.items():
        sonuc[name] = punisher_request(endpoint)
    return jsonify(sonuc)

# ============================================================
# AD SOYAD SORGULAMA
# ============================================================

@app.route("/adsoyad/bilgi", methods=["GET"])
@rate_limit
def adsoyad_bilgi():
    ad = request.args.get('ad')
    soyad = request.args.get('soyad')
    if not ad or not soyad:
        return jsonify({'hata': 'AD ve SOYAD zorunlu'}), 400
    return jsonify(punisher_request('adsoyad.php', {'ad': ad, 'soyad': soyad}))

@app.route("/adsoyad/pro", methods=["GET"])
@rate_limit
def adsoyad_pro():
    ad = request.args.get('ad')
    soyad = request.args.get('soyad')
    if not ad or not soyad:
        return jsonify({'hata': 'AD ve SOYAD zorunlu'}), 400
    return jsonify(punisher_request('adsoyadpro.php', {'ad': ad, 'soyad': soyad}))

# ============================================================
# AİLE SORGULAMA
# ============================================================

@app.route("/aile/bilgi", methods=["GET"])
@rate_limit
def aile_bilgi():
    tc = request.args.get('tc')
    if not tc or len(tc) != 11:
        return jsonify({'hata': '11 haneli TC zorunlu'}), 400
    return jsonify(punisher_request('aile.php', {'tc': tc}))

@app.route("/aile/pro", methods=["GET"])
@rate_limit
def aile_pro():
    tc = request.args.get('tc')
    if not tc or len(tc) != 11:
        return jsonify({'hata': '11 haneli TC zorunlu'}), 400
    return jsonify(punisher_request('ailepro.php', {'tc': tc}))

@app.route("/anne/sorgu", methods=["GET"])
@rate_limit
def anne_sorgu():
    tc = request.args.get('tc')
    if not tc or len(tc) != 11:
        return jsonify({'hata': '11 haneli TC zorunlu'}), 400
    
    tc_bilgi = punisher_request('tc.php', {'tc': tc})
    anne_tc = None
    
    if isinstance(tc_bilgi, dict):
        anne_tc = tc_bilgi.get('anne_tc')
        if not anne_tc and 'data' in tc_bilgi and isinstance(tc_bilgi['data'], dict):
            anne_tc = tc_bilgi['data'].get('anne_tc')
    
    if anne_tc:
        return jsonify(punisher_request('tc.php', {'tc': anne_tc}))
    return jsonify({'mesaj': 'Anne TC bulunamadı'})

@app.route("/baba/sorgu", methods=["GET"])
@rate_limit
def baba_sorgu():
    tc = request.args.get('tc')
    if not tc or len(tc) != 11:
        return jsonify({'hata': '11 haneli TC zorunlu'}), 400
    
    tc_bilgi = punisher_request('tc.php', {'tc': tc})
    baba_tc = None
    
    if isinstance(tc_bilgi, dict):
        baba_tc = tc_bilgi.get('baba_tc')
        if not baba_tc and 'data' in tc_bilgi and isinstance(tc_bilgi['data'], dict):
            baba_tc = tc_bilgi['data'].get('baba_tc')
    
    if baba_tc:
        return jsonify(punisher_request('tc.php', {'tc': baba_tc}))
    return jsonify({'mesaj': 'Baba TC bulunamadı'})

@app.route("/cocuk/sorgu", methods=["GET"])
@rate_limit
def cocuk_sorgu():
    tc = request.args.get('tc')
    if not tc or len(tc) != 11:
        return jsonify({'hata': '11 haneli TC zorunlu'}), 400
    return jsonify(punisher_request('cocuk.php', {'tc': tc}))

@app.route("/es/sorgu", methods=["GET"])
@rate_limit
def es_sorgu():
    tc = request.args.get('tc')
    if not tc or len(tc) != 11:
        return jsonify({'hata': '11 haneli TC zorunlu'}), 400
    return jsonify(punisher_request('es.php', {'tc': tc}))

@app.route("/kardes/sorgu", methods=["GET"])
@rate_limit
def kardes_sorgu():
    tc = request.args.get('tc')
    if not tc or len(tc) != 11:
        return jsonify({'hata': '11 haneli TC zorunlu'}), 400
    return jsonify(punisher_request('kardes.php', {'tc': tc}))

@app.route("/sulale/bilgi", methods=["GET"])
@rate_limit
def sulale_bilgi():
    tc = request.args.get('tc')
    if not tc or len(tc) != 11:
        return jsonify({'hata': '11 haneli TC zorunlu'}), 400
    return jsonify(punisher_request('sulale.php', {'tc': tc}))

@app.route("/sulale/pro", methods=["GET"])
@rate_limit
def sulale_pro():
    tc = request.args.get('tc')
    if not tc or len(tc) != 11:
        return jsonify({'hata': '11 haneli TC zorunlu'}), 400
    return jsonify(punisher_request('sulalepro.php', {'tc': tc}))

# ============================================================
# ADRES & İŞYERİ
# ============================================================

@app.route("/adres/sorgu", methods=["GET"])
@rate_limit
def adres_sorgu():
    tc = request.args.get('tc')
    if not tc or len(tc) != 11:
        return jsonify({'hata': '11 haneli TC zorunlu'}), 400
    return jsonify(punisher_request('adres.php', {'tc': tc}))

@app.route("/isyeri/sorgu", methods=["GET"])
@rate_limit
def isyeri_sorgu():
    tc = request.args.get('tc')
    if not tc or len(tc) != 11:
        return jsonify({'hata': '11 haneli TC zorunlu'}), 400
    return jsonify(punisher_request('isyeri.php', {'tc': tc}))

@app.route("/tapu/sorgu", methods=["GET"])
@rate_limit
def tapu_sorgu():
    tc = request.args.get('tc')
    if not tc or len(tc) != 11:
        return jsonify({'hata': '11 haneli TC zorunlu'}), 400
    return jsonify(punisher_request('tapu.php', {'tc': tc}))

# ============================================================
# GSM SORGULAMA
# ============================================================

@app.route("/tc-gsm/sorgu", methods=["GET"])
@rate_limit
def tc_gsm():
    tc = request.args.get('tc')
    if not tc or len(tc) != 11:
        return jsonify({'hata': '11 haneli TC zorunlu'}), 400
    return jsonify(punisher_request('tcgsm.php', {'tc': tc}))

@app.route("/gsm-tc/sorgu", methods=["GET"])
@rate_limit
def gsm_tc():
    gsm = request.args.get('gsm')
    if not gsm:
        return jsonify({'hata': 'GSM zorunlu'}), 400
    return jsonify(punisher_request('gsmtc.php', {'gsm': gsm}))

# ============================================================
# ÖZEL SORGULAR
# ============================================================

@app.route("/dogum-ilce/sorgu", methods=["GET"])
@rate_limit
def dogum_ilce():
    dogumt = request.args.get('dogumt')
    il = request.args.get('il')
    ilce = request.args.get('ilce')
    if not dogumt or not il or not ilce:
        return jsonify({'hata': 'dogumt, il ve ilce zorunlu'}), 400
    return jsonify(punisher_request('dogumtililce.php', {'dogumt': dogumt, 'il': il, 'ilce': ilce}))

@app.route("/soyad-dogum/sorgu", methods=["GET"])
@rate_limit
def soyad_dogum():
    dogumt = request.args.get('dogumt')
    soyad = request.args.get('soyad')
    if not dogumt or not soyad:
        return jsonify({'hata': 'dogumt ve soyad zorunlu'}), 400
    return jsonify(punisher_request('soyaddogumt.php', {'dogumt': dogumt, 'soyad': soyad}))

@app.route("/iban/sorgu", methods=["GET"])
@rate_limit
def iban_sorgu():
    iban = request.args.get('iban')
    if not iban:
        return jsonify({'hata': 'IBAN zorunlu'}), 400
    return jsonify(punisher_request('iban.php', {'iban': iban}))

@app.route("/operator/sorgu", methods=["GET"])
@rate_limit
def operator_sorgu():
    numara = request.args.get('numara')
    if not numara:
        return jsonify({'hata': 'Numara zorunlu'}), 400
    return jsonify(punisher_request('gncloperator.php', {'numara': numara}))

# ============================================================
# ANA SAYFA - Developer bilgisi YOK
# ============================================================

@app.route("/")
def home():
    return jsonify({
        "service": "Nabi API Service",
        "status": "online",
        "version": "4.0",
        "rate_limit": "3 sorgu/saniye",
        "total_endpoints": 23,
        "endpoints": {
            "tc": {
                "bilgi": "/tc/bilgi?tc=11111111110",
                "pro": "/tc/pro?tc=11111111110",
                "tum": "/tc/tum?tc=11111111110"
            },
            "adsoyad": {
                "bilgi": "/adsoyad/bilgi?ad=roket&soyad=atar",
                "pro": "/adsoyad/pro?ad=roket&soyad=atar"
            },
            "aile": {
                "bilgi": "/aile/bilgi?tc=11111111110",
                "pro": "/aile/pro?tc=11111111110",
                "anne": "/anne/sorgu?tc=11111111110",
                "baba": "/baba/sorgu?tc=11111111110",
                "cocuk": "/cocuk/sorgu?tc=11111111110",
                "es": "/es/sorgu?tc=11111111110",
                "kardes": "/kardes/sorgu?tc=11111111110",
                "sulale": "/sulale/bilgi?tc=11111111110",
                "sulale_pro": "/sulale/pro?tc=11111111110"
            },
            "adres_isyeri": {
                "adres": "/adres/sorgu?tc=11111111110",
                "isyeri": "/isyeri/sorgu?tc=11111111110",
                "tapu": "/tapu/sorgu?tc=11111111110"
            },
            "gsm": {
                "tc_gsm": "/tc-gsm/sorgu?tc=11111111110",
                "gsm_tc": "/gsm-tc/sorgu?gsm=5415722525"
            },
            "ozel": {
                "dogum_ilce": "/dogum-ilce/sorgu?dogumt=17.03.1998&il=İstanbul&ilce=Kadıköy",
                "soyad_dogum": "/soyad-dogum/sorgu?dogumt=17.03.1998&soyad=DENİZ",
                "iban": "/iban/sorgu?iban=TR280006256953335759003718",
                "operator": "/operator/sorgu?numara=5315312472"
            }
        }
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "OK",
        "version": "4.0",
        "timestamp": datetime.now().isoformat(),
        "rate_limit": "3/s",
        "encoding": "UTF-8"
    })

# ============================================================
# BAŞLAT
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("="*60)
    print("🌿 NABI API SERVICE")
    print("="*60)
    print(f"📡 PORT: {port}")
    print(f"🔒 RATE LIMIT: 3 sorgu/saniye")
    print(f"📊 TOTAL API: 23")
    print(f"🌐 http://localhost:{port}")
    print("="*60)
    app.run(host="0.0.0.0", port=port)
