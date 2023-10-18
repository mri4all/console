import numpy as np

def fermi_filter(shape, cutoff_radius_ratio=0.5, transition_width=10, is_3d=False):
    '''
    Create a Fermi filter.
    Input: shape, tuple, shape of the filter
           cutoff_radius, float, cutoff_radius of the Fermi filter, range within 0~1.
           transition_width, float, width of the transition band, controls the sharpness of the Fermi filter
           is_3d, bool, whether to apply the filter in 3D or 2D

    Output: filter, shape (x,y,z)
    '''
    if is_3d: # spherical Fermi filter
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

def sine_bell_filter(shape, cutoff_radius_ratio=0.5, is_3d=False):
    '''
    Create a sine bell filter.
    Input: shape, tuple, shape of the filter
           radius, float, radius of the sine bell filter. range 0~1
           sharpness, float, sharpness of the sine bell filter
    Output: filter, shape (x,y,z)
    '''
    if is_3d: # spherical sine bell filter
        axes = [np.linspace(-dim/2, dim/2, dim) for dim in shape]
        grid = np.meshgrid(*axes, indexing='xy')
        pos = np.stack(grid, axis=-1)
        filter = np.sin(np.pi*np.linalg.norm(pos, axis=-1)/(cutoff_radius_ratio*shape[0]))**2
    else: # 2D sine bell filter on each slice
        axes = [np.linspace(-dim/2, dim/2, dim) for dim in shape[0:2]]
        grid = np.meshgrid(*axes, indexing='xy')
        pos = np.stack(grid, axis=-1)
        filter = np.sin(np.pi*np.linalg.norm(pos, axis=-1)/(cutoff_radius_ratio*shape[0]))**2
        filter = np.repeat(filter[:,:,None], shape[2], axis=2)
    return filter

# def fermi_filter(shape, cutoff_radius = 0.5, transition_width = 10, cutoff_radius_z = 0.1, is_3d = True):
#     '''
#     Create a 3D Fermi filter.
#     Input: shape, tuple, shape of the filter
#            cutoff_radius, float, cutoff_radius of the Fermi filter, range within 0~1.
#            transition_width, float, width of the transition band, controls the sharpness of the Fermi filter
#     Output: filter, shape (x,y,z)
#     '''
#     axes = [np.linspace(-dim/2, dim/2, dim) for dim in shape]
#     # grid = np.meshgrid(*axes, indexing='xy')
#     xv,yv,zv = np.meshgrid(*axes, indexing='xy')
#     # 2D Fermi filter in the x-y plane
#     norm_xy = np.sqrt(xv**2 + yv**2)
#     # fermi_xy = 1 / (1 + np.exp((norm_xy - cutoff_radius) / transition_width))

#     # pos = np.stack([grid[0],grid[1]], axis=-1)
#     filter_xy = 1/(1+np.exp((norm_xy-cutoff_radius)/transition_width))
#     filter = np.minimum(filter_xy, 1/(1+np.exp((np.abs(zv)-cutoff_radius_z)/transition_width)))
#     # filter_z = 1/(1+np.exp((np.abs(zv)-cutoff_radius_z)/transition_width))
#     # filter = filter_xy * filter_z
                  

#     return filter

# def fermi_filter(shape, cutoff_radius = 0.5, transition_width = 10, cutoff_radius_z = 1, is_3d = True):
#     '''
#     Create a 3D Fermi filter.
#     Input: shape, tuple, shape of the filter
#            cutoff_radius, float, cutoff_radius of the Fermi filter, range within 0~1.
#            transition_width, float, width of the transition band, controls the sharpness of the Fermi filter
#     Output: filter, shape (x,y,z)
#     '''
#     axes = [np.linspace(-dim/2, dim/2, dim) for dim in shape]
#     # grid = np.meshgrid(*axes, indexing='xy')
#     xv,yv,zv = np.meshgrid(*axes, indexing='xy')
#     xv,yv,zv = np.meshgrid(*axes, indexing='xy')
#     # 2D Fermi filter in the x-y plane
#     norm_xy = np.sqrt(xv**2 + yv**2)
#     # fermi_xy = 1 / (1 + np.exp((norm_xy - cutoff_radius) / transition_width))

#     # pos = np.stack([grid[0],grid[1]], axis=-1)
#     filter_xy = 1/(1+np.exp((norm_xy-cutoff_radius)/transition_width))
#     print('debug: ', filter_xy.shape, zv.shape)
#     # filter = np.minimum(filter_xy, 1/(1+np.exp((np.abs(zv)-cutoff_radius_z)/transition_width)))
#     # filter_z = 1/(1+np.exp((np.abs(zv)-cutoff_radius_z)/transition_width))
#     # filter = filter_xy * filter_z
#     # filter = np.repeat(filter_xy[:,:,None], shape[2], axis=2)    

#     return filter