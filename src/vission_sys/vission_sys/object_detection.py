#!/usr/bin/env python3
import rclpy
import os
from rclpy.node import Node
import cv2 
from ament_index_python import get_package_share_directory
from cv_bridge import CvBridge, CvBridgeError
from sensor_msgs.msg import Image
from ultralytics import YOLO
from visualization_msgs.msg import Marker, MarkerArray
import math
from std_msgs.msg import ColorRGBA
from geometry_msgs.msg import Point

class ObjectDetection(Node):

    def __init__(self):
        super().__init__('object_detection')
        pkg = get_package_share_directory('vission_sys')
        self.get_logger().info("Running object detection")
        yolo_path = os.path.join(pkg, 'config', "yolo11n.pt")
        coco_path = os.path.join(pkg, 'config', "coco8.yaml")
        self.model = YOLO(yolo_path)
        self.cvb  = CvBridge()
        # self.cap = cv2.VideoCapture(0)
        # self.cap.set(3, 720)
        # self.cap.set(4, 720)
        self.classNames = [
            'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 
            'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 
            'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 
            'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 
            'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 
            'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 
            'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 
            'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 
            'scissors', 'teddy bear', 'hair drier', 'toothbrush'
        ]

        self.sub_cam = self.create_subscription(Image, '/camera_depth_frame/image_raw',self.callback, 10)
        self.publisher_ = self.create_publisher(Image, '/object_detetion_frame', 10)
        self.marker_pub = self.create_publisher(MarkerArray, '/marker_obj_array', 10)
        timer_period = 0.01  # seconds
        # self.timer = self.create_timer(timer_period, self.callback)
        self.i = 0
        

    def callback(self, data):
        # success, img = self.cap.read()
        img = self.cvb.imgmsg_to_cv2(data, "bgr8")
        self.results = self.model.track(source=img,persist=True, stream=True)
        

        marker_array = MarkerArray()

        for r in self.results:
            boxes = r.boxes  # Get bounding boxes
            marker_id = 0
            for box in boxes:
                
                # text.id = 0
                if math.ceil(box.conf[0] * 100) > 50:
                    x1, y1, x2, y2 = box.xyxy[0]  # Get bounding box coordinates
                    x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])  # Convert to int
                
                    cls = int(box.cls[0])
                    classname = self.classNames[cls]
                    # Calculate the confidence of the detected object
                    confidence = math.ceil(box.conf[0] * 100) 
                    print(f'{classname}: {confidence}%')
                    
                    # Draw the bounding box from the image
                    color = (0, 255, 0)  # Default color: green

                    # Draw the rectangle on the image
                    cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
                    # Write the class name and confidence on the image
                    org = (x1, y1 - 10)  # Position the text above the bounding box
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    obj_id = 0
                    if box.id is not None:
                        obj_id = int(box.id[0]) # This is your unique tracking ID
                        
                        # Now you can use it in your text
                        cv2.putText(img, f"ID: {obj_id} {classname} {confidence:.2f}%", (x1, y1 - 10), font, 0.5, color, 2)
                        marker = Marker()
                        marker.header.frame_id = '/map'
                        marker.header.stamp = self.get_clock().now().to_msg()
                        marker.type = Marker.LINE_LIST
                        marker.ns = "boxes"
                        marker.action = marker.ADD
                        marker.scale.x = 0.1
                        marker.scale.y = 0.1
                        marker.scale.z = 0.1
                        marker.color = ColorRGBA(r=1.0, g=0.0, b=0.0, a=1.0)
                        # marker.id = 0

                        text = Marker()
                        text.header.frame_id = '/map'
                        text.header.stamp = self.get_clock().now().to_msg()
                        text.type = Marker.TEXT_VIEW_FACING

                        text.action = text.ADD
                        text.scale.x = 0.35
                        text.scale.y = 0.35
                        text.scale.z = 0.35
                        text.color = ColorRGBA(r=1.0, g=0.5, b=0.5, a=1.0)
                        text.ns = "labels"
                        marker.id = obj_id
                        marker.points = [
                        Point(x=x1/100.0, y=y1/100.0), Point(x=x1/100.0, y=y2/100.0),
                        Point(x=x1/100.0, y=y2/100.0), Point(x=x2/100.0, y=y2/100.0),
                        Point(x=x2/100.0, y=y2/100.0), Point(x=x2/100.0, y=y1/100.0),
                        Point(x=x2/100.0, y=y1/100.0), Point(x=x1/100.0, y=y1/100.0),
                        ]
                        marker.lifetime = rclpy.duration.Duration(seconds=0.2).to_msg()
                        text.id = obj_id
                        text.pose.position.x = (x1+30)/100
                        text.pose.position.y = (y1-30)/100
                        text.pose.position.z = (0.0)
                        # Detect the class name of the object
                        
                        text.text = classname
                        text.lifetime = rclpy.duration.Duration(seconds=0.2).to_msg()

                        marker_array.markers.append(marker)
                        marker_array.markers.append(text)
                # marker.points.clear()
        self.marker_pub.publish(marker_array)
        # cv2.imshow("instance-segmentation-object-tracking", img)
        self.publisher_.publish(self.cvb.cv2_to_imgmsg(img, "bgr8"))
        # Exit the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord("q"):
            return()


