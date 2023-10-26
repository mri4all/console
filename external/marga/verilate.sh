#!/usr/bin/env bash
# Generate C++ source files for inclusion in higher-level simulation

verilator -Wall -Wno-UNUSED -Wno-PINCONNECTEMPTY -Wno-PINMISSING \
	  -CFLAGS "--std=c++17 -I../../include"\
	  -Ihdl \
	  --cc --trace \
	  --trace-depth 1 \
	  marga.sv \
	  --exe ../src/marga_sim.cpp ../src/marga_sim_main.cpp

	  # +define+__ICARUS__=1 \

# --trace-depth 1 is another potentially useful flag, for setting the VCD trace depth
# --exe allow building with "make -C obj_dir/ -f Vionpulse_sim.mk Vionpulse_sim" for basic testing. cmake is used from toplevel ionpulse_sdk CMake
