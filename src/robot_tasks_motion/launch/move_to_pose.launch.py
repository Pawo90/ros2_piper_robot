# robot_tasks_motion/launch/move_to_pose.launch.py

from launch import LaunchDescription
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():

    moveit_config = (
        MoveItConfigsBuilder("piper_arm", package_name="robot_moveit_config")
        .to_moveit_configs()
    )

    return LaunchDescription([
        Node(
            package="robot_tasks_motion",
            executable="move_to_pose_node",
            output="screen",
            parameters=[
                moveit_config.robot_description,
                moveit_config.robot_description_semantic,
                moveit_config.robot_description_kinematics,
                {"use_sim_time": True},
            ],
        )
    ])