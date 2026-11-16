import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'vission_sys'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        ('share/' + package_name+'/config', ['config/haarcascade_frontalface_default.xml']),
        ('share/' + package_name+'/config', ['config/res10_300x300_ssd_iter_140000.caffemodel']),
        ('share/' + package_name+'/config', ['config/deploy.prototxt.txt']),
        ('share/' + package_name+'/config', ['config/yolo11n.pt']),
        ('share/' + package_name+'/config', ['config/yolo11x.pt']),
        ('share/' + package_name+'/config', ['config/coco.yaml'])
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='adithya-si3510',
    maintainer_email='adithya-si3510@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'faceDetect = vission_sys.face_detection:main',
            'faceDetectDNN = vission_sys.face_detection_dnn:main',
            'objectTracking = vission_sys.object_detection:main',
            'colorTrack = vission_sys.color_tracking:main'
        ],
    },
)
