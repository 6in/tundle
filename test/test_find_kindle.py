#!/usr/bin/env python3
# Kindle検索機能のテスト

from AppKit import NSWorkspace

# グローバル変数の設定
kindle_window_title = "Kindle"  # Kindle for Macのアプリケーション名


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


def main():
    print("実行中のアプリケーションを検索しています...")
    
    # すべての実行中のアプリを表示
    workspace = NSWorkspace.sharedWorkspace()
    running_apps = workspace.runningApplications()
    
    print("\n=== 実行中のアプリケーション一覧 ===")
    for app in running_apps:
        app_name = app.localizedName()
        if app_name:  # 名前があるもののみ表示
            print(f"  - {app_name}")
    
    # Kindleアプリを検索
    print("\n=== Kindleアプリの検索 ===")
    kindle_app = find_kindle_window()
    
    if kindle_app:
        print(f"✓ Kindleアプリが見つかりました！")
        print(f"  アプリ名: {kindle_app.localizedName()}")
        print(f"  プロセスID: {kindle_app.processIdentifier()}")
        print(f"  実行可能ファイル: {kindle_app.executableURL()}")
        print(f"  アクティブ: {kindle_app.isActive()}")
    else:
        print("✗ Kindleアプリが見つかりませんでした")
        print("  Kindle for Macが起動していることを確認してください")


if __name__ == "__main__":
    main()
