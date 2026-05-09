import heapq

class RoadNetwork:
    """
    Tek şeritli yolun ve üzerindeki bileşenlerin (sensörler, cepler, depolar) verilerini tutar.
    Ayrık düğümler (discrete nodes) üzerinden çalışır: (lokasyon, tip)
    """
    def __init__(self, length=240, step=10):
        self.length = length
        self.step = step
        self.sensors = [i for i in range(0, self.length + 1, 40)]
        self.pockets = [80, 200]  # Cepler (varsayılan)
        self.depots = [70, 120, 240]  # Ara depolar / Warehouses (varsayılan)
        
        self.capacity = {
            'pocket': 1,
            'depot': 3
        }
        
        self.distance_matrix = {}

    def add_depot(self, position):
        if 0 <= position <= self.length and position not in self.depots and position % self.step == 0:
            self.depots.append(position)
            self.depots.sort()

    def add_pocket(self, position):
        if 0 <= position <= self.length and position not in self.pockets and position % self.step == 0:
            self.pockets.append(position)
            self.pockets.sort()

    def is_valid_node(self, node):
        loc, ntype = node
        if loc < 0 or loc > self.length or loc % self.step != 0:
            return False
        if ntype == 'path':
            return True
        elif ntype == 'pocket':
            return loc in self.pockets
        elif ntype == 'depot':
            return loc in self.depots
        return False

    def get_neighbors(self, node):
        """
        Graf üzerindeki fiziksel (zaman hariç) komşulukları döner.
        """
        loc, ntype = node
        neighbors = []
        if ntype == 'path':
            # 1. Ana yolda ileri veya geri gitmek
            if loc + self.step <= self.length:
                neighbors.append((loc + self.step, 'path'))
            if loc - self.step >= 0:
                neighbors.append((loc - self.step, 'path'))
            
            # 2. Aynı lokasyondaki cebe veya depoya girmek
            if loc in self.pockets:
                neighbors.append((loc, 'pocket'))
            if loc in self.depots:
                neighbors.append((loc, 'depot'))
                
        elif ntype in ('pocket', 'depot'):
            # Cepten veya depodan ana yola çıkış (aynı lokasyona)
            neighbors.append((loc, 'path'))
            # Kendi içinde bekleyebilir
            neighbors.append((loc, ntype))
            
        return neighbors

    def precompute_distances(self):
        """
        A* algoritmasında kullanılacak heuristik mesafeler için lookup table.
        1D yolda mesafe `abs(target_loc - current_loc)` / step olarak hesaplanabilir.
        """
        pass
