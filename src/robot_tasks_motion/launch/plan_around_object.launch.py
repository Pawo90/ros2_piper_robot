# robot_tasks_motion/launch/plan_around_object.launch.py

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
            executable="plan_around_object_node",
            output="screen",
            parameters=[
                moveit_config.robot_description,
                moveit_config.robot_description_semantic,
                moveit_config.robot_description_kinematics,
                {"use_sim_time": True},
            ],
        )
    ])