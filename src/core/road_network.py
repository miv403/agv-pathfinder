import heapq

class RoadNetwork:
    """
    Tek şeritli yolun ve üzerindeki bileşenlerin (sensörler, cepler, depolar) verilerini tutar.
    """
    def __init__(self, length=240):
        self.length = length
        self.sensors = [i for i in range(0, self.length + 1, 40)]
        self.pockets = [80, 200]  # Cepler (varsayılan)
        self.depots = [70, 120, 240]  # Ara depolar (varsayılan)
        
        # Algoritma için ön hesaplama haritası (lookup table) taslağı
        self.distance_matrix = {}

    def add_depot(self, position):
        if 0 <= position <= self.length and position not in self.depots:
            self.depots.append(position)
            self.depots.sort()

    def add_pocket(self, position):
        if 0 <= position <= self.length and position not in self.pockets:
            self.pockets.append(position)
            self.pockets.sort()

    def precompute_distances(self):
        """
        Düğümler (başlangıç, depolar, cepler) arası mesafelerin önceden hesaplanması.
        """
        pass
