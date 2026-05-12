from flask import Blueprint, request, jsonify
import os
import cv2
import time
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np

ALLOWED_WAVELETS = {"haar", "db1", "db2", "bior4.4", "sym2"}


def clamp_int(value, default, min_value, max_value=None):
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = default

    value = max(min_value, value)

    if max_value is not None:
        value = min(max_value, value)

    return value


def validate_wavelet(value):
    if value not in ALLOWED_WAVELETS:
        return "haar"
    return value


from dsp.jpeg.codec import encode_decode_jpeg_color
from dsp.jpeg2000.codec import (
    encode_decode_jpeg2000_color,
    encode_decode_jpeg2000_lossless_color
)
from dsp.evaluation.metrics import calculate_metrics
from utils.image_utils import generate_error_map
from dsp.evaluation.graphs import (
    generate_quality_analysis_plot,
    generate_jpeg2000_analysis_plot,
    generate_comparison_plot
)

compression_bp = Blueprint("compression", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "data", "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "data", "outputs")
PLOT_FOLDER = os.path.join(BASE_DIR, "data", "plots")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(PLOT_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "tif", "tiff"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def read_image_safe(path):
    img = Image.open(path).convert("RGB")
    return np.array(img)[:, :, ::-1]


def get_size_info(original_size_bytes, compressed_size_bytes, output_path, pixel_count):
    output_size_bytes = os.path.getsize(output_path)

    return {
        "original_size_kb": round(original_size_bytes / 1024, 2),
        "compressed_size_kb": round(compressed_size_bytes / 1024, 2),
        "output_file_size_kb": round(output_size_bytes / 1024, 2),
        "compression_ratio": round(original_size_bytes / max(compressed_size_bytes, 1), 2),
        "bpp": round((compressed_size_bytes * 8) / pixel_count, 4),
        "size_type": "real_output_file_size"
    }


def write_jpeg2000_file(output_path, image, factor):
    # Lossy JPEG2000 writing for natural/synthetic/hybrid images.
    # Small value = smaller file.
    factor = max(1, int(factor))

    if factor < 10:
        jp2_quality = 20
    elif factor < 20:
        jp2_quality = 10
    else:
        jp2_quality = 1

    success = cv2.imwrite(
        output_path,
        image,
        [int(cv2.IMWRITE_JPEG2000_COMPRESSION_X1000), jp2_quality]
    )

    if not success:
        raise RuntimeError("JPEG2000 file could not be written.")


def write_lossless_jpeg2000_file(output_path, image_bgr):
    """
    Biomedical images require true lossless behavior.
    This function writes JPEG2000 with reversible/lossless settings using Pillow.
    """
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(image_rgb)

    try:
        pil_img.save(
            output_path,
            format="JPEG2000",
            irreversible=False
        )
    except Exception as e:
        raise RuntimeError(f"Lossless JPEG2000 file could not be written: {str(e)}")


def read_jpeg2000_as_bgr(path):
    """
    Reads the saved JP2 file back and converts it to BGR for pixel-level verification.
    """
    try:
        img_rgb = Image.open(path).convert("RGB")
        return np.array(img_rgb)[:, :, ::-1]
    except Exception as e:
        raise RuntimeError(f"Saved JPEG2000 file could not be read back: {str(e)}")

@compression_bp.route("/compress", methods=["POST"])
def compress_image():
    if "image" not in request.files:
        return jsonify({"error": "No image file uploaded"}), 400

    image = request.files["image"]

    if image.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(image.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    filename = secure_filename(image.filename)
    name_without_ext = filename.rsplit(".", 1)[0]
    timestamp = int(time.time() * 1000)

    upload_path = os.path.join(UPLOAD_FOLDER, filename)
    image.save(upload_path)

    algorithm = request.form.get("algorithm", "jpeg")
    image_type = request.form.get("image_type", "natural")
    quality = clamp_int(request.form.get("quality", 50), default=50, min_value=1, max_value=100)

    try:
        original_img = read_image_safe(upload_path)
        original_gray = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)
    except Exception as e:
        return jsonify({"error": f"Image could not be processed: {str(e)}"}), 500

    original_size_bytes = os.path.getsize(upload_path)
    height, width = original_img.shape[:2]
    pixel_count = height * width

    if image_type == "biomedical":
        wavelet = validate_wavelet(request.form.get("wavelet", "haar"))
        level = clamp_int(request.form.get("level", 2), default=2, min_value=1, max_value=5)

        try:
            result = encode_decode_jpeg2000_lossless_color(
                original_img,
                wavelet=wavelet,
                level=level
            )
        except Exception as e:
            return jsonify({"error": f"JPEG2000 lossless compression failed: {str(e)}"}), 500

        reconstructed = result["reconstructed"]

        output_filename = f"jpeg2000_lossless_result_{name_without_ext}_{timestamp}.jp2"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        try:
            write_lossless_jpeg2000_file(output_path, original_img)
            reconstructed = read_jpeg2000_as_bgr(output_path)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

        # True lossless verification:
        # The saved JP2 file is decoded again and compared pixel-by-pixel with the original image.
        if not np.array_equal(original_img, reconstructed):
            diff = cv2.absdiff(original_img, reconstructed)
            max_diff = int(diff.max())

            return jsonify({
                "error": "Lossless verification FAILED: decoded JP2 is not identical to the original image.",
                "max_pixel_difference": max_diff
            }), 500

        preview_filename = f"preview_jpeg2000_lossless_{name_without_ext}_{timestamp}.png"
        preview_path = os.path.join(OUTPUT_FOLDER, preview_filename)
        cv2.imwrite(preview_path, reconstructed)

        reconstructed_gray = cv2.cvtColor(reconstructed, cv2.COLOR_BGR2GRAY)

        error_filename = f"error_jpeg2000_lossless_{name_without_ext}_{timestamp}.png"
        error_path = os.path.join(PLOT_FOLDER, error_filename)

        error_map = np.zeros_like(original_img)
        cv2.imwrite(error_path, error_map)

        mse, psnr, ssim = calculate_metrics(original_gray, reconstructed_gray)

        output_size_bytes = os.path.getsize(output_path)

        return jsonify({
            "algorithm": "jpeg2000-lossless",
            "image_type": image_type,
            "quality": "N/A",
            "factor": result["factor"],
            "wavelet": result["wavelet"],
            "level": result["level"],
            "original_size_kb": round(original_size_bytes / 1024, 2),
            "compressed_size_kb": round(output_size_bytes / 1024, 2),
            "output_file_size_kb": round(output_size_bytes / 1024, 2),
            "compression_ratio": round(original_size_bytes / max(output_size_bytes, 1), 2),
            "bpp": round((output_size_bytes * 8) / pixel_count, 4),
            "mse": mse,
            "psnr": psnr,
            "ssim": ssim,
            "compressed_url": f"/outputs/{preview_filename}",
            "download_url": f"/outputs/{output_filename}",
            "plot_url": "",
            "error_url": f"/plots/{error_filename}",
            "size_type": "jpeg2000_output_file_size"
        })

    if algorithm == "jpeg":
        try:
            result = encode_decode_jpeg_color(original_img, quality=quality)
        except Exception as e:
            return jsonify({"error": f"JPEG compression failed: {str(e)}"}), 500

        reconstructed = result["reconstructed"]

        output_filename = f"jpeg_result_{name_without_ext}_{timestamp}.jpg"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        cv2.imwrite(
            output_path,
            reconstructed,
            [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        )

        reconstructed_gray = cv2.cvtColor(reconstructed, cv2.COLOR_BGR2GRAY)

        qualities = [10, 30, 50, 70, 90]
        psnr_values = []
        ratio_values = []

        for q in qualities:
            temp_result = encode_decode_jpeg_color(original_img, quality=q)
            temp_reconstructed = temp_result["reconstructed"]
            temp_gray = cv2.cvtColor(temp_reconstructed, cv2.COLOR_BGR2GRAY)

            _, temp_psnr, _ = calculate_metrics(original_gray, temp_gray)

            temp_output_filename = f"temp_jpeg_q{q}_{name_without_ext}_{timestamp}.jpg"
            temp_output_path = os.path.join(OUTPUT_FOLDER, temp_output_filename)

            cv2.imwrite(
                temp_output_path,
                temp_reconstructed,
                [int(cv2.IMWRITE_JPEG_QUALITY), q]
            )

            temp_size_bytes = os.path.getsize(temp_output_path)

            temp_ratio = round(
                original_size_bytes / max(temp_size_bytes, 1),
                2
            )

            psnr_values.append(temp_psnr)
            ratio_values.append(temp_ratio)

            os.remove(temp_output_path)

        plot_filename = f"jpeg_quality_plot_{name_without_ext}_{timestamp}.png"
        plot_path = os.path.join(PLOT_FOLDER, plot_filename)

        generate_quality_analysis_plot(
            qualities,
            psnr_values,
            ratio_values,
            plot_path
        )

        plot_url = f"/plots/{plot_filename}"

    elif algorithm == "jpeg2000":
        factor = clamp_int(request.form.get("factor", 10), default=10, min_value=1)
        wavelet = validate_wavelet(request.form.get("wavelet", "haar"))
        level = clamp_int(request.form.get("level", 2), default=2, min_value=1, max_value=5)

        try:
            result = encode_decode_jpeg2000_color(
                original_img,
                factor=factor,
                wavelet=wavelet,
                level=level
            )
        except Exception as e:
            return jsonify({"error": f"JPEG2000 compression failed: {str(e)}"}), 500

        reconstructed = result["reconstructed"]

        output_filename = f"jpeg2000_result_{name_without_ext}_{timestamp}.jp2"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        try:
            write_jpeg2000_file(output_path, reconstructed, factor=factor)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

        preview_filename = f"preview_jpeg2000_{name_without_ext}_{timestamp}.png"
        preview_path = os.path.join(OUTPUT_FOLDER, preview_filename)
        cv2.imwrite(preview_path, reconstructed)

        reconstructed_gray = cv2.cvtColor(reconstructed, cv2.COLOR_BGR2GRAY)

        factors = [5, 10, 15, 20, 30]
        psnr_values = []
        bpp_values = []

        for f in factors:
            temp_result = encode_decode_jpeg2000_color(
                original_img,
                factor=f,
                wavelet=wavelet,
                level=level
            )

            temp_reconstructed = temp_result["reconstructed"]
            temp_gray = cv2.cvtColor(temp_reconstructed, cv2.COLOR_BGR2GRAY)

            _, temp_psnr, _ = calculate_metrics(original_gray, temp_gray)

            temp_output_filename = f"temp_jpeg2000_f{f}_{name_without_ext}_{timestamp}.jp2"
            temp_output_path = os.path.join(OUTPUT_FOLDER, temp_output_filename)

            write_jpeg2000_file(temp_output_path, temp_reconstructed, factor=f)

            temp_size_bytes = os.path.getsize(temp_output_path)
            temp_bpp = (temp_size_bytes * 8) / pixel_count

            psnr_values.append(temp_psnr)
            bpp_values.append(round(temp_bpp, 4))

            os.remove(temp_output_path)

        plot_filename = f"jpeg2000_plot_{name_without_ext}_{timestamp}.png"
        plot_path = os.path.join(PLOT_FOLDER, plot_filename)

        generate_jpeg2000_analysis_plot(
            factors,
            psnr_values,
            bpp_values,
            plot_path
        )

        plot_url = f"/plots/{plot_filename}"

    else:
        return jsonify({"error": "Unknown algorithm"}), 400

    error_filename = f"error_{algorithm}_{name_without_ext}_{timestamp}.png"
    error_path = os.path.join(PLOT_FOLDER, error_filename)

    error_map = generate_error_map(original_img, reconstructed)
    cv2.imwrite(error_path, error_map)

    error_url = f"/plots/{error_filename}"

    mse, psnr, ssim = calculate_metrics(original_gray, reconstructed_gray)

    if algorithm == "jpeg2000":
        compressed_size_bytes = result["bitstream_size_bytes"]
    else:
        compressed_size_bytes = os.path.getsize(output_path)

    if algorithm == "jpeg":
        size_type = "jpeg_output_file_size"
    else:
        size_type = "jpeg2000_huffman_bitstream_size"

    size_info = get_size_info(
        original_size_bytes,
        compressed_size_bytes,
        output_path,
        pixel_count
    )

    size_info["size_type"] = size_type

    display_filename = output_filename
    if algorithm == "jpeg2000":
        display_filename = preview_filename

    return jsonify({
        "algorithm": algorithm,
        "image_type": image_type,
        "quality": quality if algorithm == "jpeg" else "",
        "factor": result.get("factor", ""),
        "wavelet": result.get("wavelet", ""),
        "level": result.get("level", ""),
        **size_info,
        "mse": mse,
        "psnr": psnr,
        "ssim": ssim,
        "compressed_url": f"/outputs/{display_filename}",
        "download_url": f"/outputs/{output_filename}",
        "plot_url": plot_url,
        "error_url": error_url
    })


@compression_bp.route("/compare", methods=["POST"])
def compare_images():
    if "image" not in request.files:
        return jsonify({"error": "No image file uploaded"}), 400

    image = request.files["image"]

    if image.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(image.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    filename = secure_filename(image.filename)
    name_without_ext = filename.rsplit(".", 1)[0]
    timestamp = int(time.time() * 1000)

    upload_path = os.path.join(UPLOAD_FOLDER, filename)
    image.save(upload_path)

    image_type = request.form.get("image_type", "natural")

    if image_type == "biomedical":
        return jsonify({
            "error": "Comparison mode is not available for biomedical/fingerprint images. Use JPEG2000 lossless analysis mode."
        }), 400

    quality = clamp_int(request.form.get("quality", 50), default=50, min_value=1, max_value=100)
    factor = clamp_int(request.form.get("factor", 10), default=10, min_value=1)
    wavelet = validate_wavelet(request.form.get("wavelet", "haar"))
    level = clamp_int(request.form.get("level", 2), default=2, min_value=1, max_value=5)

    try:
        original_img = read_image_safe(upload_path)
        original_gray = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)
    except Exception as e:
        return jsonify({"error": f"Image could not be processed: {str(e)}"}), 500

    original_size_bytes = os.path.getsize(upload_path)
    original_size_kb = round(original_size_bytes / 1024, 2)

    height, width = original_img.shape[:2]
    pixel_count = height * width

    try:
        jpeg_result = encode_decode_jpeg_color(original_img, quality=quality)
    except Exception as e:
        return jsonify({"error": f"JPEG compression failed: {str(e)}"}), 500

    jpeg_reconstructed = jpeg_result["reconstructed"]

    jpeg_output_filename = f"compare_jpeg_{name_without_ext}_{timestamp}.jpg"
    jpeg_output_path = os.path.join(OUTPUT_FOLDER, jpeg_output_filename)

    cv2.imwrite(
        jpeg_output_path,
        jpeg_reconstructed,
        [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    )

    jpeg_gray = cv2.cvtColor(jpeg_reconstructed, cv2.COLOR_BGR2GRAY)

    jpeg_error_filename = f"error_compare_jpeg_{name_without_ext}_{timestamp}.png"
    jpeg_error_path = os.path.join(PLOT_FOLDER, jpeg_error_filename)

    jpeg_error_map = generate_error_map(original_img, jpeg_reconstructed)
    cv2.imwrite(jpeg_error_path, jpeg_error_map)

    jpeg_mse, jpeg_psnr, jpeg_ssim = calculate_metrics(original_gray, jpeg_gray)

    jpeg_size_bytes = os.path.getsize(jpeg_output_path)
    jpeg_size_kb = round(jpeg_size_bytes / 1024, 2)
    jpeg_output_size_kb = round(os.path.getsize(jpeg_output_path) / 1024, 2)
    jpeg_ratio = round(original_size_bytes / max(jpeg_size_bytes, 1), 2)
    jpeg_bpp = round((jpeg_size_bytes * 8) / pixel_count, 4)

    try:
        jpeg2000_result = encode_decode_jpeg2000_color(
            original_img,
            factor=factor,
            wavelet=wavelet,
            level=level
        )
    except Exception as e:
        return jsonify({"error": f"JPEG2000 compression failed: {str(e)}"}), 500

    jpeg2000_reconstructed = jpeg2000_result["reconstructed"]

    jpeg2000_output_filename = f"compare_jpeg2000_{name_without_ext}_{timestamp}.jp2"
    jpeg2000_output_path = os.path.join(OUTPUT_FOLDER, jpeg2000_output_filename)

    try:
        write_jpeg2000_file(jpeg2000_output_path, jpeg2000_reconstructed, factor=factor)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    jpeg2000_preview_filename = f"preview_compare_jpeg2000_{name_without_ext}_{timestamp}.png"
    jpeg2000_preview_path = os.path.join(OUTPUT_FOLDER, jpeg2000_preview_filename)
    cv2.imwrite(jpeg2000_preview_path, jpeg2000_reconstructed)

    jpeg2000_gray = cv2.cvtColor(jpeg2000_reconstructed, cv2.COLOR_BGR2GRAY)

    jpeg2000_error_filename = f"error_compare_jpeg2000_{name_without_ext}_{timestamp}.png"
    jpeg2000_error_path = os.path.join(PLOT_FOLDER, jpeg2000_error_filename)

    jpeg2000_error_map = generate_error_map(original_img, jpeg2000_reconstructed)
    cv2.imwrite(jpeg2000_error_path, jpeg2000_error_map)

    jpeg2000_mse, jpeg2000_psnr, jpeg2000_ssim = calculate_metrics(
        original_gray,
        jpeg2000_gray
    )

    jpeg2000_size_bytes = jpeg2000_result["bitstream_size_bytes"]
    jpeg2000_size_kb = round(jpeg2000_size_bytes / 1024, 2)
    jpeg2000_output_size_kb = round(os.path.getsize(jpeg2000_output_path) / 1024, 2)
    jpeg2000_ratio = round(original_size_bytes / max(jpeg2000_size_bytes, 1), 2)
    jpeg2000_bpp = round((jpeg2000_size_bytes * 8) / pixel_count, 4)

    labels = ["JPEG", "JPEG2000"]
    psnr_values = [jpeg_psnr, jpeg2000_psnr]
    ratio_values = [jpeg_ratio, jpeg2000_ratio]

    plot_filename = f"comparison_plot_{name_without_ext}_{timestamp}.png"
    plot_path = os.path.join(PLOT_FOLDER, plot_filename)

    generate_comparison_plot(
        labels,
        psnr_values,
        ratio_values,
        plot_path
    )

    return jsonify({
        "mode": "comparison",
        "image_type": image_type,
        "plot_url": f"/plots/{plot_filename}",

        "jpeg": {
            "algorithm": "jpeg",
            "quality": quality,
            "original_size_kb": original_size_kb,
            "compressed_size_kb": jpeg_size_kb,
            "output_file_size_kb": jpeg_output_size_kb,
            "compression_ratio": jpeg_ratio,
            "bpp": jpeg_bpp,
            "mse": jpeg_mse,
            "psnr": jpeg_psnr,
            "ssim": jpeg_ssim,
            "compressed_url": f"/outputs/{jpeg_output_filename}",
            "error_url": f"/plots/{jpeg_error_filename}",
            "size_type": "jpeg_output_file_size"
        },

        "jpeg2000": {
            "algorithm": "jpeg2000",
            "factor": factor,
            "wavelet": wavelet,
            "level": level,
            "original_size_kb": original_size_kb,
            "compressed_size_kb": jpeg2000_size_kb,
            "output_file_size_kb": jpeg2000_output_size_kb,
            "compression_ratio": jpeg2000_ratio,
            "bpp": jpeg2000_bpp,
            "mse": jpeg2000_mse,
            "psnr": jpeg2000_psnr,
            "ssim": jpeg2000_ssim,
            "compressed_url": f"/outputs/{jpeg2000_preview_filename}",
            "download_url": f"/outputs/{jpeg2000_output_filename}",
            "error_url": f"/plots/{jpeg2000_error_filename}",
            "size_type": "jpeg2000_huffman_bitstream_size"
        }
    })
