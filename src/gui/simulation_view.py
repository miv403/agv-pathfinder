from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath
from PyQt5.QtCore import Qt, QPointF

import math

class SimulationView(QGraphicsView):
    def __init__(self, road_network):
        super().__init__()
        self.road_network = road_network
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        
        self.vehicle_items = {} # vehicle_id -> QGraphicsItem map
        
        # Ekran boyutlarına göre yolu çizmek için temel ayarlar
        self.scene.setSceneRect(0, 0, 800, 600)
        
        self.margin_x = 100
        self.width_x = 600
        self.start_y = 100
        self.y_step = 120  # Dikey kıvrımlar daha kısa

        self.draw_environment()

    def get_2d_position(self, distance_1d):
        """
        0-240m arasındaki 1 boyutlu uzaklığı, ekrandaki S şeklindeki 2 boyutlu (x, y) koordinatlarına çevirir.
        """
        seg_len = self.road_network.length / 3.0
        
        if distance_1d <= seg_len:
            segment = 0
            remainder = distance_1d
        elif distance_1d <= 2 * seg_len:
            segment = 1
            remainder = distance_1d - seg_len
        else:
            segment = 2
            remainder = distance_1d - 2 * seg_len
            
        if segment == 0:
            x = self.margin_x + (remainder / seg_len) * self.width_x
            y = self.start_y
        elif segment == 1:
            x = self.margin_x + self.width_x - (remainder / seg_len) * self.width_x
            y = self.start_y + self.y_step
        else: # segment == 2
            x = self.margin_x + (remainder / seg_len) * self.width_x
            y = self.start_y + 2 * self.y_step
            
        return QPointF(x, y)

    def draw_environment(self):
        self.scene.clear()
        
        # 1. Yolu Çiz (S Şeklinde)
        path = QPainterPath()
        # Segment 0
        path.moveTo(self.margin_x, self.start_y)
        path.lineTo(self.margin_x + self.width_x, self.start_y)
        # Dikey geçiş 1 (Sadece Görsel)
        path.lineTo(self.margin_x + self.width_x, self.start_y + self.y_step)
        # Segment 1
        path.lineTo(self.margin_x, self.start_y + self.y_step)
        # Dikey geçiş 2 (Sadece Görsel)
        path.lineTo(self.margin_x, self.start_y + 2 * self.y_step)
        # Segment 2
        path.lineTo(self.margin_x + self.width_x, self.start_y + 2 * self.y_step)
            
        pen = QPen(QColor("gray"), 30, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self.scene.addPath(path, pen)

        # 2. Sensörleri Çiz (Mavi Daireler, Yolun Altında)
        for s in self.road_network.sensors:
            pos = self.get_2d_position(s)
            y_offset = 25  # Yolun altına iz düşüm
            self.scene.addEllipse(pos.x() - 5, pos.y() + y_offset - 5, 10, 10, QPen(Qt.black), QBrush(Qt.cyan))
            text = self.scene.addText(f"S{s}")
            text.setPos(pos.x() - 10, pos.y() + y_offset + 5)

        self.capacity_labels = {}

        # 3. Cepleri Çiz (Yeşil Kareler, Yolun Üstünde)
        for p in self.road_network.pockets:
            pos = self.get_2d_position(p)
            y_offset = -30  # Yolun üstüne iz düşüm
            self.scene.addRect(pos.x() - 10, pos.y() + y_offset - 10, 20, 20, QPen(Qt.black), QBrush(Qt.green))
            text = self.scene.addText(f"C{p}")
            text.setPos(pos.x() - 10, pos.y() + y_offset - 35)
            
            cap = self.road_network.capacity.get('pocket', 1)
            cap_text = self.scene.addText(f"0/{cap}")
            cap_text.setDefaultTextColor(QColor("darkgreen"))
            cap_text.setPos(pos.x() - 10, pos.y() + y_offset + 10)
            self.capacity_labels[p] = cap_text

        # 4. Depoları Çiz (Kırmızı Kareler, Yolun Üstünde)
        for d in self.road_network.depots:
            pos = self.get_2d_position(d)
            y_offset = -32  # Yolun üstüne iz düşüm
            self.scene.addRect(pos.x() - 12, pos.y() + y_offset - 12, 24, 24, QPen(Qt.black), QBrush(Qt.red))
            text = self.scene.addText(f"D{d}")
            text.setPos(pos.x() - 10, pos.y() + y_offset - 35)
            
            cap = self.road_network.capacity.get('depot', 3)
            cap_text = self.scene.addText(f"0/{cap}")
            cap_text.setDefaultTextColor(QColor("darkred"))
            cap_text.setPos(pos.x() - 10, pos.y() + y_offset + 12)
            self.capacity_labels[d] = cap_text
            
    def update_road(self):
        """Yeni depo veya sensör eklendiğinde ekranı günceller."""
        self.draw_environment()
        
    def add_vehicle(self, vehicle):
        """Aracı ekrana ekler."""
        pos = self.get_2d_position(vehicle.position)
        item = self.scene.addEllipse(pos.x() - 8, pos.y() - 8, 16, 16, QPen(Qt.black), QBrush(QColor(vehicle.color)))
        self.vehicle_items[vehicle.vehicle_id] = item

    def clear_vehicles(self):
        """Tüm araç görsel nesnelerini siler."""
        for item in self.vehicle_items.values():
            self.scene.removeItem(item)
        self.vehicle_items = {}

    def get_type_y_offset(self, ntype):
        """Düğüm tipine göre görsel Y ekseni kaymasını (offset) döner."""
        if ntype == 'pocket':
            return -30
        elif ntype == 'depot':
            return -32
        return 0

    def update_vehicle_position_smooth(self, vehicle, loc, type1, type2=None, fraction=0.0):
        """Aracın ekrandaki konumunu yumuşak (interpolated) olarak günceller."""
        if vehicle.vehicle_id in self.vehicle_items:
            # X/Y koordinatını bul (get_2d_position ondalıklı değerleri mükemmel eşler)
            pos = self.get_2d_position(loc)
            
            offset1 = self.get_type_y_offset(type1)
            offset2 = self.get_type_y_offset(type2) if type2 else offset1
            
            # Eğer cebe/depoya girip çıkıyorsa Y offset'i de yumuşakça anime et
            y_offset = offset1 + (offset2 - offset1) * fraction
                
            item = self.vehicle_items[vehicle.vehicle_id]
            # setRect, posizyonu güncellemek için (ellipse x,y'si bounding box)
            item.setRect(pos.x() - 8, pos.y() + y_offset - 8, 16, 16)
