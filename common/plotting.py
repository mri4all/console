import matplotlib.pyplot as plt


def set_plotting_defaults():
    plt.style.use("dark_background")
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    colors = ["#E0A526"] + colors
    plt.rcParams["axes.prop_cycle"] = plt.cycler(color=colors)
    plt.rcParams["lines.linewidth"] = 1.0
    plt.rcParams["figure.autolayout"] = True
    plt.tight_layout()
