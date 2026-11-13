
const tvTarihSaat = document.getElementById("tvTarihSaat");

function tarihSaatGuncelle() {
    const simdi = new Date();

    const tarih = simdi.toLocaleDateString("tr-TR", {
        day: "2-digit",
        month: "long",
        year: "numeric"
    });

    const saat = simdi.toLocaleTimeString("tr-TR", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    });

    tvTarihSaat.textContent = `${tarih} | ${saat}`;
}

tarihSaatGuncelle();
setInterval(tarihSaatGuncelle, 1000);

const hastaListesi = document.getElementById("hastaListesi");
const baglantiDurumu = document.getElementById("baglantiDurumu");

const sayfaHastaSayisi = 5;
const sayfaGecisSuresi = 10000;
const guncellemeSuresi = 3000;
const gosterimSuresi = 60000;

let hastalar = [];
let mevcutSayfa = 0;

// Sunucuda zaman bilgisi bulunmadığında geçici zaman takibi
const ilkGorulmeZamanlari = new Map();

const durumlar = {
    hazirlaniyor: {
        metin: "Hasta hazırlanıyor",
        sinif: ""
    },
    basladi: {
        metin: "Diyaliz işlemi başladı",
        sinif: ""
    },
    bitti: {
        metin: "Diyaliz tedavisi tamamlandı",
        sinif: "durum-bitti"
    },
    transfer: {
        metin: "Hasta kliniğe transfer edildi",
        sinif: "durum-transfer"
    },
    iptal: {
        metin: "Diyaliz işlemi iptal edildi",
        sinif: "durum-iptal"
    }
};

// Gösterim süresi dolan hastaları ayıkla


function gecerliHastalariGetir() {

    const simdi = Date.now();

    const gecerliHastalar = hastalar.filter(hasta => {

        if (hasta.durum !== "bitti" &&
            hasta.durum !== "transfer") {
            return true;
        }

        const anahtar = String(hasta.hasta_no);

        let durumZamani;

        if (hasta.durum_tarihi) {
            durumZamani = new Date(
                hasta.durum_tarihi.replace(" ", "T")
            ).getTime();
        } else {
            durumZamani = ilkGorulmeZamanlari.get(anahtar);

            if (!durumZamani) {
                durumZamani = simdi;
                ilkGorulmeZamanlari.set(anahtar, durumZamani);
            }
        }

        if (!Number.isFinite(durumZamani)) {
            return true;
        }

        return simdi - durumZamani < gosterimSuresi;
    });


    // Önce iptal, sonra normal, en son yeşil hastalar
    gecerliHastalar.sort((a, b) => {

        const sira = {
            iptal: 0,
            hazirlaniyor: 1,
            basladi: 1,
            bitti: 2,
            transfer: 2
        };

        return (sira[a.durum] ?? 1) - (sira[b.durum] ?? 1);
    });


    return gecerliHastalar;
}



function hastalariEkranaYaz() {

    hastaListesi.innerHTML = "";

    const gecerliHastalar = gecerliHastalariGetir();

    if (gecerliHastalar.length === 0) {

        hastaListesi.innerHTML = `
            <div class="bilgi-mesaji">
                Şu anda görüntülenecek hasta bilgisi bulunmuyor.
            </div>
        `;

        return;
    }

    const toplamSayfa = Math.ceil(
        gecerliHastalar.length / sayfaHastaSayisi
    );

    if (mevcutSayfa >= toplamSayfa) {
        mevcutSayfa = 0;
    }

    const baslangic = mevcutSayfa * sayfaHastaSayisi;

    const gosterilecekHastalar = gecerliHastalar.slice(
        baslangic,
        baslangic + sayfaHastaSayisi
    );

    gosterilecekHastalar.forEach(hasta => {

        const durum = durumlar[hasta.durum];

        if (!durum) {
            return;
        }

        const kart = document.createElement("article");

        kart.className = `hasta-karti ${durum.sinif}`;

        const hastaBilgisi = document.createElement("div");
        hastaBilgisi.className = "hasta-bilgisi";

        const etiket = document.createElement("div");
        etiket.className = "hasta-etiketi";
        etiket.textContent = "";

        const ad = document.createElement("div");
        ad.className = "hasta-adi";
        ad.textContent = hasta.ad_soyad;

        const durumEtiketi = document.createElement("div");
        durumEtiketi.className = "durum-etiketi";
        durumEtiketi.textContent = durum.metin;

        hastaBilgisi.appendChild(etiket);
        hastaBilgisi.appendChild(ad);


        const saat = document.createElement("div");
        saat.className = "hasta-saat";

        if (hasta.durum_tarihi) {

            const durumZamani = new Date(
                hasta.durum_tarihi.replace(" ", "T")
            );

            saat.textContent = durumZamani.toLocaleTimeString("tr-TR", {
                hour: "2-digit",
                minute: "2-digit"
            });

        } else {
            saat.textContent = "--:--";
        }

        kart.appendChild(hastaBilgisi);
        kart.appendChild(durumEtiketi);
        kart.appendChild(saat);

        hastaListesi.appendChild(kart);

    });
}

async function hastalariGetir() {

    try {

        const cevap = await fetch("/api/hasta-durumlari", {
            cache: "no-store"
        });

        if (!cevap.ok) {
            throw new Error("Sunucu yanıt vermedi.");
        }

        const veri = await cevap.json();

        if (!veri.basarili) {
            throw new Error("Hasta bilgileri alınamadı.");
        }

        hastalar = veri.hastalar || [];
        document.getElementById("toplamHastaSayisi").textContent = hastalar.length;

        // Durumu değişen hastaların eski zaman kayıtlarını temizle
        const mevcutAnahtarlar = new Set(
            hastalar.map(hasta => String(hasta.hasta_no))
        );

        for (const anahtar of ilkGorulmeZamanlari.keys()) {
            if (!mevcutAnahtarlar.has(anahtar)) {
                ilkGorulmeZamanlari.delete(anahtar);
            }
        }

        hastalariEkranaYaz();

        baglantiDurumu.textContent = "● Bağlantı aktif";
        baglantiDurumu.style.color = "#18794e";

    } catch (hata) {

        console.error("TV ekranı hatası:", hata);

        baglantiDurumu.textContent = "Bağlantı kurulamadı";
        baglantiDurumu.style.color = "#c0392b";
    }
}

// İlk listeyi getir
hastalariGetir();

// Hasta bilgilerini 3 saniyede bir güncelle
setInterval(hastalariGetir, guncellemeSuresi);

// Her 10 saniyede bir sonraki sayfaya geç
setInterval(() => {

    const toplamSayfa = Math.ceil(
        gecerliHastalariGetir().length / sayfaHastaSayisi
    );

    if (toplamSayfa <= 1) {
        mevcutSayfa = 0;
        return;
    }

    mevcutSayfa++;

    if (mevcutSayfa >= toplamSayfa) {
        mevcutSayfa = 0;
    }

    hastalariEkranaYaz();

}, sayfaGecisSuresi);
