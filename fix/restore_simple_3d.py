# restore_simple_3d.py として保存
"""確実に動作する最小限の3Dマップに戻す"""

minimal_3d = '''    def create_pydeck_3d(self,
                         buildings: gpd.GeoDataFrame,
                         water_level: float = 5.0,
                         save_path: Optional[Path] = None) -> pdk.Deck:
        """PyDeckで3D可視化（最小限版）"""
        if buildings.crs and buildings.crs != 'EPSG:4326':
            buildings = buildings.to_crs('EPSG:4326')
        
        # シンプルなデータ構造
        data = []
        for idx, building in buildings.iterrows():
            if building.geometry.geom_type == 'Polygon':
                coords = list(building.geometry.exterior.coords)
                status = building.get('flood_status', 'safe')
                
                # 基本的な色設定
                if status == 'flooded':
                    color = [255, 0, 0]
                elif status == 'partial':
                    color = [255, 165, 0]
                else:
                    color = [0, 255, 0]
                
                data.append({
                    'polygon': coords,
                    'height': float(building.get('height', 10)),
                    'color': color
                })
        
        bounds = buildings.total_bounds
        
        # 最小限のレイヤー設定
        layer = pdk.Layer(
            'PolygonLayer',
            data,
            get_polygon='polygon',
            get_elevation='height',
            get_fill_color='color',
            extruded=True
        )
        
        # 最小限のビュー設定
        view = pdk.ViewState(
            latitude=float((bounds[1] + bounds[3]) / 2),
            longitude=float((bounds[0] + bounds[2]) / 2),
            zoom=13,
            pitch=45
        )
        
        # 最小限のデッキ設定
        deck = pdk.Deck(
            layers=[layer],
            initial_view_state=view
        )
        
        if save_path:
            deck.to_html(str(save_path))
            print(f"3Dマップを保存しました: {save_path}")
        
        return deck
'''

with open('src/visualizer.py', 'r') as f:
    content = f.read()

import re
pattern = r'def create_pydeck_3d\(self,.*?return deck'
match = re.search(pattern, content, re.DOTALL)

if match:
    content = content[:match.start()] + minimal_3d + content[match.end():]
    with open('src/visualizer.py', 'w') as f:
        f.write(content)
    print("✅ 最小限の3Dマップに戻しました")