"""
dsp/evaluation/metrics.py

CENG 384 - Signal Processing
Görüntü kalite metrikleri: MSE ve PSNR hesaplama modülü.
Normalize edilmiş (0.0 – 1.0 aralığında) float32 tipinde
512×512 NumPy array'leri üzerinde çalışır.
"""

import numpy as np


def calculate_mse(original: np.ndarray, decoded: np.ndarray) -> float:
    """
    İki görüntü matrisi arasındaki Mean Squared Error (MSE) değerini hesaplar.

    Formül:
        MSE = (1 / N) * Σ (original_i - decoded_i)²

    Parameters
    ----------
    original : np.ndarray
        Orijinal görüntü – float32, 512×512.
    decoded : np.ndarray
        Decode edilmiş görüntü – float32, 512×512.

    Returns
    -------
    float
        MSE değeri (JSON serileştirmeye uygun saf Python float).
    """
    mse = np.mean((original - decoded) ** 2)
    return float(mse)


def calculate_psnr(original: np.ndarray, decoded: np.ndarray) -> float:
    """
    İki görüntü matrisi arasındaki Peak Signal-to-Noise Ratio (PSNR) değerini hesaplar.

    Normalize edilmiş görüntüler için MAX_I = 1.0 kabul edilir.

    Formül:
        PSNR = 10 · log₁₀(1.0² / MSE)

    MSE sıfır ise (mükemmel yeniden oluşturma) numpy.inf döndürülür.

    Parameters
    ----------
    original : np.ndarray
        Orijinal görüntü – float32, 512×512.
    decoded : np.ndarray
        Decode edilmiş görüntü – float32, 512×512.

    Returns
    -------
    float
        PSNR değeri (dB cinsinden, JSON serileştirmeye uygun saf Python float).
        Mükemmel eşleşmede numpy.inf döner.
    """
    mse = calculate_mse(original, decoded)

    if mse == 0.0:
        return float(np.inf)

    psnr = 10.0 * np.log10(1.0 / mse)
    return float(psnr)


if __name__ == "__main__":
    # ---------- Test Bloğu ----------
    rng = np.random.default_rng(seed=42)

    # 512×512 boyutunda normalize float32 test görüntüleri
    original = rng.random((512, 512), dtype=np.float32)
    decoded = rng.random((512, 512), dtype=np.float32)

    mse_val = calculate_mse(original, decoded)
    psnr_val = calculate_psnr(original, decoded)

    print("=" * 45)
    print("  CENG 384 – Görüntü Kalite Metrikleri Testi")
    print("=" * 45)
    print(f"  Görüntü boyutu : 512 × 512")
    print(f"  MSE             : {mse_val:.6f}")
    print(f"  PSNR            : {psnr_val:.2f} dB")
    print(f"  MSE tipi        : {type(mse_val).__name__}")
    print(f"  PSNR tipi       : {type(psnr_val).__name__}")
    print("-" * 45)

    # Mükemmel eşleşme testi (MSE == 0 → PSNR == inf)
    identical = original.copy()
    mse_zero = calculate_mse(original, identical)
    psnr_inf = calculate_psnr(original, identical)

    print("  Mükemmel Eşleşme Testi")
    print(f"  MSE  : {mse_zero}")
    print(f"  PSNR : {psnr_inf}")
    print("=" * 45)
