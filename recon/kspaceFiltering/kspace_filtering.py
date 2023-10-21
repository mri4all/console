import numpy as np

def fermi_filter(shape, cutoff_radius_ratio=0.5, transition_width_ratio=0.1, z_type='fermi', cutoff_radius_z_ratio=0.9, transition_width_z_ratio=0.1):
    '''
    Create a Fermi filter for k-space data.
    
    Parameters:
    - shape (tuple): Shape of the filter with length 3, in the form (x, y, z).
    - cutoff_radius_ratio (float): Cutoff radius of the Fermi filter, ranging from 0 to 1. Default is 0.5.
    - transition_width (float): Width of the transition band, controlling the sharpness of the Fermi filter. Default is 10.
    - is_isotropic_3d (bool): Whether to apply the filter in 3D isotropic form or as a 2D filter repeated in each slice. Default is False.
    
    Returns:
    - ndarray: The Fermi filter with shape (x, y, z).
    '''
    if not isinstance(shape, tuple) or len(shape) != 3:
        raise ValueError("Matrix size must be a tuple of length 3.")
    radius = cutoff_radius_ratio*shape[0]
    width = transition_width_ratio*shape[-1]
    if z_type=='isotropic': # 3D isotropic Fermi filter
        axes = [np.linspace(-dim/2, dim/2, dim) for dim in shape]
        grid = np.meshgrid(*axes, indexing='xy')
        pos = np.stack(grid, axis=-1)
        filter = 1/(1+np.exp((np.linalg.norm(pos, axis=-1)-radius)/width))
    elif z_type=='fermi': # 2D Fermi filter on each slice with 1d Fermi filter on z axis
        radius_z = cutoff_radius_z_ratio*shape[-1]
        width_z = transition_width_z_ratio*shape[-1]
        axes = [np.linspace(-dim/2, dim/2, dim) for dim in shape]
        grid = np.meshgrid(*axes, indexing='xy')
        pos = np.stack((grid[0],grid[1]), axis=-1)
        filter = 1/(1+np.exp((np.linalg.norm(pos, axis=-1)-radius)/width))
        filter_z_1d = 1/(1+np.exp((np.abs(grid[2])-radius_z)/width_z))
        filter = filter * filter_z_1d
    elif z_type=='same': # 2D Fermi filter on each slice
        axes = [np.linspace(-dim/2, dim/2, dim) for dim in shape[0:2]]
        grid = np.meshgrid(*axes, indexing='xy')
        pos = np.stack(grid, axis=-1)
        filter = 1/(1+np.exp((np.linalg.norm(pos, axis=-1)-radius)/(width)))
        filter = np.repeat(filter[:,:,None], shape[2], axis=2)
    filter = filter/filter.max()
    return filter

def sine_bell_filter(shape, z_type='fermi', cutoff_radius_z_ratio=0.2, transition_width_z_ratio=0.1):
    '''
    Create a sine bell filter.
    
    Parameters:
    - shape (tuple): The shape of the filter, must be a tuple of length 3 (x, y, z).
    - is_isotropic_3d (bool): Whether to apply the filter in 3D isotropic form or as a 2D filter repeated in each slice. Default is False.
    
    Returns:
    - ndarray: The sine bell filter with shape (x, y, z).
    '''
    if not isinstance(shape, tuple) or len(shape) != 3:
        raise ValueError("Matrix size must be a tuple of length 3.")

    if z_type=='isotropic': # 3D isotropic sine bell filter
        axes = [np.linspace(0, np.pi, dim) for dim in shape]
        grid = np.meshgrid(*axes, indexing='xy')
        filter = np.sin(grid[0])*np.sin(grid[1])*np.sin(grid[2])
    elif z_type=='fermi':  # 2D sine bell filter on each slice with 1d Fermi filter on z axis
        radius_z = cutoff_radius_z_ratio*shape[-1]
        width_z = transition_width_z_ratio*shape[-1]
        axes = [np.linspace(0, np.pi, dim) for dim in shape]
        grid = np.meshgrid(*axes, indexing='xy')
        # Calculate 2D sine-bell filter
        filter = np.sin(grid[0])*np.sin(grid[1])
        filter_z_1d = 1/(1+np.exp((np.abs(grid[2])-radius_z)/width_z))
        filter = filter * filter_z_1d
    elif z_type=='same': # 2D sine bell filter on each slice
        axes = [np.linspace(0, np.pi, dim) for dim in shape[0:2]]
        grid = np.meshgrid(*axes, indexing='xy')
        # Calculate 2D sine-bell filter
        filter = np.sin(grid[0])*np.sin(grid[1])
        # repeat the 2D filter to 3D
        filter = np.repeat(filter[:,:,None], shape[2], axis=2)
    filter = filter/filter.max()
    return filter



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


def kFilter(kspace, filter_type, center_correction=True, **kwargs):
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
    z_type = kwargs.get('z_type', 'fermi')
    return_mask = kwargs.get('return_mask', False)
    width_z = kwargs.get('width_z', 0.1)
    if filter_type == 'fermi':
        radius = kwargs.get('radius', 0.5)
        width = kwargs.get('width', 0.1)
        radius_z = kwargs.get('radius_z', 0.9)
        mask = fermi_filter(shape = kspace.shape, cutoff_radius_ratio = radius, transition_width_ratio = width, cutoff_radius_z_ratio = radius_z, transition_width_z_ratio = width_z, z_type = z_type)
    elif filter_type == 'sine_bell':
        radius_z = kwargs.get('radius_z', 0.2)
        mask = sine_bell_filter(shape = kspace.shape, cutoff_radius_z_ratio = radius_z, transition_width_z_ratio = width_z, z_type = z_type)
    else:
        raise ValueError('Invalid filter type. Options are: fermi, sine_bell')
    if center_correction:
        kspace = kspace_center_correction(kspace)
    kspace = kspace * mask
    if return_mask:
        return kspace, mask
    else:
        return kspace



