import sys
from PyQt5.QtWidgets import QApplication
from src.gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # PyQt uygulamasının stilini ayarlayabiliriz (isteğe bağlı)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        return 0

if __name__ == '__main__':
    main()
