"""
PLATEAU Flood Visualizer メインプログラム
"""

import typer
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.progress import track
import json

from simulator import FloodSimulator
from visualizer import FloodVisualizer
from generator import ApocalypseGenerator, MockGenerator

# Typer CLIアプリ
app = typer.Typer(help="PLATEAU浸水シミュレーション＆終末世界ビジュアライザー")
console = Console()


@app.command()
def simulate(
    city: str = typer.Argument("tokyo", help="都市名 (tokyo/nagoya)"),
    water_level: float = typer.Option(10.0, "--level", "-l", help="浸水水位(m)"),
    data_dir: Path = typer.Option("data/plateau", "--data", "-d", help="データディレクトリ"),
    output_dir: Path = typer.Option("outputs", "--output", "-o", help="出力ディレクトリ"),
    visualize: bool = typer.Option(True, "--viz/--no-viz", help="可視化を実行"),
    generate: bool = typer.Option(False, "--generate", "-g", help="AI画像生成を実行")
):
    """浸水シミュレーションを実行"""
    
    console.print(f"\n[bold blue]🌊 PLATEAU 浸水シミュレーション[/bold blue]")
    console.print(f"都市: {city}")
    console.print(f"水位: {water_level}m\n")
    
    # シミュレータ初期化
    with console.status("[bold green]シミュレータを初期化中..."):
        sim = FloodSimulator(city, data_dir)
    
    # データ読み込み
    try:
        with console.status("[bold green]建物データを読み込み中..."):
            sim.load_buildings()
        
        with console.status("[bold green]標高データを読み込み中..."):
            sim.load_dem()
            
    except FileNotFoundError as e:
        console.print(f"[bold red]エラー: {e}[/bold red]")
        console.print("[yellow]サンプルデータで実行します[/yellow]")
    
    # シミュレーション実行
    console.print("\n[bold]シミュレーション実行中...[/bold]")
    results = sim.simulate_flood(water_level)
    
    # 結果を表示
    display_results(results)
    
    # 結果を保存
    sim.export_results(water_level, output_dir)
    
    # 可視化
    if visualize:
        console.print("\n[bold blue]📊 可視化処理[/bold blue]")
        viz = FloodVisualizer(sim)
        
        output_maps = output_dir / "maps"
        output_maps.mkdir(parents=True, exist_ok=True)
        
        # 2Dマップ
        with console.status("[bold green]2Dマップを生成中..."):
            viz.create_folium_map(
                sim.buildings,
                water_level,
                save_path=output_maps / f"flood_map_2d_{water_level}m.html"
            )
        
        # 3Dマップ
        with console.status("[bold green]3Dマップを生成中..."):
            viz.create_pydeck_3d(
                sim.buildings,
                water_level,
                save_path=output_maps / f"flood_map_3d_{water_level}m.html"
            )
        
        # 統計チャート
        with console.status("[bold green]統計チャートを生成中..."):
            viz.create_statistics_chart(
                results,
                save_path=output_maps / f"flood_stats_{water_level}m.html"
            )
        
        console.print("[bold green]✅ 可視化完了！[/bold green]")
    
    # AI画像生成
    if generate:
        console.print("\n[bold blue]🎨 AI画像生成[/bold blue]")
        
        # API接続を試みる
        gen = ApocalypseGenerator()
        if not gen.check_connection():
            console.print("[yellow]APIに接続できません。モックモードで実行します。[/yellow]")
            gen = MockGenerator()
        
        output_images = output_dir / "images"
        gen.generate_flood_scene(results, output_dir=output_images)
        
        console.print("[bold green]✅ 画像生成完了！[/bold green]")
    
    console.print("\n[bold green]🎉 全ての処理が完了しました！[/bold green]")


