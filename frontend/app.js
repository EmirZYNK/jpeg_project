const imageInput = document.getElementById('imageInput');
const ratioSlider = document.getElementById('ratioSlider');
const ratioValue = document.getElementById('ratioValue');
const compressBtn = document.getElementById('compressBtn');
const originalPreview = document.getElementById('originalPreview');
const algorithmSelect = document.getElementById('algorithmSelect');
const jpeg2000Params = document.getElementById('jpeg2000Params');

// Algoritma değişince JPEG2000 ayarlarını göster/gizle
algorithmSelect.addEventListener('change', (e) => {
    // Eğer jpeg2000 seçiliyse blok görünür, değilse gizli kalır
    jpeg2000Params.style.display = e.target.value === 'jpeg2000' ? 'block' : 'none';
});

// Slider değerini göster
ratioSlider.addEventListener('input', (e) => {
    ratioValue.innerText = e.target.value;
});

// Orijinal resmi anında önizle
imageInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        originalPreview.src = URL.createObjectURL(file);
        document.getElementById('resultsArea').style.display = 'flex';
        document.getElementById('originalStats').innerText = `Boyut: ${(file.size / 1024).toFixed(2)} KB`;
    }
});

compressBtn.addEventListener('click', async () => {
    const file = imageInput.files[0];
    if (!file) {
        alert("Lütfen bir resim seçin!");
        return;
    }

    const algorithm = algorithmSelect.value;
    const ratio = ratioSlider.value;

    const formData = new FormData();
    formData.append('image', file);
    formData.append('algorithm', algorithm);
    formData.append('ratio', ratio);
    
    // --- YENİ PARAMETRELERİ EKLE ---
    formData.append('category', document.getElementById('categorySelect').value);
    formData.append('wavelet', document.getElementById('waveletSelect').value);
    formData.append('level', document.getElementById('levelInput').value);

    compressBtn.innerText = "Sıkıştırılıyor...";
    compressBtn.disabled = true;

    try {
        const response = await fetch('/api/compress', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            // Resim ve Başlık Güncelleme
            document.getElementById('compressedPreview').src = data.compressed_url;
            document.getElementById('resultAlgo').innerText = data.algorithm.toUpperCase();
            
            // İstatistikleri Güncelleme
            document.getElementById('originalStats').innerText = `Boyut: ${data.original_size_kb} KB`;
            document.getElementById('compressedStats').innerText = `Yeni Boyut: ${data.compressed_size_kb} KB \n Sıkıştırma: %${data.compression_ratio}`;
            
            // Metrikleri (MSE/PSNR/SSIM) Yazdırma
            document.getElementById('mseVal').innerText = data.mse;
            document.getElementById('psnrVal').innerText = data.psnr;
            document.getElementById('ssimVal').innerText = data.ssim;

            // --- GRAFİĞİ GÖSTER (YENİ) ---
            if (data.plot_url) {
                const plotImg = document.getElementById('comparisonPlot');
                plotImg.src = data.plot_url;
                plotImg.style.display = 'block';
            }

        } else {
            alert("Hata: " + data.error);
        }
    } catch (error) {
        console.error("Hata:", error);
        alert("Bir bağlantı hatası oluştu.");
    } finally {
        compressBtn.innerText = "Sıkıştırmayı Başlat";
        compressBtn.disabled = false;
    }
});