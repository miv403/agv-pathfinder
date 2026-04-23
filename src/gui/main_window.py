from PyQt5.QtWidgets import QMainWindow, QSplitter
from PyQt5.QtCore import Qt

from src.core.road_network import RoadNetwork
from src.core.vehicle import Vehicle
from src.gui.simulation_view import SimulationView
from src.gui.control_panel import ControlPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Otonom Araç Optimizasyonu (CBS / A*)")
        self.resize(1000, 600)

        # 1. Veri Modelini Oluştur
        self.road_network = RoadNetwork(length=240)
        self.vehicles = []

        # 2. Arayüz Bileşenlerini Oluştur
        self.simulation_view = SimulationView(self.road_network)
        self.control_panel = ControlPanel(self.road_network)

        # 3. Layout (Splitter ile ikiye bölme)
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.simulation_view)
        splitter.addWidget(self.control_panel)
        splitter.setSizes([750, 250])

        self.setCentralWidget(splitter)

        # 4. Sinyalleri Bağla
        self.control_panel.add_task_signal.connect(self.handle_add_task)
        self.control_panel.add_depot_signal.connect(self.handle_add_depot)

    def handle_add_task(self, vehicle_id, selected_depots):
        print(f"Yeni Araç Eklendi: ID={vehicle_id}, Görevler={selected_depots}")
        # Aracı başlangıç noktasında oluştur
        v = Vehicle(vehicle_id=vehicle_id, start_pos=0)
        for d in selected_depots:
            v.add_task(d)
        
        self.vehicles.append(v)
        
        # Arayüze aracı çiz
        self.simulation_view.add_vehicle(v)

    def handle_add_depot(self, position):
        if position not in self.road_network.depots:
            print(f"Yeni Depo Eklendi: Mesafe={position}")
            self.road_network.add_depot(position)
            # Arayüzü güncelle
            self.simulation_view.update_road()
            # Çizilen araçları tekrar eklemek gerekebilir çünkü draw_environment ekranı temizliyor.
            # Şimdilik araçların da yeniden çizildiğini varsayalım ya da yeniden çizecek bir fonksiyon yazılabilir.
            for v in self.vehicles:
                self.simulation_view.add_vehicle(v)
            
            # TODO: Kontrol panelindeki checkbox'ları güncelle
        else:
            print(f"Uyarı: {position}. metrede zaten bir depo var.")
