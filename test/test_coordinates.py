#!/usr/bin/env python3
"""
Kindleウィンドウキャプチャの座標と画面確認テスト
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from AppKit import NSScreen
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionAll,
    kCGNullWindowID,
)
from AppKit import NSWorkspace

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


def get_all_screens_info():
    """すべてのスクリーン情報を取得"""
    screens = NSScreen.screens()
    print("=" * 60)
    print("スクリーン情報:")
    print("=" * 60)
    for i, screen in enumerate(screens):
        frame = screen.frame()
        print(f"\nスクリーン {i}:")
        print(f"  位置: ({frame.origin.x}, {frame.origin.y})")
        print(f"  サイズ: {frame.size.width}x{frame.size.height}")
    
    primary_screen = screens[0]
    primary_frame = primary_screen.frame()
    print(f"\nプライマリスクリーン（スクリーン 0）:")
    print(f"  解像度: {primary_frame.size.width}x{primary_frame.size.height}")
    print(f"  左上位置: ({primary_frame.origin.x}, {primary_frame.origin.y})")
    
    return screens


def get_kindle_window_bounds_detailed(app):
    """Kindleウィンドウの詳細情報を取得"""
    pid = app.processIdentifier()
    windows = CGWindowListCopyWindowInfo(kCGWindowListOptionAll, kCGNullWindowID)
    
    print("\n" + "=" * 60)
    print(f"Kindleプロセス（PID: {pid}）のウィンドウ:")
    print("=" * 60)
    
    largest_window = None
    largest_area = 0
    
    for window in windows:
        if window.get("kCGWindowOwnerPID") == pid:
            window_name = window.get("kCGWindowName", "")
            bounds = window.get("kCGWindowBounds")
            
            if bounds:
                area = bounds["Width"] * bounds["Height"]
                print(f"\nウィンドウ: '{window_name}'")
                print(f"  位置: X={bounds['X']}, Y={bounds['Y']}")
                print(f"  サイズ: {bounds['Width']}x{bounds['Height']}")
                print(f"  面積: {area}")
                
                # 面積が大きいウィンドウを保持
                if area > largest_area and bounds["Width"] > 100 and bounds["Height"] > 100:
                    largest_area = area
                    largest_window = bounds
    
    if largest_window:
        print(f"\n✓ 最大ウィンドウ:")
        print(f"  位置: X={largest_window['X']}, Y={largest_window['Y']}")
        print(f"  サイズ: {largest_window['Width']}x{largest_window['Height']}")
        return (largest_window["X"], largest_window["Y"], 
                largest_window["Width"], largest_window["Height"])
    
    return None


def check_coordinate_system():
    """座標系の確認"""
    print("\n" + "=" * 60)
    print("座標系の確認:")
    print("=" * 60)
    
    screens = NSScreen.screens()
    main_screen = screens[0]
    frame = main_screen.frame()
    
    print(f"\nmacOS座標系:")
    print(f"  左下原点: (0, 0)")
    print(f"  メインスクリーン幅: {frame.size.width}")
    print(f"  メインスクリーン高さ: {frame.size.height}")
    
    # マルチモニターの場合
    if len(screens) > 1:
        print(f"\n警告: マルチモニター環境が検出されました（{len(screens)}つのスクリーン）")
        print(f"  セカンダリスクリーンがある場合、座標がマイナスになる可能性があります")


def main():
    print("\n" + "🔍 Kindleウィンドウ座標診断ツール\n")
    
    # スクリーン情報
    screens = get_all_screens_info()
    
    # 座標系確認
    check_coordinate_system()
    
    # Kindleウィンドウ情報
    app = find_kindle_window()
    if not app:
        print("\n✗ Kindleアプリが見つかりません")
        return
    
    print(f"\n✓ Kindleアプリを検出")
    bounds = get_kindle_window_bounds_detailed(app)
    
    if not bounds:
        print("\n✗ Kindleウィンドウが見つかりません")
        return
    
    # キャプチャ座標の計算
    x, y, width, height = bounds
    screen_height = screens[0].frame().size.height
    
    print("\n" + "=" * 60)
    print("キャプチャ座標の計算:")
    print("=" * 60)
    print(f"\nウィンドウ座標:")
    print(f"  X: {x}, Y: {y}")
    print(f"  幅: {width}, 高さ: {height}")
    print(f"\nスクリーン高さ: {screen_height}")
    
    # 座標計算
    bbox_left = int(x)
    bbox_top = int(screen_height - y - height)
    bbox_right = int(x + width)
    bbox_bottom = int(screen_height - y)
    
    region = (bbox_left, bbox_top, bbox_right, bbox_bottom)
    print(f"\nImageGrab.grab() の bbox: {region}")
    print(f"  左: {bbox_left}, 上: {bbox_top}, 右: {bbox_right}, 下: {bbox_bottom}")
    print(f"  キャプチャサイズ: {bbox_right - bbox_left}x{bbox_bottom - bbox_top}")
    
    # 警告チェック
    print("\n" + "=" * 60)
    print("確認事項:")
    print("=" * 60)
    
    if bbox_left < 0 or bbox_top < 0:
        print("⚠️  キャプチャ座標がマイナス値です")
        print("   マルチモニター環境の場合、座標系の調整が必要な可能性があります")
    
    if x < 0:
        print(f"⚠️  ウィンドウX座標がマイナス（{x}）です")
        print("   セカンダリモニターにKindleが表示されている可能性があります")
    
    print("\n✓ 座標計算は完了しました")
    print("  実際のキャプチャを実行して、結果を確認してください")


if __name__ == "__main__":
    main()
