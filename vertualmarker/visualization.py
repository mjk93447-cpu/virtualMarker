from typing import List

import matplotlib.pyplot as plt

from .geometry import Point
from .strategy2 import Strategy2Result


def visualize_result(
    original_polylines: List[List[Point]],
    result: Strategy2Result,
    out_path: str,
) -> None:
    """Visualize turtle line and bending points.

    - Original polylines: plotted in light gray
    - Turtle line: plotted in blue
    - Bending points: colored by index
    - TLSP, BSP, Mv, Mv_shifted, front/upper head segments: highlighted
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    # All original polylines
    for pl in original_polylines:
        if len(pl) < 2:
            continue
        xs = [p[0] for p in pl]
        ys = [p[1] for p in pl]
        ax.plot(xs, ys, color="lightgray", linewidth=1, alpha=0.5)

    # Turtle line
    tl = result.turtle_line_points
    xs = [p[0] for p in tl]
    ys = [p[1] for p in tl]
    ax.plot(xs, ys, color="blue", linewidth=2, label="Turtle line")

    # Bending points with color by index
    bx = [p[0] for p in result.bending_points]
    by = [p[1] for p in result.bending_points]
    indices = list(range(1, len(result.bending_points) + 1))
    sc = ax.scatter(
        bx,
        by,
        c=indices,
        cmap="viridis",
        s=15,
        label="Bending points (index color)",
    )
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("Index")

    # Highlight key points
    ax.scatter(
        [result.tlsp[0]],
        [result.tlsp[1]],
        color="red",
        s=40,
        label="TLSP",
        zorder=5,
    )
    ax.scatter(
        [result.bsp[0]],
        [result.bsp[1]],
        color="orange",
        s=40,
        label="BSP",
        zorder=5,
    )
    ax.scatter(
        [result.mv[0]],
        [result.mv[1]],
        color="purple",
        s=40,
        label="Mv",
        zorder=5,
    )
    ax.scatter(
        [result.mv_shifted[0]],
        [result.mv_shifted[1]],
        color="magenta",
        s=40,
        label="Mv shifted",
        zorder=5,
    )

    # Front head segment
    fh = result.front_head_segment
    ax.plot(
        [fh.start[0], fh.end[0]],
        [fh.start[1], fh.end[1]],
        color="green",
        linewidth=2,
        label="Front head",
    )

    # Upper head segment
    uh = result.upper_head_segment
    ax.plot(
        [uh.start[0], uh.end[0]],
        [uh.start[1], uh.end[1]],
        color="brown",
        linewidth=2,
        label="Upper head",
    )

    ax.set_aspect("equal", adjustable="datalim")
    ax.invert_yaxis()  # 이미지 좌표계(y가 아래로 증가) 가정
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("Strategy 2 - Turtle Line & Bending Points")
    ax.legend(loc="best", fontsize=8)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)

