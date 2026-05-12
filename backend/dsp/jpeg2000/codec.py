import numpy as np

from dsp.jpeg2000.entropy import (
    encode_coefficients_to_bitstream,
    decode_coefficients_from_bitstream
)
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


def encode_decode_jpeg2000_gray(image_gray, factor=10, wavelet="haar", level=2):
    factor = max(1, int(factor))
    level = max(1, int(level))

    coeffs = apply_dwt_2d(
        image_gray,
        wavelet=wavelet,
        level=level
    )

    quantized = quantize_coeffs(coeffs, factor=factor)

    bitstream = encode_coefficients_to_bitstream(
        quantized,
        lossless=False
    )

    bitstream_size_bytes = len(bitstream)

    decoded_quantized = decode_coefficients_from_bitstream(bitstream)

    dequantized = dequantize_coeffs(
        decoded_quantized,
        factor=factor
    )

    reconstructed = apply_idwt_2d(
        dequantized,
        wavelet=wavelet,
        original_shape=image_gray.shape
    )

    reconstructed = to_uint8(reconstructed)

    nonzero_count = count_nonzero_coeffs(decoded_quantized)

    return {
        "reconstructed": reconstructed,
        "bitstream_size_bytes": bitstream_size_bytes,
        "estimated_size_bytes": bitstream_size_bytes,
        "nonzero_coeffs": nonzero_count,
        "wavelet": wavelet,
        "level": level,
        "factor": factor
    }


def encode_decode_jpeg2000_color(image_bgr, factor=10, wavelet="haar", level=2):
    factor = max(1, int(factor))
    level = max(1, int(level))

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
    reconstructed_bgr = to_uint8(reconstructed_bgr)

    bitstream_size_bytes = (
        y_result["bitstream_size_bytes"]
        + cr_result["bitstream_size_bytes"]
        + cb_result["bitstream_size_bytes"]
    )

    nonzero_coeffs = (
        y_result["nonzero_coeffs"]
        + cr_result["nonzero_coeffs"]
        + cb_result["nonzero_coeffs"]
    )

    return {
        "reconstructed": reconstructed_bgr,
        "bitstream_size_bytes": bitstream_size_bytes,
        "estimated_size_bytes": bitstream_size_bytes,
        "nonzero_coeffs": nonzero_coeffs,
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

    bitstream = encode_coefficients_to_bitstream(
        coeffs,
        lossless=True
    )

    bitstream_size_bytes = len(bitstream)

    decoded_coeffs = decode_coefficients_from_bitstream(bitstream)

    reconstructed = apply_idwt_2d(
        decoded_coeffs,
        wavelet=wavelet,
        original_shape=image_gray.shape
    )

    reconstructed = to_uint8(reconstructed)

    nonzero_count = count_nonzero_coeffs(decoded_coeffs)

    return {
        "reconstructed": reconstructed,
        "bitstream_size_bytes": bitstream_size_bytes,
        "estimated_size_bytes": bitstream_size_bytes,
        "nonzero_coeffs": nonzero_count,
        "wavelet": wavelet,
        "level": level,
        "factor": "lossless"
    }


def encode_decode_jpeg2000_lossless_color(image_bgr, wavelet="haar", level=2):
    level = max(1, int(level))

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
    reconstructed_bgr = to_uint8(reconstructed_bgr)

    bitstream_size_bytes = (
        y_result["bitstream_size_bytes"]
        + cr_result["bitstream_size_bytes"]
        + cb_result["bitstream_size_bytes"]
    )

    nonzero_coeffs = (
        y_result["nonzero_coeffs"]
        + cr_result["nonzero_coeffs"]
        + cb_result["nonzero_coeffs"]
    )

    return {
        "reconstructed": reconstructed_bgr,
        "bitstream_size_bytes": bitstream_size_bytes,
        "estimated_size_bytes": bitstream_size_bytes,
        "nonzero_coeffs": nonzero_coeffs,
        "wavelet": wavelet,
        "level": level,
        "factor": "lossless"
    }