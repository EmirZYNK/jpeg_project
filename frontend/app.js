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

const categorySelect = document.getElementById('categorySelect');
const biomedicalModeGroup = document.getElementById('biomedicalModeGroup');
const lossyRadios = document.getElementsByName('lossyMode');

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
// DİNAMİK LİMİT KONTROLLERİ (Biyomedikal, Parmak İzi ve Genel Limitler)
// =====================================================================
function checkSliderLimits() {
    const category = categorySelect.value;
    if (category === 'biomedical' || category === 'fingerprint') {
        // Otomatik modda yuvarlamayı önlemek için adımı geçici olarak ondalıklı yapıyoruz
        ratioSlider.step = "0.01"; 
        if (window.maxLosslessRatio) {
            ratioSlider.max = window.maxLosslessRatio;
            ratioSlider.value = window.maxLosslessRatio;
        } else {
            ratioSlider.max = 1;
            ratioSlider.value = 1;
        }
    } else {
        // Manuel kontrol edilen tüm modlarda adım kesinlikle tam sayı (1) olarak kalır!
        ratioSlider.step = "1"; 
        ratioSlider.max = 50; 
    }
    ratioValue.innerText = ratioSlider.value;
    document.getElementById('targetHint').innerText = ratioSlider.value == 1 ? "Orijinal Kalite" : ``;
}

// KAYIPSIZ MOD ARABİRİM KONTROLÜ (Sürgü kilidi açıldığında adımı tam sayıya geri döndürür)
function updateUIForLossless() {
    const category = categorySelect.value;
    const isLossless = (category === 'biomedical' || category === 'fingerprint');
    
    if (isLossless && window.maxLosslessRatio) {
        ratioSlider.step = "0.01"; // Otomatik kilitleme için ondalık izni
        compressBtn.innerText = `Kayıpsız Sıkıştır (Maksimum: ${window.maxLosslessRatio}x)`;
        ratioSlider.max = window.maxLosslessRatio;
        ratioSlider.value = window.maxLosslessRatio;
        ratioValue.innerText = window.maxLosslessRatio;
        ratioSlider.disabled = true; // Sürgü kilitli olduğu için kullanıcı manuel kaydıramaz
        document.getElementById('targetHint').innerText = "Kayıpsız Sıkıştırma Oranı (Kilitli)";
    } else {
        compressBtn.innerText = "Sıkıştırmayı Başlat";
        ratioSlider.step = "1"; // Sürgü açıldığı an manuel kaydırma için tam sayı (1) moduna döner
        ratioSlider.disabled = false;
    }
}

// SEÇİM KUTUSU EVENT LISTENER'LARININ GÜNCELLENMESİ
categorySelect.addEventListener('change', (e) => {
    biomedicalModeGroup.style.display = 'none'; // Kayıplı/Kayıpsız seçim kutusunu her zaman gizliyoruz
    checkSliderLimits();
    updateUIForLossless();
});

// Not: lossyRadios için tanımlanan eski event listener döngüsü temizlenmiştir.

ratioSlider.addEventListener('input', (e) => {
    ratioValue.innerText = e.target.value;
    document.getElementById('targetHint').innerText = e.target.value == 1 ? "Orijinal Kalite" : ``;
});

// =====================================================================
// ÇALIŞMA & GÖRÜNÜM MODU GEÇİŞ MANTIĞI
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
        updateROIOverlay();
    });
});

algorithmSelect.addEventListener('change', (e) => {
    jpeg2000Params.style.display = e.target.value === 'jpeg2000' ? 'flex' : 'none';
});

viewRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
        if (e.target.value === 'sidebyside') {
            compContainer.classList.add('side-by-side');
        } else {
            compContainer.classList.remove('side-by-side');
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
        const objectURL = URL.createObjectURL(file);
        originalImage.src = objectURL;

        uploadPlaceholder.style.display = 'none';
        compContainer.style.display = 'block';
        wrapperCompressed.style.visibility = 'hidden'; 
        
        compareSlider.style.display = 'none';
        sliderLine.style.display = 'none';
        
        document.getElementById('statsRowAnalysis').style.display = 'none';
        document.getElementById('statsRowComparison').style.display = 'none';
        document.getElementById('graphRow').style.display = 'none';
        document.getElementById('subbandRow').style.display = 'none';
        document.getElementById('errorMapRow').style.display = 'none';
        
        const tempImg = new Image();
        tempImg.src = objectURL;
        tempImg.onload = async function() {
            const w = Math.floor(tempImg.width / 16) * 16;
            const h = Math.floor(tempImg.height / 16) * 16;
            
            // Kanvas yardımıyla resmin grayscale (siyah-beyaz) olup olmadığını mikro saniyeler içinde anlıyoruz
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = Math.min(tempImg.width, 300); // 300px genişliğinde küçük bir örnek taramak yeterlidir
            canvas.height = Math.min(tempImg.height, 300);
            ctx.drawImage(tempImg, 0, 0, canvas.width, canvas.height);
            const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
            
            let isGrayscale = true;
            for (let i = 0; i < imgData.length; i += 16) { // her 4 pikselden birini kontrol et (aşırı hızlı çalışır)
                if (imgData[i] !== imgData[i+1] || imgData[i+1] !== imgData[i+2]) {
                    isGrayscale = false;
                    break;
                }
            }
            
            const bytesPerPixel = isGrayscale ? 1 : 3;
            const rawBytes = w * h * bytesPerPixel;
            const rawKB = (rawBytes / 1024).toFixed(2);
            
            document.getElementById('origSize').innerText = rawKB;
            document.getElementById('origSizeComp').innerText = rawKB;
            
            // İlk yükleme ekranındaki Bitrate etiketini siyah-beyazlığa göre ayarlariz (8.00 veya 24.00)
            const bppEl = document.getElementById('origBpp');
            if (bppEl) {
                bppEl.innerText = (bytesPerPixel * 8).toFixed(2);
            }

            // GÖRSEL YÜKLENDİKTEN SONRA KAYIPSIZ MAKSİMUM ORANI HESAPLIYORUZ
            const formData = new FormData();
            formData.append('image', file);
            try {
                const response = await fetch('/api/calculate-lossless-max', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                if (response.ok) {
                    window.maxLosslessRatio = data.max_lossless_ratio;
                    console.log("Maksimum Kayıpsız Oran Saptandı:", window.maxLosslessRatio);
                    checkSliderLimits();
                    updateUIForLossless();
                }
            } catch (err) {
                console.error("Kayıpsız oran sorgulama hatası:", err);
            }
        };
    }
});

compareSlider.addEventListener('input', (e) => {
    const percentage = e.target.value;
    wrapperCompressed.style.clipPath = `polygon(0 0, ${percentage}% 0, ${percentage}% 100%, 0 100%)`;
    sliderLine.style.left = `${percentage}%`;
});

// =====================================================================
// DROPDOWN OKLARI & DİNAMİK FORMÜLLER
// =====================================================================
document.querySelectorAll('.info-toggle').forEach(toggle => {
    toggle.addEventListener('click', (e) => {
        const span = e.target;
        span.classList.toggle('open');
        const detailDiv = span.nextElementSibling;
        detailDiv.classList.toggle('show');
    });
});

