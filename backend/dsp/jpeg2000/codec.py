import numpy as np

from dsp.jpeg2000.dwt import apply_dwt_2d, apply_idwt_2d
from dsp.jpeg2000.quantization import (
    quantize_coeffs,
    dequantize_coeffs,
    count_nonzero_coeffs
)
from dsp.preprocessing.color_space import (
    bgr_to_ycrcb,
    ycrcb_to_bgr,
    split_channels,
    merge_channels
)


def to_uint8(image):
    return np.clip(np.round(image), 0, 255).astype(np.uint8)


def estimate_jpeg2000_size(nonzero_count, total_pixels, factor):
    factor = max(1, int(factor))

    entropy_factor = 0.28
    compression_factor = 10 / factor

    estimated = nonzero_count * entropy_factor * compression_factor

    min_size = total_pixels * 0.03

    return int(max(1, min(estimated, total_pixels, max(estimated, min_size))))


def encode_decode_jpeg2000_gray(image_gray, factor=10, wavelet="haar", level=2):
    factor = max(1, int(factor))
    level = max(1, int(level))

    coeffs = apply_dwt_2d(
        image_gray,
        wavelet=wavelet,
        level=level
    )

    quantized = quantize_coeffs(coeffs, factor=factor)
    dequantized = dequantize_coeffs(quantized, factor=factor)

    reconstructed = apply_idwt_2d(
        dequantized,
        wavelet=wavelet,
        original_shape=image_gray.shape
    )

    reconstructed = to_uint8(reconstructed)

    nonzero_count = count_nonzero_coeffs(quantized)
    total_pixels = image_gray.shape[0] * image_gray.shape[1]

    estimated_size_bytes = estimate_jpeg2000_size(
        nonzero_count,
        total_pixels,
        factor
    )

    return {
        "reconstructed": reconstructed,
        "estimated_size_bytes": estimated_size_bytes,
        "nonzero_coeffs": nonzero_count,
        "wavelet": wavelet,
        "level": level,
        "factor": factor
    }


def encode_decode_jpeg2000_color(image_bgr, factor=10, wavelet="haar", level=2):
    ycrcb = bgr_to_ycrcb(image_bgr)
    y, cr, cb = split_channels(ycrcb)

    y_result = encode_decode_jpeg2000_gray(
        y,
        factor=factor,
        wavelet=wavelet,
        level=level
    )

    cr_result = encode_decode_jpeg2000_gray(
        cr,
        factor=factor,
        wavelet=wavelet,
        level=level
    )

    cb_result = encode_decode_jpeg2000_gray(
        cb,
        factor=factor,
        wavelet=wavelet,
        level=level
    )

    merged_ycrcb = merge_channels(
        y_result["reconstructed"],
        cr_result["reconstructed"],
        cb_result["reconstructed"]
    )

    reconstructed_bgr = ycrcb_to_bgr(merged_ycrcb)

    estimated_size_bytes = (
        y_result["estimated_size_bytes"]
        + cr_result["estimated_size_bytes"]
        + cb_result["estimated_size_bytes"]
    )

    return {
        "reconstructed": to_uint8(reconstructed_bgr),
        "estimated_size_bytes": estimated_size_bytes,
        "nonzero_coeffs": (
            y_result["nonzero_coeffs"]
            + cr_result["nonzero_coeffs"]
            + cb_result["nonzero_coeffs"]
        ),
        "wavelet": wavelet,
        "level": level,
        "factor": factor
    }


def encode_decode_jpeg2000_lossless_gray(image_gray, wavelet="haar", level=2):
    level = max(1, int(level))

    coeffs = apply_dwt_2d(
        image_gray,
        wavelet=wavelet,
        level=level
    )

    reconstructed = apply_idwt_2d(
        coeffs,
        wavelet=wavelet,
        original_shape=image_gray.shape
    )

    reconstructed = to_uint8(reconstructed)

    nonzero_count = count_nonzero_coeffs(coeffs)

    return {
        "reconstructed": reconstructed,
        "estimated_size_bytes": image_gray.nbytes,
        "nonzero_coeffs": nonzero_count,
        "wavelet": wavelet,
        "level": level,
        "factor": "lossless"
    }


def encode_decode_jpeg2000_lossless_color(image_bgr, wavelet="haar", level=2):
    ycrcb = bgr_to_ycrcb(image_bgr)
    y, cr, cb = split_channels(ycrcb)

    y_result = encode_decode_jpeg2000_lossless_gray(
        y,
        wavelet=wavelet,
        level=level
    )

    cr_result = encode_decode_jpeg2000_lossless_gray(
        cr,
        wavelet=wavelet,
        level=level
    )

    cb_result = encode_decode_jpeg2000_lossless_gray(
        cb,
        wavelet=wavelet,
        level=level
    )

    merged_ycrcb = merge_channels(
        y_result["reconstructed"],
        cr_result["reconstructed"],
        cb_result["reconstructed"]
    )

    reconstructed_bgr = ycrcb_to_bgr(merged_ycrcb)

    return {
        "reconstructed": to_uint8(reconstructed_bgr),
        "estimated_size_bytes": image_bgr.nbytes,
        "nonzero_coeffs": (
            y_result["nonzero_coeffs"]
            + cr_result["nonzero_coeffs"]
            + cb_result["nonzero_coeffs"]
        ),
        "wavelet": wavelet,
        "level": level,
        "factor": "lossless"
    }