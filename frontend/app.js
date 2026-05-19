// =====================================================================
// ARAYÜZ ELEMANLARI
// =====================================================================
const hiddenFileInput = document.getElementById('hiddenFileInput');
const sidebarUploadBtn = document.getElementById('sidebarUploadBtn');
const uploadPlaceholder = document.getElementById('uploadPlaceholder');
const sidebarFileName = document.getElementById('sidebarFileName');

const ratioSlider = document.getElementById('ratioSlider');
const ratioValue = document.getElementById('ratioValue');
const compressBtn = document.getElementById('compressBtn');
const algorithmSelect = document.getElementById('algorithmSelect');
const algoControlGroup = document.getElementById('algoControlGroup');
const jpeg2000Params = document.getElementById('jpeg2000Params');

const modeRadios = document.getElementsByName('appMode');
const viewRadios = document.getElementsByName('viewMode');

const compContainer = document.getElementById('compContainer');
const compareSlider = document.getElementById('compareSlider');
const sliderLine = document.getElementById('sliderLine');

const originalImage = document.getElementById('originalImage');
const compressedImage = document.getElementById('compressedImage');

const wrapperOriginal = document.getElementById('wrapperOriginal');
const wrapperCompressed = document.getElementById('wrapperCompressed');
const labelOriginal = document.getElementById('labelOriginal');
const labelCompressed = document.getElementById('labelCompressed');

// =====================================================================
// ÇALIŞMA MODU GEÇİŞ MANTIĞI
// =====================================================================
modeRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
        const mode = e.target.value;
        compContainer.setAttribute('data-mode', mode); 

        if (mode === 'comparison') {
            algoControlGroup.style.display = 'none';
            jpeg2000Params.style.display = 'flex'; 
            labelCompressed.innerText = 'JPEG (DCT)';
            labelOriginal.innerText = 'JPEG 2000 (DWT)';
        } else {
            algoControlGroup.style.display = 'flex';
            jpeg2000Params.style.display = algorithmSelect.value === 'jpeg2000' ? 'flex' : 'none';
            labelCompressed.innerText = 'İşlenmiş Resim';
            labelOriginal.innerText = 'Orijinal Resim';
        }
    });
});

algorithmSelect.addEventListener('change', (e) => {
    jpeg2000Params.style.display = e.target.value === 'jpeg2000' ? 'flex' : 'none';
});

ratioSlider.addEventListener('input', (e) => {
    const factor = e.target.value;
    ratioValue.innerText = factor;
    document.getElementById('targetHint').innerText = factor == 1 ? "Orijinal Kalite" : ``;
});

// =====================================================================
// GÖRÜNÜM MODU (SLIDER / YAN YANA) GEÇİŞ MANTIĞI
// =====================================================================
viewRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
        if (e.target.value === 'sidebyside') {
            compContainer.classList.add('side-by-side');
        } else {
            compContainer.classList.remove('side-by-side');
            
            // Slider hizanı geri yükle
            const percentage = compareSlider.value;
            wrapperCompressed.style.clipPath = `polygon(0 0, ${percentage}% 0, ${percentage}% 100%, 0 100%)`;
        }
    });
});

// =====================================================================
// DOSYA YÜKLEME VE ÖNİZLEME
// =====================================================================
sidebarUploadBtn.addEventListener('click', () => hiddenFileInput.click());
uploadPlaceholder.addEventListener('click', () => hiddenFileInput.click());

hiddenFileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        sidebarFileName.innerText = file.name.length > 20 ? file.name.substring(0, 20) + '...' : file.name;
        originalImage.src = URL.createObjectURL(file);
        
        uploadPlaceholder.style.display = 'none';
        compContainer.style.display = 'block';
        
        // ÖNEMLİ DÜZELTME: display: none yerine visibility: hidden kullanıyoruz. 
        // Böylece kutunun kendisi silinmiyor, Flexbox yapısı bozulmuyor, sadece görünmez oluyor.
        wrapperCompressed.style.visibility = 'hidden'; 
        
        compareSlider.style.display = 'none';
        sliderLine.style.display = 'none';
        
        document.getElementById('statsRowAnalysis').style.display = 'none';
        document.getElementById('statsRowComparison').style.display = 'none';
        document.getElementById('graphRow').style.display = 'none';
        
        const sizeKB = (file.size / 1024).toFixed(2);
        document.getElementById('origSize').innerText = sizeKB;
        document.getElementById('origSizeComp').innerText = sizeKB;
    }
});