function fillFormulas(prefix, stats, origBytes, totalPixels, originalBpp) {
    // prefix = 'comp', 'j', 'k'

    // Boyut Formülü
    if (document.getElementById(`detail-${prefix}Size`)) {
        const kb = (stats.bytes / 1024).toFixed(2);
        document.getElementById(`detail-${prefix}Size`).innerHTML = `
            <strong>Formül:</strong> Sıkıştırılmış Ham Boyut = (Toplam Piksel * ${originalBpp === 8 ? 1 : 3}) / Sıkıştırma Çarpanı<br>
            <strong>Bu Resim:</strong> ${stats.bytes} / 1024 = <b style="color:#feb47b">${kb} KB</b>
        `;
    }
    // BPP Formülü
    if (document.getElementById(`detail-${prefix}Bpp`)) {
        document.getElementById(`detail-${prefix}Bpp`).innerHTML = `
            <strong>Formül:</strong> (Sıkıştırılmış Boyut (Bayt) * 8) / Toplam Piksel = ${originalBpp} / Sıkıştırma Çarpanı<br>
            <strong>Bu Resim:</strong> (${stats.bytes} * 8) / ${totalPixels} = <b style="color:#feb47b">${stats.bpp} Bits/Pixel</b>
        `;
    }
    // Oran Formülü
    if (document.getElementById(`detail-${prefix}Ratio`)) {
        document.getElementById(`detail-${prefix}Ratio`).innerHTML = `
            <strong>Formül:</strong> Orijinal Ham Boyut / Sıkıştırılmış Ham Boyut<br>
            <strong>Bu Resim:</strong> ${origBytes} / ${stats.bytes} = <b style="color:#feb47b">${stats.ratio}x</b>
        `;
    }
    // PSNR Formülü
    if (document.getElementById(`detail-${prefix}Psnr`) || document.getElementById(`detail-psnrVal`)) {
        const tId = prefix === 'comp' ? 'detail-psnrVal' : `detail-${prefix}Psnr`;
        document.getElementById(tId).innerHTML = `
            <strong>Formül:</strong> 10 * log10( (255^2) / MSE )<br>
            <strong>Bu Resim:</strong> 10 * log10( 65025 / ${stats.mse} ) = <b style="color:#feb47b">${stats.psnr} dB</b>
        `;
    }
    // SSIM Formülü
    if (document.getElementById(`detail-${prefix}Ssim`) || document.getElementById(`detail-ssimVal`)) {
        const tId = prefix === 'comp' ? 'detail-ssimVal' : `detail-${prefix}Ssim`;
        document.getElementById(tId).innerHTML = `
            <strong>Formül:</strong> Yapısal Benzerlik İndeksi (Parlaklık, Kontrast ve Yapı çarpımı)<br>
            <strong>Bu Resim:</strong> Piksel bloklarının yapısal matris analiz sonucu = <b style="color:#feb47b">${stats.ssim}</b>
        `;
    }
    // MSE Formülü
    if (document.getElementById(`detail-${prefix}Mse`) || document.getElementById(`detail-mseVal`)) {
        const tId = prefix === 'comp' ? 'detail-mseVal' : `detail-${prefix}Mse`;
        document.getElementById(tId).innerHTML = `
            <strong>Formül:</strong> 1/N * Σ(Orijinal_Piksel - Sıkıştırılmış_Piksel)²<br>
            <strong>Bu Resim:</strong> Tüm pikseller arası hataların kareler ortalaması = <b style="color:#feb47b">${stats.mse}</b>
        `;
    }
}

