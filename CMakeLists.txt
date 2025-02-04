cmake_minimum_required(VERSION 3.10)

# Set the project name
project(MilkVideoConverter)

# Find OpenCV package
find_package(OpenCV REQUIRED)

# Add the static library
add_library(video_processor video_processor.cpp)

# Link OpenCV libraries
target_link_libraries(video_processor ${OpenCV_LIBS})