"""
AI画像生成モジュール（Stable Diffusion API連携）
"""

import requests
import base64
import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from PIL import Image
import io
import numpy as np
from datetime import datetime


class ApocalypseGenerator:
    """終末世界ビジュアル生成"""
    
    def __init__(self, 
                 api_url: str = "http://localhost:7860",
                 model_type: str = "sd"):
        """
        Args:
            api_url: Stable Diffusion WebUI APIのURL
            model_type: 'sd' for Stable Diffusion WebUI, 'comfy' for ComfyUI
        """
        self.api_url = api_url
        self.model_type = model_type
        self.headers = {"Content-Type": "application/json"}
        
        # APIの接続確認
        self.check_connection()
    
    def check_connection(self) -> bool:
        """API接続を確認"""
        try:
            if self.model_type == "sd":
                response = requests.get(f"{self.api_url}/sdapi/v1/options")
            else:
                response = requests.get(f"{self.api_url}/system_stats")
            
            if response.status_code == 200:
                print(f"✅ API接続成功: {self.api_url}")
                return True
        except requests.exceptions.ConnectionError:
            print(f"⚠️ API接続失敗: {self.api_url}")
            print("  Stable Diffusion WebUIが起動していることを確認してください")
            print("  起動コマンド: ./webui.sh --api --xformers")
            return False
        
        return False
    
    def build_flood_prompt(self, flood_info: Dict) -> Dict[str, str]:
        """浸水情報からプロンプトを構築
        
        Args:
            flood_info: 浸水シミュレーション結果
        
        Returns:
            プロンプトとネガティブプロンプトの辞書
        """
        water_level = flood_info.get('water_level', 10)
        affected_percentage = flood_info.get('affected_percentage', 50)
        
        # 浸水レベルに応じたプロンプト調整
        if water_level < 5:
            flood_severity = "shallow flooding, water reflections"
        elif water_level < 15:
            flood_severity = "deep flooding, partially submerged buildings"
        else:
            flood_severity = "catastrophic deluge, skyscrapers emerging from deep water"
        
        # メインプロンプト
        prompt = f"""
        Post-apocalyptic flooded Tokyo metropolis, {flood_severity},
        {affected_percentage:.0f}% of buildings affected,
        abandoned cityscape, murky brown water,
        collapsed infrastructure, rusted metal structures,
        overgrown vegetation on building facades,
        dramatic stormy sky, dark clouds, moody atmosphere,
        broken windows, debris floating,
        cinematic lighting, golden hour, ray tracing,
        ultra detailed, photorealistic, 8k resolution,
        wide angle view, aerial perspective
        """.strip().replace('\n', ' ')
        
        # ネガティブプロンプト
        negative_prompt = """
        people, humans, cars, vehicles, bright colors,
        sunny, clear sky, cartoon, anime, illustration,
        low quality, blurry, pixelated, watermark, text,
        oversaturated, neon colors
        """.strip().replace('\n', ' ')
        
        return {
            "prompt": prompt,
            "negative_prompt": negative_prompt
        }
    
    def txt2img(self, 
                prompt_dict: Dict[str, str],
                width: int = 1024,
                height: int = 768,
                steps: int = 20,
                cfg_scale: float = 7.0,
                seed: int = -1) -> Optional[bytes]:
        """テキストから画像を生成
        
        Args:
            prompt_dict: プロンプトとネガティブプロンプト
            width: 画像幅
            height: 画像高さ
            steps: 生成ステップ数
            cfg_scale: プロンプトへの忠実度
            seed: シード値（-1でランダム）
        
        Returns:
            生成された画像のバイトデータ
        """
        if not self.check_connection():
            return None
        
        payload = {
            "prompt": prompt_dict["prompt"],
            "negative_prompt": prompt_dict["negative_prompt"],
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "seed": seed,
            "sampler_name": "DPM++ 2M Karras",
            "batch_size": 1,
            "n_iter": 1
        }
        
        print(f"🎨 画像生成中... (ステップ数: {steps})")
        
        try:
            response = requests.post(
                f"{self.api_url}/sdapi/v1/txt2img",
                json=payload,
                headers=self.headers,
                timeout=300  # 5分のタイムアウト
            )
            
            if response.status_code == 200:
                result = response.json()
                image_data = base64.b64decode(result['images'][0])
                print("✅ 画像生成完了！")
                return image_data
            else:
                print(f"❌ エラー: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 生成エラー: {e}")
            return None
    
    def img2img(self,
                base_image: bytes,
                prompt_dict: Dict[str, str],
                denoising_strength: float = 0.75,
                steps: int = 20) -> Optional[bytes]:
        """画像から画像を生成（スタイル変換）
        
        Args:
            base_image: 元画像のバイトデータ
            prompt_dict: プロンプト辞書
            denoising_strength: 変換強度（0-1）
            steps: 生成ステップ数
        
        Returns:
            生成された画像のバイトデータ
        """
        if not self.check_connection():
            return None
        
        # 画像をbase64エンコード
        base64_image = base64.b64encode(base_image).decode('utf-8')
        
        payload = {
            "init_images": [base64_image],
            "prompt": prompt_dict["prompt"],
            "negative_prompt": prompt_dict["negative_prompt"],
            "denoising_strength": denoising_strength,
            "steps": steps,
            "cfg_scale": 7.0,
            "sampler_name": "DPM++ 2M Karras",
            "batch_size": 1,
            "n_iter": 1
        }
        
        print(f"🎨 画像変換中... (強度: {denoising_strength})")
        
        try:
            response = requests.post(
                f"{self.api_url}/sdapi/v1/img2img",
                json=payload,
                headers=self.headers,
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                image_data = base64.b64decode(result['images'][0])
                print("✅ 画像変換完了！")
                return image_data
            else:
                print(f"❌ エラー: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 変換エラー: {e}")
            return None
    
    def generate_flood_scene(self,
                           flood_info: Dict,
                           map_image: Optional[bytes] = None,
                           output_dir: Path = Path("outputs/images")) -> Optional[Path]:
        """浸水シーンを生成
        
        Args:
            flood_info: 浸水情報
            map_image: マップ画像（img2img用）
            output_dir: 出力ディレクトリ
        
        Returns:
            生成画像のパス
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # プロンプト生成
        prompt_dict = self.build_flood_prompt(flood_info)
        
        print("\n=== 生成プロンプト ===")
        print(f"Prompt: {prompt_dict['prompt'][:100]}...")
        print(f"Negative: {prompt_dict['negative_prompt'][:100]}...")
        
        # 画像生成
        if map_image:
            image_data = self.img2img(map_image, prompt_dict)
        else:
            image_data = self.txt2img(prompt_dict)
        
        if image_data:
            # ファイル名を生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            water_level = flood_info.get('water_level', 0)
            filename = f"apocalypse_{water_level}m_{timestamp}.png"
            filepath = output_dir / filename
            
            # 画像を保存
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            print(f"💾 画像を保存しました: {filepath}")
            
            # 画像情報を表示
            img = Image.open(io.BytesIO(image_data))
            print(f"  サイズ: {img.size}")
            print(f"  フォーマット: {img.format}")
            
            return filepath
        
        return None
    
    def generate_comparison_grid(self,
                                water_levels: List[float],
                                simulator,
                                output_path: Path = Path("outputs/comparison.png")):
        """複数水位の比較グリッドを生成
        
        Args:
            water_levels: 水位リスト
            simulator: FloodSimulatorインスタンス
            output_path: 出力パス
        """
        images = []
        
        for level in water_levels:
            print(f"\n水位 {level}m の画像を生成中...")
            
            # シミュレーション実行
            results = simulator.simulate_flood(level)
            
            # 画像生成
            image_path = self.generate_flood_scene(results)
            
            if image_path:
                img = Image.open(image_path)
                images.append(img)
        
        if images:
            # グリッドを作成
            grid_width = min(len(images), 2)
            grid_height = (len(images) + 1) // 2
            
            # 画像サイズを統一
            target_size = (512, 384)
            images = [img.resize(target_size, Image.Resampling.LANCZOS) for img in images]
            
            # グリッド画像を作成
            grid_img = Image.new('RGB', 
                               (grid_width * target_size[0], 
                                grid_height * target_size[1]))
            
            for idx, img in enumerate(images):
                x = (idx % grid_width) * target_size[0]
                y = (idx // grid_width) * target_size[1]
                grid_img.paste(img, (x, y))
            
            # 保存
            grid_img.save(output_path)
            print(f"\n📊 比較グリッドを保存しました: {output_path}")


class MockGenerator(ApocalypseGenerator):
    """API接続なしでテスト用のモック画像を生成"""
    
    def check_connection(self) -> bool:
        print("📝 モックモードで実行中（API接続なし）")
        return True
    
    def txt2img(self, prompt_dict: Dict[str, str], **kwargs) -> bytes:
        """ダミー画像を生成"""
        # グラデーション画像を作成
        width = kwargs.get('width', 1024)
        height = kwargs.get('height', 768)
        
        img = Image.new('RGB', (width, height))
        pixels = img.load()
        
        # 青から赤へのグラデーション（浸水を表現）
        for y in range(height):
            for x in range(width):
                r = int(255 * y / height)
                b = int(255 * (1 - y / height))
                pixels[x, y] = (r, 0, b)
        
        # テキストを追加
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        text = "Mock Apocalypse Image\n(API未接続)"
        draw.text((width//2 - 100, height//2), text, fill=(255, 255, 255))
        
        # バイトデータに変換
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()


if __name__ == "__main__":
    # テスト実行
    print("=== AI画像生成テスト ===\n")
    
    # モックモードでテスト
    generator = MockGenerator()
    
    # サンプル浸水情報
    flood_info = {
        'water_level': 15.0,
        'affected_percentage': 75.0,
        'flooded_buildings': 1000,
        'total_buildings': 1500
    }
    
    # 画像生成
    output_path = generator.generate_flood_scene(flood_info)
    
    if output_path:
        print(f"\n✅ テスト完了！")
    else:
        print(f"\n❌ テスト失敗")