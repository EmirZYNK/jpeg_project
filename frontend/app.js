let selectedFile = null;
let selectedImageUrl = "";

const imageCompareRange2 = document.getElementById("imageCompareRange2");
const afterLayer2 = document.getElementById("afterLayer2");
const sliderLine2 = document.getElementById("sliderLine2");
const originalPreview2 = document.getElementById("originalPreview2");

const imageCompareRange = document.getElementById("imageCompareRange");
const afterLayer = document.getElementById("afterLayer");
const sliderLine = document.getElementById("sliderLine");

const imageTypeSelect = document.getElementById("imageTypeSelect");
const modeSelect = document.getElementById("modeSelect");
const imageInput = document.getElementById("imageInput");
const algorithmSelect = document.getElementById("algorithmSelect");

const jpegParams = document.getElementById("jpegParams");
const jpeg2000Params = document.getElementById("jpeg2000Params");

const qualitySlider = document.getElementById("qualitySlider");
const qualityValue = document.getElementById("qualityValue");

const waveletSelect = document.getElementById("waveletSelect");
const levelInput = document.getElementById("levelInput");
const factorSlider = document.getElementById("factorSlider");
const factorValue = document.getElementById("factorValue");

const compressBtn = document.getElementById("compressBtn");

const originalPreview = document.getElementById("originalPreview");
const compressedPreview = document.getElementById("compressedPreview");
const jpeg2000Preview = document.getElementById("jpeg2000Preview");
const jpeg2000Box = document.getElementById("jpeg2000Box");
const compressedTitle = document.getElementById("compressedTitle");

const resultText = document.getElementById("resultText");

const plotBox = document.getElementById("plotBox");
const plotPreview = document.getElementById("plotPreview");
const plotTitle = document.getElementById("plotTitle");

const errorMapContainer = document.getElementById("errorMapContainer");
const errorMapItem2 = document.getElementById("errorMapItem2");
const errorMapPreview = document.getElementById("errorMapPreview");
const errorMapPreview2 = document.getElementById("errorMapPreview2");
const errorMapTitle = document.getElementById("errorMapTitle");
const errorMapTitle2 = document.getElementById("errorMapTitle2");

const modeTabs = document.querySelectorAll(".mode-tab");
const algoButtons = document.querySelectorAll(".algo-btn");

const mseCard = document.getElementById("mseCard");
const psnrCard = document.getElementById("psnrCard");
const ssimCard = document.getElementById("ssimCard");
const ratioCard = document.getElementById("ratioCard");


function resetSliders() {
    imageCompareRange.value = 50;
    afterLayer.style.clipPath = "inset(0 50% 0 0)";
    sliderLine.style.left = "50%";

    imageCompareRange2.value = 50;
    afterLayer2.style.clipPath = "inset(0 50% 0 0)";
    sliderLine2.style.left = "50%";
}


function resetResults() {
    compressedPreview.src = "";
    jpeg2000Preview.src = "";

    if (selectedImageUrl) {
        originalPreview.src = selectedImageUrl;
        originalPreview2.src = selectedImageUrl;
    }

    if (modeSelect.value === "comparison") {
        jpeg2000Box.style.display = "block";
        compressedTitle.innerText = "JPEG";
    } else {
        jpeg2000Box.style.display = "none";
        compressedTitle.innerText = "Compressed";
    }

    plotPreview.src = "";
    plotBox.style.display = "none";

    errorMapPreview.src = "";
    errorMapPreview2.src = "";
    errorMapContainer.style.display = "none";
    errorMapItem2.style.display = "none";

    resultText.innerHTML = "";

    mseCard.innerText = "-";
    psnrCard.innerText = "-";
    ssimCard.innerText = "-";
    ratioCard.innerText = "-";

    resetSliders();
}


function setMetricCards(mse, psnr, ssim, ratio) {
    mseCard.innerHTML = mse ?? "-";
    psnrCard.innerHTML = psnr ?? "-";
    ssimCard.innerHTML = ssim ?? "-";
    ratioCard.innerHTML = ratio ? `${ratio}x` : "-";
}


function updateAlgorithmButtons() {
    algoButtons.forEach(btn => {
        btn.classList.toggle("active", btn.dataset.algorithm === algorithmSelect.value);
    });
}


function updateModeTabs() {
    modeTabs.forEach(tab => {
        tab.classList.toggle("active", tab.dataset.mode === modeSelect.value);
    });
}


function updateAlgorithmUI() {
    const algorithm = algorithmSelect.value;

    if (algorithm === "jpeg") {
        jpegParams.style.display = "block";
        jpeg2000Params.style.display = "none";
    } else {
        jpegParams.style.display = "none";
        jpeg2000Params.style.display = "block";
    }

    updateAlgorithmButtons();
}


