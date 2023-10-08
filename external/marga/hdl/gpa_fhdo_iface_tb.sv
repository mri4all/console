//-----------------------------------------------------------------------------
// Title         : gpa_fhdo_iface_tb
// Project       : ocra
//-----------------------------------------------------------------------------
// File          : gpa_fhdo_iface_tb.sv
// Author        :   <benjamin.menkuec@fh-dortmund.de>
// Created       : 03.09.2020
// Last modified : 03.09.2020
//-----------------------------------------------------------------------------
// Description :
//
// Testbench for GPA-FHDO interface and GPA-FHDO board model
//
//-----------------------------------------------------------------------------
// Copyright (c) 2020 by OCRA developers This model is the confidential and
// proprietary property of OCRA developers and the possession or use of this
// file requires a written license from OCRA developers.
//------------------------------------------------------------------------------

`ifndef _GPA_FHDO_IFACE_TB_
 `define _GPA_FHDO_IFACE_TB_

`include "gpa_fhdo_iface.sv"
`include "dac80504_model.sv"
`include "ads8684_model.sv"

 `timescale 1ns/1ns

module gpa_fhdo_iface_tb;
   
	reg			clk;			
	reg [31:0]		data_i;	
	reg [5:0]		spi_clk_div_i;	   
	reg			valid_i;		

	//
	wire			busy_o;			
	wire			ldacn;			
	wire			sclk;			
	wire			sdo;			
	wire			sdi;			
	wire			csn;
        wire 			ncsn = !csn;
        wire [15:0] 			adc_value_o;
	wire [15:0] 			voutx, vouty, voutz, voutz2;

	initial begin
		$dumpfile("icarus_compile/000_gpa_fhdo_iface_tb.lxt");
		$dumpvars(0, gpa_fhdo_iface_tb);

		// initialisation
		clk = 1;
		data_i = 0;
		valid_i = 0;
		spi_clk_div_i = 32;
	   
		#1000 send(1,2,3,4);
		#20000 send(-1,-2,-3,-4);	   
	   
		// read adc -- each read obtains the value from the previous read command
		//
		// (i.e. reading ch0, ch1, ch2, ch3, ch0 will return
		// undefined, ch0, ch1, ch2, ch3 data
		#80000
		#10 data_i = {5'b01000, 2'd0, 1'd0, 24'hC00000};
		valid_i = 1;
		#10 valid_i = 0;
	   
		#80000
		#10 data_i = {5'b01000, 2'd0, 1'd0, 24'hC10000};
		valid_i = 1;
		#10 valid_i = 0;

		#80000
		#10 data_i = {5'b01000, 2'd0, 1'd0, 24'hC20000};
		valid_i = 1;
		#10 valid_i = 0;

		#80000
		#10 data_i = {5'b01000, 2'd0, 1'd0, 24'hC30000};
		valid_i = 1;
		#10 valid_i = 0;

		#80000
		#10 data_i = {5'b01000, 2'd0, 1'd0, 24'hC00000};
		valid_i = 1;
		#10 valid_i = 0;

		#80000
		#10 data_i = {5'b01000, 2'd0, 1'd0, 24'hC00000};
		valid_i = 1;
		#10 valid_i = 0;	   
		//
		
		#20000 send(5,6,7,8);

		// VN: some manual tests, max throughput
		#20000 data_i = {5'd0, 2'd0, 1'd0, 8'h08, 16'ha}; valid_i = 1; #10 valid_i = 0;
		#320 wait(!busy_o);
		#10 data_i = {5'd0, 2'd1, 1'd0, 8'h09, 16'hb}; valid_i = 1; #10 valid_i = 0;
		#320 wait(!busy_o);
		#10 data_i = {5'd0, 2'd2, 1'd0, 8'h0a, 16'hc}; valid_i = 1; #10 valid_i = 0;
		#320 wait(!busy_o);
		#10 data_i = {5'd0, 2'd3, 1'd0, 8'h0b, 16'hd}; valid_i = 1; #10 valid_i = 0;
		#320 wait(!busy_o);
		#10 data_i = {5'd0, 2'd0, 1'd0, 8'h08, 16'he}; valid_i = 1; #10 valid_i = 0;
		#320 wait(!busy_o);
		#10 data_i = {5'd0, 2'd1, 1'd0, 8'h09, 16'hf}; valid_i = 1; #10 valid_i = 0;
		#320 wait(!busy_o);
		#10 data_i = {5'd0, 2'd2, 1'd0, 8'h0a, 16'h10}; valid_i = 1; #10 valid_i = 0;
		#320 wait(!busy_o);
		#10 data_i = {5'd0, 2'd3, 1'd0, 8'h0b, 16'h11}; valid_i = 1; #10 valid_i = 0;

		#20000 $finish;
	end // initial begin

	task send; // send data to OCRA1 interface core
	input [15:0] inx, iny, inz, inz2;
	begin
		// TODO: perform a check to see whether the busy line is set before trying to send data
		#10 data_i = {5'd0, 2'd0, 1'd0, 6'h02, 2'd0, inx};
		valid_i = 1;
		#10 valid_i = 0;
		#80000 data_i = {5'd0, 2'd1, 1'd0, 6'h02, 2'd1, iny};
		valid_i = 1;
		#10 valid_i = 0;
		#80000 data_i = {5'd0, 2'd2, 1'd0, 6'h02, 2'd2, inz};
		valid_i = 1;
		#10 valid_i = 0; 	 
		#80000 data_i = {5'd0, 2'd3, 1'd1, 6'h02, 2'd3, inz2};
		valid_i = 1;
		#10 valid_i = 0;
	end
	endtask // send

   always #5 clk = !clk;

gpa_fhdo_iface UUT(
	.clk		(clk),
	/*AUTOINST*/
	// Outputs
	.busy_o		(busy_o),
	.fhd_sdo_o	(sdo),
	.fhd_clk_o  (sclk),
	.fhd_csn_o	(csn),
	.adc_value_o(adc_value_o),
	// Inputs		     
	.data_i		(data_i),		
	.valid_i	(valid_i),
	.fhd_sdi_i		(sdi),
	.spi_clk_div_i	(spi_clk_div_i[5:0]));

dac80504_model GPA_FHDO_DAC(
	// Outputs
	//.sdo		(sdi),			 // disconnect to not interfere with adc
	.vout0		(voutx[15:0]),
	.vout1		(vouty[15:0]),
	.vout2		(voutz[15:0]),
	.vout3		(voutz2[15:0]),
	// Inputs
	.sclk		(sclk),
	.ldacn		(ldacn),
	.csn		(csn),
	.sdi		(sdo));
	
ads8684_model GPA_FHDO_ADC(
	// Outputs
	.sdo		(sdi),			 
	// Inputs
	.sclk		(sclk),
	.csn		(ncsn),
	.sdi		(sdo),
	.ain_0p		(voutx[15:0]),
	.ain_1p		(vouty[15:0]),
	.ain_2p		(voutz[15:0]),
	.ain_3p		(voutz2[15:0]));	
	


endmodule // gpa_fhdo_iface_tb
`endif //  `ifndef _GPA_FHDO_IFACE_TB_
