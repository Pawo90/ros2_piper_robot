import os
import launch
import launch_ros
from ament_index_python.packages import get_package_share_directory
from launch_param_builder import ParameterBuilder
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    # Build moveit_config object
    moveit_config = (
        MoveItConfigsBuilder("robot")
        .robot_description(file_path="config/piper_arm.urdf.xacro")
        .joint_limits(file_path="config/joint_limits.yaml")
        .to_moveit_configs()
    )

    # Get parameters for the Servo node
    servo_params = (
        ParameterBuilder("robot_moveit_servo")
        .yaml("config/servo_parameters.yaml")
        .to_dict()
    )

    # This sets the update rate and planning group name for the acceleration limiting filter.
    acceleration_filter_update_period = {"update_period": 0.01}
    planning_group_name = {"planning_group_name": "arm"}

    # RViz
    rviz_config_file = (
        get_package_share_directory("robot_moveit_config")
        + "/config/moveit.rviz"
    )
    rviz_node = launch_ros.actions.Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
        ],
    )

    # ros2_control using FakeSystem as hardware
    ros2_controllers_path = os.path.join(
        get_package_share_directory("robot_moveit_config"),
        "config",
        "ros2_controllers.yaml",
    )
    ros2_control_node = launch_ros.actions.Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[ros2_controllers_path],
        remappings=[
            ("/controller_manager/robot_description", "/robot_description"),
        ],
        output="screen",
    )

    joint_state_broadcaster_spawner = launch_ros.actions.Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager-timeout",
            "300",
            "--controller-manager",
            "/controller_manager",
        ],
    )

    arm_controller_spawner = launch_ros.actions.Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arm_controller", "-c", "/controller_manager"],
    )

    # robot_state_publisher for publish /robot_description
    # without this planning_scene_monitor in our servo node don't know how robot looks like.
    robot_state_publisher_node = launch_ros.actions.Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        parameters=[moveit_config.robot_description],
        output="screen",
    )

    # static_tf2_broadcaster for publish transform from world → base_link
    # without this TF is incomplete and sevrvo can't calculate kinematics
    static_tf2_broadcaster_node = launch_ros.actions.Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_tf2_broadcaster",
        arguments=["0", "0", "0", "0", "0", "0", "world", "base_link"],
        output="screen",
    )

    # Our coustom servo node
    servo_cpp_node = launch_ros.actions.Node(
        package="robot_moveit_servo",
        executable="servo_node",
        name="servo_cpp_node",
        parameters=[
            servo_params,
            acceleration_filter_update_period,
            planning_group_name,
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.joint_limits,
        ],
        output="screen",
    )

    return launch.LaunchDescription(
        [
            rviz_node,
            ros2_control_node,
            joint_state_broadcaster_spawner,
            arm_controller_spawner,
            robot_state_publisher_node,
            static_tf2_broadcaster_node,
            servo_cpp_node,
        ]
    )