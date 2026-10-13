# Configuration

| Section | Variable | Type | Description |
| --- | --- | --- | --- |
| General | `use_sim_time` | `bool` | ROSシミュレーション時刻を使用するか。rosbag再生で`/clock`を使用する場合は`true`にする。 |
| Frames | `map_frame` | `string` | 3次元事前地図の座標系。`map_frame` → `odom_frame`の親フレーム。 |
| Frames | `odom_frame` | `string` | SLAMオドメトリと登録済み点群の座標系。`map_frame` → `odom_frame`の子フレーム。 |
| Frames | `base_frame` | `string` | 車体座標系。受信オドメトリの`child_frame_id`にも使用する。 |
| Topics | `cloud_topic` | `string` | `odom_frame`座標系に変換された**1スキャン分**の点群トピック。累積地図は入力しない。 |
| Topics | `odom_topic` | `string` | `odom_frame` → `base_frame`の位置姿勢を含むオドメトリトピック。 |
| Topics | `initial_pose_topic` | `string` | `map_frame`座標系における車体の初期位置・姿勢を受け取るトピック。 |
| Prior Map | `prior_map_path` | `string` | 3次元事前地図PCDのファイルパス。**必須**。通常はLaunch引数`prior_map`で設定する。空文字のままでは起動できない。 |
| Submap | `submap_duration_sec` | `double` | スライディングサブマップに保持する点群の最大時間幅［s］。 |
| Submap | `max_scans` | `int` | サブマップに保持するスキャン数の上限。時間幅とスキャン数の両条件で古いデータを削除する。 |
| Submap | `scan_voxel_size` | `double` | 個々の入力スキャンをダウンサンプリングするボクセル幅［m］。 |
| Submap | `submap_voxel_size` | `double` | 複数スキャンの統合後に行うサブマップのボクセル幅［m］。 |
| Prior Map | `prior_map_voxel_size` | `double` | 事前PCDを読み込み時にダウンサンプリングするボクセル幅［m］。 |
| Submap | `min_scan_points` | `int` | スキャン採用に必要な最小点数。無効点除去後とボクセル処理後の両方で判定する。 |
| Submap | `min_submap_points` | `int` | GICPへ入力するサブマップに必要な最小点数。 |
| Prior Map | `min_target_points` | `int` | 事前地図全体および抽出した照合対象領域に必要な最小点数。 |
| Registration | `registration_frequency` | `double` | サブマップと事前地図の照合を試みる周期［Hz］。実際の処理頻度はGICP計算時間にも依存する。 |
| Prior Map | `local_map_radius_xy` | `double` | 予測車体位置を中心に事前地図から切り出すXY各方向の半幅［m］。 |
| Prior Map | `local_map_half_height` | `double` | 予測車体位置を中心に事前地図から切り出すZ方向の半幅［m］。 |
| GICP | `gicp_max_correspondence_distance` | `double` | GICPで対応点とみなす最大距離［m］。適合度計算にも渡す。 |
| GICP | `gicp_max_iterations` | `int` | GICPの最大反復回数。 |
| GICP | `gicp_transformation_epsilon` | `double` | PCL GICPの変換変化に関する収束判定閾値。 |
| GICP | `gicp_euclidean_fitness_epsilon` | `double` | PCL GICPの適合度変化に関する収束判定閾値。 |
| Quality | `max_fitness_score` | `double` | 採用可能なGICP適合度の上限。`getFitnessScore()`が返す平均二乗距離に相当する指標［概ねm²］。小さいほど厳しい。 |
| Quality | `overlap_distance` | `double` | 照合後のサブマップ点が事前地図に対応すると判断する最近傍距離の閾値［m］。 |
| Quality | `min_overlap_ratio` | `double` | `overlap_distance`以内に最近傍点を持つサブマップ点の割合の下限［0〜1］。大きいほど厳しい。 |
| Correction | `max_correction_translation` | `double` | 2回目以降の照合で許容する車体推定位置の補正量［m］。 |
| Correction | `max_correction_rotation_rad` | `double` | 2回目以降の照合で許容する姿勢補正角［rad］。 |
| Correction | `bootstrap_max_correction_translation` | `double` | 初回の照合で許容する車体推定位置の補正量［m］。 |
| Correction | `bootstrap_max_correction_rotation_rad` | `double` | 初回の照合で許容する姿勢補正角［rad］。 |
| Freshness | `max_odom_age_sec` | `double` |  オドメトリ・点群の鮮度および両者の時刻差の許容閾値［s］。 |
| Freshness | `max_alignment_age_sec` | `double` | 最後に採用した照合結果の最大有効時間［s］。超過時は`map_frame` → `odom_frame`のTF配信を止める。 |

## 設定上の注意事項

1. **入力座標系を統一する。** `cloud_topic`の`PointCloud2.header.frame_id`および`odom_topic`の`Odometry.header.frame_id`は`odom_frame`と一致し、オドメトリの`child_frame_id`は`base_frame`と一致する必要がある。
2. **事前地図とNav2用2次元地図を整合させる。** 3次元事前PCDは`map_frame`座標系で保存する。Nav2用`map.yaml`・`map.pgm`と原点・軸方向・スケールが違う場合は、地図そのものを座標変換する。
3. **初期位置を与える。** 本実装には自動的な大域位置探索がない。`/initialpose`から初期の`map_frame` → `odom_frame`候補を計算し、GICPで検証する。
4. **数値の妥当性を保つ。** 時間、距離、ボクセル幅、照合閾値などは有限かつ正の値にする。`max_scans`は2以上、点数・反復回数の下限は1以上、`min_overlap_ratio`は`0 < value <= 1`とする。
5. **変更後はノードを再起動する。** `use_sim_time`を除く主要設定値は現在のC++実装で起動時に読み取り、動的変更を反映する仕組みは設けていない。
6. **品質判定は安全停止ではない。** 照合失敗や鮮度超過でTF配信が止まっても、WHILLの停止を保証しない。走行系には独立した安全監視が必要である。

## 調整時の目安

- **サブマップの形状・計算負荷**：`submap_duration_sec`、`max_scans`、`scan_voxel_size`、`submap_voxel_size`を調整する。長いサブマップほど観測構造は増える一方、SLAMの累積歪みも入りやすい。
- **照合の成立性**：`local_map_radius_xy`、`local_map_half_height`、`gicp_max_correspondence_distance`、`gicp_max_iterations`を確認する。事前地図から切り出す範囲が小さすぎると対応先が不足する。
- **誤照合の抑制**：`max_fitness_score`、`min_overlap_ratio`、`max_correction_translation`、`max_correction_rotation_rad`を調整する。閾値だけでは繰り返し構造による誤収束を完全には防げない。
- **初期位置の不確かさ**：`bootstrap_max_correction_translation`と`bootstrap_max_correction_rotation_rad`は初回照合専用であり、通常時の補正上限とは区別する。
