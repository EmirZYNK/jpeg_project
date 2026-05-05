import numpy as np

Q_Y = np.array([
    [16, 11, 10, 16, 24, 40, 51, 61],
    [12, 12, 14, 19, 26, 58, 60, 55],
    [14, 13, 16, 24, 40, 57, 69, 56],
    [14, 17, 22, 29, 51, 87, 80, 62],
    [18, 22, 37, 56, 68, 109, 103, 77],
    [24, 35, 55, 64, 81, 104, 113, 92],
    [49, 64, 78, 87, 103, 121, 120, 101],
    [72, 92, 95, 98, 112, 100, 103, 99]
], dtype=np.float32)

Q_C = np.array([
    [17, 18, 24, 47, 99, 99, 99, 99],
    [18, 21, 26, 66, 99, 99, 99, 99],
    [24, 26, 56, 99, 99, 99, 99, 99],
    [47, 66, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99]
], dtype=np.float32)


def get_scale_factor(quality):
    quality = max(1, min(100, int(quality)))

    if quality < 50:
        scale = 5000 / quality
    else:
        scale = 200 - quality * 2

    return scale / 100.0


def get_bit_allocation_matrix():
    return np.array([
        [1.0, 1.0, 1.0, 1.2, 1.4, 1.8, 2.2, 2.6],
        [1.0, 1.0, 1.2, 1.4, 1.8, 2.2, 2.6, 3.0],
        [1.0, 1.2, 1.4, 1.8, 2.2, 2.6, 3.0, 3.4],
        [1.2, 1.4, 1.8, 2.2, 2.6, 3.0, 3.4, 3.8],
        [1.4, 1.8, 2.2, 2.6, 3.0, 3.4, 3.8, 4.2],
        [1.8, 2.2, 2.6, 3.0, 3.4, 3.8, 4.2, 4.6],
        [2.2, 2.6, 3.0, 3.4, 3.8, 4.2, 4.6, 5.0],
        [2.6, 3.0, 3.4, 3.8, 4.2, 4.6, 5.0, 5.4]
    ], dtype=np.float32)


def get_quantization_matrix(quality=50, channel_type="luma"):
    scale = get_scale_factor(quality)
    base_matrix = Q_C if channel_type == "chroma" else Q_Y
    bit_allocation = get_bit_allocation_matrix()

    q_matrix = base_matrix * scale * bit_allocation
    return np.maximum(q_matrix, 1)


def blockwise_quantization(dct_channel, quality=50, channel_type="luma"):
    q_matrix = get_quantization_matrix(quality, channel_type)

    h, w = dct_channel.shape
    quantized = np.zeros_like(dct_channel, dtype=np.float32)

    for i in range(0, h, 8):
        for j in range(0, w, 8):
            block = dct_channel[i:i+8, j:j+8]
            quantized[i:i+8, j:j+8] = np.round(block / q_matrix)

    return quantized


def blockwise_dequantization(quantized_channel, quality=50, channel_type="luma"):
    q_matrix = get_quantization_matrix(quality, channel_type)

    h, w = quantized_channel.shape
    dequantized = np.zeros_like(quantized_channel, dtype=np.float32)

    for i in range(0, h, 8):
        for j in range(0, w, 8):
            block = quantized_channel[i:i+8, j:j+8]
            dequantized[i:i+8, j:j+8] = block * q_matrix

    return dequantized