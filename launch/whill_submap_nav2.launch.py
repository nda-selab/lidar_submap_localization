"""WHILL Nav2 with 3D prior-map localization and a 2D map server, NO AMCL.

Use instead of autonomous_navigation.launch.py, not alongside it.
Default hardware:=false is intentionally conservative for rosbag/bench testing.
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def other(package, *components, condition=None, arguments=None):
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare(package), *components,
        ])),
        condition=condition,
        launch_arguments=(arguments or {}).items(),
    )


def generate_launch_description():
    map_yaml = PathJoinSubstitution([
        FindPackageShare('whill_nav2_bringup'), 'maps', 'map.yaml',
    ])
    nav2_params = PathJoinSubstitution([
        FindPackageShare('whill_nav2_bringup'), 'config', 'nav2_params.yaml',
    ])
    yaml_config = PathJoinSubstitution([
        FindPackageShare('lidar_submap_localization'), 'config', 'localization.yaml',
    ])
    sim_time = LaunchConfiguration('use_sim_time')
    sensor_hostname = LaunchConfiguration('sensor_hostname')

    hardware = other(
        'whill_nav2_bringup', 'launch', 'bringup', 'hardware_bringup.launch.py',
        condition=IfCondition(LaunchConfiguration('hardware')),
        arguments={'sensor_hostname': sensor_hostname},
    )
    slam_and_base_tf = other(
        'whill_nav2_bringup', 'launch', 'components', 'localization.launch.py',
    )
    scan = other(
        'whill_nav2_bringup', 'launch', 'components', 'points_to_scan.launch.py',
    )
    navigation = other(
        'whill_nav2_bringup', 'launch', 'components', 'whill_navigation.launch.py',
        arguments={
            'params_file': nav2_params,
            'use_sim_time': sim_time,
            'autostart': 'true',
        },
    )
    visual = other(
        'whill_nav2_bringup', 'launch', 'components', 'visualization.launch.py',
        arguments={'use_rviz': LaunchConfiguration('use_rviz')},
    )

    # Deliberately launch only the 2D map server. No AMCL is started.
    # The 3D localizer is the ONLY map->odom broadcaster.
    map_server = Node(
        package='nav2_map_server', executable='map_server', name='map_server',
        output='screen',
        parameters=[{
            'yaml_filename': LaunchConfiguration('map'),
            'use_sim_time': ParameterValue(sim_time, value_type=bool),
        }],
    )
    map_lifecycle = Node(
        package='nav2_lifecycle_manager', executable='lifecycle_manager',
        name='lifecycle_manager_localization', output='screen',
        parameters=[{
            'autostart': True,
            'use_sim_time': ParameterValue(sim_time, value_type=bool),
            'node_names': ['map_server'],
        }],
    )
    localizer = other(
        'lidar_submap_localization', 'launch', 'submap_localization.launch.py',
        arguments={
            'prior_map': LaunchConfiguration('prior_map'),
            'use_sim_time': sim_time,
            'config': LaunchConfiguration('localization_config'),
        },
    )
    watchdog = Node(
        package='whill_nav2_bringup', executable='whill_cmd_vel_watchdog.py',
        name='whill_cmd_vel_watchdog', output='screen',
        parameters=[{
            'input_topic': '/cmd_vel',
            'output_topic': '/whill/controller/cmd_vel',
            'command_timeout_sec': 0.4,
            'publish_frequency': 20.0,
            'max_forward_speed': 0.25,
            'max_reverse_speed': 0.15,
            'max_angular_speed': 0.5,
        }],
    )
    return LaunchDescription([
        DeclareLaunchArgument('prior_map', description='Absolute path to prior 3D PCD'),
        DeclareLaunchArgument('map', default_value=map_yaml),
        DeclareLaunchArgument('localization_config', default_value=yaml_config),
        DeclareLaunchArgument('hardware', default_value='false'),
        DeclareLaunchArgument('sensor_hostname', default_value='os-992029000281.local'),
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('use_rviz', default_value='true'),
        hardware,
        TimerAction(period=3.0, actions=[slam_and_base_tf, scan, map_server, map_lifecycle, localizer]),
        TimerAction(period=6.0, actions=[navigation, watchdog, visual]),
    ])
