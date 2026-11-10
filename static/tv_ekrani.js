
const hastaListesi = document.getElementById("hastaListesi");
const baglantiDurumu = document.getElementById("baglantiDurumu");

const sayfaHastaSayisi = 5;
const sayfaGecisSuresi = 10000;

let hastalar = [];
let mevcutSayfa = 0;

const durumlar = {
    hazirlaniyor: {
        metin: "Hasta hazırlanıyor",
        sinif: "durum-hazirlaniyor"
    },
    basladi: {
        metin: "Diyaliz işlemi başladı",
        sinif: "durum-basladi"
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

function hastalariEkranaYaz() {

    hastaListesi.innerHTML = "";

    if (hastalar.length === 0) {
        hastaListesi.innerHTML = `
            <div class="bilgi-mesaji">
                Şu anda görüntülenecek hasta bilgisi bulunmuyor.
            </div>
        `;
        return;
    }

    const baslangic = mevcutSayfa * sayfaHastaSayisi;
    const gosterilecekHastalar = hastalar.slice(
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
        etiket.textContent = "HASTA";

        const ad = document.createElement("div");
        ad.className = "hasta-adi";
        ad.textContent = hasta.ad_soyad;

        const durumEtiketi = document.createElement("div");
        durumEtiketi.className = "durum-etiketi";
        durumEtiketi.textContent = durum.metin;

        hastaBilgisi.appendChild(etiket);
        hastaBilgisi.appendChild(ad);

        kart.appendChild(hastaBilgisi);
        kart.appendChild(durumEtiketi);

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

        const toplamSayfa = Math.ceil(
            hastalar.length / sayfaHastaSayisi
        );

        if (toplamSayfa === 0) {
            mevcutSayfa = 0;
        } else if (mevcutSayfa >= toplamSayfa) {
            mevcutSayfa = 0;
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

// İlk hasta listesini getir
hastalariGetir();

// Hasta bilgilerini 3 saniyede bir güncelle
setInterval(hastalariGetir, 3000);

// Her 10 saniyede bir sonraki sayfaya geç
setInterval(() => {

    const toplamSayfa = Math.ceil(
        hastalar.length / sayfaHastaSayisi
    );

    if (toplamSayfa <= 1) {
        return;
    }

    mevcutSayfa++;

    if (mevcutSayfa >= toplamSayfa) {
        mevcutSayfa = 0;
    }

    hastalariEkranaYaz();

}, sayfaGecisSuresi);
