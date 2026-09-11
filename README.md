# FER MoveIt! config in ROS2

[Code](https://github.com/unisa-acg/fer_moveit_config) | [Website](https://sites.google.com/unisa.it/fer-ros2/home) | [Videos](https://sites.google.com/unisa.it/fer-ros2/applications)

This repository supports the paper

> A. Langella, D. Risi, V. Petrone, E. Ferrentino, P. Chiacchio, "Keeping the Franka Emika Panda alive: a ROS 2 stack with a reliable position interface", 23rd International Conference on Informatics, Automation and Robotics (ICINCO), 2026, Accepted for publication, DOI: [10.48550/arXiv.2608.19740](https://doi.org/10.48550/arXiv.2608.19740)

## Getting Started

### Dependencies

#### Source dependencies

Let's start by creating and populating the colcon workspace with the `fer_moveit_config` package suite and its dependencies.
For the time being, you will need to download the repositories manually to ensure the authors' anonymity.

To populate the workspace with the package suite and its dependencies, under your workspace's `src` folder, follow these instructions:

```bash
git clone -b feature/fer_async_hardware_interface_to_jazzy https://github.com/unisa-acg/franka_ros2.git
git clone -b feature/fer_async_hw_interface https://github.com/unisa-acg/franka_description.git
git clone -b active-control-backport https://github.com/unisa-acg/libfranka.git
cd libfranka/
git clone https://github.com/tingelst/libfranka-common.git common
cd ../
```

#### System dependencies

Run

```bash
rosdep install --from-paths src -i
```

to install all system dependencies.

### Build

When all dependencies are installed, you can safely build everything with colcon: move to your workspace's root folder and run:

```bash
colcon build --packages-up-to fer_moveit_config --cmake-args -DCMAKE_BUILD_TYPE=Release
```

### Demos

Please refer to the [package's readme](./fer_moveit_config/README.md) for instructions on how to execute demos.

## Contributing

Please see our [contribution guidelines](./CONTRIBUTING.md).

## Real-time kernel installation

Please refer to [this guide](./REALTIME.md) for useful links and information about installing a real-time kernel.

&copy; *2026 Automatic Control Group (UNISA)*
