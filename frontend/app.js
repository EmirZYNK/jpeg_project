const BACKEND_URL = "http://127.0.0.1:5000";

// --- SOL PANEL SEÇİMLERİ ---
const modeInputs          = document.querySelectorAll('input[name="mode"]');
const methodInputs        = document.querySelectorAll('input[name="method"]');
const methodSection       = document.getElementById("methodSection");
const actionButton        = document.getElementById("actionButton");

const qualityRange        = document.getElementById("qualityRange");
const dwtLevelRange       = document.getElementById("dwtLevelRange");
const qualityValue        = document.getElementById("qualityValue");
const dwtValue            = document.getElementById("dwtValue");

const imageInput          = document.getElementById("imageInput");
const selectedFile        = document.getElementById("selectedFile");
const imageInfo           = document.getElementById("imageInfo");
const imageInfoText       = document.getElementById("imageInfoText");

const imageTypeSelect     = document.getElementById("imageType");
const biomedicalWarning   = document.getElementById("biomedicalWarning");
const compressionLossy    = document.getElementById("compressionLossy");
const compressionLossless = document.getElementById("compressionLossless");
const waveletButtons      = document.querySelectorAll(".wavelet-btn");

// --- ANALYSIS MODE ELEMENTLERİ ---
const analysisView        = document.getElementById("analysisView");
const analysisTitle       = document.getElementById("analysisTitle");
const analysisNote        = document.getElementById("analysisNote");
const reconstructedTitle  = document.getElementById("reconstructedTitle");

const originalPreview     = document.getElementById("originalPreview");
const originalText        = document.getElementById("originalText");
const originalImageMeta   = document.getElementById("originalImageMeta");

const reconPreview        = document.getElementById("reconPreview");
const reconText           = document.getElementById("reconText");

// --- COMPARISON MODE ELEMENTLERİ ---
const comparisonView            = document.getElementById("comparisonView");
const originalPreviewComparison = document.getElementById("originalPreviewComparison");
const originalTextComparison    = document.getElementById("originalTextComparison");
const comparisonImageMeta       = document.getElementById("comparisonImageMeta");

const compJpegPreview           = document.getElementById("compJpegPreview");
const compJpegText              = document.getElementById("compJpegText");
const compJpeg2000Preview       = document.getElementById("compJpeg2000Preview");
const compJpeg2000Text          = document.getElementById("compJpeg2000Text");


// --- YARDIMCI FONKSİYONLAR ---
function getSelectedMode() {
  return document.querySelector('input[name="mode"]:checked').value;
}

function getSelectedMethod() {
  return document.querySelector('input[name="method"]:checked').value;
}

function detectColorMode(img) {
  const canvas = document.createElement("canvas");
  canvas.width  = Math.min(img.naturalWidth, 64);
  canvas.height = Math.min(img.naturalHeight, 64);

  const ctx = canvas.getContext("2d");
  ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

  const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
  let isGray = true;

  for (let i = 0; i < data.length; i += 4) {
    if (data[i] !== data[i + 1] || data[i] !== data[i + 2]) {
      isGray = false;
      break;
    }
  }

  return isGray ? "Grayscale" : "RGB";
}

function updateModeUI() {
  const mode = getSelectedMode();

  if (mode === "analysis") {
    analysisView.classList.add("active");
    comparisonView.classList.remove("active");
    methodSection.style.display = "block";
    actionButton.textContent = "Compress Image";
    updateMethodUI();
  } else {
    analysisView.classList.remove("active");
    comparisonView.classList.add("active");
    methodSection.style.display = "none";
    actionButton.textContent = "Compare Methods";
  }
}

function updateMethodUI() {
  const method = getSelectedMethod();
  const label  = method === "jpeg" ? "JPEG" : "JPEG2000";

  analysisTitle.textContent      = `Analysis Mode Active (Single Method: ${label})`;
  reconstructedTitle.textContent = `Reconstructed Image (${label})`;
  analysisNote.textContent       = `Note: Only the selected compression method (${label}) is applied.`;
}

function handleImageTypeChange() {
  const isBiomedical = imageTypeSelect.value === "biomedical";

  if (isBiomedical) {
    compressionLossless.checked = true;
    compressionLossy.checked = false;
    compressionLossy.disabled = true;
    compressionLossy.closest("label").classList.add("locked");
    biomedicalWarning.style.display = "block";
  } else {
    compressionLossy.disabled = false;
    compressionLossy.closest("label").classList.remove("locked");
    biomedicalWarning.style.display = "none";
  }
}

