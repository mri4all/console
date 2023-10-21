import numpy as np

def grad_delay_correction(kData, kTraj, delayT, param):
    ## JChen
    ## 10.20.2023
    # to be passed by imaging parameters
    # kData.shape = kx, ky, kz
    # kTraj pe table, numPE x (pe_y, pe_z)
    etLength = param.etLength
    BW_px = param.BW
    baseResolution = param.baseResolution
    numPE = kTraj.shape[0]
    Ns = kData.shape[0]

    if Ns%2:
        nx = np.arange(-Ns//2,Ns//2+1,1)
    else:
        nx = np.arange(-Ns//2,Ns//2,1) 

    T_PE = baseResolution/BW_px
    for L in range(etLength):
        idx_trj = np.arange(L, etLength, numPE)
        phi = 2 * np.pi * (delayT + T_PE*L) * nx
        tmp = kData[:,kTraj[idx_trj,0], kTraj[idx_trj,1]]
        kData[:,kTraj[idx_trj,0], kTraj[idx_trj,1]] \
            =np.fft.fft(np.fft.ifft(tmp) * np.exp(1j * phi))  ## check dim 
        
    return kData