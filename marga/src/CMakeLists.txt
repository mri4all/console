# Verilator CMake for building a unified binary for simulating the
# Marga server and Zynq PS/PL system.
#
# Mostly borrowed from the Verilator CMake example file.
#
# Use it as follows:
# cd /path/to/marga
# rm -rf build && mkdir build && cd build
# cmake ../src
# make -j4
#
# This will build the marga_sim binary.

cmake_minimum_required(VERSION 3.12)
project(marga_sim)

find_package(verilator HINTS $ENV{VERILATOR_ROOT} ${VERILATOR_ROOT})
if (NOT verilator_FOUND)
  message(FATAL_ERROR "Verilator was not found. Either install it, or set the VERILATOR_ROOT environment variable")
endif()

set (CMAKE_C_FLAGS "-O3 -g -Wall -std=c11")
set (CMAKE_CXX_FLAGS "-O3 -g -Wall -std=c++17")

# # For debugging only
# set (CMAKE_C_FLAGS "-O0 -g -Wall -std=c11")
# set (CMAKE_CXX_FLAGS "-O0 -g -Wall -std=c++17")

set(SERVER_PATH "../../marcos_server/src")
set(SERVER_SRC	${SERVER_PATH}/hardware.cpp
		${SERVER_PATH}/iface.cpp
		${SERVER_PATH}/mpack/mpack.c)

add_compile_definitions(VERILATOR_BUILD)

add_executable(marga_sim marga_sim_main.cpp marga_model.cpp ${SERVER_SRC})
target_include_directories(marga_sim PRIVATE ${SERVER_PATH} "./")

# TODO Verilator CFLAGS

verilate(marga_sim
	INCLUDE_DIRS "../hdl"
	VERILATOR_ARGS -Wall -Wno-UNUSED -Wno-PINCONNECTEMPTY -Wno-PINMISSING --cc -O3 --threads 4 --trace-fst --trace-depth 4
	SOURCES ../hdl/marga_model.sv)
