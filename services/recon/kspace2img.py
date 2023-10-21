import numpy as np
import os
import sys
import logging
import matplotlib.pyplot as plt

sys.path.append("../")
sys.path.append("/opt/mri4all/console/external/")

import sigpy as sp

def final_recon(B0_corr):
    '''Wrapper with B0 input and Reconstructed image Output
    
    Parameters
    ----------
    B0_corr : numpy.ndarray
        B0_corrected data in frequency domain
        Expects (X, Y, Z, TE) with ndim= 3 or 4

    Returns
    -------
    reconstructed_image : numpy.ndarray
        Reconstructed data in image domain'''

    '''Check the shape'''
    reconstructed_image = kspace2img(B0_corr)
    print(reconstructed_image)
       
    return reconstructed_image
  
def fft(x):
    '''Computes the Fast Fourier Transform'''
    # s = np.fft.fftshift(np.fft.fftn(np.fft.fftshift(x, axes=(0,1,2)), axes=(0,1,2)), axes=(0,1,2))
    # f = np.fft.fftshift(np.fft.fftn(np.fft.fftshift(x)))
    s = sp.fft(x, norm='ortho')

    return s

def kspace2img(k_space_B0_corr):
    '''Reconstruct K-space data to image space takes in a 3D (or multislice 2D kspace)
    
    Parameters
    ----------
    k_space_B0_corr : numpy.ndarray
        K-space data in frequency domain
        
    Returns
    -------
    reconstructed_img : numpy.ndarray
        Reconstructed data in image domain'''
    final_arr = np.empty_like(k_space_B0_corr)

    '''Raise error if Ndim is not 3 or 4'''
    if final_arr.ndim<3 or final_arr.ndim > 4 :
        logging.error(f"Invalid shape of B0 data, expected 3 or 4 but got {np.ndim(k_space_B0_corr)}")
    # elif final_arr.ndim==3:
    #     final_arr = np.expand_dims(final_arr, axis=-1)
    
    # for _ in range(final_arr.shape[-1]):
    #     slice_data = final_arr[:,:,:,_] 
    #     fft_output = fft(slice_data)
    #     np.append(final_arr, fft_output)

    else:     
        for _ in range(final_arr.shape[-1]):
            slice_data = final_arr[:,:,_] 
            fft_output = fft(slice_data)
            np.append(final_arr, fft_output)
    
    return final_arr

def main():
    test_B0= np.load('/vagrant/sample_files/test_data_kspace_d1s1.npy')
    # test_B0= np.load('/vagrant/sample_files/kspace.npy')
    # print(test_B0.shape)
    img = final_recon(test_B0)

if __name__=='__main__':
    main()
