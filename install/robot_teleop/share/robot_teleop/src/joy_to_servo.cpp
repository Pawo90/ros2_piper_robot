#include <vector>
#include <string>
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/joy.hpp"
#include "std_srvs/srv/set_bool.hpp"
#include "moveit_msgs/srv/servo_command_type.hpp"
#include "control_msgs/msg/joint_jog.hpp"

using namespace std::placeholders;
using SetBool = std_srvs::srv::SetBool;
using ServoCommandType = moveit_msgs::srv::ServoCommandType;


class JoyToServoNode : public rclcpp::Node
{
public:
  JoyToServoNode() : Node("joy_to_servo_node")
  {
    // --- SERVICE CLIENTS ---
    servo_pause_client_ = this->create_client<SetBool>("/servo_node/pause_servo");
    switch_command_type_client_ = this->create_client<ServoCommandType>("/servo_node/switch_command_type");

    // --- PUBLISHERS ---
    joint_jog_publisher_ = this->create_publisher<control_msgs::msg::JointJog>(
      "/servo_node/delta_joint_cmds", 10
    );

    timer_ = this->create_timer(
      std::chrono::milliseconds(10),
      std::bind(&JoyToServoNode::publishJointJog, this)
    );
         
    // --- SUBSCRIBERS ---
    joy_subscriber_ = this->create_subscription<sensor_msgs::msg::Joy>(
      "/joy", 10, std::bind(&JoyToServoNode::callback_joy, this, _1)
    );

    RCLCPP_INFO(this->get_logger(), "Joy to servo node has been started.");
  }

  // --- CALL CLIENTS SEVICES ---
  void callPauseServo(bool value) {
    while (!servo_pause_client_->wait_for_service(std::chrono::seconds(2))) {
      RCLCPP_WARN(this->get_logger(), "Waiting for /servo_node/pause_servo...");
    }

    auto request = std::make_shared<SetBool::Request>();
    request->data = value;
    servo_pause_client_->async_send_request(
      request,
      std::bind(&JoyToServoNode::callbackPauseServoResponse,
      this, _1)
    );
  }

  void callSwtichCommandType(int8_t value) {
    while (!switch_command_type_client_->wait_for_service(std::chrono::seconds(2))) {
      RCLCPP_WARN(this->get_logger(), "Waiting /servo_node/switch_command_type...");
    }
                
    auto request = std::make_shared<ServoCommandType::Request>();
    request->command_type = value;
    switch_command_type_client_->async_send_request(
      request,
      std::bind(&JoyToServoNode::callbackSwtichCommandType,
      this, _1)
    );

  }

  // --- SERVICES CLIENTS CALLBACKS ---
  void callbackPauseServoResponse(rclcpp::Client<SetBool>::SharedFuture future){
      auto response = future.get();
      RCLCPP_INFO(this->get_logger(), "Get response: %d, Message: %s", (int)response->success, response->message.c_str());
  }

  void callbackSwtichCommandType(rclcpp::Client<ServoCommandType>::SharedFuture future){
      auto response = future.get();
      RCLCPP_INFO(this->get_logger(), "Changing move mode request response: %d", (int)response->success);
  }


private:
  // --- PUBLISHER ---
  void publishJointJog() {
    auto msg = control_msgs::msg::JointJog();

    msg.header.stamp = this->get_clock()->now();
    msg.header.frame_id = "base_link";
    msg.joint_names = {"joint1"};
    msg.duration = 0.0;

    if (joy_axes[0] >= 0.7) {
      msg.velocities = {0.3};

    } else if ((joy_axes[0] <= -0.7)) {
      msg.velocities = {-0.3};

    } else {
      msg.velocities = {0.0};
    }    

    joint_jog_publisher_->publish(msg);
  };

  // --- SUBSCRIBERS CALLBACKS ---
  void callback_joy(const sensor_msgs::msg::Joy::SharedPtr msg) {
    RCLCPP_INFO(this->get_logger(), "Lx: %.2f Ly: %.2f A: %d",
      msg->axes[0], msg->axes[1], msg->buttons[0]
    );

    joy_axes = msg->axes;
  };

  // --- VARIABLES ---
  std::vector<float> joy_axes = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
  
  // --- TIMERS ---
  rclcpp::TimerBase::SharedPtr timer_;

  // --- SUBSCRIBERS ---
  rclcpp::Subscription<sensor_msgs::msg::Joy>::SharedPtr joy_subscriber_;
  // --- PUBLISHERS ---
  rclcpp::Publisher<control_msgs::msg::JointJog>::SharedPtr joint_jog_publisher_;
    
  // -- SERVICE CLIENTS ---
  rclcpp::Client<SetBool>::SharedPtr servo_pause_client_;
  rclcpp::Client<ServoCommandType>::SharedPtr switch_command_type_client_;
    
};

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<JoyToServoNode>();
  node->callPauseServo(false);
  node->callSwtichCommandType(0);

  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}