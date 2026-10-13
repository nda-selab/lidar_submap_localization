# Trouble Shooting

## 動作確認コマンド

```bash
ros2 topic echo /localization/status
ros2 topic echo /localization/pose --once
ros2 topic echo /localization/submap --once --field header
ros2 run tf2_ros tf2_echo map odom
ros2 topic echo /cloud_registered --once --field header
ros2 topic echo /odom_nav --once --field child_frame_id
```

## 開発・診断用コマンド

```bash
# Launchファイルと設定の基本チェック
python3 -m compileall -q launch
python3 -m pytest -q test/test_config.py

# 実行中のトピック配信元・購読先の確認
ros2 topic info /tf --verbose
ros2 topic info /cmd_vel --verbose
ros2 topic info /whill/controller/cmd_vel --verbose
```

詳細な導入手順については[INSTALL_JA.md](INSTALL_JA.md)も参照する。