// =====================================================================
// SLIDER (KARŞILAŞTIRMA ÇUBUĞU) KONTROLÜ
// =====================================================================
compareSlider.addEventListener('input', (e) => {
    const percentage = e.target.value;
    wrapperCompressed.style.clipPath = `polygon(0 0, ${percentage}% 0, ${percentage}% 100%, 0 100%)`;
    sliderLine.style.left = `${percentage}%`;
});

// =====================================================================
// SIKIŞTIRMA VE BACKEND İLETİŞİMİ
// =====================================================================
compressBtn.addEventListener('click', async () => {
    const file = hiddenFileInput.files[0];
    if (!file) { alert("Lütfen önce bir resim seçin!"); return; }

    const currentMode = document.querySelector('input[name="appMode"]:checked').value;
    compContainer.setAttribute('data-mode', currentMode); 
    
    const formData = new FormData();
    formData.append('image', file);
    formData.append('mode', currentMode);
    formData.append('algorithm', algorithmSelect.value);
    formData.append('factor', ratioSlider.value);
    formData.append('category', document.getElementById('categorySelect').value);
    formData.append('wavelet', document.getElementById('waveletSelect').value);
    formData.append('level', document.getElementById('levelInput').value);

    compressBtn.innerText = "İşleniyor...";
    compressBtn.disabled = true;

    try {
        const response = await fetch('/api/compress', { method: 'POST', body: formData });
        const data = await response.json();

        if (response.ok) {
            // ÖNEMLİ DÜZELTME: İşlem bitti, kutuyu görünür yap (display flex ayarını ezmez)
            wrapperCompressed.style.visibility = 'visible'; 
            
            compareSlider.style.display = 'block';
            sliderLine.style.display = 'block';
            
            // Slider konumunu sıfırla
            compareSlider.value = 50;
            wrapperCompressed.style.clipPath = `polygon(0 0, 50% 0, 50% 100%, 0 100%)`;
            sliderLine.style.left = '50%';

            if (data.mode === 'comparison') {
                compressedImage.src = data.jpeg_url; 
                originalImage.src = data.j2k_url;    
                
                document.getElementById('statsRowAnalysis').style.display = 'none';
                document.getElementById('statsRowComparison').style.display = 'grid';

                document.getElementById('jSize').innerText = data.jpeg_stats.size;
                document.getElementById('jBpp').innerText = data.jpeg_stats.bpp;
                document.getElementById('jPsnr').innerText = data.jpeg_stats.psnr;
                document.getElementById('jSsim').innerText = data.jpeg_stats.ssim;
                document.getElementById('jMse').innerText = data.jpeg_stats.mse;

                document.getElementById('kSize').innerText = data.j2k_stats.size;
                document.getElementById('kBpp').innerText = data.j2k_stats.bpp;
                document.getElementById('kPsnr').innerText = data.j2k_stats.psnr;
                document.getElementById('kSsim').innerText = data.j2k_stats.ssim;
                document.getElementById('kMse').innerText = data.j2k_stats.mse;

            } else {
                compressedImage.src = data.compressed_url;
                originalImage.src = URL.createObjectURL(file);
                
                document.getElementById('statsRowComparison').style.display = 'none';
                document.getElementById('statsRowAnalysis').style.display = 'grid';

                document.getElementById('resultAlgo').innerText = data.algorithm.toUpperCase();
                document.getElementById('compSize').innerText = data.compressed_size_kb;
                document.getElementById('compRatio').innerText = data.compression_ratio;
                document.getElementById('compBpp').innerText = data.bpp;
                document.getElementById('psnrVal').innerText = data.psnr;
                document.getElementById('ssimVal').innerText = data.ssim;
                document.getElementById('mseVal').innerText = data.mse;
            }

            if (data.plot_url) {
                document.getElementById('comparisonPlot').src = data.plot_url;
                document.getElementById('graphRow').style.display = 'block';
                setTimeout(() => {
                    const targetRow = data.mode === 'comparison' ? 'statsRowComparison' : 'statsRowAnalysis';
                    document.getElementById(targetRow).scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 400);
            }

        } else {
            alert("Sunucu Hatası: " + data.error);
        }
    } catch (error) {
        console.error(error);
        alert("Bağlantı hatası!");
    } finally {
        compressBtn.innerText = "Sıkıştırmayı Başlat";
        compressBtn.disabled = false;
    }
});