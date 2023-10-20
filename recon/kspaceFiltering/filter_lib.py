import numpy as np

def fermi_filter(shape, cutoff_radius_ratio=0.5, transition_width=10, isotropic=False):
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
    
    if isotropic: # 3D isotropic Fermi filter
        axes = [np.linspace(-dim/2, dim/2, dim) for dim in shape]
        grid = np.meshgrid(*axes, indexing='xy')
        pos = np.stack(grid, axis=-1)
        filter = 1/(1+np.exp((np.linalg.norm(pos, axis=-1)-cutoff_radius_ratio*shape[0])/transition_width))
    else: # 2D Fermi filter on each slice
        axes = [np.linspace(-dim/2, dim/2, dim) for dim in shape[0:2]]
        grid = np.meshgrid(*axes, indexing='xy')
        pos = np.stack(grid, axis=-1)
        filter = 1/(1+np.exp((np.linalg.norm(pos, axis=-1)-cutoff_radius_ratio*shape[0])/transition_width))
        filter = np.repeat(filter[:,:,None], shape[2], axis=2)
    return filter

def sine_bell_filter(shape, isotropic=False):
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
    
    if isotropic: # 3D isotropic sine bell filter
        axes = [np.linspace(0, np.pi, dim) for dim in shape]
        grid = np.meshgrid(*axes, indexing='xy')
        filter = np.sin(grid[0])*np.sin(grid[1])*np.sin(grid[2])

    else: # 2D sine bell filter on each slice
        axes = [np.linspace(0, np.pi, dim) for dim in shape[0:2]]
        grid = np.meshgrid(*axes, indexing='xy')
        
        # Calculate 2D sine-bell filter
        filter = np.sin(grid[0])*np.sin(grid[1])
        # repeat the 2D filter to 3D
        filter = np.repeat(filter[:,:,None], shape[2], axis=2)
    return filter