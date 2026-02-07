# 必要なライブラリのインポート
import pyautogui as pag
import os, os.path as osp
import datetime, time
from PIL import ImageGrab
import cv2
import numpy as np
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionAll,
    kCGNullWindowID,
)
from AppKit import NSWorkspace, NSRunningApplication, NSScreen
import subprocess
import sys
import argparse

# グローバル変数の設定
kindle_window_title = "Kindle"  # Kindle for Macのアプリケーション名
page_change_key = "right"  # 次のページへ移動するキー
kindle_fullscreen_wait = 5  # フルスクリーン後の待機時間(秒)
l_margin = 1  # 左側マージン
r_margin = 1  # 右側マージン
waitsec = 1.0  # キー押下後の待機時間(秒)

# ページ数設定（コマンドライン引数で上書き）
max_pages = None  # 指定がない場合は全ページ

# トリミング設定（コマンドライン引数で上書き）
crop_top = 0  # 上部トリミング（ピクセル）
crop_bottom = 0  # 下部トリミング（ピクセル）
crop_left = 0  # 左部トリミング（ピクセル）
crop_right = 0  # 右部トリミング（ピクセル）

# 出力設定（コマンドライン引数で上書き）
output_dir = None  # 保存先ベースフォルダ
output_title = None  # 保存先フォルダ名


def find_kindle_window():
    """
    Kindleアプリケーションを検索してプロセスを返す関数
    Returns:
        app: Kindleアプリケーションのプロセス。見つからない場合はNone
    """
    workspace = NSWorkspace.sharedWorkspace()
    running_apps = workspace.runningApplications()

    for app in running_apps:
        app_name = app.localizedName()
        if app_name and kindle_window_title in app_name:
            return app
    return None


def setup_kindle_window(app):
    """
    Kindleウィンドウを前面に表示しフォーカスを設定
    Args:
        app: アプリケーションオブジェクト
    """
    # アプリケーションをアクティブにする
    app.activateWithOptions_(1 << 1)  # NSApplicationActivateIgnoringOtherApps
    time.sleep(0.5)

    # AppleScriptでウィンドウを前面に持ってくる
    script = """tell application "System Events"
        set frontmost of process "Kindle" to true
    end tell"""
    subprocess.run(["osascript", "-e", script], check=False)
    time.sleep(1)


def get_kindle_window_bounds(app):
    """
    Kindleウィンドウの位置とサイズを取得
    Args:
        app: Kindleアプリケーションオブジェクト
    Returns:
        (x, y, width, height): ウィンドウの位置とサイズ、取得失敗時はNone
    """
    pid = app.processIdentifier()
    windows = CGWindowListCopyWindowInfo(kCGWindowListOptionAll, kCGNullWindowID)
    
    # 最も大きいウィンドウを探す
    largest_window = None
    largest_area = 0
    
    for window in windows:
        if window.get("kCGWindowOwnerPID") == pid:
            bounds = window.get("kCGWindowBounds")
            
            if bounds:
                area = bounds["Width"] * bounds["Height"]
                # 面積が大きいウィンドウを保持（ただし最小サイズは指定）
                if area > largest_area and bounds["Width"] > 100 and bounds["Height"] > 100:
                    largest_area = area
                    largest_window = (bounds["X"], bounds["Y"], bounds["Width"], bounds["Height"])
    
    return largest_window


def crop_image(img):
    """
    画像をトリミング
    Args:
        img: PIL Image または NumPy配列
    Returns:
        トリミングされた画像（NumPy配列）
    """
    # PIL ImageをNumPy配列に変換（必要な場合）
    if not isinstance(img, np.ndarray):
        img = np.array(img)
    
    height, width = img.shape[:2]
    
    # トリミング範囲を計算
    top = crop_top
    bottom = height - crop_bottom
    left = crop_left
    right = width - crop_right
    
    # 範囲チェック
    if top >= bottom or left >= right:
        print(f"警告: トリミング範囲が不正です。元の画像を返します。")
        return img
    
    # トリミング実行
    return img[top:bottom, left:right]


