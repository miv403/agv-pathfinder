import heapq

class CooperativeAStar:
    """
    Cooperative A* (CA*) Algoritması.
    Araçları önceliğe göre sıralar ve uzay-zaman (Space-Time) grafında sıralı olarak rotalar.
    Deadlock resolver ve d_min güvenlik tamponu mekanizmalarını içerir.
    """
    def __init__(self, road_network):
        self.rn = road_network
        self.reservation_table = {}  # (loc, type, t) -> count

    def reset(self):
        self.reservation_table = {}

    def heuristic(self, current_node, goal_node):
        """
        Heuristik fonksiyon: Sadece lokasyonlar arası düz 1D mesafe (adım cinsinden).
        Aynı lokasyondaki tip (pocket/depot vs) geçişleri t+1 alacağı için +0 maliyetle heuristic'e ekleyebiliriz,
        ancak düz mesafe admisibility için yeterlidir.
        """
        c_loc, _ = current_node
        g_loc, _ = goal_node
        return abs(c_loc - g_loc) // self.rn.step

    def is_valid_state(self, node, t):
        """
        Verilen (node, t) durumunun rezervasyon tablosunda müsait olup olmadığını kontrol eder.
        """
        loc, ntype = node
        key = (loc, ntype, t)
        
        if ntype == 'path':
            # Ana yolda buffer kuralları gereği tabloya eklenen herhangi bir blokaj kapasite aşımıdır
            if self.reservation_table.get(key, 0) >= 1:
                return False
        else:
            # Pocket veya depot: kapasite kontrolü
            if self.reservation_table.get(key, 0) >= self.rn.capacity.get(ntype, 1):
                return False
                
        return True

    def reserve_route(self, route):
        """
        A* sonucu bulunan rotayı merkezi rezervasyon tablosuna ekler.
        """
        for state in route:
            node, t = state
            loc, ntype = node
            
            if ntype == 'path':
                # Kullanıcının kuralı: 50 -> 30, 40, 50, 60, 70
                # Yani d_min = 20 için +/- 20m buffer (2 step)
                for d in [-20, -10, 0, 10, 20]:
                    buffer_loc = loc + d
                    if 0 <= buffer_loc <= self.rn.length:
                        b_key = (buffer_loc, 'path', t)
                        self.reservation_table[b_key] = self.reservation_table.get(b_key, 0) + 1
            else:
                # Pocket veya Depot: Sadece bulunduğu nokta
                key = (loc, ntype, t)
                self.reservation_table[key] = self.reservation_table.get(key, 0) + 1

    def find_path_segment(self, start_node, t_start, goal_node):
        """
        Tek bir segment (başlangıç -> hedef) için A* çalıştırır.
        Bulunan rotayı: [(node, t), (node, t+1), ...] şeklinde döner.
        """
        open_set = []
        # heap: (f_score, t, node) - t'yi de koyduk ki tie-break durumunda zamana göre sıralansın
        heapq.heappush(open_set, (0, t_start, start_node))
        
        came_from = {}
        g_score = {(start_node, t_start): 0}
        
        # Sınır: Çok uzun beklemeleri veya sonsuz döngüyü engellemek için maks A* iterasyonu (örn. 10000)
        max_iter = 10000
        iterations = 0
        
        while open_set:
            iterations += 1
            if iterations > max_iter:
                return None  # Deadlock veya yol bulunamadı
                
            _, current_t, current_node = heapq.heappop(open_set)
            
            if current_node == goal_node:
                # Hedefe ulaşıldı, rotayı oluştur
                path = []
                curr = (current_node, current_t)
                while curr in came_from:
                    path.append(curr)
                    curr = came_from[curr]
                path.append((start_node, t_start))
                path.reverse()
                return path
                
            for next_node in self.rn.get_neighbors(current_node):
                next_t = current_t + 1
                
                # Kural 2: Ana yolda (path) beklemek yasaktır!
                if next_node == current_node and next_node[1] == 'path':
                    continue
                    
                # Çakışma kontrolü
                if not self.is_valid_state(next_node, next_t):
                    continue
                    
                tentative_g = g_score[(current_node, current_t)] + 1
                
                if tentative_g < g_score.get((next_node, next_t), float('inf')):
                    came_from[(next_node, next_t)] = (current_node, current_t)
                    g_score[(next_node, next_t)] = tentative_g
                    f = tentative_g + self.heuristic(next_node, goal_node)
                    heapq.heappush(open_set, (f, next_t, next_node))
                    
        return None  # Çözüm bulunamadı

    def solve(self, vehicles):
        """
        Tüm sistemi planlar ve çözer.
        Stage 1: Önceliklendirme
        Stage 2 & 3: Sıralı Rota Hesaplama ve Deadlock Resolver
        """
        self.reset()
        
        # Max capacity check: yoldaki toplam araç sayısı depo/cep kapasitelerini aşmamalı (deadlock rule)
        total_slots = sum(self.rn.capacity.get('pocket', 1) for _ in self.rn.pockets) + \
                      sum(self.rn.capacity.get('depot', 3) for _ in self.rn.depots)
                      
        if len(vehicles) > total_slots:
            return {"status": "error", "message": f"Araç sayısı ({len(vehicles)}) yoldaki güvenli slot sayısını ({total_slots}) aşıyor! Deadlock kaçınılmaz."}

        # Stage 1: Sort vehicles
        # VIP: True > False (Yani True olanlar önce gelir)
        # Furthest: Büyükten küçüğe
        sorted_vehicles = sorted(
            vehicles,
            key=lambda v: (v.is_vip, v.furthest_target_distance),
            reverse=True
        )

        all_routes = {}  # vehicle_id -> list of (node, t)

        for vehicle in sorted_vehicles:
            full_route = []
            
            # Start at t_initial
            # We implement Deadlock Resolver: if A* fails, increment t_initial and try again
            t_initial = 0
            max_delay_attempts = 200 # t_initial = 1000'e kadar (200 * 5) dener
            success = False
            
            while t_initial < max_delay_attempts * 5 and not success:
                vehicle_route = []
                current_t = t_initial
                # Basitlik için başlangıç düğümü 'path' olarak varsayılır
                current_node = (vehicle.position, 'path') 
                
                # Hedefleri sırayla gez (Segment bazlı A*)
                segment_success = True
                
                for task_loc in vehicle.tasks:
                    # Görev lokasyonunu 'depot' veya 'pocket' varsayıyoruz, değilse 'path'
                    if task_loc in self.rn.depots:
                        target_node = (task_loc, 'depot')
                    elif task_loc in self.rn.pockets:
                        target_node = (task_loc, 'pocket')
                    else:
                        target_node = (task_loc, 'path')
                        
                    segment_path = self.find_path_segment(current_node, current_t, target_node)
                    
                    if not segment_path:
                        segment_success = False
                        break
                        
                    # Önceki hedefin son düğümü ile yeni hedefin ilk düğümü aynı, mükerrerliği önle
                    if vehicle_route:
                        vehicle_route.extend(segment_path[1:])
                    else:
                        vehicle_route.extend(segment_path)
                        
                    # Sonraki segment için başlangıç bilgilerini güncelle
                    last_node, last_t = vehicle_route[-1]
                    current_node = last_node
                    current_t = last_t
                    
                if segment_success:
                    # Tüm görevler başarıyla ulaşıldı, rotayı rezerve et
                    self.reserve_route(vehicle_route)
                    all_routes[vehicle.vehicle_id] = vehicle_route
                    success = True
                else:
                    # Deadlock resolver: t_initial'ı artır ve tekrar dene
                    t_initial += 5  # "Ex: t = t + 5"
                    
            if not success:
                return {
                    "status": "error", 
                    "message": f"Araç {vehicle.vehicle_id} için çözüm bulunamadı! Yol çok dolu olabilir."
                }

        return {
            "status": "success",
            "routes": all_routes
        }
