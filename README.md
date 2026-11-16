# ROS 2 with Computer Vision

**Intern:** Adithya S
**Stack:** ROS 2 Humble · Ubuntu 22.04 LTS · Python · OpenCV · Ultralytics YOLO · RViz2

One ROS 2 package, `vission_sys`, with four computer-vision nodes. Each node subscribes to a camera image, runs one CV operation and publishes the annotated image plus RViz markers.

| Operation | Executable | Method | Input topic |
|---|---|---|---|
| [Face Detection (Haar Cascade)](#face-detection-haar-cascade) | `faceDetect` | OpenCV Haar cascade | `/image_raw` |
| [Face Detection (DNN / ResNet-10 SSD)](#face-detection-dnn--resnet-10-ssd) | `faceDetectDNN` | OpenCV DNN, Caffe model | `/image_raw` |
| [Object Detection and Tracking (YOLO)](#object-detection-and-tracking-yolo) | `objectTracking` | Ultralytics YOLO | `/camera_depth_frame/image_raw` |
| [Color Tracking](#color-tracking) | `colorTrack` | HSV color masks | `/image_raw` |

## Contents
1. [Repository Layout](#repository-layout)
2. [Workspace Setup](#workspace-setup)
3. [Model Files (config folder)](#model-files-config-folder)
4. [Camera Source](#camera-source)
5. [Face Detection (Haar Cascade)](#face-detection-haar-cascade)
6. [Face Detection (DNN / ResNet-10 SSD)](#face-detection-dnn--resnet-10-ssd)
7. [Object Detection and Tracking (YOLO)](#object-detection-and-tracking-yolo)
8. [Color Tracking](#color-tracking)
9. [Viewing the Output](#viewing-the-output)
10. [Troubleshooting](#troubleshooting)

## Repository Layout
```
Ros_with_computer_vision/
└── src/vission_sys/
    ├── config/                      # face and YOLO model files
    ├── launch/
    │   └── facedetection.launch.py  # camera + both face detectors
    ├── vission_sys/
    │   ├── face_detection.py        # Haar cascade
    │   ├── face_detection_dnn.py    # DNN face detector
    │   ├── object_detection.py      # YOLO detection + tracking
    │   └── color_tracking.py        # blue / green / red tracking
    ├── resource/  test/  package.xml  setup.py  setup.cfg
```

## Workspace Setup

### 1. Install dependencies
```bash
sudo apt update
sudo apt install ros-humble-v4l2-camera ros-humble-cv-bridge ros-humble-rqt-image-view \
                 ros-humble-rviz2 python3-opencv python3-pip
pip3 install ultralytics pillow "numpy<2"
```

| Needed for | Package |
|---|---|
| Camera driver (`v4l2_camera_node`) | `ros-humble-v4l2-camera` |
| ROS image ↔ OpenCV conversion (`CvBridge`) | `ros-humble-cv-bridge` |
| Image processing, Haar cascade, DNN module | `python3-opencv` |
| YOLO object detection and tracking | `ultralytics` (pip) |
| Image import used by the color-tracking node | `pillow` (pip) |
| Viewing the camera and output images | `ros-humble-rqt-image-view`, `ros-humble-rviz2` |

`numpy<2` is there because the ROS Humble `cv_bridge` is built against NumPy 1.x. If `ultralytics` upgrades NumPy to 2.x, the nodes crash when they convert images.

No LaserScan/PointCloud tools, OctoMap or RTAB-Map are needed, and no package has to be cloned from Git.

### 2. Add the model files
The package will not build until the model files are in `src/vission_sys/config/`. See [Model Files](#model-files-config-folder).

### 3. Clone, build and source
```bash
git clone <your-repo-url> Ros_with_computer_vision
cd Ros_with_computer_vision
colcon build
source install/setup.bash
```
Run `source install/setup.bash` in every new terminal.

---

## Model Files (config folder)
All model files belong in `src/vission_sys/config/`. The YOLO `.pt` weights are stored with Git LFS because `yolo11x.pt` is larger than GitHub's 100 MB per-file limit. Install Git LFS before cloning, or pull the model files after cloning:

```bash
sudo apt update
sudo apt install git-lfs
git lfs install
git lfs pull
```

The `.pt` files are checked out into `src/vission_sys/config/` by Git LFS; do not put them in the ROS `install/` directory. If you need to download the YOLO11x weight manually, get `yolo11x.pt` from the [official Ultralytics assets releases](https://github.com/ultralytics/assets/releases) and save it to `src/vission_sys/config/yolo11x.pt`.

The package installs these runtime files at build time:

| File | Used by |
|---|---|
| `haarcascade_frontalface_default.xml` | Face Detection (Haar Cascade) |
| `deploy.prototxt.txt` | Face Detection (DNN) |
| `res10_300x300_ssd_iter_140000.caffemodel` | Face Detection (DNN) |
| `yolo11n.pt` | Object Detection and Tracking (YOLO; loaded by the node) |
| `yolo11x.pt` | YOLO alternative weight |
| `coco.yaml` | YOLO dataset configuration |

The config folder also contains `yolo11m.pt` and `yolo11l.pt` as alternative YOLO weights. The Haar cascade and face-detector files come from the [OpenCV repository](https://github.com/opencv/opencv); the YOLO weights come from [Ultralytics](https://github.com/ultralytics/assets/releases). The node loads `yolo11n.pt`; its `coco8.yaml` path is currently unused.

After adding or changing model files, rebuild:
```bash
colcon build --packages-select vission_sys
source install/setup.bash
```

## Camera Source
The face and color nodes read `/image_raw`. For a USB or laptop webcam, start the camera driver in its own terminal (the face-detection launch file already does this):
```bash
ros2 run v4l2_camera v4l2_camera_node
```
Check that images are coming in:
```bash
ros2 topic list            # /image_raw should be listed
ros2 topic hz /image_raw
```
In a simulation, point the nodes at your simulated camera topic with a remap (see each section).

---

## Face Detection (Haar Cascade)
Detects frontal faces with OpenCV's classic Haar cascade. Fast, runs on a CPU, but less accurate with side views and poor lighting.

| | |
|---|---|
| Executable | `faceDetect` |
| Subscribes | `/image_raw` (`sensor_msgs/Image`) |
| Publishes | `/face_detect_frame` (image with green boxes), `/face_marker` (`MarkerArray`, green rectangles, frame `map`) |
| Model | `config/haarcascade_frontalface_default.xml` |

### Launch
1. Start the camera: `ros2 run v4l2_camera v4l2_camera_node`
2. Start the detector in a new terminal:
   ```bash
   ros2 run vission_sys faceDetect
   ```
3. View the result:
   ```bash
   ros2 run rqt_image_view rqt_image_view /face_detect_frame
   ```
4. For RViz, set the Fixed Frame to `map`, add a **MarkerArray** display on `/face_marker`.

---

## Face Detection (DNN / ResNet-10 SSD)
Detects faces with a deep neural network (Caffe SSD with a ResNet-10 backbone). More accurate than Haar and shows a confidence score per face. Detections below **50%** confidence are ignored.

| | |
|---|---|
| Executable | `faceDetectDNN` |
| Subscribes | `/image_raw` |
| Publishes | `/face_detect_frame_resnet` (image with red boxes and confidence %), `/face_marker_resnet` (`MarkerArray`, red rectangles, frame `map`) |
| Models | `config/deploy.prototxt.txt`, `config/res10_300x300_ssd_iter_140000.caffemodel` |

### Launch
1. Start the camera: `ros2 run v4l2_camera v4l2_camera_node`
2. Start the detector:
   ```bash
   ros2 run vission_sys faceDetectDNN
   ```
3. View the result:
   ```bash
   ros2 run rqt_image_view rqt_image_view /face_detect_frame_resnet
   ```
4. For RViz, set the Fixed Frame to `map`, add a **MarkerArray** display on `/face_marker_resnet`.

### Run both face detectors together
The launch file starts the camera, the Haar node and the DNN node, so the two methods can be compared side by side:
```bash
ros2 launch vission_sys facedetection.launch.py
```
Then open `/face_detect_frame` and `/face_detect_frame_resnet` in `rqt_image_view`.

---

## Object Detection and Tracking (YOLO)
Detects the 80 COCO object classes with Ultralytics YOLO and tracks each object with a persistent ID (`model.track`). Only detections above **50%** confidence with a tracking ID are drawn.

| | |
|---|---|
| Executable | `objectTracking` |
| Subscribes | `/camera_depth_frame/image_raw` (the simulated camera topic) |
| Publishes | `/object_detetion_frame` (image with boxes, ID, class and confidence), `/marker_obj_array` (`MarkerArray`: red box outlines and class-name labels, frame `/map`) |
| Models | `config/yolo11n.pt` (see the note in [Model Files](#model-files-config-folder)) |

### Launch
1. Make sure an image source is publishing. For a **real webcam**, start the camera and remap the input topic:
   ```bash
   ros2 run v4l2_camera v4l2_camera_node
   ros2 run vission_sys objectTracking --ros-args -r /camera_depth_frame/image_raw:=/image_raw
   ```
   For the **simulated robot**, start your simulation and run:
   ```bash
   ros2 run vission_sys objectTracking
   ```
2. View the result:
   ```bash
   ros2 run rqt_image_view rqt_image_view /object_detetion_frame
   ```
   (The topic name is spelled `detetion` in the code.)
3. For RViz, set the Fixed Frame to `map`, add a **MarkerArray** display on `/marker_obj_array`.

The first run is slower while the model loads. A GPU speeds it up a lot but is not required.

---

## Color Tracking
Finds **blue, green and red** objects with HSV color masks. The brightness channel is boosted first, then each color is thresholded, and every contour larger than **500 px²** gets a labeled box.

| | |
|---|---|
| Executable | `colorTrack` |
| Subscribes | `/image_raw` |
| Publishes | `/colorDetection` (image with colored boxes and labels), `/color_points` (`PoseArray` of box centers), `/color_marker` (`Marker`, sphere list, frame `map`) |
| Models | none |

### Launch
1. Start the camera: `ros2 run v4l2_camera v4l2_camera_node`
2. Start the tracker:
   ```bash
   ros2 run vission_sys colorTrack
   ```
   A window called `frameB` opens with the live result (it needs a display). Press **q** in that window to quit.
3. Hold a blue, green or red object in front of the camera.
4. View the topics:
   ```bash
   ros2 run rqt_image_view rqt_image_view /colorDetection
   ros2 topic echo /color_points
   ```
5. For RViz, set the Fixed Frame to `map`, add a **PoseArray** display on `/color_points` and a **Marker** display on `/color_marker`.

---

## Viewing the Output
| What | Command |
|---|---|
| Any image topic | `ros2 run rqt_image_view rqt_image_view <topic>` |
| All running topics | `ros2 topic list` |
| Message rate | `ros2 topic hz <topic>` |
| Markers and poses | RViz2 with Fixed Frame `map` |

The marker coordinates are the pixel positions divided by 100, so they show where things are in the image, not in real-world meters.

## Troubleshooting
| Problem | Fix |
|---|---|
| `colcon build` fails with a missing file under `config/` | Add all five model files to `src/vission_sys/config/`. |
| A node says the model file is not found | Rebuild after adding the file (`colcon build --packages-select vission_sys`) and source `install/setup.bash`. |
| `objectTracking` cannot find `yolo11n.pt` | Add `yolo11n.pt` to `config/` and rebuild, or change the model name in the code. |
| No images arrive | Check `ros2 topic list` and `ros2 topic hz /image_raw`; check the camera device (`/dev/video0`) and permissions. |
| `objectTracking` shows nothing | It listens to `/camera_depth_frame/image_raw`; remap it to your camera topic as shown above. |
| Crash while converting images (NumPy error) | `pip3 install "numpy<2"`. |
| RViz shows no markers | Set the Fixed Frame to `map` and use the right topic in the display. |
# Ros_with_computer_vision
