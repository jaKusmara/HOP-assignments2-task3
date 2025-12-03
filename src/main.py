from dataset_handler import DatasetHandler
from shelf import *

def main():
    path = './data/dataset.csv'
    
    ds_h = DatasetHandler(path)

    ds_h.load()
    
    prepared_data = ds_h.prepare_data()

    shelf = Shelf()

    shelf.run_shelf(prepared_data)
        


if __name__ == "__main__":
    main()