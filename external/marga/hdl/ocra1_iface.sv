//-----------------------------------------------------------------------------
// Title         : ocra1_iface
// Project       : ocra
//-----------------------------------------------------------------------------
// File          : ocra1_iface.sv
// Author        :   <vlad@arch-ssd>
// Created       : 03.09.2020
// Last modified : 03.09.2020
//-----------------------------------------------------------------------------
// Description :
//
// Interface between gradient BRAM module and OCRA1 GPA board, with a
// four-channel SPI serialiser and associated FSM logic.
//
//-----------------------------------------------------------------------------
// Copyright (c) 2020 by OCRA developers This model is the confidential and
// proprietary property of OCRA developers and the possession or use of this
// file requires a written license from OCRA developers.
//------------------------------------------------------------------------------

`ifndef _OCRA1_IFACE_
 `define _OCRA1_IFACE_

 `timescale 1ns/1ns

module ocra1_iface(
		   input 	clk,
		   input 	rst_n, // not used for anything other than data_present flag for now

		   // data words from gradient memory core
		   /* verilator lint_off UNUSED */
		   input [31:0] data_i, // bits 26:25: target channel, bit 24: broadcast/transmit,
		   /*lint_on*/

		   // data valid flag, should be held high for 1 cycle to initiate a transfer
		   input 	valid_i,

		   // SPI clock divider
		   input [5:0] 	spi_clk_div_i,

		   // OCRA1 interface (startup values are set here as well)
		   output reg 	oc1_clk_o = 0,
		   output reg 	oc1_syncn_o = 1,
		   output reg 	oc1_ldacn_o = 0,
		   output reg 	oc1_sdox_o = 0,
		   output reg 	oc1_sdoy_o = 0,
		   output reg 	oc1_sdoz_o = 0,
		   output reg 	oc1_sdoz2_o = 0,

		   output reg 	busy_o = 0, // should be held high while module is carrying out an SPI transfer
		   output reg 	data_lost_o = 0
		   );

   // 122.88 -> 3.84 MHz clock freq - ~150 ksps update rate possible
   // spi_clk_edge_div used for toggling the SPI clock
   reg [4:0] 			spi_clk_edge_div = 0; // spi_clk_div_r divided by 2

   localparam IDLE = 25, START = 24, END = 0;

   reg [5:0] 			state = IDLE;
   reg [5:0] 			div_ctr = 0;
   reg 				valid_r = 0;
   reg [23:0] 			payload_r = 0;
   reg 				broadcast_r = 0, broadcast_r2 = 0;
   reg [1:0] 			channel_r = 0;
   reg [23:0] 			datax_r = 0, datay_r = 0, dataz_r = 0, dataz2_r = 0; // used for SPI output
   reg [23:0] 			datax_r2 = 0, datay_r2 = 0, dataz_r2 = 0, dataz2_r2 = 0; // used for temp storage
   reg [3:0] 			data_present = 0;

   always @(posedge clk) begin
      // default assignments, which will take place unless overridden by other assignments in the FSM
//       oc1_clk_o <= 1;
      oc1_syncn_o <= 0;
      busy_o <= 1;

      spi_clk_edge_div <= spi_clk_div_i[5:1];
      broadcast_r2 <= broadcast_r;

      // handle input instructions
      valid_r <= valid_i;
      broadcast_r <= 0; // default
      if (valid_i) begin
	 payload_r <= data_i[23:0];
	 broadcast_r <= data_i[24];
	 channel_r <= data_i[26:25];
      end

      if (valid_r) begin
	 // Save the fact that now there's data in the register. If
	 // there was already data present in the relevant register
	 // that hadn't yet been sent out, flag a data-lost error.
	 data_present[channel_r] <= 1'd1;
	 data_lost_o <= data_present[channel_r];

	 case (channel_r)
	   2'b00: datax_r2 <= payload_r;
	   2'b01: datay_r2 <= payload_r;
	   2'b10: dataz_r2 <= payload_r;
	   default: dataz2_r2 <= payload_r;
	   // 2'b00: datax_r <= payload_r;
	   // 2'b01: datay_r <= payload_r;
	   // 2'b10: dataz_r <= payload_r;
	   // default: dataz2_r <= payload_r;
	 endcase // case (channel_r)
      end

      if (!rst_n) data_present <= 4'd0; // assume that there's no valid data present after a reset

      // could use a wire, but deliberately adding a clocked register stage to help with timing
      {oc1_sdox_o, oc1_sdoy_o, oc1_sdoz_o, oc1_sdoz2_o} <= {datax_r[23], datay_r[23], dataz_r[23], dataz2_r[23]};

      case (state)
	IDLE: begin
	   oc1_syncn_o <= 1;
	   busy_o <= 0;
	   state <= IDLE;
	   if (broadcast_r2) begin
	      data_present <= 4'd0;
	      data_lost_o <= 0;
	      {datax_r, datay_r, dataz_r, dataz2_r} <= {datax_r2, datay_r2, dataz_r2, dataz2_r2};
	      state <= START;
	   end
	end
	END: begin
	   // all the data has been clocked out; just go back to IDLE
	   state <= IDLE;
	end
	default: begin // covers the START state and all the states down to 0
	   oc1_clk_o <= div_ctr <= {1'b0, spi_clk_edge_div};
	   // divisor logic
	   if (div_ctr == spi_clk_div_i) begin
	      div_ctr <= 0;
	      {datax_r, datay_r, dataz_r, dataz2_r} <= {datax_r << 1, datay_r << 1, dataz_r << 1, dataz2_r << 1};
	      state <= state - 1; // eventually will hit the END state
	   end else begin
	      div_ctr <= div_ctr + 1;
	   end
	end // case: default

      endcase // case (state)
   end // always @ (posedge clk)

endmodule // ocra1_iface
`endif //  `ifndef _OCRA1_IFACE_
