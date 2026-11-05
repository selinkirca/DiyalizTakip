
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "diyaliz.db"

kullanici_adi = "selin"

with sqlite3.connect(DB_PATH) as baglanti:
    sonuc = baglanti.execute("""
        UPDATE sekreterler
        SET rol = 'admin'
        WHERE kullanici_adi = ?
    """, (kullanici_adi,))

    if sonuc.rowcount > 0:
        print(f"{kullanici_adi} kullanıcısı admin yapıldı.")
    else:
        print("Kullanıcı bulunamadı.")
