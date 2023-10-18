from .filter_lib import *

def kspace_center_correction(kspace):
    '''
    Identify the maximum value in the k-space matrix and adjust the matrix via rolling operations to position this maximum value at the center.
    Input: kspace, shape (x,y,z)
    Output: centered kspace, shape (x,y,z)
    '''
    index_max = np.argmax(np.abs(kspace))
    max_index_2d = np.unravel_index(index_max, kspace.shape)
    h,w,z = kspace.shape
    move_h = h//2 - max_index_2d[0]
    move_w = w//2 - max_index_2d[1]
    kspace = np.roll(kspace, (move_h,move_w,0),axis=(0,1,2))
    return kspace

def kspace_filtering(kspace, filter_type, center_correction=True, return_mask=False, **kwargs):
    '''
    Apply a filter to the k-space data.
    Input: kspace, shape (x,y,z)
           filter_type, string, options: 'fermi', 'sine_bell'
           filter_params, dict, contains parameters for the filter
    Output: filtered kspace, shape (x,y,z)
    '''
    if filter_type == 'fermi':
        mask = fermi_filter(kspace.shape, kwargs['radius'], kwargs['width'], kwargs['is_3d'])
    elif filter_type == 'sine_bell':
        mask = sine_bell_filter(kspace.shape, kwargs['radius'], kwargs['is_3d'])
    else:
        raise ValueError('Invalid filter type. Options are: fermi, sine_bell')
    if center_correction:
        kspace = kspace_center_correction(kspace)
    kspace = kspace * mask
    if return_mask:
        return kspace, mask
    else:
        return kspace



