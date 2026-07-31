from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import generate_move_group_launch


def setup_launch(context, *args, **kwargs):
    ROBOT_NAME = "fer"

    # Get the tf_prefix value from the LaunchConfiguration and context
    xacro_args = {
        "tf_prefix": LaunchConfiguration("tf_prefix").perform(context),
        "gazebo": LaunchConfiguration("gazebo").perform(context),
        "hand": LaunchConfiguration("hand").perform(context),
    }

    moveit_controllers_file = PathJoinSubstitution(
        [
            FindPackageShare("acg_resources_fer_moveit_config"),
            "config",
            LaunchConfiguration("moveit_controllers_file"),
        ]
    ).perform(context)

    # Build the MoveIt config
    moveit_config = (
        MoveItConfigsBuilder(ROBOT_NAME, package_name="acg_resources_fer_moveit_config")
        .trajectory_execution(file_path=moveit_controllers_file)
        .robot_description(mappings=xacro_args)
        .robot_description_semantic(mappings=xacro_args)
        .to_moveit_configs()
    )

    ld = LaunchDescription()
    ld.add_action(generate_move_group_launch(moveit_config))

    return ld.entities


def generate_launch_description():
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "tf_prefix", default_value="fer_", description="Prefix for the tf names."
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "gazebo",
            default_value="false",
            description="Flag which must be enabled when the robot is simulated in Gazebo.",
            choices=("false", "true"),
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "hand",
            default_value="true",
            description="Flag to enable the hand of the robot.",
            choices=("false", "true"),
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            "moveit_controllers_file",
            default_value="moveit_controllers.yaml",
            description="MoveIt controller mapping yaml filename inside acg_resources_fer_moveit_config/config",
        ),
    )
    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=setup_launch)]
    )
