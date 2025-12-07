# Seri Port Tabanlı Canlı Sistem İzleme ve Analiz Uygulaması

Bu projede, bilgisayardan alınan **zaman bilgisi, CPU kullanımı, RAM kullanımı ve sıcaklık verileri** seri port üzerinden başka bir uygulamaya gönderilmekte; alınan veriler **canlı grafiklerle izlenmekte, eşik değerlerine göre alarm üretilmekte ve tüm veriler dosyalara kaydedilmektedir.**

---

## Projenin Amacı

Seri iletişim kullanarak:
- Bilgisayar performans verilerinin **anlık olarak gönderilmesi**
- Başka bir uygulama tarafından **canlı izlenmesi**
- **Eşik değerlerine göre alarm üretilmesi**
- **Tüm verilerin dosyalara kaydedilmesi**
amaçlanmaktadır.

Bu çalışma; **seri haberleşme, gerçek zamanlı izleme ve veri analizi** konularını bir arada içeren uçtan uca bir uygulamadır.

---

## Sistem Mimarisi

- **Sender (Gönderici GUI):**
  - CPU, RAM, sıcaklık ve zaman bilgilerini toplar
  - Seçilen seri port üzerinden gönderir

- **Receiver (Alıcı GUI):**
  - Verileri seri porttan alır
  - Canlı grafikler çizer
  - Eşik kontrolü yapar
  - Alarm üretir
  - Tüm verileri CSV dosyalarına kaydeder

İki uygulama arasında iletişim **sanal seri port çifti** ile sağlanmaktadır.

---

## 🛠 Kullanılan Teknolojiler

- **Programlama Dili:** Python 3
- **Arayüz:** Tkinter
- **Seri Haberleşme:** pySerial
- **Grafik:** Matplotlib
- **İstatistik:** NumPy
- **Dosya Kayıt:** CSV
- **Sanal Seri Port:** socat / com0com

---

## 📁 Proje Klasör Yapısı

```text
yenimimari2/
│
├── sender/
│   ├── sender_gui.py
│   └── sender_logic.py
│
├── receiver/
│   ├── receiver_gui.py
│   ├── receiver_logic.py
│── data/
│   ├── veri_kaydi/
│   ├── cpu_alarm/
│   ├── ram_alarm/
│   └── cpu_details/
│
└── README.md
```

##  Kurulum

Bu adımlar macOS üzerinde test edilmiştir. Windows için de benzer şekilde uygulanabilir.

---

### 1 Python Kurulumu

Python 3 yüklü değilse aşağıdaki adresten indir:

```bash
https://www.python.org
```

Kurulumu doğrulamak için:

```bash
python3 --version
```

### 2 Projeyi Bilgisayara Klonla


```bash
git clone <GITHUB_REPO_LINKİN>
cd yenimimari2
```

### 3 Gerekli Python Kütüphanelerini Kur

```bash
pip install pyserial matplotlib numpy psutil
```

### 4 Sanal Seri Port Oluşturma (macOS)

Seri port iletişimini test etmek için socat kullanılır:

```bash
brew install socat
```

Port çifti oluştur:

```bash
socat -d -d pty,raw,echo=0 pty,raw,echo=0
```

Terminal çıktısında şu şekilde iki port görünür:

```bash
/dev/ttys00X   <-->   /dev/ttys00Y
```

Bu portları Sender ve Receiver uygulamalarında kullanacağız.

### 5 Receiver Uygulamasını Çalıştır

Öncelikle **alıcı (receiver) uygulaması** başlatılmalıdır:

```bash
cd receiver
python main_receiver.py
```

Açılan arayüzde aşağıdaki ayarları yap:
	•	Seri Port: socat ile oluşturulan portlardan biri (ör: /dev/ttys00Y)
	•	Baudrate: 9600
	•	CPU Eşik Değeri: İstediğin alarm seviyesi
	•	RAM Eşik Değeri: İstediğin alarm seviyesi

Ayarları yaptıktan sonra:
	•	“Alımı Başlat” butonuna bas
	•	Sistem veri almaya ve canlı grafikleri çizmeye başlayacaktır

### 6 Sender Uygulamasını Çalıştır

Yeni bir terminal aç:

```bash
cd sender
python main.py
```

Açılan arayüzde:
	•	Seri Port: /dev/ttys00X
	•	Baudrate: 9600
	•	“Gönderimi Başlat” butonuna bas


