import serial
import csv
from datetime import datetime
import numpy as np


class ReceiverLogic:
    def __init__(self):
        self.running = False
        self.data_cpu = []
        self.data_ram = []
        self.last_timestamp = None
        self.ser = None

    def connect(self, port, baud):
        self.ser = serial.Serial(port, baud, timeout=1)

    def disconnect(self):
        if self.ser:
            self.ser.close()

    def start_session(self):
        self.running = True
        self.data_cpu.clear()
        self.data_ram.clear()
        self.last_timestamp = None

        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.csv_file = f"veri_kaydi_{now}.csv"
        self.alarm_file = f"alarm_log_{now}.csv"

        with open(self.csv_file, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Tarih", "Saat", "CPU", "RAM", "ALARM"])

        with open(self.alarm_file, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Tarih", "Saat", "CPU", "Eşik"])

    def stop(self):
        self.running = False
        self.disconnect()

    def read_line(self):
        return self.ser.readline().decode().strip()

    def process_line(self, line, threshold):
        tarih, saat, cpu, ram = line.split(",")
        cpu = float(cpu)
        ram = float(ram)

        current_timestamp = f"{tarih} {saat}"
        if self.last_timestamp == current_timestamp:
            return None
        self.last_timestamp = current_timestamp

        alarm = 1 if cpu >= threshold else 0

        with open(self.csv_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([tarih, saat, cpu, ram, alarm])

        if alarm == 1:
            with open(self.alarm_file, "a", newline="") as af:
                aw = csv.writer(af)
                aw.writerow([tarih, saat, cpu, threshold])

        self.data_cpu.append(cpu)
        self.data_ram.append(ram)

        avg = np.mean(self.data_cpu)
        std = np.std(self.data_cpu)

        return tarih, saat, cpu, ram, alarm, avg, std