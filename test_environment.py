# ========== test_environment.py ==========
#!/usr/bin/env python
"""
環境の動作確認スクリプト
"""

import sys
import importlib
from pathlib import Path


def check_package(name, import_name=None):
    """パッケージのインポート確認"""
    if import_name is None:
        import_name = name
    
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"  ✅ {name:20} {version}")
        return True
    except ImportError:
        print(f"  ❌ {name:20} not installed")
        return False


def check_environment():
    """環境チェック"""
    print("=" * 50)
    print("PLATEAU Environment Check")
    print("=" * 50)
    
    print(f"\n📍 Python Version: {sys.version}")
    print(f"📍 Python Path: {sys.executable}")
    
    print("\n📦 Core Packages:")
    core_packages = [
        ('geopandas', 'geopandas'),
        ('rasterio', 'rasterio'),
        ('folium', 'folium'),
        ('pydeck', 'pydeck'),
        ('plotly', 'plotly'),
        ('fastapi', 'fastapi'),
        ('typer', 'typer'),
        ('rich', 'rich'),
    ]
    
    all_ok = True
    for name, import_name in core_packages:
        if not check_package(name, import_name):
            all_ok = False
    
    print("\n📦 Optional Packages:")
    optional_packages = [
        ('py3dtiles', 'py3dtiles'),
        ('laspy', 'laspy'),
        ('open3d', 'open3d'),
        ('torch', 'torch'),
    ]
    
    for name, import_name in optional_packages:
        check_package(name, import_name)
    
    # GDAL確認
    print("\n🌍 GDAL Check:")
    try:
        from osgeo import gdal
        print(f"  ✅ GDAL version: {gdal.__version__}")
    except ImportError:
        print(f"  ❌ GDAL not available")
        all_ok = False
    
    # GPU確認
    print("\n🎮 GPU Check:")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"  ✅ GPU: {torch.cuda.get_device_name(0)}")
            print(f"  ✅ CUDA: {torch.version.cuda}")
        else:
            print("  ⚠️  GPU not available (CPU mode)")
    except ImportError:
        print("  ℹ️  PyTorch not installed (optional)")
    
    # ディレクトリ確認
    print("\n📁 Directory Structure:")
    dirs = ['data', 'data/plateau', 'outputs', 'src', 'notebooks']
    for dir_name in dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"  ✅ {dir_name:20} exists")
        else:
            print(f"  ⚠️  {dir_name:20} not found (will be created)")
            dir_path.mkdir(parents=True, exist_ok=True)
    
    # 結果
    print("\n" + "=" * 50)
    if all_ok:
        print("✅ Environment is ready!")
    else:
        print("⚠️  Some packages are missing. Run:")
        print("   conda env create -f environment.yml")
        print("   conda activate plateau_env")
    print("=" * 50)
    
    return all_ok


if __name__ == "__main__":
    check_environment()
