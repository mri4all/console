
# import numpy as np
import matplotlib.pyplot as plt
from kspaceFiltering.kspace_filtering import *
from recon_utils.imaging import *
import numpy as np

kData = np.load('/vagrant/test_data_kspace_d1s1.npy')
kTraj = np.genfromtxt(r"/vagrant/trajectory.csv", delimiter=",")  # pe_table a lot by 2 # check rotation
iData0 = np.fft.ifftshift(np.fft.ifftn(kData), axes=[0,1,2])

delayT = 8e-6 # in us
Ns = kData.shape[0]

etLength = 4
BW = 40e3 # 40kHz
ESP = 1e-6*20e3 #us 
T_PE = 1/BW

if Ns%2:
    nx = np.arange(-Ns//2+1,Ns//2+1,1)/Ns
else:
    nx = np.arange(-Ns//2,Ns//2,1)/Ns 
    
for L in range(etLength):
    coords1 =  np.where(kTraj % etLength == L)[1] #ny
    coords2 = np.where(kTraj % etLength == L)[0] #nz
    # idx_trj = np.arange(L, etLength, numPE)
    # phi = 2 * np.pi * nx  * (delayT + ESP - Ns*T_PE/2) * L
    phi = 2 * np.pi * nx  * delayT * BW  * (L + 1)

    tmp = kData[:,coords1, coords2]
    kData[:,coords1, coords2] \
        =np.fft.fft(np.fft.ifft(tmp, axis=0) *  np.fft.fftshift(np.exp(-1j * phi)[:,None], axes=0), axis=0)  ## check dim 

#kData = kFilter(kData, 'fermi', center_correction=True)

iData = np.fft.ifftshift(np.fft.ifftn(kData), axes=[0,1,2])
plt.figure()
plt.imshow(abs(iData0[:,:,18])-abs(iData[:,:,18]))
plt.colorbar()
plt.savefig('iKData_DelayCorr_diff.png')
plt.close()

plt.figure()
plt.imshow(abs(iData[:,:,18]), vmin=0, vmax=0.003)
plt.colorbar()
plt.savefig('iKData_corr.png')
plt.close()

