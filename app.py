from flask import Flask, render_template, request, redirect, url_for, flash, session
import pyodbc
from functools import wraps
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")  # Güvenlik için rastgele bir şey yazın

# --- 1. VERİTABANI BAĞLANTISI (MSSQL) ---
def baglanti_kur():
    try:
        conn = pyodbc.connect(
            f"DRIVER={{{os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')}}};"
            f"SERVER={os.getenv('DB_SERVER', 'localhost\SQLEXPRESS')};"
            f"DATABASE={os.getenv('DB_NAME', 'KutuphaneDB')};"
            f"Trusted_Connection={os.getenv('DB_TRUSTED_CONNECTION', 'yes')};"
            f"TrustServerCertificate={os.getenv('DB_TRUST_SERVER_CERTIFICATE', 'yes')};"
        )
        return conn
    except Exception as e:
        print("Veritabanı Bağlantı Hatası:", e)
        return None

# --- YARDIMCI FONKSİYONLAR ---
# MSSQL verileri 'tuple' olarak döner (Örn: (1, 'Ali')). 
# HTML şablonlarında 'item.ad' diyebilmek için bunları Sözlüğe (Dict) çevirmeliyiz.

def sozluge_cevir(cursor, row):
    """Tek bir satırı sözlüğe çevirir."""
    if not row:
        return None
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))

def liste_sozluge_cevir(cursor, rows):
    """Satır listesini sözlük listesine çevirir."""
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in rows]

# --- 2. GÜVENLİK DECORATORLARI (YETKİ KONTROLLERİ) ---
def giris_gerekli(f):
    @wraps(f)
    def sarmalanan_fonksiyon(*args, **kwargs):
        if 'giris_yapildi' not in session:
            flash("Bu sayfayı görmek için önce giriş yapmalısınız.", "warning")
            return redirect(url_for('giris'))
        return f(*args, **kwargs)
    return sarmalanan_fonksiyon

def admin_gerekli(f):
    @wraps(f)
    def sarmalanan_fonksiyon(*args, **kwargs):
        if session.get('rol') != 'admin':
            flash("Bu işlem için yetkiniz yok! (Sadece Adminler)", "danger")
            return redirect(url_for('ana_sayfa'))
        return f(*args, **kwargs)
    return sarmalanan_fonksiyon

# --- 3. GİRİŞ, KAYIT VE ÇIKIŞ İŞLEMLERİ ---
@app.route('/giris', methods=['GET', 'POST'])
def giris():
    if request.method == 'POST':
        eposta = request.form['eposta']
        sifre = request.form['sifre']
        
        conn = baglanti_kur()
        if conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM Uyeler WHERE eposta = ?", (eposta,))
            row = cursor.fetchone()
            kullanici = sozluge_cevir(cursor, row)
            conn.close()

            if kullanici and check_password_hash(kullanici['sifre'], sifre):
                session['giris_yapildi'] = True
                session['ad_soyad'] = kullanici['ad_soyad']
                session['id'] = kullanici['id']
                session['rol'] = kullanici['rol'] 
                
                flash(f"Hoş geldin, {kullanici['ad_soyad']}", "success")
                
                if session['rol'] == 'admin':
                    return redirect(url_for('ana_sayfa'))
                else:
                    return redirect(url_for('uye_detay', id=kullanici['id']))
            else:
                flash("Hatalı E-posta veya Şifre!", "danger")
        else:
            flash("Veritabanı bağlantısı kurulamadı!", "danger")
            
    return render_template('giris.html')

