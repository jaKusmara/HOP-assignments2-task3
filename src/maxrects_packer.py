from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import datetime
import csv
import math

# ------------------ Dáta ------------------ #

@dataclass
class Part:
    """
    Jedna fyzická súčiastka (jeden kus).
    base_width / base_height sú už dve najväčšie rozmery (v cm).
    isolation = šírka izolačného pásu z každej strany (v cm).
    """
    name: str
    base_width: int
    base_height: int
    weight: float
    order_time: datetime
    isolation: int = 5

    def __post_init__(self):
        self.base_width = int(self.base_width)
        self.base_height = int(self.base_height)

    @property
    def eff_width(self) -> int:
        """Rozmer vrátane izolácie v osi x."""
        return self.base_width + 2 * self.isolation

    @property
    def eff_height(self) -> int:
        """Rozmer vrátane izolácie v osi y."""
        return self.base_height + 2 * self.isolation

    @property
    def area(self) -> int:
        """Plocha súčiastky vrátane izolácie."""
        return self.eff_width * self.eff_height

    @property
    def density(self) -> float:
        """Vlastná plošná hmotnosť d = m / S_sn."""
        return self.weight / self.area


@dataclass
class Rect:
    """Obdĺžnik na plechu (voľný alebo obsadený)."""
    x: int
    y: int
    w: int
    h: int

    @property
    def area(self) -> int:
        return self.w * self.h

    def intersects(self, other: "Rect") -> bool:
        return not (
            other.x >= self.x + self.w
            or other.x + other.w <= self.x
            or other.y >= self.y + self.h
            or other.y + other.h <= self.y
        )

    def contains(self, other: "Rect") -> bool:
        return (
            other.x >= self.x
            and other.y >= self.y
            and other.x + other.w <= self.x + self.w
            and other.y + other.h <= self.y + self.h
        )


@dataclass
class Placement:
    """Umiestnenie jednej súčiastky na plech."""
    part: Part
    x: int  # súradnica ľavého horného rohu *vrátane* izolácie
    y: int
    w: int  # rozmery obsadeného obdĺžnika (vrátane izolácie)
    h: int
    rotated: bool

    @property
    def inner_x(self) -> int:
        """X súradnica skutočnej súčiastky (bez izolácie) – na výstup."""
        return self.x + self.part.isolation

    @property
    def inner_y(self) -> int:
        """Y súradnica skutočnej súčiastky (bez izolácie) – na výstup."""
        return self.y + self.part.isolation


