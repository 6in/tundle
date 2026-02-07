#!/usr/bin/env python3
"""
PyTorchのMetal環境対応確認スクリプト
"""

import torch
import sys

print("=" * 60)
print("PyTorch Metal環境確認")
print("=" * 60)

print(f"\nPyTorch版: {torch.__version__}")
print(f"Python版: {sys.version}")

# CPU情報
print(f"\n🖥️ CPU情報:")
print(f"  CPU: {torch.get_num_threads()}個のスレッド")

# GPU/Metal情報
print(f"\n🎮 Metal (GPU) 情報:")
print(f"  Metal利用可能: {torch.backends.mps.is_available()}")
print(f"  Metal ビルド対応: {torch.backends.mps.is_built()}")

if torch.backends.mps.is_available() and torch.backends.mps.is_built():
    print(f"\n✅ PyTorchはMetalで動作可能です")
    
    # 簡単な計算テスト
    print(f"\n🧪 Metalで簡単な計算テスト:")
    
    try:
        # Metalデバイスに設定
        device = torch.device("mps")
        
        # テンソル生成
        x = torch.randn(1000, 1000, device=device)
        y = torch.randn(1000, 1000, device=device)
        
        # 行列積計算
        z = torch.matmul(x, y)
        
        print(f"  ✓ テンソルをMetalで計算成功")
        print(f"  デバイス: {device}")
        print(f"  テンソル形状: {z.shape}")
        
    except Exception as e:
        print(f"  ✗ Metal計算エラー: {e}")
else:
    print(f"\n⚠️ MetalはこのMacで利用できません")
    print(f"  - Apple Silicon (M1/M2/M3など) MacBook が必要です")
    print(f"  - IntelベースのMacではCPUのみで動作します")
    print(f"  - PyTorch最新版（1.12以上）が必要です")

print("\n" + "=" * 60)
