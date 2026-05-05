from flask import Blueprint, request, jsonify
import os, sys, time, io
import numpy as np
from PIL import Image
import pywt  

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
    factor = int(request.form.get('factor', 1))
    
    wavelet_type = request.form.get('wavelet', 'bior4.4')
    decomposition_level = int(request.form.get('level', 2))
    category = request.form.get('category', 'natural')
    
    original_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(original_path)
    original_size = os.path.getsize(original_path)
    target_size_bytes = original_size / factor

    try:
        img = Image.open(original_path).convert('RGB')
        w, h = img.size
        img = img.crop((0, 0, (w//8)*8, (h//8)*8))
        img_np = np.array(img)
        Y, Cb, Cr = rgb_to_ycbcr(img_np)
        
        dct_Y = blockwise_dct(Y); dct_Cb = blockwise_dct(Cb); dct_Cr = blockwise_dct(Cr)
        dwt_Y = apply_dwt_2d(Y, wavelet_type, decomposition_level)
        dwt_Cb = apply_dwt_2d(Cb, wavelet_type, decomposition_level)
        dwt_Cr = apply_dwt_2d(Cr, wavelet_type, decomposition_level)

        test_factors = [20, 15, 10, 5, 1] 
        test_bpps = [round(24 / tf, 2) for tf in test_factors] 
        real_jpeg_psnrs, real_j2k_psnrs = [], []

        for tf in test_factors:
            q_est = max(1, int(95 / tf))
            rec_j = ycbcr_to_rgb(
                blockwise_idct(blockwise_dequantization(blockwise_quantization(dct_Y, q_est, True, category), q_est, True, category)),
                blockwise_idct(blockwise_dequantization(blockwise_quantization(dct_Cb, q_est, False, category), q_est, False, category)),
                blockwise_idct(blockwise_dequantization(blockwise_quantization(dct_Cr, q_est, False, category), q_est, False, category))
            )
            real_jpeg_psnrs.append(calculate_metrics(img_np, rec_j)[1])

            j2k_graph_q = 0 if tf == 1 else tf
            rec_k = ycbcr_to_rgb(
                apply_idwt_2d(adaptive_quantize_dwt(dwt_Y, j2k_graph_q), wavelet_type)[:Y.shape[0], :Y.shape[1]],
                apply_idwt_2d(adaptive_quantize_dwt(dwt_Cb, j2k_graph_q), wavelet_type)[:Cb.shape[0], :Cb.shape[1]],
                apply_idwt_2d(adaptive_quantize_dwt(dwt_Cr, j2k_graph_q), wavelet_type)[:Cr.shape[0], :Cr.shape[1]]
            )
            real_j2k_psnrs.append(calculate_metrics(img_np, rec_k)[1])

        plot_url = generate_comparison_plot(test_bpps, real_jpeg_psnrs, real_j2k_psnrs)

        total_pixels = img_np.shape[0] * img_np.shape[1]

        def get_jpeg_result():
            q_est = max(1, int(95 / factor))
            q_Y = blockwise_quantization(dct_Y, q_est, True, category)
            q_Cb = blockwise_quantization(dct_Cb, q_est, False, category)
            q_Cr = blockwise_quantization(dct_Cr, q_est, False, category)
            return ycbcr_to_rgb(
                blockwise_idct(blockwise_dequantization(q_Y, q_est, True, category)),
                blockwise_idct(blockwise_dequantization(q_Cb, q_est, False, category)),
                blockwise_idct(blockwise_dequantization(q_Cr, q_est, False, category))
            )

        def get_j2k_result(target_byte_size):
            q_step = 1.0 
            best_np = None
            for _ in range(15):
                q_w_Y = adaptive_quantize_dwt(dwt_Y, q_step)
                q_w_Cb = adaptive_quantize_dwt(dwt_Cb, q_step)
                q_w_Cr = adaptive_quantize_dwt(dwt_Cr, q_step)
                res_np = ycbcr_to_rgb(
                    apply_idwt_2d(q_w_Y, wavelet_type)[:Y.shape[0], :Y.shape[1]],
                    apply_idwt_2d(q_w_Cb, wavelet_type)[:Cb.shape[0], :Cb.shape[1]],
                    apply_idwt_2d(q_w_Cr, wavelet_type)[:Cr.shape[0], :Cr.shape[1]]
                )
                temp_img = Image.fromarray(res_np)
                temp_io = io.BytesIO()
                temp_img.save(temp_io, format='JPEG', quality=95, optimize=True)
                current_size = temp_io.tell()
                best_np = res_np
                if abs(current_size - target_byte_size) < (target_byte_size * 0.02): break
                if current_size > target_byte_size: q_step *= 1.3
                else: q_step *= 0.7
            return best_np

        def save_and_eval(np_img, prefix, force_target_bytes=None):
            out_name = f"{prefix}_{int(time.time())}.jpg"
            out_path = os.path.join(OUTPUT_FOLDER, out_name)
            pil_img = Image.fromarray(np_img)
            t_bytes = force_target_bytes if force_target_bytes else target_size_bytes
            current_q = 95
            while True:
                pil_img.save(out_path, format='JPEG', quality=current_q, optimize=True)
                c_size = os.path.getsize(out_path)
                if factor == 1 or c_size <= t_bytes or current_q <= 5: break
                current_q -= 2
            mse, psnr, ssim = calculate_metrics(img_np, np.array(pil_img)) 
            real_bpp = round((os.path.getsize(out_path) * 8) / total_pixels, 3)
            return out_name, os.path.getsize(out_path), mse, psnr, ssim, real_bpp

        if mode == 'comparison':
            jpeg_np = get_jpeg_result()
            j_name, j_size, j_mse, j_psnr, j_ssim, j_bpp = save_and_eval(jpeg_np, "comp_jpeg")
            j2k_np = get_j2k_result(j_size)
            k_name, k_size, k_mse, k_psnr, k_ssim, k_bpp = save_and_eval(j2k_np, "comp_j2k", force_target_bytes=j_size)
            return jsonify({
                'mode': 'comparison', 'jpeg_url': f'/outputs/{j_name}?t={int(time.time())}', 'j2k_url': f'/outputs/{k_name}?t={int(time.time())}',
                'jpeg_stats': {'size': round(j_size/1024, 2), 'bpp': j_bpp, 'psnr': j_psnr, 'ssim': j_ssim, 'mse': j_mse},
                'j2k_stats': {'size': round(k_size/1024, 2), 'bpp': k_bpp, 'psnr': k_psnr, 'ssim': k_ssim, 'mse': k_mse},
                'original_size_kb': round(original_size / 1024, 2), 'plot_url': 'data:image/png;base64,' + plot_url
            }), 200

        else: 
            final_np = get_jpeg_result() if algorithm == 'jpeg' else get_j2k_result(target_size_bytes)
            out_name, out_size, mse, psnr, ssim, res_bpp = save_and_eval(final_np, "single")
            response_data = {
                'mode': 'analysis', 'compressed_url': f'/outputs/{out_name}?t={int(time.time())}',
                'original_size_kb': round(original_size / 1024, 2), 'compressed_size_kb': round(out_size / 1024, 2),
                'algorithm': algorithm, 'compression_ratio': round(original_size / out_size, 2),
                'bpp': res_bpp, 'mse': mse, 'psnr': psnr, 'ssim': ssim, 'plot_url': 'data:image/png;base64,' + plot_url
            }

            if algorithm == 'jpeg2000':
                coeffs_1 = pywt.wavedec2(Y, wavelet_type, level=1)
                LL, (LH, HL, HH) = coeffs_1
                def save_layer(arr, name, is_ll=False):
                    if is_ll:
                        arr_min, arr_max = arr.min(), arr.max()
                        norm = (arr - arr_min) / (arr_max - arr_min) * 255 if arr_max > arr_min else arr
                        img_np = np.clip(norm, 0, 255).astype(np.uint8)
                    else:
                        amp = np.clip(np.abs(arr) * 4.0, 0, 255) 
                        img_np = amp.astype(np.uint8)
                    out_name = f"dwt_layer_{name}_{int(time.time())}.png"
                    out_path = os.path.join(OUTPUT_FOLDER, out_name)
                    Image.fromarray(img_np).save(out_path)
                    return f'/outputs/{out_name}?t={int(time.time())}'

                coeffs_N = pywt.wavedec2(Y, wavelet_type, level=decomposition_level)
                enhanced_coeffs = []
                LL_N = coeffs_N[0]
                LL_min, LL_max = LL_N.min(), LL_N.max()
                LL_norm = (LL_N - LL_min) / (LL_max - LL_min) * 255 if LL_max > LL_min else LL_N
                enhanced_coeffs.append(LL_norm)
                for i in range(1, len(coeffs_N)):
                    c_LH, c_HL, c_HH = coeffs_N[i]
                    enhanced_coeffs.append((np.clip(np.abs(c_LH) * 4.0, 0, 255), np.clip(np.abs(c_HL) * 4.0, 0, 255), np.clip(np.abs(c_HH) * 4.0, 0, 255)))
                pyramid_arr, _ = pywt.coeffs_to_array(enhanced_coeffs)
                pyramid_name = f"dwt_pyramid_{int(time.time())}.png"
                Image.fromarray(pyramid_arr.astype(np.uint8)).save(os.path.join(OUTPUT_FOLDER, pyramid_name))

                response_data['dwt_urls'] = {
                    'LL': save_layer(LL, 'LL', True), 'LH': save_layer(LH, 'LH', False),
                    'HL': save_layer(HL, 'HL', False), 'HH': save_layer(HH, 'HH', False),
                    'pyramid': f'/outputs/{pyramid_name}?t={int(time.time())}'
                }
            return jsonify(response_data), 200
    except Exception as e:
        import traceback; traceback.print_exc() 
        return jsonify({'error': str(e)}), 500