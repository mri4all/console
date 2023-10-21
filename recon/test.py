
import numpy as np
import matplotlib.pyplot as plt
import kspaceFiltering.kspace_filtering as kFilter


kData = np.load('/vagrant/kspace.npy')[:,:,None]
print(kData.shape)
plt.imshow(abs(kData))
plt.savefig('absKData1.png')

kData = kFilter.kFilter(kData, 'fermi', center_correction=True)

plt.imshow(abs(kData))
plt.savefig('absKData2.png')



