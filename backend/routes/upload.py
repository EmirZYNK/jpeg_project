import os
import time
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


# ============================================================
# YARDIMCI FONKSİYON: Tek bir kanalı sıkıştırma pipeline'ından geçirir
# FR1 için: RGB resimlerde her kanal (R, G, B) bağımsız olarak bu fonksiyondan geçer
# ============================================================
def process_single_channel(channel_data, method, quality, wavelet, level, use_entropy):
    """
    Tek bir renk kanalını (veya gri tonlamalı resmi) sıkıştırma pipeline'ından geçirir.

    Returns:
        reconstructed: Yeniden oluşturulmuş kanal verisi (numpy array)
        huffman_bits: Huffman kodlama toplam bit sayısı (None ise entropy kapalı)
    """
    huffman_bits = None

    if method == "jpeg":
        # === ENCODER (SIKIŞTIRMA) ===
        dct_data = process_image_dct(channel_data)
        quantized_data = process_quantization(dct_data, quality=quality)

        # FR13/FR14: Entropy Coding (Opsiyonel)
        if use_entropy:
            huff_table = encode_huffman(quantized_data)
            flat_data = quantized_data.flatten().astype(int)
            huffman_bits = sum(len(huff_table.get(val, '0' * 8)) for val in flat_data)

        # === DECODER (GERİ AÇMA) ===
        dequantized_data = process_dequantization(quantized_data, quality=quality)
        reconstructed = process_image_idct(dequantized_data)

    elif method == "jpeg2000":
        # === ENCODER (SIKIŞTIRMA) ===
        dwt_coeffs = apply_dwt_2d(channel_data, wavelet_name=wavelet, level=level)
        quantized_dwt_data = quantize_dwt(dwt_coeffs, quality=quality)

        # FR13/FR14: Entropy Coding (Opsiyonel)
        if use_entropy:
            all_coeffs = []
            for c in quantized_dwt_data:
                if isinstance(c, np.ndarray):
                    all_coeffs.append(c.flatten())
                else:
                    for sub in c:
                        all_coeffs.append(sub.flatten())
            combined = np.concatenate(all_coeffs)
            huff_table = encode_huffman(combined)
            flat_data = combined.flatten().astype(int)
            huffman_bits = sum(len(huff_table.get(val, '0' * 8)) for val in flat_data)

        # === DECODER (GERİ AÇMA) ===
        dequantized_dwt_data = dequantize_dwt(quantized_dwt_data, quality=quality)
        reconstructed = apply_idwt_2d(dequantized_dwt_data, wavelet_name=wavelet)

    return reconstructed, huffman_bits


# --- Frontend'e Resim Gönderme Rotası ---
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
    is_lossless = data.get("is_lossless", False)
    use_entropy = data.get("use_entropy", False)

    if not filename:
        return jsonify({"success": False, "message": "filename is required."}), 400

    if method not in ["jpeg", "jpeg2000"]:
        return jsonify({"success": False, "message": "method must be 'jpeg' or 'jpeg2000'."}), 400

    image_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(image_path):
        return jsonify({"success": False, "message": "Uploaded image not found."}), 404

    # FR22: Kayıpsız mod seçildiyse quality'yi 100'e zorla
    if is_lossless:
        quality = 100

    # FR1: Resim renkli mi yoksa siyah-beyaz mı otomatik algıla
    image = Image.open(image_path)
    is_color = image.mode in ("RGB", "RGBA", "CMYK")

    if is_color:
        image_rgb = image.convert("RGB")
        img_array = np.array(image_rgb).astype(np.float32)
        channels = [img_array[:, :, i] for i in range(3)]  # R, G, B
        color_mode = "RGB"
    else:
        image_gray = image.convert("L")
        channels = [np.array(image_gray).astype(np.float32)]
        color_mode = "Grayscale"

    # Orijinal dosya boyutu (byte)
    original_file_size = os.path.getsize(image_path)

    # Oluşacak yeni resmin adı ve yolu (PNG formatında kaydediyoruz)
    recon_basename = os.path.splitext(filename)[0]
    recon_filename = f"reconstructed_{method}_{recon_basename}.png"
    recon_path = os.path.join(UPLOAD_FOLDER, recon_filename)

    # === ZAMANLAMA BAŞLAT ===
    start_time = time.time()

    # Her kanalı bağımsız olarak sıkıştırma pipeline'ından geçir
    reconstructed_channels = []
    total_huffman_bits = 0

    for channel in channels:
        recon_ch, huff_bits = process_single_channel(
            channel, method, quality, wavelet, level, use_entropy
        )
        # DWT boyut uyumsuzluğu olursa orijinal boyuta kırp
        h, w = channel.shape
        recon_ch = recon_ch[:h, :w]
        reconstructed_channels.append(np.clip(recon_ch, 0, 255).astype(np.uint8))
        if huff_bits is not None:
            total_huffman_bits += huff_bits

    # === ZAMANLAMA BİTİR ===
    elapsed_time = round(time.time() - start_time, 4)

    # Kanalları birleştir ve kaydet
    if is_color:
        reconstructed_img = np.stack(reconstructed_channels, axis=2)
        Image.fromarray(reconstructed_img, 'RGB').save(recon_path)
    else:
        reconstructed_img = reconstructed_channels[0]
        Image.fromarray(reconstructed_img).save(recon_path)

    # === BOYUT VE ORAN HESAPLAMA ===
    compressed_file_size = os.path.getsize(recon_path)
    compressed_size_kb = round(compressed_file_size / 1024, 2)

    if compressed_file_size > 0:
        compression_ratio = round(original_file_size / compressed_file_size, 2)
    else:
        compression_ratio = 0

    # === METRİK HESAPLAMA ===
    if is_color:
        original_norm = img_array / 255.0
        recon_norm = reconstructed_img.astype(np.float32) / 255.0
    else:
        original_norm = channels[0] / 255.0
        recon_norm = reconstructed_img.astype(np.float32) / 255.0

    psnr_val = calculate_psnr(original_norm, recon_norm)
    mse_val = calculate_mse(original_norm, recon_norm)

    # Eğer resim kayıpsızsa (birebir aynıysa) Infinity yazar, değilse yuvarlar.
    psnr_display = "Infinity" if psnr_val == float('inf') else round(psnr_val, 2)

    # Yanıt JSON'unu oluştur
    response = {
        "success": True,
        "message": f"{method.upper()} compression and reconstruction completed.",
        "recon_filename": recon_filename,
        "psnr": psnr_display,
        "mse": round(mse_val, 5),
        "compression_ratio": f"{compression_ratio}:1",
        "compressed_size": compressed_size_kb,
        "encoding_time": elapsed_time,
        "color_mode": color_mode
    }

    # FR13/FR14: Entropy coding istatistikleri
    if use_entropy and total_huffman_bits > 0:
        huffman_size_kb = round(total_huffman_bits / 8 / 1024, 2)
        uncompressed_bits = sum(ch.size for ch in channels) * 8
        entropy_ratio = round(uncompressed_bits / total_huffman_bits, 2)
        response["huffman_compressed_size"] = huffman_size_kb
        response["entropy_compression_ratio"] = f"{entropy_ratio}:1"

    return jsonify(response), 200