def capture_kindle_screenshot():
    """
    Kindleウィンドウのスクリーンショットのみをキャプチャ
    Returns:
        PILImage: キャプチャした画像、失敗時はNone
    """
    app = find_kindle_window()
    if not app:
        return None
    
    # Kindleウィンドウを前面に
    app.activateWithOptions_(1 << 1)
    time.sleep(0.2)
    
    # ウィンドウの位置とサイズを取得
    bounds = get_kindle_window_bounds(app)
    if not bounds:
        return None
    
    x, y, width, height = bounds
    
    # すべてのスクリーンを確認して、ウィンドウが表示されているスクリーンを特定
    screens = NSScreen.screens()
    main_screen = screens[0]
    main_frame = main_screen.frame()
    
    # マルチモニター対応：全体の座標をメインスクリーン相対に変換
    # ウィンドウのプライマリスクリーン高さを使用
    screen_height = main_frame.size.height
    
    # ウィンドウが他のモニターにある場合も対応
    # 各スクリーンの相対座標を計算
    offset_y = 0
    for screen in screens:
        screen_frame = screen.frame()
        # このスクリーンがウィンドウを含んでいるか確認
        if (screen_frame.origin.x <= x < screen_frame.origin.x + screen_frame.size.width or
            screen_frame.origin.x <= x + width <= screen_frame.origin.x + screen_frame.size.width):
            offset_y = screen_frame.origin.y
            break
    
    # 指定した領域をキャプチャ（座標を整数に変換）
    # PIL/ImageGrabは仮想スクリーン座標系を使用するため、直接使用
    region = (int(x), int(y), int(x + width), int(y + height))
    try:
        screenshot = ImageGrab.grab(bbox=region)
        # トリミング処理を適用
        if crop_top > 0 or crop_bottom > 0 or crop_left > 0 or crop_right > 0:
            screenshot_array = crop_image(screenshot)
            # NumPy配列をPIL Imageに戻す
            from PIL import Image
            screenshot = Image.fromarray(cv2.cvtColor(screenshot_array, cv2.COLOR_BGR2RGB))
        return screenshot
    except Exception as e:
        print(f"警告: ImageGrab失敗（{e}）、代替方法を試行中...")
        # 失敗時は全画面キャプチャにフォールバック
        return ImageGrab.grab()


def get_title(custom_title=None):
    """
    保存用のタイトルを取得
    Args:
        custom_title: 指定されたタイトル（指定がない場合は現在時刻）
    """
    if custom_title:
        return str(custom_title)
    return str(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))


def get_save_folder(custom_folder=None):
    """保存先フォルダを取得（指定がない場合はデフォルトパス）"""
    folder = custom_folder or "/Users/ohya/workspaces/kindle-capture/capture"
    # フォルダが存在しない場合は作成
    if not os.path.isdir(folder):
        try:
            os.makedirs(folder, exist_ok=True)
            print(f"保存フォルダを作成しました: {folder}")
        except Exception as e:
            print(f"エラー: フォルダを作成できませんでした: {e}", file=sys.stderr)
            return None
    return folder


def find_content_boundaries(img):
    """
    画像内のコンテンツ境界を検出
    Args:
        img: 画像データ（NumPy配列）
    Returns:
        lft: 左端の位置
        rht: 右端の位置
    """

    def cmps(img, rng):
        """ピクセルの色を比較して境界を検出"""
        for i in rng:
            if np.all(img[20][i] != img[19][0]):
                return i

    lft = cmps(img, range(l_margin, img.shape[1] - r_margin))
    rht = cmps(img, reversed(range(l_margin, img.shape[1] - r_margin)))
    return lft, rht


def capture_and_save_pages(lft, rht, title, max_pages_limit=None):
    """
    ページをキャプチャして保存
    Args:
        lft: 左端の位置
        rht: 右端の位置
        title: 保存時のタイトル
        max_pages_limit: 最大ページ数（Noneの場合は無制限）
    Returns:
        page - 1: 保存したページ数
    """
    # 画面サイズ取得と初期化
    first_screenshot = capture_kindle_screenshot()
    if first_screenshot is None:
        return 0
    
    first_array = np.array(first_screenshot)
    sc_h = first_array.shape[0]
    old = np.zeros((sc_h, rht - lft, 3), np.uint8)
    page = 1
    # 保存先フォルダの設定
    cd = os.getcwd()
    target_folder = osp.join(base_save_folder, title)
    os.makedirs(target_folder, exist_ok=True)
    os.chdir(target_folder)
    
    # 最大ページ数（指定がなければ無制限）
    max_pages_value = max_pages_limit if max_pages_limit is not None else float('inf')
    
    while page <= max_pages_value:
        # ファイル名設定と時間計測開始
        filename = f"{page:03d}.png"
        start = time.perf_counter()
        while True:
            # ページめくり後の待機
            time.sleep(waitsec)
            # Kindleウィンドウのスクリーンショット取得と処理
            s = capture_kindle_screenshot()
            if s is None:
                os.chdir(cd)
                return page - 1
            
            s = np.array(s)
            ss = cv2.cvtColor(s, cv2.COLOR_RGB2BGR)
            ss = ss[:, lft:rht]
            # ページめくり完了を確認
            if not np.array_equal(old, ss):
                break
            # タイムアウト処理
            if time.perf_counter() - start > 10.0:
                os.chdir(cd)
                return page - 1
        # 画像保存と次ページへ
        cv2.imwrite(filename, ss)
        old = ss
        print(f"Page: {page}, {ss.shape}, {time.perf_counter() - start:.2f} sec")
        page += 1
        # 最大ページに達していなければページめくり（キーを押す）
        if page <= max_pages_value:
            pag.press(page_change_key)
    
    # ループ終了時に保存したディレクトリに戻る
    os.chdir(cd)
    return page - 1


