from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QGroupBox, QSpinBox, QHBoxLayout, QComboBox, QListWidget, QListWidgetItem
from PyQt5.QtCore import pyqtSignal, Qt

class ControlPanel(QWidget):
    # Yeni görev/araç eklendiğinde (vehicle_id, start_loc, direction, secili_depolar) ileten sinyal
    add_task_signal = pyqtSignal(int, int, str, list)
    
    # Yeni depo eklendiğinde (pozisyon) ileten sinyal
    add_depot_signal = pyqtSignal(int)
    
    # Simülasyonu başlatma sinyali
    start_simulation_signal = pyqtSignal()

    def __init__(self, road_network):
        super().__init__()
        self.road_network = road_network
        self.vehicle_count = 0
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
        
        # --- 4. Spawn Button ---
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
        depot_layout.addWidget(QLabel("Mesafe:"))
        depot_layout.addWidget(self.depot_spinbox)
        
        add_depot_btn = QPushButton("Depo Ekle")
        add_depot_btn.clicked.connect(self.on_add_depot_clicked)
        depot_layout.addWidget(add_depot_btn)
        
        depot_group.setLayout(depot_layout)
        layout.addWidget(depot_group)

        # 3. Başlat Butonu
        start_btn = QPushButton("Simülasyonu Başlat")
        start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        start_btn.clicked.connect(self.on_start_clicked)
        layout.addWidget(start_btn)

        layout.addStretch()
        self.setLayout(layout)
        self.setFixedWidth(250)

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
            
        self.vehicle_count += 1
        
        self.add_task_signal.emit(self.vehicle_count, start_location, direction, selected_depots)
        
        # Temizle
        self.task_list.clear()

    def on_add_depot_clicked(self):
        pos = self.depot_spinbox.value()
        self.add_depot_signal.emit(pos)

    def on_start_clicked(self):
        self.start_simulation_signal.emit()

    def refresh_depot_list(self):
        """Yeni depo eklendiğinde combo listesini günceller."""
        self.update_depot_combo()
