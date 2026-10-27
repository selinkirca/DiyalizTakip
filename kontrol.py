
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "diyaliz.db"

with sqlite3.connect(DB_PATH) as baglanti:
    baglanti.row_factory = sqlite3.Row

    kullanicilar = baglanti.execute("""
        SELECT id, kullanici_adi, rol
        FROM sekreterler
    """).fetchall()

    for kullanici in kullanicilar:
        print(
            "ID:", kullanici["id"],
            "| Kullanıcı adı:", kullanici["kullanici_adi"],
            "| Rol:", kullanici["rol"]
        )

    if not kullanicilar:
        print("Veritabanında hiç kullanıcı yok.")
