# fix_3d_buildings.py として保存
"""3D建物表示を改善するパッチ"""

import sys
sys.path.append('.')

# visualizer.pyを読み込む
with open('src/visualizer.py', 'r') as f:
    content = f.read()

# create_pydeck_3dメソッドを改善版に置き換え
improved_method = '''    def create_pydeck_3d(self,
                         buildings: gpd.GeoDataFrame,
                         water_level: float = 5.0,
                         save_path: Optional[Path] = None) -> pdk.Deck:
        """PyDeckで3D可視化（改善版）"""
        # 座標系を変換（必要に応じて）
        if buildings.crs and buildings.crs != 'EPSG:4326':
            buildings = buildings.to_crs('EPSG:4326')
        
        # データを準備
        data = []
        for idx, building in buildings.iterrows():
            # ポリゴンの座標を取得
            if building.geometry.geom_type == 'Polygon':
                coords = list(building.geometry.exterior.coords)
            else:
                continue
            
            status = building.get('flood_status', 'safe')
            height = building.get('height', 10)
            depth = building.get('flood_depth', 0)
            
            # 色を設定（透明度を調整）
            if status == 'flooded':
                color = [255, 50, 50, 200]  # 赤（より鮮明に）
            elif status == 'partial':
                color = [255, 165, 0, 200]  # オレンジ
            else:
                color = [50, 255, 50, 200]  # 緑
            
            data.append({
                'polygon': coords,
                'height': height,
                'flood_depth': depth,
                'color': color,
                'status': status,
                'line_color': [255, 255, 255, 100]  # 白い輪郭線
            })
        
        # ビューの設定（より良い角度）
        bounds = buildings.total_bounds
        view_state = pdk.ViewState(
            latitude=(bounds[1] + bounds[3]) / 2,
            longitude=(bounds[0] + bounds[2]) / 2,
            zoom=15,  # ズームレベルを上げる
            pitch=60,  # より急な角度で立体感を強調
            bearing=45  # 45度回転
        )
        
        # 建物レイヤー（立体表示）
        building_layer = pdk.Layer(
            'PolygonLayer',
            data=data,
            get_polygon='polygon',
            get_elevation='height * 20',  # 高さを20倍に強調
            get_fill_color='color',
            get_line_color='line_color',
            line_width_min_pixels=1,
            extruded=True,  # 立体化
            wireframe=False,  # ワイヤーフレームをオフ
            pickable=True,
            auto_highlight=True,
            elevation_scale=1
        )
        
        # 水面レイヤー（半透明の青）
        water_bounds = [
            [bounds[0], bounds[1]],
            [bounds[2], bounds[1]],
            [bounds[2], bounds[3]],
            [bounds[0], bounds[3]]
        ]
        
        water_layer = pdk.Layer(
            'PolygonLayer',
            data=[{
                'polygon': water_bounds,
                'elevation': water_level
            }],
            get_polygon='polygon',
            get_elevation='elevation * 20',  # 水位も同じスケールで
            get_fill_color=[100, 150, 255, 80],  # 半透明の青
            extruded=False,
            pickable=False
        )
        
        # 浸水した建物の水面下部分を表示（オプション）
        flooded_bases = []
        for idx, building in buildings[buildings['flood_status'].isin(['flooded', 'partial'])].iterrows():
            if building.geometry.geom_type == 'Polygon':
                coords = list(building.geometry.exterior.coords)
                flooded_bases.append({
                    'polygon': coords,
                    'height': min(building.get('flood_depth', 0), building.get('height', 10))
                })
        
        flood_layer = pdk.Layer(
            'PolygonLayer',
            data=flooded_bases,
            get_polygon='polygon',
            get_elevation='height * 20',
            get_fill_color=[50, 100, 200, 120],  # 水色で浸水部分
            extruded=True,
            pickable=False
        ) if flooded_bases else None
        
        # レイヤーリスト
        layers = [building_layer, water_layer]
        if flood_layer:
            layers.append(flood_layer)
        
        # デッキを作成
        deck = pdk.Deck(
            layers=layers,
            initial_view_state=view_state,
            tooltip={
                'html': '<b>建物情報</b><br/>状態: {status}<br/>高さ: {height:.1f}m<br/>浸水深: {flood_depth:.1f}m',
                'style': {
                    'backgroundColor': 'steelblue',
                    'color': 'white'
                }
            },
            map_style='mapbox://styles/mapbox/dark-v10'  # ダークテーマ
        )
        
        # HTMLとして保存
        if save_path:
            deck.to_html(str(save_path))
            print(f"3Dマップを保存しました: {save_path}")
        
        return deck'''

# メソッドを置き換え
import re
pattern = r'def create_pydeck_3d\(self,.*?return deck'
match = re.search(pattern, content, re.DOTALL)

if match:
    content = content[:match.start()] + improved_method + content[match.end():]
    
    # ファイルを保存
    with open('src/visualizer.py', 'w') as f:
        f.write(content)
    
    print("✅ 3D表示を改善しました！")
else:
    print("⚠️ メソッドが見つかりません。手動で修正してください。")

print("\n次のステップ:")
print("1. WebUIを再起動: python src/main.py server --port 8000")
print("2. ブラウザをリロード")
print("3. シミュレーションを再実行")