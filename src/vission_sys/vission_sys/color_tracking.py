import cv2
from PIL import Image

import numpy  as np
import rclpy
from sensor_msgs.msg import Image
from rclpy.node import Node
from cv_bridge import CvBridge, CvBridgeError
from geometry_msgs.msg import Pose, PoseArray, Point
from visualization_msgs.msg import Marker

class ColorDetection(Node):

    def __init__(self):
        super().__init__('color_detection_node')
        self.get_logger().info("color detection node is online!")
        self.sub = self.create_subscription(Image,"/image_raw",self.callback,10)
        self.pub = self.create_publisher(Image, '/colorDetection', 10)
        self.point = self.create_publisher(PoseArray, '/color_points', 10)
        self.mk_pub = self.create_publisher(Marker, '/color_marker', 10)
        self.cv = CvBridge()
    def callback(self, data):
        try:
            frame = self.cv.imgmsg_to_cv2(data, 'bgr8')
        except CvBridgeError as e:
            print(e)
            return
        hsvImage = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        value_channel = hsvImage[:, :, 2]

        # Increase the intensity by multiplying with the factor
        increased_value_channel = np.clip(value_channel * 1.5, 0, 255).astype(np.uint8)
        hsvImage[:, :, 2] = increased_value_channel
            
            
        lower_blue = np.array([90,70,50])    # [ 92 110  55] [139 255 255]
        upper_blue = np.array([130,255,255])
        mask = cv2.inRange(hsvImage, lower_blue, upper_blue)

        
        lower_green = np.array([40, 40,40])    # [  0 105  76] [179 255 255]
        upper_green = np.array([70, 255,255])
        green_mask = cv2.inRange(hsvImage, lower_green, upper_green)

        lower_red1 = np.array([0, 130, 70])  #[ 0 129  64] [ 13 255 255]
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 120, 60]) #[164 212  64] [179 255 255]
        upper_red2 = np.array([180, 255, 255])

        mask1 = cv2.inRange(hsvImage, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsvImage, lower_red2, upper_red2)

        red_mask = mask1 + mask2

        resultB = cv2.bitwise_and(frame,frame,mask=mask)
        resultG = cv2.bitwise_and(frame,frame,mask=green_mask)
        resultR = cv2.bitwise_and(frame,frame,mask=red_mask)
        

        contureB, _ = cv2.findContours(mask,mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_NONE)
        contureG, _ = cv2.findContours(green_mask,mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_NONE)
        contureR, _ = cv2.findContours(red_mask,mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_NONE)
        points_cor = PoseArray()
        for con in contureB:
            area = cv2.contourArea(con)
            
            if area > 500:
                x, y, w, h = cv2.boundingRect(con)
                cv2.rectangle(frame, (x,y), (x+w,y+h), (155,0,0), 2)
                point = Pose()
                point.position.x = float(x+w/2)/100
                point.position.y = float(y+h/2)/100
                point.position.z = 0.0
                cv2.putText(frame, f"(Blue)", (x,y+10),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
                points_cor.poses.append(point)    
        for con in contureG:
            area = cv2.contourArea(con)

            if area > 500:
                x, y, w, h = cv2.boundingRect(con)
                cv2.rectangle(frame, (x,y), (x+w,y+h), (0,155,0), 2)
                point = Pose()
                point.position.x = float(x+w/2)/100
                point.position.y = float(y+h/2)/100
                point.position.z = 0.0
                cv2.putText(frame, f"(Green)", (x,y+10),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
                points_cor.poses.append(point)
        for con in contureR:
            area = cv2.contourArea(con)

            if area > 500:
                x, y, w, h = cv2.boundingRect(con)
                cv2.rectangle(frame, (x,y), (x+w,y+h), (0,0,155), 2)
                point = Pose()
                point.position.x = float(x+w/2)/100
                point.position.y = float(y+h/2)/100
                point.position.z = 0.0
                cv2.putText(frame, f"(Red)", (x,y+10),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
                points_cor.poses.append(point)


        marker= Marker()
        marker.header.frame_id = 'map'
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.type = Marker.SPHERE_LIST
        marker.scale.x = 0.5
        marker.scale.y = 0.5
        marker.scale.z = 0.5
        marker.color.r = 1.0
        marker.color.g = 0.0
        marker.color.b = 0.0
        marker.color.a = 1.0
        marker.action = Marker.ADD
        pose = points_cor.poses
        
        for pos in (pose):
            pt = Point()
            pt.x = pos.position.x
            pt.y = pos.position.y
            pt.z = pos.position.z
            marker.points.append(pt)
        marker.lifetime = rclpy.duration.Duration(seconds = 0.03).to_msg()
        
        cv2.imshow('frameB', frame)
        # cv2.imshow('frameR', resultG)

        msg = Image()
        msg = self.cv.cv2_to_imgmsg(frame, 'bgr8')
        self.point.publish(points_cor)
        self.pub.publish(msg)
        print("published")
        self.mk_pub.publish(marker)

        if cv2.waitKey(1) & 0xFF == ord('q'):

            cv2.destroyAllWindows()
            rclpy.shutdown()
            return
    

def main(args = None):
    rclpy.init(args=args)
    rclpy.spin(ColorDetection())

    rclpy.shutdown()


if __name__ == "__main__":
    main()

# yellow = [0, 255, 255]  # yellow in BGR colorspace
# cap = cv2.VideoCapture(0)
# while True:
    
#     # if bbox is not None:
#     #     x1, y1, x2, y2 = bbox

#     #     frame = cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 5)



    


#     # img = cv2.drawContours(frame, contureB, -1, (255,0,0), thickness= 2, lineType= cv2.LINE_AA)
#     # img = cv2.drawContours(frame, contureR, -1, (0,0,255), thickness= 2, lineType= cv2.LINE_AA)
#     cv2.imshow('frameB', frame)
#     cv2.imshow('frameR', resultG)

#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break


