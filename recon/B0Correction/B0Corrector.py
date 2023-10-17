import numpy as np
import OCTOPUS as oc
from typing import Optional, Any, Mapping

import recon_utils

class B0Corrector():
    '''
    B0 trajectory correction for reconstruction calling from OCTOPUS.
    
    https://github.com/imr-framework/OCTOPUS/tree/master
    '''
    def __init__(self, 
                 Y: np.ndarray, 
                 kt: np.ndarray, 
                 df: np.ndarray, 
                 nonCart: Optional[bool]=None, 
                 params: Optional[Mapping[str, Any]]=None):
        
        self.Y = Y  # raw k-space (rads)
        self.kt = kt  # k-space trajectory, acq times for each frequency encode (s) 
        self.df = df  # delta B0field map (Hz) 
        self.nonCart = nonCart # non-Cartesian trajectory?
        self.params = params  # parameters for B0 correction
        
        if self.params is not None:
            keys = ['Npoints', 'Nshots', 'N', 'dcf', 't_vector', 't_readout']
            for key in keys:
                if key not in self.params.keys():
                    raise ValueError(f"Key {key} not found in params")
                    
    def __call__(self) -> np.ndarray:
        return self.correct_MFI()  # default method
    
    def correct_Cartesian_basic(self) -> np.ndarray: 
        '''
        Doc from OCTOPUS for Cartesian off-resonance correction:
        
        Off-resonance correction for Cartesian trajectories

        Parameters
        ----------
        M : numpy.ndarray
            Cartesian image data
        kt : numpy.ndarray
            Cartesian k-space trajectory
        df : numpy.ndarray
            Field map

        Returns
        -------
        M_hat : numpy.ndarray
            Off-resonance corrected image data
        '''
        return oc.orc(recon_utils.centered_ifft2(self.Y), self.kt, self.df)  # expects image domain
    
    def correct_MFI(self) -> np.ndarray: 
        '''
        Doc from OCTOPUS for MFI: 
        
        Off-resonance Correction by Multi-Frequency Interpolation
        Man, L., Pauly, J. M. and Macovski, A. (1997), Multifrequency interpolation for fast off‐resonance correction. Magn. Reson. Med., 37: 785-792. doi:10.1002/mrm.1910370523

        Parameters
        ----------
        dataIn : numpy.ndarray
            k-space raw data or image data
        dataInType : str
            Can be either 'raw' or 'im'
        kt : numpy.ndarray
            k-space trajectory
        df : numpy.ndarray
            Field map
        Lx : int
            L (frequency bins) factor
        nonCart : int
            Non-cartesian trajectory option. Default is None (Cartesian).
        params : dict
            Sequence parameters. Default is None.
        Returns
        -------
        M_hat : numpy.ndarray
            Corrected image data.
        '''
        return oc.MFI(self.Y, 'raw', self.kt, self.df, Lx=1, nonCart=self.nonCart, params=self.params) 