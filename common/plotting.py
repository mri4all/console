import matplotlib.pyplot as plt


def set_plotting_defaults():
    plt.style.use("dark_background")
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    colors = ["#E0A526"] + colors
    plt.rcParams["axes.prop_cycle"] = plt.cycler(color=colors)
    plt.tight_layout()