function updateModeUI() {
    const mode = modeSelect.value;
    const imageType = imageTypeSelect.value;
    const algorithmContainer = document.getElementById("algorithmContainer");

    if (imageType === "biomedical") {
        modeSelect.value = "analysis";
        modeSelect.disabled = true;

        algorithmSelect.value = "jpeg2000";
        algorithmSelect.disabled = true;

        algorithmContainer.style.display = "block";
        jpegParams.style.display = "none";
        jpeg2000Params.style.display = "block";

        jpeg2000Box.style.display = "none";
        compressedTitle.innerText = "Compressed";

        modeTabs.forEach(tab => {
            tab.disabled = tab.dataset.mode === "comparison";
        });

        algoButtons.forEach(btn => {
            btn.disabled = btn.dataset.algorithm === "jpeg";
        });

        updateModeTabs();
        updateAlgorithmButtons();
        return;
    }

    modeSelect.disabled = false;
    algorithmSelect.disabled = false;

    modeTabs.forEach(tab => tab.disabled = false);
    algoButtons.forEach(btn => btn.disabled = false);

    if (mode === "comparison") {
        algorithmContainer.style.display = "none";
        jpegParams.style.display = "block";
        jpeg2000Params.style.display = "block";

        jpeg2000Box.style.display = "block";
        compressedTitle.innerText = "JPEG";
    } else {
        algorithmContainer.style.display = "block";
        jpeg2000Box.style.display = "none";
        compressedTitle.innerText = "Compressed";
        updateAlgorithmUI();
    }

    updateModeTabs();
    updateAlgorithmButtons();
}


function renderComparisonResults(data) {
    resultText.innerHTML = `
        <div class="result-summary">
            <div class="result-box">
                <h3>Test Information</h3>
                <div class="result-row"><span>Mode</span><span>Comparison</span></div>
                <div class="result-row"><span>Image Type</span><span>${data.image_type}</span></div>
            </div>

            <div class="result-box">
                <h3>Quick Result</h3>
                <div class="result-row"><span>Better PSNR</span><span>${data.jpeg.psnr > data.jpeg2000.psnr ? "JPEG" : "JPEG2000"}</span></div>
                <div class="result-row"><span>Better SSIM</span><span>${data.jpeg.ssim > data.jpeg2000.ssim ? "JPEG" : "JPEG2000"}</span></div>
                <div class="result-row"><span>Better Ratio</span><span>${data.jpeg.compression_ratio > data.jpeg2000.compression_ratio ? "JPEG" : "JPEG2000"}</span></div>
            </div>
        </div>

        <div class="result-methods">
            <div class="result-box jpeg-result">
                <h3>JPEG Results</h3>
                <div class="result-row"><span>Quality</span><span>${data.jpeg.quality}</span></div>
                <div class="result-row"><span>Original Size</span><span>${data.jpeg.original_size_kb} KB</span></div>
                <div class="result-row"><span>Compressed Size</span><span>${data.jpeg.compressed_size_kb} KB</span></div>
                <div class="result-row"><span>Output Size</span><span>${data.jpeg.output_file_size_kb || "N/A"} KB</span></div>
                <div class="result-row"><span>Compression Ratio</span><span>${data.jpeg.compression_ratio}x</span></div>
                <div class="result-row"><span>BPP</span><span>${data.jpeg.bpp}</span></div>
                <div class="result-row"><span>MSE</span><span>${data.jpeg.mse}</span></div>
                <div class="result-row"><span>PSNR</span><span>${data.jpeg.psnr} dB</span></div>
                <div class="result-row"><span>SSIM</span><span>${data.jpeg.ssim}</span></div>
            </div>

            <div class="result-box jp2-result">
                <h3>JPEG2000 Results</h3>
                <div class="result-row"><span>Wavelet</span><span>${data.jpeg2000.wavelet}</span></div>
                <div class="result-row"><span>DWT Level</span><span>${data.jpeg2000.level}</span></div>
                <div class="result-row"><span>Factor</span><span>${data.jpeg2000.factor}</span></div>
                <div class="result-row"><span>Original Size</span><span>${data.jpeg2000.original_size_kb} KB</span></div>
                <div class="result-row"><span>Simulated Compressed Size</span><span>${data.jpeg2000.compressed_size_kb} KB</span></div>
                <div class="result-row"><span>Compression Ratio</span><span>${data.jpeg2000.compression_ratio}x</span></div>
                <div class="result-row"><span>BPP</span><span>${data.jpeg2000.bpp}</span></div>
                <div class="result-row"><span>MSE</span><span>${data.jpeg2000.mse}</span></div>
                <div class="result-row"><span>PSNR</span><span>${data.jpeg2000.psnr} dB</span></div>
                <div class="result-row"><span>SSIM</span><span>${data.jpeg2000.ssim}</span></div>
            </div>
        </div>

        <div class="note-box">
            JPEG size is calculated from the generated JPG file. JPEG2000 size is estimated from transform coefficients because this system does not generate a JP2 codestream.
        </div>
    `;
}


