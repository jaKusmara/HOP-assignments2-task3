import csv

from src.dataset_handler import DatasetHandler
from src.grid_packing import (
    generate_items_for_half_day,
    pack_items_grid,
    SHEET_SIZE_CM,
)

def main():
    path = './data/dataset.csv'
    ds_h = DatasetHandler(path)
    ds_h.load()
    half_days = ds_h.prepare_data()  

    output_path = './data/output.csv'

    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        # PODĽA ZADANIA:
        # 1,MR-009,2025-09-16 01:40:17,5,5
        # -> bez hlavičky, takže ju nebudeme písať

        for block_index, half_day_block in enumerate(half_days, start=1):
            #1. vygeneruj jednotlivé kusy (Item) z jedného pol dňa
            items = generate_items_for_half_day(half_day_block)

            #2. aplikuj mriežkový packing
            placed, sheets = pack_items_grid(items)

            #3. zapíš výsledok do CSV – každý kus jeden riadok
            for p in placed:
                writer.writerow([p.sheet_id, p.sn, p.timestamp, p.x_cm, p.y_cm])

            #4. vypíš využitie priestoru pre kontrolu
            used_area = sum(s.used_area_cm2 for s in sheets)
            total_area = len(sheets) * SHEET_SIZE_CM * SHEET_SIZE_CM
            utilization = used_area / total_area * 100 if total_area > 0 else 0.0

            print(f"Half-day {block_index}: sheets={len(sheets)}, utilization={utilization:.2f}%")

if __name__ == "__main__":
    main()