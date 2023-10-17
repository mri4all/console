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
        for indx in range(nx):
            for indy in range(ny):
                rv = xv[indx, indy]**2+ yv[indx, indy]**2
                mask[indx, indy] = 1/(1+np.exp((rv-ww)/rr))
        
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
        for indx in range(nx):
            for indy in range(ny):
                mask[indx, indy] = 1/(1+np.exp((xv[indx, indy]**2-wwx)/rr))
                mask[indx, indy] = min(mask[indx, indy],1/(1+np.exp((yv[indx, indy]**2-wwy)/rr)))
        
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
        xv, yv, yz = np.meshgrid(np.linspace(-1,1,nx),np.linspace(-1,1,ny), np.linspace(-1,1,nz) )
        for indx in range(nx):
            for indy in range(ny):
                for indz in range(nz):
                    rv = xv[indx, indy,indz]**2+ yv[indx, indy,indz]**2
                    mask[indx, indy, indz] = 1/(1+np.exp((rv-ww)/rr))
                    mask[indx, indy, indz] = min(mask[indx, indy, indz], 1/(1+np.exp((zv[indx, indy, indz]**2-wwz)/rr)))

        return mask
        
    def sine_bell_filter2D(matrix_size, a=1):
        
        """ 
        a kspace sine bell filter mask 2D
        JC
        """
        mask_1 = np.sin(np.pi * a * np.arange(matrix_size[0])/matrix_size[0])
        mask_2 = np.sin(np.pi * a * np.arange(matrix_size[1])/matrix_size[1])

        return np.outer(mask_1,mask_2)
        