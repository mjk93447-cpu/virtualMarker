"""Visualization module for Strategy 2 results."""
from typing import List, Tuple

import matplotlib.pyplot as plt

from .geometry import Point, distance
from .strategy2 import Strategy2Result


def _annotation_offsets_for_key_points(result: Strategy2Result) -> dict[str, Tuple[int, int]]:
    """Return label offsets while avoiding overlap for nearby key points."""
    offsets: dict[str, Tuple[int, int]] = {
        "TLSP": (6, -10),
        "BSP": (6, 8),
        "Mv": (7, -8),
        "Mv'": (7, 8),
    }
    # Prevent Mv' and BSP label collision when points are almost overlapping
    if distance(result.mv_shifted, result.bsp) < 10.0:
        offsets["BSP"] = (14, 16)
        offsets["Mv'"] = (-34, -16)
    return offsets


def visualize_result(
    original_points: List[Point],
    result: Strategy2Result,
    out_path: str,
) -> None:
    """Visualize turtle-line result, diagnostics and indexed path."""
    fig, ax = plt.subplots(figsize=(10, 8))

    # Base edge map points (background)
    if original_points:
        ox = [p[0] for p in original_points]
        oy = [p[1] for p in original_points]
        ax.scatter(
            ox,
            oy,
            color="#BDBDBD",
            s=0.8,
            alpha=0.22,
            linewidths=0.0,
            label="Original edge points",
            zorder=1,
        )

    # Longest connected components (input-faithful view in gray)
    for idx, comp in enumerate(result.longest_two_components):
        if not comp:
            continue
        cx = [p[0] for p in comp]
        cy = [p[1] for p in comp]
        ax.scatter(
            cx,
            cy,
            color="#8E939C",
            s=2.0,
            alpha=0.72,
            linewidths=0.0,
            label="Longest lines (raw)" if idx == 0 else None,
            zorder=2,
        )

    # Turtle line highlight
    tl = result.turtle_line_path
    if len(tl) >= 2:
        xs = [p[0] for p in tl]
        ys = [p[1] for p in tl]
        ax.plot(
            xs,
            ys,
            color="#1F77B4",
            linewidth=0.85,
            label="Turtle line",
            alpha=0.95,
            zorder=3,
        )

    # Indexed bending trajectory
    if result.bending_points:
        bx = [p[0] for p in result.bending_points]
        by = [p[1] for p in result.bending_points]
        indices = list(range(1, len(result.bending_points) + 1))
        sc = ax.scatter(
            bx,
            by,
            c=indices,
            cmap="turbo",
            s=8,
            label="Bending points (1..PBL)",
            linewidths=0.0,
            zorder=5,
        )
        cbar = fig.colorbar(sc, ax=ax)
        cbar.set_label("Bending index")

    offsets = _annotation_offsets_for_key_points(result)

    # Key points
    ax.scatter(
        [result.tlsp[0]],
        [result.tlsp[1]],
        color="#D62728",
        s=62,
        marker="v",
        label="TLSP",
        zorder=10,
        edgecolors="white",
        linewidths=0.8,
    )
    ax.annotate(
        "TLSP",
        xy=result.tlsp,
        xytext=offsets["TLSP"],
        textcoords="offset points",
        fontsize=8,
        color="#D62728",
        weight="bold",
    )

    ax.scatter(
        [result.bsp[0]],
        [result.bsp[1]],
        color="#FF7F0E",
        s=62,
        marker="D",
        label="BSP",
        zorder=10,
        edgecolors="white",
        linewidths=0.8,
    )
    ax.annotate(
        "BSP",
        xy=result.bsp,
        xytext=offsets["BSP"],
        textcoords="offset points",
        fontsize=8,
        color="#FF7F0E",
        weight="bold",
    )

    ax.scatter(
        [result.mv[0]],
        [result.mv[1]],
        color="#9467BD",
        s=58,
        marker="P",
        label="Mv",
        zorder=10,
        edgecolors="white",
        linewidths=0.8,
    )
    ax.annotate(
        "Mv",
        xy=result.mv,
        xytext=offsets["Mv"],
        textcoords="offset points",
        fontsize=8,
        color="#9467BD",
        weight="bold",
    )

    ax.scatter(
        [result.mv_shifted[0]],
        [result.mv_shifted[1]],
        color="#E377C2",
        s=54,
        marker="x",
        label="Mv shifted",
        zorder=10,
        linewidths=1.2,
    )
    ax.annotate(
        "Mv'",
        xy=result.mv_shifted,
        xytext=offsets["Mv'"],
        textcoords="offset points",
        fontsize=8,
        color="#E377C2",
        weight="bold",
    )

    # FH / UH detected runs
    if result.front_head_run:
        fh_x = [p[0] for p in result.front_head_run]
        fh_y = [p[1] for p in result.front_head_run]
        ax.plot(
            fh_x,
            fh_y,
            color="#2CA02C",
            linewidth=1.25,
            label="Front head (FH)",
            zorder=8,
        )

    if result.upper_head_run:
        uh_x = [p[0] for p in result.upper_head_run]
        uh_y = [p[1] for p in result.upper_head_run]
        ax.plot(
            uh_x,
            uh_y,
            color="#8C564B",
            linewidth=1.25,
            label="Upper head (UH)",
            zorder=8,
        )

    # Critical issue markers
    critical_points = [
        d.point for d in result.diagnostics if d.severity == "critical" and d.point is not None
    ]
    if critical_points:
        ix = [p[0] for p in critical_points]
        iy = [p[1] for p in critical_points]
        ax.scatter(
            ix,
            iy,
            color="#FF2D2D",
            s=80,
            marker="X",
            edgecolors="white",
            linewidths=0.8,
            zorder=12,
            label="Critical issue point",
        )

    ax.set_aspect("equal", adjustable="datalim")
    ax.invert_yaxis()  # 이미지 좌표계 (y가 아래로 증가)
    ax.set_xlabel("X (pixel)")
    ax.set_ylabel("Y (pixel)")
    ax.set_title("Strategy 2 - Turtle Line, Longest Components, and Bending Trajectory")
    ax.legend(loc="best", fontsize=8, framealpha=0.9)
    ax.grid(True, alpha=0.15, linewidth=0.5)

    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