@app.route('/kayit', methods=['GET', 'POST'])
def kayit_ol():
    if 'giris_yapildi' in session:
        return redirect(url_for('ana_sayfa'))

    if request.method == 'POST':
        ad_soyad = request.form['ad_soyad']
        telefon = request.form['telefon']
        eposta = request.form['eposta']
        sifre = request.form['sifre']
        hashli_sifre = generate_password_hash(sifre)
        
        conn = baglanti_kur()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO Uyeler (ad_soyad, telefon, eposta, sifre, rol) 
                VALUES (?, ?, ?, ?, 'uye')
            """, (ad_soyad, telefon, eposta, hashli_sifre))
            
            conn.commit()
            flash("Kayıt başarılı! Şimdi giriş yapabilirsiniz.", "success")
            conn.close()
            return redirect(url_for('giris'))
            
        except pyodbc.IntegrityError:
            flash("Bu E-posta adresi zaten sistemde kayıtlı!", "danger")
            conn.close()
            
    return render_template('kayit.html')

@app.route('/cikis')
def cikis():
    session.clear()
    flash("Başarıyla çıkış yapıldı.", "info")
    return redirect(url_for('giris'))


@app.route('/')
def ana_sayfa():
    conn = baglanti_kur()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Kitaplar")
    toplam_kitap = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Uyeler")
    toplam_uye = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Odunc WHERE durum = 'Aktif'")
    genel_odunc_sayisi = cursor.fetchone()[0]

    son_hareketler = []
    gecikenler = []
    odunc_verilen = genel_odunc_sayisi

    if session.get('giris_yapildi'): 
        if session.get('rol') == 'admin':
            cursor.execute("""
                SELECT TOP 5 Uyeler.ad_soyad, Kitaplar.baslik, Odunc.alis_tarihi, Odunc.durum 
                FROM Odunc
                JOIN Uyeler ON Odunc.uye_id = Uyeler.id
                JOIN Kitaplar ON Odunc.kitap_id = Kitaplar.id
                ORDER BY Odunc.id DESC
            """)
            son_hareketler = liste_sozluge_cevir(cursor, cursor.fetchall())
            
            cursor.execute("""
                SELECT Uyeler.ad_soyad, Kitaplar.baslik, 
                DATEDIFF(day, Odunc.alis_tarihi, GETDATE()) as gecen_gun
                FROM Odunc
                JOIN Uyeler ON Odunc.uye_id = Uyeler.id
                JOIN Kitaplar ON Odunc.kitap_id = Kitaplar.id
                WHERE Odunc.durum = 'Aktif' AND DATEDIFF(day, Odunc.alis_tarihi, GETDATE()) > 15
                ORDER BY gecen_gun DESC
            """)
            gecikenler = liste_sozluge_cevir(cursor, cursor.fetchall())

        else:
            cursor.execute("SELECT COUNT(*) FROM Odunc WHERE uye_id = ? AND durum = 'Aktif'", (session['id'],))
            odunc_verilen = cursor.fetchone()[0]

            cursor.execute("""
                SELECT TOP 5 Uyeler.ad_soyad, Kitaplar.baslik, Odunc.alis_tarihi, Odunc.durum 
                FROM Odunc
                JOIN Uyeler ON Odunc.uye_id = Uyeler.id
                JOIN Kitaplar ON Odunc.kitap_id = Kitaplar.id
                WHERE Odunc.uye_id = ? 
                ORDER BY Odunc.id DESC
            """, (session['id'],))
            son_hareketler = liste_sozluge_cevir(cursor, cursor.fetchall())

            cursor.execute("""
                SELECT Uyeler.ad_soyad, Kitaplar.baslik, 
                DATEDIFF(day, Odunc.alis_tarihi, GETDATE()) as gecen_gun
                FROM Odunc
                JOIN Uyeler ON Odunc.uye_id = Uyeler.id
                JOIN Kitaplar ON Odunc.kitap_id = Kitaplar.id
                WHERE Odunc.durum = 'Aktif' AND DATEDIFF(day, Odunc.alis_tarihi, GETDATE()) > 15 AND Odunc.uye_id = ?
                ORDER BY gecen_gun DESC
            """, (session['id'],))
            gecikenler = liste_sozluge_cevir(cursor, cursor.fetchall())

    conn.close()
    return render_template('index.html', 
                          t_kitap=toplam_kitap, 
                          t_uye=toplam_uye, 
                          t_odunc=odunc_verilen,
                          hareketler=son_hareketler,
                          gecikenler=gecikenler)


@app.route('/kitaplar', methods=['GET', 'POST'])
def kitaplar():
    conn = baglanti_kur()
    cursor = conn.cursor()

    if request.method == 'POST':
        if not session.get('giris_yapildi'):
            flash("Kitap eklemek için önce giriş yapmalısınız.", "warning")
            return redirect(url_for('giris'))

        if session.get('rol') != 'admin':
            flash("Kitap ekleme yetkiniz yok!", "danger")
            return redirect(url_for('kitaplar'))

        baslik = request.form['baslik']
        yazar = request.form['yazar']
        tur = request.form['tur']
        stok = request.form['stok']
        sayfa = request.form['sayfa_sayisi']
        yayinevi = request.form['yayinevi']
        yil = request.form['basim_yili']

        cursor.execute("""
            INSERT INTO Kitaplar (baslik, yazar, tur, stok, sayfa_sayisi, yayinevi, basim_yili) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (baslik, yazar, tur, stok, sayfa, yayinevi, yil))
        
        conn.commit()
        conn.close()
        flash("Kitap başarıyla eklendi.", "success")
        return redirect(url_for('kitaplar'))

    cursor.execute("SELECT * FROM Kategoriler")
    kategoriler = liste_sozluge_cevir(cursor, cursor.fetchall())
    
    cursor.execute("SELECT * FROM Kitaplar ORDER BY id DESC")
    kitap_listesi = liste_sozluge_cevir(cursor, cursor.fetchall())
    
    conn.close()
    return render_template('kitaplar.html', kitaplar=kitap_listesi, kategoriler=kategoriler)

