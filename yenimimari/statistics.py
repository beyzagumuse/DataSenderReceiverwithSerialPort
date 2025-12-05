import numpy as np

class Statistics:
    def __init__(self):
        self.cpu_values = []

    def add(self, cpu):
        self.cpu_values.append(cpu)

    def mean(self):
        if not self.cpu_values:
            return 0
        return float(np.mean(self.cpu_values))

    def std(self):
        if not self.cpu_values:
            return 0
        return float(np.std(self.cpu_values))