//-----------------------------------------------------------------------------
// Title         : dac80504_model_tb
// Project       : ocra
//-----------------------------------------------------------------------------
// File          : dac80504_model_tb.sv
// Author        :   <vlad@arch-ssd>
// Created       : 02.09.2020
// Last modified : 02.09.2020
//-----------------------------------------------------------------------------
// Description :
// Simple testbench for DAC80504 model
//-----------------------------------------------------------------------------
// Copyright (c) 2020 by OCRA developers This model is the confidential and
// proprietary property of OCRA developers and the possession or use of this
// file requires a written license from OCRA developers.
//------------------------------------------------------------------------------

`ifndef _DAC80504_MODEL_TB_
 `define _DAC80504_MODEL_TB_

 `include "dac80504_model.sv"

 `timescale 1ns/1ns

module dac80504_model_tb;
   /*autoreginput*/
   // Beginning of automatic reg inputs (for undeclared instantiated-module inputs)
   reg			csn;			// To UUT of dac80504_model.v
   reg			ldacn;			// To UUT of dac80504_model.v
   reg			sclk;			// To UUT of dac80504_model.v
   reg			sdi;			// To UUT of dac80504_model.v
   // End of automatics
   /*autowire*/
   // Beginning of automatic wires (for undeclared instantiated-module outputs)
   wire			sdo;			// From UUT of dac80504_model.v
   wire [15:0]		vout0;			// From UUT of dac80504_model.v
   wire [15:0]		vout1;			// From UUT of dac80504_model.v
   wire [15:0]		vout2;			// From UUT of dac80504_model.v
   wire [15:0]		vout3;			// From UUT of dac80504_model.v
   // End of automatics

   reg [23:0] 		word_to_send;
   reg 			err = 0;
   integer 		k;
   
   initial begin
      $dumpfile("icarus_compile/000_dac80504_model_tb.lxt");
      $dumpvars(0, dac80504_model_tb);

      csn = 0;
      ldacn = 0;
      sclk = 0;
      sdi = 0;

      // prepare for incoming data
      #100 csn = 1;
      #100 ldacn = 1;

      // sync reg: broadcast off, sync (from ldac) off for channel 0
      // (will update DAC outputs from csn rising edge), on for the
      // other channels
      word_to_send = {1'b0, 3'd0, 4'b0010, {16'h000e}};
      #20 csn = 0;
      for (k = 23; k >= 0; k = k - 1) begin
	 #10 sclk = 1;
	 sdi = word_to_send[k];
	 #10 sclk = 0;
      end
      #10 csn = 1;

      // dac reg 0
      word_to_send = {1'b0, 3'd0, 4'b1000, {16'hbeef}};
      #20 csn = 0;
      for (k = 23; k >= 0; k = k - 1) begin
	 #10 sclk = 1;
	 sdi = word_to_send[k];
	 #10 sclk = 0;
      end

      // check DAC output word is as expected before and after cs
      #10 if (vout0 != 'h8000) begin
	 $display("%d ns: Unexpected DAC output, expected %x, saw %x.", $time, 0, vout0);
	 err <= 1;
      end      
      #10 csn = 1;
      #10 if (vout0 != 'hbeef) begin
	 $display("%d ns: Unexpected DAC output, expected %x, saw %x.", $time, 16'hbeef, vout0);
	 err <= 1;
      end

      // dac reg 2
      #20 ldacn = 0;
      word_to_send = {1'b0, 3'd0, 4'b1010, {16'hcafe}};
      #20 csn = 0;
      for (k = 23; k >= 0; k = k - 1) begin
	 #10 sclk = 1;
	 sdi = word_to_send[k];
	 #10 sclk = 0;
      end

      // check DAC output word is as expected before and after cs
      #10 if (vout2 != 'h8000) begin
	 $display("%d ns: Unexpected DAC output, expected %x, saw %x.", $time, 0, vout2);
	 err <= 1;
      end      
      #10 csn = 1;
      #10 if (vout2 != 'h8000) begin
	 $display("%d ns: Unexpected DAC output, expected %x, saw %x.", $time, 0, vout2);
	 err <= 1;
      end
      #10 ldacn = 1;
      #10 if (vout2 != 'hcafe) begin
	 $display("%d ns: Unexpected DAC output, expected %x, saw %x.", $time, 'hcafe, vout2);
	 err <= 1;
      end      
      
      #1000 if (err) begin
	 $display("THERE WERE ERRORS");
	 $stop; // to return a nonzero error code if the testbench is later scripted at a higher level
      end
      $finish;
   end
   
   dac80504_model UUT(/*autoinst*/
		      // Outputs
		      .sdo		(sdo),
		      .vout0		(vout0[15:0]),
		      .vout1		(vout1[15:0]),
		      .vout2		(vout2[15:0]),
		      .vout3		(vout3[15:0]),
		      // Inputs
		      .ldacn		(ldacn),
		      .csn		(csn),
		      .sclk		(sclk),
		      .sdi		(sdi));
   
endmodule // dac80504_model_tb
`endif //  `ifndef _DAC80504_MODEL_TB_