@app.route('/ara')
def kitap_ara():
    arama_kelimesi = request.args.get('arama') 
    conn = baglanti_kur()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM Kategoriler")
    kategoriler = liste_sozluge_cevir(cursor, cursor.fetchall())
    
    if arama_kelimesi:
        sql = "SELECT * FROM Kitaplar WHERE baslik LIKE ? OR yazar LIKE ?"
        param = '%' + arama_kelimesi + '%'
        cursor.execute(sql, (param, param))
        sonuclar = liste_sozluge_cevir(cursor, cursor.fetchall())
        flash(f"'{arama_kelimesi}' için sonuçlar listeleniyor.", "info")
    else:
        sonuclar = [] 
        
    conn.close()
 
    return render_template('kitaplar.html', kitaplar=sonuclar, kategoriler=kategoriler)

@app.route('/kitaplar/sil/<int:id>')
@giris_gerekli
@admin_gerekli
def kitap_sil(id):
    conn = baglanti_kur()
    cursor = conn.cursor()
    
    cursor.execute("SELECT count(*) FROM Odunc WHERE kitap_id = ? AND durum = 'Aktif'", (id,))
    if cursor.fetchone()[0] > 0:
        flash("Bu kitap şu an bir üyede! Önce teslim almalısınız.", "danger")
    else:
        cursor.execute("DELETE FROM Kitaplar WHERE id = ?", (id,))
        conn.commit()
        flash("Kitap başarıyla silindi.", "success")
    
    conn.close()
    return redirect(url_for('kitaplar'))

@app.route('/kitaplar/duzenle/<int:id>', methods=['GET', 'POST'])
@giris_gerekli
@admin_gerekli
def kitap_duzenle(id):
    conn = baglanti_kur()
    cursor = conn.cursor()

    if request.method == 'POST':
        baslik = request.form['baslik']
        yazar = request.form['yazar']
        tur = request.form['tur']
        stok = request.form['stok']
        sayfa = request.form['sayfa_sayisi'] 
        yayinevi = request.form['yayinevi']  
        yil = request.form['basim_yili']     
        
        cursor.execute("""
            UPDATE Kitaplar 
            SET baslik=?, yazar=?, tur=?, stok=?, sayfa_sayisi=?, yayinevi=?, basim_yili=?
            WHERE id=?
        """, (baslik, yazar, tur, stok, sayfa, yayinevi, yil, id))
        
        conn.commit()
        conn.close()
        flash("Kitap bilgileri güncellendi.", "success")
        return redirect(url_for('kitaplar'))
    
    cursor.execute("SELECT * FROM Kitaplar WHERE id = ?", (id,))
    kitap = sozluge_cevir(cursor, cursor.fetchone())
    conn.close()
    
    return render_template('kitap_duzenle.html', kitap=kitap)

