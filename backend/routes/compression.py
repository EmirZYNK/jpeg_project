from flask import Blueprint, request, jsonify
import os, sys, time, io
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
from dsp.evaluation.graphs import generate_histogram, generate_error_map, generate_subband_grid

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
    mode = request.form.get('mode', 'analysis') 
    algorithm = request.form.get('algorithm')
    factor = float(request.form.get('factor', 1))
    
    wavelet_type = request.form.get('wavelet', 'bior4.4')
    decomposition_level = int(request.form.get('level', 2))
    category = request.form.get('category', 'natural')
    lossy_mode = request.form.get('lossyMode', 'true') == 'true'
    
    # Biyomedikal mod kısıtlamaları
    if category == 'biomedical':
        if not lossy_mode:
            factor = 1.0
        elif factor > 5.0:
            factor = 5.0

    original_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(original_path)
    original_size = os.path.getsize(original_path)

    try:
        # 1. Görüntü Hazırlığı
        img = Image.open(original_path).convert('RGB')
        w, h = img.size
        img = img.crop((0, 0, (w//8)*8, (h//8)*8))
        img_np = np.array(img)
        Y, Cb, Cr = rgb_to_ycbcr(img_np)
        
        dct_Y = blockwise_dct(Y); dct_Cb = blockwise_dct(Cb); dct_Cr = blockwise_dct(Cr)
        dwt_Y = apply_dwt_2d(Y, wavelet_type, decomposition_level)
        dwt_Cb = apply_dwt_2d(Cb, wavelet_type, decomposition_level)
        dwt_Cr = apply_dwt_2d(Cr, wavelet_type, decomposition_level)

        total_pixels = img_np.shape[0] * img_np.shape[1]

        # 2. YARDIMCI MOTORLAR (HUFFMAN VE AĞIR DÖNGÜLER KALDIRILDI)
        def get_jpeg_result():
            q_est = max(1, int(95 / factor))
            if factor == 1.0: q_est = 100
            q_Y = blockwise_quantization(dct_Y, q_est, True, category)
            q_Cb = blockwise_quantization(dct_Cb, q_est, False, category)
            q_Cr = blockwise_quantization(dct_Cr, q_est, False, category)
            return ycbcr_to_rgb(
                blockwise_idct(blockwise_dequantization(q_Y, q_est, True, category)),
                blockwise_idct(blockwise_dequantization(q_Cb, q_est, False, category)),
                blockwise_idct(blockwise_dequantization(q_Cr, q_est, False, category))
            )

        def get_j2k_result():
            q_step = factor * 5.0 if factor > 1 else 1.0
            if factor == 1.0: q_step = 1.0
            
            q_w_Y = adaptive_quantize_dwt(dwt_Y, q_step)
            q_w_Cb = adaptive_quantize_dwt(dwt_Cb, q_step)
            q_w_Cr = adaptive_quantize_dwt(dwt_Cr, q_step)
            res_np = ycbcr_to_rgb(
                apply_idwt_2d(q_w_Y, wavelet_type)[:Y.shape[0], :Y.shape[1]],
                apply_idwt_2d(q_w_Cb, wavelet_type)[:Cb.shape[0], :Cb.shape[1]],
                apply_idwt_2d(q_w_Cr, wavelet_type)[:Cr.shape[0], :Cr.shape[1]]
            )
            return res_np

        def save_and_eval(np_img, prefix):
            out_name = f"{prefix}_{int(time.time())}.png"
            out_path = os.path.join(OUTPUT_FOLDER, out_name)
            pil_img = Image.fromarray(np_img)
            # Arayüzde göstermek için kayıpsız PNG olarak yazıyoruz (Yeniden oluşturulmuş ham hali)
            pil_img.save(out_path, format='PNG')
            
            # Teorik sıkıştırılmış boyut hesaplama (Huffman olmadığı için matematiksel tahmin)
            c_size = int(original_size / max(1.0, factor))
            if factor == 1.0: c_size = original_size
                
            mse, psnr, ssim = calculate_metrics(img_np, np_img) 
            real_bpp = round((c_size * 8) / total_pixels, 3)
            
            return out_name, c_size, mse, psnr, ssim, real_bpp, np_img

        # 3. MODA GÖRE ÇIKTI VE HİSTOGRAM OLUŞTURMA
        if mode == 'comparison':
            jpeg_np = get_jpeg_result()
            j_name, j_size, j_mse, j_psnr, j_ssim, j_bpp, final_j_np = save_and_eval(jpeg_np, "comp_jpeg")
            
            j2k_np = get_j2k_result()
            k_name, k_size, k_mse, k_psnr, k_ssim, k_bpp, final_k_np = save_and_eval(j2k_np, "comp_j2k")
            
            plot_url = generate_histogram(img_np, final_j_np, "JPEG", final_k_np, "JPEG 2000")
            err_j_url = generate_error_map(img_np, final_j_np)
            err_k_url = generate_error_map(img_np, final_k_np)
            subband_url = generate_subband_grid(dwt_Y)
            
            return jsonify({
                'mode': 'comparison',
                'jpeg_url': f'/outputs/{j_name}?t={int(time.time())}',
                'j2k_url': f'/outputs/{k_name}?t={int(time.time())}',
                'jpeg_stats': {'size': round(j_size/1024, 2), 'bytes': j_size, 'bpp': j_bpp, 'psnr': j_psnr, 'ssim': j_ssim, 'mse': j_mse, 'ratio': round(original_size / max(1, j_size), 2)},
                'j2k_stats': {'size': round(k_size/1024, 2), 'bytes': k_size, 'bpp': k_bpp, 'psnr': k_psnr, 'ssim': k_ssim, 'mse': k_mse, 'ratio': round(original_size / max(1, k_size), 2)},
                'original_size_kb': round(original_size / 1024, 2),
                'original_size_bytes': original_size,
                'total_pixels': total_pixels,
                'plot_url': 'data:image/png;base64,' + plot_url,
                'error_map_j_url': 'data:image/png;base64,' + err_j_url,
                'error_map_k_url': 'data:image/png;base64,' + err_k_url,
                'subband_url': 'data:image/png;base64,' + subband_url
            }), 200

        else: # Analysis Mode
            final_np = get_jpeg_result() if algorithm == 'jpeg' else get_j2k_result()
            out_name, out_size, mse, psnr, ssim, res_bpp, final_out_np = save_and_eval(final_np, "single")
            
            algo_name = "JPEG" if algorithm == 'jpeg' else "JPEG 2000"
            plot_url = generate_histogram(img_np, final_out_np, algo_name)
            error_map_url = generate_error_map(img_np, final_out_np)
            
            subband_url = None
            if algorithm == 'jpeg2000':
                subband_url = generate_subband_grid(dwt_Y)
            
            return jsonify({
                'mode': 'analysis',
                'compressed_url': f'/outputs/{out_name}?t={int(time.time())}',
                'original_size_kb': round(original_size / 1024, 2),
                'compressed_size_kb': round(out_size / 1024, 2),
                'original_size_bytes': original_size,
                'compressed_size_bytes': out_size,
                'total_pixels': total_pixels,
                'algorithm': algorithm,
                'compression_ratio': round(original_size / max(1, out_size), 2),
                'bpp': res_bpp, 'mse': mse, 'psnr': psnr, 'ssim': ssim,
                'plot_url': 'data:image/png;base64,' + plot_url,
                'error_map_url': 'data:image/png;base64,' + error_map_url,
                'subband_url': 'data:image/png;base64,' + subband_url if subband_url else None
            }), 200

    except Exception as e:
        import traceback
        traceback.print_exc() 
        return jsonify({'error': str(e)}), 500