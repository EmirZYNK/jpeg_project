import os
from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np

# --- ENCODER (İleri Dönüşüm) IMPORTS ---
from dsp.jpeg.dct import process_image_dct
from dsp.jpeg.quantization import process_quantization
from dsp.jpeg.huffman import encode_huffman
from dsp.jpeg2000.dwt import apply_dwt_2d
from dsp.jpeg2000.quantization import quantize_dwt

# --- DECODER (Ters Dönüşüm) IMPORTS ---
from dsp.decoder.inverse_dct import process_image_idct
from dsp.jpeg.quantization import process_dequantization
from dsp.decoder.inverse_dwt import apply_idwt_2d
from dsp.jpeg2000.quantization import dequantize_dwt

# --- METRİKLER IMPORTS ---
from dsp.evaluation.metrics import calculate_psnr, calculate_mse

upload_bp = Blueprint("upload_bp", __name__)

# Dizin yolu ayarları (Hataları önlemek için mutlak yol kullanıyoruz)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "data", "uploads")
ALLOWED_EXTENSIONS = {"png", "bmp", "tif", "tiff", "jpg", "jpeg"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )

# --- YENİ EKLENDİ: Frontend'e Resim Gönderme Rotası ---
@upload_bp.route("/uploads/<filename>")
def get_image(filename):
    """Sıkıştırılıp yeniden oluşturulmuş resmi arayüze gönderir."""
    return send_from_directory(UPLOAD_FOLDER, filename)


@upload_bp.route("/upload", methods=["POST"])
def upload_image():
    if "image" not in request.files:
        return jsonify({"success": False, "message": "No image file received."}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"success": False, "message": "No selected file."}), 400

    if not allowed_file(file.filename):
        return jsonify({"success": False, "message": "Unsupported file format. Use PNG, BMP, TIFF, JPG."}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)

    return jsonify({
        "success": True,
        "message": "Image uploaded successfully.",
        "filename": filename,
        "path": save_path
    }), 200


@upload_bp.route("/compress", methods=["POST"])
def compress_image():
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({"success": False, "message": "No JSON data received."}), 400

    filename = data.get("filename")
    method = data.get("method")
    quality = int(data.get("quality", 75))
    wavelet = data.get("wavelet", "haar")
    level = int(data.get("level", 1))

    if not filename:
        return jsonify({"success": False, "message": "filename is required."}), 400

    if method not in ["jpeg", "jpeg2000"]:
        return jsonify({"success": False, "message": "method must be 'jpeg' or 'jpeg2000'."}), 400

    image_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(image_path):
        return jsonify({"success": False, "message": "Uploaded image not found."}), 404

    # Resmi Oku ve Numpy Array'e Çevir
    image = Image.open(image_path).convert("L")
    gray_image = np.array(image).astype(np.float32)
    
    # Metrik hesaplamaları için orijinal resmi 0-1 aralığında normalize et
    normalized_img = gray_image / 255.0

    # Oluşacak yeni resmin adı ve yolu
    recon_filename = f"reconstructed_{method}_{filename}"
    recon_path = os.path.join(UPLOAD_FOLDER, recon_filename)

    if method == "jpeg":
        # === ENCODER (SIKIŞTIRMA) ===
        dct_data = process_image_dct(gray_image)
        quantized_data = process_quantization(dct_data, quality=quality)
        huffman_table = encode_huffman(quantized_data)
        
        # === DECODER (GERİ AÇMA) ===
        dequantized_data = process_dequantization(quantized_data, quality=quality)
        reconstructed_gray = process_image_idct(dequantized_data)

    elif method == "jpeg2000":
        # === ENCODER (SIKIŞTIRMA) ===
        dwt_coeffs = apply_dwt_2d(gray_image, wavelet_name=wavelet, level=level)
        quantized_dwt_data = quantize_dwt(dwt_coeffs, quality=quality)

        # === DECODER (GERİ AÇMA) ===
        dequantized_dwt_data = dequantize_dwt(quantized_dwt_data, quality=quality)
        reconstructed_gray = apply_idwt_2d(dequantized_dwt_data, wavelet_name=wavelet)

    # Değerleri 0-255 aralığına sıkıştır ve tam sayıya çevir
    reconstructed_gray = np.clip(reconstructed_gray, 0, 255).astype(np.uint8)
    
    # Yeni resmi "uploads" klasörüne kaydet
    Image.fromarray(reconstructed_gray).save(recon_path)

    # === METRİK HESAPLAMA ===
    # Metrik hesabı için oluşturulan resmi de 0-1 aralığına çekiyoruz
    norm_reconstructed = reconstructed_gray.astype(np.float32) / 255.0
    
    psnr_val = calculate_psnr(normalized_img, norm_reconstructed)
    mse_val = calculate_mse(normalized_img, norm_reconstructed)

    # Eğer resim kayıpsızsa (birebir aynıysa) Infinity yazar, değilse yuvarlar.
    psnr_display = "Infinity" if psnr_val == float('inf') else round(psnr_val, 2)

    return jsonify({
        "success": True,
        "message": f"{method.upper()} compression and reconstruction completed.",
        "recon_filename": recon_filename, # Frontend'in resmi çekeceği dosya adı
        "psnr": psnr_display,
        "mse": round(mse_val, 5)
    }), 200