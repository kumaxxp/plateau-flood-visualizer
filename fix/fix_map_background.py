# fix_map_background.py として保存
"""3Dマップの背景地図を修正"""

import sys
sys.path.append('.')

# visualizer.pyを修正
with open('src/visualizer.py', 'r') as f:
    content = f.read()

# map_styleの行を見つけて修正
old_style = "map_style='mapbox://styles/mapbox/dark-v10'"
new_style = "map_style=pdk.map_styles.LIGHT"  # PyDeckの組み込みスタイル

if old_style in content:
    content = content.replace(old_style, new_style)
    print("✅ map_styleを修正しました")

# 別の方法：map_styleを完全に削除（OpenStreetMapがデフォルト）
# または以下のスタイルを使用
alternative_styles = """
            # 以下のいずれかを使用可能：
            # map_style=None,  # デフォルト（OpenStreetMap）
            # map_style=pdk.map_styles.LIGHT,
            # map_style=pdk.map_styles.DARK,
            # map_style=pdk.map_styles.ROAD,
            # map_style=pdk.map_styles.SATELLITE,
"""

# ViewStateの設定も調整
view_state_fix = """        # ビューの設定（より良い角度）
        bounds = buildings.total_bounds
        view_state = pdk.ViewState(
            latitude=(bounds[1] + bounds[3]) / 2,
            longitude=(bounds[0] + bounds[2]) / 2,
            zoom=14,  # ズームレベルを調整
            pitch=45,  # 45度の角度
            bearing=0,  # 北向き
            height=600  # ビューの高さ
        )"""

# import文も確認
if "import pydeck.map_styles" not in content:
    import_line = "import pydeck as pdk"
    content = content.replace(import_line, "import pydeck as pdk\nimport pydeck.map_styles")

# ファイルを保存
with open('src/visualizer.py', 'w') as f:
    f.write(content)

print("✅ 地図背景の設定を修正しました")
print("\n次のステップ:")
print("1. WebUIを再起動")
print("2. ブラウザのキャッシュをクリア（Ctrl+Shift+R）")