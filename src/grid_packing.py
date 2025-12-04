from dataclasses import dataclass
from typing import List, Tuple

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
        # 2D mriežka: 0 = voľné, 1 = obsadené
        self.grid = [[0] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
        self.current_weight = 0.0
        self.used_area_cm2 = 0.0

    def can_place(self, item: Item, x: int, y: int) -> bool:
        # váhový limit
        if self.current_weight + item.weight > MAX_WEIGHT:
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

    def place(self, item: Item, x: int, y: int) -> PlacedItem:
        """Označí bunky ako obsadené a vráti PlacedItem v cm."""
        for yy in range(y, y + item.h_cells):
            for xx in range(x, x + item.w_cells):
                self.grid[yy][xx] = 1

        self.current_weight += item.weight
        self.used_area_cm2 += item.square

        # prevod bunkovej pozície na cm
        x_cm = x * GRID_SIZE_CM
        y_cm = y * GRID_SIZE_CM

        return PlacedItem(
            sheet_id=self.sheet_id,
            sn=item.sn,
            timestamp=item.timestamp,
            x_cm=x_cm,
            y_cm=y_cm,
        )


# --------------------------------------------------------------#
# Funkcie pre spracovanie dát a balenie do mriežky


def generate_items_for_half_day(raw_half_day_block) -> List[Item]:
    """
    raw_half_day_block je jeden prvok zo zoznamu, ktorý vracia prepare_data(),
    t.j. list riadkov:
    [sn, [w_cm, h_cm], weight, date, time, square, stressSquare]
    """
    items: List[Item] = []
    for row in raw_half_day_block:
        sn, dim, weight, date_str, time_str, square, stress_square = row
        w_cm, h_cm = dim
        w_cells = w_cm // GRID_SIZE_CM
        h_cells = h_cm // GRID_SIZE_CM
        timestamp = f"{date_str} {time_str}"

        
        items.append(
            Item(
                sn=sn,
                w_cells=w_cells,
                h_cells=h_cells,
                weight=float(weight),
                timestamp=timestamp,
                square=float(square),
            )
        )

    return items


def pack_items_grid(items: List[Item]) -> Tuple[List[PlacedItem], List[Sheet]]:
    sheets: List[Sheet] = []
    placed: List[PlacedItem] = []

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

        # ak sa nenašlo miesto na žiadnom existujúcom plechu -> nový plech
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

            # teoreticky by sa tu malo vždy podariť umiestniť
            if placed_item is None:
                raise RuntimeError(
                    "Item sa nezmestí ani na prázdny plech – pravdepodobne chyba v dimenziách."
                )

    return placed, sheets


def sort_items_by_area_desc(items: List[Item]) -> List[Item]:
    """Heuristika: zoradenie podľa plochy (square) zostupne."""
    return sorted(items, key=lambda it: it.square, reverse=True)


# --------------------------------------------------------------#
# Spúšťa optimalizovaný grid packing


class GridPacking:
    """
    Trieda, ktorá spúšťa mriežkový packing pre všetky half-day bloky
    a vie spočítať globálne priemerné zaťaženie a využitie plochy.
    Pracuje s OPTIMALIZOVANÝM riešením (zoradenie podľa plochy).
    """

    def __init__(self):
        # všetky plechy zo všetkých half-day blokov (iba optimalizované riešenie)
        self.sheets_all: List[Sheet] = []

    def run(self, prepared_data) -> None:
        """
        prepared_data je výstup ds_h.prepare_data(): zoznam half-day blokov.
        Pre každý blok:
          - vygeneruje Item-y,
          - spraví optimalizovaný packing,
          - uloží plechy do self.sheets_all,
          - zapíše optimalizované rozloženie do data/output.csv.
        """
        import csv

        output_path = './output/output.csv'
        with open(output_path, 'w', newline='') as f_opt:
            writer_opt = csv.writer(f_opt)

            for half_day_block in prepared_data:
                # 1) Item-y pre jeden half-day
                items = generate_items_for_half_day(half_day_block)

                # 2) OPTIMALIZOVANÉ poradie – podľa plochy zostupne
                items_sorted = sort_items_by_area_desc(items)

                # 3) packing na mriežke
                placed_opt, sheets_opt = pack_items_grid(items_sorted)

                # 4) pripoj plechy do globálneho zoznamu
                self.sheets_all.extend(sheets_opt)

                # 5) zapíš výsledok do CSV
                for p in placed_opt:
                    writer_opt.writerow([p.sheet_id, p.sn, p.timestamp, p.x_cm, p.y_cm])

    def get_sheet_avg_weight(self):
        """
        Vráti dvojicu:
          (priemerná váha na plech v kg, priemerné zaťaženie v % z MAX_WEIGHT).
        """
        if not self.sheets_all:
            return 0.0, 0.0

        total_weight = sum(s.current_weight for s in self.sheets_all)
        sheet_count = len(self.sheets_all)
        avg_w = total_weight / sheet_count
        avg_w_pct = (avg_w / MAX_WEIGHT) * 100.0
        return avg_w, avg_w_pct

    def get_sheet_avg_area(self):
        """
        Vráti dvojicu:
          (priemerná zabratá plocha v cm^2, priemerné využitie plochy v %).
        """
        if not self.sheets_all:
            return 0.0, 0.0

        total_area_used = sum(s.used_area_cm2 for s in self.sheets_all)
        sheet_count = len(self.sheets_all)
        avg_a = total_area_used / sheet_count
        avg_a_pct = avg_a / (SHEET_SIZE_CM * SHEET_SIZE_CM) * 100.0
        return avg_a, avg_a_pct