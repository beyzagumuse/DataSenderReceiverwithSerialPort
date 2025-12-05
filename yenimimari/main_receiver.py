import tkinter as tk
from gui_receiver import ReceiverGUI

if __name__ == "__main__":
    root = tk.Tk()
    app = ReceiverGUI(root)
    root.mainloop()