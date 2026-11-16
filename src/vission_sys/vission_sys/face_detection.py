#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from ament_index_python import get_package_share_directory
from sensor_msgs.msg import Image
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point
import cv2
from cv_bridge import CvBridge, CvBridgeError
import os


class FaceDetection(Node):
    def __init__(self):
        super().__init__('face_detection_node')
        self.get_logger().info('Face Detection is running!!')

        self.pkg = get_package_share_directory('vission_sys')
        self.path = os.path.join(self.pkg, 'config', 'haarcascade_frontalface_default.xml')
        self.facecascad = cv2.CascadeClassifier(self.path)
        
        # self.cap = cv2.VideoCapture(0)
        # self.cap.set(3, 640)
        # self.cap.set(4, 480)
        
        # self.timer = self.create_timer(0.1, self.face_func)

        self.subscriber = self.create_subscription(Image, 'image_raw', self.face_func,10)
        
        self.publisher = self.create_publisher(Image, 'face_detect_frame', 10)
        self.markPublisher = self.create_publisher(MarkerArray, 'face_marker', 10)
        self.cvb = CvBridge()
        


    def face_func(self, data):
        marker_arry = MarkerArray()
        # success, img = self.cap.read()
        # if not success:
        #     self.get_logger().warning("Failed to grab frame")
        #     return
        try:
           img = self.cvb.imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
           print(e)

        img_gry = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        self.face = self.facecascad.detectMultiScale(img_gry, 1.1,4)
        for id, (x, y, w, h) in enumerate(self.face):
            cv2.rectangle(img, (x,y),(x+w,y+h), (0,255,0), 2)
            mk = Marker()
            mk.header.frame_id = 'map'
            mk.type = Marker.LINE_STRIP
            mk.header.stamp = self.get_clock().now().to_msg()
            mk.ns = "faces"
            mk.pose.orientation.w = 0.0
            mk.scale.x = 0.1
            mk.color.r = 0.0
            mk.color.g = 1.0
            mk.color.b = 0.0
            mk.color.a = 1.0
            mk.id = id
            mk.action = Marker.ADD
            mk.lifetime = rclpy.duration.Duration(seconds=0.3).to_msg()
            mk.points = [
                Point(x=float(x)/100,y=float(y)/100,z=0.0),
                Point(x=float(x+w)/100,y=float(y)/100,z=0.0),
                Point(x=float(x+w)/100,y=float(y+h)/100,z=0.0),
                Point(x=float(x)/100,y=float(y+h)/100,z=0.0),
                Point(x=float(x)/100,y=float(y)/100,z=0.0)
            ]
            marker_arry.markers.append(mk)
            
            
        self.markPublisher.publish(marker_arry)
           
        
        # mk.points.clear()
        # mk.header.stamp = self.get_clock().now().to_msg()

        #cv2.imshow('FaceDetection', img)
        self.publisher.publish(self.cvb.cv2_to_imgmsg(img, 'bgr8'))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            # self.cap.release()
            cv2.destroyAllWindows()
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = FaceDetection()
    rclpy.spin(node=node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()