import numpy as np

def grad_delay_correction(kData, kTraj, delayT, etLength, BW, ESP):
    ## JChen
    ## 10.20.2023
    # to be passed by imaging parameters
    # kData.shape = kx, ky, kz
    # kTraj pe table, numPE x (pe_y, pe_z)
    # BW # Hz
    # ESP # sec
    
    numPE = kTraj.shape[0]
    Ns = kData.shape[0]

    T_PE =1/BW
    
    if Ns%2:
        nx = np.arange(-Ns//2+1,Ns//2+1,1)/Ns
    else:
        nx = np.arange(-Ns//2,Ns//2,1)/Ns   

    for L in range(etLength):
        idx_trj = np.arange(L, etLength, numPE)
        phi = 2 * np.pi * nx  * delayT * BW  * (L + 1)

        tmp = kData[:,kTraj[idx_trj,0], kTraj[idx_trj,1]]
        kData[:,kTraj[idx_trj,0], kTraj[idx_trj,1]] \
        = np.fft.fft(np.fft.ifft(tmp, axis=0) *  np.fft.fftshift(np.exp(-1j * phi)[:,None], axes=0), axis=0)
        
    return kData