// Hata Haritası Göster/Gizle Butonu
document.getElementById('toggleErrorMapBtn').addEventListener('click', () => {
    const container = document.getElementById('errorMapContainer');
    if(container.style.display === 'none') {
        container.style.display = 'block';
    } else {
        container.style.display = 'none';
    }
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
    formData.append('category', categorySelect.value);
    formData.append('wavelet', document.getElementById('waveletSelect').value);
    formData.append('level', document.getElementById('levelInput').value);
    
    // YENİ PARAMETRELERİN BACKEND'E GÖNDERİLMESİ
    formData.append('decodeLayers', decodeLayersSelect.value);
    formData.append('roiEnabled', roiCheckbox.checked);
    formData.append('roiX', roiXSlider.value);
    formData.append('roiY', roiYSlider.value);
    formData.append('roiR', roiRSlider.value);
    
    // Tıbbi veya parmak izi kategorilerinde kayıpsız modun (lossyMode = false) otomatik iletilmesini sağlıyoruz:
    const category = categorySelect.value;
    if (category === 'biomedical' || category === 'fingerprint') {
        formData.append('lossyMode', 'false');
    } else {
        const lossyMode = document.querySelector('input[name="lossyMode"]:checked');
        if(lossyMode) formData.append('lossyMode', lossyMode.value);
    }

    compressBtn.innerText = "İşleniyor...";
    compressBtn.disabled = true;

    try {
        const response = await fetch('/api/compress', { method: 'POST', body: formData });
        const data = await response.json();

        if (response.ok) {
            wrapperCompressed.style.visibility = 'visible'; 
            compareSlider.style.display = 'block';
            sliderLine.style.display = 'block';
            
            compareSlider.value = 50;
            wrapperCompressed.style.clipPath = `polygon(0 0, 50% 0, 50% 100%, 0 100%)`;
            sliderLine.style.left = '50%';

            // DÜZELTME: Orijinal boyut alanlarını backend'den gelen gerçek ham değere eşitliyoruz
            document.getElementById('origSize').innerText = data.original_size_kb;
            document.getElementById('origSizeComp').innerText = data.original_size_kb;
            document.getElementById('origBpp').innerText = data.original_bpp.toFixed(2);

            // Orijinal İstatistiklerin Formülü ve Etiketleri
            if(document.getElementById('detail-origSize')) {
                document.getElementById('detail-origSize').innerHTML = `
                    <strong>Dosya:</strong> Yüklenen Orijinal Boyut (Ham Sıkıştırılmamış)<br>
                    <strong>Değer:</strong> ${data.original_size_bytes} Bayt
                `;
            }
            if(document.getElementById('detail-origBpp')) {
                document.getElementById('detail-origBpp').innerHTML = data.original_bpp === 8 ? 
                    `<strong>Standart:</strong> Sıkıştırılmamış Grayscale Görüntü (1 kanal * 8 bit) = 8 BPP` :
                    `<strong>Standart:</strong> Sıkıştırılmamış RGB Görüntü (8 bit R + 8 bit G + 8 bit B) = 24 BPP`;
            }
            if(document.getElementById('detail-origSizeComp')) {
                document.getElementById('detail-origSizeComp').innerHTML = `<strong>Orijinal Dosya:</strong> ${data.original_size_bytes} Bayt`;
            }

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

                // fillFormulas fonksiyonuna dinamik bpp parametresini ekliyoruz
                fillFormulas('j', data.jpeg_stats, data.original_size_bytes, data.total_pixels, data.original_bpp);
                fillFormulas('k', data.j2k_stats, data.original_size_bytes, data.total_pixels, data.original_bpp);

                document.getElementById('errorMapRow').style.display = 'block';
                document.getElementById('errorMapSingleBox').style.display = 'none';
                document.getElementById('errorMapCompareBox').style.display = 'flex';
                document.getElementById('errorMapJ').src = data.error_map_j_url;
                document.getElementById('errorMapK').src = data.error_map_k_url;

                if (data.subband_url) {
                    document.getElementById('subbandRow').style.display = 'block';
                    document.getElementById('subbandPlot').src = data.subband_url;
                } else {
                    document.getElementById('subbandRow').style.display = 'none';
                }

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

                const singleStats = {
                    bytes: data.compressed_size_bytes,
                    bpp: data.bpp, ratio: data.compression_ratio,
                    mse: data.mse, psnr: data.psnr, ssim: data.ssim
                };
                fillFormulas('comp', singleStats, data.original_size_bytes, data.total_pixels, data.original_bpp);

                document.getElementById('errorMapRow').style.display = 'block';
                document.getElementById('errorMapCompareBox').style.display = 'none';
                document.getElementById('errorMapSingleBox').style.display = 'block';
                document.getElementById('errorMapPlot').src = data.error_map_url;

                if (data.subband_url) {
                    document.getElementById('subbandRow').style.display = 'block';
                    document.getElementById('subbandPlot').src = data.subband_url;
                } else {
                    document.getElementById('subbandRow').style.display = 'none';
                }
            }

            if (data.plot_url) {
                document.getElementById('comparisonPlot').src = data.plot_url;
                document.getElementById('graphRow').style.display = 'block';
                setTimeout(() => {
                    document.getElementById('compContainer').scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 400);
            }

        } else {
            alert("Sunucu Hatası: " + data.error);
        }
    } catch (error) {
        console.error(error);
        alert("Bağlantı hatası!");
    } finally {
        compressBtn.disabled = false;
        updateUIForLossless(); // İşlem bittiğinde buton yazısının kayıpsız mod durumuna göre kalmasını sağlar
    }
});

// =====================================================================
// GERÇEK ZAMANLI ROI VİZÖR GÖRSELLEŞTİRME VE KATMAN MOTORU
// =====================================================================
const decodeLayersSelect = document.getElementById('decodeLayersSelect');
const roiCheckbox = document.getElementById('roiCheckbox');
const roiControls = document.getElementById('roiControls');
const roiXSlider = document.getElementById('roiXSlider');
const roiYSlider = document.getElementById('roiYSlider');
const roiRSlider = document.getElementById('roiRSlider');
const roiXVal = document.getElementById('roiXVal');
const roiYVal = document.getElementById('roiYVal');
const roiRVal = document.getElementById('roiRVal');
const levelInput = document.getElementById('levelInput');

