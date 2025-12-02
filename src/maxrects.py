# src/packing.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from math import inf
from datetime import datetime
from src.models import Component
from src.utils import calcStressSquareCoefficient, calcStressScore


PLATE_SIZE_CM = 500        # 5m x 5m
MAX_WEIGHT = 200.0         # kg
MARGIN_CM = 5              # 5 cm okolo reálnej súčiastky (už je v +10)


# ---------- pomocná funkcia: preklad výstupu DatasetHandleru ----------

def batch_to_components(batch_rows: List[list]) -> List[Component]:
    """
    batch_rows je to, čo vracia DatasetHandler.prepare_data():
    [ [sn, dim(list), weight, count, date_str, time_str, square, stressSquare], ... ]

    Tu:
    - z toho spravíme Component objekty
    - count rozbalíme na jednotlivé kusy
    """
    components: List[Component] = []

    for sn, dim_list, weight, count, date_str, time_str, square, stress in batch_rows:
        # rekonštrukcia timestampu
        ts = datetime.fromisoformat(f"{date_str} {time_str}")
        w, h = int(dim_list[0]), int(dim_list[1])

        for _ in range(int(count)):
            components.append(
                Component(
                    sn=str(sn),
                    width=w,
                    height=h,
                    weight=float(weight),
                    timestamp=ts,
                    square=float(square),
                    stress_square=float(stress),
                )
            )

    return components


# ---------- Rect / Placement / Sheet ----------

@dataclass
class Rect:
    x: int
    y: int
    w: int
    h: int

    @property
    def area(self) -> int:
        return self.w * self.h

    def intersects(self, other: "Rect") -> bool:
        return not (
            other.x >= self.x + self.w or
            other.x + other.w <= self.x or
            other.y >= self.y + self.h or
            other.y + other.h <= self.y
        )

    def contains(self, other: "Rect") -> bool:
        return (
            other.x >= self.x and
            other.y >= self.y and
            other.x + other.w <= self.x + self.w and
            other.y + other.h <= self.y + self.h
        )


@dataclass
class Placement:
    component: Component
    x: int      # ľavý horný roh OBALU (s izoláciou)
    y: int
    w: int
    h: int
    rotated: bool

    @property
    def inner_x(self) -> int:
        """Skutočná pozícia súčiastky (bez izolácie)."""
        return self.x + MARGIN_CM

    @property
    def inner_y(self) -> int:
        return self.y + MARGIN_CM


@dataclass
class Sheet:
    index: int
    width: int = PLATE_SIZE_CM
    height: int = PLATE_SIZE_CM
    max_weight: float = MAX_WEIGHT
    free_rects: List[Rect] = field(default_factory=list)
    placements: List[Placement] = field(default_factory=list)
    current_weight: float = 0.0

    def __post_init__(self):
        # jeden veľký voľný obdĺžnik – celá plocha plechu
        self.free_rects = [Rect(0, 0, self.width, self.height)]

    def remaining_area(self) -> int:
        return sum(r.area for r in self.free_rects)

    # ---------- MaxRects – Best Area Fit ----------

    def find_position_for(self, w: int, h: int) -> Optional[Tuple[int, int]]:
        best_area_fit = inf
        best_short_side = inf
        best_pos: Optional[Tuple[int, int]] = None

        for fr in self.free_rects:
            if w <= fr.w and h <= fr.h:
                leftover_horiz = fr.w - w
                leftover_vert = fr.h - h
                area_fit = fr.area - w * h
                short_side = min(leftover_horiz, leftover_vert)

                if area_fit < best_area_fit or (
                    area_fit == best_area_fit and short_side < best_short_side
                ):
                    best_area_fit = area_fit
                    best_short_side = short_side
                    best_pos = (fr.x, fr.y)

        return best_pos

    def place(self, component: Component, x: int, y: int, w: int, h: int, rotated: bool):
        placed_rect = Rect(x, y, w, h)

        # split voľných obdĺžnikov
        i = 0
        while i < len(self.free_rects):
            fr = self.free_rects[i]
            if not fr.intersects(placed_rect):
                i += 1
                continue

            del self.free_rects[i]
            self.free_rects.extend(self._split_free_rect(fr, placed_rect))

        self._prune_free_rects()

        self.placements.append(Placement(component, x, y, w, h, rotated))
        self.current_weight += component.weight

    def _split_free_rect(self, free: Rect, placed: Rect) -> List[Rect]:
        res: List[Rect] = []

        if not free.intersects(placed):
            res.append(free)
            return res

        # nad
        if placed.y > free.y and placed.y < free.y + free.h:
            res.append(Rect(free.x, free.y, free.w, placed.y - free.y))

        # pod
        p_bottom = placed.y + placed.h
        f_bottom = free.y + free.h
        if p_bottom < f_bottom and p_bottom > free.y:
            res.append(Rect(free.x, p_bottom, free.w, f_bottom - p_bottom))

        # vľavo
        if placed.x > free.x and placed.x < free.x + free.w:
            x = free.x
            w = placed.x - free.x
            y = max(free.y, placed.y)
            bottom = min(free.y + free.h, placed.y + placed.h)
            h = bottom - y
            if w > 0 and h > 0:
                res.append(Rect(x, y, w, h))

        # vpravo
        p_right = placed.x + placed.w
        f_right = free.x + free.w
        if p_right < f_right and p_right > free.x:
            x = p_right
            w = f_right - p_right
            y = max(free.y, placed.y)
            bottom = min(free.y + free.h, placed.y + placed.h)
            h = bottom - y
            if w > 0 and h > 0:
                res.append(Rect(x, y, w, h))

        return res

    def _prune_free_rects(self):
        i = 0
        while i < len(self.free_rects):
            j = i + 1
            removed = False
            while j < len(self.free_rects):
                r1 = self.free_rects[i]
                r2 = self.free_rects[j]
                if r1.contains(r2):
                    del self.free_rects[j]
                elif r2.contains(r1):
                    del self.free_rects[i]
                    removed = True
                    break
                else:
                    j += 1
            if not removed:
                i += 1


