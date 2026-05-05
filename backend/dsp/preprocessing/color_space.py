import cv2
import numpy as np


def to_uint8(image):
    return np.clip(image, 0, 255).astype(np.uint8)


def bgr_to_ycrcb(image_bgr):
    image_bgr = to_uint8(image_bgr)
    return cv2.cvtColor(image_bgr, cv2.COLOR_BGR2YCrCb)


def ycrcb_to_bgr(image_ycrcb):
    image_ycrcb = to_uint8(image_ycrcb)
    return cv2.cvtColor(image_ycrcb, cv2.COLOR_YCrCb2BGR)


def split_channels(image):
    return cv2.split(image)


def merge_channels(y, cr, cb):
    y = to_uint8(y)
    cr = to_uint8(cr)
    cb = to_uint8(cb)
    return cv2.merge([y, cr, cb])