// Slayt 93'teki çözünürlük oranlarını dinamik hesaplayan fonksiyon
function updateDecodeLayersOptions() {
    if (!levelInput || !decodeLayersSelect) return;
    const level = parseInt(levelInput.value) || 1;
    
    decodeLayersSelect.innerHTML = '<option value="0">Tümü (Tam Çözünürlük - %100)</option>';
    for (let i = 1; i <= level; i++) {
        const percent = Math.round(100 / Math.pow(2, level - i));
        decodeLayersSelect.innerHTML += `<option value="${i}">Layer ${i} (Sadece İlk %${percent} Çözünürlük)</option>`;
    }
}

// Seviye girdisi değiştikçe katman seçeneklerini de güncel tutuyoruz
levelInput.addEventListener('input', updateDecodeLayersOptions);
document.addEventListener('DOMContentLoaded', updateDecodeLayersOptions);

// Sayfa ilk yüklendiğinde seçeneklerin anında hesaplanması için çağrı
updateDecodeLayersOptions();

// REAL-TIME VİZÖR GÜNCELLEME FONKSİYONU
function updateROIOverlay() {
    let overlay = document.getElementById('roiVisualOverlay');
    
    // Eğer görsel daire DOM'da yoksa dinamik olarak oluşturup stillendiriyoruz
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'roiVisualOverlay';
        
        // compContainer'ın pozisyonlama bağlamını (relative) garantiye alıyoruz
        compContainer.style.position = 'relative';
        
        overlay.style.position = 'absolute';
        overlay.style.border = '2.5px dashed #ff7e5f'; // Turuncu kesikli çizgiler
        overlay.style.background = 'rgba(255, 126, 95, 0.15)'; // Hafif turuncu şeffaf dolgu
        overlay.style.boxShadow = '0 0 15px rgba(255, 126, 95, 0.6)'; // Parlama efekti
        overlay.style.borderRadius = '50%';
        overlay.style.pointerEvents = 'none'; // Resim karşılaştırma sürgüsünün engellenmesini önler
        overlay.style.transform = 'translate(-50%, -50%)'; // Merkezi (X,Y) noktasına hizalar
        overlay.style.zIndex = '999'; // En üstte görünmesini sağlar
        overlay.style.display = 'none';
        compContainer.appendChild(overlay);
    }

    // ROI aktifse ve resim alanı görünür durumdaysa vizörü göster ve güncelle
    if (roiCheckbox && roiCheckbox.checked && compContainer.style.display !== 'none') {
        overlay.style.display = 'block';
        
        // Konumlandırma (Yüzdesel)
        const x = roiXSlider.value;
        const y = roiYSlider.value;
        overlay.style.left = `${x}%`;
        overlay.style.top = `${y}%`;

        // Boyutlandırma (Python backend'indeki "max(h, w)" ölçeklemesine birebir uyumlu piksel hesabı)
        const r = parseFloat(roiRSlider.value);
        const rect = compContainer.getBoundingClientRect();
        const maxDim = Math.max(rect.width, rect.height);
        const diameter = (r * 2 / 100) * maxDim;
        
        overlay.style.width = `${diameter}px`;
        overlay.style.height = `${diameter}px`;
    } else {
        overlay.style.display = 'none';
    }
}

// Pencere boyutu değiştiğinde vizörün konumunu ve boyutunu otomatik yeniden hesaplatıyoruz
window.addEventListener('resize', updateROIOverlay);

// Tüm sürgülere ve kutucuklara anlık vizör dinleyicisi bağlıyoruz
roiCheckbox.addEventListener('change', (e) => {
    roiControls.style.display = e.target.checked ? 'flex' : 'none';
    updateROIOverlay();
});

roiXSlider.addEventListener('input', (e) => {
    roiXVal.innerText = e.target.value;
    updateROIOverlay();
});

roiYSlider.addEventListener('input', (e) => {
    roiYVal.innerText = e.target.value;
    updateROIOverlay();
});

// Sürükleme anında daha yumuşak çalışması için 'input' olayını dinliyoruz
roiRSlider.addEventListener('input', (e) => {
    roiRVal.innerText = e.target.value;
    updateROIOverlay();
});