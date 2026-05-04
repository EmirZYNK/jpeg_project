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
    mode = request.form.get('mode', 'analysis') # 'analysis' veya 'comparison'
    algorithm = request.form.get('algorithm')
    factor = int(request.form.get('factor', 1))
    
    wavelet_type = request.form.get('wavelet', 'bior4.4')
    decomposition_level = int(request.form.get('level', 2))
    category = request.form.get('category', 'natural')
    
    original_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(original_path)
    original_size = os.path.getsize(original_path)
    target_size = original_size / factor

    try:
        # 1. Görüntü Hazırlığı ve Ortak Dönüşümler
        img = Image.open(original_path).convert('RGB')
        w, h = img.size
        img = img.crop((0, 0, (w//8)*8, (h//8)*8))
        img_np = np.array(img)
        Y, Cb, Cr = rgb_to_ycbcr(img_np)
        
        # Grafik için önceden hazırlanan dönüşümler (Hız için 1 kez yapılıyor)
        dct_Y = blockwise_dct(Y); dct_Cb = blockwise_dct(Cb); dct_Cr = blockwise_dct(Cr)
        dwt_Y = apply_dwt_2d(Y, wavelet_type, decomposition_level)
        dwt_Cb = apply_dwt_2d(Cb, wavelet_type, decomposition_level)
        dwt_Cr = apply_dwt_2d(Cr, wavelet_type, decomposition_level)

        # 2. GRAFİK VERİ ÜRETİMİ (RD CURVE)
        test_factors = [20, 15, 10, 5, 1] 
        test_bpps = [round(24 / tf, 2) for tf in test_factors] 
        real_jpeg_psnrs, real_j2k_psnrs = [], []

        for tf in test_factors:
            # JPEG Test
            q_est = max(1, int(95 / tf))
            rec_j = ycbcr_to_rgb(
                blockwise_idct(blockwise_dequantization(blockwise_quantization(dct_Y, q_est, True, category), q_est, True, category)),
                blockwise_idct(blockwise_dequantization(blockwise_quantization(dct_Cb, q_est, False, category), q_est, False, category)),
                blockwise_idct(blockwise_dequantization(blockwise_quantization(dct_Cr, q_est, False, category), q_est, False, category))
            )
            real_jpeg_psnrs.append(calculate_metrics(img_np, rec_j)[1])

            # J2K Test
            j2k_tf = 1 if tf == 1 else tf * 2
            rec_k = ycbcr_to_rgb(
                apply_idwt_2d(adaptive_quantize_dwt(dwt_Y, j2k_tf), wavelet_type)[:Y.shape[0], :Y.shape[1]],
                apply_idwt_2d(adaptive_quantize_dwt(dwt_Cb, j2k_tf), wavelet_type)[:Cb.shape[0], :Cb.shape[1]],
                apply_idwt_2d(adaptive_quantize_dwt(dwt_Cr, j2k_tf), wavelet_type)[:Cr.shape[0], :Cr.shape[1]]
            )
            real_j2k_psnrs.append(calculate_metrics(img_np, rec_k)[1])

        plot_url = generate_comparison_plot(test_bpps, real_jpeg_psnrs, real_j2k_psnrs)

        # 3. YARDIMCI MOTOR FONKSİYONLARI
        total_pixels = img_np.shape[0] * img_np.shape[1]

        def get_jpeg_result():
            q_est = max(1, int(95 / factor))
            q_Y = blockwise_quantization(dct_Y, q_est, True, category)
            q_Cb = blockwise_quantization(dct_Cb, q_est, False, category)
            q_Cr = blockwise_quantization(dct_Cr, q_est, False, category)
            
            # Huffman BPP Hesabı
            total_bits = 0
            for channel in [q_Y, q_Cb, q_Cr]:
                prev_dc = 0
                symbols = []
                for i in range(0, channel.shape[0], 8):
                    for j in range(0, channel.shape[1], 8):
                        z = block_to_zigzag(channel[i:i+8, j:j+8])
                        dc_diff, rle = encode_block(z, prev_dc)
                        prev_dc = z[0]
                        symbols.append(str(dc_diff))
                        symbols.extend([str(x) for x in rle])
                bitstream, _ = huffman_encode(symbols)
                total_bits += len(bitstream)
            
            res_np = ycbcr_to_rgb(
                blockwise_idct(blockwise_dequantization(q_Y, q_est, True, category)),
                blockwise_idct(blockwise_dequantization(q_Cb, q_est, False, category)),
                blockwise_idct(blockwise_dequantization(q_Cr, q_est, False, category))
            )
            return res_np, round(total_bits / total_pixels, 3)

        def get_j2k_result():
            j2k_f = 1 if factor == 1 else factor * 2
            res_np = ycbcr_to_rgb(
                apply_idwt_2d(adaptive_quantize_dwt(dwt_Y, j2k_f), wavelet_type)[:Y.shape[0], :Y.shape[1]],
                apply_idwt_2d(adaptive_quantize_dwt(dwt_Cb, j2k_f), wavelet_type)[:Cb.shape[0], :Cb.shape[1]],
                apply_idwt_2d(adaptive_quantize_dwt(dwt_Cr, j2k_f), wavelet_type)[:Cr.shape[0], :Cr.shape[1]]
            )
            return res_np, round((target_size * 8) / total_pixels, 3)

        def save_and_eval(np_img, prefix):
            out_name = f"{prefix}_{int(time.time())}.jpg"
            out_path = os.path.join(OUTPUT_FOLDER, out_name)
            # Kayıt sırasında ek sıkıştırma olmaması için yüksek kalite (95) kullanıyoruz
            Image.fromarray(np_img).save(out_path, format='JPEG', quality=95)
            mse, psnr, ssim = calculate_metrics(img_np, np_img)
            return out_name, os.path.getsize(out_path), mse, psnr, ssim

        # 4. MODA GÖRE ÇIKTI ÜRETİMİ
        if mode == 'comparison':
            jpeg_np, j_bpp = get_jpeg_result()
            j2k_np, k_bpp = get_j2k_result()
            
            j_name, j_size, j_mse, j_psnr, j_ssim = save_and_eval(jpeg_np, "comp_jpeg")
            k_name, k_size, k_mse, k_psnr, k_ssim = save_and_eval(j2k_np, "comp_j2k")
            
            return jsonify({
                'mode': 'comparison',
                'jpeg_url': f'/outputs/{j_name}?t={int(time.time())}',
                'j2k_url': f'/outputs/{k_name}?t={int(time.time())}',
                'jpeg_stats': {'size': round(j_size/1024, 2), 'bpp': j_bpp, 'psnr': j_psnr, 'ssim': j_ssim, 'mse': j_mse},
                'j2k_stats': {'size': round(k_size/1024, 2), 'bpp': k_bpp, 'psnr': k_psnr, 'ssim': k_ssim, 'mse': k_mse},
                'original_size_kb': round(original_size / 1024, 2),
                'plot_url': 'data:image/png;base64,' + plot_url
            }), 200

        else: # Analysis Mode
            final_np, calc_bpp = get_jpeg_result() if algorithm == 'jpeg' else get_j2k_result()
            out_name, out_size, mse, psnr, ssim = save_and_eval(final_np, "single")
            
            return jsonify({
                'mode': 'analysis',
                'compressed_url': f'/outputs/{out_name}?t={int(time.time())}',
                'original_size_kb': round(original_size / 1024, 2),
                'compressed_size_kb': round(out_size / 1024, 2),
                'algorithm': algorithm,
                'compression_ratio': round(original_size / out_size, 2),
                'bpp': calc_bpp, 'mse': mse, 'psnr': psnr, 'ssim': ssim,
                'plot_url': 'data:image/png;base64,' + plot_url
            }), 200

    except Exception as e:
        import traceback
        traceback.print_exc() 
        return jsonify({'error': str(e)}), 500