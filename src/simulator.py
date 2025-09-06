"""
PLATEAU 浸水シミュレーションモジュール
"""

import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from shapely.geometry import Point, Polygon, box
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import json
from tqdm import tqdm


class FloodSimulator:
    """PLATEAUデータを使用した浸水シミュレーション"""
    
    def __init__(self, city: str = "tokyo", data_dir: Optional[Path] = None):
        """
        Args:
            city: 都市名 ('tokyo' or 'nagoya')
            data_dir: データディレクトリのパス
        """
        self.city = city
        self.data_dir = Path(data_dir) if data_dir else Path("data/plateau")
        self.buildings = None
        self.dem = None
        self.bounds = None
        
    def load_buildings(self, filepath: Optional[Path] = None) -> gpd.GeoDataFrame:
        """建物データの読み込み
        
        Args:
            filepath: 建物データファイルパス（GeoPackage, GeoJSON, Shapefile対応）
        
        Returns:
            建物のGeoDataFrame
        """
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
                raise FileNotFoundError(f"建物データが見つかりません: {self.data_dir}")
        
        print(f"建物データ読み込み中: {filepath}")
        self.buildings = gpd.read_file(filepath)
        
        # 必要な列を確認・追加
        if 'height' not in self.buildings.columns:
            # 階数から高さを推定（1階あたり3.5m）
            if 'storeys' in self.buildings.columns:
                self.buildings['height'] = self.buildings['storeys'] * 3.5
            else:
                self.buildings['height'] = 10.0  # デフォルト高さ
        
        if 'ground_height' not in self.buildings.columns:
            self.buildings['ground_height'] = 0.0
        
        # 座標系を確認
        if self.buildings.crs is None:
            self.buildings.set_crs('EPSG:4326', inplace=True)
        
        self.bounds = self.buildings.total_bounds
        print(f"  建物数: {len(self.buildings):,}")
        print(f"  範囲: {self.bounds}")
        
        return self.buildings
    
    def load_dem(self, filepath: Optional[Path] = None) -> np.ndarray:
        """標高データ（DEM）の読み込み
        
        Args:
            filepath: DEMファイルパス（GeoTIFF）
        
        Returns:
            標高データの配列
        """
        if filepath is None:
            filepath = self.data_dir / f"{self.city}_dem.tif"
        
        if not filepath.exists():
            print(f"警告: DEMファイルが見つかりません。仮想DEMを生成します。")
            return self._create_virtual_dem()
        
        print(f"DEM読み込み中: {filepath}")
        with rasterio.open(filepath) as src:
            self.dem = src.read(1)
            self.dem_transform = src.transform
            self.dem_crs = src.crs
        
        print(f"  DEM形状: {self.dem.shape}")
        print(f"  標高範囲: {self.dem.min():.1f}m - {self.dem.max():.1f}m")
        
        return self.dem
    
    def _create_virtual_dem(self) -> np.ndarray:
        """仮想的なDEMデータを生成（テスト用）"""
        if self.buildings is None:
            raise ValueError("先に建物データを読み込んでください")
        
        # 建物の範囲から仮想DEMを作成
        minx, miny, maxx, maxy = self.bounds
        resolution = 0.0001  # 約10m
        
        width = int((maxx - minx) / resolution)
        height = int((maxy - miny) / resolution)
        
        # ランダムな地形を生成（川を模擬）
        np.random.seed(42)
        dem = np.random.randn(height, width) * 2 + 5  # 平均5m
        
        # スムージング
        from scipy.ndimage import gaussian_filter
        dem = gaussian_filter(dem, sigma=5)
        
        self.dem = dem
        self.dem_transform = rasterio.transform.from_bounds(
            minx, miny, maxx, maxy, width, height
        )
        self.dem_crs = 'EPSG:4326'
        
        return dem
    
    def simulate_flood(self, water_level: float = 5.0) -> Dict:
        """指定水位での浸水シミュレーション
        
        Args:
            water_level: 浸水水位（メートル）
        
        Returns:
            シミュレーション結果の辞書
        """
        if self.buildings is None:
            self.load_buildings()
        
        if self.dem is None:
            self.load_dem()
        
        print(f"\n浸水シミュレーション実行中（水位: {water_level}m）...")
        
        # 建物ごとの浸水判定
        flooded_buildings = []
        partially_flooded = []
        safe_buildings = []
        
        for idx, building in tqdm(self.buildings.iterrows(), 
                                 total=len(self.buildings),
                                 desc="建物を評価中"):
            ground_height = building.get('ground_height', 0)
            building_height = building.get('height', 10)
            
            # 浸水深さを計算
            flood_depth = water_level - ground_height
            
            if flood_depth > building_height:
                # 完全水没
                flooded_buildings.append(idx)
            elif flood_depth > 0:
                # 部分水没
                partially_flooded.append(idx)
            else:
                # 安全
                safe_buildings.append(idx)
        
        # 結果をGeoDataFrameに追加
        self.buildings['flood_status'] = 'safe'
        self.buildings.loc[flooded_buildings, 'flood_status'] = 'flooded'
        self.buildings.loc[partially_flooded, 'flood_status'] = 'partial'
        
        self.buildings['flood_depth'] = np.maximum(
            0, water_level - self.buildings['ground_height']
        )
        
        # 統計情報を計算
        results = {
            'water_level': water_level,
            'total_buildings': len(self.buildings),
            'flooded_buildings': len(flooded_buildings),
            'partially_flooded': len(partially_flooded),
            'safe_buildings': len(safe_buildings),
            'flooded_percentage': len(flooded_buildings) / len(self.buildings) * 100,
            'affected_percentage': (len(flooded_buildings) + len(partially_flooded)) / len(self.buildings) * 100,
            'max_flood_depth': self.buildings['flood_depth'].max(),
            'mean_flood_depth': self.buildings[self.buildings['flood_depth'] > 0]['flood_depth'].mean()
        }
        
        print(f"\n=== シミュレーション結果 ===")
        print(f"水位: {water_level}m")
        print(f"完全水没: {results['flooded_buildings']:,}棟 ({results['flooded_percentage']:.1f}%)")
        print(f"部分水没: {results['partially_flooded']:,}棟")
        print(f"影響建物: {results['affected_percentage']:.1f}%")
        print(f"最大浸水深: {results['max_flood_depth']:.1f}m")
        
        return results
    
    def get_affected_areas(self, water_level: float = 5.0) -> gpd.GeoDataFrame:
        """浸水エリアのポリゴンを生成
        
        Args:
            water_level: 浸水水位
        
        Returns:
            浸水エリアのGeoDataFrame
        """
        if self.buildings is None or 'flood_status' not in self.buildings.columns:
            self.simulate_flood(water_level)
        
        # 浸水建物を選択
        affected = self.buildings[
            self.buildings['flood_status'].isin(['flooded', 'partial'])
        ]
        
        if len(affected) == 0:
            return gpd.GeoDataFrame()
        
        # 建物を結合してバッファを作成（浸水エリアを表現）
        affected_union = affected.geometry.buffer(0.0001).unary_union
        
        # 結果をGeoDataFrameに変換
        flood_areas = gpd.GeoDataFrame(
            [{'water_level': water_level, 'geometry': affected_union}],
            crs=self.buildings.crs
        )
        
        return flood_areas
    
    def export_results(self, water_level: float, output_dir: Path = Path("outputs")):
        """シミュレーション結果をエクスポート
        
        Args:
            water_level: 浸水水位
            output_dir: 出力ディレクトリ
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # GeoJSONとして保存
        output_file = output_dir / f"flood_simulation_{self.city}_{water_level}m.geojson"
        
        if 'flood_status' not in self.buildings.columns:
            self.simulate_flood(water_level)
        
        # エクスポート用のデータを準備
        export_data = self.buildings[['geometry', 'height', 'flood_status', 'flood_depth']].copy()
        export_data.to_file(output_file, driver='GeoJSON')
        
        print(f"結果を保存しました: {output_file}")
        
        # 統計情報もJSONで保存
        stats_file = output_dir / f"flood_stats_{self.city}_{water_level}m.json"
        stats = self.simulate_flood(water_level)
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"統計情報を保存しました: {stats_file}")
        
        return output_file, stats_file


if __name__ == "__main__":
    # テスト実行
    simulator = FloodSimulator("tokyo")
    
    # データ読み込み
    try:
        simulator.load_buildings()
        simulator.load_dem()
    except FileNotFoundError as e:
        print(f"エラー: {e}")
        print("サンプルデータで実行します")
    
    # シミュレーション実行
    results = simulator.simulate_flood(water_level=10.0)
    
    # 結果をエクスポート
    simulator.export_results(water_level=10.0)