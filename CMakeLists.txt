cmake_minimum_required(VERSION 3.8)
project(lidar_submap_localization)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(pcl_conversions REQUIRED)
find_package(PCL REQUIRED COMPONENTS common io filters registration kdtree)
find_package(Eigen3 REQUIRED)

add_executable(submap_localizer src/submap_localizer.cpp)
target_include_directories(submap_localizer PRIVATE ${PCL_INCLUDE_DIRS})
target_link_libraries(submap_localizer ${PCL_LIBRARIES} Eigen3::Eigen)
ament_target_dependencies(submap_localizer
  rclcpp sensor_msgs nav_msgs geometry_msgs std_msgs tf2_ros pcl_conversions)

install(TARGETS submap_localizer DESTINATION lib/${PROJECT_NAME})
install(DIRECTORY config launch DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_cmake_pytest QUIET)
  if(ament_cmake_pytest_FOUND)
    ament_add_pytest_test(test_config test/test_config.py)
  endif()
endif()

ament_package()