# --- 6. ÜYE YÖNETİMİ ---
@app.route('/uyeler', methods=['GET', 'POST'])
@giris_gerekli
@admin_gerekli
def uyeler():
    conn = baglanti_kur()
    cursor = conn.cursor()

    if request.method == 'POST':
        ad_soyad = request.form['ad_soyad']
        telefon = request.form['telefon']
        eposta = request.form['eposta']
        try:
            # Admin eklediğinde varsayılan şifre '1234'
            varsayilan_sifre = generate_password_hash("1234")

            cursor.execute("""
                INSERT INTO Uyeler (ad_soyad, telefon, eposta, sifre, rol) 
                VALUES (?, ?, ?, ?, 'uye')
            """, (ad_soyad, telefon, eposta, varsayilan_sifre))

            conn.commit()
            flash("Yeni üye kaydedildi. (Varsayılan Şifre: 1234)", "success")
            
        except pyodbc.IntegrityError:
            flash("Bu E-posta adresi zaten kayıtlı!", "danger")
        
        conn.close()
        return redirect(url_for('uyeler'))
    
    cursor.execute("SELECT * FROM Uyeler ORDER BY id DESC")
    uye_listesi = liste_sozluge_cevir(cursor, cursor.fetchall())
    conn.close()
    
    return render_template('uyeler.html', uyeler=uye_listesi)

@app.route('/uyeler/sil/<int:id>')
@giris_gerekli
@admin_gerekli
def uye_sil(id):
    conn = baglanti_kur()
    cursor = conn.cursor()
    
    cursor.execute("SELECT count(*) FROM Odunc WHERE uye_id = ? AND durum = 'Aktif'", (id,))
    aktif_kitap_sayisi = cursor.fetchone()[0]
    
    if aktif_kitap_sayisi > 0:
        flash(f"Bu üyenin elinde {aktif_kitap_sayisi} adet teslim edilmemiş kitap var!", "danger")
    else:
        cursor.execute("DELETE FROM Rezervasyonlar WHERE uye_id = ?", (id,))
        cursor.execute("DELETE FROM Uyeler WHERE id = ?", (id,))
        conn.commit()
        flash("Üye silindi.", "success")
    
    conn.close()
    return redirect(url_for('uyeler'))

@app.route('/uyeler/detay/<int:id>')
def uye_detay(id):
    if 'rol' not in session:
         return redirect(url_for('giris'))
    if session['rol'] != 'admin' and session['id'] != id:
        return redirect(url_for('ana_sayfa'))

    conn = baglanti_kur()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Uyeler WHERE id = ?", (id,))
    uye = sozluge_cevir(cursor, cursor.fetchone())

    cursor.execute("""
        SELECT Kitaplar.baslik, Kitaplar.tur, Odunc.alis_tarihi, Odunc.id
        FROM Odunc
        JOIN Kitaplar ON Odunc.kitap_id = Kitaplar.id
        WHERE Odunc.uye_id = ? AND Odunc.durum = 'Aktif'
    """, (id,))
    elindekiler = liste_sozluge_cevir(cursor, cursor.fetchall())

    cursor.execute("""
        SELECT Kitaplar.baslik, Kitaplar.yazar, Odunc.alis_tarihi, Odunc.iade_tarihi
        FROM Odunc
        JOIN Kitaplar ON Odunc.kitap_id = Kitaplar.id
        WHERE Odunc.uye_id = ? AND Odunc.durum = 'Teslim Edildi'
        ORDER BY Odunc.iade_tarihi DESC
    """, (id,))
    gecmis = liste_sozluge_cevir(cursor, cursor.fetchall())

    toplam_okunan = len(gecmis) + len(elindekiler)

    conn.close()
    return render_template('uye_detay.html', uye=uye, elindekiler=elindekiler, gecmis=gecmis, toplam=toplam_okunan)

