cmake_minimum_required(VERSION 3.8)
project(robot_tasks_motion)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(moveit_visual_tools REQUIRED)
find_package(Eigen3 REQUIRED)

add_executable(move_to_pose_node src/move_to_pose_node.cpp)
add_executable(plan_around_object_node src/plan_around_object_node.cpp)
add_executable(pick_and_place src/pick_and_place.cpp)

target_include_directories(move_to_pose_node PUBLIC
  ${EIGEN3_INCLUDE_DIRS}
)

ament_target_dependencies(move_to_pose_node
  rclcpp
  moveit_ros_planning_interface
  geometry_msgs
  moveit_visual_tools
  Eigen3
)

ament_target_dependencies(plan_around_object_node
  rclcpp
  moveit_ros_planning_interface
  geometry_msgs
  moveit_visual_tools
  Eigen3
)

ament_target_dependencies(pick_and_place
  rclcpp
  moveit_ros_planning_interface
  geometry_msgs
  moveit_visual_tools
  Eigen3
)

install(TARGETS  
  move_to_pose_node
  plan_around_object_node
  pick_and_place  
  DESTINATION lib/${PROJECT_NAME}  
)

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}/
)

ament_package()
