from .filter_lib import *

def kspace_center_correction(kspace):
    '''
    Adjust the k-space matrix to position its maximum value at the center.
    
    Parameters:
    - kspace (ndarray): The k-space data with shape (x, y, z).
    
    Returns:
    - ndarray: The centered k-space data with shape (x, y, z).
    '''
    
    index_max = np.argmax(np.abs(kspace))
    max_index_2d = np.unravel_index(index_max, kspace.shape)
    h, w, z = kspace.shape
    move_h = h // 2 - max_index_2d[0]
    move_w = w // 2 - max_index_2d[1]
    kspace = np.roll(kspace, (move_h, move_w, 0), axis=(0, 1, 2))
    
    return kspace


def kspace_filtering(kspace, filter_type, center_correction=True, **kwargs):
    '''
    Apply a filter to the k-space data.
    
    Parameters:
    - kspace (ndarray): The k-space data with shape (x, y, z).
    - filter_type (str): The type of filter to apply. Options are 'fermi' and 'sine_bell'.
    - center_correction (bool): Whether to perform center correction before filtering. Default is True.
    - **kwargs (dict): Additional keyword arguments for specifying filter parameters.
    
    Returns:
    - ndarray: The filtered k-space data with shape (x, y, z).
    - ndarray (optional): The filter mask, only if return_mask is True.
    '''
    # Set isotropic to False by default if not specified
    isotropic = kwargs.get('isotropic', False)
    return_mask = kwargs.get('return_mask', False)

    if filter_type == 'fermi':
        radius = kwargs.get('radius', 0.5)
        width = kwargs.get('width', 10)
        mask = fermi_filter(shape = kspace.shape, cutoff_radius_ratio = radius, transition_width = width, isotropic = isotropic)
    elif filter_type == 'sine_bell':
        mask = sine_bell_filter(shape = kspace.shape, isotropic = isotropic)
    else:
        raise ValueError('Invalid filter type. Options are: fermi, sine_bell')
    if center_correction:
        kspace = kspace_center_correction(kspace)
    kspace = kspace * mask
    if return_mask:
        return kspace, mask
    else:
        return kspace



