import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


BG = "#0b1220"
CARD = "#0f172a"
GRID = "#334155"
TEXT = "#e0ecff"
MUTED = "#94a3b8"
BLUE = "#60a5fa"
PURPLE = "#a78bfa"
GREEN = "#34d399"


def style_axis(ax):
    ax.set_facecolor(CARD)
    ax.tick_params(colors=MUTED)

    for spine in ax.spines.values():
        spine.set_color("#223252")

    ax.grid(True, alpha=0.22, color=GRID)


def style_legend(legend):
    legend.get_frame().set_facecolor(BG)
    legend.get_frame().set_edgecolor("#223252")
    legend.get_frame().set_linewidth(1.2)

    for text in legend.get_texts():
        text.set_color(TEXT)


def save_dark_plot(output_path, fig):
    plt.tight_layout(rect=[0, 0, 1, 0.88])
    plt.savefig(
        output_path,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
        dpi=140
    )
    plt.close()
    return output_path


def generate_quality_analysis_plot(qualities, psnr_values, ratio_values, output_path):
    fig, ax1 = plt.subplots(figsize=(9, 5), facecolor=BG)
    style_axis(ax1)

    ax1.plot(qualities, psnr_values, marker="o", linewidth=2.4,
             markersize=7, color=BLUE, label="PSNR")
    ax1.set_xlabel("JPEG Quality", color=MUTED)
    ax1.set_ylabel("PSNR (dB)", color=BLUE)

    ax2 = ax1.twinx()
    ax2.set_facecolor(CARD)
    ax2.tick_params(colors=MUTED)
    for spine in ax2.spines.values():
        spine.set_color("#223252")

    ax2.plot(qualities, ratio_values, marker="s", linewidth=2.4,
             markersize=7, color=PURPLE, label="Compression Ratio")
    ax2.set_ylabel("Compression Ratio", color=PURPLE)

    fig.suptitle("JPEG Quality Analysis", color=TEXT, fontsize=15, fontweight="bold")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()

    legend = ax1.legend(
        lines1 + lines2,
        labels1 + labels2,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.18),
        ncol=2,
        frameon=True,
        fontsize=10
    )
    style_legend(legend)

    return save_dark_plot(output_path, fig)


def generate_jpeg2000_analysis_plot(factors, psnr_values, bpp_values, output_path):
    fig, ax1 = plt.subplots(figsize=(9, 5), facecolor=BG)
    style_axis(ax1)

    ax1.plot(factors, psnr_values, marker="o", linewidth=2.4,
             markersize=7, color=BLUE, label="PSNR")
    ax1.set_xlabel("JPEG2000 Compression Factor", color=MUTED)
    ax1.set_ylabel("PSNR (dB)", color=BLUE)

    ax2 = ax1.twinx()
    ax2.set_facecolor(CARD)
    ax2.tick_params(colors=MUTED)
    for spine in ax2.spines.values():
        spine.set_color("#223252")

    ax2.plot(factors, bpp_values, marker="s", linewidth=2.4,
             markersize=7, color=GREEN, label="BPP")
    ax2.set_ylabel("BPP", color=GREEN)

    fig.suptitle("JPEG2000 Factor / BPP Analysis", color=TEXT, fontsize=15, fontweight="bold")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()

    legend = ax1.legend(
        lines1 + lines2,
        labels1 + labels2,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.18),
        ncol=2,
        frameon=True,
        fontsize=10
    )
    style_legend(legend)

    return save_dark_plot(output_path, fig)


def generate_comparison_plot(labels, psnr_values, ratio_values, output_path):
    x = np.arange(len(labels))
    width = 0.5

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), facecolor=BG)
    colors = [BLUE, PURPLE]

    axes[0].bar(x, psnr_values, width, color=colors)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels, color=MUTED)
    axes[0].set_xlabel("Compression Method", color=MUTED)
    axes[0].set_ylabel("PSNR (dB)", color=MUTED)
    axes[0].set_title("Image Quality", color=TEXT, fontsize=12, fontweight="bold")
    style_axis(axes[0])

    axes[1].bar(x, ratio_values, width, color=colors)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels, color=MUTED)
    axes[1].set_xlabel("Compression Method", color=MUTED)
    axes[1].set_ylabel("Compression Ratio", color=MUTED)
    axes[1].set_title("Compression Efficiency", color=TEXT, fontsize=12, fontweight="bold")
    style_axis(axes[1])

    for ax, values in zip(axes, [psnr_values, ratio_values]):
        for i, value in enumerate(values):
            ax.text(i, value, f"{value:.2f}", ha="center", va="bottom",
                    color=TEXT, fontsize=10, fontweight="bold")

    fig.suptitle("JPEG vs JPEG2000 Performance Comparison",
                 color=TEXT, fontsize=15, fontweight="bold")

    return save_dark_plot(output_path, fig)