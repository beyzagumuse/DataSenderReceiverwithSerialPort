import serial
import psutil
import datetime
import time
import subprocess
import re


class SerialSenderLogic:
    def __init__(self):
        self.ser = None
        self.running = False
        self.paused = False

    def connect(self, port, baud):
        self.ser = serial.Serial(port, baud)

    def disconnect(self):
        if self.ser:
            self.ser.close()

    def start(self):
        self.running = True
        self.paused = False

    def stop(self):
        self.running = False
        self.paused = False
        self.disconnect()

    def toggle_pause(self):
        self.paused = not self.paused
        return self.paused

    # SICAKLIK 
    def get_temperature(self):
        try:
            path = "/opt/homebrew/bin/osx-cpu-temp"
            output = subprocess.check_output([path]).decode("utf-8")
            temp = output.replace("°C", "").strip()
            return float(temp)
        except Exception as e:
            print("SICAKLIK OKUNAMADI:", e)
            return 55555.0

    def get_system_data(self):
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        temp = self.get_temperature()

        data = f"{date_str},{time_str},{cpu},{ram},{temp}\n"
        return date_str, time_str, cpu, ram, temp, data

    def send_loop(self, callback):
        while self.running:
            if not self.paused:
                date_str, time_str, cpu, ram, temp, data = self.get_system_data()
                self.ser.write(data.encode())
                callback(date_str, time_str, cpu, ram, temp)
            time.sleep(1)