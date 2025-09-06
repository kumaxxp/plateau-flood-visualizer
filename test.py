# 基本的なプロジェクトファイルを作成
touch src/__init__.py
touch src/simulator.py
touch src/generator.py
touch src/visualizer.py
touch src/main.py

# サンプルノートブック
cat > notebooks/example.ipynb << 'EOF'
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": ["# PLATEAU Flood Visualization\n", "水没シミュレーションの実行例"]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "plateau_env",
   "language": "python",
   "name": "plateau_env"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
