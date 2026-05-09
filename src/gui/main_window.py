from PyQt5.QtWidgets import QMainWindow, QSplitter, QMessageBox
from PyQt5.QtCore import Qt, QTimer

from src.core.road_network import RoadNetwork
from src.core.vehicle import Vehicle
from src.gui.simulation_view import SimulationView
from src.gui.control_panel import ControlPanel
from src.core.solver_thread import SolverThread

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Otonom Araç Optimizasyonu (Cooperative A*)")
        self.resize(1000, 600)

        # 1. Veri Modelini Oluştur
        self.road_network = RoadNetwork(length=240, step=10)
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
        self.control_panel.start_simulation_signal.connect(self.handle_start_simulation)

        # 5. Animasyon State
        self.solver_thread = None
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_step)
        self.current_time_step = 0
        self.animation_routes = {}

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
            for v in self.vehicles:
                self.simulation_view.add_vehicle(v)
        else:
            print(f"Uyarı: {position}. metrede zaten bir depo var.")

    def handle_start_simulation(self):
        if not self.vehicles:
            QMessageBox.warning(self, "Uyarı", "Başlamadan önce araç eklemelisiniz!")
            return
            
        print("Simülasyon başlıyor... Algoritma çalışıyor.")
        self.solver_thread = SolverThread(self.road_network, self.vehicles)
        self.solver_thread.optimization_finished.connect(self.handle_optimization_finished)
        self.solver_thread.start()

    def handle_optimization_finished(self, result):
        if result['status'] == 'success':
            print("Optimizasyon başarılı! Animasyon başlıyor...")
            self.animation_routes = result['routes']
            self.current_time_step = 0
            # Biraz yavaş görelim, örneğin saniyede 1.5 - 2 adım (500ms)
            self.animation_timer.start(500) 
        else:
            QMessageBox.critical(self, "Deadlock / Hata", result['message'])

    def animate_step(self):
        active_vehicles = False
        
        for vehicle in self.vehicles:
            if vehicle.vehicle_id in self.animation_routes:
                route = self.animation_routes[vehicle.vehicle_id]
                
                # O anki t değerindeki durumu bul
                current_state = None
                for state in route:
                    if state[1] == self.current_time_step:
                        current_state = state
                        break
                        
                if current_state:
                    node, t = current_state
                    loc, ntype = node
                    vehicle.position = loc
                    # Tipi de gönderiyoruz ki ceplerdeyken kenarda çizilsin
                    self.simulation_view.update_vehicle_position(vehicle, ntype)
                    active_vehicles = True
                elif self.current_time_step > route[-1][1]:
                    # Görev bitti
                    pass
                elif self.current_time_step < route[0][1]:
                    # Henüz başlangıç t'sine gelmedi (t_initial gecikmesi)
                    active_vehicles = True 
                
        if not active_vehicles:
            print(f"Animasyon tamamlandı. Toplam süre: t={self.current_time_step}")
            self.animation_timer.stop()
            
        self.current_time_step += 1
