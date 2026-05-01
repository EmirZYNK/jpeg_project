import numpy as np
from skimage.metrics import peak_signal_noise_ratio as psnr_metric
from skimage.metrics import structural_similarity as ssim_metric
from skimage.metrics import mean_squared_error as mse_metric

def calculate_metrics(original_np, compressed_np):
    """
    İki görüntü arasındaki kalite farkını MSE, PSNR ve SSIM ile hesaplar.
    """
    # MSE: Mean Squared Error (Düşük olması daha iyidir)
    # Pikseller arasındaki ortalama hata karesini ölçer.
    mse_val = mse_metric(original_np, compressed_np)
    
    # PSNR: Peak Signal-to-Noise Ratio (Yüksek olması daha iyidir)
    # Genelde 30 dB üstü insan gözü için 'iyi' kabul edilir.
    psnr_val = psnr_metric(original_np, compressed_np)
    
    # SSIM: Structural Similarity Index (1.0'a yakın olması daha iyidir)
    # Görüntünün dokusunu ve yapısını ne kadar koruduğunu ölçer.
    ssim_val = ssim_metric(original_np, compressed_np, channel_axis=2)
    
    # Değerleri yuvarlayarak döndür: MSE, PSNR, SSIM
    return round(mse_val, 2), round(psnr_val, 2), round(ssim_val, 4)