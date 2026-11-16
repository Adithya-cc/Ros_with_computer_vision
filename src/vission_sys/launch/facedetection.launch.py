from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    haar_cascade = Node(
        package='vission_sys',
        executable='faceDetect',
        name='haar_face_node',
        output='screen'
    )

    resnet = Node(
        package='vission_sys',
        executable='faceDetectDNN',
        name='dnn_face_node',
        output='screen'
    )

    camera = Node(
        package='v4l2_camera',
        executable='v4l2_camera_node',
        name='camera',
        output='screen'
    )

    return LaunchDescription([
        camera,
        haar_cascade,
        resnet
    ])