@dataclass
class Sheet:
    """Jeden plech v MaxRects algoritme."""
    width: int
    height: int
    max_weight: float
    isolation: int
    index: int  # poradové číslo plechu v dávke (AM/PM)
    free_rects: List[Rect] = field(default_factory=list)
    placements: List[Placement] = field(default_factory=list)
    current_weight: float = 0.0

    def __post_init__(self):
        # zmenšíme využiteľnú plochu o okrajový izolačný pás
        usable_w = self.width - 2 * self.isolation
        usable_h = self.height - 2 * self.isolation
        if usable_w <= 0 or usable_h <= 0:
            raise ValueError("Sheet too small after margins")
        self.free_rects = [Rect(self.isolation, self.isolation, usable_w, usable_h)]

    def remaining_area(self) -> int:
        return sum(r.area for r in self.free_rects)

    # -------- MaxRects – výber pozície -------- #

    def find_position_for(self, rect_w: int, rect_h: int) -> Optional[Tuple[int, int]]:
        """
        Best Area Fit heuristika:
        nájde voľný obdĺžnik, kde sa rect zmestí,
        tak aby bol zvyškový priestor (area_fit) čo najmenší.
        """
        best_area_fit = math.inf
        best_short_side = math.inf
        best_pos = None

        for fr in self.free_rects:
            if rect_w <= fr.w and rect_h <= fr.h:
                leftover_horiz = fr.w - rect_w
                leftover_vert = fr.h - rect_h
                area_fit = fr.area - rect_w * rect_h
                short_side = min(leftover_horiz, leftover_vert)

                if area_fit < best_area_fit or (
                    area_fit == best_area_fit and short_side < best_short_side
                ):
                    best_area_fit = area_fit
                    best_short_side = short_side
                    best_pos = (fr.x, fr.y)

        return best_pos

    def place(self, part: Part, x: int, y: int, rect_w: int, rect_h: int, rotated: bool):
        """Umiestni obdĺžnik a upraví zoznam voľných obdĺžnikov (MaxRects split + prune)."""
        new_rect = Rect(x, y, rect_w, rect_h)

        # Split všetkých voľných obdĺžnikov, ktoré sa prekrývajú
        i = 0
        while i < len(self.free_rects):
            fr = self.free_rects[i]
            if not fr.intersects(new_rect):
                i += 1
                continue

            del self.free_rects[i]
            self.free_rects.extend(self._split_free_rect(fr, new_rect))

        # Prune – odstránenie obdĺžnikov, ktoré sú úplne obsiahnuté v iných
        self._prune_free_rects()

        # Uloženie umiestnenia
        self.placements.append(Placement(part, x, y, rect_w, rect_h, rotated))
        self.current_weight += part.weight

    def _split_free_rect(self, free: Rect, placed: Rect) -> List[Rect]:
        """Rozseká voľný obdĺžnik okolo obsadeného (štandardný MaxRects split)."""
        result: List[Rect] = []

        if not free.intersects(placed):
            result.append(free)
            return result

        # Nad
        if placed.y > free.y and placed.y < free.y + free.h:
            result.append(Rect(free.x, free.y, free.w, placed.y - free.y))

        # Pod
        p_bottom = placed.y + placed.h
        f_bottom = free.y + free.h
        if p_bottom < f_bottom and p_bottom > free.y:
            result.append(Rect(free.x, p_bottom, free.w, f_bottom - p_bottom))

        # Vľavo
        if placed.x > free.x and placed.x < free.x + free.w:
            x = free.x
            w = placed.x - free.x
            y = max(free.y, placed.y)
            bottom = min(free.y + free.h, placed.y + placed.h)
            h = bottom - y
            if w > 0 and h > 0:
                result.append(Rect(x, y, w, h))

        # Vpravo
        p_right = placed.x + placed.w
        f_right = free.x + free.w
        if p_right < f_right and p_right > free.x:
            x = p_right
            w = f_right - p_right
            y = max(free.y, placed.y)
            bottom = min(free.y + free.h, placed.y + placed.h)
            h = bottom - y
            if w > 0 and h > 0:
                result.append(Rect(x, y, w, h))

        return result

    def _prune_free_rects(self):
        """Odstráni obdĺžniky, ktoré sú úplne obsiahnuté v iných (aby sa neprekrývali)."""
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


# ------------------ MaxRects + hustota ------------------ #

class MaxRectsPacker:
    def __init__(
        self,
        plate_width: int = 500,
        plate_height: int = 500,
        isolation: int = 5,
        max_weight: float = 200.0,
    ):
        self.plate_width = plate_width
        self.plate_height = plate_height
        self.isolation = isolation
        self.max_weight = max_weight

    def pack_batch(self, parts: List[Part]) -> List[Sheet]:
        """
        Zabalí jednu dávku (AM alebo PM).
        Implementuje heuristiku:
        - cieľová hustota D = (200 - mc) / S_p
        - vyberá súčiastku s d = m / S_sn najbližšou k D,
          ktorá sa zmestí (MaxRects) a hmotnostne vyhovuje.
        """
        remaining = parts.copy()
        sheets: List[Sheet] = []
        sheet_idx = 1

        while remaining:
            sheet = Sheet(
                width=self.plate_width,
                height=self.plate_height,
                max_weight=self.max_weight,
                isolation=self.isolation,
                index=sheet_idx,
            )

            placed_any = True
            while placed_any and remaining:
                placed_any = False

                rem_area = sheet.remaining_area()
                if rem_area <= 0:
                    break

                # cieľová hustota D
                D = (self.max_weight - sheet.current_weight) / rem_area

                best_part_idx: Optional[int] = None
                best_pos: Optional[Tuple[int, int]] = None
                best_rotated = False
                best_diff = math.inf

                for idx, part in enumerate(remaining):
                    # hmotnostné obmedzenie
                    if sheet.current_weight + part.weight > self.max_weight:
                        continue

                    eff_w, eff_h = part.eff_width, part.eff_height

                    # skúsiť obe orientácie (otáčanie v rovine je dovolené)
                    for rotated, (w, h) in [
                        (False, (eff_w, eff_h)),
                        (True, (eff_h, eff_w)),
                    ]:
                        pos = sheet.find_position_for(w, h)
                        if pos is None:
                            continue

                        d = part.density
                        diff = abs(d - D)

                        if diff < best_diff:
                            best_diff = diff
                            best_part_idx = idx
                            best_pos = pos
                            best_rotated = rotated

                if best_part_idx is not None and best_pos is not None:
                    part = remaining.pop(best_part_idx)
                    eff_w, eff_h = part.eff_width, part.eff_height
                    w, h = (eff_h, eff_w) if best_rotated else (eff_w, eff_h)
                    x, y = best_pos
                    sheet.place(part, x, y, w, h, rotated=best_rotated)
                    placed_any = True
                else:
                    # už nevieme položiť žiadnu ďalšiu súčiastku
                    break

            if sheet.placements:
                sheets.append(sheet)
                sheet_idx += 1
            else:
                # ochrana proti nekonečnej slučke – nič sa neuložilo na prázdny plech
                break

        return sheets


