import numpy as np
import matplotlib.pyplot as plt

kData = np.load('/vagrant/kspace.npy')
data = np.fft.fft(np.fft.fft(np.fft.fftshift(kData,axes=0), axis=0), axis=1)

plt.imshow(abs(data), vmin=0, vmax=1)
plt.colorbar()
plt.savefig('kData.png')