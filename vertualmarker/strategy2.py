from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional

from .geometry import (
    Point,
    Segment,
    build_segments,
    distance,
    polyline_length,
    find_closest_point_on_polyline,
    sample_along_polyline,
)


@dataclass
class Strategy2Config:
    FH: float  # Forehead vertical length threshold
    UH: float  # Upper head horizontal length threshold
    SX: float  # Shift in x for virtual marker
    SY: float  # Shift in y for virtual marker
    PBL: int   # Panel bending length (treated as number of output points)
    # 각도 및 샘플링 정밀도 파라미터
    vertical_angle_tol_deg: float = 5.0   # 세로 구간 판정 각도 허용치(도)
    horizontal_angle_tol_deg: float = 5.0  # 가로 구간 판정 각도 허용치(도)
    sample_step: float = 1.0  # BSP에서 따라갈 때 포인트 간 거리(픽셀)


@dataclass
class Strategy2Result:
    tlsp: Point
    turtle_line_points: List[Point]
    front_head_segment: Segment
    upper_head_segment: Segment
    mv: Point
    mv_shifted: Point
    bsp: Point
    bending_points: List[Point]  # points with indices 1..PBL


class Strategy2Error(Exception):
    """Domain-specific error for Strategy 2 processing."""


def parse_txt_points(path: str) -> List[List[Point]]:
    """Parse TXT file into list of polylines.

    Assumptions:
    - Each line is either:
        x y
      or
        x,y
      where x, y are float or integer.
    - Empty lines separate different polylines.
    """
    polylines: List[List[Point]] = []
    current: List[Point] = []

    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                if current:
                    polylines.append(current)
                    current = []
                continue

            # Split by comma or whitespace
            if "," in line:
                parts = line.split(",")
            else:
                parts = line.split()
            if len(parts) < 2:
                continue
            try:
                x = float(parts[0])
                y = float(parts[1])
            except ValueError:
                continue
            current.append((x, y))

    if current:
        polylines.append(current)

    if not polylines:
        raise Strategy2Error("입력 txt 파일에서 좌표를 찾을 수 없습니다.")

    return polylines


def pick_two_longest_polylines(polylines: List[List[Point]]) -> Tuple[List[Point], List[Point]]:
    if len(polylines) < 2:
        raise Strategy2Error("최소 두 개의 연결된 선(폴리라인)이 필요합니다.")

    lengths = [(polyline_length(pl), i) for i, pl in enumerate(polylines)]
    lengths.sort(reverse=True)  # longest first
    idx1 = lengths[0][1]
    idx2 = lengths[1][1]
    return polylines[idx1], polylines[idx2]


def find_turtle_line(pl1: List[Point], pl2: List[Point]) -> List[Point]:
    """Find turtle line as polyline containing the lowest point in y."""
    all_points = [(p, 1) for p in pl1] + [(p, 2) for p in pl2]
    # In image coordinates, y가 클수록 아래라고 가정
    lowest_point, which = max(all_points, key=lambda t: t[0][1])
    return pl1 if which == 1 else pl2


def orient_turtle_line(points: List[Point]) -> Tuple[List[Point], Point]:
    """Ensure TLSP (lower endpoint) is the first point.

    Returns oriented points and TLSP.
    """
    if len(points) < 2:
        raise Strategy2Error("거북이 선에 최소 두 개의 점이 필요합니다.")

    p_start, p_end = points[0], points[-1]
    # 아래쪽(endpoints with larger y)
    if p_start[1] >= p_end[1]:
        tlsp = p_start
        oriented = points
    else:
        tlsp = p_end
        oriented = list(reversed(points))

    return oriented, tlsp