# ------------------ I/O a pomocné funkcie ------------------ #

def load_parts_from_file(path: str, isolation: int = 5) -> List[Part]:
    """Načíta vstupné CSV a rozbalí počty kusov na jednotlivé Part objekty."""
    parts: List[Part] = []
    with open(path, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or row[0].startswith("#"):
                continue
            name, dim_str, weight_str, count_str, time_str = [c.strip() for c in row]

            # rozmery: zoberieme tri, zoradíme zostupne a použijeme dve najväčšie
            dims = [int(d) for d in dim_str.split("x")]
            dims.sort(reverse=True)
            base_w, base_h = dims[0], dims[1]

            weight = float(weight_str)
            count = int(count_str)
            t = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")

            for _ in range(count):
                parts.append(
                    Part(
                        name=name,
                        base_width=base_w,
                        base_height=base_h,
                        weight=weight,
                        order_time=t,
                        isolation=isolation,
                    )
                )
    return parts


def split_batches(parts: List[Part]) -> tuple[List[Part], List[Part]]:
    """Rozdelí súčiastky na AM (00:00–11:59) a PM (12:00–23:59) dávku."""
    am, pm = [], []
    for p in parts:
        if p.order_time.hour < 12:
            am.append(p)
        else:
            pm.append(p)
    return am, pm


def sheets_to_rows(sheets: List[Sheet]) -> List[tuple[int, str, str, int, int]]:
    """
    Prevedie riešenie na riadky vo formáte:
    (číslo plechu, názov, čas objednávky, x, y)
    kde x,y sú pozície skutočnej súčiastky (bez izolácie).
    """
    rows: List[tuple[int, str, str, int, int]] = []
    for sheet in sheets:
        for pl in sheet.placements:
            time_str = pl.part.order_time.strftime("%Y-%m-%d %H:%M:%S")
            rows.append(
                (sheet.index, pl.part.name, time_str, pl.inner_x, pl.inner_y)
            )
    return rows


def write_solution(path: str, rows: List[tuple[int, str, str, int, int]]) -> None:
    """Zapíše výsledok do CSV (bez hlavičky)."""
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def compute_utilization(
    parts: List[Part],
    sheets: List[Sheet],
    plate_w: int = 500,
    plate_h: int = 500,
) -> float:
    """
    Vypočíta využitie plochy podľa:
        U = (sum S_sn) / (N * A_max * B_max) * 100 %
    kde S_sn je plocha súčiastky s izoláciou.
    """
    if not sheets:
        return 0.0
    total_area_parts = sum(p.area for p in parts)
    total_plate_area = len(sheets) * plate_w * plate_h
    return 100.0 * total_area_parts / total_plate_area


# ------------------ Príklad použitia (main) ------------------ #

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Použitie: python maxrects_packer.py vstup.csv vystup.csv")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    all_parts = load_parts_from_file(input_path, isolation=5)
    am_parts, pm_parts = split_batches(all_parts)

    packer = MaxRectsPacker()

    am_sheets = packer.pack_batch(am_parts)
    pm_sheets = packer.pack_batch(pm_parts)

    # číslovanie plechov sa pre AM a PM resetuje – preto 2x voláme pack_batch
    rows = sheets_to_rows(am_sheets) + sheets_to_rows(pm_sheets)
    write_solution(output_path, rows)

    # voliteľne: vypísať využitie
    am_util = compute_utilization(am_parts, am_sheets)
    pm_util = compute_utilization(pm_parts, pm_sheets)
    print(f"Využitie AM dávky: {am_util:.2f} %")
    print(f"Využitie PM dávky: {pm_util:.2f} %")
