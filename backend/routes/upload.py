import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np

from dsp.jpeg.dct import process_image_dct
from dsp.jpeg.quantization import process_quantization
from dsp.jpeg.huffman import encode_huffman

from dsp.jpeg2000.dwt import apply_dwt_2d
from dsp.jpeg2000.quantization import quantize_dwt

upload_bp = Blueprint("upload_bp", __name__)

UPLOAD_FOLDER = "backend/data/uploads"
ALLOWED_EXTENSIONS = {"png", "bmp", "tif", "tiff"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@upload_bp.route("/upload", methods=["POST"])
def upload_image():
    if "image" not in request.files:
        return jsonify({
            "success": False,
            "message": "No image file received."
        }), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({
            "success": False,
            "message": "No selected file."
        }), 400

    if not allowed_file(file.filename):
        return jsonify({
            "success": False,
            "message": "Unsupported file format. Use PNG, BMP, TIFF."
        }), 400

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
        return jsonify({
            "success": False,
            "message": "No JSON data received."
        }), 400

    filename = data.get("filename")
    method = data.get("method")
    quality = int(data.get("quality", 75))
    wavelet = data.get("wavelet", "haar")
    level = int(data.get("level", 1))

    if not filename:
        return jsonify({
            "success": False,
            "message": "filename is required."
        }), 400

    if method not in ["jpeg", "jpeg2000"]:
        return jsonify({
            "success": False,
            "message": "method must be 'jpeg' or 'jpeg2000'."
        }), 400

    image_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(image_path):
        return jsonify({
            "success": False,
            "message": "Uploaded image not found."
        }), 404

    image = Image.open(image_path).convert("L")
    gray_image = np.array(image).astype(np.float32)

    if method == "jpeg":
        dct_data = process_image_dct(gray_image)
        quantized_data = process_quantization(dct_data, quality=quality)
        huffman_table = encode_huffman(quantized_data)

        return jsonify({
            "success": True,
            "message": "JPEG compression completed.",
            "filename": filename,
            "method": method,
            "quality": quality,
            "image_path": image_path,
            "input_shape": list(gray_image.shape),
            "huffman_table_size": len(huffman_table)
        }), 200

    if method == "jpeg2000":
        dwt_coeffs = apply_dwt_2d(
            gray_image,
            wavelet_name=wavelet,
            level=level
        )
        quantized_dwt_data = quantize_dwt(dwt_coeffs, quality=quality)

        return jsonify({
            "success": True,
            "message": "JPEG2000 compression completed.",
            "filename": filename,
            "method": method,
            "quality": quality,
            "wavelet": wavelet,
            "level": level,
            "image_path": image_path,
            "input_shape": list(gray_image.shape),
            "dwt_coeff_count": len(quantized_dwt_data)
        }), 200