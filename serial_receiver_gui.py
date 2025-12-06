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
        root.geometry("1200x800")
        root.configure(bg="#f5f5f5")
        self.last_timestamp = None
        

        self.running = False
        self.data_cpu = []

        # ===== GRID ANA YAPI (RESPONSIVE) =====
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=3)
        root.rowconfigure(0, weight=0)
        root.rowconfigure(1, weight=0)
        root.rowconfigure(2, weight=1)
        root.rowconfigure(3, weight=0)

        # ===== STYLE (SENDER İLE AYNI) =====
        style = ttk.Style()
        style.theme_use("default")

        style.configure("Green.TButton",
                        background="#3b8f3e",
                        foreground="white",
                        font=("Arial", 11, "bold"),
                        padding=10)

        style.configure("Brown.TButton",
                        background="#5a330a",
                        foreground="white",
                        font=("Arial", 11, "bold"),
                        padding=10)

        style.configure("Black.TButton",
                        background="black",
                        foreground="white",
                        font=("Arial", 11, "bold"),
                        padding=10)

        # ===== BAŞLIK =====
        tk.Label(root, text="Seri Port Veri Alıcı & Analiz",
                 font=("Arial", 20, "bold"),
                 bg="#f5f5f5", fg="black").grid(row=0, column=0, columnspan=2, pady=20)

        # ===== AYAR PANELİ =====
        frame = tk.Frame(root, bg="white", highlightbackground="black", highlightthickness=1)
        frame.grid(row=1, column=0, columnspan=2, padx=30, pady=10, sticky="ew")
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=1)

        tk.Label(frame, text="Seri Port:", bg="white", fg="black").grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.port_combo = ttk.Combobox(frame, width=30)
        self.port_combo.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.refresh_ports()

        tk.Label(frame, text="Baudrate:", bg="white", fg="black").grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.baud_entry = tk.Entry(frame, width=30, fg="black", bg="white")
        self.baud_entry.insert(0, "9600")
        self.baud_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        tk.Label(frame, text="CPU Eşik (%):", bg="white", fg="black").grid(row=0, column=2, padx=10, pady=10, sticky="w")

        self.cpu_threshold = tk.Entry(frame, width=15, fg="black", bg="white")
        self.cpu_threshold.insert(0, "50")
        self.cpu_threshold.grid(row=0, column=3, padx=10, pady=10, sticky="w")

        # ===== BUTONLAR =====
        btn_frame = tk.Frame(root, bg="#f5f5f5")
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)

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

        # ===== SOL: ALINAN VERİ =====
        box = tk.Frame(root, bg="white", highlightbackground="black", highlightthickness=1)
        box.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")
        box.columnconfigure(0, weight=1)

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

        # ===== SAĞ: GRAFİK (RESPONSIVE) =====
        graph_frame = tk.Frame(root, bg="white", highlightbackground="black", highlightthickness=1)
        graph_frame.grid(row=2, column=1, padx=20, pady=20, sticky="nsew")

        graph_frame.rowconfigure(0, weight=1)
        graph_frame.columnconfigure(0, weight=1)

        self.fig, self.ax = plt.subplots()
        self.ax.set_title("CPU Kullanımı (%)")
        self.ax.set_xlabel("Zaman")
        self.ax.set_ylabel("CPU %")

        self.line, = self.ax.plot([], [])

        # Eşik çizgisi (kırmızı yatay çizgi)
        self.threshold_line = self.ax.axhline(
            y=float(self.cpu_threshold.get()),
            color="red",
            linestyle="--",
            linewidth=2,
            label="CPU Eşik"
        )

        self.ax.legend()

        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        # ===== İSTATİSTİK =====
        self.avg_label = tk.Label(root, text="Ortalama: -", bg="#f5f5f5", fg="black")
        self.avg_label.grid(row=4, column=1, sticky="w", padx=25)

        self.std_label = tk.Label(root, text="Standart Sapma: -", bg="#f5f5f5", fg="black")
        self.std_label.grid(row=5, column=1, sticky="w", padx=25)

    # ===== TÜM PORTLARI LİSTELE =====
    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [p.device for p in ports]

        forced = "/dev/ttys006"
        if forced not in port_list:
            port_list.append(forced)

        self.port_combo["values"] = port_list
        if port_list:
            self.port_combo.set(port_list[0])

    # ===== BAŞLAT =====
    def start(self):
        self.running = True
        self.status_label.config(text="Durum: Çalışıyor")

        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.csv_file = f"veri_kaydi_{now}.csv"

        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Tarih", "Saat", "CPU", "RAM"])

        self.ser = serial.Serial(self.port_combo.get(),
                                 int(self.baud_entry.get()),
                                 timeout=1)

        threading.Thread(target=self.receive_loop, daemon=True).start()

    # ===== DURDUR =====
    def stop(self):
        self.running = False
        self.status_label.config(text="Durum: Durduruldu")

    # ===== ÇIKIŞ =====
    def exit_app(self):
        self.running = False
        try:
            self.ser.close()
        except:
            pass
        self.root.destroy()

    # ===== VERİ OKUMA =====
    def receive_loop(self):
        while self.running:
            try:
                line = self.ser.readline().decode().strip()
                if not line:
                    continue

                tarih, saat, cpu, ram = line.split(",")
                cpu = float(cpu)
                ram = float(ram)

                current_timestamp = f"{tarih} {saat}"

                # ✅ AYNI SANİYE İÇİN TEKRAR YAZMA
                if self.last_timestamp == current_timestamp:
                    continue

                self.last_timestamp = current_timestamp

                self.lbl_date.config(text=f"Tarih: {tarih}")
                self.lbl_time.config(text=f"Saat: {saat}")
                self.lbl_cpu.config(text=f"CPU: {cpu}")
                self.lbl_ram.config(text=f"RAM: {ram}")

                with open(self.csv_file, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([tarih, saat, cpu, ram])

                self.data_cpu.append(cpu)

                x_vals = list(range(len(self.data_cpu)))
                y_vals = self.data_cpu

                threshold = float(self.cpu_threshold.get())

                # Çizgiyi temizle
                self.ax.clear()

                # Eşik altı ve üstü ayır
                below_x = [i for i, v in zip(x_vals, y_vals) if v < threshold]
                below_y = [v for v in y_vals if v < threshold]

                above_x = [i for i, v in zip(x_vals, y_vals) if v >= threshold]
                above_y = [v for v in y_vals if v >= threshold]

                # Eşik altı → mavi çizgi
                # ✅ HER ZAMAN TÜM VERİYİ MAVİ ÇİZ
                self.ax.plot(x_vals, y_vals, color="blue", label="Normal")

                # Eşik üstü → kırmızı nokta
                self.ax.scatter(above_x, above_y, color="red", label="Kritik")

                # Eşik yatay çizgisi
                self.ax.axhline(y=threshold, color="red", linestyle="--", linewidth=2, label="CPU Eşik")

                self.ax.set_title("CPU Kullanımı (%)")
                self.ax.set_xlabel("Zaman")
                self.ax.set_ylabel("CPU %")
                self.ax.legend()

                # ----- SABİT EŞİK ODAKLI Y-AXIS -----
                y_min = max(0, threshold - 10)
                y_max = threshold + 10

                self.ax.set_ylim(y_min, y_max)
                self.canvas.draw()

                over = [x for x in self.data_cpu if x >= threshold]

                if over:
                    avg = np.mean(over)
                    std = np.std(over)
                    self.avg_label.config(text=f"Ortalama: {avg:.2f}")
                    self.std_label.config(text=f"Standart Sapma: {std:.2f}")

            except:
                pass


if __name__ == "__main__":
    root = tk.Tk()
    app = ReceiverApp(root)
    root.mainloop()