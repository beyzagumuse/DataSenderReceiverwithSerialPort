import serial
import threading
import time
from data_logger import DataLogger
from statistics import Statistics

class SerialReceiverService:
    def __init__(self):
        self.ser = None
        self.running = False
        self.logger = DataLogger()
        self.stats = Statistics()
        self.threshold = 50
        self.callback = None
        self.thread = None

    def connect(self, port, baud):
        self.ser = serial.Serial(port, baud, timeout=1)

    def set_threshold(self, value):
        self.threshold = value

    def start(self, callback):
        if not self.ser or not self.ser.is_open:
            return

        self.running = True
        self.callback = callback

        self.thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        time.sleep(0.2)  # thread'in çıkmasını bekle

        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except:
                pass

    def _receive_loop(self):
        while self.running:
            try:
                if self.ser and self.ser.is_open:
                    line = self.ser.readline().decode(errors="ignore").strip()

                    if not line:
                        continue

                    parts = line.split(",")

                    if len(parts) == 4:
                        date_str, time_str, cpu, ram = parts
                        cpu = float(cpu)
                        ram = float(ram)

                        # CSV KAYDI
                        self.logger.log(date_str, time_str, cpu, ram)

                        # EŞİK KONTROLÜ
                        if cpu > self.threshold:
                            self.stats.add(cpu)

                        mean = self.stats.mean()
                        std = self.stats.std()

                        # GUI CALLBACK
                        if self.callback:
                            self.callback(date_str, time_str, cpu, ram, mean, std)

                else:
                    break

            except serial.SerialException:
                # Port kapatıldıysa sessizce çık
                break

            except Exception as e:
                print("Receiver Hata:", e)

        print("Receiver thread güvenli şekilde durdu.")