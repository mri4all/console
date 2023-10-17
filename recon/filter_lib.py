import numpy as np

class filter_lib():
    
    def kFilter_circFermi2D(matrix_size, rr, ww):
        """ 
        a kspace fermi filter mask 2D
        JC
        for default choice
            ww = 0.7 radius
            rr = 0.05 width
        TODO: make it ratio
        """
        nx, ny = matrix_size
        mask = np.zeros((nx, ny))
        xv, yv = np.meshgrid(np.linspace(-1,1,nx),np.linspace(-1,1,ny) )

        rv = xv**2+ yv**2
        mask = 1/(1+np.exp((rv-ww)/rr))

        return mask
    
    def kFilter_cartFermi2D(matrix_size,  rr, wwx, wwy):
        """ 
        a kspace fermi filter mask 2D
        JC
        for default choice
            wwx = 0.7 window width
            wwy = 0.7 window width
            rr = 0.1
        TODO: make it ratio
        """
        nx, ny = matrix_size
        mask = np.zeros((nx, ny))
        xv, yv = np.meshgrid(np.linspace(-1,1,nx),np.linspace(-1,1,ny) )
        mask = 1/(1+np.exp((xv**2-wwx)/rr))
        mask = np.minimum(mask,1/(1+np.exp((yv**2-wwy)/rr)))

        return mask
    
    def kFilter_circFermi3D(matrix_size, rr, ww, wwz):
        
        """ 
        a kspace fermi filter mask 2D
        JC
        for default choice
            ww = 0.7 width
            rr = 0.05 radius
            wwz = 0.9 width
        TODO: make it ratio
        """
        nx, ny, nz = matrix_size
        mask = np.zeros((nx, ny, nz))
        xv, yv, zv = np.meshgrid(np.linspace(-1,1,nx),np.linspace(-1,1,ny), np.linspace(-1,1,nz) )

        rv = xv**2+ yv**2
        mask = 1/(1+np.exp((rv-ww)/rr))
        mask = np.mininum(mask, 1/(1+np.exp((zv**2-wwz)/rr)))

        return mask
        
    def sine_bell_filter2D(matrix_size, a=1):
        
        """ 
        a kspace sine bell filter mask 2D
        JC
        """
        mask_1 = np.sin(np.pi * a * np.arange(matrix_size[0])/matrix_size[0])
        mask_2 = np.sin(np.pi * a * np.arange(matrix_size[1])/matrix_size[1])

        return np.outer(mask_1,mask_2)

    def sine_bell_fermi3D(matrix_size, rr, wwz, a=1):
        
        """ 
        a kspace sine bell filter mask 2D
        JC
        """


        nx, ny, nz = matrix_size
        mask = np.zeros((nx, ny, nz))
        xv, yv, zv = np.meshgrid(np.linspace(-1,1,nx),np.linspace(-1,1,ny), np.linspace(-1,1,nz) )
        mask_1 = np.sin(np.pi * a * np.arange(matrix_size[0])/matrix_size[0])
        mask_2 = np.sin(np.pi * a * np.arange(matrix_size[1])/matrix_size[1])
        mask = np.outer(mask_1,mask_2)
        mask = np.mininum(np.repeat(mask[:,:,None],nz,axis=2), 1/(1+np.exp((zv**2-wwz)/rr)))

        return mask  
        