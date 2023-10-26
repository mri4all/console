import numpy as np
import matplotlib.pyplot as plt


def imshow(img, vmin=None, vmax=None, fig=None, figsize=(5,5), title=None, colorbar=False):
    if fig is None:
        fig = plt.figure(figsize=figsize)
    plt.imshow(img, cmap='gray', vmin=vmin, vmax=vmax)
    plt.axis('off');
    if title:
        plt.title(title)
    if colorbar: 
        plt.colorbar()
    return None

def show_mag_image(img):
    imshow(abs(img), title='Magnitude')

def show_phase_image(img):
    imshow(np.angle(img), vmin=-np.pi, vmax=np.pi, title='Phase')