# --- 7. ÖDÜNÇ VE REZERVASYON İŞLEMLERİ ---
@app.route('/odunc')
@giris_gerekli
@admin_gerekli
def odunc_listesi():
    conn = baglanti_kur()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            Odunc.id, 
            Uyeler.ad_soyad, 
            Kitaplar.baslik, 
            Odunc.alis_tarihi,
            DATEDIFF(day, Odunc.alis_tarihi, GETDATE()) as gecen_gun
        FROM Odunc 
        JOIN Uyeler ON Odunc.uye_id = Uyeler.id 
        JOIN Kitaplar ON Odunc.kitap_id = Kitaplar.id
        WHERE Odunc.durum = 'Aktif'
    """)
    aktif_hareketler = liste_sozluge_cevir(cursor, cursor.fetchall())

    cursor.execute("SELECT id, ad_soyad FROM Uyeler")
    uyeler = liste_sozluge_cevir(cursor, cursor.fetchall())

    cursor.execute("SELECT id, baslik, stok FROM Kitaplar WHERE stok > 0")
    kitaplar = liste_sozluge_cevir(cursor, cursor.fetchall())

    conn.close()
    return render_template('odunc.html', hareketler=aktif_hareketler, uyeler=uyeler, kitaplar=kitaplar)

@app.route('/odunc/ver', methods=['POST'])
@giris_gerekli
@admin_gerekli
def odunc_ver():
    uye_id = request.form['uye_id']
    kitap_id = request.form['kitap_id']
    
    conn = baglanti_kur()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO Odunc (uye_id, kitap_id, alis_tarihi) VALUES (?, ?, GETDATE())", (uye_id, kitap_id))
    cursor.execute("UPDATE Kitaplar SET stok = stok - 1 WHERE id = ?", (kitap_id,))
    
    conn.commit()
    conn.close()
    return redirect(url_for('odunc_listesi'))

@app.route('/odunc/iade/<int:id>')
@giris_gerekli
@admin_gerekli
def iade_al(id):
    conn = baglanti_kur()
    cursor = conn.cursor()

    cursor.execute("SELECT kitap_id FROM Odunc WHERE id = ?", (id,))
    kitap_id = cursor.fetchone()[0]

    cursor.execute("""
        SELECT TOP 1 Uyeler.ad_soyad FROM Rezervasyonlar 
        JOIN Uyeler ON Rezervasyonlar.uye_id = Uyeler.id
        WHERE kitap_id = ? AND durum = 'Beklemede' 
        ORDER BY talep_tarihi ASC
    """, (kitap_id,))
    siradaki_kisi = cursor.fetchone()
    
    if siradaki_kisi:
        flash(f"İade alındı. DİKKAT: Sırada bekleyen var: {siradaki_kisi[0]}", "warning")
    else:
        flash("Kitap başarıyla iade alındı.", "success")

    cursor.execute("UPDATE Odunc SET durum = 'Teslim Edildi', iade_tarihi = GETDATE() WHERE id = ?", (id,))
    cursor.execute("UPDATE Kitaplar SET stok = stok + 1 WHERE id = ?", (kitap_id,))
    
    conn.commit()
    conn.close()
    return redirect(url_for('odunc_listesi'))

@app.route('/rezervasyon/talep/<int:kitap_id>', methods=['POST'])
@giris_gerekli
def rezervasyon_talep(kitap_id):
    if session.get('rol') == 'admin':
        flash("Yöneticiler rezervasyon yapamaz.", "warning")
        return redirect(url_for('kitaplar'))

    conn = baglanti_kur()
    cursor = conn.cursor()
    uye_id = session['id']
    MAX_KOTA = 3  
    
    # Kota Kontrolü
    cursor.execute("SELECT COUNT(*) FROM Odunc WHERE uye_id = ? AND durum = 'Aktif'", (uye_id,))
    elindeki_sayi = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Rezervasyonlar WHERE uye_id = ? AND durum = 'Beklemede'", (uye_id,))
    bekleyen_sayi = cursor.fetchone()[0]

    if (elindeki_sayi + bekleyen_sayi) >= MAX_KOTA:
        flash(f"Kota Dolu! Toplam {MAX_KOTA} sınırını aştınız.", "danger")
        conn.close()
        return redirect(url_for('kitaplar'))

    # Mükerrer talep kontrolü
    cursor.execute("SELECT id FROM Rezervasyonlar WHERE uye_id = ? AND kitap_id = ? AND durum = 'Beklemede'", (uye_id, kitap_id))
    if cursor.fetchone():
        flash("Zaten bekleyen talebiniz var.", "warning")
    else:
        cursor.execute("INSERT INTO Rezervasyonlar (uye_id, kitap_id, talep_tarihi) VALUES (?, ?, GETDATE())", (uye_id, kitap_id))
        conn.commit()
        flash("Talep alındı.", "success")

    conn.close()
    return redirect(url_for('kitaplar'))

@app.route('/rezervasyonlar')
@giris_gerekli
@admin_gerekli
def rezervasyonlar():
    conn = baglanti_kur()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT Rezervasyonlar.id, Uyeler.ad_soyad, Kitaplar.baslik, Rezervasyonlar.talep_tarihi, Rezervasyonlar.durum, Kitaplar.stok
        FROM Rezervasyonlar
        JOIN Uyeler ON Rezervasyonlar.uye_id = Uyeler.id
        JOIN Kitaplar ON Rezervasyonlar.kitap_id = Kitaplar.id
        ORDER BY CASE WHEN Rezervasyonlar.durum = 'Beklemede' THEN 0 ELSE 1 END, Rezervasyonlar.talep_tarihi DESC
    """)
    talepler = liste_sozluge_cevir(cursor, cursor.fetchall())
    conn.close()
    return render_template('rezervasyonlar.html', talepler=talepler)

