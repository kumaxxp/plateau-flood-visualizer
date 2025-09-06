"""
PLATEAU Flood Visualizer Package
水没シミュレーション＆終末世界ビジュアライザー
"""

__version__ = "1.0.0"
__author__ = "Your Name"

from .simulator import FloodSimulator
from .visualizer import FloodVisualizer
from .generator import ApocalypseGenerator, MockGenerator

__all__ = [
    "FloodSimulator",
    "FloodVisualizer",
    "ApocalypseGenerator",
    "MockGenerator"
]