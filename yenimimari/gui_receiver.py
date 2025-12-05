import tkinter as tk
from tkinter import ttk
import serial.tools.list_ports
from serial_receiver_service import SerialReceiverService
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ReceiverGUI:
    def __init__(self, root):
        self.root = root
        self.service = SerialReceiverService()

        root.title("Seri Port Veri Alıcı")
        root.geometry("1000x700")
        root.configure(bg="#f5f5f5")

        tk.Label(root, text="Seri Port Veri Alıcı",
                 font=("Arial", 20, "bold"),
                 bg="#f5f5f5").pack(pady=10)

        tk.Label(root, text="Port:").place(x=30, y=70)
        self.port_combo = ttk.Combobox(root, width=20)
        self.port_combo.place(x=90, y=70)
        self.refresh_ports()

        tk.Label(root, text="Baud:").place(x=30, y=110)
        self.baud_entry = tk.Entry(root, width=23)
        self.baud_entry.insert(0, "9600")
        self.baud_entry.place(x=90, y=110)

        tk.Label(root, text="CPU Eşik:").place(x=30, y=150)
        self.threshold_entry = tk.Entry(root, width=23)
        self.threshold_entry.insert(0, "50")
        self.threshold_entry.place(x=90, y=150)

        tk.Button(root, text="Başlat", command=self.start).place(x=30, y=190)
        tk.Button(root, text="Durdur", command=self.stop).place(x=120, y=190)

        self.mean_lbl = tk.Label(root, text="Ortalama: -")
        self.mean_lbl.place(x=30, y=240)

        self.std_lbl = tk.Label(root, text="Std Sapma: -")
        self.std_lbl.place(x=30, y=270)

        self.cpu_data = []

        self.fig, self.ax = plt.subplots()
        self.ax.set_title("Canlı CPU Grafiği")
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().place(x=300, y=70, width=650, height=500)

    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [p.device for p in ports]

        forced_port = "/dev/ttys006"
        if forced_port not in port_list:
            port_list.append(forced_port)

        self.port_combo["values"] = port_list
        self.port_combo.set(forced_port)

    def start(self):
        port = self.port_combo.get()
        baud = int(self.baud_entry.get())
        threshold = float(self.threshold_entry.get())

        self.service.connect(port, baud)
        self.service.set_threshold(threshold)
        self.service.start(self.update_ui)

    def stop(self):
        self.service.stop()

    def update_ui(self, date_str, time_str, cpu, ram, mean, std):
        self.cpu_data.append(cpu)
        self.ax.clear()
        self.ax.plot(self.cpu_data)
        self.ax.set_title("Canlı CPU Grafiği")
        self.canvas.draw()

        self.mean_lbl.config(text=f"Ortalama: {mean:.2f}")
        self.std_lbl.config(text=f"Std Sapma: {std:.2f}")