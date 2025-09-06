# データダウンロード用スクリプト
# download_plateau_data.py として保存
#!/usr/bin/env python
"""PLATEAUデータのダウンロードヘルパー"""

import requests
import zipfile
from pathlib import Path
import json

def download_plateau_sample():
    """サンプルデータのダウンロード先を案内"""
    
    print("=" * 60)
    print("PLATEAU データダウンロード ガイド")
    print("=" * 60)
    
    print("\n📍 東京23区のデータ取得方法:\n")
    
    print("1. ブラウザで以下のURLにアクセス:")
    print("   https://www.geospatial.jp/ckan/dataset/plateau-tokyo23ku-2022")
    
    print("\n2. 以下のデータをダウンロード:")
    print("   - 建築物モデル（CityGML or GeoJSON形式）")
    print("   - できれば「bldg」を含むファイル")
    
    print("\n3. 小さいエリアから始める（例：渋谷区のみ）:")
    print("   - 13113_shibuya-ku_2022_citygml_1_op.zip")
    
    print("\n4. ダウンロードしたファイルを解凍:")
    print("   unzip [ファイル名].zip -d data/plateau/")
    
    print("\n" + "=" * 60)
    print("より簡単な方法：東京都のサンプルデータ（GeoJSON）")
    print("=" * 60)
    
    # 東京都オープンデータから建物データを取得する例
    sample_urls = {
        "新宿駅周辺": "https://raw.githubusercontent.com/tokyo-metropolitan-gov/opendata-api/master/data/building_shinjuku_sample.geojson",
        "渋谷駅周辺": "https://raw.githubusercontent.com/tokyo-metropolitan-gov/opendata-api/master/data/building_shibuya_sample.geojson"
    }
    
    print("\nサンプルデータ（これらは例です、実際のURLは異なる場合があります）:")
    for area, url in sample_urls.items():
        print(f"  - {area}: {url}")
    
    return sample_urls

if __name__ == "__main__":
    download_plateau_sample()