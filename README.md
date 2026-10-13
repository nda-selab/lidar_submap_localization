# lidar_submap_localization

本パッケージは、LiDAR SLAMのオドメトリ座標系で生成した**スライディング方式の局所サブマップ**と、固定された3次元事前地図（PCD）を照合し、事前地図上の自己位置・姿勢を推定する。

FAST-LIO2の内部処理やオドメトリは変更しない。GICP（Generalized ICP）によって座標変換 **`T_map_odom`** を推定し、照合結果が品質判定に合格した場合にのみ `map -> odom` のTFを配信する。

## Environment

| Type | Details |
| --- | --- |
| OS | Ubuntu 22.04 LTS |
| ROS | ROS 2 Humble |

## Installation

ROS 2 Humble、PCL、Eigen3、`pcl_conversions`、`tf2_ros`、および`package.xml`に記載したROSメッセージ関連パッケージを使用する。

```bash
cd ~/ros2_ws/src

git clone git@github.com:nda-selab/lidar_submap_localization.git

cd ~/ros2_ws

source /opt/ros/humble/setup.bash

colcon build --symlink-install --packages-select lidar_submap_localization

source install/setup.bash
```

## 入出力インターフェース

| Category | Topic | Type | Description |
| --- | --- | --- | --- |
| 入力 | `/cloud_registered` | `sensor_msgs/msg/PointCloud2` | `odom`座標系の**1スキャン分の位置合わせ済み点群**。累積地図全体ではないこと |
| 入力 | `/odom_nav` | `nav_msgs/msg/Odometry` | `header.frame_id: odom`、`child_frame_id: base_link` |
| 入力 | `/initialpose` | `geometry_msgs/msg/PoseWithCovarianceStamped` | `map`座標系における`base_link`の初期位置・姿勢（RVizの「2D Pose Estimate」） |
| ファイル | `prior_map.pcd` | PCD | `map`座標系で表現した3次元事前地図 |
| 出力 | `/tf`（`map -> odom`） | TF | 照合品質に応じて配信。**配信元は本ノードの1つに限定すること** |
| 出力 | `/localization/pose` | `geometry_msgs/msg/PoseStamped` | `map`座標系における`base_link`の推定位置・姿勢 |
| 出力 | `/localization/submap` | `sensor_msgs/msg/PointCloud2` | `odom`座標系のスライディングサブマップ（RViz表示用） |
| 出力 | `/localization/status` | `std_msgs/msg/String` | `ACCEPT`、`REJECT_*`、`WAIT_*`と、適合度・重なり率・補正量などの診断情報 |

## 座標系と推定原理

```text
map --（本パッケージ：GICP）--> odom --（odom_to_base_link）--> base_link

T_map_base(t) = T_map_odom * T_odom_base(t)
T_map_odom     = argmin_T GICP( T * submap_odom, prior_map_map )
```

既存のFAST-LIO2の`research`ブランチでは、次の設定を使用する。

```yaml
frames:
  world_frame: odom
  body_frame: os_imu
```

このとき、`/cloud_registered`は`odom`座標系で出力される。また、`/Odometry`をWHILL側の`odom_to_base_link.py`で変換することで、`/odom_nav`と`odom -> base_link`のTFを取得できる。

ほかのSLAMフレームワークを使用する場合は、**1スキャン分の登録済み点群とオドメトリ**を同じ形式で提供するアダプタを用意する。SLAM固有の累積地図をそのまま使用するのではなく、直近の登録済みスキャンから共通のサブマップを再構築する。

> **地図座標系に関する重要事項**
>
> Nav2用の2次元地図`maps/map.yaml`と3次元事前地図PCDは、原点・軸方向・スケールが整合する**同じ`map`座標系**で用意する必要がある。別の原点で生成したPCDは、座標変換してから`map`座標系の地図として保存すること。ROSのTFフレーム名だけを変更しても地図の不整合は解消しない。

## 最初の動作確認：自己位置推定のみ（推奨）

FAST-LIO2などのSLAM、`odom_to_base_link.py`、既存の静的TF、およびRVizを別途起動する。`/cloud_registered`と`/odom_nav`の座標系が想定どおりであることを確認してから、本パッケージを起動する。

```bash
ros2 launch lidar_submap_localization submap_localization.launch.py \
  prior_map:=/absolute/path/to/merged_map.pcd
```

### 初期位置・姿勢の指定

RVizの「2D Pose Estimate」から、`map`座標系の`/initialpose`を送信する。

- X・Y・Yaw：RVizで指定した位置・向きを使用する。
- Z・Roll・Pitch：受信したPoseメッセージに含まれる値を使用する。
- RVizからの一般的な入力ではZ=0、Roll=0、Pitch=0となる。これは`base_link`が地図のZ=0の床面に存在する場合などに限って適切である。
- 6自由度の初期位置・姿勢が必要な場合は、別のPublisherから適切な`/initialpose`を送信する。

