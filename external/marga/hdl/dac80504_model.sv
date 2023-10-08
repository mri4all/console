//-----------------------------------------------------------------------------
// Title         : dac80504_model
// Project       : OCRA
//-----------------------------------------------------------------------------
// File          : dac80504_model.sv
// Author        :   <vlad@arch-ssd>
// Created       : 31.08.2020
// Last modified : 31.08.2020
//-----------------------------------------------------------------------------
// Description :
// Behavioural model of the TI DAC80504 DAC
//-----------------------------------------------------------------------------
// Copyright (c) 2020 by OCRA developers This model is the confidential and
// proprietary property of OCRA developers and the possession or use of this
// file requires a written license from OCRA developers.
//------------------------------------------------------------------------------

`ifndef _DAC80504_MODEL_
 `define _DAC80504_MODEL_

 `timescale 1ns/1ns

module dac80504_model(
		      // pin labelling as in the DAC80504 datasheet
		      input 		ldacn,
		      input 		csn,
		      input 		sclk,
		      input 		sdi,

		      output reg 	sdo,
		      output reg [15:0] vout0, vout1, vout2, vout3 // 
		      );

   // internal DAC registers
   reg [15:0] 				sync_reg = 'hff00, config_reg = 0, gain_reg = 0, trigger_reg = 0, brdcast_reg = 0, status_reg = 0,
					dac0_reg = 0, dac1_reg = 0, dac2_reg = 0, dac3_reg = 0;

   // broadcast and sync control
   wire [3:0] 				dac_brdcast_en = sync_reg[11:8], dac_sync_en = sync_reg[3:0];

   // wire 			  rbuf = ctrl_reg[1], opgnd = ctrl_reg[2], 
   // 				  dactri = ctrl_reg[3], bin2sc = ctrl_reg[4], sdodis = ctrl_reg[5];
   reg [23:0] 				spi_input = 0;
   wire [15:0] 				spi_payload = spi_input[15:0];
   wire [3:0] 				spi_addr = spi_input[19:16];
   reg [5:0] 				spi_counter = 0;
   reg 					read_mode = 0; // TODO: implement readback mode in FSM
   wire 				spi_transfer_done = spi_counter == 24; // if more than 24 bits sent, will hold most recent 24   

   initial begin
      sdo = 0;
      vout0 = 16'h8000;
      vout1 = 16'h8000;
      vout2 = 16'h8000;
      vout3 = 16'h8000;
   end

   always @(negedge sclk or posedge csn) begin
      if (!csn) begin
	 spi_input <= {spi_input[22:0], sdi}; // clock in data only when syncn low
	 if (spi_counter != 24) spi_counter <= spi_counter + 1;
	 if (spi_counter == 0) read_mode <= sdi; // MSB of transfer
      end else begin
	 spi_counter <= 0;
	 spi_input <= 0;
      end
   end
   
   always @(posedge csn) begin
      if (spi_transfer_done && !read_mode) begin
	 // $display("addr %d payload %d",spi_addr,spi_payload);
	 case(spi_addr)
	   4'b0010: sync_reg <= spi_payload;
	   4'b0011: config_reg <= spi_payload;
	   4'b0100: gain_reg <= spi_payload;
	   4'b0101: trigger_reg <= spi_payload;
	   4'b0110: brdcast_reg <= spi_payload;
	   4'b0111: status_reg <= spi_payload;
	   4'b1000: begin
	      dac0_reg <= spi_payload;
	      if (!dac_sync_en[0]) vout0 <= spi_payload;
	   end
	   4'b1001: begin
	      dac1_reg <= spi_payload;
	      if (!dac_sync_en[1]) vout1 <= spi_payload;
	   end
	   4'b1010: begin
	      dac2_reg <= spi_payload;
	      if (!dac_sync_en[2]) vout2 <= spi_payload;
	   end
	   4'b1011: begin
	      dac3_reg <= spi_payload;
	      if (!dac_sync_en[3]) vout3 <= spi_payload;
	   end
	   default;
	 endcase // case (spi_addr)
      end // if (spi_transfer_done && !read_mode)
   end // always @ (negedge sclk or csn)

   // Only very basic behaviour implemented so far - no broadcasts
   // etc. May need to extend depending on what features of the
   // DAC80504 the GPA-FHDO is using.
   always @(posedge ldacn) begin
      if (dac_sync_en[0] && ldacn) vout0 <= dac0_reg;
      if (dac_sync_en[1] && ldacn) vout1 <= dac1_reg;
      if (dac_sync_en[2] && ldacn) vout2 <= dac2_reg;
      if (dac_sync_en[3] && ldacn) vout3 <= dac3_reg;
   end
   
endmodule // dac80504_model
`endif //  `ifndef _DAC80504_MODEL_
