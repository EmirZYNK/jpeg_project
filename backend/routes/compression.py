from flask import Blueprint, request, jsonify
import os, sys, time
import numpy as np
from PIL import Image

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

from dsp.jpeg.zigzag import block_to_zigzag
from dsp.jpeg.lossless import encode_block
from dsp.jpeg.huffman import huffman_encode

compression_bp = Blueprint('compression', __name__)
UPLOAD_FOLDER = '../data/uploads'
OUTPUT_FOLDER = '../data/outputs'

def clear_folders():
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path): os.unlink(file_path)
            except Exception as e:
                pass

@compression_bp.route('/compress', methods=['POST'])
def compress_image():
    clear_folders()

    if 'image' not in request.files: return jsonify({'error': 'Resim seçilmedi.'}), 400

    file = request.files['image']
    algorithm = request.form.get('algorithm')
    factor = int(request.form.get('factor', 1))
    
    wavelet_type = request.form.get('wavelet', 'bior4.4')
    decomposition_level = int(request.form.get('level', 2))
    category = request.form.get('category', 'natural')
    
    original_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(original_path)
    original_size = os.path.getsize(original_path)
    target_size = original_size / factor

    output_filename = f"res_{int(time.time())}.jpg"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    try:
        # 1. Görüntü Hazırlığı
        img = Image.open(original_path).convert('RGB')
        w, h = img.size
        img = img.crop((0, 0, (w//8)*8, (h//8)*8))
        img_np = np.array(img)
        Y, Cb, Cr = rgb_to_ycbcr(img_np)
        
        # =====================================================================
        # 2. GRAFİK İÇİN HIZLI GERÇEK VERİ ÜRETİMİ (RATE-DISTORTION CURVE)
        # =====================================================================
        # Akademik sıralama için çok sıkıştırılmıştan (20x), orijinaline (1x) doğru gidiyoruz
        test_factors = [20, 15, 10, 5, 1] 
        
        # Orijinal RGB = 24 Bit. Çarpana bölerek tahmini BPP'yi (X Ekseni) buluyoruz
        test_bpps = [round(24 / tf, 2) for tf in test_factors] 
        
        real_jpeg_psnrs = []
        real_j2k_psnrs = []

        # İşlemi hızlandırmak için temel dönüşümleri 1 kez yapıyoruz
        dct_Y = blockwise_dct(Y); dct_Cb = blockwise_dct(Cb); dct_Cr = blockwise_dct(Cr)
        dwt_Y = apply_dwt_2d(Y, wavelet_type, decomposition_level)
        dwt_Cb = apply_dwt_2d(Cb, wavelet_type, decomposition_level)
        dwt_Cr = apply_dwt_2d(Cr, wavelet_type, decomposition_level)

        for tf in test_factors:
            # --- JPEG GERÇEK TESTİ ---
            q_est = max(1, int(95 / tf))
            q_Y_t = blockwise_quantization(dct_Y, q_est, True, category)
            q_Cb_t = blockwise_quantization(dct_Cb, q_est, False, category)
            q_Cr_t = blockwise_quantization(dct_Cr, q_est, False, category)
            
            dq_Y_t = blockwise_dequantization(q_Y_t, q_est, True, category)
            dq_Cb_t = blockwise_dequantization(q_Cb_t, q_est, False, category)
            dq_Cr_t = blockwise_dequantization(q_Cr_t, q_est, False, category)
            
            rec_jpeg = ycbcr_to_rgb(blockwise_idct(dq_Y_t), blockwise_idct(dq_Cb_t), blockwise_idct(dq_Cr_t))
            _, psnr_j, _ = calculate_metrics(img_np, rec_jpeg)
            real_jpeg_psnrs.append(psnr_j)

            # --- JPEG2000 GERÇEK TESTİ (GÜNCELLENDİ) ---
            # tf=1 (Orijinal) ise 1 gönderiyoruz ki kayıpsız (lossless) çalışsın
            j2k_tf = 1 if tf == 1 else tf * 2
            
            q_w_Y = adaptive_quantize_dwt(dwt_Y, j2k_tf)
            q_w_Cb = adaptive_quantize_dwt(dwt_Cb, j2k_tf)
            q_w_Cr = adaptive_quantize_dwt(dwt_Cr, j2k_tf)
            
            rec_Y = apply_idwt_2d(q_w_Y, wavelet_type)[:Y.shape[0], :Y.shape[1]]
            rec_Cb = apply_idwt_2d(q_w_Cb, wavelet_type)[:Cb.shape[0], :Cb.shape[1]]
            rec_Cr = apply_idwt_2d(q_w_Cr, wavelet_type)[:Cr.shape[0], :Cr.shape[1]]
            
            rec_j2k = ycbcr_to_rgb(rec_Y, rec_Cb, rec_Cr)
            _, psnr_k, _ = calculate_metrics(img_np, rec_j2k)
            real_j2k_psnrs.append(psnr_k)

        # Grafiği Çiz
        plot_url = generate_comparison_plot(test_bpps, real_jpeg_psnrs, real_j2k_psnrs)
        # =====================================================================

        # 3. KULLANICININ SEÇTİĞİ ALGORİTMA İLE ASIL SIKIŞTIRMA VE BPP HESABI
        calculated_bpp = 0
        total_pixels = img_np.shape[0] * img_np.shape[1]

        if algorithm == 'jpeg':
            q_estimate = max(1, int(95 / factor))
            q_Y = blockwise_quantization(dct_Y, q_estimate, True, category)
            q_Cb = blockwise_quantization(dct_Cb, q_estimate, False, category)
            q_Cr = blockwise_quantization(dct_Cr, q_estimate, False, category)
            
            # Kayıpsız (Huffman) BPP Hesabı
            total_bits = 0
            for channel_data in [q_Y, q_Cb, q_Cr]:
                ch_h, ch_w = channel_data.shape
                prev_dc = 0
                all_encoded_symbols = []
                for i in range(0, ch_h, 8):
                    for j in range(0, ch_w, 8):
                        block = channel_data[i:i+8, j:j+8]
                        zigzag_arr = block_to_zigzag(block)
                        dc_diff, rle_data = encode_block(zigzag_arr, prev_dc)
                        prev_dc = zigzag_arr[0]
                        all_encoded_symbols.append(str(dc_diff))
                        all_encoded_symbols.extend([str(item) for item in rle_data])
                
                bitstream, _ = huffman_encode(all_encoded_symbols)
                total_bits += len(bitstream)
            
            calculated_bpp = round(total_bits / total_pixels, 3)

            dq_Y = blockwise_dequantization(q_Y, q_estimate, True, category)
            dq_Cb = blockwise_dequantization(q_Cb, q_estimate, False, category)
            dq_Cr = blockwise_dequantization(q_Cr, q_estimate, False, category)
            final_np = ycbcr_to_rgb(blockwise_idct(dq_Y), blockwise_idct(dq_Cb), blockwise_idct(dq_Cr))
            
        else:
            # JPEG2000 Asıl İşlem (GÜNCELLENDİ)
            # Seçilen çarpan 1 ise veriyi bozmuyoruz
            final_j2k_factor = 1 if factor == 1 else factor * 2
            
            q_coeffs_Y = adaptive_quantize_dwt(dwt_Y, final_j2k_factor) 
            q_coeffs_Cb = adaptive_quantize_dwt(dwt_Cb, final_j2k_factor) 
            q_coeffs_Cr = adaptive_quantize_dwt(dwt_Cr, final_j2k_factor) 
            
            rec_Y = apply_idwt_2d(q_coeffs_Y, wavelet=wavelet_type)[:Y.shape[0], :Y.shape[1]]
            rec_Cb = apply_idwt_2d(q_coeffs_Cb, wavelet=wavelet_type)[:Cb.shape[0], :Cb.shape[1]]
            rec_Cr = apply_idwt_2d(q_coeffs_Cr, wavelet=wavelet_type)[:Cr.shape[0], :Cr.shape[1]]
            
            final_np = ycbcr_to_rgb(rec_Y, rec_Cb, rec_Cr)
            calculated_bpp = round((target_size * 8) / total_pixels, 3)

        # 4. ÇIKTIYI DOSYAYA KAYDETME
        final_image = Image.fromarray(final_np)
        current_q = 90
        while True:
            final_image.save(output_path, format='JPEG', quality=current_q, optimize=True)
            current_size = os.path.getsize(output_path)
            if factor == 1 or current_size <= target_size or current_q <= 5:
                break
            current_q -= 5 

        # 5. METRİKLERİ HESAPLA VE FRONTEND'E DÖN
        mse_s, psnr_s, ssim_s = calculate_metrics(img_np, final_np)
        real_factor = round(original_size / current_size, 2)

        return jsonify({
            'compressed_url': f'/outputs/{output_filename}?t={int(time.time())}',
            'original_size_kb': round(original_size / 1024, 2),
            'compressed_size_kb': round(current_size / 1024, 2),
            'algorithm': algorithm,
            'compression_ratio': real_factor,
            'bpp': calculated_bpp,
            'mse': mse_s,
            'psnr': psnr_s,
            'ssim': ssim_s,
            'plot_url': 'data:image/png;base64,' + plot_url
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc() 
        return jsonify({'error': str(e)}), 500