**最初のGICP照合が品質判定に合格するまで、`map -> odom`のTFは配信されない。** 自動的な大域位置認識・初期位置探索は実装していない。

## WHILL・Nav2との統合起動

既存のAMCLによる位置推定を使用する起動構成を、3次元事前地図照合方式に置き換える。

```bash
ros2 launch lidar_submap_localization whill_submap_nav2.launch.py \
  prior_map:=/absolute/path/to/merged_map.pcd \
  map:=/absolute/path/to/map.yaml \
  hardware:=true
```

このLaunchでは、次のノード群を起動する。

- WHILL、Ouster、URGのハードウェア関連ノード（オプション）
- FAST-LIO2と`odom_to_base_link.py`
- `pointcloud_to_laserscan`
- AMCLを除いた2次元`map_server`
- 本パッケージの3次元自己位置推定ノード
- WHILL用のNav2ナビゲーションノード群（Velocity Smootherを含む）
- WHILL用の速度指令Watchdog
- RViz

> **重複起動は禁止**
>
> このLaunchと`whill_nav2_bringup`の`autonomous_navigation.launch.py`、または別のAMCL起動ファイルを同時に実行しないこと。`map -> odom`のTF配信元や速度指令Publisherが競合するおそれがある。必要な`whill_nav2_bringup`の版とWatchdogノードがインストールされていることを確認する。

### rosbagによるオフライン検証

rosbag実験では`hardware:=false`を基本とする。Ouster／URGのセンサデータと`/tf_static`をbagから再生するか、静的TFノードを別途起動する必要がある。

Launch側ではFAST-LIO2とNav2も起動するため、再生するbagには必要なセンサデータを含め、`use_sim_time:=true`の場合は`/clock`も配信すること。

**オフライン検証時の速度指令を、接続中のWHILLドライバへ送ってはいけない。**

## サブマップ生成・地図照合・棄却条件

- **サブマップ生成**：各スキャンを`scan_voxel_size`でボクセルダウンサンプリングした後、`odom`座標系で直近5秒・最大60スキャンをスライディングバッファに保持し、`submap_voxel_size`で再度ダウンサンプリングする。
- **事前地図の準備**：起動時に`prior_map_voxel_size`でダウンサンプリングし、予測された`map`座標系の車体位置の周辺から、XYZ方向の局所領域を抽出する。
- **GICPの初期値**：直前に採用された`T_map_odom`を使用する。初期化時は手動入力の`/initialpose`から初期変換を得る。
- **照合結果の棄却**：非収束、適合度の悪化、事前地図近傍にあるサブマップ点の割合不足、非現実的に大きい車体位置・姿勢補正などを棄却する。具体的な閾値は`config/localization.yaml`を参照する。
- **TF配信**：少なくとも1回の照合が採用された後、受信したオドメトリの時刻に合わせて`map -> odom`を配信する。最後の採用結果から`max_alignment_age_sec`以上経過すると、TF配信を停止する。

### 制限事項

- 初期化前にTFを配信しない設計であり、**自動大域自己位置推定（場所認識）は行わない**。
- 適合度と重なり率による判定だけでは、似た廊下の繰り返し構造などによる誤対応・退化を完全には検出できない。GICPが収束したことだけでは、正しい自己位置推定を保証できない。
- 正確性は、記録済み走行軌跡や独立した基準点を使用して評価する必要がある。
- SLAMのオドメトリやサブマップに対するループ閉じ込み、非剛体的な変形補正は行わない。

## 安全上の重要事項

1. **自己位置推定の失敗は、自動停止を保証しない。** `map -> odom`のTFが途絶した場合や誤った姿勢が推定された場合にも、安全な停止が保証されるわけではない。Nav2とWHILLの走行系には、推定結果の鮮度と妥当性を監視する独立した停止機構が必要である。既存の速度指令Watchdogは指令の受信状況を監視するだけで、自己位置推定の状態は監視しない。
2. **Watchdog自体の故障に備える必要がある。** `whill_nav2_bringup`の`whill_cmd_vel_watchdog`は`/cmd_vel`のタイムアウト時にゼロ速度を出力するが、Watchdogの停止やPCの故障時には停止を保証できない。ドライバまたは車体制御器における通信断時の停止機構が不可欠である。
3. **WHILL実機での検証は未完了。** まず記録済みbagで検証し、次に駆動輪を安全に切り離した状態などで試験し、その後に監督下で低速走行を行う。

## 関連ファイル

- [`config/localization.yaml`](config/localization.yaml)：設定YAMLファイル
- [`config/README.md`](config/README.md)：設定パラメータ説明
- [`config/README.md`](config/README.md)：設定パラメータ説明
- [`doc/INSTALL_JA.md`](doc/INSTALL_JA.md)：導入・検証手順
