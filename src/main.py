from dataset_handler import DatasetHandler
from maxrects import MaxRectsPacker, batch_to_components, sheets_to_output_rows, compute_stats
import csv

def main():
    path = './data/dataset.csv'
    ds_h = DatasetHandler(path)
    ds_h.load()

    raw_batches = ds_h.prepare_data()

    packer = MaxRectsPacker()
    all_rows = []
    all_sheets = []

    for batch_rows in raw_batches:
        if not batch_rows:
            continue
        components = batch_to_components(batch_rows)
        sheets = packer.pack_batch(components)
        all_sheets.extend(sheets)
        rows = sheets_to_output_rows(sheets)
        all_rows.extend(rows)

    with open('./output/output_maxrects.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(all_rows)

    avg_area, avg_area_pct, avg_w, avg_w_pct = compute_stats(all_sheets)

    print("\n--- Štatistika plechov ---")
    print(f"Priemerné využitie plochy na plech: {avg_area:.2f} cm^2 ({avg_area_pct:.2f} %)")
    print(f"Priemerné zaťaženie plechu:        {avg_w:.2f} kg ({avg_w_pct:.2f} %)")

if __name__ == "__main__":
    main()
