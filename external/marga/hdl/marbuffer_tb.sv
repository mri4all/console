//-----------------------------------------------------------------------------
// Title         : marbuffer_tb
// Project       : marga
//-----------------------------------------------------------------------------
// File          : marbuffer_tb.sv
// Author        :   <vlad@arch-ssd>
// Created       : 18.12.2020
// Last modified : 18.12.2020
//-----------------------------------------------------------------------------
// Description :
//
// Simple testbench for marbuffer
//
//-----------------------------------------------------------------------------
// Copyright (c) 2020 by OCRA developers This model is the confidential and
// proprietary property of OCRA developers and the possession or use of this
// file requires a written license from OCRA developers.
//------------------------------------------------------------------------------

`ifndef _MARBUFFER_TB_
 `define _MARBUFFER_TB_

 `include "marbuffer.sv"

 `timescale 1ns/1ns

module marbuffer_tb;
   parameter fifo_size = 4;
   /*AUTOREGINPUT*/
   // Beginning of automatic reg inputs (for undeclared instantiated-module inputs)
   reg			clk;			// To UUT of marbuffer.v
   reg [15:0]		data_i;			// To UUT of marbuffer.v
   reg [6:0]		delay_i;		// To UUT of marbuffer.v
   reg			direct_i;		// To UUT of marbuffer.v
   reg			valid_i;		// To UUT of marbuffer.v
   // End of automatics
   /*AUTOWIRE*/
   // Beginning of automatic wires (for undeclared instantiated-module outputs)
   wire [15:0]		data_o;			// From UUT of marbuffer.v
   wire			empty_o;		// From UUT of marbuffer.v
   wire			err_o;			// From UUT of marbuffer.v
   wire			full_o;			// From UUT of marbuffer.v
   wire			stb_o;			// From UUT of marbuffer.v
   // End of automatics

   reg err = 0;
   always #5 clk = !clk;
   integer i;
   initial begin
      $dumpfile("icarus_compile/000_marbuffer_tb.lxt");
      $dumpvars(0, marbuffer_tb);

      clk = 1;
      data_i = 0;
      delay_i = 0;
      valid_i = 0;
      direct_i = 0;

      // Fill the FIFO with words
      #1 burst(1, 0); // single word, zero delay
      #20 burst(1, 1); // single word, nonzero delay
      #20 burst(8, 0); // multiple words, zero delay
      #10 burst(7, 1); // multiple words, nonzero delay: fill up FIFO but don't cause an overflow
      #100 burst(8, 1); // as above, but cause an overflow

      // Keep the FIFO filled, using basic flow control; slightly overflow the timer
      #30 for (i = 0; i < 135; i = i + 1) begin
	 wait(!full_o);
	 #1 burst(1, i+2); // start with nonzero delay to avoid empty periods
	 #10;
      end

      // Direct write
      #400 direct_i = 1; data_i = 1234;
      #10 direct_i = 0;

      // Write in with the error pattern discovered 14/01/2021
      #400 valid_i = 1; delay_i = 2; data_i = 1111;
      #10 valid_i = 0;
      #20 valid_i = 1; delay_i = 0; data_i = 2222;
      #10 valid_i = 0;

      #1000 if (err) begin
	 $display("THERE WERE ERRORS");
	 $stop; // to return a nonzero error code if the testbench is later scripted at a higher level
      end
      $finish;
   end // initial begin

   // check outputs
   integer n;
   initial begin
      #5 check_outputs(0, 1, 0, 0, 0);
      #10 check_outputs(0, 1, 0, 0, 0);
      #10 check_outputs(0, 0, 0, 0, 0);
      #10 check_outputs(1, 0, 0, 1, 0);
      #10 check_outputs(1, 1, 0, 0, 0);

      #20 check_outputs(1, 0, 0, 0, 0);
      #10 check_outputs(2, 1, 0, 1, 0);

      // stream of 8 values
      #10 for (n = 3; n < 11; n = n + 1) #10 check_outputs(n, 0, 0, 1, 0);

      // stream of 7 values with delay, no errors
      #30 check_outputs(11, 0, 0, 1, 0);
      #20 check_outputs(12, 0, 0, 1, 0);
      #20 check_outputs(13, 0, 1, 1, 0);
      #20 check_outputs(14, 0, 0, 1, 0);
      #20 check_outputs(15, 0, 0, 1, 0);
      #20 check_outputs(16, 0, 0, 1, 0);
      #20 check_outputs(17, 1, 0, 1, 0);

      // stream of 8 values with delay, overflow
      #50 check_outputs(18, 0, 0, 1, 0);
      #20 check_outputs(19, 0, 0, 1, 0);
      #20 check_outputs(20, 0, 1, 1, 0);
      #10 check_outputs(20, 0, 0, 0, 1); // error flag
      #10 check_outputs(21, 1, 0, 1, 0);

      #30 for (n = 0; n < 124; n = n + 1) begin
	 #30;
	 #(10 * n) check_outputs(26 + n, 0, 'bx, 1, 0);
      end
      // overflow: verify first few values
      #2550 check_outputs(151, 0, 1, 1, 0);
      #10 check_outputs(152, 0, 1, 1, 0);
      #20 check_outputs(153, 0, 0, 1, 0);
      #30 check_outputs(154, 0, 0, 1, 0);
      #40 check_outputs(155, 0, 1, 1, 0);

      #460 check_outputs(1234, 1, 0, 1, 0);

      #440 check_outputs(1111, 0, 0, 1, 0);
      #10 check_outputs(2222, 0, 0, 1, 0);

      // #20 check_outputs(7, 0, 0, 1);
      // #10 check_outputs(7, 0, 0, 0);
      // #10 check_outputs(8, 0, 0, 1);
      // #10 check_outputs(8, 0, 1, 0);

      // // check full flag
      // #10 check_outputs(9, 0, 1, 1);
      // #10 check_outputs(9, 0, 1, 0);
      // #10 check_outputs(10, 0, 0, 1);
      // #10 check_outputs(10, 0, 1, 0);

      // check long-term timing with flow control based on the full flag
   end

   reg [15:0] k = 1; // increment for each output, to make it easier to track
   integer m;
   task burst;
      input [9:0] quantity;
      input [6:0] delay;

      begin
	 valid_i = 1;
	 delay_i = delay;
	 for (m = 0; m < quantity; m = m + 1) begin
	    data_i = k;
	    #10 k = k + 1;
	 end
	 valid_i = 0;
      end
   endtask // burst

   task check_outputs;
      input [15:0] data;
      input 	   empty;
      input 	   full;
      input 	   stb;
      input 	   overflow_err;

      begin
	 if (data != data_o) begin
	    $display("%d ns: data_o expected 0x%x, saw 0x%x.",
		     $time, data, data_o);
	    err <= 1;
	 end
	 if (empty != empty_o) begin
	    $display("%d ns: empty_o expected %d, saw %d.",
		     $time, empty, empty_o);
	    err <= 1;
	 end
	 if (full != full_o) begin
	    $display("%d ns: full_o expected %d, saw %d.",
		     $time, full, full_o);
	    err <= 1;
	 end
	 if (stb != stb_o) begin
	    $display("%d ns: stb_o expected %d, saw %d.",
		     $time, stb, stb_o);
	    err <= 1;
	 end
	 if (overflow_err != err_o) begin
	    $display("%d ns: err_o expected %d, saw %d.",
		     $time, overflow_err, err_o);
	    err <= 1;
	 end
      end
   endtask // check_outputs

   marbuffer #(/*AUTOINSTPARAM*/
	       // Parameters
	       .fifo_size		(fifo_size))
   UUT(/*AUTOINST*/
       // Outputs
       .data_o				(data_o[15:0]),
       .empty_o				(empty_o),
       .full_o				(full_o),
       .err_o				(err_o),
       .stb_o				(stb_o),
       // Inputs
       .clk				(clk),
       .data_i				(data_i[15:0]),
       .delay_i				(delay_i[6:0]),
       .valid_i				(valid_i),
       .direct_i			(direct_i));

endmodule // marbuffer_tb
`endif //  `ifndef _MARBUFFER_TB_