# ---------- MaxRectsPacker – hustotná heuristika ----------

class MaxRectsPacker:
    """
    Heuristika z vašej analýzy:
    D = (200 - mc) / Sp, kde Sp je NEvyužitá plocha plechu
    d = m / Ssn
    vyberáme komponent s |d - D| minimálnym, ktorý sa zmestí (MaxRects + váhový limit)
    """

    def pack_batch(self, components: List[Component]) -> List[Sheet]:
        remaining = components.copy()
        sheets: List[Sheet] = []
        sheet_index = 1

        while remaining:
            sheet = Sheet(index=sheet_index)
            sheet_index += 1

            placed_any = True
            while placed_any and remaining:
                placed_any = False

                rem_area = sheet.remaining_area()
                if rem_area <= 0:
                    break

                # cieľový stres plechu D
                sheet_stress = calcStressSquareCoefficient(
                    sheet.current_weight, rem_area
                )

                best_idx: Optional[int] = None
                best_pos: Optional[Tuple[int, int]] = None
                best_rot = False
                best_score = inf

                for idx, comp in enumerate(remaining):
                    # hmotnostný limit
                    if sheet.current_weight + comp.weight > sheet.max_weight:
                        continue

                    w, h = comp.dims

                    for rotated, (cw, ch) in [(False, (w, h)), (True, (h, w))]:
                        pos = sheet.find_position_for(cw, ch)
                        if pos is None:
                            continue

                        comp_stress = comp.stress_square
                        score = abs(
                            calcStressScore(comp_stress, sheet_stress)
                        )  # ~ |d - D|

                        if score < best_score:
                            best_score = score
                            best_idx = idx
                            best_pos = pos
                            best_rot = rotated

                if best_idx is not None and best_pos is not None:
                    comp = remaining.pop(best_idx)
                    w, h = comp.dims
                    if best_rot:
                        w, h = h, w
                    x, y = best_pos
                    sheet.place(comp, x, y, w, h, rotated=best_rot)
                    placed_any = True
                else:
                    break  # nič nevieme umiestniť

            if sheet.placements:
                sheets.append(sheet)
            else:
                break  # bezpečnostná brzda

        return sheets


def sheets_to_output_rows(sheets: List[Sheet]) -> List[list]:
    """
    Výstup:
        [číslo plechu, sn, timestamp, x, y]
    kde x, y sú pozície reálnej súčiastky (bez izolácie),
    presne ako chce zadanie.
    """
    rows: List[list] = []
    for sheet in sheets:
        for pl in sheet.placements:
            ts_str = pl.component.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            rows.append([
                sheet.index,
                pl.component.sn,
                ts_str,
                pl.inner_x,
                pl.inner_y,
            ])
    return rows
