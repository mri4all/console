from .filter_lib import *
from .kspace_filtering import *
from .utils import *



## for debugging filtering algorithm locally using the provided demo kspace data or image data
def debug_filter_on_demo_data(file_name, slc = 18, isimg=True, filter_type = 'fermi', **kwargs):
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec

    # 0.load demo data
    if isimg:
        img_arr = np.load(file_name)
        kspace = get_ksp_from_img(img_arr)
    else:
        kspace = np.load(file_name)
        img_arr = get_img_from_ksp(kspace)

    assert img_arr.ndim == 3, 'input image should be 3D'
    assert img_arr.shape[2]>slc, 'slice number out of range'

    # 2. center correction
    kspace_center = kspace_center_correction(kspace)
    # 3. filtering
    x,y,z = kspace_center.shape
    # kwg = { 'radius':x//2, 'sharpness':10}
    # kwg = { 'radius':0.5, 'sharpness':10}
    kspace_center_filtered, mask = kspace_filtering(kspace_center, filter_type, center_correction=False, return_mask=True, **kwargs)
    # 4. back to image
    output = get_img_from_ksp(kspace_center_filtered)
    # 5. compare the original image and the filtered image

    fig = plt.figure(figsize=(20, 6))
    gs = gridspec.GridSpec(1, 4, [1,1,1,3])  # 4 columns, the last one is twice as wide

    # First three subplots
    ax0 = plt.subplot(gs[0])
    ax0.imshow(np.abs(img_arr[:, :, slc]))
    ax0.set_title("Original")

    ax1 = plt.subplot(gs[1])
    ax1.imshow(np.abs(output[:, :, slc]))
    ax1.set_title("Output")

    ax2 = plt.subplot(gs[2])
    ax2.imshow(np.abs(np.abs(output[:, :, slc]) - np.abs(img_arr[:, :, slc])))
    ax2.set_title("Difference")

    # Last subplot
    ax3 = plt.subplot(gs[3])

    # Total number of slices and the number of slices to plot
    total_slices = 25
    slices_to_plot = 9

    # Calculate the spacing between slices
    slice_spacing = total_slices // (slices_to_plot - 1)  # Minus 1 to ensure you get the last slice

    ax3.set_ylim([0,1])
    # Loop through and plot the slices
    for i in range(slices_to_plot):
        slc = i * slice_spacing
        if slc < total_slices:
            ax3.plot(mask[:, 64, slc], label=f"Slice {slc}")
            

    # Add legend to the plot
    ax3.legend()

    # Set a title and labels for the axes
    ax3.set_title("Comparison of Different Slices")
    ax3.set_xlabel("X-axis")
    ax3.set_ylabel("Y-axis")

    # Show the plot
    plt.tight_layout()
    plt.show()