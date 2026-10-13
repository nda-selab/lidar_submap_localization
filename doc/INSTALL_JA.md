# ROS 2 Humble 導入手順（WHILL・FAST-LIO2）

このパッケージは、既存のSLAMによる`odom -> base_link`を変更せず、`odom`座標系で蓄積した**直近の登録済みスキャン群**を事前PCDにGICP照合します。検証に成功した場合だけ`map -> odom`のTFを配信します。

## 1. ファイルの配置・ビルド

```bash
cd ~/ros2_ws/src
unzip ~/Downloads/lidar_submap_localization.zip
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
CMAKE_BUILD_PARALLEL_LEVEL=1 colcon build --symlink-install \
  --packages-select lidar_submap_localization --parallel-workers 1 \
  --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  "-DCMAKE_CXX_FLAGS_RELWITHDEBINFO=-O2 -g0 -DNDEBUG"
source install/setup.bash
```

ZIPを展開すると`~/ros2_ws/src/lidar_submap_localization/`ができます。依存が不足している場合はシステムのROS2 Humble・PCL・Eigen3・`pcl_conversions`パッケージの導入を確認してください。

## 2. 事前に確認するデータ

```bash
ros2 topic echo /cloud_registered --once --field header
ros2 topic echo /odom_nav --once --field header
ros2 topic echo /odom_nav --once --field child_frame_id
```

- `/cloud_registered`: `frame_id=odom`。複数スキャン蓄積地図**ではなく、現在フレームの登録済み点群**が周期的に配信されていること。
- `/odom_nav`: `header.frame_id=odom`, `child_frame_id=base_link`。
- `prior_map.pcd`: 3D事前地図。2Dの`map.pgm/map.yaml`と座標原点・方向が一致すること。

## 3. まず単独で試験

既存SLAM・オドメトリ変換・静的TF・RVizを用意し、以下で単独ノードを起動：

```bash
ros2 launch lidar_submap_localization submap_localization.launch.py \
  prior_map:=/absolute/path/to/merged_map.pcd
```

RVizの2D Pose Estimateで初期位置を与えてください。ローカライザは初期姿勢を受け取るまでTFを出しません。また、初回GICP照合が品質判定を通らなければTFを出しません。初期姿勢入力のZ・Roll・Pitchも使うため、PCDと2D地図の床高さが一致しているか確認してください。

```bash
ros2 topic echo /localization/status
ros2 run tf2_ros tf2_echo map odom
ros2 topic echo /localization/pose --once
```

`/localization/status`の`ACCEPT`は品質閾値を通過したことを示すだけで、真値との一致や退化の解消を保証しません。

## 4. WHILL用統合起動

**既存の`autonomous_navigation.launch.py`と同時に使用しないでください。** AMCLが`map -> odom`を重複配信してしまいます。

```bash
ros2 launch lidar_submap_localization whill_submap_nav2.launch.py \
  prior_map:=/absolute/path/to/merged_map.pcd \
  map:=/absolute/path/to/map.yaml \
  hardware:=true
```

統合Launchは、既存のFAST-LIO2、`odom_to_base_link.py`、2D地図サーバ、Nav2、速度平滑化・Watchdogを使用します。**AMCLは起動しません**。`/scan_ouster`は引き続きNav2の障害物検出に使います。

実機なしのbag試験は`hardware:=false`（既定）。この場合、`/ouster/points`・`/ouster/imu`、静的TF等をbagから供給するか別途起動してください。bagの`/clock`を使用する場合、時間設定を全関連ノードで統一してください。

## 5. 実機走行前に残る課題

- GICP誤照合の検出：幾何拘束の弱い環境や似た廊下では残差が低くても誤収束することがあります。真値で評価してください。
- `map -> odom`が古くなった場合にNav2とWHILLを**独立して停止させる監視**は未実装です。TF配信停止だけで安全な停止を保証しません。
- モータを動かす前にWatchdog・ドライバ・非常停止を独立に検証してください。
- PCD全域の点数が大きい場合は事前地図のボクセル化、部分地図の範囲、周期を調整してください。

## 6. 実験パラメータ

`config/localization.yaml`の`submap_duration_sec`（既定5秒）、`submap_voxel_size`（0.3 m）、`registration_frequency`（1 Hz）、`max_fitness_score`、`min_overlap_ratio`、`max_correction_translation`などをbagで評価します。まず、静止・直線・旋回の各区間を記録し、地図重なりと`map -> odom`の時間変化を確認してください。
