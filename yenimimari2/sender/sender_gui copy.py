import tkinter as tk
from tkinter import ttk
import threading
import serial.tools.list_ports
from sender_logic import SerialSenderLogic


class SerialSenderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Seri Port Veri Gönderici")
        self.root.geometry("900x600")
        self.root.configure(bg="#f5f5f5")
        self.root.resizable(False, False)

        self.logic = SerialSenderLogic()

        # ===== STYLE =====
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
        tk.Label(root, text="Seri Port Veri Gönderici",
                 font=("Arial", 20, "bold"),
                 bg="#f5f5f5", fg="black").pack(pady=20)

        # ===== PORT SEÇİM =====
        frame = tk.Frame(root, bg="white", highlightbackground="black", highlightthickness=1)
        frame.place(x=200, y=100, width=500, height=170)

        tk.Label(frame, text="Seri Port:",
                 bg="white", fg="black",
                 font=("Arial", 11)).place(x=30, y=30)

        self.port_combo = ttk.Combobox(frame, width=25)
        self.port_combo.place(x=200, y=30)
        self.refresh_ports()

        tk.Label(frame, text="Baudrate:",
                 bg="white", fg="black",
                 font=("Arial", 11)).place(x=30, y=80)

        self.baud_entry = tk.Entry(frame, width=28)
        self.baud_entry.insert(0, "9600")
        self.baud_entry.place(x=200, y=80)

        ttk.Button(frame, text="Portları Yenile",
                   command=self.refresh_ports).place(x=200, y=120, width=200)

        # ===== BUTONLAR =====
        self.start_btn = ttk.Button(root, text="Gönderimi Başlat",
                                    style="Green.TButton",
                                    command=self.start_sending)
        self.start_btn.place(x=220, y=300, width=200)

        self.pause_btn = ttk.Button(root, text="Gönderimi Duraklat",
                                    style="Brown.TButton",
                                    command=self.pause_sending)
        self.pause_btn.place(x=480, y=300, width=200)

        self.stop_btn = ttk.Button(root, text="Gönderimi Bitir",
                                   style="Black.TButton",
                                   command=self.stop_sending)
        self.stop_btn.place(x=350, y=360, width=200)

        # ===== GÖNDERİLEN VERİ =====
        data_frame = tk.Frame(root, bg="white", highlightbackground="black", highlightthickness=1)
        data_frame.place(x=320, y=430, width=260, height=130)

        tk.Label(data_frame, text="Gönderilen Veri",
                 font=("Arial", 11, "bold"),
                 bg="white", fg="black").pack(pady=5)

        self.date_lbl = tk.Label(data_frame, text="Tarih: -", bg="white", fg="black")
        self.date_lbl.pack(anchor="w", padx=10)

        self.time_lbl = tk.Label(data_frame, text="Saat: -", bg="white", fg="black")
        self.time_lbl.pack(anchor="w", padx=10)

        self.cpu_lbl = tk.Label(data_frame, text="CPU: -", bg="white", fg="black")
        self.cpu_lbl.pack(anchor="w", padx=10)

        self.ram_lbl = tk.Label(data_frame, text="RAM: -", bg="white", fg="black")
        self.ram_lbl.pack(anchor="w", padx=10)

        # ===== DURUM =====
        self.status_lbl = tk.Label(root, text="Durum: Bekleniyor",
                                   font=("Arial", 11, "bold"),
                                   fg="black",
                                   bg="#f5f5f5")
        self.status_lbl.pack(side="bottom", pady=10)

    # ===== PORTLAR =====
    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        self.port_combo["values"] = port_list
        if port_list:
            self.port_combo.set(port_list[0])

    # ===== BAŞLAT =====
    def start_sending(self):
        port = self.port_combo.get().strip()
        baud = int(self.baud_entry.get())

        if not port:
            self.status_lbl.config(text="Durum: Port Girilmedi", fg="red")
            return

        try:
            self.logic.connect(port, baud)
        except:
            self.status_lbl.config(text="Port Açma Hatası", fg="red")
            return

        self.logic.start()
        self.status_lbl.config(text="Durum: Gönderiliyor", fg="green")

        threading.Thread(
            target=self.logic.send_loop,
            args=(self.update_labels,),
            daemon=True
        ).start()

    # ===== DURAKLAT =====
    def pause_sending(self):
        paused = self.logic.toggle_pause()
        if paused:
            self.status_lbl.config(text="Durum: Duraklatıldı", fg="orange")
        else:
            self.status_lbl.config(text="Durum: Gönderiliyor", fg="green")

    # ===== DURDUR =====
    def stop_sending(self):
        self.logic.stop()
        self.status_lbl.config(text="Durum: Durduruldu", fg="red")

    # ===== UI GÜNCELLE =====
    def update_labels(self, date_str, time_str, cpu, ram):
        self.date_lbl.config(text=f"Tarih: {date_str}")
        self.time_lbl.config(text=f"Saat: {time_str}")
        self.cpu_lbl.config(text=f"CPU: {cpu}")
        self.ram_lbl.config(text=f"RAM: {ram}")