
import os
import sqlite3
from pathlib import Path
from functools import wraps
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session,
    flash
)

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)


# Flask uygulamasını başlat
app = Flask(__name__)

# Güvenlik anahtarı ortam değişkeninden alınır
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")

if not app.config["SECRET_KEY"]:
    raise RuntimeError(
        "FLASK_SECRET_KEY ortam değişkenini ayarlayın."
    )


# Veritabanı dosyasının konumu
DB_PATH = Path(__file__).resolve().parent / "diyaliz.db"



# --------------------------------------------------
# VERİTABANI BAĞLANTISI
# --------------------------------------------------

def veritabani_baglantisi():
    baglanti = sqlite3.connect(DB_PATH)
    baglanti.row_factory = sqlite3.Row
    return baglanti

def hasta_sutunlarini_hazirla():
    with veritabani_baglantisi() as baglanti:

        sutunlar = [
            satir["name"]
            for satir in baglanti.execute(
                "PRAGMA table_info(hastalar)"
            ).fetchall()
        ]

        if "durum" not in sutunlar:
            baglanti.execute("""
                ALTER TABLE hastalar
                ADD COLUMN durum TEXT DEFAULT ''
            """)

        if "sure" not in sutunlar:
            baglanti.execute("""
                ALTER TABLE hastalar
                ADD COLUMN sure TEXT DEFAULT ''
            """)

def islem_kaydi_ekle(
    islem_turu,
    islem_aciklamasi,
    hedef_turu=None,
    hedef_id=None,
    onceki_deger=None,
    yeni_deger=None
):

    islem_kaydet(
        kullanici_id=session.get("sekreter_id"),
        kullanici_adi=session.get("kullanici_adi"),
        kullanici_rolu=session.get("rol"),
        islem_turu=islem_turu,
        islem_aciklamasi=islem_aciklamasi,
        hedef_turu=hedef_turu,
        hedef_id=hedef_id,
        onceki_deger=onceki_deger,
        yeni_deger=yeni_deger
    )

hasta_sutunlarini_hazirla()

# --------------------------------------------------
# GİRİŞ KONTROLÜ
# --------------------------------------------------

