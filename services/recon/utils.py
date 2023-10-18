import numpy as np

def center_kspace(kspace):
    '''
    Identify the maximum value in the k-space matrix and adjust the matrix via rolling operations to position this maximum value at the center.
    Input: kspace, shape (x,y,z)
    Output: centered kspace, shape (x,y,z)
    '''
    index_max = np.argmax(np.abs(kspace))
    max_index_2d = np.unravel_index(index_max, kspace.shape)
    h,w,z = kspace.shape
    move_h = h//2 - max_index_2d[0]
    move_w = w//2 - max_index_2d[1]
    kspace = np.roll(kspace, (move_h,move_w,0),axis=(0,1,2))
    return kspace