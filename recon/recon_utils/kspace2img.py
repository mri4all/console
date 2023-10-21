import numpy as np
import os
import sys
import logging
import matplotlib.pyplot as plt

sys.path.append("../")
sys.path.append("/opt/mri4all/console/external/")

import sigpy as sp
 
#Alternate Script for running kspace reconstruction
def fft(x):
    '''Computes the Fast Fourier Transform'''
    s = sp.fft(x, norm='ortho')

    return s

def kspace2img(k_space):
    '''Reconstruct K-space data to image space. Assumes kspace data to be 3 or 4 dimensions.
    
    Parameters
    ----------
    k_space : numpy.ndarray
        K-space data in frequency domain
        
    Returns
    -------
    reconstructed_img : numpy.ndarray
        Reconstructed data in image domain'''
    reconstructed_img = np.empty_like(k_space)

    '''Raise error if Ndim is not 3 or 4'''
    if reconstructed_img.ndim<3 or reconstructed_img.ndim > 4 :
        logging.error(f"Invalid shape of B0 data, expected 3 or 4 but got {np.ndim(k_space)}")
    else:     
        for _ in range(reconstructed_img.shape[-1]):
            slice_data = reconstructed_img[:,:,_] 
            fft_output = fft(slice_data)
            np.append(reconstructed_img, fft_output)
    
    return reconstructed_img