class Vehicle:
    """
    Otonom araç verilerini tutan sınıf.
    """
    def __init__(self, vehicle_id, start_pos=0):
        self.vehicle_id = vehicle_id
        self.position = start_pos  # 1D pozisyon (0-240 arası)
        self.tasks = []            # Ziyaret edilecek depolar
        self.direction = 1         # 1: Sağ (İleri), -1: Sol (Geri)
        self.status = "Bekliyor"   # "Hareket Halinde", "Bekliyor", "Tamamlandı"
        self.color = "blue"        # Arayüzde aracı temsil edecek renk

    def add_task(self, depot_pos):
        if depot_pos not in self.tasks:
            self.tasks.append(depot_pos)

    def __repr__(self):
        return f"Vehicle({self.vehicle_id}, pos={self.position}, tasks={self.tasks})"
