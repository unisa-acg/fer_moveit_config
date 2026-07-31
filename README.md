# FER MoveIt! config in ROS2

This repository supports the paper

> "Keeping the Franka Emika Panda alive: a ROS~2 stack\\with a reliable position interface", Submitted to ICINCO 2026

## Getting Started

Let's start by creating and populating the colcon workspace with the `fer_moveit_config` package suite and its dependencies.
For the time being, you will need to download the repositories manually to ensure the authors' anonymity.

To populate the workspace with the package suite and its dependencies, under your workspace's `src` folder, follow these instructions:

```bash
wget https://anonymous.4open.science/api/repo/libfranka-636F/zip -O libfranka.zip
wget https://anonymous.4open.science/api/repo/franka_ros2-AF7B/zip -O franka_ros2.zip
wget https://anonymous.4open.science/api/repo/franka_description-7ECD/zip -O franka_description.zip
unzip libfranka.zip -d libfranka
unzip franka_ros2.zip -d franka_ros2
unzip franka_description.zip -d franka_description
cd ..
cd src/libfranka/
git clone https://github.com/tingelst/libfranka-common.git common
cd -
```

Then, you can safely build everything with colcon: move to your workspace's root folder and run:

```bash
colcon build --packages-up-to fer_moveit_config --cmake-args -DCMAKE_BUILD_TYPE=Release
```

Please refer to the [package's readme](./fer_moveit_config/README.md) for instructions on how to execute demos.

## Contributing

Please see our [contribution guidelines](./CONTRIBUTING.md).

## Real-time kernel installation

Please refer to [this guide](./REALTIME.md) for useful links and information about installing a real-time kernel.

&copy; *2026 Automatic Control Group (UNISA)*
