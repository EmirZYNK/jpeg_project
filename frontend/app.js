
const modeInputs       = document.querySelectorAll('input[name="mode"]');
const methodInputs     = document.querySelectorAll('input[name="method"]');
const methodSection    = document.getElementById("methodSection");
const analysisView     = document.getElementById("analysisView");
const comparisonView   = document.getElementById("comparisonView");
const actionButton     = document.getElementById("actionButton");

const analysisTitle    = document.getElementById("analysisTitle");
const reconstructedTitle = document.getElementById("reconstructedTitle");
const analysisNote     = document.getElementById("analysisNote");

const qualityRange     = document.getElementById("qualityRange");
const dwtLevelRange    = document.getElementById("dwtLevelRange");
const qualityValue     = document.getElementById("qualityValue");
const dwtValue         = document.getElementById("dwtValue");

const imageInput       = document.getElementById("imageInput");
const selectedFile     = document.getElementById("selectedFile");
const imageInfo        = document.getElementById("imageInfo");
const imageInfoText    = document.getElementById("imageInfoText");

const originalPreview           = document.getElementById("originalPreview");
const originalText              = document.getElementById("originalText");
const originalImageMeta         = document.getElementById("originalImageMeta");

const originalPreviewComparison = document.getElementById("originalPreviewComparison");
const originalTextComparison    = document.getElementById("originalTextComparison");
const comparisonImageMeta       = document.getElementById("comparisonImageMeta");

const imageTypeSelect    = document.getElementById("imageType");
const biomedicalWarning  = document.getElementById("biomedicalWarning");
const compressionLossy   = document.getElementById("compressionLossy");
const compressionLossless = document.getElementById("compressionLossless");
const waveletButtons     = document.querySelectorAll(".wavelet-btn");


function getSelectedMode()   { return document.querySelector('input[name="mode"]:checked').value; }
function getSelectedMethod() { return document.querySelector('input[name="method"]:checked').value; }

function detectColorMode(img) {
  const canvas = document.createElement("canvas");
  canvas.width  = Math.min(img.naturalWidth,  64);
  canvas.height = Math.min(img.naturalHeight, 64);
  const ctx = canvas.getContext("2d");
  ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
  const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
  let isGray = true;
  for (let i = 0; i < data.length; i += 4) {
    if (data[i] !== data[i + 1] || data[i] !== data[i + 2]) { isGray = false; break; }
  }
  return isGray ? "Grayscale" : "RGB";
}


function showImageMeta(img, metaEl) {
  const w = img.naturalWidth;
  const h = img.naturalHeight;
  const mode = detectColorMode(img);
  if (metaEl) metaEl.textContent = `${w} × ${h} px  ·  ${mode}`;
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
    compressionLossy.checked    = false;
    compressionLossy.disabled   = true;

    
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
  dwtValue.textContent     = dwtLevelRange.value;
}


imageInput.addEventListener("change", () => {
  const file = imageInput.files[0];

  
  originalPreview.src = "";
  originalPreview.style.display = "none";
  originalText.style.display    = "block";
  if (originalImageMeta) originalImageMeta.textContent = "";

  if (originalPreviewComparison) {
    originalPreviewComparison.src = "";
    originalPreviewComparison.style.display = "none";
  }
  if (originalTextComparison) originalTextComparison.style.display = "block";
  if (comparisonImageMeta) comparisonImageMeta.textContent = "";

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

    
    originalPreview.src = src;
    originalPreview.style.display = "block";
    originalText.style.display    = "none";

    
    if (originalPreviewComparison) {
      originalPreviewComparison.src = src;
      originalPreviewComparison.style.display = "block";
    }
    if (originalTextComparison) originalTextComparison.style.display = "none";

    
    originalPreview.onload = function () {
      const w    = originalPreview.naturalWidth;
      const h    = originalPreview.naturalHeight;
      const mode = detectColorMode(originalPreview);
      const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);

      
      imageInfoText.textContent = `${w}×${h}  ·  ${mode}  ·  ${fileSizeMB} MB`;
      imageInfo.style.display   = "block";

      
      if (originalImageMeta) originalImageMeta.textContent = `${w} × ${h} px  ·  ${mode}  ·  ${fileSizeMB} MB`;

      
      if (originalPreviewComparison) {
        originalPreviewComparison.onload = function () {
          if (comparisonImageMeta)
            comparisonImageMeta.textContent = `${w} × ${h} px  ·  ${mode}  ·  ${fileSizeMB} MB`;
        };
      }
    };
  };
  reader.readAsDataURL(file);
});


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


actionButton.addEventListener("click", () => {
  const mode            = getSelectedMode();
  const method          = mode === "analysis" ? getSelectedMethod() : "both";
  const imageType       = imageTypeSelect.value;
  const quality         = qualityRange.value;
  const dwtLevel        = dwtLevelRange.value;
  const wavelet         = document.querySelector(".wavelet-btn.active").dataset.wavelet;
  const compressionType = document.querySelector('input[name="compressionType"]:checked').value;
  const entropyCoding   = document.getElementById("entropyCoding").checked;
  const file            = imageInput.files[0];

  const params = { file: file ? file.name : null, mode, method, imageType, quality, dwtLevel, wavelet, compressionType, entropyCoding };
  console.log("Compression params:", params);

  
  alert("Arayüz iskeleti çalışıyor. Backend bağlanınca gerçek işlem burada yapılacak.");
});


updateSliders();
updateModeUI();