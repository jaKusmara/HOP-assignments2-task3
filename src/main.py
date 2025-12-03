from dataset_handler import DatasetHandler
from shelf import *

def main():
    path = './data/dataset.csv'
    
    ds_h = DatasetHandler(path)

    ds_h.load()
    
    prepared_data = ds_h.prepare_data()

    shelf = Shelf()

    shelf.run_shelf(prepared_data)

    avg_w, avg_w_pct = shelf.get_sheet_avg_weight()
    avg_a, avg_a_pct = shelf.get_sheet_avg_area()

    print(f"Priemerná váha na plech: {avg_w:.2f} kg ({avg_w_pct:.2f} %)")
    print(f"Priemerná zabrata plocha: {avg_a:.2f} mm² ({avg_a_pct:.2f} %)")

        


if __name__ == "__main__":
    main()