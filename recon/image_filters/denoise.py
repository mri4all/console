import common.logger as logger
import numpy as np
from scipy.ndimage import gaussian_filter
from skimage.restoration import (
    denoise_nl_means,
    denoise_bilateral,
    denoise_tv_chambolle,
)

log = logger.get_logger()

MAX_DENOISE_STRENGTH = 9

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

    log.info(
        f"Applying bilateral denoising with sigma_color={sigma_color} and sigma_spatial={sigma_spatial}"
    )
    image_bilateral = denoise_bilateral(
        image,
        sigma_color=sigma_color,
        sigma_spatial=sigma_spatial,
        channel_axis=channel_axis,
    )
    return image_bilateral


def apply_nl_means_denoise(
    image, patch_size=5, patch_distance=3, h=0.1, channel_axis=-1
):
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

    log.info(
        f"Applying NL means denoising with patch_size={patch_size}, patch_distance={patch_distance} and h={h}"
    )
    image_nl_means = denoise_nl_means(
        image,
        patch_size=patch_size,
        patch_distance=patch_distance,
        h=h,
        channel_axis=channel_axis,
    )
    return image_nl_means


def apply_total_variation_denoise(image, weight=0.1, channel_axis=-1):
    """
    Applies total variation denoising to the input image.

    Parameters:
    image (numpy.ndarray): The input image to be denoised. If the image is complex, its magnitude is extracted before denoising.
    weight (float, optional): The denoising weight. Default is 0.1.
    channel_axis (int, optional): The axis of the color channel. Default is -1 (the last dimension).

    Returns:
    numpy.ndarray: The denoised image.
    """

    if np.iscomplexobj(image):
        log.info("Extracting magnitude of complex image")
        image = np.abs(image)

    log.info(f"Applying total variation denoising with weight={weight}")
    image_tv_chambolle = denoise_tv_chambolle(
        image,
        weight=weight,
        channel_axis=channel_axis,
    )
    return image_tv_chambolle


def remove_gaussian_noise(image, sigma=0.2):
    """
    Removes Gaussian noise from the input image.

    Parameters:
    image (numpy.ndarray): The input image from which noise is to be removed.
    sigma (float, optional): The standard deviation for the Gaussian kernel.

    Returns:
    numpy.ndarray: The denoised image.
    """
    if np.iscomplexobj(image):
        log.info("Extracting magnitude of complex image")
        image = np.abs(image)

    log.info(f"Applying Gaussian filter with sigma={sigma}")
    image_gaussian = gaussian_filter(image, sigma=sigma)
    return image_gaussian


def _apply_filter(real_part, imag_part, method, strength):
    # Normalize strength to be between 0 and 1
    normalized_strength = strength / MAX_DENOISE_STRENGTH

    # Apply the filter to the real and imaginary parts separately
    if method == "gaussian_filter":
        sigma = normalized_strength * 0.5
        real_part_denoised = remove_gaussian_noise(real_part, sigma=sigma)
        imag_part_denoised = remove_gaussian_noise(imag_part, sigma=sigma)
    elif method == "bilateral":
        sigma_color = normalized_strength * 0.05
        sigma_spatial = normalized_strength * 15
        real_part_denoised = apply_bilateral_denoise(
            real_part, sigma_color=sigma_color, sigma_spatial=sigma_spatial
        )
        imag_part_denoised = apply_bilateral_denoise(
            imag_part, sigma_color=sigma_color, sigma_spatial=sigma_spatial
        )
    elif method == "nl_means":
        h = normalized_strength * 0.1
        real_part_denoised = apply_nl_means_denoise(real_part, h=h)
        imag_part_denoised = apply_nl_means_denoise(imag_part, h=h)
    elif method == "total_variation":
        weight = normalized_strength * 0.1
        real_part_denoised = apply_total_variation_denoise(real_part, weight=weight)
        imag_part_denoised = apply_total_variation_denoise(imag_part, weight=weight)
    else:
        real_part_denoised = real_part
        imag_part_denoised = imag_part
        log.error(f"Method {method} not recognized.")

    return real_part_denoised, imag_part_denoised


def remove_gaussian_noise_complex(image_complex, method="gaussian_filter", strength=50):
    """
    Removes Gaussian noise from the real and imaginary parts of the input complex image, separately.

    Parameters:
    image_complex (numpy.ndarray) : A complex input image from which noise is to be removed.
    method (str, optional): The method used for denoising. Options are 'gaussian_filter', 'bilateral',
                            'nl_means', and 'total_variation'. Default is 'gaussian_filter'.
    strength (int, optional): The strength of the denoising process. Higher values indicate stronger denoising.
                             Default is 50.

    Returns:
    numpy.ndarray: The denoised complex image.
    """

    # Check that the input is a complex ndarray
    if not np.iscomplexobj(image_complex):
        log.error("The input image must be a complex ndarray.")
        raise ValueError("The input image must be a complex ndarray.")

    # Separate the complex image into the real and imaginary parts
    real_part = np.real(image_complex)
    imag_part = np.imag(image_complex)

    real_part_denoised, imag_part_denoised = _apply_filter(
        real_part, imag_part, method, strength
    )

    # Combine the denoised real and imaginary parts to form the denoised complex image
    image_denoised_complex = real_part_denoised + 1j * imag_part_denoised

    return image_denoised_complex