@app.command()
def batch(
    city: str = typer.Argument("tokyo", help="都市名"),
    levels: str = typer.Option("5,10,15,20", "--levels", "-l", help="水位リスト(カンマ区切り)"),
    data_dir: Path = typer.Option("data/plateau", "--data", "-d", help="データディレクトリ"),
    output_dir: Path = typer.Option("outputs", "--output", "-o", help="出力ディレクトリ")
):
    """複数水位でバッチ実行"""
    
    water_levels = [float(x.strip()) for x in levels.split(",")]
    
    console.print(f"\n[bold blue]🔄 バッチ処理[/bold blue]")
    console.print(f"都市: {city}")
    console.print(f"水位: {water_levels}\n")
    
    # シミュレータ初期化
    sim = FloodSimulator(city, data_dir)
    sim.load_buildings()
    sim.load_dem()
    
    # 各水位で実行
    all_results = []
    for level in track(water_levels, description="シミュレーション実行中"):
        results = sim.simulate_flood(level)
        results['water_level'] = level
        all_results.append(results)
        sim.export_results(level, output_dir)
    
    # 結果をまとめて保存
    summary_file = output_dir / f"batch_summary_{city}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    # 比較チャートを作成
    viz = FloodVisualizer(sim)
    comparison = viz.create_water_level_comparison(water_levels, sim)
    comparison.write_html(str(output_dir / "maps" / "comparison_chart.html"))
    
    console.print(f"\n[bold green]✅ バッチ処理完了！[/bold green]")
    console.print(f"結果: {summary_file}")


@app.command()
def server(
    port: int = typer.Option(8000, "--port", "-p", help="ポート番号"),
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="ホスト")
):
    """WebUIサーバーを起動"""
    
    console.print(f"\n[bold blue]🌐 WebUIサーバー起動[/bold blue]")
    console.print(f"URL: http://localhost:{port}\n")
    
    # FastAPIアプリを起動
    import uvicorn
    from web_app import app as web_app
    
    uvicorn.run(web_app, host=host, port=port)


@app.command()
def info():
    """システム情報を表示"""
    
    console.print("\n[bold blue]ℹ️ システム情報[/bold blue]\n")
    
    # パッケージバージョン確認
    import geopandas as gpd
    import rasterio
    import pydeck
    from osgeo import gdal
    
    table = Table(title="インストール済みパッケージ")
    table.add_column("パッケージ", style="cyan")
    table.add_column("バージョン", style="green")
    
    packages = [
        ("GeoPandas", gpd.__version__),
        ("Rasterio", rasterio.__version__),
        ("PyDeck", pydeck.__version__),
        ("GDAL", gdal.__version__),
    ]
    
    for name, version in packages:
        table.add_row(name, version)
    
    console.print(table)
    
    # GPU確認
    try:
        import torch
        if torch.cuda.is_available():
            console.print(f"\n[bold green]🎮 GPU検出: {torch.cuda.get_device_name(0)}[/bold green]")
            console.print(f"CUDA Version: {torch.version.cuda}")
        else:
            console.print("\n[yellow]⚠️ GPU未検出[/yellow]")
    except ImportError:
        console.print("\n[yellow]PyTorch未インストール[/yellow]")
    
    # データディレクトリ確認
    data_dir = Path("data/plateau")
    if data_dir.exists():
        files = list(data_dir.glob("*"))
        console.print(f"\n[bold]データディレクトリ:[/bold] {data_dir}")
        console.print(f"ファイル数: {len(files)}")
    else:
        console.print(f"\n[yellow]データディレクトリが存在しません: {data_dir}[/yellow]")


def display_results(results: dict):
    """結果をテーブル表示"""
    
    table = Table(title="シミュレーション結果")
    table.add_column("項目", style="cyan")
    table.add_column("値", style="green")
    
    table.add_row("水位", f"{results['water_level']:.1f} m")
    table.add_row("総建物数", f"{results['total_buildings']:,}")
    table.add_row("完全水没", f"{results['flooded_buildings']:,} ({results['flooded_percentage']:.1f}%)")
    table.add_row("部分水没", f"{results['partially_flooded']:,}")
    table.add_row("影響建物率", f"{results['affected_percentage']:.1f}%")
    table.add_row("最大浸水深", f"{results['max_flood_depth']:.1f} m")
    
    console.print(table)


if __name__ == "__main__":
    app()