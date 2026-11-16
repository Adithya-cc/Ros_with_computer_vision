#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from ament_index_python import get_package_share_directory
from sensor_msgs.msg import Image
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point
import numpy as np
import cv2
from cv_bridge import CvBridge, CvBridgeError
import os


class FaceDetection(Node):
    def __init__(self):
        super().__init__('face_detection_node')
        self.get_logger().info('Face Detection is running!!')

        self.pkg = get_package_share_directory('vission_sys')
        self.prototxt_path = os.path.join(self.pkg, 'config', 'deploy.prototxt.txt')
        self.model_path = os.path.join(self.pkg, 'config', 'res10_300x300_ssd_iter_140000.caffemodel')
        self.confidence=0.5
        self.net = cv2.dnn.readNetFromCaffe(self.prototxt_path,self.model_path)
        
        # self.cap = cv2.VideoCapture(0)
        # self.cap.set(3, 640)
        # self.cap.set(4, 480)
        
        #self.timer = self.create_timer(0.1, self.face_func)
        self.subscriber = self.create_subscription(Image, 'image_raw', self.face_func,10)


        self.publisher = self.create_publisher(Image, 'face_detect_frame_resnet', 10)
        self.markPublisher = self.create_publisher(MarkerArray, 'face_marker_resnet', 10)
        self.cvb = CvBridge()
        

    def face_func(self, data):
        try:
           img = self.cvb.imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
           print(e)
        marker_array = MarkerArray()
        (h, w) = img.shape[:2]
        self.blob = cv2.dnn.blobFromImage(cv2.resize(img, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))

        self.net.setInput(self.blob)
        self.detection = self.net.forward()
        id = 0
        for i in range(0, self.detection.shape[2]):
            # extract teh confidence (i.e., probability associated with the prediction
            confidence = self.detection[0, 0, i, 2]

            # filter out weak self.detection by ensuring the 'confidence' is greater than the minimum confidence
            if confidence < self.confidence:
                continue

            # compute the (x, u) coordinates of the bounding box for the object
            box = self.detection[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype('int')
            
            # draw the bounding box of the face along with the associated probability
            text = '{:.2f}%'.format(confidence * 100)
            y = startY - 10 if startY - 10 > 10 else startY + 10
            cv2.rectangle(img, (startX, startY), (endX, endY), (0, 0, 255), 2)
            cv2.putText(img, text, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (0, 0, 255), 2)
            self.mk = Marker()
            self.mk.header.frame_id = 'map'
            self.mk.type = Marker.LINE_STRIP
            self.mk.pose.orientation.w = 0.0
            self.mk.scale.x = 0.1
            self.mk.color.r = 1.0
            self.mk.color.g = 0.0
            self.mk.color.b = 0.0
            self.mk.color.a = 1.0
            self.mk.header.stamp = self.get_clock().now().to_msg()
            self.mk.id = id
            self.mk.points = [
                Point(x=float(startX)/100,y=float(startY)/100,z=0.0),
                Point(x=float(endX)/100,y=float(startY)/100,z=0.0),
                Point(x=float(endX)/100,y=float(endY)/100,z=0.0),
                Point(x=float(startX)/100,y=float(endY)/100,z=0.0),
                Point(x=float(startX)/100,y=float(startY)/100,z=0.0)
            ]
            marker_array.markers.append(self.mk)
            self.mk.lifetime = rclpy.duration.Duration(seconds=0.3).to_msg()
            id+=1
        self.markPublisher.publish(marker_array)
           
            
        # self.mk.points.clear()
        

        #cv2.imshow('FaceDetection', img)
        self.publisher.publish(self.cvb.cv2_to_imgmsg(img, encoding='bgr8'))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            #self.cap.release()
            cv2.destroyAllWindows()
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = FaceDetection()
    rclpy.spin(node=node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()