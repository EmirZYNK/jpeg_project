const imageInput = document.getElementById('imageInput');
const ratioSlider = document.getElementById('ratioSlider');
const ratioValue = document.getElementById('ratioValue');
const compressBtn = document.getElementById('compressBtn');
const originalPreview = document.getElementById('originalPreview');
const algorithmSelect = document.getElementById('algorithmSelect');
const jpeg2000Params = document.getElementById('jpeg2000Params');
const targetHint = document.getElementById('targetHint');

// Algoritma değişince JPEG2000 ayarlarını göster/gizle
algorithmSelect.addEventListener('change', (e) => {
    jpeg2000Params.style.display = e.target.value === 'jpeg2000' ? 'block' : 'none';
});

// Slider her değiştiğinde tahmini hedef boyutu göster (Dinamik Hesaplama)
ratioSlider.addEventListener('input', (e) => {
    const factor = e.target.value;
    ratioValue.innerText = factor;
    
    if (imageInput.files[0]) {
        const originalSize = imageInput.files[0].size / 1024; // KB cinsinden
        const targetSize = (originalSize / factor).toFixed(2);
        targetHint.innerText = `Hedef Boyut: ~${targetSize} KB (${factor} kat küçültme)`;
    }
});

// Orijinal resmi anında önizle
imageInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        originalPreview.src = URL.createObjectURL(file);
        document.getElementById('resultsArea').style.display = 'flex';
        const sizeKB = (file.size / 1024).toFixed(2);
        document.getElementById('originalStats').innerText = `Boyut: ${sizeKB} KB`;
        
        // Resim seçildiği an hedef boyutu hesapla
        const factor = ratioSlider.value;
        const targetSize = (sizeKB / factor).toFixed(2);
        targetHint.innerText = `Hedef Boyut: ~${targetSize} KB (${factor} kat küçültme)`;
    }
});

compressBtn.addEventListener('click', async () => {
    const file = imageInput.files[0];
    if (!file) {
        alert("Lütfen bir resim seçin!");
        return;
    }

    const algorithm = algorithmSelect.value;
    const factor = ratioSlider.value; // Artık ratio yerine factor kullanıyoruz

    const formData = new FormData();
    formData.append('image', file);
    formData.append('algorithm', algorithm);
    formData.append('factor', factor); // Backend'e 'factor' olarak gidiyor
    
    // Diğer parametreler
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
            document.getElementById('compressedStats').innerText = `Yeni Boyut: ${data.compressed_size_kb} KB \n Veri Azaltma Oranı: ${data.compression_ratio}x`;
            
            // Metrikleri Yazdırma
            document.getElementById('mseVal').innerText = data.mse;
            document.getElementById('psnrVal').innerText = data.psnr;
            document.getElementById('ssimVal').innerText = data.ssim;

            // Grafiği Göster
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