function updateSliders() {
  qualityValue.textContent = qualityRange.value;
  dwtValue.textContent = dwtLevelRange.value;
}

function updateAnalysisMetrics(data, file) {
  document.getElementById("m-psnr").textContent = data.psnr ?? "—";
  document.getElementById("m-mse").textContent = data.mse ?? "—";
  document.getElementById("m-ratio").textContent = data.compression_ratio ?? "—";
  document.getElementById("m-orig-size").textContent = file ? `${(file.size / 1024).toFixed(2)} KB` : "—";
  document.getElementById("m-comp-size").textContent = data.compressed_size ? `${data.compressed_size} KB` : "—";
  document.getElementById("m-time").textContent = data.encoding_time ? `${data.encoding_time} s` : "—";
}


// --- RESİM YÜKLEME VE ÖNİZLEME ---
imageInput.addEventListener("change", () => {
  const file = imageInput.files[0];

  // Analysis Mode Sıfırlama
  originalPreview.src = "";
  originalPreview.style.display = "none";
  originalText.style.display = "block";
  
  reconPreview.src = "";
  reconPreview.style.display = "none";
  reconText.style.display = "block";
  if (originalImageMeta) originalImageMeta.textContent = "";

  // Comparison Mode Sıfırlama
  if (originalPreviewComparison) {
    originalPreviewComparison.src = "";
    originalPreviewComparison.style.display = "none";
  }
  if (originalTextComparison) originalTextComparison.style.display = "block";
  if (comparisonImageMeta) comparisonImageMeta.textContent = "";

  if (compJpegPreview) {
    compJpegPreview.src = "";
    compJpegPreview.style.display = "none";
    compJpegText.style.display = "block";
  }
  if (compJpeg2000Preview) {
    compJpeg2000Preview.src = "";
    compJpeg2000Preview.style.display = "none";
    compJpeg2000Text.style.display = "block";
  }

  // Bilgileri sıfırla
  imageInfo.style.display = "none";
  imageInfoText.textContent = "";

  if (!file) {
    selectedFile.textContent = "No file selected";
    return;
  }

  selectedFile.textContent = `Selected: ${file.name}`;

  const reader = new FileReader();

  reader.onload = function (e) {
    const src = e.target.result;

    // Analysis Original Görüntü
    originalPreview.src = src;
    originalPreview.style.display = "block";
    originalText.style.display = "none";

    // Comparison Original Görüntü
    if (originalPreviewComparison) {
      originalPreviewComparison.src = src;
      originalPreviewComparison.style.display = "block";
      originalTextComparison.style.display = "none";
    }

    originalPreview.onload = function () {
      const w = originalPreview.naturalWidth;
      const h = originalPreview.naturalHeight;
      const mode = detectColorMode(originalPreview);
      const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);

      imageInfoText.textContent = `${w}×${h}  ·  ${mode}  ·  ${fileSizeMB} MB`;
      imageInfo.style.display = "block";

      if (originalImageMeta) originalImageMeta.textContent = `${w} × ${h} px  ·  ${mode}  ·  ${fileSizeMB} MB`;
      if (comparisonImageMeta) comparisonImageMeta.textContent = `${w} × ${h} px  ·  ${mode}  ·  ${fileSizeMB} MB`;
    };
  };

  reader.readAsDataURL(file);
});


// --- EVENT LISTENERS ---
modeInputs.forEach(input => input.addEventListener("change", updateModeUI));
methodInputs.forEach(input => input.addEventListener("change", updateMethodUI));
qualityRange.addEventListener("input", updateSliders);
dwtLevelRange.addEventListener("input", updateSliders);
imageTypeSelect.addEventListener("change", handleImageTypeChange);

waveletButtons.forEach(button => {
  button.addEventListener("click", () => {
    waveletButtons.forEach(btn => btn.classList.remove("active"));
    button.classList.add("active");
  });
});


