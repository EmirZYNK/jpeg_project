import numpy as np
from skimage.metrics import mean_squared_error, peak_signal_noise_ratio, structural_similarity


def calculate_metrics(original, reconstructed):
    if original.shape != reconstructed.shape:
        raise ValueError("Original and reconstructed images must have the same shape")

    mse = mean_squared_error(original, reconstructed)

    if mse == 0:
        psnr = 100.0
    else:
        psnr = peak_signal_noise_ratio(original, reconstructed, data_range=255)

    ssim = structural_similarity(original, reconstructed, data_range=255)

    return round(mse, 2), round(psnr, 2), round(ssim, 4)