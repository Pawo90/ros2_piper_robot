# ros2_piper_robot

A ROS 2 (Jazzy) workspace for the **Piper** 6-DOF robotic arm, covering URDF/Gazebo simulation, MoveIt 2 motion planning, real-time servoing, and two teleoperation modes — joystick and hand-gesture control via a perception pipeline.

## Overview

This workspace is built around `gz_ros2_control` + Gazebo Harmonic for simulation and MoveIt 2 for planning and Cartesian/joint servoing. On top of that, two teleoperation paths are implemented: a classic joystick-to-servo bridge, and an experimental gesture-based controller that reads hand position from a camera feed (via MediaPipe) and converts it into Cartesian twist commands.

## Packages

| Package | Description |
|---|---|
| `robot_description` | URDF/xacro model of the Piper arm and gripper, with STL meshes for visualization and collision. |
| `robot_bringup` | Top-level launch files (`robot.launch.py`, `robot_sim.launch.py`) that bring up description, controllers, MoveIt, and the Gazebo bridge together. |
| `robot_moveit_config` | MoveIt 2 Setup Assistant-generated configuration: kinematics, joint limits, controllers, planning groups, and demo/RViz launch files. |
| `robot_moveit_servo` | C++ MoveIt Servo node and parameters for real-time joint/Cartesian jogging. |
| `robot_teleop` | C++ node (`joy_to_servo`) that converts joystick input into MoveIt Servo commands (joint jog / twist jog / stop modes). |
| `robot_perception` | Python node using MediaPipe Hand Landmarker to translate hand position and pinch gestures (read from an image topic) into Cartesian twist commands for teleoperation. |

## Requirements

- ROS 2 Jazzy
- Gazebo Harmonic + `gz_ros2_control`
- MoveIt 2
- Python: `mediapipe`, `opencv-python`, `cv_bridge` (for `robot_perception`)

## Build

```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

## Usage

Launch the full simulation stack (Gazebo + controllers + MoveIt):

```bash
ros2 launch robot_bringup robot_sim.launch.py
```

Start MoveIt Servo for real-time jogging:

```bash
ros2 launch robot_moveit_servo servo.launch.py
```

Joystick teleoperation:

```bash
ros2 run robot_teleop joy_to_servo
```

Gesture-based teleoperation (requires a camera publishing to `/image`):

```bash
ros2 run robot_perception robot_gesture_teleop
```

## Status

Actively under development. Current focus: stabilizing the Gazebo Harmonic simulation pipeline and exploring bin-picking with RGB-D perception (YOLO + depth fusion).

## License

TODO

Perception launch
Remove hardcoded path
Add install requirements