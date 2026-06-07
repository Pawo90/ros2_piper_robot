cmake_minimum_required(VERSION 3.8)
project(robot_teleop)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(moveit_msgs REQUIRED)
find_package(control_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)

add_executable(joy_to_servo src/joy_to_servo.cpp)
ament_target_dependencies(joy_to_servo
 rclcpp
 sensor_msgs
 std_srvs
 moveit_msgs
 control_msgs
 geometry_msgs)


install(
  TARGETS 
  joy_to_servo
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY config include launch src
  DESTINATION share/${PROJECT_NAME}/
)

ament_package()
