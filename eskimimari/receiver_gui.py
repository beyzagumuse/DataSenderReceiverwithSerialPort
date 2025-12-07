import serial
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import csv
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import statistics

class ReceiverGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Seri Port Veri Alıcı & Analiz")
        self.root.geometry("900x600")

        self.serial_port = None
        self.is_receiving = False

        self.cpu_values = []
        self.time_values = []

        # PORT
        tk.Label(root, text="Seri Port:").place(x=20, y=20)
        self.port_combo = ttk.Combobox(root, values=["/dev/ttys006"])
        self.port_combo.place(x=120, y=20)

        # BAUD
        tk.Label(root, text="Baudrate:").place(x=20, y=60)
        self.baud_entry = tk.Entry(root)
        self.baud_entry.insert(0, "9600")
        self.baud_entry.place(x=120, y=60)

        # CPU EŞİK
        tk.Label(root, text="CPU Eşik (%):").place(x=20, y=100)
        self.threshold_entry = tk.Entry(root)
        self.threshold_entry.insert(0, "10")
        self.threshold_entry.place(x=120, y=100)

        # BUTONLAR
        tk.Button(root, text="Alımı Başlat", command=self.start_receiving).place(x=20, y=150)
        tk.Button(root, text="Alımı Durdur", command=self.stop_receiving).place(x=140, y=150)

        # TABLO
        self.tree = ttk.Treeview(root, columns=("time", "cpu", "ram"), show="headings", height=8)
        self.tree.heading("time", text="Tarih & Saat")
        self.tree.heading("cpu", text="CPU (%)")
        self.tree.heading("ram", text="RAM (%)")
        self.tree.place(x=320, y=20)

        # DURUM
        self.status_label = tk.Label(root, text="Durum: Bekleniyor", fg="blue")
        self.status_label.place(x=20, y=200)

        # İSTATİSTİK
        self.stat_label = tk.Label(root, text="Ortalama: -   Std Sapma: -", fg="purple")
        self.stat_label.place(x=20, y=240)

        # CSV
        self.file = open("veri_kaydi.csv", "a", newline="")
        self.writer = csv.writer(self.file)

        # GRAFİK
        self.fig, self.ax = plt.subplots()
        self.ax.set_title("Canlı CPU Kullanımı")
        self.ax.set_xlabel("Ölçüm")
        self.ax.set_ylabel("CPU %")
        self.line, = self.ax.plot([], [])

        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().place(x=20, y=280, width=850, height=300)

    def start_receiving(self):
        port = self.port_combo.get()
        baud = int(self.baud_entry.get())

        try:
            self.serial_port = serial.Serial(port, baud, timeout=1)
            self.is_receiving = True
            self.status_label.config(text="Durum: Veri Alınıyor", fg="green")

            thread = threading.Thread(target=self.receive_data)
            thread.daemon = True
            thread.start()

        except:
            messagebox.showerror("HATA", "Seri port açılamadı!")

    def stop_receiving(self):
        self.is_receiving = False
        self.status_label.config(text="Durum: Durduruldu", fg="red")
        if self.serial_port:
            self.serial_port.close()

    def receive_data(self):
        while self.is_receiving:
            try:
                data = self.serial_port.readline().decode().strip()
                if data:
                    parts = data.split(",")

                    if len(parts) == 3:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cpu = float(parts[1])
                        ram = float(parts[2])

                        # TABLO
                        self.tree.insert("", "end", values=(timestamp, cpu, ram))
                        self.tree.yview_moveto(1)

                        # CSV (TARİHLİ)
                        self.writer.writerow([timestamp, cpu, ram])
                        self.file.flush()

                        # GRAFİK
                        self.cpu_values.append(cpu)

                        if len(self.cpu_values) > 50:
                            self.cpu_values.pop(0)

                        self.line.set_data(range(len(self.cpu_values)), self.cpu_values)
                        self.ax.set_xlim(0, 50)
                        self.ax.set_ylim(0, 100)
                        self.canvas.draw()

                        # ✅ HER ZAMAN ORTALAMA & STD HESAPLA
                        if len(self.cpu_values) > 1:
                            avg = round(statistics.mean(self.cpu_values), 2)
                            std = round(statistics.stdev(self.cpu_values), 2)
                        else:
                            avg = cpu
                            std = 0

                        self.stat_label.config(
                            text=f"Ortalama: {avg}   Std Sapma: {std}",
                            fg="purple"
                        )

                        # 🔴 SADECE EŞİK AŞINCA KIRMIZIYA DÖN
                        threshold = float(self.threshold_entry.get())
                        if cpu > threshold:
                            self.stat_label.config(fg="red")

            except:
                pass


root = tk.Tk()
app = ReceiverGUI(root)
root.mainloop()