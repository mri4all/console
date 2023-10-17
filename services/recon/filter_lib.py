import numpy as np

class filter_lib():
    
    def kFilter_circleFermi2D(matrix_size, rr, ww):
        """ 
        a kspace fermi filter mask 2D
        JC
        for default choice
            rr = 0.9 radius
            ww = 0.03 width
        """
        nx, ny = matrix_size
        mask = np.zeros((nx, ny))
        xv, yv = np.meshgrid(np.linspace(-1,1,nx),np.linspace(-1,1,ny) )
        for indx in range(nx):
            for indy in range(ny):
                rv = np.sqrt(xv[indx, indy]**2+ yv[indx, indy]**2)
                mask[indx, indy] = 1/(1+np.exp((rv-rr)/ww))
        
        return mask
    
    def kFilter_circleFermi3D(matrix_size, rr, wwx, wwz):
        
        pass
        