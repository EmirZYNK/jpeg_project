import pickle
import zlib
import numpy as np
import pywt


def encode_coefficients_to_bitstream(coeffs, lossless=False):
    coeff_array, coeff_slices = pywt.coeffs_to_array(coeffs)

    if lossless:
        coeff_array = coeff_array.astype(np.float32)
        dtype = "float32"
    else:
        coeff_array = np.round(coeff_array).astype(np.int16)
        dtype = "int16"

    package = {
        "shape": coeff_array.shape,
        "slices": coeff_slices,
        "dtype": dtype,
        "data": coeff_array.tobytes()
    }

    raw_bytes = pickle.dumps(package)
    bitstream = zlib.compress(raw_bytes, level=9)

    return bitstream


def decode_coefficients_from_bitstream(bitstream):
    package = pickle.loads(zlib.decompress(bitstream))

    dtype = np.dtype(package["dtype"])

    coeff_array = np.frombuffer(
        package["data"],
        dtype=dtype
    ).reshape(package["shape"])

    coeffs = pywt.array_to_coeffs(
        coeff_array,
        package["slices"],
        output_format="wavedec2"
    )

    return coeffs