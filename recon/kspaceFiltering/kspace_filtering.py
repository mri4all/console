import numpy as np

def kspace_center_correction(kspace):
    '''
    Adjust the k-space matrix to position its maximum value at the center.
    
    Parameters:
    - kspace (ndarray): The center coorected k-space data.
    
    Returns:
    - ndarray: The centered k-space data.
    '''
    
    index_max = np.argmax(np.abs(kspace))
    max_index_2d = np.unravel_index(index_max, kspace.shape)
    
    if len(kspace.shape)==1:
        h = kspace.shape[0]
        move_h = h // 2 - max_index_2d[0]
        kspace = np.roll(kspace, (move_h), axis=(0))
    else:
        h, w = kspace.shape[0], kspace.shape[1]
        move_h = h // 2 - max_index_2d[0]
        move_w = w // 2 - max_index_2d[1]
        kspace = np.roll(kspace, (move_h, move_w), axis=(0, 1))
    
    return kspace

def kFilter(kspace, filter_type='fermi', center_correction=True, **kwargs):
    '''
    Apply a filter to the k-space data to suppress high-frequency noise. kspace dimension could be 1D, 2D or 3D.
    
    Parameters:
    - kspace (ndarray): The k-space data with shape (x) or (x,y) or (x, y, z).
    - filter_type (str): The type of filter to apply. Options are 'fermi', 'sine_bell' and 'gaussian'.
    - center_correction (bool): Whether to perform center correction before filtering. Default is True.
    - **kwargs (dict): Additional keyword arguments for specifying filter parameters.
        if filter_type is 'fermi', we can further adjust arguments radius (default 0.5) and width (default 0.1). Range from 0 to 1.
        if filter_type is 'gaussian, we can further adjust sigma (default 0.8). Range from 0 to 1.
        if 3D kspace data, we can adjust z_type, which could be 'same', 'fermi' and 'isotropic'.
            if z_type is 'fermi', we can further adjust radius_z (default 0.9) and width_z (default 0.1). Range from 0 to 1.
        if return_mask is True, return both filtered kspace and filter mask. Default is False
    
    Returns:
    - ndarray: The filtered k-space data with shape (x), (x, y) or (x, y, z).
    - ndarray (optional): The filter mask, only if return_mask is True.
    '''
    # Set default value if not specified
    z_type = kwargs.get('z_type', 'fermi')
    return_mask = kwargs.get('return_mask', False)
    width_z = kwargs.get('width_z', 0.1)
    radius_z = kwargs.get('radius_z', 0.9)
    if filter_type == 'fermi':
        radius = kwargs.get('radius', 0.5)
        width = kwargs.get('width', 0.1)
        mask = fermi_filter(shape = kspace.shape, cutoff_radius_ratio = radius, transition_width_ratio = width, cutoff_radius_z_ratio = radius_z, transition_width_z_ratio = width_z, z_type = z_type)
    elif filter_type == 'sine_bell':
        mask = sine_bell_filter(shape = kspace.shape, cutoff_radius_z_ratio = radius_z, transition_width_z_ratio = width_z, z_type = z_type)
    elif filter_type == 'gaussian':
        sigma = kwargs.get('sigma', 0.8)
        mask = gaussian_filter( shape = kspace.shape, sigma_ratio=sigma, cutoff_radius_z_ratio = radius_z, transition_width_z_ratio = width_z, z_type=z_type)

    else:
        raise ValueError('Invalid filter type. Options are: fermi, sine_bell, gaussian')
    if center_correction:
        kspace = kspace_center_correction(kspace)
    kspace = kspace * mask
    if return_mask:
        return kspace, mask
    else:
        return kspace

###### different types of filters ######

def gaussian_filter(shape, sigma_ratio=0.8, z_type='fermi', cutoff_radius_z_ratio=0.9, transition_width_z_ratio=0.1):
    '''
    Create a Gaussian filter for k-space data.

    Parameters:
    - shape (tuple): Shape of the filter with length 1 or 2 or 3, in the form (x), (x, y) or (x, y, z).
    - sigma_ratio (float): Standard deviation of the Gaussian filter, as a ratio of the matrix dimensions. Default is 0.8.
    - z_type (str): Specifies the type of filter in the z-direction ('isotropic', 'fermi' or 'same'). Default is 'fermi'.
    - cutoff_radius_z_ratio (float): fermi radius ratio on z axis.  Default is 0.9.
    - transition_width_z_ratio (float): fermi width ratio on z axis.  Default is 0.1.

    Returns:
    - ndarray: The Gaussian filter with shape (x), (x, y) or (x, y, z).
    '''

    if not isinstance(shape, tuple):
        raise ValueError("Matrix size must be a tuple")
    
    axes = [np.linspace(-dim/2, dim/2, dim) for dim in shape]
    grid = np.meshgrid(*axes, indexing='xy')
    pos = np.stack(grid, axis=-1)
    sigma = sigma_ratio * shape[0]
    if len(shape) == 3:
        if z_type == 'isotropic':
            pos = np.stack(grid, axis=-1)
            filter = np.exp(-np.sum(pos**2, axis=-1) / (2*sigma**2))
        if z_type == 'fermi':
            radius_z = cutoff_radius_z_ratio*shape[-1]
            width_z = transition_width_z_ratio*shape[-1]
            filter = np.exp(-np.sum(pos[...,0:2]**2, axis=-1) / (2*sigma**2))
            filter_z_1d = 1/(1+np.exp((np.abs(grid[-1])-radius_z)/width_z))
            filter = filter * filter_z_1d
        elif z_type == 'same':
            filter = np.exp(-np.sum(pos[..., :2]**2, axis=-1) / (2*sigma**2))
    elif len(shape) == 2 or len(shape) == 1:
        filter = np.exp(-np.sum(pos**2, axis=-1) / (2*sigma**2))
    else:
        raise ValueError("Invalid shape dimension: shape must be either 1D, 2D or 3D")

    filter = filter / filter.max()
    return filter

