import matplotlib
matplotlib.use('Agg') # Sunucu tarafında (Flask/Django vb.) hata almamak için

import matplotlib.pyplot as plt
import io
import base64

def generate_comparison_plot(bpp_values, psnr_values_jpeg, psnr_values_jpeg2000):
    """
    Gerçek Rate-Distortion (Kalite - BPP) Eğrisi Çizer.
    Akademik standartlarda (IEEE) X ekseni her zaman Bitrate (BPP) olarak verilir.
    """
    
    plt.clf() 
    # Koyu tema (Modern ve frontend ile uyumlu)
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor('#1e1e2e')
    ax.set_facecolor('#1e1e2e')
    
    # Gerçek verileri çiz (X ekseni: BPP, Y ekseni: PSNR)
    ax.plot(bpp_values, psnr_values_jpeg, label='JPEG (DCT)', marker='o', color='#89b4fa', linewidth=2, markersize=8)
    ax.plot(bpp_values, psnr_values_jpeg2000, label='JPEG 2000 (DWT)', marker='s', color='#a6e3a1', linewidth=2, markersize=8)
    
    # Eksen ve Başlık Ayarları (Akademik Terminolojiye Güncellendi)
    ax.set_xlabel('Bitrate: BPP (Bits Per Pixel)', fontsize=12, color='#cdd6f4')
    ax.set_ylabel('Reconstruction Quality (PSNR - dB)', fontsize=12, color='#cdd6f4')
    ax.set_title('JPEG vs JPEG 2000: Rate-Distortion (R-D) Curve', fontsize=14, color='#f5e0dc', pad=15)
    
    # Izgara ve Eksen renkleri
    ax.grid(True, linestyle='--', alpha=0.3, color='#585b70')
    ax.tick_params(colors='#a6adc8')
    for spine in ax.spines.values():
        spine.set_color('#585b70')
    
    # Legend (Açıklama tablosu)
    legend = ax.legend(facecolor='#313244', edgecolor='#585b70')
    for text in legend.get_texts():
        text.set_color('#cdd6f4')
    
    plt.tight_layout()
    
    # Grafiği base64 olarak belleğe al (Frontend'de göstermek için)
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', dpi=100)
    img.seek(0)
    plt.close(fig)
    
    return base64.b64encode(img.getvalue()).decode()