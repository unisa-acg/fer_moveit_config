from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution


def launch_setup(context, *args, **kwargs):
    THIS_PACKAGE_NAME = "acg_resources_fer_moveit_config"
    robot_ip = LaunchConfiguration("robot_ip")
    hand = LaunchConfiguration("hand")
    moveit_controllers_file = LaunchConfiguration("moveit_controllers_file")
    controller = LaunchConfiguration("controller")
    async_interface = LaunchConfiguration("async_interface")
    filter_commands = LaunchConfiguration("filter_commands")
    joint_position_rate_limit = LaunchConfiguration("joint_position_rate_limit")
    joint_position_low_pass_filter = LaunchConfiguration(
        "joint_position_low_pass_filter"
    )
    position_control_gain = LaunchConfiguration("position_control_gain")

    franka_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                PathJoinSubstitution(
                    [FindPackageShare("franka_bringup"), "launch", "franka.launch.py"]
                )
            ]
        ),
        launch_arguments={
            "robot_ip": robot_ip,
            "arm_id": "fer",
            "load_gripper": hand,
            "use_rviz": "false",
            "controller_file_package": THIS_PACKAGE_NAME,
            "controller_file_path": "config/ros2_controllers_real.yaml",
            "initial_joint_controller": controller,
            "async_interface": async_interface,
            "filter_commands": filter_commands,
            "joint_position_rate_limit": joint_position_rate_limit,
            "joint_position_low_pass_filter": joint_position_low_pass_filter,
            "position_control_gain": position_control_gain,
        }.items(),
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        output="log",
        arguments=[
            "-d",
            PathJoinSubstitution(
                [
                    FindPackageShare(THIS_PACKAGE_NAME),
                    "config",
                    "moveit.rviz",
                ]
            ),
        ],
    )

    move_group_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                PathJoinSubstitution(
                    [
                        FindPackageShare(THIS_PACKAGE_NAME),
                        "launch",
                        "move_group.launch.py",
                    ]
                )
            ]
        ),
        launch_arguments={
            "hand": hand,
            "moveit_controllers_file": moveit_controllers_file,
        }.items(),
    )

    plotjuggler = Node(
        package="plotjuggler",
        executable="plotjuggler",
        name="plotjuggler",
        arguments=[
            "-l",
            PathJoinSubstitution(
                [FindPackageShare(THIS_PACKAGE_NAME), "config", "fer.xml"]
            ),
        ],
    )

    return [franka_bringup_launch, rviz_node, move_group_launch, plotjuggler]


def generate_launch_description():
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "robot_ip", description="IP address by which the robot can be reached."
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "hand",
            description="Load the hand?",
            default_value="false",
            choices=("false", "true"),
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "moveit_controllers_file",
            default_value="moveit_controllers.yaml",
            description="MoveIt controller mapping yaml filename inside acg_resources_fer_moveit_config/config.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "controller",
            default_value="fer_arm_trajectory_controller_effort",
            description="Joint trajectory controller to start.",
            choices=(
                "fer_arm_trajectory_controller_effort",
                "fer_arm_trajectory_controller_position",
            ),
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "async_interface",
            default_value="true",
            description="Use an async hardware interface?",
            choices=("false", "true"),
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "filter_commands",
            default_value="false",
            description="Filter position commands?",
            choices=("false", "true"),
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "joint_position_rate_limit",
            default_value="true",
            description="Use rate limiter on position commands?",
            choices=("false", "true"),
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "joint_position_low_pass_filter",
            default_value="true",
            description="Use a low pass filter on position commands?",
            choices=("false", "true"),
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "position_control_gain",
            default_value="0.001",
            description="Position control gain",
        )
    )
    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
