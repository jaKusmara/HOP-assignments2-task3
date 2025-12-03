import csv

class Shelf:
    def __init__(self):
        self._shelf_x = 0.0
        self._shelf_y = 0.0
        self._shelf_height = 0.0
        self._current_weight = 0.0
        self._sheet_no = 0
        self.komponent_res = []

    def run_shelf(self, dataset):
        for komponents in dataset:
            self._reset_sheet()
            self._make_shelf(komponents)  
        
        self._write_csv()

    def _make_shelf(self, komponents):       
        for komponent in komponents:
            k_x = komponent[1][0] # Sirka komponentu
            k_y = komponent[1][1] # Vyska komponentu
            k_w = komponent[2] # Vaha komponentu

            print(komponent)
            
            # Kontrola hmotnosti 200KG a vysky / Novy plech
            if self._current_weight + k_w > 200 or self._shelf_y + k_y > 200:
                self._new_sheet()

            
            # Kontrola sirky / Nova polica
            if self._shelf_x + k_x > 200:
                self._shelf_x = 0.0
                self._shelf_y = self._shelf_height
                self._shelf_height = 0.0

            # Vyska police
            if self._shelf_height < k_y :
                self._shelf_height = komponent[1][1]

            # Priratanie vahy
            self._current_weight += k_w

            # Append komponentu do zoznamu
            self.komponent_res.append([self._sheet_no, komponent[0], komponent[3], komponent[4]])

    def _reset_sheet(self):
        self._sheet_no = 0
        self._shelf_x = 0.0
        self._shelf_y = 0.0
        self._shelf_height = 0.0
        self._current_weight = 0.0

    def _new_sheet(self):
        self._sheet_no += 1
        self._shelf_x = 0.0
        self._shelf_y = 0.0
        self._shelf_height = 0.0
        self._current_weight = 0.0

    def _write_csv(self):
        with open('./output/shelf_output.csv', 'w', newline='') as csvfile:
            for item in self.komponent_res:
                writer = csv.writer(csvfile, delimiter=',')
                writer.writerow(item)
    

            