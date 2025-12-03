import csv

class Shelf:
    MAX_WIDTH = 200.0
    MAX_HEIGHT = 200.0
    MAX_WEIGHT = 200.0

    def __init__(self):
        self._shelf_x = 0.0                # x-os shelfu
        self._shelf_y = 0.0                # y-os shelfu
        self._shelf_height = 0.0           # vyska shelfu
        self._current_weight = 0.0         # vaha plechu
        self._sheet_no = 0                 # cislo plechu

        self.komponent_res = []            # vysledok za pol dna

        # priemery
        self.sheet_avg_weight = 0.0        # priemerná váha na plech
        self.sheet_avg_weight_pct = 0.0    # priemerné % využitie váhy plechu
        self.sheet_avg_area = 0.0          # priemerná zabrata plocha plechu
        self.sheet_avg_area_pct = 0.0      # priemerné % využitie plochy plechu

    # --------- GETTERY ----------

    def get_sheet_avg_weight(self):
        return self.sheet_avg_weight, self.sheet_avg_weight_pct
    
    def get_sheet_avg_area(self):
        return self.sheet_avg_area, self.sheet_avg_area_pct

    # --------- FUNKCIE ----------

    # --------- MAIN ---------
    def run_shelf(self, dataset):
        self.komponent_res.clear()
        for komponents in dataset:
            self._sheet_no = 0
            self._make_shelf(komponents)
        self._write_csv()
        
    
    def _make_shelf(self, komponents):
        used_weight = 0.0   # súčet váh všetkých plechov
        used_area = 0.0     # súčet plôch všetkých komponentov

        # reset pozície a váhy pre pol dna
        self._shelf_x = 0.0
        self._shelf_y = 0.0
        self._shelf_height = 0.0
        self._current_weight = 0.0

        for komponent in komponents:
            k_x = komponent[1][0]  # šírka
            k_y = komponent[1][1]  # výška
            k_w = komponent[2]     # váha
            k_s = k_x * k_y        # plocha komponentu

            # 1) kontrola hmotnosti
            if self._current_weight + k_w > self.MAX_WEIGHT:
                used_weight += self._current_weight   # pripočítaj váhu starého plechu
                self._new_sheet()                     # začni nový plech

            # 2) kontrola šírky
            if self._shelf_x + k_x > self.MAX_WIDTH:
                self._shelf_x = 0.0
                self._shelf_y += self._shelf_height
                self._shelf_height = 0.0

            # 3) kontrola výšky – nevojde na výšku → nový plech
            if self._shelf_y + k_y > self.MAX_HEIGHT:
                used_weight += self._current_weight   # zavri plech
                self._new_sheet()                     # nový plech

            # výška police
            if self._shelf_height < k_y:
                self._shelf_height = k_y

            # prirátanie váhy
            self._current_weight += k_w

            # prirátanie plochy (globálne – nezáleží na tom, na ktorom plechu)
            used_area += k_s

            # posun v osi x
            self._shelf_x += k_x

            # uloženie výsledku
            self.komponent_res.append(
                [self._sheet_no, komponent[0], komponent[3], komponent[4], self._shelf_x, self._shelf_y, k_x, k_y]
            )

        if self._current_weight > 0:
            used_weight += self._current_weight
            total_sheets = self._sheet_no + 1 
        else:
            total_sheets = self._sheet_no

        self._set_stats(total_sheets, used_weight, used_area)

    # --------- NOVY PLECH ---------
    def _new_sheet(self):
        self._sheet_no += 1
        self._shelf_x = 0.0
        self._shelf_y = 0.0
        self._shelf_height = 0.0
        self._current_weight = 0.0

    # --------- ULOZENIE STATOV ---------
    def _set_stats(self, total_sheets, used_weight, used_area):
        self.sheet_avg_weight = used_weight / total_sheets
        self.sheet_avg_weight_pct = (self.sheet_avg_weight / self.MAX_WEIGHT) * 100.0
        avg_area_per_sheet = used_area / total_sheets
        self.sheet_avg_area = avg_area_per_sheet
        max_area_per_sheet = self.MAX_WIDTH * self.MAX_HEIGHT
        self.sheet_avg_area_pct = (avg_area_per_sheet / max_area_per_sheet) * 100.0

    # --------- ZAPISANIE DO CSV ---------
    def _write_csv(self):
        with open('./output/shelf_output.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            for item in self.komponent_res:
                writer.writerow(item)
