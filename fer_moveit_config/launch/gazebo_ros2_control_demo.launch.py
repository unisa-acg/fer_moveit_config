import os

from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
    RegisterEventHandler,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue


THIS_PACKAGE_NAME = "acg_resources_fer_moveit_config"


def launch_setup(context, *args, **kwargs):
    # Value argument from launch configuration
    runtime_config_package = LaunchConfiguration("runtime_config_package")
    tf_prefix = LaunchConfiguration("tf_prefix")
    hand = LaunchConfiguration("hand")
    initial_positions_package = LaunchConfiguration("initial_positions_package")
    initial_positions_file = LaunchConfiguration("initial_positions_file")
    ros2_controllers_file = LaunchConfiguration("ros2_controllers_file")
    enable_effort_interfaces = LaunchConfiguration("enable_effort_interfaces")
    robot_state_publisher_frequency = LaunchConfiguration(
        "robot_state_publisher_frequency"
    )
    gazebo_gui_config_file = LaunchConfiguration("gazebo_gui_config_file")
    gazebo_world_package = LaunchConfiguration("gazebo_world_package")
    gazebo_world_file = LaunchConfiguration("gazebo_world_file")
    controller = LaunchConfiguration("controller")
    use_rviz = LaunchConfiguration("use_rviz")
    rviz_config_package = LaunchConfiguration("rviz_config_package")
    rviz_config_file = LaunchConfiguration("rviz_config_file")

    # Get initial positions file path
    initial_positions = PathJoinSubstitution(
        [FindPackageShare(initial_positions_package), "config", initial_positions_file]
    )

    # Get controllers file path
    ros2_controllers = PathJoinSubstitution(
        [FindPackageShare(runtime_config_package), "config", ros2_controllers_file]
    )

    # Get URDF via xacro
    xacro_file = PathJoinSubstitution(
        [
            FindPackageShare(THIS_PACKAGE_NAME),
            "config",
            "fer.urdf.xacro",
        ]
    )

    # Load robot description without mock hardware
    robot_description = Command(
        [
            FindExecutable(name="xacro"),
            " ",
            xacro_file,
            " ",
            "tf_prefix:=",
            tf_prefix,
            " ",
            "hand:=",
            hand,
            " ",
            "initial_positions_file:=",
            initial_positions,
            " ",
            "ros2_controllers_file:=",
            ros2_controllers,
            " ",
            "use_mock_hardware:=",
            "false",
            " ",
            "enable_effort_interfaces:=",
            enable_effort_interfaces,
            " ",
            "gazebo:=",
            "true",
        ]
    )

    # Prepare Gazebo resources: this is needed by Gazebo to find the meshes referenced by the URDF
    gazebo_resource_path = AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH",
        os.sep.join(
            FindPackageShare("franka_description").perform(context).split(os.sep)[:-1]
        ),
    )

    # Include Gazebo launch file to launch its environment
    launches = []
    gazebo_launch_file = PathJoinSubstitution(
        [FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"]
    )
    gazebo_gui_config = PathJoinSubstitution(
        [FindPackageShare(THIS_PACKAGE_NAME), "config", gazebo_gui_config_file]
    )
    gazebo_world = (
        PathJoinSubstitution(
            [FindPackageShare(gazebo_world_package), gazebo_world_file]
        )
        if gazebo_world_package.perform(context)
        else gazebo_world_file
    )
    launches.append(
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(gazebo_launch_file),
            launch_arguments=[
                (
                    "gz_args",
                    [
                        " -r -v 4 --gui-config ",
                        gazebo_gui_config,
                        " ",
                        gazebo_world,
                    ],
                )
            ],
        )
    )

    # Define all nodes that have to be launched

    # Start the robot state publisher
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[
            {"robot_description": ParameterValue(robot_description, value_type=str)},
            {"publish_frequency": robot_state_publisher_frequency},
        ],
    )

    # Spawn the model in Gazebo. This also loads the plugin and starts the control node.
    # At the time of writing this script, the 'create' command does not allow spawning
    # the robot at a specific joint configuration
    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-string",
            robot_description,
            "-name",
            "fer",
            "-allow_renaming",
            "true",
        ],
    )

    # Spawn controllers
    controllers = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            controller,
            "hand_controller",
            "-c",
            "/controller_manager",
        ],
    )

    # Delay `joint_state_broadcaster` and `hand_controller` start after spawning the model in Gazebo
    delay_controllers_after_gz_spawn = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=gz_spawn_entity,
            on_exit=[controllers],
        )
    )

    # Load RViz
    rviz_config = PathJoinSubstitution(
        [FindPackageShare(rviz_config_package), "config", rviz_config_file]
    )
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config],
        condition=IfCondition(use_rviz),
    )
    delay_rviz_after_joint_state_broadcaster = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=controllers,
            on_exit=[rviz_node],
        )
    )

    # This file contains the parameters for the bridge between ROS2 and Gazebo Sim
    gz_params_bridge = PathJoinSubstitution(
        [
            FindPackageShare(THIS_PACKAGE_NAME),
            "config",
            "gz_params_bridge.yaml",
        ]
    )
    ros_gz_parameter_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        parameters=[{"config_file": gz_params_bridge}],
        output="screen",
    )

    nodes = [
        gz_spawn_entity,
        robot_state_publisher,
        delay_controllers_after_gz_spawn,
        delay_rviz_after_joint_state_broadcaster,
        ros_gz_parameter_bridge,
    ]

    return [gazebo_resource_path] + launches + nodes


def generate_launch_description():
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "runtime_config_package",
            default_value=THIS_PACKAGE_NAME,
            description="Package with the controllers' configuration.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "tf_prefix", default_value="fer", description="Prefix for the tf names."
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "hand",
            default_value="true",
            description="Flag to enable the hand of the robot.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "initial_positions_package",
            default_value=THIS_PACKAGE_NAME,
            description="Package with the initial positions of the robot joints.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "initial_positions_file",
            default_value="initial_positions.yaml",
            description="File with the initial positions of the robot joints under `initial_positions_package`/config.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "ros2_controllers_file",
            default_value="ros2_controllers.yaml",
            description="YAML file with the parameters for the controllers under `runtime_config_package`/config.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "enable_effort_interfaces",
            default_value="false",
            description="Enable effort interfaces for the robot.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "robot_state_publisher_frequency",
            default_value="1000.0",
            description="The frequency (in Hz) at which the robot_state_publisher publishes.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "gazebo_gui_config_file",
            default_value="gz_gui.config",
            description="The Gazebo GUI config file under this package's 'config' folder.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "gazebo_world_package",
            default_value="",
            description="Package with the Gazebo world file.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "gazebo_world_file",
            default_value="empty.sdf",
            description="The path to the Gazebo world file inside the "
            "`gazebo_world_package`. If not specified, the default empty world is used.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "controller",
            default_value="fer_forward_position_controller",
            description="Load the forward position controller by default.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_rviz",
            default_value="true",
            choices=("false", "true"),
            description="Start RViz2 automatically with this launch file.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "rviz_config_package",
            default_value=THIS_PACKAGE_NAME,
            description="Package with the RViz config file.",
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "rviz_config_file",
            default_value="ros2_control_demo.rviz",
            description="RViz config file to use under `rviz_config_package`/config.",
        )
    )

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
