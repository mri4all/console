//-----------------------------------------------------------------------------
// Title         : rx_chain_model
// Project       : marga
//-----------------------------------------------------------------------------
// File          : rx_chain_model.sv
// Author        :   <vlad@vlad-laptop>
// Created       : 25.12.2020
// Last modified : 25.12.2020
//-----------------------------------------------------------------------------
// Description :
//
// Basic model to replace the Xilinx IP involved in the RX chain;
// doesn't do any RX but simulates the data flow.
//
//-----------------------------------------------------------------------------
// Copyright (c) 2020 by OCRA developers This model is the confidential and
// proprietary property of OCRA developers and the possession or use of this
// file requires a written license from OCRA developers.
//------------------------------------------------------------------------------

`ifndef _RX_CHAIN_MODEL_
 `define _RX_CHAIN_MODEL_

 `timescale 1ns/1ns

module rx_chain_model(
		      input 		clk,
		      input 		rst_n,

		      input [15:0] 	rate_axis_tdata_i,
		      input 		rate_axis_tvalid_i,

		      input [31:0] 	rx_iq_axis_tdata_i,
		      input 		rx_iq_axis_tvalid_i,

		      input 		axis_tready_i,
		      output reg 	axis_tvalid_o,
		      output reg [63:0] axis_tdata_o
		      );

   // Currently still 12-bit rate, although bus is capable of 16 bits for further CIC configuration
   reg [11:0] 				cnt = 0;
   reg [11:0] 				rate = 600;

   wire [15:0] 				rx_i = rx_iq_axis_tdata_i[15:0],
					rx_q = rx_iq_axis_tdata_i[31:16];

   reg [19:0] 				rst_n_shreg = 0;

   initial axis_tdata_o = 0;

   always @(posedge clk) begin
      rst_n_shreg <= {rst_n_shreg[18:0], rst_n};
      axis_tvalid_o <= 0;
      if (!rst_n) begin
	 cnt <= 0;
	 rate <= 600;
      end else begin
	 if (rate_axis_tvalid_i && rst_n_shreg[19]) rate <= rate_axis_tdata_i[11:0];

	 if (rx_iq_axis_tvalid_i) cnt <= cnt + 1;

	 if (cnt >= rate - 1) begin
	    axis_tvalid_o <= 1;
	    axis_tdata_o <= {rx_q, 16'd0, rx_i, 16'd0};
	    cnt <= 0;
	 end
      end
   end

endmodule // rx_chain_model
`endif //  `ifndef _RX_CHAIN_MODEL_
