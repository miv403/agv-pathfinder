from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QPushButton, QGroupBox, QSpinBox, QHBoxLayout, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import pyqtSignal, Qt

class ControlPanel(QWidget):
    # Yeni görev/araç eklendiğinde (vehicle_id, secili_depolar) ileten sinyal
    add_task_signal = pyqtSignal(int, list)
    
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
        
        # --- Top: Selection Area ---
        selection_layout = QHBoxLayout()
        self.depot_combo = QComboBox()
        self.update_depot_combo() # Fills combo with current depots
        
        add_task_btn = QPushButton("Ekle")
        add_task_btn.clicked.connect(self.add_task_to_table)
        
        selection_layout.addWidget(QLabel("Depo:"))
        selection_layout.addWidget(self.depot_combo)
        selection_layout.addWidget(add_task_btn)
        task_layout.addLayout(selection_layout)
        
        # --- Middle: The Task Grid ---
        # Start with 1 column for now. 
        # IN THE FUTURE: Change to 3 columns ["Depo", "Yön", "Konum"]
        self.task_table = QTableWidget(0, 1) 
        self.task_table.setHorizontalHeaderLabels(["Seçili Depolar"])
        self.task_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        task_layout.addWidget(self.task_table)
        
        # --- Bottom: Spawn Vehicle ---
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

    def add_task_to_table(self):
        if self.depot_combo.count() == 0:
            return
            
        depot_id = self.depot_combo.currentData()
        
        # Create a new row
        row_position = self.task_table.rowCount()
        self.task_table.insertRow(row_position)
        
        # Column 0: Depot ID
        item = QTableWidgetItem(f"Depo {depot_id}")
        item.setData(Qt.UserRole, depot_id) # Store the raw int ID invisibly
        self.task_table.setItem(row_position, 0, item)

    def spawn_vehicle(self):
        row_count = self.task_table.rowCount()
        if row_count == 0:
            print("Uyarı: Araca atanmış görev yok.")
            return
            
        selected_depots = []
        
        # Iterate through rows and extract the raw data
        for row in range(row_count):
            item = self.task_table.item(row, 0)
            depot_id = item.data(Qt.UserRole)
            selected_depots.append(depot_id)
            
        self.vehicle_count += 1
        
        # Emit your existing signal
        self.add_task_signal.emit(self.vehicle_count, selected_depots)
        
        # Clear the table for the next vehicle setup
        self.task_table.setRowCount(0)

    def on_add_depot_clicked(self):
        pos = self.depot_spinbox.value()
        self.add_depot_signal.emit(pos)

    def on_start_clicked(self):
        self.start_simulation_signal.emit()

    def refresh_depot_list(self):
        """Yeni depo eklendiğinde combo listesini günceller."""
        self.update_depot_combo()
