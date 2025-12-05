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

BAUDRATE = 9600
FORCED_PORT = "/dev/ttys006"

class SerialReceiverGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Seri Port Veri Alıcı & Analiz")
        self.root.geometry("1200x800")
        self.root.configure(bg="white")

        self.running = False
        self.cpu_values = []
        self.ser = None

        # ================= BAŞLIK =================
        tk.Label(root, text="Seri Port Veri Alıcı & Analiz",
                 font=("Arial", 18, "bold"),
                 bg="white", fg="black").pack(pady=12)

        # ================= PORT / BAUD / EŞİK =================
        top_frame = tk.Frame(root, bg="white")
        top_frame.pack(pady=8)

        tk.Label(top_frame, text="Seri Port:", bg="white", fg="black").grid(row=0, column=0, padx=10)
        self.port_combo = ttk.Combobox(top_frame, width=28)
        self.port_combo.grid(row=0, column=1, padx=10)

        tk.Label(top_frame, text="Baudrate:", bg="white", fg="black").grid(row=0, column=2, padx=10)
        self.baud_entry = tk.Entry(top_frame, width=12, bg="white", fg="black")
        self.baud_entry.insert(0, str(BAUDRATE))
        self.baud_entry.grid(row=0, column=3, padx=10)

        tk.Label(top_frame, text="CPU Eşik (%):", bg="white", fg="black").grid(row=0, column=4, padx=10)
        self.threshold_entry = tk.Entry(top_frame, width=10, bg="white", fg="black")
        self.threshold_entry.insert(0, "50")
        self.threshold_entry.grid(row=0, column=5, padx=10)

        self.refresh_ports()

        # ================= BUTONLAR =================
        button_frame = tk.Frame(root, bg="white")
        button_frame.pack(pady=16)

        self.start_btn = tk.Button(button_frame, text="Alımı Başlat",
                                   bg="#0a7e3b", fg="white",
                                   width=26, height=2, relief="flat",
                                   command=self.start)
        self.start_btn.grid(row=0, column=0, padx=15)

        self.stop_btn = tk.Button(button_frame, text="Alımı Durdur",
                                  bg="#5a2d00", fg="white",
                                  width=26, height=2, relief="flat",
                                  command=self.stop)
        self.stop_btn.grid(row=0, column=1, padx=15)

        self.exit_btn = tk.Button(button_frame, text="Alımı Bitir",
                                  bg="black", fg="white",
                                  width=55, height=2, relief="flat",
                                  command=self.exit_app)
        self.exit_btn.grid(row=1, column=0, columnspan=2, pady=12)

        # ================= ORTA ALAN =================
        middle_frame = tk.Frame(root, bg="white")
        middle_frame.pack(fill="both", expand=True, padx=25)

        # ---- ALINAN VERİ (KÜÇÜLTÜLDÜ) ----
        left_frame = tk.LabelFrame(middle_frame, text="Alınan Veri",
                                   bg="white", fg="black", font=("Arial", 11, "bold"))
        left_frame.place(x=0, y=0, width=320, height=180)

        self.lbl_date = tk.Label(left_frame, text="Tarih:", bg="white", fg="black", anchor="w")
        self.lbl_date.pack(fill="x", padx=10, pady=3)

        self.lbl_time = tk.Label(left_frame, text="Saat:", bg="white", fg="black", anchor="w")
        self.lbl_time.pack(fill="x", padx=10, pady=3)

        self.lbl_cpu = tk.Label(left_frame, text="CPU:", bg="white", fg="black", anchor="w")
        self.lbl_cpu.pack(fill="x", padx=10, pady=3)

        self.lbl_ram = tk.Label(left_frame, text="RAM:", bg="white", fg="black", anchor="w")
        self.lbl_ram.pack(fill="x", padx=10, pady=3)

        # ---- CPU GRAFİĞİ (AŞAĞI UZATILDI) ----
        right_frame = tk.LabelFrame(middle_frame, text="CPU Kullanımı (%)",
                                    bg="white", fg="black", font=("Arial", 11, "bold"))
        right_frame.place(x=350, y=0, width=820, height=520)

        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.line, = self.ax.plot([], [])
        self.ax.set_xlabel("Zaman")
        self.ax.set_ylabel("CPU %")

        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # ================= ALT ANALİZ =================
        self.mean_lbl = tk.Label(root, text="Ortalama: -",
                                 font=("Arial", 12, "bold"),
                                 bg="white", fg="black")
        self.mean_lbl.pack(pady=4)

        self.std_lbl = tk.Label(root, text="Standart Sapma: -",
                                font=("Arial", 12, "bold"),
                                bg="white", fg="black")
        self.std_lbl.pack()

        self.status_lbl = tk.Label(root, text="Durum: Bekleniyor",
                                   font=("Arial", 12, "bold"),
                                   fg="black", bg="white")
        self.status_lbl.pack(pady=10)

    # ================= PORT YENİLE =================
    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [p.device for p in ports]
        if FORCED_PORT not in port_list:
            port_list.append(FORCED_PORT)

        self.port_combo["values"] = port_list
        if port_list:
            self.port_combo.set(port_list[0])

    # ================= BAŞLAT =================
    def start(self):
        port = self.port_combo.get()
        baud = int(self.baud_entry.get())

        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.csv_file = f"veri_kaydi_{now}.csv"

        with open(self.csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Tarih", "Saat", "CPU", "RAM"])

        self.ser = serial.Serial(port, baud)
        self.running = True
        self.cpu_values.clear()
        self.status_lbl.config(text="Durum: Veri Alınıyor", fg="green")

        threading.Thread(target=self.receive_loop, daemon=True).start()

    def stop(self):
        self.running = False
        if self.ser:
            self.ser.close()
        self.status_lbl.config(text="Durum: Durduruldu", fg="#5a2d00")

    def exit_app(self):
        self.running = False
        if self.ser:
            self.ser.close()
        self.root.destroy()

    # ================= VERİ OKUMA =================
    def receive_loop(self):
        x_data, y_data = [], []
        idx = 0

        while self.running:
            try:
                raw = self.ser.readline().decode().strip().split(",")
                date, time_s, cpu, ram = raw
                cpu = float(cpu)

                self.lbl_date.config(text=f"Tarih: {date}")
                self.lbl_time.config(text=f"Saat: {time_s}")
                self.lbl_cpu.config(text=f"CPU: {cpu}")
                self.lbl_ram.config(text=f"RAM: {ram}")

                with open(self.csv_file, "a", newline="") as f:
                    csv.writer(f).writerow(raw)

                x_data.append(idx)
                y_data.append(cpu)
                idx += 1

                self.line.set_data(x_data, y_data)
                self.ax.relim()
                self.ax.autoscale_view()
                self.canvas.draw()

                self.cpu_values.append(cpu)
                mean = np.mean(self.cpu_values)
                std = np.std(self.cpu_values)

                self.mean_lbl.config(text=f"Ortalama: {mean:.2f}")
                self.std_lbl.config(text=f"Standart Sapma: {std:.2f}")

            except:
                pass


if __name__ == "__main__":
    root = tk.Tk()
    app = SerialReceiverGUI(root)
    root.mainloop()