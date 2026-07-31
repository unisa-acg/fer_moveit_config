import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.conditions import IfCondition
from launch.actions import (
    DeclareLaunchArgument,
    OpaqueFunction,
    RegisterEventHandler,
    IncludeLaunchDescription,
    GroupAction,
)
from launch.substitutions import (
    Command,
    FindExecutable,
    PathJoinSubstitution,
    LaunchConfiguration,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.event_handlers import OnProcessExit

from launch_ros.actions import Node, SetParameter
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue


def launch_setup(context, *args, **kwargs):

    ROBOT_NAME = "fer"
    GAZEBO_FLAG = "true"

    # Value argument from launch configuration
    gui = LaunchConfiguration("gui")
    robot_state_publisher_frequency = LaunchConfiguration(
        "robot_state_publisher_frequency"
    )
    gazebo_world_package = LaunchConfiguration("gazebo_world_package")
    gazebo_world_file_path = LaunchConfiguration("gazebo_world_file_path")

    # Get URDF via xacro
    xacro_file = PathJoinSubstitution(
        [
            FindPackageShare("acg_resources_fer_moveit_config"),
            "config",
            "fer.urdf.xacro",
        ]
    )

    robot_description_content = Command(
        [
            FindExecutable(name="xacro"),
            " ",
            xacro_file,
            " ",
            "use_mock_hardware:=false",
            " ",
            "gazebo:=",
            GAZEBO_FLAG,
            " ",
            "hand:=",
            LaunchConfiguration("hand"),
        ]
    )
    robot_description = {
        "robot_description": ParameterValue(robot_description_content, value_type=str)
    }
    robot_state_publisher_frequency = {
        "publish_frequency": LaunchConfiguration("robot_state_publisher_frequency")
    }

    rviz_config_file = PathJoinSubstitution(
        [
            FindPackageShare("acg_resources_fer_moveit_config"),
            "config",
            "moveit_gazebo.rviz",
        ]
    )

    # Prepare Gazebo resources and launch path
    os.environ["GZ_SIM_RESOURCE_PATH"] = (
        get_package_share_directory("franka_description") + "/.."
    )

    gazebo_launch_file = PathJoinSubstitution(
        [FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"]
    )

    # Setup parameter_bridge between ROS2 and Gazebo to broadcast Gazebo clock
    gz_params_bridge = PathJoinSubstitution(
        [
            FindPackageShare("acg_resources_fer_moveit_config"),
            "config",
            "gz_params_bridge.yaml",
        ]
    ).perform(context)

    # Prepare other launch paths
    move_group_launch_file = PathJoinSubstitution(
        [
            FindPackageShare("acg_resources_fer_moveit_config"),
            "launch",
            "move_group.launch.py",
        ]
    )

    rviz_launch_file = PathJoinSubstitution(
        [
            FindPackageShare("acg_resources_fer_moveit_config"),
            "launch",
            "moveit_rviz.launch.py",
        ]
    )

    # Include launch files in this one
    launches = []

    gazebo_world = (
        PathJoinSubstitution(
            [FindPackageShare(gazebo_world_package), gazebo_world_file_path]
        )
        if gazebo_world_package.perform(context)
        else gazebo_world_file_path
    ).perform(context)

    launches.append(
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(gazebo_launch_file),
            launch_arguments=[("gz_args", ["-r -v 4 " + gazebo_world])],
        )
    )

    move_group_launch_description = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(move_group_launch_file),
        launch_arguments=[
            ("moveit_manage_controllers", "false"),
            ("gazebo", GAZEBO_FLAG),
        ],
    )

    rviz_launch_description = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(rviz_launch_file),
        launch_arguments=[
            ("rviz_config", rviz_config_file),
        ],
        condition=IfCondition(gui),
    )

    # Define Node actions

    # Spawn the model in Gazebo. This also loads the plugin and starts the control node.
    # At the time of writing this script, the 'create' command does not allow spawning
    # the robot at a specific joint configuration
    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-string",
            robot_description_content,
            "-name",
            ROBOT_NAME,
            "-allow_renaming",
            "true",
        ],
    )

    # Bridge node
    gazebo_ros_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "--ros-args",
            "-p",
            f"config_file:={gz_params_bridge}",
        ],
        output="screen",
    )

    robot_state_pub_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description, robot_state_publisher_frequency],
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
        ],
    )

    # This is the controller that we shall use when
    # the MoveIt! planning pipeline is active, like in this case
    trajectory_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "fer_arm_trajectory_controller",
            "--controller-manager",
            "/controller_manager",
        ],
    )

    hand_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["hand_controller", "--controller-manager", "/controller_manager"],
    )

    # Define GroupAction actions (needed to enforce use_sim_time)
    group_actions = []

    group_actions.append(
        GroupAction(
            actions=[
                SetParameter(name="use_sim_time", value=True),
                move_group_launch_description,
                robot_state_pub_node,
            ]
        )
    )

    # Load controllers after spawning the model in Gazebo
    delay_controllers_after_gz_spawn = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=gz_spawn_entity,
            on_exit=[
                joint_state_broadcaster_spawner,
                trajectory_controller_spawner,
                hand_controller_spawner,
            ],
        )
    )

    # Delay RViz start after spawning joint trajectory controller
    delay_rviz_after_trajectory_controller_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=trajectory_controller_spawner,
            on_exit=[rviz_launch_description],
        )
    )

    nodes = [
        gz_spawn_entity,
        gazebo_ros_bridge,
        delay_controllers_after_gz_spawn,
        delay_rviz_after_trajectory_controller_spawner,
    ]

    return launches + group_actions + nodes


def generate_launch_description():

    # Declare arguments
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "gui",
            default_value="true",
            description="Start RViz2 automatically with this launch file.",
        )
    )

    declared_arguments.append(
        DeclareLaunchArgument(
            "tf_prefix", default_value="fer_", description="Prefix for the tf names."
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
            "hand",
            default_value="true",
            description="Flag to enable the hand of the robot.",
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
            "gazebo_world_file_path",
            default_value="empty.sdf",
            description="The path to the Gazebo world file inside the "
            "`gazebo_world_package`. If not specified, the default empty world is used.",
        )
    )

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
