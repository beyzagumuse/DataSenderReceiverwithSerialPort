import tkinter as tk
from sender_gui import SerialSenderGUI

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialSenderGUI(root)
    root.mainloop()