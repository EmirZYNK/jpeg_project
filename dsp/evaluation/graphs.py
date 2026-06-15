import matplotlib
matplotlib.use('Agg') # Sunucu tarafında hata almamak için

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import io
import base64
import numpy as np
import pywt

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

def generate_subband_grid(coeffs):
    """
    DWT alt bantlarını (LL, HL, LH, HH) hiyerarşik bir piramit yapısında görselleştirir.
    Boşlukları (gaps) tamamen sıfırlar, her çözünürlük seviyesine (grubuna) farklı renkte 
    kalın çerçeveler ekler ve sol üst köşelerine ilgili bandın adını (LL, LH, HL, HH) yazar.
    """
    plt.clf()
    plt.style.use('dark_background')
    
    # 7x7 inçlik kare bir figür oluşturuyoruz
    fig = plt.figure(figsize=(7, 7))
    fig.patch.set_facecolor('#1e1e2e')
    
    # Canlı ve modern renk paleti (Catppuccin & ImgPress temasıyla tam uyumlu)
    color_palette = [
        '#ff7e5f',  # Canlı Turuncu (LL bandı için)
        '#89b4fa',  # Açık Mavi (Level 1 - En dıştaki detaylar)
        '#a6e3a1',  # Pastel Yeşil (Level 2)
        '#f9e2af',  # Yumuşak Sarı (Level 3)
        '#cba6f7',  # Açık Mor (Level 4)
        '#f38ba8',  # Pastel Kırmızı (Level 5)
    ]
    
    # Ana GridSpec: Tüm figürü sınır çizgilerine kadar sıfır boşlukla kaplar
    main_gs = gridspec.GridSpec(1, 1, figure=fig, left=0.01, right=0.99, bottom=0.01, top=0.99)
    
    def plot_subband(ax, data, label, color):
        # Katsayı detaylarını görünür kılmak için logaritmik ölçekleme uyguluyoruz
        data_vis = np.abs(data)
        data_vis = np.log1p(data_vis)
        
        # aspect='auto' piksel boşluklarını engellemek için resmi hücreye tam yayar
        ax.imshow(data_vis, cmap='gray', aspect='auto')
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Belirgin ve kalın renkli çerçeveler (çözünürlük grupları için)
        for spine in ax.spines.values():
            spine.set_edgecolor(color)
            spine.set_linewidth(2.5)  # Kalınlık seviyesi artırıldı
            spine.set_visible(True)
            
        # Sol üst köşeye etiket yazdır (Açık tonlu arka planlarda yazıyı koyu yapar)
        text_color = '#11111b' if color in ['#f9e2af', '#a6e3a1'] else '#ffffff'
        ax.text(0.04, 0.96, label, transform=ax.transAxes,
                color=text_color, fontsize=9.5, fontweight='bold',
                verticalalignment='top', horizontalalignment='left',
                bbox=dict(facecolor=color, alpha=0.9, edgecolor='none', boxstyle='round,pad=0.25'))

    def draw_dwt_grid(gs_spec, idx):
        # idx: katsayı listesindeki derinlik indeksi (N'den 1'e doğru gider)
        # Sıkı bir 2x2 grid oluşturuyoruz (aralarındaki tüm boşlukları sıfırlamak için hspace=0, wspace=0)
        gs = gridspec.GridSpecFromSubplotSpec(2, 2, subplot_spec=gs_spec, wspace=0.0, hspace=0.0)
        
        # PyWavelets formatı: coeffs[idx] = (LH, HL, HH)
        lh, hl, hh = coeffs[idx]
        
        # Çözünürlük seviyesini hesapla (Level 1 en dış seviyedir)
        level_num = len(coeffs) - idx
        color = color_palette[level_num % len(color_palette)]
        
        # 1. HL Bandı (Sağ Üst - Dikey Detaylar)
        ax_hl = fig.add_subplot(gs[0, 1])
        plot_subband(ax_hl, hl, f"HL {level_num}", color)
        
        # 2. LH Bandı (Sol Alt - Yatay Detaylar)
        ax_lh = fig.add_subplot(gs[1, 0])
        plot_subband(ax_lh, lh, f"LH {level_num}", color)
        
        # 3. HH Bandı (Sağ Alt - Köşegen Detaylar)
        ax_hh = fig.add_subplot(gs[1, 1])
        plot_subband(ax_hh, hh, f"HH {level_num}", color)
        
        # 4. Sol Üst Hücre: Daha derin bir çözünürlük katmanı varsa rekürsif çağrı, son seviyede ise LL bandı
        if idx > 1:
            draw_dwt_grid(gs[0, 0], idx - 1)
        else:
            # En derin seviyedeki kaba yaklaşım bandı (LL - Low-Low Approximation)
            ll = coeffs[0]
            ax_ll = fig.add_subplot(gs[0, 0])
            ll_color = color_palette[0]  # LL bandı için özel turuncu çerçeve
            plot_subband(ax_ll, ll, f"LL {level_num}", ll_color)

    # Rekürsif çizim fonksiyonunu en dış seviyeden (N. indeksten) başlatıyoruz
    N = len(coeffs) - 1
    draw_dwt_grid(main_gs[0, 0], N)
    
    # Grafiği base64 string olarak belleğe alıp sunucuya iletiyoruz
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', dpi=130)
    img.seek(0)
    plt.close(fig)
    
    return base64.b64encode(img.getvalue()).decode()