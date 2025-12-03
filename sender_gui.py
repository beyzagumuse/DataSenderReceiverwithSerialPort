import serial
import psutil
import datetime
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox

class SenderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Seri Port Veri Gönderici")
        self.root.geometry("400x300")

        self.serial_port = None
        self.is_sending = False

        # PORT SEÇİMİ
        tk.Label(root, text="Seri Port Seç:").pack(pady=5)
        self.port_combo = ttk.Combobox(root, values=["/dev/ttys005"])
        self.port_combo.pack()

        # BAUDRATE
        tk.Label(root, text="Baudrate:").pack()
        self.baud_entry = tk.Entry(root)
        self.baud_entry.insert(0, "9600")
        self.baud_entry.pack()

        # BUTONLAR
        self.start_btn = tk.Button(root, text="Gönderimi Başlat", command=self.start_sending)
        self.start_btn.pack(pady=10)

        self.stop_btn = tk.Button(root, text="Gönderimi Durdur", command=self.stop_sending)
        self.stop_btn.pack()

        # DURUM
        self.status_label = tk.Label(root, text="Durum: Bekleniyor", fg="blue")
        self.status_label.pack(pady=20)

    def start_sending(self):
        port = self.port_combo.get()
        baud = int(self.baud_entry.get())

        try:
            self.serial_port = serial.Serial(port, baud)
            self.is_sending = True
            self.status_label.config(text="Durum: Gönderiliyor", fg="green")

            thread = threading.Thread(target=self.send_data)
            thread.daemon = True
            thread.start()

        except:
            messagebox.showerror("HATA", "Seri port açılamadı!")

    def stop_sending(self):
        self.is_sending = False
        self.status_label.config(text="Durum: Durduruldu", fg="red")

        if self.serial_port:
            self.serial_port.close()

    def send_data(self):
        while self.is_sending:
            time_now = datetime.datetime.now().strftime("%H:%M:%S")
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent

            data = f"{time_now},{cpu},{ram}\n"
            self.serial_port.write(data.encode())

            print("Gönderildi:", data)
            time.sleep(1)


root = tk.Tk()
app = SenderGUI(root)
root.mainloop()