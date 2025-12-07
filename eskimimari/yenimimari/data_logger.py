import csv
from datetime import datetime

class DataLogger:
    def __init__(self, filename="veri_kaydi.csv"):
        self.filename = filename
        self._write_header()

    def _write_header(self):
        try:
            with open(self.filename, "x", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Tarih", "Saat", "CPU", "RAM"])
        except FileExistsError:
            pass

    def log(self, date_str, time_str, cpu, ram):
        with open(self.filename, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([date_str, time_str, cpu, ram])