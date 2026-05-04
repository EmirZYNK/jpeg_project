// Arayüz Elemanları
const hiddenFileInput = document.getElementById('hiddenFileInput');
const sidebarUploadBtn = document.getElementById('sidebarUploadBtn');
const uploadPlaceholder = document.getElementById('uploadPlaceholder');
const sidebarFileName = document.getElementById('sidebarFileName');

const ratioSlider = document.getElementById('ratioSlider');
const ratioValue = document.getElementById('ratioValue');
const compressBtn = document.getElementById('compressBtn');
const algorithmSelect = document.getElementById('algorithmSelect');
const jpeg2000Params = document.getElementById('jpeg2000Params');

// Resim ve Slider Elemanları
const compContainer = document.getElementById('compContainer');
const compareSlider = document.getElementById('compareSlider');
const originalImage = document.getElementById('originalImage');
const compressedImage = document.getElementById('compressedImage');
const sliderLine = document.getElementById('sliderLine');

// UI Etkileşimleri: Tıklamaları Gizli Input'a Yönlendir
sidebarUploadBtn.addEventListener('click', () => hiddenFileInput.click());
uploadPlaceholder.addEventListener('click', () => hiddenFileInput.click());

// Jpeg2000 menüsü aç/kapat
algorithmSelect.addEventListener('change', (e) => {
    jpeg2000Params.style.display = e.target.value === 'jpeg2000' ? 'flex' : 'none';
});

// Kaydırma Çubuğu Bilgi Güncelleme
ratioSlider.addEventListener('input', (e) => {
    const factor = e.target.value;
    ratioValue.innerText = factor;
    document.getElementById('targetHint').innerText = factor == 1 ? "Orijinal Kalite" : `~${(24/factor).toFixed(2)} BPP'ye Düşürülecek`;
});

// Dosya Seçildiğinde Çalışacak Kod
hiddenFileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        // İsim ve Önizleme Ayarları
        sidebarFileName.innerText = file.name.length > 20 ? file.name.substring(0, 20) + '...' : file.name;
        originalImage.src = URL.createObjectURL(file);
        
        // Arayüzü Değiştir
        uploadPlaceholder.style.display = 'none'; // Tıklama kutusunu gizle
        compContainer.style.display = 'block'; // Resmi göster
        
        // Başlangıçta sadece Orijinal resmi tam ekran göster
        compressedImage.style.display = 'none'; 
        compareSlider.style.display = 'none';
        sliderLine.style.display = 'none';
        
        // Diğer istatistik panellerini gizle (sıkıştırma yapılana kadar)
        document.getElementById('statsRow').style.display = 'none';
        document.getElementById('graphRow').style.display = 'none';
        
        // Orijinal Boyut Bilgisi
        document.getElementById('origSize').innerText = (file.size / 1024).toFixed(2);
    }
});

// Resim Üzerindeki Görsel Slider'ı Haraket Ettirme
compareSlider.addEventListener('input', (e) => {
    const percentage = e.target.value;
    compressedImage.style.clipPath = `polygon(0 0, ${percentage}% 0, ${percentage}% 100%, 0 100%)`;
    sliderLine.style.left = `${percentage}%`;
});


// Sıkıştırma İşlemi
compressBtn.addEventListener('click', async () => {
    const file = hiddenFileInput.files[0];
    if (!file) {
        alert("Lütfen önce bir resim seçin!");
        return;
    }

    const formData = new FormData();
    formData.append('image', file);
    formData.append('algorithm', algorithmSelect.value);
    formData.append('factor', ratioSlider.value);
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
            // Sıkıştırılmış Resmi Yükle
            compressedImage.src = data.compressed_url;
            compressedImage.style.display = 'block';
            
            // Slider çizgilerini görünür yap ve ortaya (50%) çek
            compareSlider.style.display = 'block';
            sliderLine.style.display = 'block';
            compareSlider.value = 50;
            compressedImage.style.clipPath = `polygon(0 0, 50% 0, 50% 100%, 0 100%)`;
            sliderLine.style.left = '50%';

            // İstatistikleri Göster ve Doldur
            document.getElementById('statsRow').style.display = 'grid';
            document.getElementById('resultAlgo').innerText = data.algorithm.toUpperCase();
            document.getElementById('compSize').innerText = data.compressed_size_kb;
            document.getElementById('compRatio').innerText = data.compression_ratio;
            document.getElementById('compBpp').innerText = data.bpp;
            document.getElementById('psnrVal').innerText = data.psnr;
            document.getElementById('ssimVal').innerText = data.ssim;
            document.getElementById('mseVal').innerText = data.mse;

            // Grafiği Yükle ve Göster
            if (data.plot_url) {
                document.getElementById('comparisonPlot').src = data.plot_url;
                document.getElementById('graphRow').style.display = 'block';
                
                // İşlem bitince yavaşça istatistiklere kaydır
                setTimeout(() => {
                    document.getElementById('statsRow').scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 300);
            }

        } else {
            alert("Hata: " + data.error);
        }
    } catch (error) {
        console.error("Hata:", error);
        alert("Bağlantı hatası!");
    } finally {
        compressBtn.innerText = "Sıkıştırmayı Başlat";
        compressBtn.disabled = false;
    }
});