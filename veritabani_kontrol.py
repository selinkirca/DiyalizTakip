import sqlite3

baglanti = sqlite3.connect("diyaliz.db")
baglanti.row_factory = sqlite3.Row

tablolar = ["hastalar", "sekreterler"]

for tablo in tablolar:

    print("\n" + "=" * 60)
    print(f"{tablo.upper()} TABLOSU")
    print("=" * 60)

    # Sütun bilgileri
    sutunlar = baglanti.execute(
        f"PRAGMA table_info({tablo})"
    ).fetchall()

    print("\nSÜTUNLAR:")

    for sutun in sutunlar:
        print(
            f"Ad: {sutun['name']} | "
            f"Tür: {sutun['type']} | "
            f"Primary Key: {sutun['pk']}"
        )

    # Tablo kayıtları
    kayitlar = baglanti.execute(
        f"SELECT * FROM {tablo}"
    ).fetchall()

    print("\nSEKRETERLER:")

    if kayitlar:
        for kayit in kayitlar:
            print(dict(kayit))
    else:
        print("Tabloda kayıt bulunmuyor.")

    print(f"\nToplam kayıt sayısı: {len(kayitlar)}")

baglanti.close()