//-----------------------------------------------------------------------------
// Title         : ad5781_model
// Project       : OCRA
//-----------------------------------------------------------------------------
// File          : ad5781_model.sv
// Author        :   <vlad@arch-ssd>
// Created       : 31.08.2020
// Last modified : 31.08.2020
//-----------------------------------------------------------------------------
// Description :
// Behavioural model of the Analog Devices AD5781 DAC
//-----------------------------------------------------------------------------
// Copyright (c) 2020 by OCRA developers This model is the confidential and
// proprietary property of OCRA developers and the possession or use of this
// file requires a written license from OCRA developers.
//------------------------------------------------------------------------------
// Modification history :
// 31.08.2020 : created
//-----------------------------------------------------------------------------

`ifndef _AD5781_MODEL_
 `define _AD5781_MODEL_

 `timescale 1ns/1ns

module ad5781_model(
		    // pin labelling as in the AD5781 datasheet
		    input 	      sdin,
		    input 	      sclk,
		    input 	      syncn,
		    input 	      ldacn,
		    input 	      clrn,
		    input 	      resetn,

		    output reg 	      sdo = 0,
		    output reg [17:0] vout = 0
		    );

   reg [23:0] 			  dac_reg = 0, ctrl_reg = 0, clearcode_reg = 0, soft_ctrl_reg = 0;
   wire 			  rbuf = ctrl_reg[1], opgnd = ctrl_reg[2],
				  dactri = ctrl_reg[3], bin2sc = ctrl_reg[4], sdodis = ctrl_reg[5];
   reg [23:0] 			  spi_input = 0;
   reg [17:0] 			  vout_r;
   wire [2:0] 			  spi_addr = spi_input[22:20];
   reg [5:0] 			  spi_counter = 0;
   reg 				  read_mode = 0; // TODO: implement readback mode in FSM
   wire 			  spi_transfer_done = spi_counter == 24; // expects exactly 24 bits, more will be rejected

   always @(negedge sclk or negedge resetn or posedge syncn) begin
      if (!resetn) begin
	 dac_reg <= 0;
	 ctrl_reg <= 0;
	 soft_ctrl_reg <= 0;
	 spi_counter <= 0;
	 spi_input <= 0;
      end else begin
	 // see P20 of datasheet Rev E
	 if (syncn) begin
	    spi_counter <= 0;
	    if (spi_transfer_done && !read_mode) begin
	       // exactly 24 negedges of sclk occurred since last syncn
	       case (spi_addr)
		 3'b001: dac_reg <= spi_input;
		 3'b010: ctrl_reg <= spi_input;
		 3'b011: clearcode_reg <= spi_input;
		 3'b100: soft_ctrl_reg <= spi_input;
		 default;
	       endcase // case (spi_addr)
	    end
	 end else begin
	    spi_counter <= spi_counter + 1;
	    if (spi_counter == 0) read_mode <= sdin; // MSB of transfer
	    spi_input <= {spi_input[22:0], sdin}; // clock in data only when syncn low
	 end // else: !if(spi_transfer_done && !read_mode)
      end
   end

   // Roughly implemented Table 9 truth table in datasheet, but don't
   // rely too closely on it! Edges are ignored; only the final
   // steady-state values are used (e.g. if the table says 'falling
   // edge, 0, 1', I have interpreted the final state to be 0, 0,
   // 1). resetn behaviour is implemented by the sequential always
   // block above.
   //
   // WARNING: ldacn behaviour when clrn is low doesn't match
   // datasheet; e.g. if ldacn is kept high then clrn still has a
   // premature effect of updating the DAC output. This isn't the mode
   // in which ocra runs the DAC though, so it shouldn't be relevant
   // for now. A more accurate model will require some extra logic.
   wire [2:0] ctrl = {ldacn, clrn, resetn};
   always @(ctrl or dac_reg) begin
      case (ctrl)
	3'b001: vout_r <= clearcode_reg[19:2];
	3'b011: vout_r <= dac_reg[19:2];
	3'b101: vout_r <= clearcode_reg[19:2];
	3'b111: vout_r <= dac_reg[19:2];
	default: vout_r <= 0; // catch unhandled cases
	//3'b111 will output clearcode_reg if clrn has a rising edge - this behaviour is un-implemented here
      endcase // case ({ldacn, clrn, resetn})
   end

   // final vout ground/tristate (represented by 'z')
   always @(opgnd or dactri or vout_r) begin
      if (opgnd || dactri) vout = 18'dz;
      else vout = vout_r;
   end

endmodule // ad5781_model
`endif //  `ifndef _AD5781_MODEL_
