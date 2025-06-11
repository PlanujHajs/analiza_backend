import pandas as pd
import numpy as np
import os

class ChartsService:
    BUILDING_STATISTICS_FILE = os.path.join('data', 'budownictwo_mieszkaniowe_w_styczniu_2025_roku_tabela_2.xls')
    HOUSING_PRICES_FILE = os.path.join('data', 'wskazniki_cen_lokali_mieszkalnych_clean.csv')

    MONTHS_ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
    QUARTERS = {
        'Q1': ['I', 'II', 'III'],
        'Q2': ['IV', 'V', 'VI'],
        'Q3': ['VII', 'VIII', 'IX'],
        'Q4': ['X', 'XI', 'XII']
    }
    CATEGORIES = ['OGÓŁEM', 'indywidualne', 'sprzedaż lub wynajem', 'spółdzielcze', 'pozostałe']

    def get_building_statistics(self) -> pd.DataFrame:
        monthly_data = self._get_monthly_building_data()
        quarterly_data = self._convert_monthly_to_quarterly(monthly_data)

        return quarterly_data

    def _get_monthly_building_data(self) -> pd.DataFrame:
        df = pd.read_excel(self.BUILDING_STATISTICS_FILE)
        result = {category: {} for category in self.CATEGORIES}
        row_idx = 121  # Starting row index (1 + 6 * (2011 - 1991)) - Start from 2011

        while row_idx + 4 < (len(df) - 7):
            year = df.iloc[row_idx, 1]
            if isinstance(year, str):
                year = year[:4]

            block = df.iloc[row_idx + 1:row_idx + 6, :].copy()
            block.set_index(block.columns[0], inplace=True)

            block = block.replace('-', '0').astype(int)

            for category in self.CATEGORIES:
                cum_values = block.loc[category].values
                monthly_values = np.diff(np.insert(cum_values, 0, 0))

                for month_label, month_value in zip(self.MONTHS_ROMAN, monthly_values):
                    col = f'{int(year)}-{month_label}'
                    result[category][col] = month_value

            row_idx += 6  # Move to the next year block

        result_df = pd.DataFrame.from_dict(result, orient='index')
        df_monthly = result_df.reindex(
            sorted(result_df.columns, key=lambda x: (int(x.split('-')[0]), self.MONTHS_ROMAN.index(x.split('-')[1]))),
            axis=1
        )

        return df_monthly

    def _convert_monthly_to_quarterly(self, df_monthly: pd.DataFrame) -> pd.DataFrame:
        quarterly_data = {category: {} for category in df_monthly.index}

        for category in quarterly_data.keys():
            for column in df_monthly.columns:
                year, month = column.split('-')

                quarter = next(q for q, months_in_q in self.QUARTERS.items() if month in months_in_q)
                quarter_key = f"{year}-{quarter}"

                if quarter_key not in quarterly_data[category]:
                    quarterly_data[category][quarter_key] = 0

                quarterly_data[category][quarter_key] += df_monthly.loc[category, column]

        df_quarterly = pd.DataFrame.from_dict(quarterly_data, orient='index')
        df_quarterly = df_quarterly.reindex(
            sorted(df_quarterly.columns,
                   key=lambda x: (int(x.split('-')[0]), ['Q1', 'Q2', 'Q3', 'Q4'].index(x.split('-')[1]))),
            axis=1
        )

        return df_quarterly

    def get_housing_prices(self) -> pd.DataFrame:
        df = pd.read_csv(self.HOUSING_PRICES_FILE, sep=';', decimal=',', index_col=0)

        return df