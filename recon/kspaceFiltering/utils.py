import numpy as np

def get_ksp_from_img(img, norm='ortho'):
    '''
    Get the k-space data from an image.
    Input: img, shape (x,y,z)
    Output: k-space data, shape (x,y,z)
    '''
    return np.fft.fftshift(np.fft.fftn(np.fft.ifftshift(img), norm=norm))

def get_img_from_ksp(kspace, norm='ortho'):
    '''
    Get the image from k-space data.
    Input: kspace, shape (x,y,z)
    Output: img, shape (x,y,z)
    '''
    return np.fft.fftshift(np.fft.ifftn(np.fft.ifftshift(kspace), norm=norm))