function renderAnalysisResults(data) {
    resultText.innerHTML = `
        <div class="result-summary">
            <div class="result-box">
                <h3>Test Information</h3>
                <div class="result-row"><span>Mode</span><span>Analysis</span></div>
                <div class="result-row"><span>Algorithm</span><span>${data.algorithm}</span></div>
                <div class="result-row"><span>Image Type</span><span>${data.image_type}</span></div>
            </div>

            <div class="result-box">
            <h3>Parameters</h3>

            ${
                data.algorithm === "jpeg"
                ? `
                    <div class="result-row"><span>Quality</span><span>${data.quality}</span></div>
                `
                : `
                    <div class="result-row"><span>Wavelet</span><span>${data.wavelet}</span></div>
                    <div class="result-row"><span>DWT Level</span><span>${data.level}</span></div>
                    <div class="result-row"><span>Factor</span><span>${data.factor}</span></div>
                `
            }
        </div>
        </div>

        <div class="result-methods one-column">
            <div class="result-box">
                <h3>Compression Results</h3>
                <div class="result-row"><span>Original Size</span><span>${data.original_size_kb} KB</span></div>
                <div class="result-row"><span>Compressed / Estimated Size</span><span>${data.compressed_size_kb} KB</span></div>
                <div class="result-row"><span>Output Size</span><span>${data.output_file_size_kb || "N/A"} KB</span></div>
                <div class="result-row"><span>Compression Ratio</span><span>${data.compression_ratio}x</span></div>
                <div class="result-row"><span>BPP</span><span>${data.bpp}</span></div>
                <div class="result-row"><span>MSE</span><span>${data.mse}</span></div>
                <div class="result-row"><span>PSNR</span><span>${data.psnr} dB</span></div>
                <div class="result-row"><span>SSIM</span><span>${data.ssim}</span></div>
            </div>
        </div>

        <div class="note-box">
            JPEG output is saved as a JPG file. JPEG2000 output is a reconstructed PNG image, and its compressed size is estimated from transform coefficients.
        </div>
    `;
}


modeTabs.forEach(tab => {
    tab.addEventListener("click", () => {
        if (tab.disabled) return;

        modeSelect.value = tab.dataset.mode;
        updateModeUI();
        resetResults();
    });
});


algoButtons.forEach(btn => {
    btn.addEventListener("click", () => {
        if (btn.disabled) return;

        algorithmSelect.value = btn.dataset.algorithm;
        updateAlgorithmUI();
        resetResults();
    });
});


imageTypeSelect.addEventListener("change", () => {
    updateModeUI();
    resetResults();
});


algorithmSelect.addEventListener("change", () => {
    updateAlgorithmUI();
    resetResults();
});


qualitySlider.addEventListener("input", () => {
    qualityValue.innerText = qualitySlider.value;
});


factorSlider.addEventListener("input", () => {
    factorValue.innerText = factorSlider.value;
});


imageInput.addEventListener("change", () => {
    selectedFile = imageInput.files[0];

    if (selectedFile) {
        selectedImageUrl = URL.createObjectURL(selectedFile);

        originalPreview.src = selectedImageUrl;
        originalPreview2.src = selectedImageUrl;

        resetResults();
    }
});


