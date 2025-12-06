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
        root.geometry("1200x820")
        root.configure(bg="#f5f5f5")

        self.running = False
        self.data_cpu = []
        self.data_ram = []
        self.last_timestamp = None
        self.current_mode = "CPU"   # CPU / RAM

        # ===== STYLE =====
        style = ttk.Style()
        style.theme_use("default")

        style.configure("Green.TButton", background="#3b8f3e", foreground="white",
                        font=("Arial", 11, "bold"), padding=10)
        style.configure("Brown.TButton", background="#5a330a", foreground="white",
                        font=("Arial", 11, "bold"), padding=10)
        style.configure("Black.TButton", background="black", foreground="white",
                        font=("Arial", 11, "bold"), padding=10)

        # ===== BAŞLIK =====
        tk.Label(root, text="Seri Port Veri Alıcı & Analiz",
                 font=("Arial", 20, "bold"),
                 bg="#f5f5f5", fg="black").grid(row=0, column=0, columnspan=2, pady=20)

        # ===== AYAR PANELİ =====
        frame = tk.Frame(root, bg="white", highlightbackground="black", highlightthickness=1)
        frame.grid(row=1, column=0, columnspan=2, padx=30, pady=10, sticky="ew")

        tk.Label(frame, text="Seri Port:", bg="white", fg="black").grid(row=0, column=0, padx=10, pady=10)
        self.port_combo = ttk.Combobox(frame, width=30)
        self.port_combo.grid(row=0, column=1, padx=10, pady=10)
        self.refresh_ports()

        tk.Label(frame, text="Baudrate:", bg="white", fg="black").grid(row=1, column=0, padx=10, pady=10)
        self.baud_entry = tk.Entry(frame, width=30, fg="black", bg="white")
        self.baud_entry.insert(0, "9600")
        self.baud_entry.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(frame, text="CPU Eşik (%):", bg="white", fg="black").grid(row=0, column=2, padx=10, pady=10)
        self.cpu_threshold = tk.Entry(frame, width=15, fg="black", bg="white")
        self.cpu_threshold.insert(0, "10")
        self.cpu_threshold.grid(row=0, column=3, padx=10, pady=10)

        # ===== SOL PANEL =====
        box = tk.Frame(root, bg="white", highlightbackground="black", highlightthickness=1)
        box.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")

        tk.Label(box, text="Alınan Veri", bg="white", fg="black",
                 font=("Arial", 11, "bold")).pack(pady=8)

        self.lbl_date = tk.Label(box, text="Tarih:", bg="white", fg="black")
        self.lbl_date.pack(anchor="w", padx=15)

        self.lbl_time = tk.Label(box, text="Saat:", bg="white", fg="black")
        self.lbl_time.pack(anchor="w", padx=15)

        self.lbl_cpu = tk.Label(box, text="CPU:", bg="white", fg="black")
        self.lbl_cpu.pack(anchor="w", padx=15)

        self.lbl_ram = tk.Label(box, text="RAM:", bg="white", fg="black")
        self.lbl_ram.pack(anchor="w", padx=15)

        self.status_label = tk.Label(box, text="Durum: Bekleniyor", bg="white", fg="black")
        self.status_label.pack(anchor="w", padx=15, pady=10)

        # ===== SAĞ GRAFİK =====
        graph_frame = tk.Frame(root, bg="white", highlightbackground="black", highlightthickness=1)
        graph_frame.grid(row=2, column=1, padx=20, pady=20, sticky="nsew")

        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # ===== GRAFİK SEÇİM BUTONLARI =====
        switch_frame = tk.Frame(root, bg="#f5f5f5")
        switch_frame.grid(row=3, column=1, pady=10)

        ttk.Button(switch_frame, text="CPU Grafiği",
                   style="Green.TButton",
                   command=self.show_cpu).grid(row=0, column=0, padx=20)

        ttk.Button(switch_frame, text="RAM Grafiği",
                   style="Brown.TButton",
                   command=self.show_ram).grid(row=0, column=1, padx=20)

        # ===== KONTROL BUTONLARI =====
        btn_frame = tk.Frame(root, bg="#f5f5f5")
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)

        self.start_btn = ttk.Button(btn_frame, text="Alımı Başlat",
                                    style="Green.TButton",
                                    command=self.start)
        self.start_btn.grid(row=0, column=0, padx=20)

        self.stop_btn = ttk.Button(btn_frame, text="Alımı Durdur",
                                   style="Brown.TButton",
                                   command=self.stop)
        self.stop_btn.grid(row=0, column=1, padx=20)

        self.exit_btn = ttk.Button(btn_frame, text="Alımı Bitir",
                                   style="Black.TButton",
                                   command=self.exit_app)
        self.exit_btn.grid(row=0, column=2, padx=20)

        # ===== İSTATİSTİK =====
        self.avg_label = tk.Label(root, text="Ortalama: -", bg="#f5f5f5", fg="black")
        self.avg_label.grid(row=5, column=1, sticky="w", padx=25)

        self.std_label = tk.Label(root, text="Standart Sapma: -", bg="#f5f5f5", fg="black")
        self.std_label.grid(row=6, column=1, sticky="w", padx=25)

        self.alarm_label = tk.Label(root, text="ALARM: YOK", bg="#f5f5f5",
                                    fg="green", font=("Arial", 11, "bold"))
        self.alarm_label.grid(row=7, column=1, sticky="w", padx=25)

    def show_cpu(self):
        self.current_mode = "CPU"

    def show_ram(self):
        self.current_mode = "RAM"

    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [p.device for p in ports]
        forced = "/dev/ttys006"
        if forced not in port_list:
            port_list.append(forced)
        self.port_combo["values"] = port_list
        if port_list:
            self.port_combo.set(port_list[0])

    def start(self):
        self.running = True
        self.data_cpu.clear()
        self.data_ram.clear()
        self.last_timestamp = None
        self.status_label.config(text="Durum: Çalışıyor")

        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.csv_file = f"veri_kaydi_{now}.csv"
        self.alarm_file = f"alarm_log_{now}.csv"

        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Tarih", "Saat", "CPU", "RAM", "ALARM"])

        with open(self.alarm_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Tarih", "Saat", "CPU", "Eşik"])

        self.ser = serial.Serial(self.port_combo.get(),
                                 int(self.baud_entry.get()),
                                 timeout=1)

        threading.Thread(target=self.receive_loop, daemon=True).start()

    def stop(self):
        self.running = False
        self.status_label.config(text="Durum: Durduruldu")

    def exit_app(self):
        self.running = False
        try:
            self.ser.close()
        except:
            pass
        self.root.destroy()

    def receive_loop(self):
        while self.running:
            try:
                line = self.ser.readline().decode().strip()
                if not line:
                    continue

                tarih, saat, cpu, ram = line.split(",")
                cpu = float(cpu)
                ram = float(ram)

                ts = f"{tarih} {saat}"
                if self.last_timestamp == ts:
                    continue
                self.last_timestamp = ts

                threshold = float(self.cpu_threshold.get())
                alarm = 1 if cpu >= threshold else 0

                self.lbl_date.config(text=f"Tarih: {tarih}")
                self.lbl_time.config(text=f"Saat: {saat}")
                self.lbl_cpu.config(text=f"CPU: {cpu}")
                self.lbl_ram.config(text=f"RAM: {ram}")

                with open(self.csv_file, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([tarih, saat, cpu, ram, alarm])

                if alarm:
                    with open(self.alarm_file, "a", newline="") as f:
                        csv.writer(f).writerow([tarih, saat, cpu, threshold])

                self.data_cpu.append(cpu)
                self.data_ram.append(ram)

                self.update_graph(threshold)
            except:
                pass

    def update_graph(self, threshold):
        self.ax.clear()

        if self.current_mode == "CPU":
            y = self.data_cpu
            over = [v for v in y if v >= threshold]

            self.ax.plot(range(len(y)), y, color="blue", label="CPU")
            self.ax.axhline(y=threshold, color="red", linestyle="--", label="CPU Eşik")

            y_min = max(0, threshold - 10)
            y_max = threshold + 10
            self.ax.set_ylim(y_min, y_max)

            if over:
                self.avg_label.config(text=f"Ortalama: {np.mean(over):.2f}")
                self.std_label.config(text=f"Standart Sapma: {np.std(over):.2f}")

            self.alarm_label.config(text="ALARM: CPU EŞİĞİ AŞILDI!" if over else "ALARM: YOK",
                                    fg="red" if over else "green")

            self.ax.set_title("CPU Kullanımı (%)")

        else:
            y = self.data_ram
            self.ax.plot(range(len(y)), y, color="purple", label="RAM")
            self.ax.set_ylim(0, 100)
            self.ax.set_title("RAM Kullanımı (%)")
            self.alarm_label.config(text="ALARM: RAM için aktif değil", fg="black")

        self.ax.set_xlabel("Zaman")
        self.ax.set_ylabel("%")
        self.ax.legend()
        self.canvas.draw()


if __name__ == "__main__":
    root = tk.Tk()
    app = ReceiverApp(root)
    root.mainloop()