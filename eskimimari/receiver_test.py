import serial
import csv
from datetime import datetime

PORT = "/dev/ttys006"
BAUDRATE = 9600

ser = serial.Serial(PORT, BAUDRATE)

file_name = "veri_kaydi.csv"

with open(file_name, "a", newline="") as file:
    writer = csv.writer(file)

    print("Alım + Kayıt başladı...")

    while True:
        data = ser.readline().decode().strip()
        print("Alındı:", data)

        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        parts = data.split(",")

        if len(parts) == 3:
            writer.writerow([time_now, parts[0], parts[1], parts[2]])