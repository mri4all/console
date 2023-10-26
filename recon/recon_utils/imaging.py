import numpy as np
from typing import Tuple


def centered_fft(x: np.ndarray) -> np.ndarray: # n-dim fft
    return np.fft.fftshift(np.fft.fftn(np.fft.ifftshift(x), norm='ortho'))


def centered_ifft(y) -> np.ndarray: # n-dim ifft
    return np.fft.fftshift(np.fft.ifftn(np.fft.ifftshift(y), norm='ortho'))


def centered_fft2(x: np.ndarray) -> np.ndarray:
    return np.fft.fftshift(np.fft.fft2(np.fft.ifftshift(x), norm='ortho'))


def centered_ifft2(y):
    return np.fft.fftshift(np.fft.ifft2(np.fft.ifftshift(y), norm='ortho'))


def nrmse(x, x_hat):
    return np.linalg.norm(x-x_hat) / np.linalg.norm(x)


def coil_compress(cimgs: np.ndarray, maps: np.ndarray):
    return np.sum(np.conj(maps)*cimgs, axis=-1)


# synthetic field map
def multivariate_gaussian(pos, mu, Sigma):
    """Return the multivariate Gaussian distribution on array pos."""

    n = mu.shape[0]
    Sigma_det = np.linalg.det(Sigma)
    Sigma_inv = np.linalg.inv(Sigma)
    N = np.sqrt((2*np.pi)**n * Sigma_det)
    # This einsum call calculates (x-mu)T.Sigma-1.(x-mu) in a vectorized
    # way across all the input variables.
    fac = np.einsum('...k,kl,...l->...', pos-mu, Sigma_inv, pos-mu)

    return np.exp(-fac / 2) / N

def synth_fmap(shape: Tuple[int,...], spread=100):
    # generate grid of positions
    axes = [np.linspace(-dim/2, dim/2, dim) for dim in shape]
    grid = np.meshgrid(*axes, indexing='xy')
    pos = np.empty(grid[0].shape + (len(shape),))
    for i, xi in enumerate(grid):
        pos[..., i] = xi

    # generate gaussian
    mu = np.array([0.,-30.])
    sigma = np.eye(2)*spread
    z = multivariate_gaussian(pos, mu, sigma)
    
    # multiply 2pi and multiply by spread (accounting for energy dispersion) for [0,1]
    gauss = 2*np.pi*z * spread
    
    return gauss


# SNR
def compute_SNR(img, noisy_img):
    return 20*np.log10(np.linalg.norm(img)/np.linalg.norm(img-noisy_img))  # default is Frobenius norm for matrices

def compute_noise_variance(SNR: float, img: np.ndarray, use_complex=True):
    N = np.prod(img.shape)
    var = np.linalg.norm(img)**2 / (N * 10**(SNR/10))
    return var/2 if use_complex else var


def kspace_center_correction(kspace):
    '''
    Identify the maximum value in the k-space matrix and adjust the matrix via rolling operations to position this maximum value at the center.
    Input: kspace, shape (x,y,z)
    Output: centered kspace, shape (x,y,z)
    BX
    '''
    index_max = np.argmax(np.abs(kspace))
    max_index_2d = np.unravel_index(index_max, kspace.shape)
    h,w,z = kspace.shape
    move_h = h//2 - max_index_2d[0]
    move_w = w//2 - max_index_2d[1]
    kspace = np.roll(kspace, (move_h,move_w,0),axis=(0,1,2))
    return kspace