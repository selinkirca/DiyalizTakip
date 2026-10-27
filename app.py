
import os
import sqlite3
from pathlib import Path
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
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
    return render_template(
        "hasta_yonetimi.html",
        kullanici_adi=session["kullanici_adi"],
        rol=session["rol"]
    )


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
        kullanicilar=kullanicilar
    )


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
# UYGULAMAYI BAŞLAT
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
