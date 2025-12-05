import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import threading
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import os
from datetime import datetime

BAUDRATE = 9600
FORCED_PORT = "/dev/ttys006"

class SerialReceiverGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Seri Port Veri Alıcı & Analiz")
        self.root.geometry("1050x700")

        self.running = False
        self.cpu_values = []
        self.ser = None

        # ================= ÜST KONTROL ALANI (ÇAKIŞMASIZ) =================
        control_frame = tk.Frame(root)
        control_frame.place(x=30, y=10, width=980, height=60)

        # --- 1. SATIR: PORT ---
        tk.Label(control_frame, text="Receiver Port:",
                 font=("Arial", 11, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.port_combo = ttk.Combobox(control_frame, width=25)
        self.port_combo.grid(row=0, column=1, padx=5, pady=5)

        self.refresh_btn = ttk.Button(control_frame, text="Portları Yenile",
                                      command=self.refresh_ports)
        self.refresh_btn.grid(row=0, column=2, padx=10, pady=5)

        # --- 2. SATIR: EŞİK + BUTONLAR ---
        tk.Label(control_frame, text="CPU Eşik (%):",
                 font=("Arial", 11, "bold")).grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.threshold_entry = tk.Entry(control_frame, width=10)
        self.threshold_entry.insert(0, "50")
        self.threshold_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        self.start_btn = ttk.Button(control_frame, text="Alımı Başlat", command=self.start)
        self.start_btn.grid(row=1, column=2, padx=10, pady=5)

        self.stop_btn = ttk.Button(control_frame, text="Alımı Durdur", command=self.stop)
        self.stop_btn.grid(row=1, column=3, padx=10, pady=5)

        # İlk açılışta portları yükle
        self.refresh_ports()

        # ================= GRAFİK =================
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [])
        self.ax.set_title("CPU Kullanımı (%)")
        self.ax.set_xlabel("Zaman")
        self.ax.set_ylabel("CPU %")

        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().place(x=30, y=90, width=980, height=430)

        # ================= ANALİZ SONUÇLARI =================
        self.mean_lbl = tk.Label(root, text="Ortalama: -", font=("Arial", 11, "bold"))
        self.mean_lbl.place(x=30, y=540)

        self.std_lbl = tk.Label(root, text="Standart Sapma: -", font=("Arial", 11, "bold"))
        self.std_lbl.place(x=250, y=540)

        self.status_lbl = tk.Label(root, text="Durum: Bekleniyor",
                                   font=("Arial", 11, "bold"), fg="blue")
        self.status_lbl.place(x=520, y=540)

    # ================= PORTLARI YENİLE =================
    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]

        if FORCED_PORT not in port_list:
            port_list.append(FORCED_PORT)

        self.port_combo["values"] = port_list

        if FORCED_PORT in port_list:
            self.port_combo.set(FORCED_PORT)
        elif port_list:
            self.port_combo.set(port_list[0])
        else:
            self.port_combo.set("")

    # ================= BAŞLAT =================
    def start(self):
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.csv_file = f"veri_kaydi_{now}.csv"
        selected_port = self.port_combo.get().strip()

        if not selected_port:
            self.status_lbl.config(text="Durum: Port Seçilmedi", fg="red")
            return

        try:
            self.ser = serial.Serial(selected_port, BAUDRATE)
        except Exception:
            self.status_lbl.config(text="Durum: Port Açılamadı", fg="red")
            return

        self.running = True
        self.cpu_values.clear()
        self.status_lbl.config(text="Durum: Veri Alınıyor", fg="green")

        # CSV BAŞLIK
        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Tarih", "Saat", "CPU", "RAM"])

        threading.Thread(target=self.receive_loop, daemon=True).start()

    # ================= DURDUR =================
    def stop(self):
        self.running = False
        if self.ser:
            self.ser.close()
        self.status_lbl.config(text="Durum: Durduruldu", fg="red")

    # ================= VERİ ALMA DÖNGÜSÜ =================
    def receive_loop(self):
        time_index = 0
        x_data, y_data = [], []

        while self.running:
            try:
                raw = self.ser.readline().decode().strip()
            except:
                continue

            parts = raw.split(",")

            if len(parts) == 4:
                date, time_s, cpu, ram = parts
                cpu = float(cpu)

                # CSV KAYIT
                with open(self.csv_file, "a", newline="") as f:
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

                # EŞİK & İSTATİSTİK
                try:
                    threshold = float(self.threshold_entry.get())
                except:
                    threshold = 9999

                if cpu > threshold:
                    self.cpu_values.append(cpu)
                    mean = np.mean(self.cpu_values)
                    std = np.std(self.cpu_values)

                    self.mean_lbl.config(text=f"Ortalama: {mean:.2f}")
                    self.std_lbl.config(text=f"Standart Sapma: {std:.2f}")

# ================= UYGULAMAYI BAŞLAT =================
if __name__ == "__main__":
    root = tk.Tk()
    app = SerialReceiverGUI(root)
    root.mainloop()