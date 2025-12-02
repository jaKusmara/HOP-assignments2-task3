from src.dataset_handler import DatasetHandler
from src.maxrects import MaxRectsPacker, batch_to_components, sheets_to_output_rows
import csv

def main():
    path = './data/dataset.csv'
    ds_h = DatasetHandler(path)
    ds_h.load()

    raw_batches = ds_h.prepare_data()

    packer = MaxRectsPacker()
    all_rows = []

    for batch_rows in raw_batches:
        if not batch_rows:
            continue
        components = batch_to_components(batch_rows)
        sheets = packer.pack_batch(components)
        rows = sheets_to_output_rows(sheets)
        all_rows.extend(rows)

    with open('./data/output.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(all_rows)

    for row in all_rows[:10]:
        print(row)

if __name__ == "__main__":
    main()
