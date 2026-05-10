from PyQt5.QtWidgets import QMainWindow, QSplitter, QMessageBox, QTableWidget, QTableWidgetItem, QLabel, QAction, QFileDialog, QMenu, QDialog, QCheckBox, QScrollArea, QVBoxLayout, QDialogButtonBox, QWidget, QDoubleSpinBox
import json
from PyQt5.QtCore import Qt, QTimer

from src.core.road_network import RoadNetwork
from src.core.vehicle import Vehicle
from src.gui.simulation_view import SimulationView
from src.gui.control_panel import ControlPanel
from src.core.solver_thread import SolverThread

class EditNodesDialog(QDialog):
    def __init__(self, title, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(300, 400)
        
        layout = QVBoxLayout(self)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        
        self.item_checkboxes = []
        for item in sorted(items):
            cb = QCheckBox(f"Konum: {item}")
            cb.setChecked(True)
            self.item_checkboxes.append((item, cb))
            self.content_layout.addWidget(cb)
            
        self.content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_selected_positions(self):
        return [pos for pos, cb in self.item_checkboxes if cb.isChecked()]

class SpeedDialog(QDialog):
    def __init__(self, current_speed, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Simülasyon Hızı")
        self.setFixedSize(250, 150)
        
        layout = QVBoxLayout(self)
        
        info_label = QLabel(f"Mevcut Hız: <b>{current_speed}x</b>")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.1, 20.0)
        self.speed_spin.setSingleStep(0.5)
        self.speed_spin.setValue(current_speed)
        self.speed_spin.setSuffix("x")
        self.speed_spin.setDecimals(1)
        
        layout.addWidget(QLabel("Hızı Ayarla:"))
        layout.addWidget(self.speed_spin)
        
        layout.addStretch()
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_speed(self):
        return self.speed_spin.value()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Otonom Araç Optimizasyonu (Cooperative A*)")
        # self.resize(1000, 600)
        self.resize(1100, 700)
        
        self.init_menu_bar()

        # 1. Veri Modelini Oluştur
        self.road_network = RoadNetwork(length=240, step=10)
        self.vehicles = []

        # 2. Arayüz Bileşenlerini Oluştur
        self.simulation_view = SimulationView(self.road_network)
        self.control_panel = ControlPanel(self.road_network)

        # 3. Layout (Splitter ile ikiye bölme)
        top_splitter = QSplitter(Qt.Horizontal)
        top_splitter.addWidget(self.simulation_view)
        top_splitter.addWidget(self.control_panel)
        top_splitter.setSizes([700, 320])
        
        # Bilgi Paneli (Alt Kısım)
        self.info_table = QTableWidget()
        self.info_table.setColumnCount(4)
        self.info_table.setHorizontalHeaderLabels(["Araç ID", "Renk", "Konum", "Görev Durumu"])
        self.info_table.horizontalHeader().setStretchLastSection(True)
        self.info_table.setEditTriggers(QTableWidget.NoEditTriggers)

        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(self.info_table)
        main_splitter.setSizes([450, 150])

        self.setCentralWidget(main_splitter)

        # 4. Sinyalleri Bağla
        self.control_panel.add_task_signal.connect(self.handle_add_task)
        self.control_panel.add_depot_signal.connect(self.handle_add_depot)
        self.control_panel.add_pocket_signal.connect(self.handle_add_pocket)
        self.control_panel.start_simulation_signal.connect(self.handle_start_simulation)
        self.control_panel.stop_simulation_signal.connect(self.handle_stop_simulation)

        # 5. Animasyon State
        self.solver_thread = None
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_step)
        self.current_time_step = 0
        self.animation_routes = {}
        self.animation_speed_factor = 1.0
        self.timer_interval = 33
        self.ms_per_logical_step = 500.0

    def init_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Dosya")

        save_action = QAction("Senaryoyu Kaydet", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_scenario)
        file_menu.addAction(save_action)

        load_action = QAction("Senaryoyu Yükle", self)
        load_action.setShortcut("Ctrl+L")
        load_action.triggered.connect(self.load_scenario)
        file_menu.addAction(load_action)

        file_menu.addSeparator()
        
        exit_action = QAction("Çıkış", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 2. Düzenle Menüsü
        self.edit_menu = menubar.addMenu("Düzenle")
        
        undo_action = QAction("Geri Al", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo_last_vehicle)
        self.edit_menu.addAction(undo_action)
        
        self.edit_menu.addSeparator()

        edit_depots_action = QAction("Depoları Düzenle", self)
        edit_depots_action.triggered.connect(self.edit_depots)
        self.edit_menu.addAction(edit_depots_action)
        
        edit_pockets_action = QAction("Cepleri Düzenle", self)
        edit_pockets_action.triggered.connect(self.edit_pockets)
        self.edit_menu.addAction(edit_pockets_action)

        self.edit_menu.addSeparator()

        reset_tasks_action = QAction("Görevleri ve Araçları Sıfırla", self)
        reset_tasks_action.triggered.connect(self.reset_tasks_and_vehicles)
        self.edit_menu.addAction(reset_tasks_action)

        reset_all_action = QAction("Tümünü Sıfırla", self)
        reset_all_action.triggered.connect(self.reset_all)
        self.edit_menu.addAction(reset_all_action)
        
        # 3. Simülasyon Menüsü
        self.sim_menu = menubar.addMenu("Simülasyon")
        
        speed_action = QAction("Hız Ayarları", self)
        speed_action.triggered.connect(self.change_speed)
        self.sim_menu.addAction(speed_action)

    def save_scenario(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Senaryoyu Kaydet", "./scenario.json", "JSON Dosyası (*.json)")
        if not filename:
            return

        scenario_data = {
            "depots": self.road_network.depots,
            "pockets": self.road_network.pockets,
            "vehicles": []
        }

        for v in self.vehicles:
            vehicle_data = {
                "id": v.vehicle_id,
                "start_pos": v.start_pos,
                "direction": "İleri" if v.direction == 1 else "Geri",
                "tasks": getattr(v, "_real_tasks", []),
                "is_vip": getattr(v, "is_vip", False)
            }
            scenario_data["vehicles"].append(vehicle_data)

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(scenario_data, f, indent=4, ensure_ascii=False)
            QMessageBox.information(self, "Başarılı", "Senaryo başarıyla kaydedildi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Senaryo kaydedilirken hata oluştu: {str(e)}")

    def load_scenario(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Senaryoyu Yükle", "", "JSON Dosyası (*.json)")
        if not filename:
            return

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Mevcut durumu temizle
            self.reset_all()

            # Depoları yükle
            for depot_pos in data.get("depots", []):
                self.handle_add_depot(depot_pos)

            # Cepleri yükle
            for pocket_pos in data.get("pockets", []):
                self.handle_add_pocket(pocket_pos)

            # Araçları yükle
            for v_data in data.get("vehicles", []):
                self.handle_add_task(
                    v_data["id"],
                    v_data["start_pos"],
                    v_data["direction"],
                    v_data["tasks"],
                    v_data.get("is_vip", False)
                )
            
            # Araç sayacını güncelle ki çakışmasın
            if self.vehicles:
                max_id = max(v.vehicle_id for v in self.vehicles)
                self.control_panel.vehicle_count = max_id

            QMessageBox.information(self, "Başarılı", "Senaryo başarıyla yüklendi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Senaryo yüklenirken hata oluştu: {str(e)}")

    def reset_tasks_and_vehicles(self):
        """Sadece araçları ve görevleri temizler, depoları ve cepleri korur."""
        self.animation_timer.stop()
        if hasattr(self, 'edit_menu'):
            self.edit_menu.setEnabled(True)
        self.vehicles = []
        self.simulation_view.clear_vehicles()
        self.info_table.setRowCount(0)
        self.animation_routes = {}
        self.current_time_step = 0
        self.control_panel.vehicle_count = 0
        self.control_panel.set_simulation_state(False)
        self.simulation_view.update_sensors([])

    def reset_all(self):
        """Depolar, cepler, araçlar dahil her şeyi sıfırla."""
        self.reset_tasks_and_vehicles()
        self.road_network.depots = []
        self.road_network.pockets = []
        self.simulation_view.update_road()
        self.control_panel.refresh_depot_list()

    def undo_last_vehicle(self):
        """Son eklenen aracı listeden ve ekrandan kaldırır."""
        if not self.vehicles:
            return
            
        last_vehicle = self.vehicles.pop()
        self.simulation_view.remove_vehicle(last_vehicle.vehicle_id)
        
        # Tablodan kaldır
        for row in range(self.info_table.rowCount()):
            item = self.info_table.item(row, 0)
            if item and item.text().startswith(str(last_vehicle.vehicle_id)):
                self.info_table.removeRow(row)
                break
        
        self.control_panel.vehicle_count = max(0, self.control_panel.vehicle_count - 1)
        self.simulation_view.update_sensors(self.vehicles)

    def change_speed(self):
        """Simülasyon hızını değiştirmek için bir diyalog açar."""
        dialog = SpeedDialog(self.animation_speed_factor, self)
        if dialog.exec_() == QDialog.Accepted:
            self.animation_speed_factor = dialog.get_speed()
            print(f"Simülasyon hızı güncellendi: {self.animation_speed_factor}x")

    def handle_add_task(self, vehicle_id, start_loc, direction_str, selected_depots, is_vip=False):
        # Shortest Job First (SJF) - Görevleri toplam maliyete göre sırala
        # Sadece VIP olmayan araçlar için (VIP zaten tek görevli)
        if not is_vip:
            selected_depots.sort(key=lambda t: abs(t - start_loc) + t)

        print(f"Yeni Araç Eklendi: ID={vehicle_id}, Konum={start_loc}, Yön={direction_str}, Görevler={selected_depots}, VIP={is_vip}")
        
        # Yön değerini sayısal karşılığa çevir
        direction = 1 if direction_str == "İleri" else -1
        
        # Aracı kullanıcının girdiği konumda oluştur
        v = Vehicle(vehicle_id=vehicle_id, start_pos=start_loc, direction=direction, is_vip=is_vip)
        v._real_tasks = list(selected_depots) # gerçek görevleri tablo için sakla
        for d in selected_depots:
            v.add_task(d)
            v.add_task(0)
            
        print(f"Araç {vehicle_id} nihai görev listesi: {v.tasks}")
        
        self.vehicles.append(v)
        
        # Arayüze aracı çiz
        self.simulation_view.add_vehicle(v)
        
        # Tabloya ekle
        row = self.info_table.rowCount()
        self.info_table.insertRow(row)
        
        display_id = str(vehicle_id)
        if is_vip:
            display_id += " (VIP)"
        self.info_table.setItem(row, 0, QTableWidgetItem(display_id))
        
        color_item = QTableWidgetItem()
        color_item.setBackground(v.color)
        self.info_table.setItem(row, 1, color_item)
        
        self.info_table.setItem(row, 2, QTableWidgetItem(str(start_loc)))
        
        status_html = ""
        for real_task in v._real_tasks:
            status_html += f'<span style="color:red; margin-right:10px; font-weight:bold;">[{real_task}]</span> '

        status_label = QLabel()
        status_label.setText(status_html)
        self.info_table.setCellWidget(row, 3, status_label)
        v._table_row = row
        
        # Sensör renklerini güncelle
        self.simulation_view.update_sensors(self.vehicles)

    def handle_add_depot(self, position):
        if position not in self.road_network.depots:
            print(f"Yeni Depo Eklendi: Mesafe={position}")
            self.road_network.add_depot(position)
            # Arayüzü güncelle
            self.simulation_view.update_road()
            for v in self.vehicles:
                self.simulation_view.add_vehicle(v)
            # Görev ekleme listesini tazele
            self.control_panel.refresh_depot_list()
        else:
            print(f"Uyarı: {position}. metrede zaten bir depo var.")

    def handle_add_pocket(self, position):
        if position not in self.road_network.pockets:
            print(f"Yeni Cep Eklendi: Mesafe={position}")
            self.road_network.add_pocket(position)
            # Arayüzü güncelle
            self.simulation_view.update_road()
            for v in self.vehicles:
                self.simulation_view.add_vehicle(v)
        else:
            print(f"Uyarı: {position}. metrede zaten bir cep var.")

    def edit_depots(self):
        dialog = EditNodesDialog("Depoları Düzenle", self.road_network.depots, self)
        if dialog.exec_() == QDialog.Accepted:
            selected = dialog.get_selected_positions()
            # Seçilmeyenleri bul (silinecekler)
            to_remove = [d for d in self.road_network.depots if d not in selected]
            
            if not to_remove:
                return

            # Araçlara atanmış mı kontrol et
            active_tasks = []
            for v in self.vehicles:
                active_tasks.extend(getattr(v, "_real_tasks", []))
            
            actually_removed = []
            for d in to_remove:
                if d in active_tasks:
                    QMessageBox.warning(self, "Uyarı", f"{d}. konumundaki depo bir araca atanmış olduğu için silinemedi.")
                else:
                    self.road_network.depots.remove(d)
                    actually_removed.append(d)
            
            if actually_removed:
                self.simulation_view.update_road()
                for v in self.vehicles:
                    self.simulation_view.add_vehicle(v)
                self.control_panel.refresh_depot_list()

    def edit_pockets(self):
        dialog = EditNodesDialog("Cepleri Düzenle", self.road_network.pockets, self)
        if dialog.exec_() == QDialog.Accepted:
            selected = dialog.get_selected_positions()
            to_remove = [p for p in self.road_network.pockets if p not in selected]
            
            if not to_remove:
                return

            for p in to_remove:
                self.road_network.pockets.remove(p)
            
            self.simulation_view.update_road()
            for v in self.vehicles:
                self.simulation_view.add_vehicle(v)

    def handle_start_simulation(self):
        if not self.vehicles:
            QMessageBox.warning(self, "Uyarı", "Başlamadan önce araç eklemelisiniz!")
            return
            
        print("Simülasyon başlıyor... Algoritma çalışıyor.")
        self.edit_menu.setEnabled(False)
        self.control_panel.set_simulation_state(True) # Butonu durdur moduna al
        self.solver_thread = SolverThread(self.road_network, self.vehicles)
        self.solver_thread.optimization_finished.connect(self.handle_optimization_finished)
        self.solver_thread.start()

    def handle_stop_simulation(self):
        """Simülasyonu durdurur ve araçları başlangıç durumuna döndürür."""
        print("Simülasyon durduruldu ve sıfırlandı.")
        self.animation_timer.stop()
        self.control_panel.set_simulation_state(False)
        self.edit_menu.setEnabled(True)
        
        # 1. Animasyon verilerini temizle
        self.animation_routes = {}
        self.simulation_time = 0.0
        
        # 2. Araçları başlangıç konumlarına görsel ve mantıksal olarak döndür
        for v in self.vehicles:
            v.position = v.start_pos
            self.simulation_view.update_vehicle_position_smooth(v, v.start_pos, 'path')
        
        # 3. Sensörleri ve doluluk yazılarını sıfırla
        self.simulation_view.update_sensors(self.vehicles)
        if hasattr(self.simulation_view, 'capacity_labels'):
            for loc, label in self.simulation_view.capacity_labels.items():
                cap = self.road_network.capacity['pocket'] if loc in self.road_network.pockets else self.road_network.capacity['depot']
                label.setPlainText(f"0/{cap}")
        
        # 4. Bilgi tablosunu başlangıç haline getir
        self.update_info_table_initial()

    def update_info_table_initial(self):
        """Tablodaki araç konumlarını ve görev durumlarını başlangıç haline getirir."""
        for v in self.vehicles:
            if hasattr(v, '_table_row') and hasattr(v, '_real_tasks'):
                row = v._table_row
                self.info_table.setItem(row, 2, QTableWidgetItem(str(v.start_pos)))
                
                status_html = ""
                for real_task in v._real_tasks:
                    status_html += f'<span style="color:red; margin-right:10px; font-weight:bold;">[{real_task}]</span> '
                
                status_label = self.info_table.cellWidget(row, 3)
                if status_label:
                    status_label.setText(status_html)

    def handle_optimization_finished(self, result):
        if result['status'] == 'success':
            print("Optimizasyon başarılı! Animasyon başlıyor...")
            
            # Rotayı daha hızlı sorgulayabilmek için sözlüğe (t -> node) dönüştür
            self.animation_routes = {}
            self.task_completion_times = {}
            self.max_t = 0
            for vid, route in result['routes'].items():
                t_dict = {t: node for node, t in route}
                self.animation_routes[vid] = t_dict
                if route:
                    self.max_t = max(self.max_t, route[-1][1])
                    
                # Hangi t'lerde görevlerin bittiğini (ya da oradan geçildiğini) hesapla
                comp_times = []
                task_idx = 0
                v = next((veh for veh in self.vehicles if veh.vehicle_id == vid), None)
                if v:
                    for state in route:
                        loc = state[0][0]
                        t = state[1]
                        if task_idx < len(v.tasks) and loc == v.tasks[task_idx]:
                            comp_times.append(t)
                            task_idx += 1
                    self.task_completion_times[vid] = comp_times
                    
            self.simulation_time = 0.0
            
            # FPS Ayarları: 30 FPS = ~33ms per frame
            self.timer_interval = 33 
            self.ms_per_logical_step = 500.0  # 1 tam adım (10m) 500ms sürsün
            
            self.animation_timer.start(self.timer_interval) 
        else:
            self.edit_menu.setEnabled(True)
            self.control_panel.set_simulation_state(False)
            QMessageBox.critical(self, "Deadlock / Hata", result['message'])

    def animate_step(self):
        import math
        
        # Süreyi ilerlet (Hız çarpanını uygula)
        step_duration = self.ms_per_logical_step / self.animation_speed_factor
        self.simulation_time += (self.timer_interval / step_duration)
        
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
                
                current_loc = 0
                if self.simulation_time < min_t:
                    # Henüz başlamadı
                    node = route_dict[min_t]
                    loc, ntype = node
                    current_loc = loc
                    self.simulation_view.update_vehicle_position_smooth(vehicle, loc, ntype)
                    active_vehicles = True
                elif self.simulation_time >= max_t:
                    # Görev bitti
                    node = route_dict[max_t]
                    loc, ntype = node
                    current_loc = loc
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
                        current_loc = interpolated_loc
                        
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
                        current_loc = loc
                        self.simulation_view.update_vehicle_position_smooth(vehicle, loc, ntype)
                        if ntype in ('pocket', 'depot'):
                            occupancy[loc] += 1
                            
                # Tabloyu güncelle
                if hasattr(vehicle, '_table_row') and hasattr(vehicle, '_real_tasks'):
                    row = vehicle._table_row
                    self.info_table.setItem(row, 2, QTableWidgetItem(str(int(current_loc))))
                    
                    comp_times = self.task_completion_times.get(vehicle.vehicle_id, [])
                    completed_count = sum(1 for ct in comp_times if self.simulation_time >= ct)
                    
                    status_html = ""
                    for i, real_task in enumerate(vehicle._real_tasks):
                        depot_idx = 2 * i
                        zero_idx = 2 * i + 1
                        
                        if completed_count > zero_idx:
                            color = "green"
                        elif completed_count > depot_idx:
                            # Yüklenmiş ve başlangıca gidiyor (orange)
                            # Yaklaşık 500ms aralıklarla Turuncu ve Açık Yeşil arasında yanıp söner
                            is_blink = int(self.simulation_time * 2) % 2 == 0
                            color = "lightgreen" if is_blink else "orange"
                        elif completed_count == depot_idx:
                            # Devam eden (ongoing) görev: Araç yola çıktıysa yanıp sönsün
                            if self.simulation_time < min_t:
                                color = "red"
                            else:
                                # Yaklaşık 500ms (1 adım) aralıklarla yanıp sönme
                                is_blink = int(self.simulation_time * 2) % 2 == 0
                                color = "lightgray" if is_blink else "inherit"
                        else:
                            color = "red"
                            
                        status_html += f'<span style="color:{color}; margin-right:10px; font-weight:bold;">[{real_task}]</span> '
                        
                    status_label = self.info_table.cellWidget(row, 3)
                    if status_label:
                        status_label.setText(status_html)
                            
        # Sensör renklerini güncelle
        self.simulation_view.update_sensors(self.vehicles)

        # VIP araçların parlayan çerçevelerini güncelle
        self.simulation_view.animate_vips(self.simulation_time)

        # UI üzerindeki occupancy (n/slots) yazılarını güncelle
        if hasattr(self.simulation_view, 'capacity_labels'):
            for loc, count in occupancy.items():
                if loc in self.simulation_view.capacity_labels:
                    cap = self.road_network.capacity['pocket'] if loc in self.road_network.pockets else self.road_network.capacity['depot']
                    self.simulation_view.capacity_labels[loc].setPlainText(f"{count}/{cap}")
                
        if self.simulation_time >= self.max_t:
            print(f"Animasyon tamamlandı. Toplam süre: t={math.floor(self.simulation_time)}")
            self.animation_timer.stop()
            self.edit_menu.setEnabled(True)
            self.control_panel.set_simulation_state(False)
