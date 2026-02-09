"""
Synthetic data generator for vertualMarker Strategy 2.

목표:
- 실제 OLED 패널 PCBL 측면 윤곽(edge map)과 유사한 2개의 긴 곡선을 생성
- 하나는 거북이 선(turtle line), 다른 하나는 그 위쪽에 평행하게 있는 선
- 중앙 부근에 곡률(벤딩 구간)을 넣고, 양쪽은 거의 직선

TXT 형식:
- x y (또는 x,y) 형식으로 한 줄에 한 점
- 빈 줄로 서로 다른 폴리라인을 구분
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from typing import List, Tuple

Point = Tuple[float, float]


@dataclass
class SyntheticParams:
    length: float = 2000.0  # 전체 x 범위
    base_y: float = 1000.0  # 거북이 선 기본 y (아래쪽)
    offset_y: float = -150.0  # 위쪽 선과의 y 오프셋
    head_height: float = 200.0  # 앞머리(세로) 구간 높이
    head_width: float = 300.0   # 윗머리(가로) 구간 길이
    bend_center_x: float = 1000.0  # 굽힘 중심 x
    bend_radius: float = 800.0  # 곡률 반경(클수록 완만)
    bend_width: float = 800.0  # 굽힘이 일어나는 x 구간 폭
    noise: float = 3.0  # 무작위 노이즈 세기
    num_points: int = 2000  # 각 폴리라인 점 개수


def generate_turtle_and_partner(params: SyntheticParams) -> List[List[Point]]:
    """Generate two polyline-like curves approximating side-bending shape.

    구성:
    - x=0 부근에 거의 수직인 "앞머리" 구간 (FH 검출용)
    - 이후 x 방향으로 이어지는 완만한 bending 곡선 구간
    """
    import random

    def bend_profile(x: float) -> float:
        # -bend_width/2 ~ +bend_width/2 부근에서 부드럽게 굽어지는 단순 모델
        dx = x - params.bend_center_x
        if abs(dx) > params.bend_width / 2:
            return 0.0
        # 단순 포물선 형태 (곡률 방향: 위쪽으로 살짝 들어간다고 가정)
        t = dx / (params.bend_width / 2)
        return - (params.bend_radius) * (1 - t * t) * 0.01

    turtle: List[Point] = []
    partner: List[Point] = []

    # 1) 앞머리 세로 구간 (x=0에서 head_height 만큼 수직 이동)
    x0 = 0.0
    y_top = params.base_y - params.head_height / 2.0
    y_bottom = params.base_y + params.head_height / 2.0

    # 두 점으로만 구성된 거의 완전한 세로 직선 (FH 검출 보장)
    turtle.append((x0, y_bottom))
    turtle.append((x0, y_top))
    partner.append((x0, y_bottom + params.offset_y))
    partner.append((x0, y_top + params.offset_y))

    # 2) 윗머리 가로 구간 (y_top 위치에서 head_width 만큼 수평 이동)
    x1 = x0 + params.head_width
    turtle.append((x1, y_top))
    partner.append((x1, y_top + params.offset_y))

    # 3) 본체 bending 구간 (x > x1)
    xs = [
        params.length * i / (params.num_points - 1)
        for i in range(params.num_points)
    ]

    for x in xs:
        # 앞머리/윗머리 구간 이후부터 사용
        x_body = x1 + 1.0 + x
        base_bend = bend_profile(x_body)
        y_t = params.base_y + base_bend
        y_p = params.base_y + params.offset_y + base_bend * 0.98  # 거의 같은 곡률

        # 약간의 노이즈
        n1 = (random.random() - 0.5) * 2 * params.noise
        n2 = (random.random() - 0.5) * 2 * params.noise

        turtle.append((x_body, y_t + n1))
        partner.append((x_body, y_p + n2))

    return [turtle, partner]


def save_polylines_txt(path: str, polylines: List[List[Point]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        first = True
        for pl in polylines:
            if not first:
                f.write("\n")
            first = False
            for x, y in pl:
                f.write(f"{x:.3f} {y:.3f}\n")


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic TXT example for vertualMarker Strategy 2."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="example_turtle.txt",
        help="Output TXT file path (default: example_turtle.txt)",
    )
    parser.add_argument(
        "--length", type=float, default=2000.0, help="Total x-length of curves",
    )
    parser.add_argument(
        "--base-y", type=float, default=1000.0, help="Base y of turtle line",
    )
    parser.add_argument(
        "--offset-y",
        type=float,
        default=-150.0,
        help="Vertical offset between turtle and partner lines",
    )
    parser.add_argument(
        "--bend-center-x",
        type=float,
        default=1000.0,
        help="X position of bending center",
    )
    parser.add_argument(
        "--bend-radius",
        type=float,
        default=800.0,
        help="Radius-like control for bending curvature (larger=gentler)",
    )
    parser.add_argument(
        "--bend-width",
        type=float,
        default=800.0,
        help="Width of x-region where bending occurs",
    )
    parser.add_argument(
        "--noise",
        type=float,
        default=3.0,
        help="Random noise amplitude on y",
    )
    parser.add_argument(
        "--num-points",
        type=int,
        default=2000,
        help="Number of points per polyline",
    )

    args = parser.parse_args(argv)

    params = SyntheticParams(
        length=args.length,
        base_y=args.base_y,
        offset_y=args.offset_y,
        bend_center_x=args.bend_center_x,
        bend_radius=args.bend_radius,
        bend_width=args.bend_width,
        noise=args.noise,
        num_points=args.num_points,
    )
    polys = generate_turtle_and_partner(params)
    save_polylines_txt(args.output, polys)
    print(f"Synthetic example saved to {args.output}")


if __name__ == "__main__":
    main()

