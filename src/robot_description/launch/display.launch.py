import os
import xacro
from launch import LaunchDescription
from ament_index_python.packages import get_package_share_directory
from launch_ros.parameter_descriptions import ParameterValue
from launch.substitutions import Command
from launch_ros.actions import Node

def generate_launch_description():

    # =========================
    # Paths to configuration and launch files
    # =========================

    # Robot description URDF
    robot_description_path = os.path.join(
        get_package_share_directory("robot_description"),
        "urdf",
        "_robot.urdf.xacro"
    )

    # RViz configration
    rviz_config_path = os.path.join(
        get_package_share_directory("robot_description"),
        "rviz",
        "rviz.rviz"
    )

    # =========================
    # Preparing parameters and configs
    # =========================
    robot_description = ParameterValue(
        Command(['xacro ', robot_description_path]),
        value_type=str
    )

    # =========================
    # Launching nodes
    # =========================
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{'robot_description': robot_description}]
    )

    joint_state_publisher_gui_node = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui"
    )

    rviz2_node = Node(
        package="rviz2",
        executable="rviz2",
        arguments=['-d', rviz_config_path]
    )


    return LaunchDescription(
    [
        robot_state_publisher_node,
        joint_state_publisher_gui_node,
        rviz2_node
    ]
)