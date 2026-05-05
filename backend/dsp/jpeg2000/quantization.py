import numpy as np


def get_subband_scale(base_factor, level_index, is_approximation=False):
    base_factor = max(1, int(base_factor))

    if is_approximation:
        return max(1, base_factor * 0.5)

    return base_factor * (1.0 + level_index * 0.6)


def quantize_coeffs(coeffs, factor=10):
    quantized = []

    for idx, c in enumerate(coeffs):
        if isinstance(c, tuple):
            scale = get_subband_scale(
                factor,
                level_index=idx,
                is_approximation=False
            )

            quantized.append(
                tuple(np.round(sub / scale) for sub in c)
            )
        else:
            scale = get_subband_scale(
                factor,
                level_index=idx,
                is_approximation=True
            )

            quantized.append(np.round(c / scale))

    return quantized


def dequantize_coeffs(quantized_coeffs, factor=10):
    dequantized = []

    for idx, c in enumerate(quantized_coeffs):
        if isinstance(c, tuple):
            scale = get_subband_scale(
                factor,
                level_index=idx,
                is_approximation=False
            )

            dequantized.append(
                tuple(sub * scale for sub in c)
            )
        else:
            scale = get_subband_scale(
                factor,
                level_index=idx,
                is_approximation=True
            )

            dequantized.append(c * scale)

    return dequantized


def count_nonzero_coeffs(coeffs):
    count = 0

    for c in coeffs:
        if isinstance(c, tuple):
            for sub in c:
                count += np.count_nonzero(sub)
        else:
            count += np.count_nonzero(c)

    return count