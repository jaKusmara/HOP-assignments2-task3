from dataclasses import dataclass
from typing import List, Tuple, Optional

GRID_SIZE_CM = 5
SHEET_SIZE_CM = 500
GRID_WIDTH = SHEET_SIZE_CM // GRID_SIZE_CM  # 100
GRID_HEIGHT = SHEET_SIZE_CM // GRID_SIZE_CM  # 100
MAX_WEIGHT = 200.0

@dataclass
class Item:
    sn: str
    w_cells: int
    h_cells: int
    weight: float
    timestamp: str  # "YYYY-MM-DD HH:MM:SS"
    square: float   # plocha v cm^2 (pre vyhodnotenie využitia)

@dataclass
class PlacedItem:
    sheet_id: int
    sn: str
    timestamp: str
    x_cm: int  # ľavý horný roh v cm
    y_cm: int

class Sheet:
    def __init__(self, sheet_id: int):
        self.sheet_id = sheet_id
        self.grid = [[0] * GRID_WIDTH for _ in range(GRID_HEIGHT)]  # 2D mriežka: 0 = voľné, 1 = obsadené
        self.current_weight = 0.0
        self.used_area_cm2 = 0.0

    def can_place(self, item: Item, x: int, y: int) -> bool:
        if self.current_weight + item.weight > MAX_WEIGHT:     # váhový limit
            return False

        # hranice
        if x + item.w_cells > GRID_WIDTH or y + item.h_cells > GRID_HEIGHT:
            return False

        # kolízia
        for yy in range(y, y + item.h_cells):
            for xx in range(x, x + item.w_cells):
                if self.grid[yy][xx] == 1:
                    return False

        return True

    # označiť bunky ako obsadené
    def place(self, item: Item, x: int, y: int) -> PlacedItem:
        for yy in range(y, y + item.h_cells):
            for xx in range(x, x + item.w_cells):
                self.grid[yy][xx] = 1

        self.current_weight += item.weight
        self.used_area_cm2 += item.square

        # prevod bunkovej pozície na cm
        x_cm = x * GRID_SIZE_CM
        y_cm = y * GRID_SIZE_CM

        # výstup – zodpovedá formátu CSV
        return PlacedItem(
            sheet_id=self.sheet_id,
            sn=item.sn,
            timestamp=item.timestamp,
            x_cm=x_cm,
            y_cm=y_cm
        )
    
class PackingStats:
    """
    Štatistiky za jeden half-day pre dané riešenie (baseline / optimalizované).
    Vstupom je zoznam plechov Sheet.
    """
    def __init__(self, sheets: List[Sheet]):
        self.sheets = sheets
        self.sheet_count = len(sheets)

        # súčet hmotností na všetkých plechoch
        self.total_weight = sum(s.current_weight for s in sheets)

        # súčet využitej plochy (cm^2)
        self.total_used_area_cm2 = sum(s.used_area_cm2 for s in sheets)

        # celková plocha všetkých plechov (cm^2)
        self.total_area_cm2 = self.sheet_count * SHEET_SIZE_CM * SHEET_SIZE_CM

        # priemerné zaťaženie jedného plechu (kg)
        self.avg_weight_per_sheet = (
            self.total_weight / self.sheet_count if self.sheet_count > 0 else 0.0
        )

        # priemerná využitá plocha na plech (cm^2)
        self.avg_used_area_per_sheet_cm2 = (
            self.total_used_area_cm2 / self.sheet_count if self.sheet_count > 0 else 0.0
        )

        # priemerné využitie plochy na plech v %
        self.avg_utilization_per_sheet_pct = (
            self.avg_used_area_per_sheet_cm2 / (SHEET_SIZE_CM * SHEET_SIZE_CM) * 100
            if self.sheet_count > 0 else 0.0
        )

    def __repr__(self) -> str:
        return (
            f"PackingStats(sheet_count={self.sheet_count}, "
            f"avg_weight={self.avg_weight_per_sheet:.2f} kg, "
            f"avg_area={self.avg_used_area_per_sheet_cm2:.2f} cm^2, "
            f"avg_util={self.avg_utilization_per_sheet_pct:.2f} %)"
        )  

#--------------------------------------------------------------#
# Funkcie pre spracovanie dát a balenie do mriežky 


def generate_items_for_half_day(raw_half_day_block):
    """
    raw_half_day_block je jeden prvok zo zoznamu, ktorý vracia prepare_data(),
    t.j. list riadkov:
    [sn, [w_cm, h_cm], weight, count, date, time, square, stressSquare]
    """
    items = []
    for row in raw_half_day_block:
        sn, dim, weight, count, date_str, time_str, square, stress_square = row
        w_cm, h_cm = dim
        w_cells = w_cm // GRID_SIZE_CM
        h_cells = h_cm // GRID_SIZE_CM
        timestamp = f"{date_str} {time_str}"

        for _ in range(int(count)):
            items.append(
                Item(
                    sn=sn,
                    w_cells=w_cells,
                    h_cells=h_cells,
                    weight=float(weight),
                    timestamp=timestamp,
                    square=float(square)
                )
            )

    return items


def pack_items_grid(items) -> Tuple[List[PlacedItem], List[Sheet]]:
    sheets: List[Sheet] = []
    placed: List[PlacedItem] = []

    def get_or_create_sheet() -> Sheet:
        if not sheets:
            sheets.append(Sheet(sheet_id=1))
        return sheets[-1]

    for item in items:
        placed_item = None

        # pokúsiť sa umiestniť v niektorom z existujúcich plechov
        for sheet in sheets:
            found = False
            for y in range(GRID_HEIGHT):
                if found:
                    break
                for x in range(GRID_WIDTH):
                    if sheet.can_place(item, x, y):
                        placed_item = sheet.place(item, x, y)
                        placed.append(placed_item)
                        found = True
                        break
            if found:
                break

        # ak sa nenašlo miesto na žiadnom existujúcom plechu -> nový
        if placed_item is None:
            new_id = len(sheets) + 1
            new_sheet = Sheet(sheet_id=new_id)
            sheets.append(new_sheet)

            found = False
            for y in range(GRID_HEIGHT):
                if found:
                    break
                for x in range(GRID_WIDTH):
                    if new_sheet.can_place(item, x, y):
                        placed_item = new_sheet.place(item, x, y)
                        placed.append(placed_item)
                        found = True
                        break

            # Teoreticky by sa tu malo vždy podariť umiestniť, lebo máme prázdny plech.
            if placed_item is None:
                raise RuntimeError("Item sa nezmestí ani na prázdny plech – pravdepodobne chyba v dimenziách.")

    return placed, sheets

def sort_items_by_area_desc(items: List[Item]) -> List[Item]:
    """Heuristika: zoradenie podľa plochy (square) zostupne."""
    return sorted(items, key=lambda it: it.square, reverse=True)