def main(args=None):
    rclpy.init(args=args)

    objectdetect = ObjectDetection()

    rclpy.spin(objectdetect)
    rclpy.shutdown()


if __name__ == '__main__':
    main()



# # Load a COCO-pretrained YOLO11n model

# # Run inference with the YOLO11n model on the 'bus.jpg' image
# results = model("path/to/bus.jpg")




# from ultralytics import YOLO
# import cv2
# import math
# # Initialize the camera and set the image resolution
# cap = cv2.VideoCapture(0)
# cap.set(3, 720)
# cap.set(4, 720)

# # Load our model
# model = YOLO('/home/adithya-si3510/Downloads/yolo11n.pt')

# # Define the classes we are going to detect
# classNames = [
#     'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 
#     'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 
#     'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 
#     'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 
#     'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 
#     'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 
#     'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 
#     'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 
#     'scissors', 'teddy bear', 'hair drier', 'toothbrush'
# ]

# # Capture Loop
# while True:
#     success, img = cap.read()  # Read the image from the camera
#     results = model.track(source=img,persist=True, stream=True)  # Send the image to YOLO for detection

#     # Loop over detected objects
#     for r in results:
#         boxes = r.boxes  # Get bounding boxes
#         for box in boxes:
#             if math.ceil(box.conf[0] * 100) > 50:
#                 x1, y1, x2, y2 = box.xyxy[0]  # Get bounding box coordinates
#                 x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])  # Convert to int
                
#                 # Detect the class name of the object
#                 cls = int(box.cls[0])
#                 classname = classNames[cls]
                
#                 # Calculate the confidence of the detected object
#                 confidence = math.ceil(box.conf[0] * 100) 
#                 print(f'{classname}: {confidence}%')

#                 # Draw the bounding box from the image
#                 color = (0, 255, 0)  # Default color: green
#                 if classname == 'cat':
#                     color = (128, 0, 128)  # Purple color for cats

#                 # Draw the rectangle on the image
#                 cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
                
#                 # Write the class name and confidence on the image
#                 org = (x1, y1 - 10)  # Position the text above the bounding box
#                 font = cv2.FONT_HERSHEY_SIMPLEX
#                 if box.id is not None:
#                     obj_id = int(box.id[0]) # This is your unique tracking ID
                    
#                     # Now you can use it in your text
#                     cv2.putText(img, f"ID: {obj_id} {classname} {confidence:.2f}%", (x1, y1 - 10), font, 0.5, color, 2)

#     # Create a window to display the image
#     cv2.imshow("Webcam", img)

#     # Exit loop
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()
