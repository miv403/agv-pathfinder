from PyQt5.QtGui import QColor

class Vehicle:
    """
    Otonom araç verilerini tutan sınıf.
    """
    def __init__(self, vehicle_id, start_pos=0, direction=1, is_vip=False):
        self.vehicle_id = vehicle_id
        self.position = start_pos  # 1D pozisyon (0-240 arası)
        self.start_pos = start_pos # Saklanan orijinal başlangıç noktası
        self.tasks = []            # Ziyaret edilecek lokasyonlar sırası
        self.direction = direction # 1: Sağ (İleri), -1: Sol (Geri)
        self.status = "Bekliyor"   # "Hareket Halinde", "Bekliyor", "Tamamlandı"
        self.is_vip = is_vip        # Öncelikli araç (Stage 1 için)
        
        # Benzersiz renk ataması (Altın Oran tabanlı Hue kaydırması)
        # ID tamsayı değilse hash değerini kullanıyoruz
        try:
            numeric_id = int(vehicle_id)
        except (ValueError, TypeError):
            numeric_id = abs(hash(str(vehicle_id)))
            
        # 137.5 derece (Altın Oran konjugatı) renklerin en geniş şekilde yayılmasını sağlar
        hue = int((numeric_id * 137.5) % 360)
        self.color = QColor.fromHsv(hue, 230, 255)  # Canlı ve doygun renkler

    def add_task(self, target_pos):
        """Araç için sırayla gidilecek görev ekler"""
        self.tasks.append(target_pos)

    @property
    def furthest_target_distance(self):
        """
        Stage 1 önceliklendirmesi için en uzak hedefin başlangıç noktasına uzaklığını döner.
        Hiç görevi yoksa 0 döner.
        """
        if not self.tasks:
            return 0
        distances = [abs(task - self.position) for task in self.tasks]
        return max(distances)

    @property
    def current_target(self):
        """Mevcut (ilk) hedef lokasyon"""
        if not self.tasks:
            return self.start_pos
        return self.tasks[0]

    @property
    def total_mission_distance(self):
        """Tüm görev noktaları arasındaki toplam mesafe"""
        if not self.tasks:
            return 0
        total = 0
        current = self.start_pos
        for task in self.tasks:
            total += abs(task - current)
            current = task
        return total

    def __repr__(self):
        return f"Vehicle({self.vehicle_id}, pos={self.position}, tasks={self.tasks}, vip={self.is_vip})"
