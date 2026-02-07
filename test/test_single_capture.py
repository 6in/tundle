#!/usr/bin/env python3
"""
現在のKindleページを1回キャプチャするテスト
"""

import os
import time
import numpy as np
import cv2
from PIL import ImageGrab
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionAll,
    kCGNullWindowID,
)
from AppKit import NSWorkspace, NSRunningApplication, NSScreen

kindle_window_title = "Kindle"


def find_kindle_window():
    """Kindleアプリケーションを検索"""
    workspace = NSWorkspace.sharedWorkspace()
    running_apps = workspace.runningApplications()

    for app in running_apps:
        app_name = app.localizedName()
        if app_name and kindle_window_title in app_name:
            return app
    return None


def get_kindle_window_bounds(app):
    """Kindleウィンドウの位置とサイズを取得（最大ウィンドウ）"""
    pid = app.processIdentifier()
    windows = CGWindowListCopyWindowInfo(kCGWindowListOptionAll, kCGNullWindowID)
    
    largest_window = None
    largest_area = 0
    
    for window in windows:
        if window.get("kCGWindowOwnerPID") == pid:
            bounds = window.get("kCGWindowBounds")
            
            if bounds:
                area = bounds["Width"] * bounds["Height"]
                if area > largest_area and bounds["Width"] > 100 and bounds["Height"] > 100:
                    largest_area = area
                    largest_window = (bounds["X"], bounds["Y"], bounds["Width"], bounds["Height"])
    
    return largest_window


def capture_kindle_screenshot():
    """Kindleウィンドウのスクリーンショットをキャプチャ"""
    app = find_kindle_window()
    if not app:
        print("✗ Kindleアプリが見つかりません")
        return None
    
    # Kindleウィンドウを前面に
    print("Kindleウィンドウをアクティブにしています...")
    app.activateWithOptions_(1 << 1)
    time.sleep(1)
    
    # ウィンドウの位置とサイズを取得
    bounds = get_kindle_window_bounds(app)
    if not bounds:
        print("✗ Kindleウィンドウの位置情報が取得できません")
        return None
    
    x, y, width, height = bounds
    
    print(f"\n📍 ウィンドウ情報:")
    print(f"  位置: X={x}, Y={y}")
    print(f"  サイズ: {width}x{height}")
    
    # キャプチャ領域
    region = (int(x), int(y), int(x + width), int(y + height))
    print(f"\n📸 キャプチャ領域 (bbox): {region}")
    
    try:
        img = ImageGrab.grab(bbox=region)
        print(f"✓ キャプチャ成功: {img.size}")
        return img
    except Exception as e:
        print(f"✗ キャプチャ失敗: {e}")
        return None


def main():
    print("=" * 60)
    print("🎯 Kindleページ単一キャプチャテスト")
    print("=" * 60)
    
    # キャプチャ実行
    img = capture_kindle_screenshot()
    
    if img is None:
        print("\n❌ テスト失敗")
        return
    
    # 画像情報
    img_array = np.array(img)
    print(f"\n📊 画像情報:")
    print(f"  形状: {img_array.shape}")
    print(f"  データ型: {img_array.dtype}")
    
    # 画像を保存
    output_dir = "/Users/ohya/workspaces/kindle-capture"
    output_file = os.path.join(output_dir, "test_capture.png")
    
    # PIL画像をBGRに変換してOpenCVで保存
    if img_array.shape[2] == 4:  # RGBAの場合
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
    else:  # RGBの場合
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    cv2.imwrite(output_file, img_bgr)
    print(f"\n✓ キャプチャを保存しました:")
    print(f"  {output_file}")
    
    print("\n✅ テスト完了")
    print("  上記のファイルを開いて、Kindleの正しいページが")
    print("  キャプチャされているか確認してください")


if __name__ == "__main__":
    main()
