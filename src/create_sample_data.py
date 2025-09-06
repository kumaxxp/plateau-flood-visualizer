# create_sample_data.py として保存
#!/usr/bin/env python
"""実際の東京の建物に似せたサンプルデータを作成"""

import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon, Point
import json
from pathlib import Path

def create_realistic_tokyo_data():
    """東京の実際の建物配置に似せたデータを生成"""
    
    print("🏢 リアルな東京建物データを生成中...")
    
    # 実際の東京の主要エリアの座標
    areas = {
        "shinjuku": {"center": [139.7003, 35.6938], "buildings": 150},
        "shibuya": {"center": [139.7019, 35.6580], "buildings": 120},
        "tokyo_station": {"center": [139.7671, 35.6812], "buildings": 100},
        "roppongi": {"center": [139.7314, 35.6627], "buildings": 80}
    }
    
    all_buildings = []
    
    for area_name, area_info in areas.items():
        center_lon, center_lat = area_info["center"]
        num_buildings = area_info["buildings"]
        
        # エリアごとに建物を生成
        for i in range(num_buildings):
            # 建物の位置（エリア中心から広がる）
            angle = np.random.uniform(0, 2 * np.pi)
            distance = np.random.exponential(0.005)  # 中心部に密集
            
            lon = center_lon + distance * np.cos(angle)
            lat = center_lat + distance * np.sin(angle)
            
            # 建物のサイズ（中心部ほど大きい）
            if distance < 0.002:  # 中心部
                size = np.random.uniform(0.0001, 0.0002)
                height = np.random.uniform(30, 200)  # 高層ビル
                storeys = int(height / 3.5)
            elif distance < 0.005:  # 中間部
                size = np.random.uniform(0.00008, 0.00015)
                height = np.random.uniform(15, 60)  # 中層ビル
                storeys = int(height / 3.5)
            else:  # 周辺部
                size = np.random.uniform(0.00005, 0.0001)
                height = np.random.uniform(6, 20)  # 低層建物
                storeys = int(height / 3.5)
            
            # 建物の形状（長方形）
            width = size * np.random.uniform(0.8, 1.2)
            depth = size * np.random.uniform(0.8, 1.2)
            
            # 建物の向き（道路に沿うように）
            rotation = np.random.choice([0, 45, 90, 135]) * np.pi / 180
            
            # ポリゴンを作成
            corners = [
                (lon - width/2, lat - depth/2),
                (lon + width/2, lat - depth/2),
                (lon + width/2, lat + depth/2),
                (lon - width/2, lat + depth/2)
            ]
            
            # 回転を適用（簡略化）
            poly = Polygon(corners)
            
            # 地面の高さ（東京の地形を模擬）
            # 東側（東京湾側）ほど低い
            ground_height = max(0, 10 - (lon - 139.7) * 100)
            
            all_buildings.append({
                'geometry': poly,
                'height': height,
                'storeys': storeys,
                'ground_height': ground_height,
                'area': area_name,
                'building_type': '商業ビル' if height > 50 else 'オフィスビル' if height > 20 else '住宅'
            })
    
    # GeoDataFrameを作成
    gdf = gpd.GeoDataFrame(all_buildings)
    gdf.set_crs('EPSG:4326', inplace=True)
    
    # 保存
    output_dir = Path("data/plateau")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "tokyo_buildings.geojson"
    gdf.to_file(output_file, driver='GeoJSON')
    
    print(f"✅ データを保存しました: {output_file}")
    print(f"   建物数: {len(gdf)}")
    print(f"   エリア: {list(areas.keys())}")
    
    # 統計情報
    print("\n📊 建物統計:")
    print(f"  平均高さ: {gdf['height'].mean():.1f}m")
    print(f"  最高: {gdf['height'].max():.1f}m")
    print(f"  最低: {gdf['height'].min():.1f}m")
    
    return gdf

if __name__ == "__main__":
    create_realistic_tokyo_data()