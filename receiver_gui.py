import serial
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import csv
from datetime import datetime

class ReceiverGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Seri Port Veri Alıcı")
        self.root.geometry("600x400")

        self.serial_port = None
        self.is_receiving = False

        # PORT SEÇİMİ
        tk.Label(root, text="Seri Port:").pack(pady=5)
        self.port_combo = ttk.Combobox(root, values=["/dev/ttys006"])
        self.port_combo.pack()

        # BAUDRATE
        tk.Label(root, text="Baudrate:").pack()
        self.baud_entry = tk.Entry(root)
        self.baud_entry.insert(0, "9600")
        self.baud_entry.pack()

        # BUTONLAR
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        self.start_btn = tk.Button(btn_frame, text="Alımı Başlat", width=15, command=self.start_receiving)
        self.start_btn.grid(row=0, column=0, padx=5)

        self.stop_btn = tk.Button(btn_frame, text="Alımı Durdur", width=15, command=self.stop_receiving)
        self.stop_btn.grid(row=0, column=1, padx=5)

        # TABLO
        self.tree = ttk.Treeview(root, columns=("time", "cpu", "ram"), show="headings")
        self.tree.heading("time", text="Saat")
        self.tree.heading("cpu", text="CPU (%)")
        self.tree.heading("ram", text="RAM (%)")
        self.tree.pack(expand=True, fill="both", pady=10)

        # DURUM
        self.status_label = tk.Label(root, text="Durum: Bekleniyor", fg="blue")
        self.status_label.pack()

        # CSV DOSYASI
        self.file = open("veri_kaydi.csv", "a", newline="")
        self.writer = csv.writer(self.file)

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
                        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cpu = parts[1]
                        ram = parts[2]

                        # TABLOYA EKLE
                        self.tree.insert("", "end", values=(time_now, cpu, ram))
                        self.tree.yview_moveto(1)

                        # CSV'YE KAYDET
                        self.writer.writerow([time_now, cpu, ram])
                        self.file.flush()

            except:
                pass


root = tk.Tk()
app = ReceiverGUI(root)
root.mainloop()