# fix_import_error.py として保存
"""PyDeckのインポートエラーを修正"""

# visualizer.pyを修正
with open('src/visualizer.py', 'r') as f:
    content = f.read()

# 問題のあるインポートを削除
content = content.replace('import pydeck.map_styles', '')

# map_styleの参照も修正
content = content.replace('pdk.map_styles.LIGHT', "'light'")
content = content.replace('pdk.map_styles.DARK', "'dark'")
content = content.replace('pdk.map_styles.ROAD', "'road'")
content = content.replace('pdk.map_styles.SATELLITE', "'satellite'")

# ファイルを保存
with open('src/visualizer.py', 'w') as f:
    f.write(content)

print("✅ インポートエラーを修正しました")