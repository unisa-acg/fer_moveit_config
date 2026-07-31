# fer_moveit_config

This package contains the FER robot configuration used by the Automatic Control Group.
It has been created through the MoveIt! Setup Assistant and then manually modified.
Since the [`.setup_assistant`](./.setup_assistant) file does not get modified upon manual modifications, additional functions shall be configured by manually editing the available launch and config files.
The [`.setup_assistant`](./.setup_assistant) file is retained to allow the `MoveItConfigBuilder` to work properly, e.g. to load a custom SRDF file instead of the default `<config_dir_path>/<robot_name>.srdf` file.

Some of the modifications applied to this package are listed here below.
The list is not exhaustive and it cannot be, as this package is likely to evolve with time and there is no reason to keep track of all the modifications with respect to the Setup Assistant's baseline in this Readme:

* Default planners configurations that are not provided with this package are read from the official `moveit_configs_utils` package by the [`move_group.launch.py`](./launch/move_group.launch.py) (also called by [`demo.launch.py`](./launch/demo.launch.py)).
* [`move_group.launch.py`](./launch/move_group.launch.py) supports selecting the MoveIt controller mapping file through the `controllers_file` argument.
  [`moveit_fer.launch.py`](./launch/moveit_fer.launch.py) defaults to `config/moveit_controllers.yaml`; pass `moveit_controllers_file:=config/moveit_controllers_real.yaml` to also enable gripper execution.
* Two configurations are provided for RViz, namely [`moveit.rviz`](./config/moveit.rviz) (default) and [`ros2_control_demo.rviz`](./config/ros2_control_demo.rviz).
    The former loads the MotionPlanning plugin, while the latter does not include planning plugins.
* [`gz_params_bridge.yaml`](./config/gz_params_bridge.yaml) has been added to use the simulator clock in the ROS2 ecosystem (needed by Gazebo-based demos).

## Usage with Motion Planning plugin

In order to execute a demo with RViz's **MotionPlanning** plugin, run

```bash
ros2 launch fer_moveit_config demo.launch.py
```

You can switch between the `fer_arm` and `fer_hand` groups.

## Trajectory execution

Together with planning, this package supports trajectory execution through `ros2_control`.
Several configurations are available, described here below.

### Execution with mock hardware and MoveIt! reference generator

