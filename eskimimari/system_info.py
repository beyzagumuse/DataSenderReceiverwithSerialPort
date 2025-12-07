import psutil
import datetime
import subprocess

def get_cpu_temp():
    try:
        output = subprocess.check_output(
            ["osx-cpu-temp"], stderr=subprocess.STDOUT
        )
        temp = output.decode().strip()
        return temp
    except:
        return "N/A"

while True:
    time_now = datetime.datetime.now().strftime("%H:%M:%S")
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent

    print(f"{time_now} | CPU: %{cpu} | RAM: %{ram} | TEMP: {get_cpu_temp()}")