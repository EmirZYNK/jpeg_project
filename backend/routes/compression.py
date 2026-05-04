from flask import Blueprint, request, jsonify
import os, sys, time
import numpy as np
from PIL import Image

# Proje kök dizinini ekle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from dsp.preprocessing.color_space import rgb_to_ycbcr, ycbcr_to_rgb
from dsp.jpeg.dct import blockwise_dct
from dsp.jpeg.quantization import blockwise_quantization, blockwise_dequantization
from dsp.decoder.inverse_dct import blockwise_idct
from dsp.jpeg2000.dwt import apply_dwt_2d 
from dsp.jpeg2000.quantization import adaptive_quantize_dwt 
from dsp.decoder.inverse_dwt import apply_idwt_2d
from dsp.evaluation.metrics import calculate_metrics
from dsp.evaluation.graphs import generate_comparison_plot

# --- YENİ EKLENEN KAYIPSIZ KODLAMA MODÜLLERİ ---
from dsp.jpeg.zigzag import block_to_zigzag
from dsp.jpeg.lossless import encode_block
from dsp.jpeg.huffman import huffman_encode

compression_bp = Blueprint('compression', __name__)
UPLOAD_FOLDER = '../data/uploads'
OUTPUT_FOLDER = '../data/outputs'

def clear_folders():
    """Dosya birikmesini önlemek için her işlemde klasörleri temizler."""
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path): os.unlink(file_path)
            except Exception as e:
                print(f"Temizlik hatası: {e}")

