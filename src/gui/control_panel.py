from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QPushButton, QGroupBox, QSpinBox, QHBoxLayout
from PyQt5.QtCore import pyqtSignal

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
        task_group = QGroupBox("Yeni Araç ve Görev Ekle")
        task_layout = QVBoxLayout()
        
        self.checkboxes = []
        for depot in self.road_network.depots:
            cb = QCheckBox(f"Depo {depot}")
            self.checkboxes.append((depot, cb))
            task_layout.addWidget(cb)

        add_task_btn = QPushButton("Görevli Araç Ekle")
        add_task_btn.clicked.connect(self.on_add_task_clicked)
        task_layout.addWidget(add_task_btn)
        
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

    def on_add_task_clicked(self):
        selected_depots = [depot for depot, cb in self.checkboxes if cb.isChecked()]
        if not selected_depots:
            print("Uyarı: Hiç depo seçilmedi. Araç görevsiz başlatılamaz.")
            return
            
        self.vehicle_count += 1
        self.add_task_signal.emit(self.vehicle_count, selected_depots)
        
        # Seçimleri temizle
        for _, cb in self.checkboxes:
            cb.setChecked(False)

    def on_add_depot_clicked(self):
        pos = self.depot_spinbox.value()
        self.add_depot_signal.emit(pos)

    def on_start_clicked(self):
        self.start_simulation_signal.emit()

    def refresh_depot_list(self):
        """Yeni depo eklendiğinde checkbox listesini günceller."""
        pass
