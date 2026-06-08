#include <vector>
#include <string>
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/joy.hpp"
#include "sensor_msgs/msg/joint_state.hpp"
#include "std_srvs/srv/set_bool.hpp"
#include "moveit_msgs/srv/servo_command_type.hpp"
#include "control_msgs/msg/joint_jog.hpp"
#include "geometry_msgs/msg/twist_stamped.hpp"

using namespace std::placeholders;
using SetBool = std_srvs::srv::SetBool;
using ServoCommandType = moveit_msgs::srv::ServoCommandType;

using Joy = sensor_msgs::msg::Joy;
using JointState = sensor_msgs::msg::JointState;



class JoyToServoNode : public rclcpp::Node
{
public:
  JoyToServoNode() :
    Node("joy_to_servo_node"),
    joy_axes_(8),
    joy_buttons_(16),
    buttons_mem_(16),
    joint_names_(6)

  {
    // --- SERVICE CLIENTS ---
    // Parameters
    servo_pause_client_ = this->create_client<SetBool>("/servo_node/pause_servo");
    switch_command_type_client_ = this->create_client<ServoCommandType>("/servo_node/switch_command_type");

    // --- PUBLISHERS ---
    joint_jog_publisher_ = this->create_publisher<control_msgs::msg::JointJog>(
      "/servo_node/delta_joint_cmds", 10
    );
    twist_jog_publisher_ = this->create_publisher<geometry_msgs::msg::TwistStamped>(
      "/servo_node/delta_twist_cmds", 10
    );

    timer_ = this->create_timer(
      std::chrono::milliseconds(10),
      std::bind(&JoyToServoNode::publishJog, this)
    );
         
    // --- SUBSCRIBERS ---
    joy_subscriber_ = this->create_subscription<Joy>(
      "/joy", 10, std::bind(&JoyToServoNode::callback_joy, this, _1)
    );

    joint_states_subscriber_ = this->create_subscription<JointState>(
      "/joint_states", 10, std::bind(&JoyToServoNode::callback_joint_states, this, _1)
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
      std::bind(&JoyToServoNode::callbackPauseServoResponse, this, _1)
    );
  }


private:
  // --- CALL METHODS ---
  void callSwtichCommandType(int8_t value) {
    while (!switch_command_type_client_->wait_for_service(std::chrono::seconds(2))) {
      RCLCPP_WARN(this->get_logger(), "Waiting /servo_node/switch_command_type...");
    }
                
    auto request = std::make_shared<ServoCommandType::Request>();
    request->command_type = value;
    switch_command_type_client_->async_send_request(
      request,
      std::bind(&JoyToServoNode::callbackSwtichCommandType, this, _1)
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

  // --- PUBLISHER ---
  void publishJog() {

    builtin_interfaces::msg::Time stamp = this->get_clock()->now();
    std::string frame_id = "base_link";

    if (current_mode_ == ServoMode::JOINT) {
      auto joint_msg = control_msgs::msg::JointJog();

      joint_msg.header.stamp = stamp;
      joint_msg.header.frame_id = frame_id;
      joint_msg.joint_names = {joint_names_[selected_joint_idx_]};
      joint_msg.duration = 0.0;

      if (joy_axes_[0] >= 0.7) {
        joint_msg.velocities = {0.3};

      } else if ((joy_axes_[0] <= -0.7)) {
        joint_msg.velocities = {-0.3};

      } else {
        joint_msg.velocities = {0.0};
      }
      joint_jog_publisher_->publish(joint_msg);    
    }

    if (current_mode_ == ServoMode::TWIST) {
      auto twist_msg = geometry_msgs::msg::TwistStamped();

      twist_msg.header.stamp = stamp;
      twist_msg.header.frame_id = frame_id;

      twist_msg.twist.linear.x = (joy_axes_[0] >= 0.7)  ?  0.1 :
                                 (joy_axes_[0] <= -0.7) ? -0.1 : 0.0;
      twist_msg.twist.linear.y = (joy_axes_[1] >= 0.7)  ?  0.1 :
                                 (joy_axes_[1] <= -0.7) ? -0.1 : 0.0;

      twist_msg.twist.linear.z = 0.0;
      twist_msg.twist.angular.x = (joy_axes_[2] >= 0.7)  ?  0.1 :
                                  (joy_axes_[2] <= -0.7) ? -0.1 : 0.0;
      twist_msg.twist.angular.y = (joy_axes_[3] >= 0.7)  ?  0.1 :
                                  (joy_axes_[3] <= -0.7) ? -0.1 : 0.0;
      twist_msg.twist.angular.z = 0.0;

      twist_jog_publisher_->publish(twist_msg);
    }

  };


  // --- SUBSCRIBERS CALLBACKS ---
  void callback_joint_states(const JointState::SharedPtr msg) {
    // std::ostringstream oss;
    // for (const auto& name : msg->name) {
    //   oss << name << " ";
    // }
    // RCLCPP_INFO(this->get_logger(), "Joints: %s", oss.str().c_str());

    joint_names_ = msg->name;

  }

  void callback_joy(const Joy::SharedPtr msg) {
    // RCLCPP_INFO(this->get_logger(), "Lx: %.2f Ly: %.2f A: %d",
    //   msg->axes[0], msg->axes[1], msg->buttons[0]
    // );
    // RCLCPP_INFO(this->get_logger(), "A: %d B: %d Y: %d X: %d",
    //   msg->buttons[0], msg->buttons[1], msg->buttons[4], msg->buttons[3]
    // );

    joy_axes_ = msg->axes;
    joy_buttons_ = msg->buttons;

    handle_mode_selection();

    if (current_mode_ == ServoMode::JOINT){
      handle_joint_selection();
    }

    // Save last states of joy byttons
    buttons_mem_ = joy_buttons_;
  };

  void handle_mode_selection() {
    bool btn_A_pressed = (joy_buttons_[0] == 1) && (buttons_mem_[0] == 0);
    bool btn_Y_pressed = (joy_buttons_[4] == 1) && (buttons_mem_[4] == 0);

    if (btn_Y_pressed) {
      current_mode_ = static_cast<ServoMode>((static_cast<int>(current_mode_) + 1) % 3);
    }
    if (btn_A_pressed) {
      current_mode_ = static_cast<ServoMode>((static_cast<int>(current_mode_) + 2) % 3);;
    }

    if (btn_A_pressed || btn_Y_pressed) {
      const std::map<ServoMode, std::string> mode_names = {
        {ServoMode::JOINT, "JOINT"},
        {ServoMode::TWIST, "TWIST"},
        {ServoMode::POSE,  "POSE"}
      };

      RCLCPP_INFO(this->get_logger(), "Set mode to: %d: %s", (int)current_mode_, mode_names.at(current_mode_).c_str());

      callSwtichCommandType(int(current_mode_));
    }
  }

  void handle_joint_selection() {

    bool btn_B_pressed = (joy_buttons_[1] == 1) && (buttons_mem_[1] == 0);
    bool btn_X_pressed = (joy_buttons_[3] == 1) && (buttons_mem_[3] == 0);

    if (btn_B_pressed) {
      selected_joint_idx_ = std::min(selected_joint_idx_ + 1, (int)joint_names_.size() - 1);
    }
    if (btn_X_pressed) {
      selected_joint_idx_ = std::max(selected_joint_idx_ - 1, 0);
    }

    if (btn_B_pressed or btn_X_pressed) {
      RCLCPP_INFO(this->get_logger(), "Set to %s", joint_names_[selected_joint_idx_].c_str());
    }
  }


  // --- VARIABLES ---
  std::vector<float> joy_axes_;
  std::vector<int> joy_buttons_;
  std::vector<int> buttons_mem_;
  std::vector<std::string> joint_names_;
  int selected_joint_idx_ = 0;

  enum class ServoMode {JOINT, TWIST, POSE};
  ServoMode current_mode_ = ServoMode::JOINT;
  
  // --- TIMERS ---
  rclcpp::TimerBase::SharedPtr timer_;

  // --- SUBSCRIBERS ---
  rclcpp::Subscription<Joy>::SharedPtr joy_subscriber_;
  rclcpp::Subscription<JointState>::SharedPtr joint_states_subscriber_;
  // --- PUBLISHERS ---
  rclcpp::Publisher<control_msgs::msg::JointJog>::SharedPtr joint_jog_publisher_;
  rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr twist_jog_publisher_;
    
  // --- SERVICE CLIENTS ---
  rclcpp::Client<SetBool>::SharedPtr servo_pause_client_;
  rclcpp::Client<ServoCommandType>::SharedPtr switch_command_type_client_;
    
};

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<JoyToServoNode>();
  node->callPauseServo(false);
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}