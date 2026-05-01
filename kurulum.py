import os

# Oluşturulacak Klasörler (API için eklediğimiz uploads ve outputs dahil)
folders = [
    "frontend",
    "backend/routes",
    "dsp/jpeg",
    "dsp/jpeg2000",
    "dsp/preprocessing",
    "dsp/decoder",
    "dsp/evaluation",
    "utils",
    "tests",
    "data/sample_images",
    "data/uploads",   # Resim yükleme klasörü
    "data/outputs"    # İşlenmiş resim klasörü
]

# Oluşturulacak Dosyalar
files = [
    "frontend/index.html",
    "frontend/style.css",
    "frontend/app.js",
    "backend/app.py",
    "backend/routes/compression.py",
    "backend/routes/upload.py",
    "backend/routes/evaluation.py",
    "dsp/jpeg/dct.py",
    "dsp/jpeg/quantization.py",
    "dsp/jpeg/huffman.py",
    "dsp/jpeg2000/dwt.py",
    "dsp/jpeg2000/wavelet_filters.py",
    "dsp/jpeg2000/quantization.py",
    "dsp/preprocessing/normalize.py",
    "dsp/preprocessing/resize.py",
    "dsp/preprocessing/color_space.py",
    "dsp/decoder/inverse_dct.py",
    "dsp/decoder/inverse_dwt.py",
    "dsp/evaluation/metrics.py",
    "dsp/evaluation/graphs.py",
    "utils/file_utils.py",
    "utils/constants.py",
    "tests/test_jpeg.py",
    "tests/test_dwt.py",
    "requirements.txt",
    "README.md",
    ".gitignore"
]

print("Proje yapısı oluşturuluyor...")

# Klasörleri oluştur
for folder in folders:
    os.makedirs(folder, exist_ok=True)
    # Python'un bu klasörleri modül olarak tanıması için __init__.py ekleyelim (Opsiyonel ama profesyonel)
    if folder not in ["frontend", "data/sample_images", "data/uploads", "data/outputs"]:
        open(os.path.join(folder, "__init__.py"), 'a').close()

# Dosyaları oluştur
for file in files:
    open(file, 'a').close()

print("Bitti! Tüm dosya ve klasörler başarıyla oluşturuldu. 🚀")