@compression_bp.route('/compress', methods=['POST'])
def compress_image():
    # 0. Temizlik yap
    clear_folders()

    if 'image' not in request.files:
        return jsonify({'error': 'Resim seçilmedi.'}), 400

    file = request.files['image']
    algorithm = request.form.get('algorithm')
    factor = int(request.form.get('factor', 1))
    
    # Parametreler
    wavelet_type = request.form.get('wavelet', 'bior4.4')
    decomposition_level = int(request.form.get('level', 2))
    category = request.form.get('category', 'natural') # Arayüzden gelen kategori
    
    original_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(original_path)
    original_size = os.path.getsize(original_path)
    target_size = original_size / factor

    output_filename = f"res_{int(time.time())}.jpg"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    try:
        # 1. Görüntüyü Oku ve Standartlaştır
        img = Image.open(original_path).convert('RGB')
        w, h = img.size
        img = img.crop((0, 0, (w//8)*8, (h//8)*8))
        img_np = np.array(img)
        
        # 2. Renk Uzayı Dönüşümü
        Y, Cb, Cr = rgb_to_ycbcr(img_np)
        
        # --- TEK SEFERLİK AĞIR MATEMATİKSEL İŞLEMLER ---
        if algorithm == 'jpeg':
            # Kaliteyi katsayıya göre tahmin et ve bir kez IDCT yap
            q_estimate = max(1, int(95 / factor))
            dct_Y = blockwise_dct(Y); dct_Cb = blockwise_dct(Cb); dct_Cr = blockwise_dct(Cr)
            
            # Kuantizasyon İşlemi
            q_Y = blockwise_quantization(dct_Y, q_estimate, True, category)
            q_Cb = blockwise_quantization(dct_Cb, q_estimate, False, category)
            q_Cr = blockwise_quantization(dct_Cr, q_estimate, False, category)
            
            # =================================================================
            # --- YENİ EKLENEN KAYIPSIZ (LOSSLESS) BÖLÜM VE BPP HESABI ---
            # =================================================================
            total_bits = 0
            
            # Her renk kanalı için sırayla Zigzag -> DPCM/RLE -> Huffman işlemi yap
            for channel_data in [q_Y, q_Cb, q_Cr]:
                ch_h, ch_w = channel_data.shape
                prev_dc = 0
                all_encoded_symbols = []
                
                # Matrisi 8x8 pencerelerle gez
                for i in range(0, ch_h, 8):
                    for j in range(0, ch_w, 8):
                        block = channel_data[i:i+8, j:j+8]
                        
                        # 1. Zigzag Tarama (2D matrisi 1D diziye çevir)
                        zigzag_arr = block_to_zigzag(block)
                        
                        # 2. DPCM ve RLE 
                        dc_diff, rle_data = encode_block(zigzag_arr, prev_dc)
                        prev_dc = zigzag_arr[0] # Sonraki blok için DC'yi güncelle
                        
                        # Sembolleri listeye ekle (Hata almamak için string'e çeviriyoruz)
                        all_encoded_symbols.append(str(dc_diff))
                        all_encoded_symbols.extend([str(item) for item in rle_data])
                
                # 3. Huffman ile Bitstream (1 ve 0 stringi) oluştur
                bitstream, _ = huffman_encode(all_encoded_symbols)
                total_bits += len(bitstream) # Toplam bit sayısını hesapla
            
            # JPEG için BPP (Bits Per Pixel) Hesabı (Gerçek bit sayısına göre)
            total_pixels = img_np.shape[0] * img_np.shape[1]
            calculated_bpp = round(total_bits / total_pixels, 3)
            # =================================================================

            # Ters İşlemler (Görüntüyü geri oluşturmak için)
            dq_Y = blockwise_dequantization(q_Y, q_estimate, True, category)
            dq_Cb = blockwise_dequantization(q_Cb, q_estimate, False, category)
            dq_Cr = blockwise_dequantization(q_Cr, q_estimate, False, category)
            
            final_np = ycbcr_to_rgb(blockwise_idct(dq_Y), blockwise_idct(dq_Cb), blockwise_idct(dq_Cr))
            
        else:
            # JPEG2000 İşlemleri
            processed_channels = []
            for channel in [Y, Cb, Cr]:
                coeffs = apply_dwt_2d(channel, wavelet=wavelet_type, level=decomposition_level)
                q_coeffs = adaptive_quantize_dwt(coeffs, factor * 2) 
                rec_channel = apply_idwt_2d(q_coeffs, wavelet=wavelet_type)
                processed_channels.append(rec_channel[:channel.shape[0], :channel.shape[1]])
            final_np = ycbcr_to_rgb(processed_channels[0], processed_channels[1], processed_channels[2])
            
            # JPEG2000 için BPP Hesabı (Tahmini hedef boyuta göre: byte * 8 = bit)
            total_pixels = img_np.shape[0] * img_np.shape[1]
            calculated_bpp = round((target_size * 8) / total_pixels, 3)

        # 3. HIZLI HEDEF BOYUT DÖNGÜSÜ
        final_image = Image.fromarray(final_np)
        current_q = 90
        while True:
            final_image.save(output_path, format='JPEG', quality=current_q, optimize=True)
            current_size = os.path.getsize(output_path)
            
            if factor == 1 or current_size <= target_size or current_q <= 5:
                break
            current_q -= 5 

        # Metrikler ve İstatistikler
        mse_s, psnr_s, ssim_s = calculate_metrics(img_np, final_np)
        real_factor = round(original_size / current_size, 2)
        
        # Grafik Verisi (Simülasyon)
        ratios = [10, 30, 50, 70, 90]
        jpeg_psnrs = [psnr_s + ((50-r)/5) for r in ratios]
        j2k_psnrs = [psnr_s + ((50-r)/4) + 2 for r in ratios]
        plot_url = generate_comparison_plot(ratios, jpeg_psnrs, j2k_psnrs)

        return jsonify({
            'compressed_url': f'/outputs/{output_filename}?t={int(time.time())}',
            'original_size_kb': round(original_size / 1024, 2),
            'compressed_size_kb': round(current_size / 1024, 2),
            'algorithm': algorithm,
            'compression_ratio': real_factor,
            'bpp': calculated_bpp,  # <-- HESAPLANAN BPP'Yİ ARAYÜZE GÖNDERİYORUZ
            'mse': mse_s,
            'psnr': psnr_s,
            'ssim': ssim_s,
            'plot_url': 'data:image/png;base64,' + plot_url
        }), 200

    except Exception as e:
        import traceback
        print(f"HATA: {e}")
        traceback.print_exc() # Hatayı detaylı görmek için eklendi
        return jsonify({'error': str(e)}), 500