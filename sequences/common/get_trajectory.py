import numpy as np

def choose_pe_order(ndims: int = 3, npe: np.ndarray = [70, 28], traj: str = 'center_out',
                    save_pe_order: bool = True) -> np.ndarray:
    
    """
    Choose k-space trajectory for Cartesian acquisition: 2D or 3D.

    Parameters
    ----------
    ndims: number of encoding dimensions: two or three
    npe: number of phase encodes
    traj: view ordering 'center_out',
    save_pe_order: save to a numpy file with fixed name for now TODO: agree on the conventions

    Return
    ------
    pe_order: One or two dimension array containing phase encoding order
    """
    
    if ndims == 2:
        if traj == 'center_out':
            pe_order = np.zeros((npe, 1), dtype=int)
            pe_order[0] = 0
            for pe in range(1, npe):
                if np.mod(pe, 2) == 0:
                    pe_order[pe] = pe_order[pe - 1] - pe
                else:
                    pe_order[pe] = pe_order[pe - 1] + pe

    if ndims == 3:
        if traj == 'center_out':
            num_total_pe = np.prod(npe[0] * npe[1])
            pe_order = np.zeros((num_total_pe, 2), dtype=int)
            pe_order[0, 0] = 0  # First dimension
            pe_order[0, 1] = 0  # Second dimension
            pe = -1
            for pe1 in range(npe[0]):
                for pe2 in range(npe[1]):
                    pe += 1
                    if np.mod(pe1, 2) == 0:
                        pe_order[pe, 0] = pe_order[pe1 - 1, 0] - pe1
                    else:
                        pe_order[pe, 0] = pe_order[pe1 - 1, 0] + pe1

                    if np.mod(pe2, 2) == 0:
                        pe_order[pe, 1] = pe_order[pe2 - 1, 1] - pe2
                    else:
                        pe_order[pe, 1] = pe_order[pe2 - 1, 1] + pe2

    if save_pe_order is True:
        np.save('pe_order.npy', pe_order)

    print(pe_order)
    return pe_order


if __name__ == "__main__":
    ndims = 3
    Npe = [128, 128]
    traj = 'center_out'
    choose_pe_order(ndims=ndims, npe=Npe, traj=traj, save_pe_order=True)
