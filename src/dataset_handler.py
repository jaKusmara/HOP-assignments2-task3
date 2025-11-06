import pandas as pd
import numpy as np
from src.utils import *

class DatasetHandler:
    def __init__(self, path):
        self.path = path
        self.df = None

    def load(self):
        self.df = pd.read_csv(self.path, names=['sn', 'dim', 'weight', 'count', 'timestamp'])
        return self.df
    
    def prepare_data(self):
        df = self.df.copy()

        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp']).sort_values('timestamp')

        df['dim'] = convertTo2D(df['dim'].str.split('x'))
        df['square'] = calcSquare(df['dim'])
        df['stressSquare'] = df['weight'] / df['square'].replace(0, pd.NA)

        # 3) Oddelenie dátumu a času
        df['date'] = df['timestamp'].dt.date
        df['time'] = df['timestamp'].dt.time

        # 4) Rozdelenie podľa polovice dňa
        parts = []
        cols = ['sn', 'dim', 'weight', 'count', 'date', 'time', 'square', 'stressSquare']

        for day in sorted(df['date'].unique()):
            day_df = df[df['date'] == day]

            # 1. polovica dňa (00:00–11:59:59)
            first_half = day_df[day_df['timestamp'].dt.hour < 12][cols]
            first_half_values = [
                [
                    row['sn'],
                    list(row['dim']),
                    row['weight'],
                    row['count'],
                    row['date'].isoformat(),
                    row['time'].isoformat(),
                    row['square'],
                    row['stressSquare'],
                ]
                for _, row in first_half.iterrows()
            ]
            parts.append(first_half_values)

            # 2. polovica dňa (12:00–23:59:59)
            second_half = day_df[day_df['timestamp'].dt.hour >= 12][cols]
            second_half_values = [
                [
                    row['sn'],
                    list(row['dim']),
                    row['weight'],
                    row['count'],
                    row['date'].isoformat(),
                    row['time'].isoformat(),
                    row['square'],
                    row['stressSquare'],
                ]
                for _, row in second_half.iterrows()
            ]
            parts.append(second_half_values)

        return parts