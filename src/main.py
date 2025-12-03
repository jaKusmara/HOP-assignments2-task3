from dataset_handler import DatasetHandler
from grid_packing import GridPacking


def main():
    path = './data/dataset.csv'

    ds_h = DatasetHandler(path)
    ds_h.load()
    prepared_data = ds_h.prepare_data()

    grid = GridPacking()
    grid.run(prepared_data)

    avg_w, avg_w_pct = grid.get_sheet_avg_weight()
    avg_a, avg_a_pct = grid.get_sheet_avg_area()

    print(f"Priemerné zaťaženie plechu: {avg_w:.2f} kg ({avg_w_pct:.2f} %)")
    print(f"Priemerné využitie plechu: {avg_a:.2f} cm^2 ({avg_a_pct:.2f} %)")


if __name__ == "__main__":
    main()