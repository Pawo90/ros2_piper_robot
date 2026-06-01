cmake_minimum_required(VERSION 3.8)
project(robot_moveit_servo)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(moveit_servo REQUIRED)

# Add executable
add_executable(servo_node src/servo_node.cpp)

# Link libraries
ament_target_dependencies(servo_node
  rclcpp
  moveit_servo
)

install(
  TARGETS 
  servo_node
  DESTINATION lib/${PROJECT_NAME}
)


install(DIRECTORY config include launch rviz src
  DESTINATION share/${PROJECT_NAME}/
)

ament_package()