@app.route('/rezervasyon/onayla/<int:id>')
@giris_gerekli
@admin_gerekli
def rezervasyon_onayla(id):
    conn = baglanti_kur()
    cursor = conn.cursor()

    cursor.execute("SELECT kitap_id, uye_id FROM Rezervasyonlar WHERE id = ?", (id,))
    talep = cursor.fetchone()
    
    if talep:
        kitap_id, uye_id = talep
        cursor.execute("SELECT stok FROM Kitaplar WHERE id = ?", (kitap_id,))
        stok = cursor.fetchone()[0]
        
        if stok > 0:
            cursor.execute("UPDATE Rezervasyonlar SET durum = 'Onaylandı' WHERE id = ?", (id,))
            cursor.execute("INSERT INTO Odunc (uye_id, kitap_id, alis_tarihi) VALUES (?, ?, GETDATE())", (uye_id, kitap_id))
            cursor.execute("UPDATE Kitaplar SET stok = stok - 1 WHERE id = ?", (kitap_id,))
            conn.commit()
            flash("Rezervasyon onaylandı.", "success")
        else:
            flash("Stok yetersiz! Önce kitap iadesi alınmalı.", "danger")
            
    conn.close()
    return redirect(url_for('rezervasyonlar'))

@app.route('/rezervasyon/reddet/<int:id>')
@giris_gerekli
@admin_gerekli
def rezervasyon_reddet(id):
    conn = baglanti_kur()
    cursor = conn.cursor()
    cursor.execute("UPDATE Rezervasyonlar SET durum = 'Reddedildi' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Talep reddedildi.", "warning")
    return redirect(url_for('rezervasyonlar'))

# --- 8. KATEGORİ VE GEÇMİŞ YÖNETİMİ ---
@app.route('/kategoriler', methods=['GET', 'POST'])
@giris_gerekli
@admin_gerekli
def kategoriler():
    conn = baglanti_kur()
    cursor = conn.cursor()

    if request.method == 'POST':
        yeni_kategori = request.form['kategori_adi']
        try:
            cursor.execute("INSERT INTO Kategoriler (ad) VALUES (?)", (yeni_kategori,))
            conn.commit()
            flash("Yeni kategori eklendi.", "success")
        except pyodbc.IntegrityError:
            flash("Bu kategori zaten mevcut!", "warning")

    cursor.execute("SELECT * FROM Kategoriler ORDER BY ad ASC")
    kategori_listesi = liste_sozluge_cevir(cursor, cursor.fetchall())
    conn.close()
    return render_template('kategoriler.html', kategoriler=kategori_listesi)

@app.route('/kategoriler/sil/<int:id>')
@giris_gerekli
@admin_gerekli
def kategori_sil(id):
    conn = baglanti_kur()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Kategoriler WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Kategori silindi.", "success")
    return redirect(url_for('kategoriler'))

@app.route('/gecmis')
@giris_gerekli
@admin_gerekli
def islem_gecmisi():
    conn = baglanti_kur()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Odunc.id, Uyeler.ad_soyad, Kitaplar.baslik, Odunc.alis_tarihi, Odunc.iade_tarihi, Odunc.durum 
        FROM Odunc
        JOIN Uyeler ON Odunc.uye_id = Uyeler.id
        JOIN Kitaplar ON Odunc.kitap_id = Kitaplar.id
        ORDER BY Odunc.id DESC
    """)
    tum_kayitlar = liste_sozluge_cevir(cursor, cursor.fetchall())
    conn.close()
    return render_template('gecmis.html', kayitlar=tum_kayitlar)

if __name__ == '__main__':
    app.run(debug=True)