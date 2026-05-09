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
        
        # Olası bir bekleme veya uzun süreçte QThread donmaması için buradayız
        result = solver.solve(self.vehicles)
        
        self.optimization_finished.emit(result)
