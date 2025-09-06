# patch_simulator.py として保存
"""simulator.pyに仮想データ生成機能を追加するパッチ"""

import sys
sys.path.append('.')

# simulator.pyを修正
simulator_code = '''
def load_buildings(self, filepath: Optional[Path] = None) -> gpd.GeoDataFrame:
    """建物データの読み込み（改善版）"""
    if filepath is None:
        # デフォルトパスを検索
        patterns = [
            f"{self.city}_buildings.gpkg",
            f"{self.city}_bldg.geojson",
            f"*{self.city}*bldg*.geojson"
        ]
        
        for pattern in patterns:
            files = list(self.data_dir.glob(pattern))
            if files:
                filepath = files[0]
                break
        else:
            # ファイルが見つからない場合は仮想データを生成
            print(f"警告: 建物データが見つかりません。仮想データを生成します。")
            return self._create_virtual_buildings()
    
    print(f"建物データ読み込み中: {filepath}")
    self.buildings = gpd.read_file(filepath)
    
    # 必要な列を確認・追加
    if 'height' not in self.buildings.columns:
        if 'storeys' in self.buildings.columns:
            self.buildings['height'] = self.buildings['storeys'] * 3.5
        else:
            self.buildings['height'] = 10.0
    
    if 'ground_height' not in self.buildings.columns:
        self.buildings['ground_height'] = 0.0
    
    if self.buildings.crs is None:
        self.buildings.set_crs('EPSG:4326', inplace=True)
    
    self.bounds = self.buildings.total_bounds
    print(f"  建物数: {len(self.buildings):,}")
    print(f"  範囲: {self.bounds}")
    
    return self.buildings

def _create_virtual_buildings(self) -> gpd.GeoDataFrame:
    """仮想建物データを生成"""
    import numpy as np
    from shapely.geometry import Polygon
    
    print("  仮想建物データを生成中...")
    buildings = []
    np.random.seed(42)
    
    # 都市の中心座標
    if self.city == "tokyo":
        center_lon, center_lat = 139.7, 35.68
    elif self.city == "nagoya":
        center_lon, center_lat = 136.9, 35.18
    else:
        center_lon, center_lat = 139.7, 35.68
    
    # 100個の建物を生成
    for i in range(100):
        lon = center_lon + np.random.uniform(-0.01, 0.01)
        lat = center_lat + np.random.uniform(-0.01, 0.01)
        size = 0.0001  # 約10m四方
        
        poly = Polygon([
            (lon, lat),
            (lon + size, lat),
            (lon + size, lat + size),
            (lon, lat + size)
        ])
        
        buildings.append({
            'geometry': poly,
            'height': np.random.uniform(5, 50),
            'ground_height': np.random.uniform(0, 5)
        })
    
    self.buildings = gpd.GeoDataFrame(buildings)
    self.buildings.set_crs('EPSG:4326', inplace=True)
    self.bounds = self.buildings.total_bounds
    
    print(f"  生成建物数: {len(self.buildings)}")
    print(f"  エリア: {self.city}（仮想データ）")
    
    return self.buildings
'''

print("パッチを適用しています...")

# simulator.pyを読み込んで修正
with open('src/simulator.py', 'r') as f:
    content = f.read()

# _create_virtual_buildings メソッドを追加
if '_create_virtual_buildings' not in content:
    # load_buildings メソッドの後に追加
    import_section = 'from tqdm import tqdm'
    new_import = 'from tqdm import tqdm\nimport numpy as np\nfrom shapely.geometry import Polygon'
    content = content.replace(import_section, new_import)
    
    # クラスの最後に新しいメソッドを追加
    class_end = 'if __name__ == "__main__":'
    new_method = '''
    def _create_virtual_buildings(self) -> gpd.GeoDataFrame:
        """仮想建物データを生成"""
        import numpy as np
        from shapely.geometry import Polygon
        
        print("  仮想建物データを生成中...")
        buildings = []
        np.random.seed(42)
        
        # 都市の中心座標
        if self.city == "tokyo":
            center_lon, center_lat = 139.7, 35.68
        elif self.city == "nagoya":
            center_lon, center_lat = 136.9, 35.18
        else:
            center_lon, center_lat = 139.7, 35.68
        
        # 100個の建物を生成
        for i in range(100):
            lon = center_lon + np.random.uniform(-0.01, 0.01)
            lat = center_lat + np.random.uniform(-0.01, 0.01)
            size = 0.0001  # 約10m四方
            
            poly = Polygon([
                (lon, lat),
                (lon + size, lat),
                (lon + size, lat + size),
                (lon, lat + size)
            ])
            
            buildings.append({
                'geometry': poly,
                'height': np.random.uniform(5, 50),
                'ground_height': np.random.uniform(0, 5)
            })
        
        self.buildings = gpd.GeoDataFrame(buildings)
        self.buildings.set_crs('EPSG:4326', inplace=True)
        self.bounds = self.buildings.total_bounds
        
        print(f"  生成建物数: {len(self.buildings)}")
        print(f"  エリア: {self.city}（仮想データ）")
        
        return self.buildings

'''
    content = content.replace(class_end, new_method + class_end)
    
    # load_buildingsメソッドを修正
    old_raise = 'raise FileNotFoundError(f"建物データが見つかりません: {self.data_dir}")'
    new_return = '''print(f"警告: 建物データが見つかりません。仮想データを生成します。")
                return self._create_virtual_buildings()'''
    content = content.replace(old_raise, new_return)
    
    # ファイルを保存
    with open('src/simulator.py', 'w') as f:
        f.write(content)
    
    print("✅ パッチ適用完了！")
else:
    print("✅ すでにパッチ適用済みです。")