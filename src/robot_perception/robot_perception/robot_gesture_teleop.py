#!/usr/bin/env python3

import os
import sys
import math
import time

venv_path = os.path.expanduser('~/ros2_ws/piper_robot/.venv/lib/python3.12/site-packages')
if venv_path not in sys.path:
    sys.path.insert(0, venv_path)

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from control_msgs.msg import JointJog
from geometry_msgs.msg import TwistStamped



class TeleopGestureNode(Node):
    def __init__(self):
        super().__init__('teleop_gesture')

        # --- ROS2 ---
        # Image subscriber
        self.img_raw_subscription_ = self.create_subscription(
            Image,
            '/image',
            self.callback_image,
            1
        )

        # Gesture teleop publisher
        self.gesture_teleop_publisher_ = self.create_publisher(
             TwistStamped,
             "/servo_node/delta_twist_cmds",
             10
        )

        # --- Open CV ---
        # Bridge to cover OpenCV images and ROS msgs
        self.bridge_ = CvBridge()

        # --- Media Pipe ---
        self.model_path_ = "/home/pawo90/ros2_ws/perception/src/teleop_gesture/teleop_gesture/hand_landmarker.task"

        self.baseOptions_ = mp.tasks.BaseOptions
        self.handLandmarker_ = mp.tasks.vision.HandLandmarker
        self.handLandmarkerOptions_ = mp.tasks.vision.HandLandmarkerOptions
        self.visionRunningMode_ = mp.tasks.vision.RunningMode

        self.options_ = self.handLandmarkerOptions_(
            base_options=self.baseOptions_(model_asset_path = self.model_path_),
            running_mode=self.visionRunningMode_.IMAGE,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5
        )
        self.landmarker_ = self.handLandmarker_.create_from_options(self.options_)

        # Logger info
        self.get_logger().info("Teleop gesture node has been started")


    def twist_msg(self, lx, ly, lz, ax, ay, az):

        msg = TwistStamped()

        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"

        msg.twist.linear.x = lx
        msg.twist.linear.y = ly
        msg.twist.linear.z = lz
        msg.twist.angular.x = ax
        msg.twist.angular.y = ay
        msg.twist.angular.z = az
        
        return msg
    

    def callback_image(self, msg: Image):
        try:
            # Conver ROS2 Image message to OpenCV image
            cv_frame = self.bridge_.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            cv_frame = cv2.flip(cv_frame, 1)

            # Get frame size
            h, w, _ = cv_frame.shape
            rgb_frame = cv2.cvtColor(cv_frame, cv2.COLOR_BGR2RGB)

            # Set image grid 3x3
            col1 = w // 3
            col2 = 2 * (w // 3)
            row1 = h // 3
            row2 = 2 * (h // 3)

            # Print grid
            # Linie pionowe
            cv2.line(cv_frame, (col1, 0), (col1, h), (0, 255, 255), 1)
            cv2.line(cv_frame, (col2, 0), (col2, h), (0, 255, 255), 1)
            # Linie poziome
            cv2.line(cv_frame, (0, row1), (w, row1), (0, 255, 255), 1)
            cv2.line(cv_frame, (0, row2), (w, row2), (0, 255, 255), 1)


            # MEDIAPIPE PREPROCESS IMAGE
            # Convert the frame received from OpenCV to a MediaPipe’s Image object.
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            # Read detection result    
            detection_result = self.landmarker_.detect(mp_image)

            # Prepare cmd
            cmd = self.twist_msg(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

            if detection_result.hand_landmarks:
                # self.get_logger().info("Hand detected!")

                detected_hand = detection_result.hand_landmarks[0]
                points_coordinates = []
                
                for idx, landmark in enumerate(detected_hand):

                    if (idx == 0) or (idx % 4 == 0):
                        # 0 - Wrist 
                        # 4 - Thumb IP
                        # 8 - Index finder Tip
                        # 12 - Middle finger Tip
                        # 16 - Ring finger Tip
                        # 20 - Pinky Tip
                        # Calculate coordinates to pixels
                        cx = int(landmark.x * w)
                        cy = int(landmark.y * h)
                        
                        points_coordinates.append((cx, cy))
                        

                        # Draw circles
                        cv2.circle(cv_frame, center=(cx, cy), radius=2, color=(0, 255, 0), thickness=-1)
                
                wrist_x = points_coordinates[0][0]
                wrist_y = points_coordinates[0][1]

                # Calculate distance betwen writst and index finger tip
                d_x = points_coordinates[2][0] - wrist_x
                d_y = points_coordinates[2][1] - wrist_y
                dist = math.hypot(d_x, d_y)

                # Hand is closed
                if dist <= 90:
                    self.get_logger().info(f"Hands is closed: {dist:.2f}")
                    
                    # Check wrist position on frame
                    if wrist_x < col1:
                        hand_col = 0
                    elif col1 <= wrist_x <= col2:
                        hand_col = 1
                    else:
                        hand_col = 2

                    if wrist_y < row1:
                        hand_row = 0
                    elif row1 <= wrist_y <= row2:
                        hand_row = 1
                    else:
                        hand_row = 2
                    
                    # Prepare comand base on wrist position
                    if hand_col == 0 and hand_row == 0:
                        cmd = self.twist_msg(0.0, -0.1, 0.1, 0.0, 0.0, 0.0)

                    elif hand_col == 1 and hand_row == 0:
                        cmd = self.twist_msg(0.0, 0.0, 0.1, 0.0, 0.0, 0.0)

                    elif hand_col == 2 and hand_row == 0:
                        cmd = self.twist_msg(0.0, 0.1, 0.1, 0.0, 0.0, 0.0)
                    
                    elif hand_col == 0 and hand_row == 1:
                        cmd = self.twist_msg(0.0, -0.1, 0.0, 0.0, 0.0, 0.0)

                    elif hand_col == 1 and hand_row == 1:
                        cmd = self.twist_msg(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

                    elif hand_col == 2 and hand_row == 1:
                        cmd = self.twist_msg(0.0, 0.1, 0.0, 0.0, 0.0, 0.0)

                    elif hand_col == 0 and hand_row == 2:
                        cmd = self.twist_msg(0.0, -0.1, -0.1, 0.0, 0.0, 0.0)

                    elif hand_col == 1 and hand_row == 2:
                        cmd = self.twist_msg(0.0, 0.0, -0.1, 0.0, 0.0, 0.0)

                    elif hand_col == 2 and hand_row == 2:
                        cmd = self.twist_msg(0.0, -0.1, -0.1, 0.0, 0.0, 0.0)


                # Hand is closed
                else:
                    self.get_logger().info(f"Hands is closed: {dist:.2f}")

                # Print coordinates near wrist
                text_position = (points_coordinates[0][0] + 15, points_coordinates[0][1] - 5)
                cv2.putText(cv_frame,
                    text=f"(x: {points_coordinates[0][0]:.2f}, y: {points_coordinates[0][1]:.2f})",
                    org=text_position,
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX, 
                    fontScale=0.4,                   
                    color=(255, 0, 0),           
                    thickness=1,                     
                    lineType=cv2.LINE_AA
                )
            
            # Publish command
            self.gesture_teleop_publisher_.publish(msg=cmd)                    
   
            # Display the image
            cv2.imshow("Processed Image", cv_frame)
            cv2.waitKey(1)

        except Exception as e:
            self.get_logger().error(f"Error processing image: {e}")





def main(args=None):
	rclpy.init(args=args)
	node = TeleopGestureNode()
	
	rclpy.spin(node)
	rclpy.shutdown()

if __name__ == '__main__':
	main()