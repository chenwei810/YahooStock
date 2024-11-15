"""
# 1. 執行打包腳本
python build.py

# 2. 或是使用 spec 文件
pyinstaller stock_monitor.spec

"""
# build.py
import PyInstaller.__main__
import sys
import os

# 確保在正確的目錄
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# PyInstaller 參數
params = [
    'stock_monitor.py',
    '--name=StockMonitor',
    '--noconsole',
    '--clean',
    '--onefile',
    # '--icon=icon.ico',  # 如果你有圖標的話
    '--add-data=README.md;.',  # 添加額外文件
    '--hidden-import=yfinance',
    '--hidden-import=pandas',
    '--hidden-import=pytz',
]

# 執行打包
PyInstaller.__main__.run(params)