// --- SIKIŞTIRMA İŞLEMİ (ANALYSIS & COMPARISON) ---
actionButton.addEventListener("click", async () => {
  const file = imageInput.files[0];

  if (!file) {
    alert("Lütfen önce bir resim seç!");
    return;
  }

  const mode = getSelectedMode();
  const quality = parseInt(qualityRange.value);
  const level = parseInt(dwtLevelRange.value);
  const wavelet = document.querySelector(".wavelet-btn.active")?.dataset.wavelet || "haar";

  try {
    actionButton.disabled = true;
    actionButton.textContent = "Processing...";

    // 1. Resmi Backend'e Yükle
    const formData = new FormData();
    formData.append("image", file);

    const uploadResponse = await fetch(`${BACKEND_URL}/upload`, {
      method: "POST",
      body: formData
    });

    const uploadData = await uploadResponse.json();
    if (!uploadData.success) {
      alert("Upload failed: " + uploadData.message);
      return;
    }

    // --- ANALYSIS MODE İŞLEMİ ---
    if (mode === "analysis") {
      const method = getSelectedMethod();
      const compressResponse = await fetch(`${BACKEND_URL}/compress`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: uploadData.filename, method, quality, wavelet, level })
      });

      const compressData = await compressResponse.json();
      if (!compressData.success) {
        alert("Compression failed: " + compressData.message);
        return;
      }

      // Metrikleri ve Resmi Güncelle
      updateAnalysisMetrics(compressData, file);
      reconPreview.src = `${BACKEND_URL}/uploads/${compressData.recon_filename}?t=${new Date().getTime()}`;
      reconPreview.style.display = "block";
      reconText.style.display = "none";

      alert("İşlem Başarılı!");
    } 
    
    // --- COMPARISON MODE İŞLEMİ ---
    else if (mode === "comparison") {
      // JPEG İstediği
      const resJpeg = await fetch(`${BACKEND_URL}/compress`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: uploadData.filename, method: "jpeg", quality, wavelet, level })
      });
      const dataJpeg = await resJpeg.json();

      // JPEG2000 İsteği
      const resJ2k = await fetch(`${BACKEND_URL}/compress`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: uploadData.filename, method: "jpeg2000", quality, wavelet, level })
      });
      const dataJ2k = await resJ2k.json();

      if (dataJpeg.success && dataJ2k.success) {
        // JPEG Resmi Gösterimi
        compJpegPreview.src = `${BACKEND_URL}/uploads/${dataJpeg.recon_filename}?t=${new Date().getTime()}`;
        compJpegPreview.style.display = "block";
        compJpegText.style.display = "none";

        // JPEG2000 Resmi Gösterimi
        compJpeg2000Preview.src = `${BACKEND_URL}/uploads/${dataJ2k.recon_filename}?t=${new Date().getTime()}`;
        compJpeg2000Preview.style.display = "block";
        compJpeg2000Text.style.display = "none";

        // Karşılaştırma Tablosunu Güncelle (ID'leri kullanarak)
        document.getElementById("comp-psnr-jpeg").textContent = dataJpeg.psnr ?? "—";
        document.getElementById("comp-psnr-j2k").textContent = dataJ2k.psnr ?? "—";
        
        document.getElementById("comp-mse-jpeg").textContent = dataJpeg.mse ?? "—";
        document.getElementById("comp-mse-j2k").textContent = dataJ2k.mse ?? "—";

        document.getElementById("comp-ratio-jpeg").textContent = dataJpeg.compression_ratio ?? "—";
        document.getElementById("comp-ratio-j2k").textContent = dataJ2k.compression_ratio ?? "—";

        document.getElementById("comp-size-jpeg").textContent = dataJpeg.compressed_size ? `${dataJpeg.compressed_size} KB` : "—";
        document.getElementById("comp-size-j2k").textContent = dataJ2k.compressed_size ? `${dataJ2k.compressed_size} KB` : "—";

        document.getElementById("comp-time-jpeg").textContent = dataJpeg.encoding_time ? `${dataJpeg.encoding_time} s` : "—";
        document.getElementById("comp-time-j2k").textContent = dataJ2k.encoding_time ? `${dataJ2k.encoding_time} s` : "—";

        alert("Karşılaştırma Başarılı!");
      }
    }

  } catch (error) {
    console.error("Backend connection error:", error);
    alert("Backend'e bağlanamadı.");
  } finally {
    actionButton.disabled = false;
    updateModeUI();
  }
});

// Sayfa yüklendiğinde varsayılan UI'yi ayarla
updateSliders();
updateModeUI();