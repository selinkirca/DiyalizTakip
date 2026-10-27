
import sqlite3
from pathlib import Path
from getpass import getpass
from werkzeug.security import generate_password_hash

DB_PATH = Path(__file__).resolve().parent / "diyaliz.db"



def veritabani_olustur():
    with sqlite3.connect(DB_PATH) as baglanti:
        baglanti.execute("""
            CREATE TABLE IF NOT EXISTS sekreterler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kullanici_adi TEXT NOT NULL UNIQUE,
                sifre_hash TEXT NOT NULL
            )
        """)

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
        return

    sifre_hash = generate_password_hash(sifre)

    try:
        with sqlite3.connect(DB_PATH) as baglanti:
            baglanti.execute("""
                INSERT INTO sekreterler
                    (kullanici_adi, sifre_hash, rol)
                VALUES (?, ?, 'admin')
            """, (kullanici_adi, sifre_hash))

        print("Admin hesabi basariyla olusturuldu.")

    except sqlite3.IntegrityError:
        print("Bu kullanici adi zaten mevcut.")
        print("Farkli bir kullanici adi deneyin.")


if __name__ == "__main__":
    veritabani_olustur()
    admin_olustur()
