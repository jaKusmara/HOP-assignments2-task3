from dataset_handler import DatasetHandler

def main():
    path = './data/dataset.csv'
    
    ds_h = DatasetHandler(path)

    ds_h.load()
    print(ds_h.prepare_data())

if __name__ == "__main__":
    main()