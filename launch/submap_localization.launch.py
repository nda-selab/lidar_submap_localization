"""Run only 3D submap-to-prior localization.

Requires pre-existing /cloud_registered (odom), /odom_nav and /initialpose.
Does not launch AMCL, Map Server, FAST-LIO2, or Nav2.
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    config = PathJoinSubstitution([
        FindPackageShare('lidar_submap_localization'),
        'config', 'localization.yaml',
    ])
    return LaunchDescription([
        DeclareLaunchArgument('prior_map', description='Absolute path to 3D PCD in map frame'),
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('config', default_value=config),
        Node(
            package='lidar_submap_localization',
            executable='submap_localizer',
            name='submap_localizer',
            output='screen',
            parameters=[
                LaunchConfiguration('config'),
                {
                    'prior_map_path': LaunchConfiguration('prior_map'),
                    'use_sim_time': ParameterValue(LaunchConfiguration('use_sim_time'), value_type=bool),
                },
            ],
        ),
    ])
