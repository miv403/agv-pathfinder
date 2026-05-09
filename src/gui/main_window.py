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
            
        # Görevleri bitince merkeze (0) geri dönmesini sağla
        if not v.tasks or v.tasks[-1] != 0:
            v.add_task(0)
            print(f"Araç {vehicle_id} için dönüş görevi eklendi: 0")
        
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
            
            # Rotayı daha hızlı sorgulayabilmek için sözlüğe (t -> node) dönüştür
            self.animation_routes = {}
            self.max_t = 0
            for vid, route in result['routes'].items():
                t_dict = {t: node for node, t in route}
                self.animation_routes[vid] = t_dict
                if route:
                    self.max_t = max(self.max_t, route[-1][1])
                    
            self.simulation_time = 0.0
            
            # FPS Ayarları: 30 FPS = ~33ms per frame
            self.timer_interval = 33 
            self.ms_per_logical_step = 500.0  # 1 tam adım (10m) 500ms sürsün
            
            self.animation_timer.start(self.timer_interval) 
        else:
            QMessageBox.critical(self, "Deadlock / Hata", result['message'])

    def animate_step(self):
        import math
        
        # Süreyi ilerlet
        self.simulation_time += (self.timer_interval / self.ms_per_logical_step)
        
        # O anki t floor değerindeki doluluk oranlarını hesapla (ui yazıları için)
        current_t_floor = math.floor(self.simulation_time)
        occupancy = {loc: 0 for loc in self.road_network.pockets + self.road_network.depots}
        
        active_vehicles = False
        
        for vehicle in self.vehicles:
            if vehicle.vehicle_id in self.animation_routes:
                route_dict = self.animation_routes[vehicle.vehicle_id]
                if not route_dict:
                    continue
                    
                min_t = min(route_dict.keys())
                max_t = max(route_dict.keys())
                
                if self.simulation_time < min_t:
                    # Henüz başlamadı
                    node = route_dict[min_t]
                    loc, ntype = node
                    self.simulation_view.update_vehicle_position_smooth(vehicle, loc, ntype)
                    active_vehicles = True
                elif self.simulation_time >= max_t:
                    # Görev bitti
                    node = route_dict[max_t]
                    loc, ntype = node
                    self.simulation_view.update_vehicle_position_smooth(vehicle, loc, ntype)
                    if ntype in ('pocket', 'depot'):
                        occupancy[loc] += 1
                else:
                    # Animasyon/Tweening interpolasyon adımı
                    active_vehicles = True
                    t1 = math.floor(self.simulation_time)
                    t2 = t1 + 1
                    fraction = self.simulation_time - t1
                    
                    if t1 in route_dict and t2 in route_dict:
                        loc1, type1 = route_dict[t1]
                        loc2, type2 = route_dict[t2]
                        
                        # 1D mesafe interpolasyonu
                        interpolated_loc = loc1 + (loc2 - loc1) * fraction
                        
                        # Doluluk tespiti: Yarıdan fazlaysa type2'de say, değilse type1'de
                        if fraction > 0.5:
                            if type2 in ('pocket', 'depot'):
                                occupancy[loc2] += 1
                        else:
                            if type1 in ('pocket', 'depot'):
                                occupancy[loc1] += 1
                                
                        # UI'ı pürüzsüz güncelle
                        self.simulation_view.update_vehicle_position_smooth(vehicle, interpolated_loc, type1, type2, fraction)
                    else:
                        # Fallback (normalde CA* ardışık t'ler üretir)
                        fallback_t = t1 if t1 in route_dict else max_t
                        loc, ntype = route_dict[fallback_t]
                        self.simulation_view.update_vehicle_position_smooth(vehicle, loc, ntype)
                        if ntype in ('pocket', 'depot'):
                            occupancy[loc] += 1
                            
        # UI üzerindeki occupancy (n/slots) yazılarını güncelle
        if hasattr(self.simulation_view, 'capacity_labels'):
            for loc, count in occupancy.items():
                if loc in self.simulation_view.capacity_labels:
                    cap = self.road_network.capacity['pocket'] if loc in self.road_network.pockets else self.road_network.capacity['depot']
                    self.simulation_view.capacity_labels[loc].setPlainText(f"{count}/{cap}")
                
        if self.simulation_time >= self.max_t:
            print(f"Animasyon tamamlandı. Toplam süre: t={math.floor(self.simulation_time)}")
            self.animation_timer.stop()
