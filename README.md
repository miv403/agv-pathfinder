# önceliklendirilmiş işbirlikçi A* temelli çok etmenli yol bulma

*Cooperative A\* Multi-Agent Pathfinding*

Detaylı bilgi için [paper.pdf](https://github.com/miv403/agv-pathfinder/blob/master/paper.pdf) dosyasını inceleyebilirsiniz.

<video src="./img/video.mp4" controls preload></video>

## Özet

**Amacı:** Dar koridor ve tek şeritli endüstriyel topolojilerde görev yapan otonom yönlendirmeli
araçların (AGV) yönlendirilmesi sırasında karşılaşılan koridor kilitlenmeleri ve darboğaz problem-
lerini çözerek toplam tamamlanma süresini optimize etmektir.

**Araştırma Yöntemi:** Araştırmada,
uzay-zaman yer ayırma tabanlı İşbirlikçi A* algoritması üzerinde kural ve öncelik tabanlı özgün
bir melez model kurgulanmıştır. Model kapsamında araçların önceliklerini, konumlarını ve iş yük-
lerini içeren sözlüksel öncelik vektörü tanımlanmış, ana yolda bekleme tamamen yasaklanarak
sığa kısıtlı cepler ve depolar kullanılmıştır. Gereksiz manevraları önlemek için asimetrik maliyet
yapısı uygulanmış ve araç içi görevler En Kısa İş İlk (SJF) yaklaşımıyla sıralanmıştır.

**Bulgular:** Yapılan senaryo analizlerinde, fiziksel güvenlik mesafesi ihlalleri dışında algoritmik bir kilitlenme
veya çarpışma hatasıyla karşılaşılmamıştır. Araç sayısı 5’ten 42’ye çıkarıldığında toplam zaman
adımı doğrusal artış gösterirken, hesaplama süresinin üstel büyüdüğü ve 42 araçta 3.85 saniyeye
ulaştığı gözlemlenmiştir.

**Sonuç ve Öneriler:** Önerilen melez modelin dar alanlarda deterministik
ve kararlı bir yönlendirme sağladığı, hesaplama süresinin çevrimdışı planlama için uygun olduğu
sonucuna varılmıştır. Gelecek çalışmalarda hesaplama maliyetini düşürmek için bölgesel planlama
ve dinamik zaman pencereleri yaklaşımlarının uygulanması önerilmektedir.

![](./img/senaryolar/0-zıt-yön-çatışması/00-başlangıç.png)

## bağımlılıklar

```bash
PyQt5
```

## çalıştırma

```bash
python main.py
```

ya da

```bash
chmod +x main.py
./main.py
```