def giris_gerekli(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "sekreter_id" not in session:
            flash("Devam etmek için giriş yapmalısınız.", "error")
            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return decorated_function


# --------------------------------------------------
# ADMİN YETKİ KONTROLÜ
# --------------------------------------------------

def admin_gerekli(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("rol") != "admin":
            flash("Bu sayfaya erişim yetkiniz yok.", "error")
            return redirect(url_for("hasta_ekrani"))

        return f(*args, **kwargs)

    return decorated_function


# --------------------------------------------------
# GİRİŞ SAYFASI
# --------------------------------------------------

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        kullanici_adi = request.form.get(
            "kullanici_adi", ""
        ).strip()

        sifre = request.form.get("sifre", "")

        with veritabani_baglantisi() as baglanti:
            sekreter = baglanti.execute(
                """
                SELECT id, kullanici_adi, sifre_hash, rol
                FROM sekreterler
                WHERE kullanici_adi = ?
                """,
                (kullanici_adi,)
            ).fetchone()

        if (
            sekreter is not None
            and check_password_hash(
                sekreter["sifre_hash"], sifre
            )
        ):
            # Önceki oturum verilerini temizle
            session.clear()

            # Giriş yapan kullanıcının bilgilerini kaydet
            session["sekreter_id"] = sekreter["id"]
            session["kullanici_adi"] = sekreter["kullanici_adi"]
            session["rol"] = sekreter["rol"]

            flash("Giriş başarılı.", "success")

            return redirect(url_for("hasta_ekrani"))

        flash("Kullanıcı adı veya şifre hatalı.", "error")

    return render_template("login.html")


# --------------------------------------------------
# HASTA YÖNETİMİ EKRANI
# --------------------------------------------------

@app.route("/hasta-ekrani")
@giris_gerekli
def hasta_ekrani():
    with veritabani_baglantisi() as baglanti:
        hastalar = baglanti.execute("""
            SELECT hasta_no, ad_soyad, grup_no
            FROM hastalar
            ORDER BY hasta_no
        """).fetchall()

    return render_template(
        "hasta_yonetimi.html",
        kullanici_adi=session["kullanici_adi"],
        rol=session["rol"],
        hastalar=hastalar
    )

@app.route("/hasta-ekle", methods=["POST"])
@giris_gerekli
def hasta_ekle():

    veri = request.get_json(silent=True) or {}

    hasta_no = veri.get("hasta_no")
    ad_soyad = str(veri.get("ad_soyad", "")).strip()
    grup_no = veri.get("grup_no")

    if not hasta_no or not ad_soyad or not grup_no:
        return jsonify({
            "basarili": False,
            "mesaj": "Lütfen tüm hasta bilgilerini doldurunuz."
        }), 400

    try:
        hasta_no = int(hasta_no)
    except (ValueError, TypeError):
        return jsonify({
            "basarili": False,
            "mesaj": "Hasta numarası geçerli olmalıdır."
        }), 400

    gecerli_gruplar = ["1", "2", "Misafir"]

    grup_no = str(grup_no).strip()

    if grup_no not in gecerli_gruplar:
        return jsonify({
            "basarili": False,
            "mesaj": "Lütfen 1, 2 veya Misafir seçeneklerinden birini seçiniz."
        }), 400

    try:
        with veritabani_baglantisi() as baglanti:

            baglanti.execute("""
                INSERT INTO hastalar
                (hasta_no, ad_soyad, grup_no, durum, sure)
                VALUES (?, ?, ?, '', '')
            """, (hasta_no, ad_soyad, grup_no))

        return jsonify({
            "basarili": True,
            "mesaj": "Hasta başarıyla kaydedildi.",
            "hasta": {
                "hasta_no": hasta_no,
                "ad_soyad": ad_soyad,
                "grup_no": grup_no
            }
        })

    except sqlite3.IntegrityError:
        return jsonify({
            "basarili": False,
            "mesaj": "Bu hasta numarası zaten kayıtlı."
        }), 409

    except sqlite3.Error as hata:
        print("Hasta kayıt hatası:", hata)

        return jsonify({
            "basarili": False,
            "mesaj": "Hasta kaydedilirken bir veritabanı hatası oluştu."
        }), 500

@app.route("/hasta-durum-guncelle", methods=["POST"])
@giris_gerekli
def hasta_durum_guncelle():

    veri = request.get_json(silent=True) or {}

    hasta_no = veri.get("hasta_no")
    durum = str(veri.get("durum", "")).strip()
    sure = str(veri.get("sure", "")).strip()

    gecerli_durumlar = [
        "",
        "hazirlaniyor",
        "basladi",
        "bitti",
        "transfer",
        "iptal"
    ]

    gecerli_sureler = [
        "",
        "30dk",
        "1saat",
        "2saat",
        "3saat",
        "4saat",
        "5saat",
        "6saat"
    ]

    try:
        hasta_no = int(hasta_no)
    except (ValueError, TypeError):
        return jsonify({
            "basarili": False,
            "mesaj": "Geçersiz hasta numarası."
        }), 400

    if durum not in gecerli_durumlar or sure not in gecerli_sureler:
        return jsonify({
            "basarili": False,
            "mesaj": "Geçersiz durum veya süre seçimi."
        }), 400

    try:
        with veritabani_baglantisi() as baglanti:

            sonuc = baglanti.execute("""
                UPDATE hastalar
                SET durum = ?, sure = ?
                WHERE hasta_no = ?
            """, (durum, sure, hasta_no))

            if sonuc.rowcount == 0:
                return jsonify({
                    "basarili": False,
                    "mesaj": "Hasta kaydı bulunamadı."
                }), 404

        return jsonify({
            "basarili": True,
            "mesaj": "Hasta bilgileri güncellendi."
        })

    except sqlite3.Error as hata:
        print("Hasta güncelleme hatası:", hata)

        return jsonify({
            "basarili": False,
            "mesaj": "Veritabanı güncelleme hatası."
        }), 500
# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/dashboard")
@giris_gerekli
def dashboard():

    return render_template(
        "dashboard.html",
        kullanici_adi=session["kullanici_adi"]
    )


# --------------------------------------------------
# ADMİN PANELİ
# --------------------------------------------------

@app.route("/admin")
@giris_gerekli
@admin_gerekli
def admin_paneli():

    with veritabani_baglantisi() as baglanti:
        kullanicilar = baglanti.execute(
            """
            SELECT id, kullanici_adi
            FROM sekreterler
            WHERE rol = 'sekreter'
            ORDER BY kullanici_adi
            """
        ).fetchall()

        return render_template(
            "admin_paneli.html",
            kullanici_adi=session["kullanici_adi"],
            rol=session["rol"],
            kullanicilar=kullanicilar,
            aktif_sayfa="sekreter"
        )


# --------------------------------------------------
# ADMİN HASTA YÖNETİMİ
# --------------------------------------------------

@app.route("/admin/hasta-yonetimi")
@giris_gerekli
@admin_gerekli
def admin_hasta_yonetimi():

    with veritabani_baglantisi() as baglanti:

        hastalar = baglanti.execute("""
            SELECT hasta_no, ad_soyad, grup_no, durum, sure
            FROM hastalar
            ORDER BY hasta_no
        """).fetchall()

    return render_template(
        "admin_hasta_yonetimi.html",
        kullanici_adi=session["kullanici_adi"],
        rol=session["rol"],
        hastalar=hastalar,
        aktif_sayfa="hasta"
    )


# --------------------------------------------------
# ADMİN HASTA EKLEME
# --------------------------------------------------

@app.route("/admin/hasta-ekle", methods=["POST"])
@giris_gerekli
@admin_gerekli
def admin_hasta_ekle():

    hasta_no = request.form.get("hasta_no", "").strip()
    ad_soyad = request.form.get("ad_soyad", "").strip()
    grup_no = request.form.get("grup_no", "").strip()

    # Boş alan kontrolü
    if not hasta_no or not ad_soyad or not grup_no:
        flash("Lütfen bütün hasta bilgilerini doldurunuz.", "error")
        return redirect(url_for("admin_hasta_yonetimi"))

    # Hasta numarası kontrolü
    if not hasta_no.isdigit() or len(hasta_no) > 12:
        flash("Hasta numarası yalnızca rakamlardan oluşmalı ve en fazla 12 basamaklı olmalıdır.", "error")
        return redirect(url_for("admin_hasta_yonetimi"))

    if int(hasta_no) == 0:
        flash("Hasta numarası sıfır olamaz.", "error")
        return redirect(url_for("admin_hasta_yonetimi"))

    # Ad-soyad kontrolü
    if len(ad_soyad) > 50:
        flash("Hasta adı ve soyadı en fazla 50 karakter olabilir.", "error")
        return redirect(url_for("admin_hasta_yonetimi"))

    # Grup kontrolü
    if grup_no not in ["1", "2", "Misafir"]:
        flash("Geçersiz grup numarası.", "error")
        return redirect(url_for("admin_hasta_yonetimi"))

    try:

        with veritabani_baglantisi() as baglanti:

            baglanti.execute("""
                INSERT INTO hastalar
                (hasta_no, ad_soyad, grup_no, durum, sure)
                VALUES (?, ?, ?, '', '')
            """, (hasta_no, ad_soyad, grup_no))

        flash("Hasta başarıyla eklendi.", "success")

    except sqlite3.IntegrityError:
        flash("Bu hasta numarası zaten kayıtlı.", "error")

    except sqlite3.Error as hata:
        print("Admin hasta ekleme hatası:", hata)
        flash("Hasta eklenirken veritabanı hatası oluştu.", "error")

    return redirect(url_for("admin_hasta_yonetimi"))


# --------------------------------------------------
# ADMİN HASTA GÜNCELLEME
# --------------------------------------------------

@app.route(
    "/admin/hasta-guncelle/<eski_hasta_no>",
    methods=["POST"]
)
@giris_gerekli
@admin_gerekli
def admin_hasta_guncelle(eski_hasta_no):

    yeni_hasta_no = request.form.get("hasta_no", "").strip()
    ad_soyad = request.form.get("ad_soyad", "").strip()
    grup_no = request.form.get("grup_no", "").strip()
    durum = request.form.get("durum", "").strip()
    sure = request.form.get("sure", "").strip()

    # Yeni hasta numarası kontrolü
    if not yeni_hasta_no.isdigit() or len(yeni_hasta_no) > 12:
        flash("Hasta numarası yalnızca rakamlardan oluşmalı ve en fazla 12 basamaklı olmalıdır.", "error")
        return redirect(url_for("admin_hasta_yonetimi"))

    if int(yeni_hasta_no) == 0:
        flash("Hasta numarası sıfır olamaz.", "error")
        return redirect(url_for("admin_hasta_yonetimi"))

    # Ad-soyad kontrolü
    if not ad_soyad or len(ad_soyad) > 50:
        flash("Hasta adı ve soyadı boş olamaz ve en fazla 50 karakter olabilir.", "error")
        return redirect(url_for("admin_hasta_yonetimi"))

    # Eski hasta numarası kontrolü
    if not eski_hasta_no.isdigit() or len(eski_hasta_no) > 12:
        flash("Mevcut hasta numarası geçersiz.", "error")
        return redirect(url_for("admin_hasta_yonetimi"))

    gecerli_gruplar = ["1", "2", "Misafir"]

    gecerli_durumlar = [
        "",
        "hazirlaniyor",
        "basladi",
        "bitti",
        "transfer",
        "iptal"
    ]

    gecerli_sureler = [
        "",
        "30dk",
        "1saat",
        "2saat",
        "3saat",
        "4saat",
        "5saat",
        "6saat"
    ]

    if (
        grup_no not in gecerli_gruplar
        or durum not in gecerli_durumlar
        or sure not in gecerli_sureler
    ):
        flash("Geçersiz grup, durum veya süre seçimi.", "error")
        return redirect(url_for("admin_hasta_yonetimi"))

    try:

        with veritabani_baglantisi() as baglanti:

            sonuc = baglanti.execute("""
                UPDATE hastalar
                SET hasta_no = ?,
                    ad_soyad = ?,
                    grup_no = ?,
                    durum = ?,
                    sure = ?
                WHERE hasta_no = ?
            """, (
                yeni_hasta_no,
                ad_soyad,
                grup_no,
                durum,
                sure,
                eski_hasta_no
            ))

            if sonuc.rowcount == 0:
                flash("Hasta kaydı bulunamadı.", "error")
                return redirect(url_for("admin_hasta_yonetimi"))

        flash("Hasta bilgileri başarıyla güncellendi.", "success")

    except sqlite3.IntegrityError:
        flash("Bu hasta numarası başka bir hastaya ait.", "error")

    except sqlite3.Error as hata:
        print("Hasta güncelleme hatası:", hata)
        flash("Hasta güncellenirken veritabanı hatası oluştu.", "error")

    return redirect(url_for("admin_hasta_yonetimi"))

# --------------------------------------------------
# ADMİN HASTA SİLME
# --------------------------------------------------

@app.route(
    "/admin/hasta-sil/<int:hasta_no>",
    methods=["POST"]
)
@giris_gerekli
@admin_gerekli
def admin_hasta_sil(hasta_no):

    try:

        with veritabani_baglantisi() as baglanti:

            sonuc = baglanti.execute("""
                DELETE FROM hastalar
                WHERE hasta_no = ?
            """, (hasta_no,))

            if sonuc.rowcount == 0:
                flash("Silinecek hasta bulunamadı.", "error")
            else:
                flash("Hasta başarıyla silindi.", "success")

    except sqlite3.Error as hata:
        print("Hasta silme hatası:", hata)
        flash("Hasta silinirken veritabanı hatası oluştu.", "error")

    return redirect(url_for("admin_hasta_yonetimi"))    

# --------------------------------------------------
# YENİ SEKRETER HESABI OLUŞTURMA
# --------------------------------------------------

@app.route("/admin/kullanici-ekle", methods=["POST"])
@giris_gerekli
@admin_gerekli
def kullanici_ekle():

    kullanici_adi = request.form.get(
        "kullanici_adi", ""
    ).strip()

    sifre = request.form.get("sifre", "")
    sifre_tekrar = request.form.get("sifre_tekrar", "")

    # Form kontrolleri
    if not kullanici_adi:
        flash("Kullanıcı adı boş olamaz.", "error")

    elif len(kullanici_adi) > 100:
        flash(
            "Kullanıcı adı en fazla 100 karakter olabilir.",
            "error"
        )

    elif len(sifre) < 8:
        flash("Şifre en az 8 karakter olmalıdır.", "error")

    elif sifre != sifre_tekrar:
        flash("Şifreler eşleşmiyor.", "error")

    else:
        # Şifreyi açık metin olarak kaydetme
        sifre_hash = generate_password_hash(sifre)

        try:
            with veritabani_baglantisi() as baglanti:
                baglanti.execute(
                    """
                    INSERT INTO sekreterler
                        (kullanici_adi, sifre_hash, rol)
                    VALUES (?, ?, 'sekreter')
                    """,
                    (kullanici_adi, sifre_hash)
                )

            flash(
                "Yeni sekreter hesabı oluşturuldu.",
                "success"
            )

        except sqlite3.IntegrityError:
            flash(
                "Bu kullanıcı adı zaten kullanılıyor.",
                "error"
            )

    return redirect(url_for("admin_paneli"))

@app.route("/admin/kullanici-sil/<int:kullanici_id>", methods=["POST"])
@giris_gerekli
@admin_gerekli
def kullanici_sil(kullanici_id):

    with veritabani_baglantisi() as baglanti:
        kullanici = baglanti.execute(
            """
            SELECT id, kullanici_adi, rol
            FROM sekreterler
            WHERE id = ?
            """,
            (kullanici_id,)
        ).fetchone()

        if kullanici is None:
            flash("Kullanıcı bulunamadı.", "error")

        elif kullanici["rol"] != "sekreter":
            flash("Admin hesabı bu ekrandan silinemez.", "error")

        else:
            baglanti.execute(
                "DELETE FROM sekreterler WHERE id = ?",
                (kullanici_id,)
            )
            flash(
                f'{kullanici["kullanici_adi"]} hesabı silindi.',
                "success"
            )

    return redirect(url_for("admin_paneli"))
# --------------------------------------------------
# ÇIKIŞ YAP
# --------------------------------------------------

@app.route("/logout", methods=["POST"])
@giris_gerekli
def logout():

    session.clear()

    flash("Başarıyla çıkış yaptınız.", "success")

    return redirect(url_for("login"))


# --------------------------------------------------
# TELEVİZYON EKRANI API
# --------------------------------------------------

# --------------------------------------------------
# TELEVİZYON EKRANI API
# --------------------------------------------------

def hasta_adi_gizle(ad_soyad):
    kelimeler = ad_soyad.split()

    gizli_kelimeler = [
        kelime[:2].upper() + "****"
        for kelime in kelimeler
    ]

    return " ".join(gizli_kelimeler)


@app.route("/api/hasta-durumlari")
def tv_hasta_durumlari():

    try:
        with veritabani_baglantisi() as baglanti:

            hastalar = baglanti.execute("""
                SELECT ad_soyad, durum
                FROM hastalar
                WHERE durum IS NOT NULL
                  AND durum != ''
                ORDER BY  hasta_no
            """).fetchall()

        hasta_listesi = [
            {
                "ad_soyad": hasta_adi_gizle(hasta["ad_soyad"]),
                "durum": hasta["durum"]
            }
            for hasta in hastalar
        ]

        return jsonify({
            "basarili": True,
            "hastalar": hasta_listesi
        })

    except sqlite3.Error as hata:
        print("TV veri çekme hatası:", hata)

        return jsonify({
            "basarili": False,
            "mesaj": "Hasta bilgileri alınamadı."
        }), 500


# --------------------------------------------------
# TELEVİZYON EKRANI
# --------------------------------------------------

@app.route("/tv")
def tv_ekrani():
    return render_template("tv_ekrani.html")

# --------------------------------------------------
# UYGULAMAYI BAŞLAT
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0", port=5000)
