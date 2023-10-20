import common.logger as logger
import numpy as np
from skimage.restoration import denoise_nl_means, denoise_bilateral

log = logger.get_logger()


def apply_bilateral_denoise(image, sigma_color=0.05, sigma_spatial=15, channel_axis=-1):
    """
    Applies bilateral denoising to the input image.

    Parameters:
    image (numpy.ndarray): The input image to be denoised. If the image is complex, its magnitude is extracted before denoising.
    sigma_color (float, optional): The 'color' standard deviation for the bilateral filter.
    sigma_spatial (int, optional): The 'spatial' standard deviation for the bilateral filter.
    channel_axis (int, optional): The axis of the color channel. Default is -1 (the last dimension).

    Returns:
    numpy.ndarray: The denoised image.
    """
    if np.iscomplexobj(image):
        log.info("Extracting magnitude of complex image")
        image = np.abs(image)
    
    log.info(f"Applying bilateral denoising with sigma_color={sigma_color} and sigma_spatial={sigma_spatial}")
    image_bilateral = denoise_bilateral(image, sigma_color=sigma_color, sigma_spatial=sigma_spatial, channel_axis=channel_axis)
    return image_bilateral

def apply_nl_means_denoise(image, patch_size=5, patch_distance=3, h=0.1, channel_axis=-1):
    """
    Applies Non-Local Means denoising to the input image.

    Parameters:
    image (numpy.ndarray): The input image to be denoised. If the image is complex, its magnitude is extracted before denoising.
    patch_size (int, optional): The size of the patches for denoising.
    patch_distance (int, optional): The maximal distance in pixels where to search patches used for denoising.
    h (float, optional): The cut-off distance (the higher h, the more smoothing effect).
    channel_axis (int, optional): The axis of the color channel. Default is -1 (the last dimension).

    Returns:
    numpy.ndarray: The denoised image.
    """
    if np.iscomplexobj(image):
        log.info("Extracting magnitude of complex image")
        image = np.abs(image)
    
    log.info(f"Applying NL means denoising with patch_size={patch_size}, patch_distance={patch_distance} and h={h}")
    image_nl_means = denoise_nl_means(image, patch_size=patch_size, patch_distance=patch_distance, h=h, channel_axis=channel_axis)
    return image_nl_means