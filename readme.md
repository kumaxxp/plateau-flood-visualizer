# 🌊 PLATEAU Flood Visualizer

PLATEAUの3D都市データを使用した水没シミュレーション＆終末世界ビジュアライザー

![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![PLATEAU](https://img.shields.io/badge/PLATEAU-対応-orange)

## 📝 概要

国土交通省の[Project PLATEAU](https://www.mlit.go.jp/plateau/)が提供する3D都市データを活用し、指定した水位での浸水シミュレーションを実行。さらに、ローカルAI（Stable Diffusion等）と連携して終末世界のビジュアルを生成するツールです。

## ✨ 主な機能

- 🏢 **PLATEAUデータの読み込み**: CityGML, GeoPackage, GeoJSON対応
- 💧 **浸水シミュレーション**: 任意の水位での建物影響を計算
- 🗺️ **多様な可視化**:
  - Foliumによる2Dマップ
  - PyDeckによる3D表示
  - Plotlyによるインタラクティブチャート
- 🎨 **AI画像生成**: Stable Diffusion連携で終末世界を生成
- 🌐 **WebUI**: ブラウザから簡単操作
- 📊 **バッチ処理**: 複数水位での一括シミュレーション

## 🚀 クイックスタート

### 必要環境

- Ubuntu 24.04 / Windows 10+ / macOS
- Python 3.11+
- NVIDIA GPU (推奨: RTX 3060以上、A5000等)
- 16GB+ RAM
- Conda (Anaconda/Miniconda)

### インストール

```bash
# 1. リポジトリをクローン
git clone https://github.com/YOUR_USERNAME/plateau-flood-visualizer.git
cd plateau-flood-visualizer

# 2. Conda環境を作成
conda env create -f environment.yml
conda activate plateau_env

# 3. プロジェクトセットアップ
python setup.py

# 4. 環境確認
python test_environment.py
```

### データの準備

1. [G空間情報センター](https://www.geospatial.jp/ckan/dataset/plateau)からPLATEAUデータをダウンロード
2. `data/plateau/`ディレクトリに配置

```bash
# データ構造例
data/
└── plateau/
    ├── tokyo_buildings.gpkg   # 建物データ
    ├── tokyo_dem.tif          # 標高データ
    └── tokyo_bldg.geojson     # 建物データ（GeoJSON形式）
```

## 📖 使い方

### CLI実行

```bash
# 基本的なシミュレーション
python src/main.py simulate tokyo --level 10.0

# 可視化付きシミュレーション
python src/main.py simulate tokyo --level 15.0 --viz

# AI画像生成も実行
python src/main.py simulate tokyo --level 10.0 --generate

# バッチ処理（複数水位）
python src/main.py batch tokyo --levels "5,10,15,20"

# システム情報確認
python src/main.py info
```

### WebUI起動

```bash
# WebUIサーバー起動
python src/main.py server --port 8000

# ブラウザで開く
# http://localhost:8000
```

### Jupyter Notebook

```bash
# Jupyter Lab起動
jupyter lab

# notebooks/example.ipynb を開いて実行
```

### Pythonスクリプトから使用

```python
from src.simulator import FloodSimulator
from src.visualizer import FloodVisualizer
from src.generator import ApocalypseGenerator

# シミュレーション実行
sim = FloodSimulator("tokyo")
sim.load_buildings()
sim.load_dem()
results = sim.simulate_flood(water_level=10.0)

# 可視化
viz = FloodVisualizer(sim)
viz.create_folium_map(sim.buildings, water_level=10.0, save_path="flood_map.html")
viz.create_pydeck_3d(sim.buildings, water_level=10.0, save_path="flood_3d.html")

# AI画像生成（要Stable Diffusion WebUI）
gen = ApocalypseGenerator()
gen.generate_flood_scene(results)
```

## 🎨 AI画像生成設定

### Stable Diffusion WebUI

```bash
# インストール
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui
cd stable-diffusion-webui

# API有効化して起動
./webui.sh --api --xformers --listen

# A5000等のGPUで高速化
./webui.sh --api --xformers --opt-sdp-attention
```

### ComfyUI（軽量版）

```bash
git clone https://github.com/comfyanonymous/ComfyUI
cd ComfyUI
pip install -r requirements.txt
python main.py --listen
```

## 📂 プロジェクト構造

```
plateau-flood-visualizer/
├── src/                    # ソースコード
│   ├── __init__.py
│   ├── simulator.py        # 浸水シミュレーション
│   ├── visualizer.py       # 可視化モジュール
│   ├── generator.py        # AI画像生成
│   ├── main.py            # CLIアプリケーション
│   └── web_app.py         # WebUIアプリケーション
├── data/                   # データディレクトリ
│   ├── plateau/           # PLATEAUデータ
│   └── dem/               # 標高データ
├── outputs/                # 出力結果
│   ├── maps/              # 生成マップ
│   ├── images/            # AI生成画像
│   └── data/              # エクスポートデータ
├── notebooks/              # Jupyter notebooks
├── static/                 # WebUI静的ファイル
├── environment.yml         # Conda環境定義
├── requirements.txt        # pip要件
├── setup.py               # セットアップスクリプト
├── test_environment.py     # 環境チェック
└── README.md              # このファイル
```

## 🔧 トラブルシューティング

### よくある問題

**Q: PLATEAUデータが読み込めない**
```bash
# GDALが正しくインストールされているか確認
python -c "from osgeo import gdal; print(gdal.__version__)"

# 再インストール
conda install -c conda-forge gdal
```

**Q: GPU が認識されない**
```bash
# CUDA確認
nvidia-smi

# PyTorchのGPU対応版をインストール
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**Q: WebUIにアクセスできない**
```bash
# ファイアウォール設定確認
sudo ufw allow 8000

# 全インターフェースでリッスン
python src/main.py server --host 0.0.0.0 --port 8000
```

## 🤝 Contributing

Pull requests 歓迎です！

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 🙏 謝辞

- [Project PLATEAU](https://www.mlit.go.jp/plateau/) - 国土交通省
- [Stable Diffusion](https://github.com/CompVis/stable-diffusion) - 画像生成AI
- すべてのオープンソース貢献者の皆様

## 📞 お問い合わせ

Issues や Discussions でお気軽にご質問ください。

---

**Note**: このツールは教育・研究目的で開発されています。実際の防災計画には専門的な評価が必要です。