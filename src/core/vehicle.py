class Vehicle:
    """
    Otonom araç verilerini tutan sınıf.
    """
    def __init__(self, vehicle_id, start_pos=0):
        self.vehicle_id = vehicle_id
        self.position = start_pos  # 1D pozisyon (0-240 arası)
        self.tasks = []            # Ziyaret edilecek lokasyonlar sırası
        self.direction = 1         # 1: Sağ (İleri), -1: Sol (Geri)
        self.status = "Bekliyor"   # "Hareket Halinde", "Bekliyor", "Tamamlandı"
        self.color = "blue"        # Arayüzde aracı temsil edecek renk
        self.is_vip = False        # Öncelikli araç (Stage 1 için)

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

    def __repr__(self):
        return f"Vehicle({self.vehicle_id}, pos={self.position}, tasks={self.tasks}, vip={self.is_vip})"
