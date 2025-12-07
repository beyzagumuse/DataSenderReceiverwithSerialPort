import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import threading
import csv
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np


class ReceiverApp:
    def __init__(self, root):
        self.root = root
        root.title("Seri Port Veri Alıcı & Analiz")

        # ==== 🔥 RESPONSIVE TAM EKRAN ====
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        root.geometry(f"{screen_w}x{screen_h}")
        root.configure(bg="#f5f5f5")

        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=2)
        root.grid_rowconfigure(2, weight=1)

        self.running = False
        self.data_cpu = []
        self.data_ram = []
        self.last_timestamp = None
        self.current_graph = "CPU"

        # ===== STYLE =====
        style = ttk.Style()
        style.theme_use("default")

        style.configure("Green.TButton", background="#3b8f3e", foreground="white", font=("Arial", 11, "bold"), padding=10)
        style.configure("Brown.TButton", background="#5a330a", foreground="white", font=("Arial", 11, "bold"), padding=10)
        style.configure("Blue.TButton", background="#312edc", foreground="white", font=("Arial", 11, "bold"), padding=10)
        style.configure("Orange.TButton", background="#dca42b", foreground="white", font=("Arial", 11, "bold"), padding=10)
        style.configure("Black.TButton", background="black", foreground="white", font=("Arial", 11, "bold"), padding=10)

        # ===== BAŞLIK =====
        tk.Label(root, text="Seri Port Veri Alıcı & Analiz",
                 font=("Arial", 20, "bold"),
                 bg="#f5f5f5", fg="black").grid(row=0, column=0, columnspan=2, pady=20)

        # ===== AYAR PANELİ =====
        frame = tk.Frame(root, bg="white", highlightbackground="black", highlightthickness=1)
        frame.grid(row=1, column=0, columnspan=2, padx=30, pady=10, sticky="ew")

        frame.grid_columnconfigure(1, weight=1)
        frame.grid_columnconfigure(3, weight=1)

        tk.Label(frame, text="Seri Port:", bg="white", fg="black").grid(row=0, column=0, padx=10, pady=10)
        self.port_combo = ttk.Combobox(frame)
        self.port_combo.grid(row=0, column=1, sticky="ew", padx=10)

        tk.Label(frame, text="Baudrate:", bg="white", fg="black").grid(row=1, column=0, padx=10)
        self.baud_entry = tk.Entry(frame, fg="black", bg="white")
        self.baud_entry.insert(0, "9600")
        self.baud_entry.grid(row=1, column=1, sticky="ew", padx=10)

        tk.Label(frame, text="CPU Eşik (%):", bg="white", fg="black").grid(row=0, column=2)
        self.cpu_threshold = tk.Entry(frame, fg="black", bg="white")
        self.cpu_threshold.insert(0, "10")
        self.cpu_threshold.grid(row=0, column=3, sticky="ew", padx=10)

        tk.Label(frame, text="RAM Eşik (%):", bg="white", fg="black").grid(row=1, column=2)
        self.ram_threshold = tk.Entry(frame, fg="black", bg="white")
        self.ram_threshold.insert(0, "10")
        self.ram_threshold.grid(row=1, column=3, sticky="ew", padx=10)

        self.refresh_ports()

        # ===== GRAFİK BUTONLARI =====
        graph_btns = tk.Frame(root, bg="#f5f5f5")
        graph_btns.grid(row=3, column=0, sticky="w", padx=40)

        ttk.Button(graph_btns, text="CPU Grafiği", style="Blue.TButton",
                   command=lambda: self.change_graph("CPU")).grid(row=0, column=0, padx=10)

        ttk.Button(graph_btns, text="RAM Grafiği", style="Orange.TButton",
                   command=lambda: self.change_graph("RAM")).grid(row=0, column=1, padx=10)

        # ===== ANA BUTONLAR =====
        btn_frame = tk.Frame(root, bg="#f5f5f5")
        btn_frame.grid(row=3, column=1, pady=20)

        self.start_btn = ttk.Button(btn_frame, text="Alımı Başlat", style="Green.TButton", command=self.start)
        self.stop_btn = ttk.Button(btn_frame, text="Alımı Durdur", style="Brown.TButton", command=self.stop)
        self.exit_btn = ttk.Button(btn_frame, text="Alımı Bitir", style="Black.TButton", command=self.exit_app)

        self.start_btn.grid(row=0, column=0, padx=10)
        self.stop_btn.grid(row=0, column=1, padx=10)
        self.exit_btn.grid(row=0, column=2, padx=10)

        # ===== SOL PANEL =====
        box = tk.Frame(root, bg="white", highlightbackground="black", highlightthickness=1)
        box.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")

        tk.Label(box, text="Alınan Veri", bg="white", fg="black", font=("Arial", 11, "bold")).pack(pady=8)
        self.lbl_date = tk.Label(box, text="Tarih:", bg="white")
        self.lbl_time = tk.Label(box, text="Saat:", bg="white")
        self.lbl_cpu = tk.Label(box, text="CPU:", bg="white")
        self.lbl_ram = tk.Label(box, text="RAM:", bg="white")
        self.status_label = tk.Label(box, text="Durum: Bekleniyor", bg="white")

        for lbl in [self.lbl_date, self.lbl_time, self.lbl_cpu, self.lbl_ram, self.status_label]:
            lbl.pack(anchor="w", padx=15)

        # ===== SAĞ GRAFİK =====
        graph_frame = tk.Frame(root, bg="white", highlightbackground="black", highlightthickness=1)
        graph_frame.grid(row=2, column=1, padx=20, pady=20, sticky="nsew")

        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # ===== İSTATİSTİK =====
        self.avg_label = tk.Label(root, text="Ortalama: -", bg="#f5f5f5")
        self.std_label = tk.Label(root, text="Standart Sapma: -", bg="#f5f5f5")
        self.alarm_label = tk.Label(root, text="ALARM: YOK", fg="green", bg="#f5f5f5", font=("Arial", 11, "bold"))

        self.avg_label.grid(row=4, column=1, sticky="w", padx=25)
        self.std_label.grid(row=5, column=1, sticky="w", padx=25)
        self.alarm_label.grid(row=6, column=1, sticky="w", padx=25)

    # ==== GRAFİK ====
    def update_graph(self, threshold, alarm):
        self.ax.clear()

        if self.current_graph == "CPU":
            y_vals = self.data_cpu
        else:
            y_vals = self.data_ram

        above_x = [i for i, v in enumerate(y_vals) if v >= threshold]
        above_y = [v for v in y_vals if v >= threshold]

        self.ax.plot(y_vals)
        self.ax.scatter(above_x, above_y)
        self.ax.axhline(y=threshold, linestyle="--")

        self.ax.set_ylim(max(0, threshold - 10), threshold + 10)
        self.canvas.draw()

        self.alarm_label.config(text="ALARM VAR!" if alarm else "ALARM YOK",
                                fg="red" if alarm else "green")

    def change_graph(self, g):
        self.current_graph = g

    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        self.port_combo["values"] = [p.device for p in ports]
        if ports:
            self.port_combo.set(ports[0].device)

    def start(self):
        self.running = True
        self.status_label.config(text="Durum: Çalışıyor")

    def stop(self):
        self.running = False
        self.status_label.config(text="Durum: Durduruldu")

    def exit_app(self):
        self.running = False
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ReceiverApp(root)
    root.mainloop()