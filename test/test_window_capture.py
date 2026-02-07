#!/usr/bin/env python3
"""
Kindleウィンドウキャプチャ機能のテスト
"""

import time
import numpy as np
from PIL import Image
from AppKit import NSWorkspace, NSScreen
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionAll,
    kCGNullWindowID,
)
from PIL import ImageGrab
import cv2

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
    """
    Kindleウィンドウの位置とサイズを取得
    """
    pid = app.processIdentifier()
    windows = CGWindowListCopyWindowInfo(kCGWindowListOptionAll, kCGNullWindowID)
    
    print(f"KindleプロセスID: {pid}")
    print(f"見つかったウィンドウ数: {len(windows)}")
    
    # 最も大きいウィンドウを探す
    largest_window = None
    largest_area = 0
    
    for window in windows:
        if window.get("kCGWindowOwnerPID") == pid:
            window_name = window.get("kCGWindowName", "")
            bounds = window.get("kCGWindowBounds")
            
            if bounds:
                area = bounds["Width"] * bounds["Height"]
                print(f"\n  - ウィンドウ名: '{window_name}'")
                print(f"    サイズ: {bounds['Width']}x{bounds['Height']} (面積: {area})")
                print(f"    位置: ({bounds['X']}, {bounds['Y']})")
                
                # 面積が大きいウィンドウを保持（ただし最小サイズは指定）
                if area > largest_area and bounds["Width"] > 100 and bounds["Height"] > 100:
                    largest_area = area
                    largest_window = (bounds["X"], bounds["Y"], bounds["Width"], bounds["Height"])
    
    if largest_window:
        print(f"\n✓ 最大ウィンドウを選択: {largest_area}ピクセル")
        return largest_window
    
    return None


def capture_kindle_screenshot(app):
    """
    Kindleウィンドウのスクリーンショットのみをキャプチャ
    """
    # Kindleウィンドウを前面に
    app.activateWithOptions_(1 << 1)
    time.sleep(0.5)
    
    # ウィンドウの位置とサイズを取得
    bounds = get_kindle_window_bounds(app)
    if not bounds:
        print("エラー: ウィンドウ情報が取得できません")
        return None
    
    x, y, width, height = bounds
    print(f"\nウィンドウ情報:")
    print(f"  X: {x}, Y: {y}")
    print(f"  幅: {width}, 高さ: {height}")
    
    # macOSの座標系は左下が原点なので調整
    screen_height = NSScreen.screens()[0].frame().size.height
    print(f"スクリーン高さ: {screen_height}")
    
    # 指定した領域をキャプチャ（座標を整数に変換）
    region = (int(x), int(screen_height - y - height), int(x + width), int(screen_height - y))
    print(f"キャプチャ領域: {region}")
    
    img = ImageGrab.grab(bbox=region)
    return img


def test_window_bounds():
    """ウィンドウ位置・サイズ取得テスト"""
    print("=" * 60)
    print("テスト1: Kindleウィンドウの位置・サイズ取得")
    print("=" * 60)
    
    app = find_kindle_window()
    if not app:
        print("✗ Kindleアプリが見つかりません")
        return False
    
    print(f"✓ Kindleアプリを検出: {app.localizedName()}")
    
    bounds = get_kindle_window_bounds(app)
    if bounds:
        print(f"✓ ウィンドウ情報を取得しました")
        print(f"  位置: ({bounds[0]}, {bounds[1]})")
        print(f"  サイズ: {bounds[2]}x{bounds[3]}")
        return True
    else:
        print("✗ ウィンドウ情報が取得できません")
        return False


def test_screenshot():
    """スクリーンショット取得テスト"""
    print("\n" + "=" * 60)
    print("テスト2: Kindleウィンドウのスクリーンショット取得")
    print("=" * 60)
    
    app = find_kindle_window()
    if not app:
        print("✗ Kindleアプリが見つかりません")
        return False
    
    print(f"✓ Kindleアプリを検出: {app.localizedName()}")
    
    img = capture_kindle_screenshot(app)
    if img:
        print(f"✓ スクリーンショットを取得しました")
        print(f"  サイズ: {img.size}")
        
        # 画像として保存
        save_path = "/Users/ohya/workspaces/kindle-capture/test_screenshot.png"
        img.save(save_path)
        print(f"  保存先: {save_path}")
        
        # 画像の情報を表示
        img_array = np.array(img)
        print(f"  配列形状: {img_array.shape}")
        print(f"  データ型: {img_array.dtype}")
        
        return True
    else:
        print("✗ スクリーンショットが取得できません")
        return False


def test_image_comparison():
    """画像比較テスト"""
    print("\n" + "=" * 60)
    print("テスト3: 画像変化検出（ページめくり検出）")
    print("=" * 60)
    
    app = find_kindle_window()
    if not app:
        print("✗ Kindleアプリが見つかりません")
        return False
    
    # 最初の画像を取得
    print("最初の画像を取得しています...")
    img1 = capture_kindle_screenshot(app)
    if not img1:
        print("✗ 最初の画像が取得できません")
        return False
    
    img1_array = np.array(img1)
    img1_cv = cv2.cvtColor(img1_array, cv2.COLOR_RGB2BGR)
    print(f"✓ 最初の画像を取得: {img1_cv.shape}")
    
    # 5秒待機
    print("\n5秒待機しています (この間にページをめくってください)...")
    time.sleep(5)
    
    # 2番目の画像を取得
    print("2番目の画像を取得しています...")
    img2 = capture_kindle_screenshot(app)
    if not img2:
        print("✗ 2番目の画像が取得できません")
        return False
    
    img2_array = np.array(img2)
    img2_cv = cv2.cvtColor(img2_array, cv2.COLOR_RGB2BGR)
    print(f"✓ 2番目の画像を取得: {img2_cv.shape}")
    
    # 画像の比較
    if np.array_equal(img1_cv, img2_cv):
        print("✗ 画像が変わっていません（ページめくりが検出されません）")
        return False
    else:
        # 差分を計算
        diff = cv2.absdiff(img1_cv, img2_cv)
        diff_count = np.count_nonzero(diff)
        total_pixels = diff.shape[0] * diff.shape[1] * diff.shape[2]
        change_ratio = (diff_count / total_pixels) * 100
        
        print(f"✓ 画像が変わっています")
        print(f"  変化ピクセル数: {diff_count}")
        print(f"  変化率: {change_ratio:.2f}%")
        
        return True


def main():
    """すべてのテストを実行"""
    print("\n" + "🧪 Kindleウィンドウキャプチャテスト")
    print("=" * 60)
    
    results = {}
    
    # テスト1
    results["ウィンドウ位置・サイズ取得"] = test_window_bounds()
    
    # テスト2
    results["スクリーンショット取得"] = test_screenshot()
    
    # テスト3
    results["画像比較（ページめくり検出）"] = test_image_comparison()
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)
    for test_name, result in results.items():
        status = "✓ 成功" if result else "✗ 失敗"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    print("\n" + ("🎉 すべてのテストに合格しました！" if all_passed else "❌ いくつかのテストが失敗しました"))


if __name__ == "__main__":
    main()
