
import sqlite3
from pathlib import Path
from getpass import getpass
from werkzeug.security import generate_password_hash

DB_PATH = Path(__file__).resolve().parent / "diyaliz.db"


<<<<<<< HEAD
def veritabani_olustur():
    with sqlite3.connect(DB_PATH) as baglanti:

        # Sekreterler tablosu
=======

def veritabani_olustur():
    with sqlite3.connect(DB_PATH) as baglanti:
>>>>>>> 4944183e79519d726f8e1117a4cc6313d45a6b46
        baglanti.execute("""
            CREATE TABLE IF NOT EXISTS sekreterler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kullanici_adi TEXT NOT NULL UNIQUE,
<<<<<<< HEAD
                sifre_hash TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT 'sekreter'
            )
        """)

        # Hastalar tablosu
        baglanti.execute("""
            CREATE TABLE IF NOT EXISTS hastalar (
                hasta_no INTEGER PRIMARY KEY,
                ad_soyad TEXT NOT NULL,
                grup_no INTEGER NOT NULL
            )
        """)

        # Sekreterler tablosunda rol sütununu kontrol et
=======
                sifre_hash TEXT NOT NULL
            )
        """)

>>>>>>> 4944183e79519d726f8e1117a4cc6313d45a6b46
        sutunlar = [
            sutun[1]
            for sutun in baglanti.execute(
                "PRAGMA table_info(sekreterler)"
            ).fetchall()
        ]

        if "rol" not in sutunlar:
            baglanti.execute("""
                ALTER TABLE sekreterler
                ADD COLUMN rol TEXT NOT NULL DEFAULT 'sekreter'
            """)

<<<<<<< HEAD
        # Örnek hasta kaydı
        baglanti.execute("""
            INSERT OR IGNORE INTO hastalar
                (hasta_no, ad_soyad, grup_no)
            VALUES (?, ?, ?)
        """, (1, "Ahmet Yılmaz", 1))

        baglanti.commit()

    print("Veritabanı hazırlandı.")
    print("Sekreterler ve hastalar tabloları kontrol edildi.")


def admin_olustur():
    print("\n--- ADMIN HESABI OLUŞTURMA ---")

    kullanici_adi = input("Admin kullanıcı adı: ").strip()

    if not kullanici_adi:
        print("Kullanıcı adı boş olamaz.")
        return

    sifre = getpass("Admin şifresi (en az 8 karakter): ")
    sifre_tekrar = getpass("Admin şifresini tekrar girin: ")

    if len(sifre) < 8:
        print("Şifre en az 8 karakter olmalıdır.")
        return

    if sifre != sifre_tekrar:
        print("Şifreler eşleşmiyor.")
=======
    print("Veritabani hazirlandi.")


def admin_olustur():
    print("\n--- ADMIN HESABI OLUSTURMA ---")

    kullanici_adi = input("Admin kullanici adi: ").strip()

    if not kullanici_adi:
        print("Kullanici adi bos olamaz.")
        return

    sifre = getpass("Admin sifresi (en az 8 karakter): ")
    sifre_tekrar = getpass("Admin sifresini tekrar girin: ")

    if len(sifre) < 8:
        print("Sifre en az 8 karakter olmalidir.")
        return

    if sifre != sifre_tekrar:
        print("Sifreler eslesmiyor.")
>>>>>>> 4944183e79519d726f8e1117a4cc6313d45a6b46
        return

    sifre_hash = generate_password_hash(sifre)

    try:
        with sqlite3.connect(DB_PATH) as baglanti:
            baglanti.execute("""
                INSERT INTO sekreterler
                    (kullanici_adi, sifre_hash, rol)
                VALUES (?, ?, 'admin')
            """, (kullanici_adi, sifre_hash))

<<<<<<< HEAD
        print("Admin hesabı başarıyla oluşturuldu.")

    except sqlite3.IntegrityError:
        print("Bu kullanıcı adı zaten mevcut.")
        print("Farklı bir kullanıcı adı deneyin.")
=======
        print("Admin hesabi basariyla olusturuldu.")

    except sqlite3.IntegrityError:
        print("Bu kullanici adi zaten mevcut.")
        print("Farkli bir kullanici adi deneyin.")
>>>>>>> 4944183e79519d726f8e1117a4cc6313d45a6b46


if __name__ == "__main__":
    veritabani_olustur()
    admin_olustur()
