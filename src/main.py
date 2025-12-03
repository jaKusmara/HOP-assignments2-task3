import csv

from src.dataset_handler import DatasetHandler
from src.grid_packing import (
    generate_items_for_half_day,
    pack_items_grid,
    SHEET_SIZE_CM,
    sort_items_by_area_desc,
    PackingStats,
)


def main():
    path = './data/dataset.csv'
    ds_h = DatasetHandler(path)
    ds_h.load()
    half_days = ds_h.prepare_data()

    output_path = './data/output.csv'

    with open(output_path, 'w', newline='') as f_opt:
        writer_opt = csv.writer(f_opt)

        for block_index, half_day_block in enumerate(half_days, start=1):
            #1. vstupné dáta pre jeden poldeň
            items = generate_items_for_half_day(half_day_block)

            # 2. BASELINE
            placed_base, sheets_base = pack_items_grid(items)
            stats_base = PackingStats(sheets_base)

            # 3. OPTIMALIZOVANÉ
            items_sorted = sort_items_by_area_desc(items)
            placed_opt, sheets_opt = pack_items_grid(items_sorted)
            stats_opt = PackingStats(sheets_opt)

            #4. OPTIMALIZOVANÉ riešenie do output.csv
            for p in placed_opt:
                writer_opt.writerow([p.sheet_id, p.sn, p.timestamp, p.x_cm, p.y_cm])

            #5. Porovnanie do konzoly (na analýzu efektivity)
            print(
                f"Half-day {block_index}: "
                f"baseline sheets={stats_base.sheet_count}, "
                f"avg_weight={stats_base.avg_weight_per_sheet:.2f} kg, "
                f"avg_util={stats_base.avg_utilization_per_sheet_pct:.2f} %, "
                f"optimized sheets={stats_opt.sheet_count}, "
                f"avg_weight={stats_opt.avg_weight_per_sheet:.2f} kg, "
                f"avg_util={stats_opt.avg_utilization_per_sheet_pct:.2f} %"
            )


if __name__ == "__main__":
    main()