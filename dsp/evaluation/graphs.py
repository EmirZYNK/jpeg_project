import matplotlib
matplotlib.use('Agg') # Sunucu tarafında hata almamak için

import matplotlib.pyplot as plt
import io
import base64
import numpy as np

def generate_histogram(original_np, comp1_np, name1, comp2_np=None, name2=None):
    """
    Orijinal ve sıkıştırılmış görüntülerin gerçek piksel değerlerinin (0-255) 
    dağılımını gösteren Histogram çizer. Gerçek piksel sayılarını baz alır.
    """
    plt.clf() 
    # Koyu tema (Modern ve frontend ile uyumlu Catppuccin)
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor('#1e1e2e')
    ax.set_facecolor('#1e1e2e')
    
    # Histogramın doğru okunması için RGB görüntüyü Gri Tonlamaya (Luminance) çevirme
    def to_gray(img_array):
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            # Standart parlaklık (luminance) formülü
            return np.dot(img_array[...,:3], [0.2989, 0.5870, 0.1140]).flatten()
        return img_array.flatten()
        
    orig_flat = to_gray(original_np)
    comp1_flat = to_gray(comp1_np)
    
    # Orijinal görüntüyü arka planda silik ve dolu (fill) olarak çiz
    ax.hist(orig_flat, bins=256, range=(0, 256), color='#cdd6f4', alpha=0.3, label='Orijinal Resim', density=False)
    
    # Sıkıştırılmış görüntüyü (Sol taraf / Analiz) çizgi olarak çiz
    color1 = '#89b4fa' if name1 == 'JPEG' else '#a6e3a1'
    ax.hist(comp1_flat, bins=256, range=(0, 256), color=color1, alpha=0.9, histtype='step', linewidth=2, label=name1, density=False)
    
    # Karşılaştırma modundaysak 2. sıkıştırılmış görüntüyü (Sağ taraf) çiz
    if comp2_np is not None and name2 is not None:
        comp2_flat = to_gray(comp2_np)
        color2 = '#a6e3a1' if name2 == 'JPEG 2000' else '#f38ba8'
        ax.hist(comp2_flat, bins=256, range=(0, 256), color=color2, alpha=0.9, histtype='step', linewidth=2, label=name2, density=False)
        
    # Eksen ve Başlık Ayarları (Gerçek Değerler)
    ax.set_xlabel('Piksel Yoğunluğu (0 - 255)', fontsize=12, color='#cdd6f4')
    ax.set_ylabel('Piksel Sayısı (Gerçek Frekans)', fontsize=12, color='#cdd6f4')
    ax.set_title('Orijinal vs Sıkıştırılmış: Piksel Yoğunluğu Histogramı', fontsize=14, color='#f5e0dc', pad=15)
    
    # Izgara ve Eksen renkleri
    ax.grid(True, linestyle='--', alpha=0.2, color='#585b70')
    ax.tick_params(colors='#a6adc8')
    for spine in ax.spines.values():
        spine.set_color('#585b70')
    
    # Legend (Açıklama tablosu)
    legend = ax.legend(facecolor='#313244', edgecolor='#585b70')
    for text in legend.get_texts():
        text.set_color('#cdd6f4')
    
    plt.tight_layout()
    
    # Grafiği base64 olarak belleğe al
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', dpi=100)
    img.seek(0)
    plt.close(fig)
    
    return base64.b64encode(img.getvalue()).decode()

def generate_error_map(original_np, comp_np):
    """
    Orijinal ve sıkıştırılmış görüntü arasındaki mutlak farkı
    hesaplayıp ısı haritası (error map) olarak döndürür.
    """
    plt.clf()
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor('#1e1e2e')
    
    # Boyutları eşitleyelim (kırpma varsa)
    min_y = min(original_np.shape[0], comp_np.shape[0])
    min_x = min(original_np.shape[1], comp_np.shape[1])
    orig = original_np[:min_y, :min_x].astype(np.float32)
    comp = comp_np[:min_y, :min_x].astype(np.float32)
    
    if len(orig.shape) == 3:
        orig = np.mean(orig, axis=2)
        comp = np.mean(comp, axis=2)
        
    diff = np.abs(orig - comp)
    
    im = ax.imshow(diff, cmap='jet')
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title('Hata Haritası (Mutlak Fark)', color='#f5e0dc', pad=15)
    ax.axis('off')
    
    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', dpi=100)
    img.seek(0)
    plt.close(fig)
    return base64.b64encode(img.getvalue()).decode()

import pywt
def generate_subband_grid(coeffs):
    """
    DWT alt bantlarını (LL, HL, LH, HH) görselleştirip base64 döner.
    """
    plt.clf()
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor('#1e1e2e')
    
    arr, _ = pywt.coeffs_to_array(coeffs)
    
    # Kapsamı daraltarak detayları görünür kılalım (log scale)
    arr = np.abs(arr)
    arr = np.log1p(arr)
    
    ax.imshow(arr, cmap='gray')
    ax.set_title('DWT Katmanları (Subbands)', color='#f5e0dc', pad=15)
    ax.axis('off')
    
    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', dpi=100)
    img.seek(0)
    plt.close(fig)
    return base64.b64encode(img.getvalue()).decode()