from PyQt5.QtCore import QThread, pyqtSignal
from src.core.cooperative_astar import CooperativeAStar
import time

class SolverThread(QThread):
    """
    Arayüzü dondurmamak için Cooperative A* (CA*) algoritmasını arka planda çalıştıracak QThread sınıfı.
    """
    # Algoritma bittiğinde sonuçları (rotalar sözlüğü) veya hata mesajını arayüze iletmek için sinyal
    optimization_finished = pyqtSignal(object) 
    
    def __init__(self, road_network, vehicles):
        super().__init__()
        self.road_network = road_network
        self.vehicles = vehicles

    def run(self):
        """
        Algoritmanın ana çalışma döngüsü.
        """
        solver = CooperativeAStar(self.road_network)
        
        t_start = time.perf_counter()
        result = solver.solve(self.vehicles)
        t_end = time.perf_counter()
        
        elapsed_ms = (t_end - t_start) * 1000
        print(f"[CA*] Hesaplama süresi: {elapsed_ms:.2f} ms ({len(self.vehicles)} araç)")
        
        self.optimization_finished.emit(result)
