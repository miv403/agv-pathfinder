from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QGroupBox, QSpinBox, QHBoxLayout, QComboBox, QListWidget, QListWidgetItem, QCheckBox
from PyQt5.QtCore import pyqtSignal, Qt

class ControlPanel(QWidget):
    # Yeni görev/araç eklendiğinde (vehicle_id, start_loc, direction, secili_depolar, is_vip) ileten sinyal
    add_task_signal = pyqtSignal(int, int, str, list, bool)
    
    # Yeni depo eklendiğinde (pozisyon) ileten sinyal
    add_depot_signal = pyqtSignal(int)
    
    # Yeni cep eklendiğinde (pozisyon) ileten sinyal
    add_pocket_signal = pyqtSignal(int)
    
    # Simülasyonu başlatma/durdurma sinyalleri
    start_simulation_signal = pyqtSignal()
    stop_simulation_signal = pyqtSignal()
    pause_simulation_signal = pyqtSignal()

    def __init__(self, road_network):
        super().__init__()
        self.road_network = road_network
        self.vehicle_count = 0
        self.is_sim_running = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 1. Görev Ekleme Alanı
        task_group = QGroupBox("Yeni Araç Ekle")
        task_layout = QVBoxLayout()
        
        # --- 1. Vehicle Properties (Single Values) ---
        props_layout = QHBoxLayout()
        
        self.start_loc_spinbox = QSpinBox()
        self.start_loc_spinbox.setRange(0, self.road_network.length)
        self.start_loc_spinbox.setSingleStep(self.road_network.step)
        
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["İleri", "Geri"])
        
        props_layout.addWidget(QLabel("Konum:"))
        props_layout.addWidget(self.start_loc_spinbox)
        props_layout.addWidget(QLabel("Yön:"))
        props_layout.addWidget(self.direction_combo)
        
        task_layout.addLayout(props_layout)
        
        # --- 2. Task Selection (Multiple Values) ---
        task_selection_layout = QHBoxLayout()
        
        self.depot_combo = QComboBox()
        self.update_depot_combo() # Fills with current depots
        
        add_task_btn = QPushButton("Ekle")
        add_task_btn.clicked.connect(self.add_task_to_list)
        
        task_selection_layout.addWidget(QLabel("Depo:"))
        task_selection_layout.addWidget(self.depot_combo)
        task_selection_layout.addWidget(add_task_btn)
        
        task_layout.addLayout(task_selection_layout)
        
        # --- 3. The Task List ---
        self.task_list = QListWidget()
        task_layout.addWidget(QLabel("Seçili Görevler:"))
        task_layout.addWidget(self.task_list)

        # --- 4. VIP Checkbox ---
        self.vip_checkbox = QCheckBox("VIP Araç")
        task_layout.addWidget(self.vip_checkbox)
        
        # --- 5. Spawn Button ---
        spawn_btn = QPushButton("Aracı Sahaya Sür")
        spawn_btn.clicked.connect(self.spawn_vehicle)
        task_layout.addWidget(spawn_btn)
        
        task_group.setLayout(task_layout)
        layout.addWidget(task_group)

        # 2. Dinamik Depo Ekleme Alanı
        depot_group = QGroupBox("Yeni Depo Ekle")
        depot_layout = QHBoxLayout()
        self.depot_spinbox = QSpinBox()
        self.depot_spinbox.setRange(0, self.road_network.length)
        self.depot_spinbox.setSingleStep(self.road_network.step)
        depot_layout.addWidget(QLabel("Mesafe:"))
        depot_layout.addWidget(self.depot_spinbox)
        
        add_depot_btn = QPushButton("Depo Ekle")
        add_depot_btn.clicked.connect(self.on_add_depot_clicked)
        depot_layout.addWidget(add_depot_btn)
        
        depot_group.setLayout(depot_layout)
        layout.addWidget(depot_group)

        # 3. Dinamik Cep Ekleme Alanı
        pocket_group = QGroupBox("Yeni Cep Ekle")
        pocket_layout = QHBoxLayout()
        self.pocket_spinbox = QSpinBox()
        self.pocket_spinbox.setRange(0, self.road_network.length)
        self.pocket_spinbox.setSingleStep(self.road_network.step)
        pocket_layout.addWidget(QLabel("Mesafe:"))
        pocket_layout.addWidget(self.pocket_spinbox)
        
        add_pocket_btn = QPushButton("Cep Ekle")
        add_pocket_btn.clicked.connect(self.on_add_pocket_clicked)
        pocket_layout.addWidget(add_pocket_btn)
        
        pocket_group.setLayout(pocket_layout)
        layout.addWidget(pocket_group)

        # 4. Başlat/Durdur ve Duraklat Butonları
        buttons_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Simülasyonu Başlat")
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.start_btn.clicked.connect(self.on_start_clicked)
        buttons_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("Duraklat")
        self.pause_btn.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 10px;")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.on_pause_clicked)
        buttons_layout.addWidget(self.pause_btn)
        
        layout.addLayout(buttons_layout)

        layout.addStretch()
        self.setLayout(layout)
        self.setFixedWidth(320)

    def update_depot_combo(self):
        self.depot_combo.clear()
        for depot in self.road_network.depots:
            self.depot_combo.addItem(f"Depo {depot}", depot)

    def add_task_to_list(self):
        if self.depot_combo.count() == 0:
            return
            
        depot_id = self.depot_combo.currentData()
        
        item = QListWidgetItem(f"Depo {depot_id}")
        item.setData(Qt.UserRole, depot_id)
        
        self.task_list.addItem(item)

    def spawn_vehicle(self):
        if self.task_list.count() == 0:
            print("Uyarı: Araca atanmış görev yok.")
            return
            
        # 1. Get Single Properties (A* uyumu için en yakın 10'luk kata yuvarla)
        raw_loc = self.start_loc_spinbox.value()
        step = self.road_network.step
        start_location = round(raw_loc / step) * step
        
        direction = self.direction_combo.currentText()
            
        # 2. Get Multiple Properties
        selected_depots = []
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            selected_depots.append(item.data(Qt.UserRole))
            
        is_vip = self.vip_checkbox.isChecked()
        
        # VIP Kısıtları Uygula
        if is_vip:
            start_location = 0
            if selected_depots:
                selected_depots = [selected_depots[0]] # Sadece ilk görevi al
            
        self.vehicle_count += 1
        
        self.add_task_signal.emit(self.vehicle_count, start_location, direction, selected_depots, is_vip)
        
        # Temizle
        self.task_list.clear()
        self.vip_checkbox.setChecked(False)

    def on_add_depot_clicked(self):
        raw_pos = self.depot_spinbox.value()
        step = self.road_network.step
        pos = round(raw_pos / step) * step
        self.add_depot_signal.emit(pos)

    def on_add_pocket_clicked(self):
        raw_pos = self.pocket_spinbox.value()
        step = self.road_network.step
        pos = round(raw_pos / step) * step
        self.add_pocket_signal.emit(pos)

    def on_start_clicked(self):
        if self.is_sim_running:
            self.stop_simulation_signal.emit()
        else:
            self.start_simulation_signal.emit()

    def on_pause_clicked(self):
        self.pause_simulation_signal.emit()

    def set_pause_state(self, paused):
        if paused:
            self.pause_btn.setText("Devam Et")
            self.pause_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 10px;")
        else:
            self.pause_btn.setText("Duraklat")
            self.pause_btn.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 10px;")

    def set_simulation_state(self, running):
        """Butonun görünümünü simülasyon durumuna göre değiştirir."""
        self.is_sim_running = running
        if running:
            self.start_btn.setText("Durdur (Sıfırla)")
            self.start_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 10px;")
            self.pause_btn.setEnabled(True)
            self.set_pause_state(False)
        else:
            self.start_btn.setText("Simülasyonu Başlat")
            self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
            self.pause_btn.setEnabled(False)
            self.set_pause_state(False)

    def refresh_depot_list(self):
        """Yeni depo eklendiğinde combo listesini günceller."""
        self.update_depot_combo()
