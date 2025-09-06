"""
PLATEAU データ可視化モジュール
"""

import folium
import pydeck as pdk
import plotly.graph_objects as go
import geopandas as gpd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import json
import pandas as pd


class FloodVisualizer:
    """浸水シミュレーション結果の可視化"""
    
    def __init__(self, simulator=None):
        """
        Args:
            simulator: FloodSimulatorインスタンス
        """
        self.simulator = simulator
        self.buildings = None
        self.flood_results = None
        
    def create_folium_map(self, 
                          buildings: gpd.GeoDataFrame,
                          water_level: float = 5.0,
                          save_path: Optional[Path] = None) -> folium.Map:
        """Foliumで2Dマップを作成
        
        Args:
            buildings: 建物データ
            water_level: 浸水水位
            save_path: 保存先パス
        
        Returns:
            Foliumマップオブジェクト
        """
        # マップの中心を計算
        bounds = buildings.total_bounds
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
        
        # マップを作成
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=14,
            tiles='CartoDB dark_matter'
        )
        
        # 浸水状態で色分け
        color_map = {
            'flooded': '#FF0000',    # 赤：完全水没
            'partial': '#FFA500',    # オレンジ：部分水没
            'safe': '#00FF00'        # 緑：安全
        }
        
        # 建物を追加
        for idx, building in buildings.iterrows():
            status = building.get('flood_status', 'safe')
            depth = building.get('flood_depth', 0)
            
            # ポップアップテキスト
            popup_text = f"""
            <b>建物情報</b><br>
            高さ: {building.get('height', 'N/A'):.1f}m<br>
            浸水状態: {status}<br>
            浸水深: {depth:.1f}m
            """
            
            # GeoJSONスタイル
            style = {
                'fillColor': color_map.get(status, '#808080'),
                'color': '#000000',
                'weight': 1,
                'fillOpacity': 0.7
            }
            
            # ジオメトリを追加
            folium.GeoJson(
                building.geometry.__geo_interface__,
                style_function=lambda x, style=style: style,
                popup=folium.Popup(popup_text, max_width=200)
            ).add_to(m)
        
        # 凡例を追加
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 200px; height: 120px; 
                    background-color: white; z-index:9999; font-size:14px;
                    border:2px solid grey; border-radius: 5px">
        <p style="margin: 10px;"><b>浸水状態 (水位: {:.1f}m)</b></p>
        <p style="margin: 10px;"><span style="color: #FF0000;">■</span> 完全水没</p>
        <p style="margin: 10px;"><span style="color: #FFA500;">■</span> 部分水没</p>
        <p style="margin: 10px;"><span style="color: #00FF00;">■</span> 安全</p>
        </div>
        '''.format(water_level)
        
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # 保存
        if save_path:
            m.save(str(save_path))
            print(f"マップを保存しました: {save_path}")
        
        return m
    
    def create_pydeck_3d(self,
                         buildings: gpd.GeoDataFrame,
                         water_level: float = 5.0,
                         save_path: Optional[Path] = None) -> pdk.Deck:
        """PyDeckで3D可視化
        
        Args:
            buildings: 建物データ
            water_level: 浸水水位
            save_path: 保存先パス
        
        Returns:
            PyDeckオブジェクト
        """
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
            
            # 色を設定
            if status == 'flooded':
                color = [255, 0, 0, 180]  # 赤
            elif status == 'partial':
                color = [255, 165, 0, 180]  # オレンジ
            else:
                color = [0, 255, 0, 180]  # 緑
            
            data.append({
                'polygon': coords,
                'height': height,
                'flood_depth': depth,
                'color': color,
                'status': status
            })
        
        # ビューの設定
        bounds = buildings.total_bounds
        view_state = pdk.ViewState(
            latitude=(bounds[1] + bounds[3]) / 2,
            longitude=(bounds[0] + bounds[2]) / 2,
            zoom=14,
            pitch=45,
            bearing=0
        )
        
        # レイヤーを作成
        polygon_layer = pdk.Layer(
            'PolygonLayer',
            data=data,
            get_polygon='polygon',
            get_elevation='height * 10',  # 高さを強調
            get_fill_color='color',
            get_line_color=[255, 255, 255],
            line_width_min_pixels=1,
            extruded=True,
            wireframe=True,
            pickable=True
        )
        
        # 水面レイヤー（オプション）
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
                'elevation': water_level * 10
            }],
            get_polygon='polygon',
            get_elevation='elevation',
            get_fill_color=[0, 100, 255, 50],
            extruded=False,
            pickable=False
        )
        
        # デッキを作成
        deck = pdk.Deck(
            layers=[polygon_layer, water_layer],
            initial_view_state=view_state,
            tooltip={
                'text': '状態: {status}\n高さ: {height}m\n浸水深: {flood_depth}m'
            }
        )
        
        # HTMLとして保存
        if save_path:
            deck.to_html(str(save_path))
            print(f"3Dマップを保存しました: {save_path}")
        
        return deck
    
    def create_plotly_3d(self,
                        buildings: gpd.GeoDataFrame,
                        water_level: float = 5.0,
                        save_path: Optional[Path] = None) -> go.Figure:
        """Plotlyで3D可視化
        
        Args:
            buildings: 建物データ
            water_level: 浸水水位
            save_path: 保存先パス
        
        Returns:
            Plotly Figureオブジェクト
        """
        fig = go.Figure()
        
        # 色マップ
        color_map = {
            'flooded': 'red',
            'partial': 'orange',
            'safe': 'green'
        }
        
        # 建物ごとにトレースを追加
        for status in ['flooded', 'partial', 'safe']:
            status_buildings = buildings[buildings['flood_status'] == status]
            
            if len(status_buildings) == 0:
                continue
            
            x_coords = []
            y_coords = []
            z_coords = []
            
            for idx, building in status_buildings.iterrows():
                if building.geometry.geom_type == 'Polygon':
                    # ポリゴンの頂点を取得
                    coords = list(building.geometry.exterior.coords)
                    height = building.get('height', 10)
                    
                    # 底面と上面の座標を作成
                    for coord in coords:
                        x_coords.extend([coord[0], coord[0], None])
                        y_coords.extend([coord[1], coord[1], None])
                        z_coords.extend([0, height, None])
            
            # トレースを追加
            fig.add_trace(go.Scatter3d(
                x=x_coords,
                y=y_coords,
                z=z_coords,
                mode='lines',
                name=status,
                line=dict(color=color_map[status], width=2),
                hovertemplate='%{text}',
                text=[status] * len(x_coords)
            ))
        
        # 水面を追加
        bounds = buildings.total_bounds
        water_x = [bounds[0], bounds[2], bounds[2], bounds[0], bounds[0]]
        water_y = [bounds[1], bounds[1], bounds[3], bounds[3], bounds[1]]
        water_z = [water_level] * 5
        
        fig.add_trace(go.Scatter3d(
            x=water_x,
            y=water_y,
            z=water_z,
            mode='lines',
            name=f'水位 ({water_level}m)',
            line=dict(color='blue', width=3),
            fill='toself',
            surfacecolor='lightblue',
            opacity=0.3
        ))
        
        # レイアウト設定
        fig.update_layout(
            title=f'浸水シミュレーション (水位: {water_level}m)',
            scene=dict(
                xaxis_title='経度',
                yaxis_title='緯度',
                zaxis_title='高さ (m)',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            showlegend=True,
            height=700
        )
        
        # 保存
        if save_path:
            fig.write_html(str(save_path))
            print(f"Plotly 3Dビューを保存しました: {save_path}")
        
        return fig
    
    def create_statistics_chart(self,
                               results: Dict,
                               save_path: Optional[Path] = None) -> go.Figure:
        """統計情報のチャートを作成
        
        Args:
            results: シミュレーション結果
            save_path: 保存先パス
        
        Returns:
            Plotly Figureオブジェクト
        """
        # データを準備
        categories = ['完全水没', '部分水没', '安全']
        values = [
            results['flooded_buildings'],
            results['partially_flooded'],
            results['safe_buildings']
        ]
        colors = ['red', 'orange', 'green']
        
        # 円グラフを作成
        fig = go.Figure(data=[
            go.Pie(
                labels=categories,
                values=values,
                marker=dict(colors=colors),
                textinfo='label+percent',
                hole=0.3
            )
        ])
        
        # タイトルと注釈
        fig.update_layout(
            title=f"浸水状況分布 (水位: {results['water_level']}m)",
            annotations=[
                dict(
                    text=f"総建物数<br>{results['total_buildings']:,}",
                    x=0.5, y=0.5,
                    font_size=20,
                    showarrow=False
                )
            ]
        )
        
        # 保存
        if save_path:
            fig.write_html(str(save_path))
            print(f"統計チャートを保存しました: {save_path}")
        
        return fig
    
    def create_water_level_comparison(self,
                                     water_levels: List[float],
                                     simulator=None) -> go.Figure:
        """複数の水位での影響を比較
        
        Args:
            water_levels: 比較する水位のリスト
            simulator: FloodSimulatorインスタンス
        
        Returns:
            Plotly Figureオブジェクト
        """
        if simulator is None:
            simulator = self.simulator
        
        if simulator is None:
            raise ValueError("Simulatorが必要です")
        
        # 各水位でシミュレーション
        affected_counts = []
        flooded_counts = []
        
        for level in water_levels:
            results = simulator.simulate_flood(level)
            affected_counts.append(
                results['flooded_buildings'] + results['partially_flooded']
            )
            flooded_counts.append(results['flooded_buildings'])
        
        # グラフを作成
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=water_levels,
            y=affected_counts,
            mode='lines+markers',
            name='影響建物（部分＋完全）',
            line=dict(color='orange', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=water_levels,
            y=flooded_counts,
            mode='lines+markers',
            name='完全水没建物',
            line=dict(color='red', width=2)
        ))
        
        fig.update_layout(
            title='水位による影響建物数の変化',
            xaxis_title='水位 (m)',
            yaxis_title='建物数',
            hovermode='x unified'
        )
        
        return fig


if __name__ == "__main__":
    # テスト実行
    from simulator import FloodSimulator
    
    # シミュレータを初期化
    sim = FloodSimulator("tokyo")
    
    try:
        sim.load_buildings()
        results = sim.simulate_flood(water_level=10.0)
        
        # 可視化
        viz = FloodVisualizer(sim)
        
        # 出力ディレクトリ作成
        output_dir = Path("outputs/maps")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 2Dマップ
        folium_map = viz.create_folium_map(
            sim.buildings,
            water_level=10.0,
            save_path=output_dir / "flood_map_2d.html"
        )
        
        # 3Dマップ
        pydeck_map = viz.create_pydeck_3d(
            sim.buildings,
            water_level=10.0,
            save_path=output_dir / "flood_map_3d.html"
        )
        
        # 統計チャート
        stats_chart = viz.create_statistics_chart(
            results,
            save_path=output_dir / "flood_statistics.html"
        )
        
        print("\n全ての可視化が完了しました！")
        
    except Exception as e:
        print(f"エラー: {e}")