def find_first_vertical_segment(
    segments: List[Segment], fh: float, angle_tol_deg: float
) -> Segment:
    """Find first vertical segment with length >= FH."""
    import math

    max_sin = math.sin(math.radians(angle_tol_deg))

    for seg in segments:
        if seg.length < fh:
            continue
        # vertical if dx is small relative to length
        if abs(seg.dx) / max(seg.length, 1e-9) <= max_sin:
            return seg
    raise Strategy2Error("조건을 만족하는 세로(FH) 구간을 찾지 못했습니다.")


def find_first_horizontal_segment(
    segments: List[Segment], uh: float, angle_tol_deg: float
) -> Segment:
    """Find first horizontal segment with length >= UH."""
    import math

    max_sin = math.sin(math.radians(angle_tol_deg))

    for seg in segments:
        if seg.length < uh:
            continue
        # horizontal if dy is small relative to length
        if abs(seg.dy) / max(seg.length, 1e-9) <= max_sin:
            return seg
    raise Strategy2Error("조건을 만족하는 가로(UH) 구간을 찾지 못했습니다.")


def compute_mv(front_head: Segment, upper_head: Segment) -> Point:
    """Compute virtual marker Mv from:
    - x: average x of front head vertical segment
    - y: average y of upper head horizontal segment
    """
    x_v = (front_head.start[0] + front_head.end[0]) / 2.0
    y_h = (upper_head.start[1] + upper_head.end[1]) / 2.0
    return (x_v, y_h)


def run_strategy2_on_points(
    polylines: List[List[Point]], config: Strategy2Config
) -> Strategy2Result:
    # 1. pick two longest polylines
    pl1, pl2 = pick_two_longest_polylines(polylines)

    # 2 & 3. find turtle line
    turtle = find_turtle_line(pl1, pl2)

    # 4. orient turtle line so TLSP is first point
    turtle_oriented, tlsp = orient_turtle_line(turtle)

    # 5 & 6. find front head and upper head segments
    all_segments = build_segments(turtle_oriented)
    front_head = find_first_vertical_segment(
        all_segments, config.FH, config.vertical_angle_tol_deg
    )

    # For "계속 선을 읽어나간다" we only search AFTER the front_head segment
    try:
        start_idx = all_segments.index(front_head) + 1
    except ValueError:
        start_idx = 0
    upper_head = find_first_horizontal_segment(
        all_segments[start_idx:], config.UH, config.horizontal_angle_tol_deg
    )

    # 7. compute virtual marker Mv
    mv = compute_mv(front_head, upper_head)

    # 8. shifted marker and BSP
    mv_shifted = (mv[0] + config.SX, mv[1] + config.SY)
    bsp = find_closest_point_on_polyline(turtle_oriented, mv_shifted)

    # Determine direction on turtle line
    # TLSP가 0번 인덱스가 되도록 정렬했으므로,
    # "TLSP로 이어지는 방향의 반대 방향"은 항상 인덱스가 증가하는 방향으로 본다.
    bsp_index = turtle_oriented.index(bsp)
    forward = True  # 항상 TLSP에서 멀어지는 방향(인덱스 증가)

    bending_points = sample_along_polyline(
        turtle_oriented,
        start_index=bsp_index,
        num_samples=config.PBL,
        step=max(config.sample_step, 1e-3),
        forward=forward,
    )

    return Strategy2Result(
        tlsp=tlsp,
        turtle_line_points=turtle_oriented,
        front_head_segment=front_head,
        upper_head_segment=upper_head,
        mv=mv,
        mv_shifted=mv_shifted,
        bsp=bsp,
        bending_points=bending_points,
    )


def run_strategy2_on_file(path: str, config: Strategy2Config) -> Strategy2Result:
    polylines = parse_txt_points(path)
    return run_strategy2_on_points(polylines, config)


def save_result_points_txt(path: str, result: Strategy2Result) -> None:
    """Save bending points as TXT: index x y."""
    with open(path, "w", encoding="utf-8") as f:
        f.write("# index x y\n")
        for idx, p in enumerate(result.bending_points, start=1):
            f.write(f"{idx} {p[0]:.6f} {p[1]:.6f}\n")

