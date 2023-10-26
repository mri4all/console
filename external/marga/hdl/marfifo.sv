//-----------------------------------------------------------------------------
// Title         : marfifo
// Project       : marga
//-----------------------------------------------------------------------------
// File          : marfifo.sv
// Author        :   <vlad@vlad-laptop>
// Created       : 24.12.2020
// Last modified : 24.12.2020
//-----------------------------------------------------------------------------
// Description :
// RX FIFO to be used as part of marga
//
// NOTE: This FIFO relies on external logic to avoid reading out too
// much data, or it will fail. External logic should closely monitor
// locs_o, and avoid requesting more data than it contains - otherwise
// meaningless data will be returned.
//
//-----------------------------------------------------------------------------
// Copyright (c) 2020 by OCRA developers This model is the confidential and
// proprietary property of OCRA developers and the possession or use of this
// file requires a written license from OCRA developers.
//------------------------------------------------------------------------------

`ifndef _MARFIFO_
 `define _MARFIFO_

 `timescale 1ns/1ns

module marfifo #
  (
   parameter LENGTH = 16384,
   parameter WIDTH = 24
   )
   (
    input clk,
    input [WIDTH-1:0] data_i,
    input valid_i,

    input read_i, // output data was read, want to read next sample

    output reg [WIDTH-1:0] data_o, // always output mem data from current out address
    output reg valid_o, // new data is valid (when out address has changed)

    output reg [$clog2(LENGTH)-1:0] locs_o,
    output reg empty_o, full_o//, err_empty_o, err_full_o
    );

   initial begin
      data_o = 0;
      valid_o = 0;
      locs_o = 0;
      empty_o = 1;
      full_o = 0;
   end

   localparam ADDR_BITS = $clog2(LENGTH);
   reg [WIDTH-1:0] fifo_mem[LENGTH-1:0];
   reg [WIDTH-1:0] data_r = 0;
   reg [WIDTH-1:0] out_data_r = 0;
   reg [ADDR_BITS-1:0] in_ptr = 0, out_ptr = 0;
   reg [ADDR_BITS-1:0] ptr_diff = 0, ptr_diff_r = 0;
   reg 		       valid_r = 0, read_r = 0;

   always @(posedge clk) begin
      // TODO: encode stream more efficiently in 32b
      data_r <= data_i;
      // in_ptr_r <= in_ptr;
      // out_ptr_r <= out_ptr;
      ptr_diff <= in_ptr - out_ptr;
      {locs_o, ptr_diff_r} <= {ptr_diff_r, ptr_diff};

      read_r <= read_i;
      empty_o <= ptr_diff_r == 0;
      /* verilator lint_off WIDTH*/
      full_o <= ptr_diff_r >= LENGTH-4; // a bit of overhead
      /* verilator lint_on WIDTH*/

      valid_r <= valid_i && !full_o;

      if (valid_r && !full_o) begin
	 fifo_mem[in_ptr] <= data_r;
	 in_ptr <= in_ptr + 1;
      end

      // TODO: pipeline the output memory so that there are always 3-4
      // samples ready to read out, and the memory only goes dry when
      // the FIFO goes empty! Must work cycle-to-cycle.

      // always read out memory from current address
      out_data_r <= fifo_mem[out_ptr];
      data_o <= out_data_r;

      // if (read_i) valid_o <= 0;
      // if (!valid_o && !empty_o) valid_o <= 1;

      if (read_i) out_ptr <= out_ptr + 1;

      // if (read_r && !empty_o) begin
      // 	 out_ptr <= out_ptr + 1;
      // end
   end

endmodule // marfifo
`endif //  `ifndef _MARFIFO_
