//-----------------------------------------------------------------------------
// Title         : marbuffer
// Project       : marga
//-----------------------------------------------------------------------------
// File          : marbuffer.sv
// Author        :   <vlad@arch-ssd>
// Created       : 17.12.2020
// Last modified : 17.12.2020
//-----------------------------------------------------------------------------
// Description :
//
// Simple buffer with variable-length FIFO, 16b input, 8b timing
// delay, 16b output after delay has passed. Minimum 8b delay is 0,
// which implies 1 clock cycle until the next FIFO output.
//
//-----------------------------------------------------------------------------
// Copyright (c) 2020 by OCRA developers This model is the confidential and
// proprietary property of OCRA developers and the possession or use of this
// file requires a written license from OCRA developers.
//------------------------------------------------------------------------------

`ifndef _MARBUFFER_
 `define _MARBUFFER_

 `timescale 1ns / 1ns

module marbuffer #
  (parameter fifo_size = 2)
   (
    input 	      clk,
    input [15:0]      data_i,
    input [6:0]       delay_i,
    input 	      valid_i,
    input 	      direct_i,
    output reg [15:0] data_o,
    output reg 	      empty_o,
    output reg	      full_o, // combinational for speed; latch until no longer full
    output reg 	      err_o, // strobe when data is rejected
    output reg 	      stb_o // single-cycle strobe output
    );

   localparam fifo_addr_bits = $clog2(fifo_size);

   reg 		      valid_r = 0;
   reg [22:0] 	      fifo[fifo_size-1:0];
   reg [22:0] 	      fifo_in_r = 0;
   reg [fifo_addr_bits-1:0] fifo_in_ptr = 0, fifo_out_ptr = 0;
   reg [fifo_addr_bits-1:0] fifo_in_ptr_r = 0;

   wire signed [fifo_addr_bits-1:0] fifo_ptr_diff = fifo_in_ptr - fifo_out_ptr;
   reg signed [fifo_addr_bits-1:0]  fifo_ptr_diff_r = 0;

   wire 		     fifo_ptrs_equal = fifo_ptr_diff == 0;
   wire 		     fifo_ptrs_almost_equal = fifo_ptr_diff == 1;

   reg 			     fifo_ptrs_equal_r = 1;
   reg 			     fifo_ptrs_almost_equal_r = 0;

   wire 		     fifo_has_emptied = fifo_ptrs_equal && fifo_ptrs_almost_equal_r;

   reg [15:0] 		     data_r = 0;
   reg [6:0] 		     delay_cnt = 0;
   wire 		     delay_cnt_almost_zero = delay_cnt == 1;

   wire [22:0] 		     fifo_out = fifo[fifo_out_ptr];
   reg 			     direct_r = 0;
   reg [15:0] 		     data_direct_r = 0;

   integer 		     k;
   initial begin
      data_o = 0;
      stb_o = 0;
      empty_o = 1;
      full_o = 0;
      err_o = 0;
      for (k = 0; k < fifo_size; k = k + 1) fifo[k] = 0;
   end

   localparam IDLE = 0, LOAD = 1, WAIT = 2;
   reg [1:0] state = IDLE;

   always @(posedge clk) begin
      valid_r <= valid_i;
      fifo_in_ptr_r <= fifo_in_ptr;
      fifo_ptr_diff_r <= fifo_ptr_diff;
      fifo_ptrs_almost_equal_r <= fifo_ptrs_almost_equal;
      fifo_ptrs_equal_r <= fifo_ptrs_equal;
      // defaults
      stb_o <= 0;

      case (state)
	default: begin
	   if (valid_r) begin
	      state <= LOAD;
	   end
	end
	LOAD: begin
	   // Read current output, increment
	   fifo_out_ptr <= fifo_out_ptr + 1;
	   if (fifo_out[22:16] == 0) begin
	      data_o <= fifo_out[15:0]; // direct output, don't use counter
	      stb_o <= 1;
	      // almost out of data, and no new data has arrived
	      if (fifo_ptrs_almost_equal && !valid_r) state <= IDLE;
	   end else begin // use counter
	      data_r <= fifo_out[15:0];
	      delay_cnt <= fifo_out[22:16];
	      state <= WAIT;
	   end
	end // case: LOAD
	WAIT: begin
	   delay_cnt <= delay_cnt - 1;
	   if (delay_cnt_almost_zero) begin
	      data_o <= data_r;
	      stb_o <= 1;
	      if ( (fifo_has_emptied || empty_o) && !valid_r) state <= IDLE;
	      else state <= LOAD;
	   end
	end // case: WAIT
      endcase // case (state)

      // Pipelined write-side logic
      valid_r <= valid_i;
      if (valid_i) begin
	 fifo_in_r <= {delay_i, data_i};
       	 fifo_in_ptr <= fifo_in_ptr + 1;
      end
      if (valid_r) fifo[fifo_in_ptr_r] <= fifo_in_r;

      // FIFO-full and error flags
      if ( (fifo_ptr_diff == 0) && (fifo_ptr_diff_r == -1) ) full_o <= 1;
      else if (fifo_ptr_diff != 0) full_o <= 0; // cancel full flag whether things are fine or an error occurred
      err_o <= full_o && fifo_ptr_diff == +1; // overflow event; self-clearing

      // FIFO-empty logic
      if (fifo_has_emptied) empty_o <= 1;
      else if (fifo_ptrs_equal_r && fifo_ptrs_almost_equal) empty_o <= 0;

      // pass-through; will override any current FIFO queues until the
      // next FIFO output event - best used when FIFO is empty
      direct_r <= direct_i;
      if (direct_i) data_direct_r <= data_i;
      if (direct_r) begin
	 data_o <= data_direct_r;
	 stb_o <= 1;
      end
   end

endmodule // marbuffer
`endif //  `ifndef _MARBUFFER_
