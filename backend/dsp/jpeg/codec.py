import numpy as np
import cv2

from dsp.jpeg.dct import blockwise_dct
from dsp.jpeg.quantization import blockwise_quantization, blockwise_dequantization
from dsp.jpeg.zigzag import zigzag_scan, inverse_zigzag
from dsp.jpeg.rle import rle_encode, rle_decode
from dsp.decoder.inverse_dct import blockwise_idct
from dsp.preprocessing.color_space import (
    bgr_to_ycrcb,
    ycrcb_to_bgr,
    split_channels,
    merge_channels
)


def to_uint8(image):
    return np.clip(image, 0, 255).astype(np.uint8)


def downsample_420(channel):
    h, w = channel.shape

    if h % 2 != 0:
        channel = np.vstack([channel, channel[-1:, :]])

    if w % 2 != 0:
        channel = np.hstack([channel, channel[:, -1:]])

    h_even, w_even = channel.shape
    channel = channel.astype(np.float32)

    return channel.reshape(
        h_even // 2, 2,
        w_even // 2, 2
    ).mean(axis=(1, 3))


def upsample_420(channel, target_shape):
    target_h, target_w = target_shape

    upsampled = channel.repeat(2, axis=0).repeat(2, axis=1)

    if upsampled.shape[0] < target_h or upsampled.shape[1] < target_w:
        upsampled = cv2.resize(
            upsampled,
            (target_w, target_h),
            interpolation=cv2.INTER_LINEAR
        )

    return upsampled[:target_h, :target_w]


def encode_decode_jpeg_gray(image_gray, quality=50, channel_type="luma"):
    image_gray = to_uint8(image_gray)

    dct_channel, original_h, original_w = blockwise_dct(image_gray)

    quantized = blockwise_quantization(
        dct_channel,
        quality=quality,
        channel_type=channel_type
    )

    h, w = quantized.shape
    reconstructed_quantized = np.zeros_like(quantized, dtype=np.float32)

    total_rle_symbols = 0

    for i in range(0, h, 8):
        for j in range(0, w, 8):
            block = quantized[i:i+8, j:j+8]

            zigzag = zigzag_scan(block)
            encoded = rle_encode(zigzag)
            total_rle_symbols += len(encoded)

            decoded = rle_decode(encoded)
            restored_block = inverse_zigzag(decoded)

            reconstructed_quantized[i:i+8, j:j+8] = restored_block

    dequantized = blockwise_dequantization(
        reconstructed_quantized,
        quality=quality,
        channel_type=channel_type
    )

    reconstructed = blockwise_idct(
        dequantized,
        original_h=original_h,
        original_w=original_w
    )

    return {
        "reconstructed": to_uint8(reconstructed),
        "dct": dct_channel,
        "quantized": quantized,
        "rle_symbols": total_rle_symbols,
        "estimated_size_bytes": int(max(1, total_rle_symbols * 0.5))
    }


def encode_decode_jpeg_color(image_bgr, quality=50):
    image_bgr = to_uint8(image_bgr)

    ycrcb = bgr_to_ycrcb(image_bgr)
    y, cr, cb = split_channels(ycrcb)

    cr_down = downsample_420(cr)
    cb_down = downsample_420(cb)

    y_result = encode_decode_jpeg_gray(
        y,
        quality=quality,
        channel_type="luma"
    )

    cr_result = encode_decode_jpeg_gray(
        cr_down,
        quality=quality,
        channel_type="chroma"
    )

    cb_result = encode_decode_jpeg_gray(
        cb_down,
        quality=quality,
        channel_type="chroma"
    )

    reconstructed_y = to_uint8(y_result["reconstructed"])

    reconstructed_cr = upsample_420(
        cr_result["reconstructed"],
        reconstructed_y.shape
    )

    reconstructed_cb = upsample_420(
        cb_result["reconstructed"],
        reconstructed_y.shape
    )

    reconstructed_cr = to_uint8(reconstructed_cr)
    reconstructed_cb = to_uint8(reconstructed_cb)

    if reconstructed_cr.shape != reconstructed_y.shape:
        reconstructed_cr = cv2.resize(
            reconstructed_cr,
            (reconstructed_y.shape[1], reconstructed_y.shape[0]),
            interpolation=cv2.INTER_LINEAR
        )

    if reconstructed_cb.shape != reconstructed_y.shape:
        reconstructed_cb = cv2.resize(
            reconstructed_cb,
            (reconstructed_y.shape[1], reconstructed_y.shape[0]),
            interpolation=cv2.INTER_LINEAR
        )

    merged_ycrcb = merge_channels(
        reconstructed_y,
        reconstructed_cr,
        reconstructed_cb
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
        "rle_symbols": (
            y_result["rle_symbols"]
            + cr_result["rle_symbols"]
            + cb_result["rle_symbols"]
        ),
        "dct": y_result["dct"],
        "quantized": y_result["quantized"]
    }