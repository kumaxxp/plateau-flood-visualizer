"""
FastAPI WebUIアプリケーション
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import json
from pathlib import Path
import shutil

from simulator import FloodSimulator
from visualizer import FloodVisualizer
from generator import ApocalypseGenerator, MockGenerator

# FastAPIアプリ初期化
app = FastAPI(title="PLATEAU Flood Visualizer")

# 静的ファイル
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# グローバル変数
simulators = {}


class SimulationRequest(BaseModel):
    """シミュレーションリクエスト"""
    city: str = "tokyo"
    water_level: float = 10.0
    generate_image: bool = False


class SimulationResponse(BaseModel):
    """シミュレーションレスポンス"""
    water_level: float
    total_buildings: int
    flooded_buildings: int
    partially_flooded: int
    safe_buildings: int
    affected_percentage: float
    map_2d_url: Optional[str] = None
    map_3d_url: Optional[str] = None
    generated_image_url: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def root():
    """メインページ"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PLATEAU Flood Visualizer</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 30px;
                backdrop-filter: blur(10px);
            }
            h1 {
                text-align: center;
                margin-bottom: 30px;
            }
            .controls {
                display: flex;
                gap: 20px;
                margin-bottom: 30px;
                flex-wrap: wrap;
            }
            .control-group {
                flex: 1;
                min-width: 200px;
            }
            label {
                display: block;
                margin-bottom: 5px;
            }
            input, select, button {
                width: 100%;
                padding: 10px;
                border-radius: 5px;
                border: none;
                background: rgba(255, 255, 255, 0.9);
                color: #333;
            }
            button {
                background: #4CAF50;
                color: white;
                cursor: pointer;
                font-size: 16px;
                margin-top: 20px;
            }
            button:hover {
                background: #45a049;
            }
            .results {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }
            .result-card {
                background: rgba(255, 255, 255, 0.2);
                padding: 15px;
                border-radius: 5px;
                text-align: center;
            }
            .result-value {
                font-size: 24px;
                font-weight: bold;
                margin-top: 10px;
            }
            .map-container {
                margin-top: 30px;
            }
            .map-links {
                display: flex;
                gap: 20px;
                justify-content: center;
            }
            .map-link {
                padding: 10px 20px;
                background: #2196F3;
                color: white;
                text-decoration: none;
                border-radius: 5px;
            }
            .map-link:hover {
                background: #0b7dda;
            }
            #loading {
                display: none;
                text-align: center;
                margin: 20px;
            }
            .spinner {
                border: 4px solid rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                border-top: 4px solid white;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌊 PLATEAU Flood Visualizer</h1>
            
            <div class="controls">
                <div class="control-group">
                    <label for="city">都市:</label>
                    <select id="city">
                        <option value="tokyo">東京</option>
                        <option value="nagoya">名古屋</option>
                    </select>
                </div>
                
                <div class="control-group">
                    <label for="waterLevel">水位 (m): <span id="levelValue">10</span></label>
                    <input type="range" id="waterLevel" min="0" max="30" value="10" step="0.5">
                </div>
                
                <div class="control-group">
                    <label>
                        <input type="checkbox" id="generateImage">
                        AI画像生成
                    </label>
                </div>
            </div>
            
            <button onclick="runSimulation()">シミュレーション実行</button>
            
            <div id="loading">
                <div class="spinner"></div>
                <p>処理中...</p>
            </div>
            
            <div id="results" class="results" style="display: none;">
                <div class="result-card">
                    <div>総建物数</div>
                    <div class="result-value" id="totalBuildings">-</div>
                </div>
                <div class="result-card">
                    <div>完全水没</div>
                    <div class="result-value" id="floodedBuildings">-</div>
                </div>
                <div class="result-card">
                    <div>部分水没</div>
                    <div class="result-value" id="partiallyFlooded">-</div>
                </div>
                <div class="result-card">
                    <div>影響率</div>
                    <div class="result-value" id="affectedPercentage">-</div>
                </div>
            </div>
            
            <div id="mapContainer" class="map-container" style="display: none;">
                <div class="map-links">
                    <a id="map2dLink" class="map-link" target="_blank">2Dマップを開く</a>
                    <a id="map3dLink" class="map-link" target="_blank">3Dマップを開く</a>
                </div>
            </div>
        </div>
        
        <script>
            // 水位スライダーの値を表示
            document.getElementById('waterLevel').addEventListener('input', function(e) {
                document.getElementById('levelValue').textContent = e.target.value;
            });
            
            async function runSimulation() {
                const city = document.getElementById('city').value;
                const waterLevel = parseFloat(document.getElementById('waterLevel').value);
                const generateImage = document.getElementById('generateImage').checked;
                
                // ローディング表示
                document.getElementById('loading').style.display = 'block';
                document.getElementById('results').style.display = 'none';
                document.getElementById('mapContainer').style.display = 'none';
                
                try {
                    const response = await fetch('/api/simulate', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            city: city,
                            water_level: waterLevel,
                            generate_image: generateImage
                        })
                    });
                    
                    const data = await response.json();
                    
                    // 結果を表示
                    document.getElementById('totalBuildings').textContent = data.total_buildings.toLocaleString();
                    document.getElementById('floodedBuildings').textContent = data.flooded_buildings.toLocaleString();
                    document.getElementById('partiallyFlooded').textContent = data.partially_flooded.toLocaleString();
                    document.getElementById('affectedPercentage').textContent = data.affected_percentage.toFixed(1) + '%';
                    
                    // マップリンクを設定
                    if (data.map_2d_url) {
                        document.getElementById('map2dLink').href = data.map_2d_url;
                        document.getElementById('map3dLink').href = data.map_3d_url;
                        document.getElementById('mapContainer').style.display = 'block';
                    }
                    
                    document.getElementById('results').style.display = 'grid';
                    
                } catch (error) {
                    alert('エラーが発生しました: ' + error);
                } finally {
                    document.getElementById('loading').style.display = 'none';
                }
            }
        </script>
    </body>
    </html>
    """
    return html_content


@app.post("/api/simulate", response_model=SimulationResponse)
async def simulate(request: SimulationRequest):
    """シミュレーションを実行"""
    
    # シミュレータを取得または作成
    if request.city not in simulators:
        sim = FloodSimulator(request.city)
        try:
            sim.load_buildings()
            sim.load_dem()
        except FileNotFoundError:
            # サンプルデータを使用
            pass
        simulators[request.city] = sim
    else:
        sim = simulators[request.city]
    
    # シミュレーション実行
    results = sim.simulate_flood(request.water_level)
    
    # 可視化
    viz = FloodVisualizer(sim)
    
    # 出力ディレクトリ
    output_dir = Path("static/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 2Dマップ生成
    map_2d_path = output_dir / f"map_2d_{request.city}_{request.water_level}.html"
    viz.create_folium_map(sim.buildings, request.water_level, map_2d_path)
    
    # 3Dマップ生成
    map_3d_path = output_dir / f"map_3d_{request.city}_{request.water_level}.html"
    viz.create_pydeck_3d(sim.buildings, request.water_level, map_3d_path)
    
    # レスポンス作成
    response = SimulationResponse(
        water_level=results['water_level'],
        total_buildings=results['total_buildings'],
        flooded_buildings=results['flooded_buildings'],
        partially_flooded=results['partially_flooded'],
        safe_buildings=results['safe_buildings'],
        affected_percentage=results['affected_percentage'],
        map_2d_url=f"/static/outputs/{map_2d_path.name}",
        map_3d_url=f"/static/outputs/{map_3d_path.name}"
    )
    
    # AI画像生成（オプション）
    if request.generate_image:
        try:
            gen = ApocalypseGenerator()
            if not gen.check_connection():
                gen = MockGenerator()
            
            image_path = gen.generate_flood_scene(results, output_dir=output_dir)
            if image_path:
                response.generated_image_url = f"/static/outputs/{image_path.name}"
        except Exception as e:
            print(f"画像生成エラー: {e}")
    
    return response


@app.post("/api/upload")
async def upload_data(file: UploadFile = File(...)):
    """PLATEAUデータをアップロード"""
    
    # ファイルを保存
    data_dir = Path("data/plateau")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = data_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"message": f"ファイル {file.filename} をアップロードしました", "path": str(file_path)}


@app.get("/api/status")
async def get_status():
    """システムステータスを取得"""
    
    data_dir = Path("data/plateau")
    data_files = list(data_dir.glob("*")) if data_dir.exists() else []
    
    return {
        "status": "running",
        "data_files": len(data_files),
        "loaded_cities": list(simulators.keys())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)