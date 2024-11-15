import sys
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
from concurrent.futures import ThreadPoolExecutor
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QPushButton, QTableWidget, 
                           QTableWidgetItem, QHeaderView, QFrame, QGridLayout,
                           QSplitter)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette, QGuiApplication

class InfoPanel(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # 標題
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; color: #00b4d8;")
        title_label.setFont(QFont('Microsoft JhengHei', 10))
        layout.addWidget(title_label)
        
        # 內容區域
        self.content = QLabel()
        self.content.setFont(QFont('Microsoft JhengHei', 12))
        self.content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.content)

    def update_content(self, text, color=None):
        if color:
            self.content.setStyleSheet(f"color: {color};")
        self.content.setText(text)

class MarketTable(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_style()
        
    def setup_style(self):
        # 設置表格樣式
        self.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                gridline-color: #2d2d2d;
                color: #e0e0e0;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #2c5380;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #00b4d8;
                border: 1px solid #3a3a3a;
                padding: 4px;
                font-weight: bold;
            }
            QScrollBar:vertical {
                border: none;
                background: #1e1e1e;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #3a3a3a;
                min-height: 20px;
                border-radius: 5px;
            }
        """)
        
        # 設置表頭
        self.setColumnCount(7)
        self.setHorizontalHeaderLabels(['類型', '名稱', '現價', '漲跌', '漲跌幅', '成交量', '更新時間'])
        
        # 設置表頭樣式
        header = self.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # 設置字體
        self.setFont(QFont('Microsoft JhengHei', 10))

class StockMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('專業版股市監控系統')
        self.setGeometry(100, 100, 1200, 800)
        self.setup_ui()
        
    def setup_ui(self):
        # 設置中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 頂部資訊面板
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)
        
        # 建立資訊面板
        self.time_panel = InfoPanel("系統時間")
        self.us_market_panel = InfoPanel("美股市場")
        self.asia_market_panel = InfoPanel("亞股市場")
        self.europe_market_panel = InfoPanel("歐股市場")
        
        top_layout.addWidget(self.time_panel)
        top_layout.addWidget(self.us_market_panel)
        top_layout.addWidget(self.asia_market_panel)
        top_layout.addWidget(self.europe_market_panel)
        
        main_layout.addWidget(top_panel)
        
        # 主要數據表格
        self.table = MarketTable()
        main_layout.addWidget(self.table)
        
        # 底部控制面板
        bottom_panel = QWidget()
        bottom_layout = QHBoxLayout(bottom_panel)
        
        update_button = QPushButton('立即更新')
        update_button.setStyleSheet("""
            QPushButton {
                background-color: #00b4d8;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #0096c7;
            }
        """)
        update_button.clicked.connect(self.update_data)
        
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #e0e0e0;")
        
        bottom_layout.addWidget(update_button)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.status_label)
        
        main_layout.addWidget(bottom_panel)
        
        # 設置深色主題
        self.setup_dark_theme()
        
        # 設置定時器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)  # 每秒更新一次
        
        # 初始化數據
        self.update_data()
        
    def setup_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QWidget {
                background-color: #121212;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)
        
    def get_stock_data(self, symbol, name, market_type='指數'):
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period='1d')
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                previous_close = hist['Open'].iloc[0]
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100
                volume = hist['Volume'].iloc[-1]
                
                return {
                    '名稱': name,
                    '現價': f"{current_price:.2f}",
                    '漲跌': f"{change:+.2f}",
                    '漲跌幅': f"{change_percent:+.2f}%",
                    '成交量': f"{volume:,.0f}",
                    '類型': market_type,
                    'change_value': change
                }
                
        except Exception as e:
            print(f"獲取 {name} 數據時發生錯誤: {str(e)}")
        
        return {
            '名稱': name,
            '現價': 'N/A',
            '漲跌': 'N/A',
            '漲跌幅': 'N/A',
            '成交量': 'N/A',
            '類型': market_type,
            'change_value': 0
        }

    def get_market_data(self):
        symbols = {
            # 指數
            "^GSPC": ("S&P 500", "國際指數"),
            "^DJI": ("道瓊工業", "國際指數"),
            "^IXIC": ("納斯達克", "國際指數"),
            "^N225": ("日經225", "國際指數"),
            "^HSI": ("恆生指數", "國際指數"),
            "000001.SS": ("上證指數", "國際指數"),
            "^FTSE": ("富時100", "國際指數"),
            "^GDAXI": ("德國DAX", "國際指數"),
            "^TWII": ("台灣加權", "台灣指數"),
            # ADR
            "TSM": ("台積電ADR", "ADR"),
            "HNHPF": ("鴻海ADR", "ADR"),
            # 台股
            "2330.TW": ("台積電", "台股"),
            "2317.TW": ("鴻海", "台股"),
            "2357.TW": ("華碩", "台股"),
        }
        
        with ThreadPoolExecutor(max_workers=len(symbols)) as executor:
            futures = [
                executor.submit(self.get_stock_data, symbol, name, market_type)
                for symbol, (name, market_type) in symbols.items()
            ]
            data = [future.result() for future in futures]
        
        return pd.DataFrame(data).sort_values(['類型', '名稱'])

    def update_data(self):
        try:
            # 更新時間
            tw_tz = pytz.timezone('Asia/Taipei')
            current_time = datetime.now(tw_tz)
            ny_time = current_time.astimezone(pytz.timezone('America/New_York'))
            london_time = current_time.astimezone(pytz.timezone('Europe/London'))
            
            # 更新資訊面板
            self.time_panel.update_content(current_time.strftime('%Y-%m-%d %H:%M:%S'))
            self.us_market_panel.update_content(f"紐約時間\n{ny_time.strftime('%H:%M:%S')}")
            self.asia_market_panel.update_content(f"台北時間\n{current_time.strftime('%H:%M:%S')}")
            self.europe_market_panel.update_content(f"倫敦時間\n{london_time.strftime('%H:%M:%S')}")
            
            # 獲取數據
            df = self.get_market_data()
            
            # 更新表格
            self.table.setRowCount(len(df))
            
            for row_idx, (_, row) in enumerate(df.iterrows()):
                # 設置時間
                update_time = current_time.strftime('%H:%M:%S')
                
                # 建立表格項目
                items = [
                    QTableWidgetItem(row['類型']),
                    QTableWidgetItem(row['名稱']),
                    QTableWidgetItem(row['現價']),
                    QTableWidgetItem(row['漲跌']),
                    QTableWidgetItem(row['漲跌幅']),
                    QTableWidgetItem(row['成交量']),
                    QTableWidgetItem(update_time)
                ]
                
                # 設置對齊
                items[0].setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                items[1].setTextAlignment(Qt.AlignmentFlag.AlignLeft)
                for item in items[2:]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                
                # 設置顏色
                try:
                    change_value = float(row.get('change_value', 0))
                    color = QColor("#ff4d4d") if change_value > 0 else QColor("#00ff00") if change_value < 0 else QColor("#e0e0e0")
                    for item in items:
                        item.setForeground(color)
                except ValueError:
                    pass
                
                # 更新表格
                for col, item in enumerate(items):
                    self.table.setItem(row_idx, col, item)
            
            self.status_label.setText("數據更新成功")
            
        except Exception as e:
            self.status_label.setText(f"更新失敗: {str(e)}")

def main():
    app = QApplication(sys.argv)
    
    # 設置應用程式樣式
    app.setStyle('Fusion')
    
    # 建立並顯示主視窗
    window = StockMonitor()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()