The [`demo.launch.py`](./launch/demo.launch.py) demo provides a basic execution demo using mock hardware, loading a `ros2_control_node` (identified by `ros2 node list` as `/controller_manager`) and spawning a joint trajectory controller.
In this case, a `moveit_simple_controller_manager` is also instantiated, which, despite its name, provides action clients connecting to the controllers loaded by the actual controller manager.
For more information, please refer to [this tutorial](https://moveit.github.io/moveit_tutorials/doc/controller_configuration/controller_configuration_tutorial.html).

### Execution with mock hardware and external reference generator

If the user intends to provide reference generators outside of MoveIt!, they can rely on the following demo:

```bash
ros2 launch fer_moveit_config ros2_control_demo.launch.py
```

This demo loads a forward position controller for the arm and a gripper action controller for the hand.

#### Arm control

Position references can be sent to the arm through the forward position controller using an external reference generator, such as `ros2 topic pub`:

```bash
ros2 topic pub /fer_forward_position_controller/commands std_msgs/msg/Float64MultiArray "data: [0.0, 0.0, 0.0, -0.7, 0.0, 0.3, 0.0]"
```

#### Hand control

Gripper commands can be sent through the gripper action controller using `ros2 action send_goal`:

```bash
ros2 action send_goal /hand_controller/gripper_cmd control_msgs/action/ParallelGripperCommand '
command:
    header:
        stamp:
            sec: 0
            nanosec: 0
        frame_id: ""
    name:
        - "fer_finger_joint1"
    position:
        - 0.04
    effort:
        - 100.0
'
```

The position is in meters (recommended operating range: > 0.0 to 0.04 for FER; very small positive values such as 1e-10 are accepted, while exactly 0.0 may be rejected), and effort is in Newtons.

#### Notes

When using mock hardware, remember that commands are just copied in the state, but no simulation really happens.
Therefore, if switching to a velocity controller, the user shall not expect the mock robot to move.
However, its state, as read by `/joint_states`, shall update according to the commands.

### Execution with Gazebo

This demo simulates the FER robot in Gazebo using the `gz_ros2_control::GazeboSimROS2ControlPlugin` plugin.
Unlike the mock hardware setup, Gazebo manages the controller manager directly via the plugin, while `gz_ros2_control/GazeboSimSystem` provides realistic physics simulation instead of command pass-through.

To launch the demo, run

```bash
ros2 launch fer_moveit_config gazebo_ros2_control_demo.launch.py
```

#### Arm control (Gazebo)

The forward position controller is loaded by default. Position references can be sent using `ros2 topic pub`:

```bash
ros2 topic pub /fer_forward_position_controller/commands std_msgs/msg/Float64MultiArray '
data:
  - 0.0
  - 0.0
  - 0.0
  - -0.7
  - 0.0
  - 0.3
  - 0.0
'
```

To use a different controller (e.g., velocity), pass the `controller` parameter at launch time:

```bash
ros2 launch fer_moveit_config gazebo_ros2_control_demo.launch.py controller:=fer_forward_velocity_controller
```

#### Hand control (Gazebo)

Gripper commands can be sent through the gripper action controller using `ros2 action send_goal`:

```bash
ros2 action send_goal /hand_controller/gripper_cmd control_msgs/action/ParallelGripperCommand '
command:
  header:
    stamp:
      sec: 0
      nanosec: 0
    frame_id: ""
  name:
    - "fer_finger_joint1"
  position:
    - 0.02
  effort:
    - 100.0
'
```

The position is in meters (recommended operating range: > 0.0 to 0.04 for FER; very small positive values such as 1e-10 are accepted, while exactly 0.0 may be rejected), and effort is in Newtons.

#### Notes (Gazebo)

* The FER arm has 7 joints, so position and velocity commands use 7-element arrays.
* The gripper fingers cannot be velocity-commanded; only position control is available.
* For the gripper position command, use strictly positive values. In practice, very small values (e.g., 1e-10) are valid, while exactly 0.0 can fail depending on the controller/simulation state.
* **In Gazebo, only `fer_finger_joint1` is actively controlled because the `fer.ros2_control.xacro` file does not declare `fer_finger_joint2`**.
  The second finger remains static and does not mirror the motion of the first finger.
  To enable bidirectional gripper motion, add `fer_finger_joint2` as a mimic joint in the `fer.ros2_control.xacro` configuration file.

### Execution with Gazebo and MoveIt! planning system

This package also offers a complete planning and simulation setup with the following demo:

```bash
ros2 launch fer_moveit_config moveit_gazebo_ros2_control_demo.launch.py
```

Here, the user can plan trajectories through the MoveIt! planning pipeline by using the `MotionPlanning` plugin in RViz.
Execution is performed on the Gazebo robot through the `moveit_simple_controller_manager`, which uses the loaded joint trajectory controller.

## Working with the real robot

### Planning and execution with the real robot

Make sure the mode switch button is **disengaged** (blue light on the robot base), then launch:

```bash
ros2 launch fer_moveit_config moveit_fer.launch.py robot_ip:=192.168.1.1
```

This starts the Franka bringup, `move_group`, and RViz with the `MotionPlanning` plugin (arm only, no gripper execution).
To also enable gripper execution via the `franka_gripper` interface (`/fer_gripper/gripper_action`), pass:

```bash
ros2 launch fer_moveit_config moveit_fer.launch.py robot_ip:=192.168.1.1 moveit_controllers_file:=moveit_controllers_real.yaml
```

**Planning pipeline:** by default MoveIt! uses the Pilz planner; switch to **OMPL** from the RViz panel dropdown before planning `fer_arm` and `fer_hand` trajectories.

A **real-time kernel (PREEMPT_RT)** is strongly recommended for deterministic controller scheduling.

## Launch File Parameters

This section describes the command-line arguments supported by the launch files in this package.

### Common Parameters

The launch files described in this document, with the exception of [`moveit_fer.launch.py`](./launch/moveit_fer.launch.py), support the following two command-line arguments:

* **`tf_prefix`**: Specifies the prefix to be applied to all TF frames and joint names.
    The default value is `fer_`, which identifies the *FER* robot instance used in our setup.

    Other supported prefixes correspond to models developed by **Franka Emika**, including:

    * `fer_`
    * `fp3_`
    * `fr3_`
    * `fr3_duo_`
    * `fr3v2_`

    The selected prefix must match the naming used in the configuration files for controllers and motion planning.

* **`hand`**: A boolean flag that enables or disables the presence of the robot’s hand (gripper).
    The default value is `true`.
    If set to `false`, the controller configuration files must be appropriately adjusted to remove references to the hand joints and actions.

* **`moveit_controllers_file`**: Filename of the MoveIt controller mapping yaml inside `fer_moveit_config/config`, used by `move_group.launch.py`.
  The default value is `moveit_controllers.yaml` (arm only, no gripper execution).
  Pass `moveit_controllers_real.yaml` to also enable gripper execution via the `franka_gripper` interface.

### Simulation-Specific Parameter

[`move_group.launch.py`](./launch/move_group.launch.py) additionally supports the following parameter:

* **`gazebo`**: A boolean flag that must be set to `true` when running the robot in the **Gazebo** simulator.
    It enables specific simulation-related configurations.
    This parameter should be omitted or set to `false` when deploying on real hardware or using alternative simulation environments.

## Known issues

If the `ros2_control.xacro` file contains both effort interfaces and other interfaces (e.g., position, velocity), the simulation with the latter interfaces does not work.
This issue is explained in [this issue](https://github.com/ros-controls/gz_ros2_control/issues/343).
A workaround for this is to create a separate Xacro file for the effort interfaces (see [this file](./config/fer.ros2_control_effort.xacro)) and load it only when necessary.

The following startup errors and warnings are expected because they concern parts of the system that are not configured:

```text
[move_group-3] [WARN] [1760204433.874619827] [move_group.moveit.moveit.ros.occupancy_map_monitor]: Resolution not specified for Octomap. Assuming resolution = 0.1 instead
[move_group-3] [ERROR] [1760204433.874649509] [move_group.moveit.moveit.ros.occupancy_map_monitor]: No 3D sensor plugin(s) defined for octomap updates
[rviz2-4] [ERROR] [1760204438.298613178] [moveit_1911965155.moveit.ros.motion_planning_frame]: Action server: /recognize_objects not available
```

The following startup warning is not expected, but the same behavior arises in official MoveIt!2 tutorials:

```text
[rviz2-4] Warning: class_loader.impl: SEVERE WARNING!!! A namespace collision has occurred with plugin factory for class rviz_default_plugins::displays::InteractiveMarkerDisplay. New factory will OVERWRITE existing one. This situation occurs when libraries containing plugins are directly linked against an executable (the one running right now generating this message). Please separate plugins out into their own library or just don't link against the library and use either class_loader::ClassLoader/MultiLibraryClassLoader to open.
[rviz2-4] [WARN] [1760204457.198612747] [interactive_marker_display_96723130432880]: Server not available during initialization, resetting
```

The following shutdown errors and warnings are not expected, but the same behavior arises in official MoveIt!2 tutorials:

```text
[ros2_control_node-5] [ERROR] [1760204498.260273828] [controller_manager.pal_statistics]: Exception in publisher thread: context cannot be slept with because it's invalid!. Aborting!
[ros2_control_node-5] Failed to publish log message to rosout: publisher's context is invalid, at ./src/rcl/publisher.c:423
[rviz2-4] [WARN] [1760204498.263045578] [interactive_marker_display_96723130432880]: Server not available while running, resetting
[rviz2-4]
[rviz2-4] >>> [rcutils|error_handling.c:108] rcutils_set_error_state()
[rviz2-4] This error state is being overwritten:
[rviz2-4]
[rviz2-4]   'rcl node's context is invalid, at ./src/rcl/node.c:428'
[rviz2-4]
[rviz2-4] with this new error message:
[rviz2-4]
[rviz2-4]   'publisher's context is invalid, at ./src/rcl/publisher.c:389'
[rviz2-4]
[rviz2-4] rcutils_reset_error() should be called after error handling to avoid this.
[rviz2-4] <<<
```
