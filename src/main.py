# main.py
from dataset_handler import DatasetHandler
from maxrects import MaxRectsPacker, batch_to_components, sheets_to_output_rows
import csv


def main():
    path = './data/dataset.csv'

    ds_h = DatasetHandler(path)
    ds_h.load()

    # pôvodný výstup – list dávok, každá dávka je list riadkov
    raw_batches = ds_h.prepare_data()

    packer = MaxRectsPacker()
    all_rows: list[list] = []

    for batch_rows in raw_batches:
        if not batch_rows:   # niektoré AM/PM dávky môžu byť prázdne
            continue

        components = batch_to_components(batch_rows)
        sheets = packer.pack_batch(components)
        rows = sheets_to_output_rows(sheets)
        all_rows.extend(rows)

    # zapíš výsledok
    with open('./data/output.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(all_rows)

    # kontrolný print prvých pár riadkov
    for row in all_rows[:10]:
        print(row)


if __name__ == "__main__":
    main()
