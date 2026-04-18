import csv
import os
import pandas as pd

class Storage:
    def __init__(self, csv_filepath='data.csv', excel_filepath='data.xlsx'):
        self.csv_filepath = csv_filepath
        self.excel_filepath = excel_filepath
        self.fieldnames = ['Name', 'Price', 'Description', 'Product_URL', 'Image_Folder', 'Image_URLs']
        
        # Initialize CSV with headers if it doesn't exist
        if not os.path.exists(self.csv_filepath):
            with open(self.csv_filepath, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()

    def append_product(self, data):
        """Appends a single product dictionary to the CSV file safely."""
        # Sanitize missing data with defaults
        sanitized_data = {key: str(data.get(key, 'N/A')).strip() for key in self.fieldnames}
        
        with open(self.csv_filepath, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writerow(sanitized_data)

    def export_to_excel(self):
        """Converts the working CSV to a proper Excel (.xlsx) file at the end of the run."""
        try:
            print(f"Exporting dataset to Excel sheet: {self.excel_filepath}")
            df = pd.read_csv(self.csv_filepath)
            df.to_excel(self.excel_filepath, index=False, engine='openpyxl')
            print("Successfully created Excel file.")
        except Exception as e:
            print(f"Failed to export to Excel: {e}")
