import serial
import psutil
import datetime
import time

PORT = "/dev/ttys005"
BAUDRATE = 9600

ser = serial.Serial(PORT, BAUDRATE)
time.sleep(2)

print("Gönderim başladı...")

while True:
    time_now = datetime.datetime.now().strftime("%H:%M:%S")
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent

    data = f"{time_now},{cpu},{ram}\n"
    ser.write(data.encode())

    print("Gönderildi:", data)
    time.sleep(1)