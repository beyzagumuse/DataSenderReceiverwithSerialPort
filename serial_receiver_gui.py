import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import threading
import csv
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class ReceiverApp:
    def __init__(self, root):
        self.root = root
        root.title("Seri Port Veri Alıcı & Analiz")
        root.geometry("1100x700")
        root.configure(bg="#f5f5f5")

        self.running = False
        self.data_cpu = []

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
                 bg="#f5f5f5", fg="black").pack(pady=20)

        # ===== AYAR ALANI =====
        frame = tk.Frame(root, bg="white", highlightbackground="black", highlightthickness=1)
        frame.place(x=250, y=90, width=600, height=130)

        tk.Label(frame, text="Seri Port:", bg="white").place(x=30, y=25)
        self.port_combo = ttk.Combobox(frame, width=25)
        self.port_combo.place(x=150, y=25)
        self.refresh_ports()

        tk.Label(frame, text="Baudrate:", bg="white").place(x=30, y=65)
        self.baud_entry = tk.Entry(frame, width=28)
        self.baud_entry.insert(0, "9600")
        self.baud_entry.place(x=150, y=65)

        tk.Label(frame, text="CPU Eşik (%):", bg="white").place(x=360, y=25)
        self.cpu_threshold = tk.Entry(frame, width=10)
        self.cpu_threshold.insert(0, "50")
        self.cpu_threshold.place(x=470, y=25)

        # ===== BUTONLAR =====
        self.start_btn = ttk.Button(root, text="Alımı Başlat",
                                    style="Green.TButton", command=self.start)
        self.start_btn.place(x=350, y=250, width=180)

        self.stop_btn = ttk.Button(root, text="Alımı Durdur",
                                   style="Brown.TButton", command=self.stop)
        self.stop_btn.place(x=570, y=250, width=180)

        self.exit_btn = ttk.Button(root, text="Alımı Bitir",
                                   style="Black.TButton", command=self.exit_app)
        self.exit_btn.place(x=460, y=310, width=180)

        # ===== ALINAN VERİ KUTUSU =====
        box = tk.Frame(root, bg="white", highlightbackground="black", highlightthickness=1)
        box.place(x=50, y=380, width=300, height=180)

        tk.Label(box, text="Alınan Veri", bg="white", font=("Arial", 11, "bold")).pack(pady=5)
        self.lbl_date = tk.Label(box, text="Tarih:", bg="white")
        self.lbl_date.pack(anchor="w", padx=10)
        self.lbl_time = tk.Label(box, text="Saat:", bg="white")
        self.lbl_time.pack(anchor="w", padx=10)
        self.lbl_cpu = tk.Label(box, text="CPU:", bg="white")
        self.lbl_cpu.pack(anchor="w", padx=10)
        self.lbl_ram = tk.Label(box, text="RAM:", bg="white")
        self.lbl_ram.pack(anchor="w", padx=10)

        # ===== GRAFİK =====
        graph_frame = tk.Frame(root, bg="white", highlightbackground="black", highlightthickness=1)
        graph_frame.place(x=380, y=370, width=670, height=300)

        self.fig, self.ax = plt.subplots()
        self.ax.set_title("CPU Kullanımı (%)")
        self.ax.set_xlabel("Zaman")
        self.ax.set_ylabel("CPU %")
        self.line, = self.ax.plot([], [])

        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # ===== İSTATİSTİK =====
        self.avg_label = tk.Label(root, text="Ortalama: -", bg="#f5f5f5")
        self.avg_label.place(x=650, y=680)

        self.std_label = tk.Label(root, text="Standart Sapma: -", bg="#f5f5f5")
        self.std_label.place(x=650, y=705)

        self.status_label = tk.Label(root, text="Durum: Bekleniyor", bg="#f5f5f5")
        self.status_label.place(x=50, y=680)

    # ===== PORTLARI YENİLE =====
    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [p.device for p in ports]

        forced = "/dev/ttys006"
        if forced not in port_list:
            port_list.append(forced)

        self.port_combo["values"] = port_list
        self.port_combo.set(forced)

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

                self.lbl_date.config(text=f"Tarih: {tarih}")
                self.lbl_time.config(text=f"Saat: {saat}")
                self.lbl_cpu.config(text=f"CPU: {cpu}")
                self.lbl_ram.config(text=f"RAM: {ram}")

                with open(self.csv_file, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([tarih, saat, cpu, ram])

                self.data_cpu.append(cpu)
                self.line.set_data(range(len(self.data_cpu)), self.data_cpu)
                self.ax.relim()
                self.ax.autoscale_view()
                self.canvas.draw()

                threshold = float(self.cpu_threshold.get())
                over = [x for x in self.data_cpu if x > threshold]

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