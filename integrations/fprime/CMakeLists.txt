####
# This sets up the build system for the 'Asteria' project, including
# components and deployments from project.cmake. In addition, it imports the core F Prime components.
####

cmake_minimum_required(VERSION 3.24.2)
project(Asteria C CXX)
set(CMAKE_CXX_STANDARD 17)
# Both the standalone bridge and scheduled topology use generated typed ports.
add_compile_definitions(FW_DIRECT_PORT_CALLS=0)
include_directories("${CMAKE_CURRENT_LIST_DIR}/../../flight")

###
# F' Core Setup
# This includes all of the F prime core components, and imports the make-system.
###
include("${CMAKE_CURRENT_LIST_DIR}/lib/fprime/cmake/FPrime.cmake")
# NOTE: register custom targets between these two lines
fprime_setup_included_code()


# This includes project-wide objects
add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/Asteria")

add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/AsteriaDeployment")

add_fprime_subdirectory("${CMAKE_CURRENT_LIST_DIR}/Bridge")

enable_testing()
add_test(NAME AsteriaTypedPorts COMMAND $<TARGET_FILE:AsteriaVerification>)
