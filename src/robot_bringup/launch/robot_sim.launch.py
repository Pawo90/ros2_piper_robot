import os
import xacro
import launch_ros
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from moveit_configs_utils import MoveItConfigsBuilder
from launch_param_builder import ParameterBuilder
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition
from launch.actions import TimerAction


def generate_launch_description():

    # =========================
    # Paths to configuration and launch files
    # =========================

    # Robot description URDF
    robot_description_path = os.path.join(
        get_package_share_directory("robot_moveit_config"),
        "config",
        "piper_arm.urdf.xacro"
    )

    # Joint limits YAML
    joint_limits_path = os.path.join(
        get_package_share_directory("robot_moveit_config"),
        "config",
        "joint_limits.yaml"
    )

    # Moveit Servo params
    moveit_servo_params_path = os.path.join(
        get_package_share_directory("robot_moveit_servo"),
        "config",
        "servo_parameters.yaml"
    )

    # RViz configration
    rviz_config_path = os.path.join(
        get_package_share_directory("robot_moveit_config"),
        "config",
        "moveit.rviz"
    )

    # =========================
    # Sim time
    # =========================
    # gz_ros2_control publishes /clock and /joint_states using simulation time.
    # Every node that consumes those topics (move_group, rviz2, servo_node,
    # robot_state_publisher, static_tf2_broadcaster, controller spawners) must
    # also run with use_sim_time:=true, or their timestamps will be compared
    # against wall-clock time and every "current state" check will fail.
    use_sim_time = {"use_sim_time": True}

    # =========================
    # Preparing parameters and configs
    # =========================

    moveit_servo_params = (
        ParameterBuilder("robot_moveit_servo")
        .yaml(moveit_servo_params_path)
        .to_dict()
    )

        # Build moveit_config object
    moveit_config = (
        MoveItConfigsBuilder("robot")
        .robot_description(file_path = robot_description_path)
        .joint_limits(file_path = joint_limits_path)
        .to_moveit_configs()
    )


    # =========================
    # Launching nodes
    # =========================
    
    # RViz
    rviz_node = launch_ros.actions.Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_path],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            use_sim_time,
        ],
    )

    # Spawn controllers - connected to gz_control_node
    joint_state_broadcaster_spawner = TimerAction(
        period=5.0,
        actions=[launch_ros.actions.Node(
            package="controller_manager",
            executable="spawner",
            arguments=[
                "joint_state_broadcaster",
                "--controller-manager-timeout", "300",
                "--controller-manager", "/controller_manager",
            ],
            parameters=[use_sim_time],
        )]
    )

    # Spawn controllers - connected to gz_control_node
    arm_controller_spawner = TimerAction(
        period=6.0,
        actions=[launch_ros.actions.Node(
            package="controller_manager",
            executable="spawner",
            arguments=["arm_controller", "-c", "/controller_manager"],
            parameters=[use_sim_time],
        )]
    )

    # Moveit - launch
    move_group_node = launch_ros.actions.Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
            use_sim_time,
        ],
    )

    # Moveit Servo
    # Launch Servo as a standalone node or as a "node component" for better latency/efficiency
    launch_as_standalone_node = LaunchConfiguration(
        "launch_as_standalone_node", default="false"
    )

    # This sets the update rate and planning group name for the acceleration limiting filter.
    acceleration_filter_update_period = {"update_period": 0.01}
    planning_group_name = {"planning_group_name": "arm"}


    # Launch as much as possible in components
    container = launch_ros.actions.ComposableNodeContainer(
        name="moveit_servo_demo_container",
        namespace="/",
        package="rclcpp_components",
        executable="component_container_mt",
        composable_node_descriptions=[
            # Example of launching Servo as a node component
            # Launching as a node component makes ROS 2 intraprocess communication more efficient.
            launch_ros.descriptions.ComposableNode(
                package="moveit_servo",
                plugin="moveit_servo::ServoNode",
                name="servo_node",
                parameters=[
                    moveit_servo_params,
                    acceleration_filter_update_period,
                    planning_group_name,
                    moveit_config.robot_description,
                    moveit_config.robot_description_semantic,
                    moveit_config.robot_description_kinematics,
                    moveit_config.joint_limits,
                    use_sim_time,
                ],
                condition=UnlessCondition(launch_as_standalone_node),
            ),
            launch_ros.descriptions.ComposableNode(
                package="robot_state_publisher",
                plugin="robot_state_publisher::RobotStatePublisher",
                name="robot_state_publisher",
                parameters=[moveit_config.robot_description, use_sim_time],
            ),
            launch_ros.descriptions.ComposableNode(
                package="tf2_ros",
                plugin="tf2_ros::StaticTransformBroadcasterNode",
                name="static_tf2_broadcaster",
                parameters=[
                    {"child_frame_id": "/base_link", "frame_id": "/world"},
                    use_sim_time,
                ],
            ),
        ],
        output="screen",
    )

    # Launch a standalone Servo node.
    # As opposed to a node component, this may be necessary (for example) if Servo is running on a different PC
    servo_node = launch_ros.actions.Node(
        package="moveit_servo",
        executable="servo_node",
        name="servo_node",
        parameters=[
            moveit_servo_params,
            acceleration_filter_update_period,
            planning_group_name,
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.joint_limits,
            use_sim_time,
        ],
        output="screen",
        condition=IfCondition(launch_as_standalone_node),
    )

    # Launch: Gazebo
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("ros_gz_sim"),
                "launch",
                "gz_sim.launch.py"
            )
        ),
        launch_arguments={"gz_args": "empty.sdf -r"}.items()
    )

    # Spawn: Robot in Gazebo
    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-topic", "robot_description"]
    )

    # --- GAZEBO BRIDGE ---
    gazebo_bridge_config_path = os.path.join(
        get_package_share_directory("robot_bringup"),
        "config",
        "gazebo_bridge.yaml"
    )
    ros_gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        parameters=[
            {"config_file": gazebo_bridge_config_path},
            use_sim_time,
        ]
    )


    return LaunchDescription(
        [
            rviz_node,
            joint_state_broadcaster_spawner,
            arm_controller_spawner,
            move_group_node,
            container,
            servo_node,
            gz_sim,
            spawn_robot,
            ros_gz_bridge
        ]
    )