def main():
    """メイン処理"""
    global base_save_folder, output_dir, output_title
    # Kindleアプリケーションを探索
    app = find_kindle_window()
    if app is None:
        print(
            "エラー: Kindleアプリケーションが見つかりません。Kindle for Macが起動していることを確認してください。",
            file=sys.stderr,
        )
        return
    # ウィンドウの設定
    setup_kindle_window(app)
    # タイトルと保存先の取得
    title = get_title(custom_title=output_title)
    base_save_folder = get_save_folder(custom_folder=output_dir)
    if not base_save_folder:
        print("エラー: 保存先フォルダが選択されていません", file=sys.stderr)
        return

    print(f"タイトル: {title}")
    print(f"保存先: {base_save_folder}")
    print("\n5秒後にキャプチャを開始します...")

    # Kindleウィンドウを再度アクティブにして、画面サイズを取得してマウス移動
    setup_kindle_window(app)
    time.sleep(kindle_fullscreen_wait)

    # 初期画像を取得して境界を検出
    img = capture_kindle_screenshot()
    if img is None:
        print("エラー: Kindleウィンドウのスクリーンショットが取得できません", file=sys.stderr)
        return
    
    img = np.array(img)
    imp = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    lft, rht = find_content_boundaries(imp)
    # キャプチャを実行
    total_pages = capture_and_save_pages(lft, rht, title, max_pages_limit=max_pages)
    # 完了メッセージを表示
    print(f"\n完了: スクリーンショットの撮影が終了しました。")
    print(f"合計 {total_pages} ページを保存しました。")


if __name__ == "__main__":
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(
        description="Kindle for Macのページをキャプチャして保存します",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  通常モード（すべてのページ）:
    uv run python step1.py

    10ページのみキャプチャ（2秒間隔）:
        uv run python step1.py --max-pages 10 --wait 2.0

    20ページのみキャプチャ（0.5秒間隔）:
        uv run python step1.py --max-pages 20 --wait 0.5
  
  トリミング付きキャプチャ（上30px、下20px削除）:
    uv run python step1.py --crop-top 30 --crop-bottom 20

    保存先ベースフォルダとフォルダ名を指定:
        uv run python step1.py --output-dir /Users/ohya/workspaces/kindle-capture/capture --title 20260207181042
        """
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="キャプチャする最大ページ数（省略時は全ページ）"
    )
    parser.add_argument(
        "--wait",
        type=float,
        default=1.0,
        help="ページめくり後の待機時間（秒）（デフォルト: 1.0）"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="保存先ベースフォルダ（省略時は既定パス）"
    )
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="保存先のフォルダ名（省略時は日時文字列）"
    )
    parser.add_argument(
        "--crop-top",
        type=int,
        default=0,
        help="上部トリミング（ピクセル）（デフォルト: 0）"
    )
    parser.add_argument(
        "--crop-bottom",
        type=int,
        default=0,
        help="下部トリミング（ピクセル）（デフォルト: 0）"
    )
    parser.add_argument(
        "--crop-left",
        type=int,
        default=0,
        help="左部トリミング（ピクセル）（デフォルト: 0）"
    )
    parser.add_argument(
        "--crop-right",
        type=int,
        default=0,
        help="右部トリミング（ピクセル）（デフォルト: 0）"
    )
    
    args = parser.parse_args()
    
    # グローバル変数を設定
    max_pages = args.max_pages
    waitsec = args.wait
    crop_top = args.crop_top
    crop_bottom = args.crop_bottom
    crop_left = args.crop_left
    crop_right = args.crop_right
    output_dir = args.output_dir
    output_title = args.title
    
    print(f"🚀 Kindle キャプチャツール起動")
    print(f"  待機時間: {waitsec}秒")
    if max_pages is not None:
        print(f"  最大ページ数: {max_pages}ページ")
    if crop_top > 0 or crop_bottom > 0 or crop_left > 0 or crop_right > 0:
        print(f"  トリミング: 上{crop_top}px, 下{crop_bottom}px, 左{crop_left}px, 右{crop_right}px")
    if output_dir:
        print(f"  保存先ベース: {output_dir}")
    if output_title:
        print(f"  フォルダ名: {output_title}")
    print()
    
    main()
