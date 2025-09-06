# ========== setup.py ==========
#!/usr/bin/env python
"""
プロジェクトセットアップスクリプト
"""

import os
import sys
from pathlib import Path


def setup_project():
    """プロジェクト構造をセットアップ"""
    
    print("🏗️  Setting up PLATEAU Flood Visualizer project...")
    
    # プロジェクトルート
    project_root = Path(__file__).parent
    
    # 必要なディレクトリを作成
    directories = [
        'data',
        'data/plateau',
        'data/dem',
        'outputs',
        'outputs/maps',
        'outputs/images',
        'outputs/data',
        'models',
        'static',
        'static/outputs',
        'notebooks',
        'src',
    ]
    
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ Created: {dir_path}")
    
    # __init__.pyを作成
    init_file = project_root / 'src' / '__init__.py'
    if not init_file.exists():
        init_file.write_text('"""PLATEAU Flood Visualizer Package"""')
        print(f"  ✅ Created: src/__init__.py")
    
    # サンプルノートブックを作成
    notebook_path = project_root / 'notebooks' / 'example.ipynb'
    if not notebook_path.exists():
        notebook_content = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": ["# PLATEAU Flood Visualization Example\n", "水没シミュレーションの実行例"]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "import sys\n",
                        "sys.path.append('../src')\n",
                        "\n",
                        "from simulator import FloodSimulator\n",
                        "from visualizer import FloodVisualizer\n",
                        "from generator import MockGenerator"
                    ]
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
        
        import json
        with open(notebook_path, 'w') as f:
            json.dump(notebook_content, f, indent=2)
        print(f"  ✅ Created: notebooks/example.ipynb")
    
    print("\n✅ Project setup complete!")
    print(f"📁 Project root: {project_root}")
    
    # 環境チェック
    print("\nRunning environment check...")
    from test_environment import check_environment
    check_environment()


if __name__ == "__main__":
    setup_project()