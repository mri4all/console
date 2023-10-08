#!/usr/bin/env bash
# Run all testbenches and halt when there's an error

globstat=0
for k in marbuffer marfifo mardecode ad5781_model ads8684_model dac80504_model gpa_fhdo_iface ocra1_iface; do
    echo "Testing $k"
    iverilog -o icarus_compile/000_$k.compiled $k.sv -Wall -g2005-sv
    if [ $? -ne 0 ]; then globstat=1; fi
    iverilog -o icarus_compile/000_$k\_tb.compiled $k\_tb.sv -Wall  -g2005-sv
    if [ $? -ne 0 ]; then globstat=1; fi
    vvp -N icarus_compile/000_$k\_tb.compiled -none
    if [ $? -ne 0 ]; then globstat=1; fi
done

# manual test of marga, marga_simple_tb
echo "Testing marga"
iverilog -o icarus_compile/000_marga.compiled marga.sv -Wall -g2005-sv
if [ $? -ne 0 ]; then globstat=1; fi
iverilog -o icarus_compile/000_marga_simple_tb.compiled marga_simple_tb.sv -Wall  -g2005-sv
if [ $? -ne 0 ]; then globstat=1; fi
vvp -N icarus_compile/000_marga_simple_tb.compiled -none
if [ $? -ne 0 ]; then globstat=1; fi

exit $globstat
