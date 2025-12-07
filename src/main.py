from dataset_handler import DatasetHandler
from shelf import *
from maxrects import MaxRectsPacker, batch_to_components, sheets_to_output_rows, compute_stats
import csv
import time
from grid_packing import GridPacking


def timer(label, func, *args, **kwargs):
    start = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = time.perf_counter() - start
    print(f"{label} čas: {elapsed:.4f} s ({elapsed*1000:.2f} ms)")
    return result


def main():
    # NACITANIE A SPRACOVANIE DF
    path = './data/dataset.csv'
    ds_h = DatasetHandler(path)
    ds_h.load()
    prepared_data = ds_h.prepare_data()

    # SHELF
    shelf = Shelf()

    print("\n--- Štatistika plechov SHELF ---")
    timer("SHELF", shelf.run_shelf, prepared_data)
    
    avg_w, avg_w_pct = shelf.get_sheet_avg_weight()
    avg_a, avg_a_pct = shelf.get_sheet_avg_area()

    print(f"Priemerná váha na plech: {avg_w:.2f} kg ({avg_w_pct:.2f} %)")
    print(f"Priemerná zabrata plocha: {avg_a:.2f} mm² ({avg_a_pct:.2f} %)")

    # MAXRECTS
    packer = MaxRectsPacker()
    all_rows = []
    all_sheets = []


    def run_maxrects(prepared_data):
        nonlocal all_rows, all_sheets
        for batch_rows in prepared_data:
            if not batch_rows:
                continue
            components = batch_to_components(batch_rows)
            sheets = packer.pack_batch(components)
            all_sheets.extend(sheets)
            rows = sheets_to_output_rows(sheets)
            all_rows.extend(rows)


    print("\n--- Štatistika plechov MAXRECTS ---")
    timer("MAXRECTS", run_maxrects, prepared_data)

    with open('./output/maxrects_output.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(all_rows)

    avg_area, avg_area_pct, avg_w, avg_w_pct = compute_stats(all_sheets)
    
    print(f"Priemerné zaťaženie plechu:        {avg_w:.2f} kg ({avg_w_pct:.2f} %)")
    print(f"Priemerné využitie plochy na plech: {avg_area:.2f} cm^2 ({avg_area_pct:.2f} %)")

    # GRID PACKING
    grid = GridPacking()

    print("\n--- Štatistika plechov GRID PACKING ---")
    timer("GRID PACKING", grid.run, prepared_data)

    avg_w, avg_w_pct = grid.get_sheet_avg_weight()
    avg_a, avg_a_pct = grid.get_sheet_avg_area()

    print(f"Priemerné zaťaženie plechu: {avg_w:.2f} kg ({avg_w_pct:.2f} %)")
    print(f"Priemerné využitie plechu:  {avg_a:.2f} cm^2 ({avg_a_pct:.2f} %)")


if __name__ == "__main__":
    main()
