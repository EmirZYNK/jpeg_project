import matplotlib
# BU SATIR ÇOK ÖNEMLİ: Grafik penceresi açılmasını engeller (Non-interactive backend)
matplotlib.use('Agg') 

import matplotlib.pyplot as plt
import io
import base64

def generate_comparison_plot(ratios, psnr_values_jpeg, psnr_values_jpeg2000):
    """Hocanın en çok bakacağı grafik: Sıkıştırma vs Kalite Karşılaştırması"""
    
    # Her seferinde yeni bir figür oluşturduğumuzdan emin olalım
    plt.clf() 
    fig = plt.figure(figsize=(10, 5))
    
    plt.plot(ratios, psnr_values_jpeg, label='JPEG (DCT)', marker='o', color='#89b4fa')
    plt.plot(ratios, psnr_values_jpeg2000, label='JPEG2000 (DWT)', marker='s', color='#a6e3a1')
    
    plt.xlabel('Sıkıştırma Oranı (%)')
    plt.ylabel('PSNR (dB) - Kalite')
    plt.title('JPEG vs JPEG2000: Performans Karşılaştırması')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Grafiği belleğe kaydet
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    
    # Figürü kapat (Bellek sızıntısını ve C++ hatalarını önler)
    plt.close(fig)
    
    return base64.b64encode(img.getvalue()).decode()