def fermi_filter(shape, cutoff_radius_ratio=0.5, transition_width_ratio=0.1, z_type='fermi', cutoff_radius_z_ratio=0.9, transition_width_z_ratio=0.1):
    '''
    Create a Fermi filter for k-space data.
    
    Parameters:
    - shape (tuple): Shape of the filter with length 1 or 2 or 3, in the form (x), (x, y) or (x, y, z).
    - cutoff_radius_ratio (float): Cutoff radius of the Fermi filter, ranging from 0 to 1. Default is 0.5.
    - transition_width_ratio (float): Width of the transition band, controlling the sharpness of the Fermi filter. Default is 0.1.
    - z_type (str): Specifies the type of filter in the z-direction ('isotropic', 'fermi' or 'same'). Default is 'fermi'.
    - cutoff_radius_z_ratio (float): fermi radius ratio on z axis.  Default is 0.9.
    - transition_width_z_ratio (float): fermi width ratio on z axis.  Default is 0.1.

    Returns:
    - ndarray: The Fermi filter with shape (x, y, z).
    '''
    if not isinstance(shape, tuple):
        raise ValueError("Matrix size must be a tuple")
    radius = cutoff_radius_ratio*shape[0]
    width = transition_width_ratio*shape[-1]
    axes = [np.linspace(-dim/2, dim/2, dim) for dim in shape]
    grid = np.meshgrid(*axes, indexing='xy')
    pos = np.stack(grid, axis=-1)
    if len(shape) == 3:
        if z_type=='isotropic': # 3D isotropic Fermi filter
            filter = 1/(1+np.exp((np.linalg.norm(pos, axis=-1)-radius)/width))
        elif z_type=='fermi': # 2D Fermi filter on each slice with 1d Fermi filter on z axis
            radius_z = cutoff_radius_z_ratio*shape[-1]
            width_z = transition_width_z_ratio*shape[-1]
            filter = 1/(1+np.exp((np.linalg.norm(pos[...,0:2], axis=-1)-radius)/width))
            filter_z_1d = 1/(1+np.exp((np.abs(grid[-1])-radius_z)/width_z))
            filter = filter * filter_z_1d
        elif z_type=='same': # 2D Fermi filter on each slice
            filter = 1/(1+np.exp((np.linalg.norm(pos[...,0:2], axis=-1)-radius)/width))

    elif len(shape)==2 or len(shape) == 1:
        filter = 1/(1+np.exp((np.linalg.norm(pos, axis=-1)-radius)/(width)))
    else:
        raise ValueError("Invalid shape dimension: shape must be either 1D, 2D or 3D")
    
    filter = filter/filter.max()
    return filter

def sine_bell_filter(shape, z_type='fermi', cutoff_radius_z_ratio=0.9, transition_width_z_ratio=0.1):
    '''
    Create a sine bell filter.
    
    Parameters:
    - shape (tuple): Shape of the filter with length 1 or 2 or 3, in the form (x), (x, y) or (x, y, z).
    - z_type (str): Specifies the type of filter in the z-direction ('isotropic', 'fermi' or 'same'). Default is 'fermi'.
    - cutoff_radius_z_ratio (float): fermi radius ratio on z axis.  Default is 0.9.
    - transition_width_z_ratio (float): fermi width ratio on z axis.  Default is 0.1.    
    Returns:
    - ndarray: The sine bell filter with shape (x, y, z).
    '''
    if not isinstance(shape, tuple):
        raise ValueError("Matrix size must be a tuple of length 2 or 3.")
    axes = [np.linspace(0, np.pi, dim) for dim in shape]
    grid = np.meshgrid(*axes, indexing='xy')
    if len(shape) == 3:
        if z_type=='isotropic': # 3D isotropic sine bell filter
            filter = np.sin(grid[0])**2*np.sin(grid[1])**2*np.sin(grid[2])**2
        elif z_type=='fermi':  # 2D sine bell filter on each slice with 1d Fermi filter on z axis
            radius_z = cutoff_radius_z_ratio*shape[-1]
            width_z = transition_width_z_ratio*shape[-1]
            filter = np.sin(grid[0])**2*np.sin(grid[1])**2
            gridz = (grid[-1]/np.pi-0.5)*shape[-1]
            filter_z_1d = 1/(1+np.exp((np.abs(gridz)-radius_z)/width_z))
            filter = filter * filter_z_1d
        elif z_type=='same': # 2D sine bell filter on each slice
            filter = np.sin(grid[0])**2*np.sin(grid[1])**2
    elif len(shape)==2:
            # Calculate 2D sine-bell filter
            filter = np.sin(grid[0])**2*np.sin(grid[1])**2 
    elif len(shape)==1:
            # Calculate 1D sine-bell filter
            filter = np.sin(grid[0])**2
    else:
        raise ValueError("Invalid shape dimension: shape must be either 1D, 2D or 3D")
    
    filter = filter/filter.max()
    return filter




