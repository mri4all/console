//-----------------------------------------------------------------------------
// Title         : ad5781_model_tb
// Project       : ocra
//-----------------------------------------------------------------------------
// File          : ad5781_model_tb.sv
// Author        :   <vlad@arch-ssd>
// Created       : 02.09.2020
// Last modified : 02.09.2020
//-----------------------------------------------------------------------------
// Description :
// Simple testbench for AD5781 model
//-----------------------------------------------------------------------------
// Copyright (c) 2020 by OCRA developers This model is the confidential and
// proprietary property of OCRA developers and the possession or use of this
// file requires a written license from OCRA developers.
//------------------------------------------------------------------------------

`ifndef _AD5781_MODEL_TB_
 `define _AD5781_MODEL_TB_

 `include "ad5781_model.sv"

 `timescale 1ns/1ns

module ad5781_model_tb;
   /*autoreginput*/
   // Beginning of automatic reg inputs (for undeclared instantiated-module inputs)
   reg			clrn;			// To UUT of ad5781_model.v
   reg			ldacn;			// To UUT of ad5781_model.v
   reg			resetn;			// To UUT of ad5781_model.v
   reg			sclk;			// To UUT of ad5781_model.v
   reg			sdin;			// To UUT of ad5781_model.v
   reg			syncn;			// To UUT of ad5781_model.v
   // End of automatics
   /*autowire*/
   // Beginning of automatic wires (for undeclared instantiated-module outputs)
   wire			sdo;			// From UUT of ad5781_model.v
   wire [17:0]		vout;			// From UUT of ad5781_model.v
   // End of automatics

   reg [23:0] 		word_to_send;
   reg 			err = 0;
   integer 		k;
   
   initial begin
      $dumpfile("icarus_compile/000_ad5781_model_tb.lxt");
      $dumpvars(0, ad5781_model_tb);

      clrn = 0;
      ldacn = 1;
      resetn = 0;
      sclk = 0;
      sdin = 0;
      syncn = 0;

      // take the DAC out of reset
      #100 resetn = 1;
      #100 syncn = 1;
      #100 clrn = 1;

      // control
      word_to_send = {1'b0, 3'b010, {20'b000010}};
      #20 syncn = 0;
      for (k = 23; k >= 0; k = k - 1) begin
	 #10 sclk = 1;
	 sdin = word_to_send[k];
	 #10 sclk = 0;
      end
      #40 syncn = 1;
      // check DAC output word is as expected
      #10 if (vout != 0) begin
	 $display("%d ns: Unexpected DAC output, expected %x, saw %x.", $time, 0, vout);
	 err <= 1;
      end

      // DAC output
      word_to_send = {1'b0, 3'b001, {18'h3dead}, 2'b00};
      #20 syncn = 0;
      for (k = 23; k >= 0; k = k - 1) begin
	 #10 sclk = 1;
	 sdin = word_to_send[k];
	 #10 sclk = 0;
      end
      #20 syncn = 1;

      #20 ldacn = 0;
      #20 ldacn = 1;
      // check DAC output word is as expected      
      if (vout != 18'h3dead) begin
	 $display("%d ns: Unexpected DAC output, expected %x, saw %x.", $time, 18'h3dead, vout);
	 err <= 1;
      end

      // DAC output, different value
      #200 word_to_send = {1'b0, 3'b001, {18'h1cafe}, 2'b00};
      #20 syncn = 0;
      for (k = 23; k >= 0; k = k - 1) begin
	 #10 sclk = 1;
	 sdin = word_to_send[k];
	 #10 sclk = 0;
      end
      #20 syncn = 1;

      #20 ldacn = 0;
      #20 ldacn = 1;
      // check DAC output word is as expected      
      if (vout != 18'h1cafe) begin
	 $display("%d ns: Unexpected DAC output, expected %x, saw %x.", $time, 18'h1cafe, vout);
	 err <= 1;
      end

      // DAC output, different value - hold LDAC low the whole time
      // DAC output, different value
      #200 word_to_send = {1'b0, 3'b001, {18'h2beef}, 2'b00};
      ldacn = 0;
      #20 syncn = 0;
      for (k = 23; k >= 0; k = k - 1) begin
	 #10 sclk = 1;
	 sdin = word_to_send[k];
	 #10 sclk = 0;
      end
      #20 syncn = 1;
      #20 syncn = 0;

      // check DAC output word is as expected      
      if (vout != 18'h2beef) begin
	 $display("%d ns: Unexpected DAC output, expected %x, saw %x.", $time, 18'h2beef, vout);
	 err <= 1;
      end

      #20 ldacn = 1;      
      
      #1000 if (err) begin
	 $display("THERE WERE ERRORS");
	 $stop; // to return a nonzero error code if the testbench is later scripted at a higher level
      end
      $finish;
   end
   
   ad5781_model UUT(/*autoinst*/
		    // Outputs
		    .sdo		(sdo),
		    .vout		(vout[17:0]),
		    // Inputs
		    .sdin		(sdin),
		    .sclk		(sclk),
		    .syncn		(syncn),
		    .ldacn		(ldacn),
		    .clrn		(clrn),
		    .resetn		(resetn));
   
endmodule // ad5781_model_tb
`endif //  `ifndef _AD5781_MODEL_TB_
