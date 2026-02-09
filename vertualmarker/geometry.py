import math
from dataclasses import dataclass
from typing import List, Tuple


Point = Tuple[float, float]


@dataclass
class Segment:
    start: Point
    end: Point

    @property
    def dx(self) -> float:
        return self.end[0] - self.start[0]

    @property
    def dy(self) -> float:
        return self.end[1] - self.start[1]

    @property
    def length(self) -> float:
        return math.hypot(self.dx, self.dy)


def distance(p1: Point, p2: Point) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def polyline_length(points: List[Point]) -> float:
    if len(points) < 2:
        return 0.0
    return sum(
        distance(points[i], points[i + 1]) for i in range(len(points) - 1)
    )


def build_segments(points: List[Point]) -> List[Segment]:
    return [
        Segment(points[i], points[i + 1])
        for i in range(len(points) - 1)
    ]


def find_closest_point_on_polyline(points: List[Point], target: Point) -> Point:
    """Return the vertex that is closest to target.

    Simpler than true projection on all segments, but usually sufficient
    for this application.
    """
    if not points:
        raise ValueError("Polyline is empty")
    return min(points, key=lambda p: distance(p, target))


def sample_along_polyline(
    points: List[Point], start_index: int, num_samples: int, step: float, forward: bool
) -> List[Point]:
    """Sample points along polyline starting from a given vertex index.

    - start_index: index of the starting vertex in `points`
    - num_samples: how many points to generate
    - step: arc-length step between samples
    - forward: True to move towards increasing indices, False for decreasing
    """
    if not points:
        raise ValueError("Polyline is empty")
    if num_samples <= 0:
        return []

    direction = 1 if forward else -1

    # Build a local path starting from start_index in the requested direction
    path: List[Point] = [points[start_index]]
    idx = start_index
    while True:
        next_idx = idx + direction
        if next_idx < 0 or next_idx >= len(points):
            break
        path.append(points[next_idx])
        idx = next_idx

    if len(path) < 2:
        raise ValueError("Not enough length on turtle line in requested direction.")

    # Pre-compute segment lengths
    segs = build_segments(path)
    seg_lengths = [s.length for s in segs]
    total_len = sum(seg_lengths)

    required_len = step * (num_samples - 1)
    if total_len < required_len:
        raise ValueError(
            f"Polyline length {total_len:.2f} is shorter than required {required_len:.2f}."
        )

    samples: List[Point] = []
    cur_seg_idx = 0
    cur_seg_pos = 0.0  # distance travelled on current segment

    def interpolate(seg: Segment, t: float) -> Point:
        # t in [0,1]
        return (
            seg.start[0] + (seg.end[0] - seg.start[0]) * t,
            seg.start[1] + (seg.end[1] - seg.start[1]) * t,
        )

    for n in range(num_samples):
        target_dist = n * step

        # Move along segments until we reach target_dist
        travelled = 0.0
        # Recompute position from scratch for simplicity and robustness
        cur_seg_idx = 0
        remaining = target_dist
        while cur_seg_idx < len(segs) and remaining > seg_lengths[cur_seg_idx]:
            remaining -= seg_lengths[cur_seg_idx]
            travelled += seg_lengths[cur_seg_idx]
            cur_seg_idx += 1

        if cur_seg_idx >= len(segs):
            # Numerical edge case: just clamp to last point
            samples.append(path[-1])
            continue

        seg = segs[cur_seg_idx]
        if seg.length == 0:
            # Degenerate segment
            samples.append(seg.end)
        else:
            t = remaining / seg.length
            samples.append(interpolate(seg, t))

    return samples

