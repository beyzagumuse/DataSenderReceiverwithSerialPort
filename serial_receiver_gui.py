import tkinter as tk
from tkinter import ttk
import serial
import threading
import csv
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

PORT = "/dev/ttys006"
BAUDRATE = 9600
CSV_FILE = "veri_kaydi.csv"

class SerialReceiverGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Seri Port Veri Alıcı & Analiz")
        self.root.geometry("1000x650")

        self.running = False
        self.cpu_values = []

        # ===== EŞİK =====
        tk.Label(root, text="CPU Eşik Değeri (%):").place(x=30, y=20)
        self.threshold_entry = tk.Entry(root)
        self.threshold_entry.insert(0, "50")
        self.threshold_entry.place(x=180, y=20)

        self.start_btn = ttk.Button(root, text="Alımı Başlat", command=self.start)
        self.start_btn.place(x=350, y=18, width=120)

        self.stop_btn = ttk.Button(root, text="Alımı Durdur", command=self.stop)
        self.stop_btn.place(x=480, y=18, width=120)

        # ===== GRAFİK =====
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [])
        self.ax.set_title("CPU Kullanımı (%)")
        self.ax.set_xlabel("Zaman")
        self.ax.set_ylabel("CPU %")

        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().place(x=30, y=80, width=920, height=400)

        # ===== ANALİZ SONUÇLARI =====
        self.mean_lbl = tk.Label(root, text="Ortalama: -")
        self.mean_lbl.place(x=30, y=520)

        self.std_lbl = tk.Label(root, text="Standart Sapma: -")
        self.std_lbl.place(x=200, y=520)

    # ===== BAŞLAT =====
    def start(self):
        self.running = True
        self.cpu_values.clear()

        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Tarih", "Saat", "CPU", "RAM"])

        self.ser = serial.Serial(PORT, BAUDRATE)
        threading.Thread(target=self.receive_loop, daemon=True).start()

    # ===== DURDUR =====
    def stop(self):
        self.running = False
        self.ser.close()

    # ===== VERİ ALMA DÖNGÜSÜ =====
    def receive_loop(self):
        time_index = 0
        x_data, y_data = [], []

        while self.running:
            raw = self.ser.readline().decode().strip()
            parts = raw.split(",")

            if len(parts) == 4:
                date, time_s, cpu, ram = parts
                cpu = float(cpu)

                # CSV KAYIT
                with open(CSV_FILE, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([date, time_s, cpu, ram])

                # GRAFİK
                x_data.append(time_index)
                y_data.append(cpu)
                time_index += 1

                self.line.set_data(x_data, y_data)
                self.ax.relim()
                self.ax.autoscale_view()
                self.canvas.draw()

                # EŞİK ANALİZİ
                threshold = float(self.threshold_entry.get())
                if cpu > threshold:
                    self.cpu_values.append(cpu)
                    mean = np.mean(self.cpu_values)
                    std = np.std(self.cpu_values)

                    self.mean_lbl.config(text=f"Ortalama: {mean:.2f}")
                    self.std_lbl.config(text=f"Standart Sapma: {std:.2f}")

# ===== UYGULAMAYI BAŞLAT =====
if __name__ == "__main__":
    root = tk.Tk()
    app = SerialReceiverGUI(root)
    root.mainloop()