compressBtn.addEventListener("click", async () => {
    const file = selectedFile;

    if (!file) {
        alert("Please select an image first.");
        return;
    }

    const mode = modeSelect.value;
    const algorithm = algorithmSelect.value;

    const formData = new FormData();
    formData.append("image", file);
    formData.append("algorithm", algorithm);
    formData.append("image_type", imageTypeSelect.value);

    if (mode === "comparison") {
        formData.append("quality", qualitySlider.value);
        formData.append("factor", factorSlider.value);
        formData.append("wavelet", waveletSelect.value);
        formData.append("level", levelInput.value);
    } else {
        if (algorithm === "jpeg") {
            formData.append("quality", qualitySlider.value);
        }

        if (algorithm === "jpeg2000") {
            formData.append("factor", factorSlider.value);
            formData.append("wavelet", waveletSelect.value);
            formData.append("level", levelInput.value);
        }
    }

    const endpoint = mode === "comparison" ? "/api/compare" : "/api/compress";

    compressBtn.innerText = "Processing...";
    compressBtn.disabled = true;

    try {
        const response = await fetch(endpoint, {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            alert(data.error || "An error occurred.");
            return;
        }

        if (mode === "comparison") {
            compressedTitle.innerText = "JPEG";
            compressedPreview.src = data.jpeg.compressed_url;

            jpeg2000Box.style.display = "block";
            jpeg2000Preview.src = data.jpeg2000.compressed_url;
            originalPreview2.src = originalPreview.src;

            setMetricCards(
                `<div class="metric-compare">
                    <div class="metric-line"><b>JPEG</b><span>${data.jpeg.mse}</span></div>
                    <div class="metric-line"><b>JPEG2000</b><span>${data.jpeg2000.mse}</span></div>
                </div>`,
                `<div class="metric-compare">
                    <div class="metric-line"><b>JPEG</b><span>${data.jpeg.psnr}</span></div>
                    <div class="metric-line"><b>JPEG2000</b><span>${data.jpeg2000.psnr}</span></div>
                </div>`,
                `<div class="metric-compare">
                    <div class="metric-line"><b>JPEG</b><span>${data.jpeg.ssim}</span></div>
                    <div class="metric-line"><b>JPEG2000</b><span>${data.jpeg2000.ssim}</span></div>
                </div>`,
                `<div class="metric-compare">
                    <div class="metric-line"><b>JPEG</b><span>${data.jpeg.compression_ratio}x</span></div>
                    <div class="metric-line"><b>JPEG2000</b><span>${data.jpeg2000.compression_ratio}x</span></div>
                </div>`
            );

            if (data.plot_url) {
                plotBox.style.display = "block";
                plotPreview.src = data.plot_url;
                plotTitle.innerText = "JPEG vs JPEG2000 Comparison Graph";
            } else {
                plotBox.style.display = "none";
                plotPreview.src = "";
            }

            if (data.jpeg && data.jpeg.error_url && data.jpeg2000 && data.jpeg2000.error_url) {
                errorMapContainer.style.display = "block";

                errorMapTitle.innerText = "JPEG Error Map";
                errorMapPreview.src = data.jpeg.error_url + "?t=" + Date.now();

                errorMapItem2.style.display = "block";
                errorMapTitle2.innerText = "JPEG2000 Error Map";
                errorMapPreview2.src = data.jpeg2000.error_url + "?t=" + Date.now();
            } else {
                errorMapContainer.style.display = "none";
                errorMapPreview.src = "";
                errorMapPreview2.src = "";
                errorMapItem2.style.display = "none";
            }

            renderComparisonResults(data);
            return;
        }

        compressedPreview.src = data.compressed_url;

        setMetricCards(
            data.mse,
            data.psnr,
            data.ssim,
            data.compression_ratio
        );

        if (data.plot_url) {
            plotBox.style.display = "block";
            plotPreview.src = data.plot_url;

            if (data.algorithm === "jpeg") {
                plotTitle.innerText = "JPEG Quality Analysis Graph";
            } else if (data.algorithm === "jpeg2000") {
                plotTitle.innerText = "JPEG2000 Factor / BPP Analysis Graph";
            } else {
                plotTitle.innerText = "Compression Analysis Graph";
            }
        } else {
            plotBox.style.display = "none";
            plotPreview.src = "";
        }

        if (data.error_url && data.image_type !== "biomedical") {
            errorMapContainer.style.display = "block";

            errorMapTitle.innerText = "Error Map";
            errorMapPreview.src = data.error_url + "?t=" + Date.now();

            errorMapItem2.style.display = "none";
            errorMapPreview2.src = "";
        } else {
            errorMapContainer.style.display = "none";
            errorMapPreview.src = "";
            errorMapPreview2.src = "";
            errorMapItem2.style.display = "none";
        }

        renderAnalysisResults(data);

    } catch (error) {
        console.error(error);
        alert("Backend connection error.");
    } finally {
        compressBtn.innerText = "Run Test →";
        compressBtn.disabled = false;
    }
});


imageCompareRange.addEventListener("input", () => {
    const value = imageCompareRange.value;
    afterLayer.style.clipPath = `inset(0 ${100 - value}% 0 0)`;
    sliderLine.style.left = `${value}%`;
});


imageCompareRange2.addEventListener("input", () => {
    const value = imageCompareRange2.value;
    afterLayer2.style.clipPath = `inset(0 ${100 - value}% 0 0)`;
    sliderLine2.style.left = `${value}%`;
});


updateAlgorithmUI();
updateModeUI();