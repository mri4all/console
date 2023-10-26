//-----------------------------------------------------------------------------
// Title         : mardecode_tb
// Project       : ocra
//-----------------------------------------------------------------------------
// File          : mardecode_tb.v
// Author        :   <vlad@arch-ssd>
// Created       : 13.09.2020
// Last modified : 13.09.2020
//-----------------------------------------------------------------------------
// Description :
//
// Testbench for mardecode, testing out the various features of the core
//
//-----------------------------------------------------------------------------
// Copyright (c) 2020 by OCRA developers This model is the confidential and
// proprietary property of OCRA developers and the possession or use of this
// file requires a written license from OCRA developers.
//------------------------------------------------------------------------------

`ifndef _MARDECODE_TB_
 `define _MARDECODE_TB_

 `include "mardecode.sv"

 `timescale 1ns/1ns

module mardecode_tb;
   // Width of S_AXI data bus
   parameter integer C_S_AXI_DATA_WIDTH = 32;
   // Width of S_AXI address bus
   parameter integer C_S_AXI_ADDR_WIDTH = 19;
   parameter BUFS = 24;
   parameter RX_FIFO_LENGTH = 16; // power of 2
   reg 		     err = 0;

   /*AUTOREGINPUT*/
   // Beginning of automatic reg inputs (for undeclared instantiated-module inputs)
   reg			S_AXI_ACLK;		// To UUT of mardecode.v
   reg [C_S_AXI_ADDR_WIDTH-1:0] S_AXI_ARADDR;	// To UUT of mardecode.v
   reg			S_AXI_ARESETN;		// To UUT of mardecode.v
   reg [2:0]		S_AXI_ARPROT;		// To UUT of mardecode.v
   reg			S_AXI_ARVALID;		// To UUT of mardecode.v
   reg [C_S_AXI_ADDR_WIDTH-1:0] S_AXI_AWADDR;	// To UUT of mardecode.v
   reg [2:0]		S_AXI_AWPROT;		// To UUT of mardecode.v
   reg			S_AXI_AWVALID;		// To UUT of mardecode.v
   reg			S_AXI_BREADY;		// To UUT of mardecode.v
   reg			S_AXI_RREADY;		// To UUT of mardecode.v
   reg [C_S_AXI_DATA_WIDTH-1:0] S_AXI_WDATA;	// To UUT of mardecode.v
   reg [(C_S_AXI_DATA_WIDTH/8)-1:0] S_AXI_WSTRB;// To UUT of mardecode.v
   reg			S_AXI_WVALID;		// To UUT of mardecode.v
   reg [63:0]		rx0_data;		// To UUT of mardecode.v
   reg			rx0_valid;		// To UUT of mardecode.v
   reg [63:0]		rx1_data;		// To UUT of mardecode.v
   reg			rx1_valid;		// To UUT of mardecode.v
   reg [31:0]		status_i;		// To UUT of mardecode.v
   reg [31:0]		status_latch_i;		// To UUT of mardecode.v
   reg			trig_i;			// To UUT of mardecode.v
   // End of automatics

   /*AUTOWIRE*/
   // Beginning of automatic wires (for undeclared instantiated-module outputs)
   wire			S_AXI_ARREADY;		// From UUT of mardecode.v
   wire			S_AXI_AWREADY;		// From UUT of mardecode.v
   wire [1:0]		S_AXI_BRESP;		// From UUT of mardecode.v
   wire			S_AXI_BVALID;		// From UUT of mardecode.v
   wire [C_S_AXI_DATA_WIDTH-1:0] S_AXI_RDATA;	// From UUT of mardecode.v
   wire [1:0]		S_AXI_RRESP;		// From UUT of mardecode.v
   wire			S_AXI_RVALID;		// From UUT of mardecode.v
   wire			S_AXI_WREADY;		// From UUT of mardecode.v
   wire [15:0]		data_o [BUFS-1:0];	// From UUT of mardecode.v
   wire			rx0_ready;		// From UUT of mardecode.v
   wire			rx1_ready;		// From UUT of mardecode.v
   wire [BUFS-1:0]	stb_o;			// From UUT of mardecode.v
   // End of automatics

   // Clock generation: assuming 100 MHz for convenience (in real design it'll be 122.88, 125 or 144 MHz depending on what's chosen)
   always #5 S_AXI_ACLK = !S_AXI_ACLK;

   integer 		k;

   // Stimuli and read/write checks
   initial begin
      $dumpfile("icarus_compile/000_mardecode_tb.lxt");
      $dumpvars(0, mardecode_tb);

      S_AXI_ACLK = 1;
      S_AXI_ARADDR = 0;
      S_AXI_ARESETN = 0;
      S_AXI_ARPROT = 0;
      S_AXI_ARVALID = 0;
      S_AXI_AWADDR = 0;
      S_AXI_AWPROT = 0;
      S_AXI_AWVALID = 0;
      S_AXI_BREADY = 0;
      S_AXI_RREADY = 0;
      S_AXI_WDATA = 0;
      S_AXI_WSTRB = 0;
      S_AXI_WVALID = 0;

      trig_i = 0;
      status_i = 0;
      status_latch_i = 0;

      #107 S_AXI_ARESETN = 1; // extra 7ns to ensure that TB stimuli occur a bit before the positive clock edges
      S_AXI_BREADY = 1; // TODO: make this more fine-grained if bus reads/writes don't work properly in hardware

      // Test program 1: go idle
      #10 wr32(19'h40000, {1'b0, UUT.INSTR_FINISH, 24'd0});
      wr32(19'h0, 32'h1);
      // read back state, and make sure it's HALT, then stop the FSM
      #100 rd32(19'h10, {4'd0, UUT.HALT, 24'd2});
      wr32(19'h0, 32'h0);

      // Wait for 0 cycles then go idle
      wr32(19'h40000, {1'b0, UUT.INSTR_WAIT, 24'd0});
      wr32(19'h40004, {1'b0, UUT.INSTR_FINISH, 24'd0});
      // just toggle briefly; doesn't matter if no readout occurs
      wr32(19'h0, 32'h1);
      wr32(19'h0, 32'h0);

      // Wait for 10 cycles then go idle (2 cycles extra from instruction set)
      #50 wr32(19'h40000, {1'b0, UUT.INSTR_WAIT, 24'd8});
      wr32(19'h40004, {1'b0, UUT.INSTR_FINISH, 24'd0});
      wr32(19'h0, 32'h1);
      wr32(19'h0, 32'h0);

      // Wait for 10 total cycles in two separate instructions then go idle
      #100 wr32(19'h40000, {1'b0, UUT.INSTR_WAIT, 24'd3});
      wr32(19'h40004, {1'b0, UUT.INSTR_WAIT, 24'd3});
      wr32(19'h40008, {1'b0, UUT.INSTR_FINISH, 24'd0});
      wr32(19'h0, 32'h1);
      wr32(19'h0, 32'h0);

      // Wait for 4 total cycles in two separate instructions then go idle
      #100 wr32(19'h40000, {1'b0, UUT.INSTR_WAIT, 24'd0});
      wr32(19'h40004, {1'b0, UUT.INSTR_WAIT, 24'd0});
      wr32(19'h40008, {1'b0, UUT.INSTR_FINISH, 24'd0});
      wr32(19'h0, 32'h1);
      wr32(19'h0, 32'h0);

      // Wait for trigger with a timeout of 10 then go idle
      #150 wr32(19'h40000, {1'b0, UUT.INSTR_TRIG, 24'd10});
      wr32(19'h40004, {1'b0, UUT.INSTR_FINISH, 24'd0});
      wr32(19'h0, 32'h1);
      wr32(19'h0, 32'h0);

      // Wait for trigger as before, long delay, but have a trigger occur this time
      #150 wr32(19'h40000, {1'b0, UUT.INSTR_TRIG, 24'd20});
      wr32(19'h40004, {1'b0, UUT.INSTR_FINISH, 24'd0});
      wr32(19'h0, 32'h1);
      wr32(19'h0, 32'h0);
      #60 trig_i = !trig_i;

      // Wait for trigger as before, long delay, but have a trigger occur this time - only this time, no timeout
      #150 wr32(19'h40000, {1'b0, UUT.INSTR_TRIG_FOREVER, 24'd0});
      wr32(19'h40004, {1'b0, UUT.INSTR_FINISH, 24'd0});
      wr32(19'h0, 32'h1);
      #90 trig_i = !trig_i;
      #40 wr32(19'h0, 32'h0);

      // Write multiple words with decreasing delay into buffers, so that they simultaneously appear at outputs
      #150 for (k = 0; k < BUFS; k = k + 1) wr32(19'h40000 + k*4, {1'b1, 7'(k), 8'(BUFS-k), 16'hde00 + 16'(k)});
      wr32(19'h40000 + BUFS*4, {1'b0, UUT.INSTR_FINISH, 24'd0});
      wr32(19'h0, 32'h1);
      wr32(19'h0, 32'h0);

      // Write multiple words into buffers, so that they appear in a burst at the outputs
      #500 for (k = 0; k < BUFS; k = k + 1) wr32(19'h40000 + k*4, {1'b1, 7'(k), 8'(BUFS-k + 70), 16'h1100 + 16'(k)});
      for (k = 0; k < BUFS; k = k + 1) wr32(19'h40000 + 1*(BUFS*4) + k*4, {1'b1, 7'(k), 8'd0, 16'h2200 + 16'(k)});
      for (k = 0; k < BUFS; k = k + 1) wr32(19'h40000 + 2*(BUFS*4) + k*4, {1'b1, 7'(k), 8'd0, 16'h3300 + 16'(k)});
      for (k = 0; k < BUFS; k = k + 1) wr32(19'h40000 + 3*(BUFS*4) + k*4, {1'b1, 7'(k), 8'd0, 16'h4400 + 16'(k)});
      wr32(19'h40000 + 4*(BUFS*4), {1'b0, UUT.INSTR_FINISH, 24'd0});
      wr32(19'h0, 32'h1);
      wr32(19'h0, 32'h0);

      // Overflow two different buffers
      #1110 rd32(19'h14, 0); // check error register is initially cleared
      for (k = 0; k < 5; k = k + 1) wr32(19'h40000 + k*4, {1'b1, 7'd0, 8'd9, 16'haaa0 + 16'(k)});
      for (k = 0; k < 5; k = k + 1) wr32(19'h40000 + (5+k)*4, {1'b1, 7'd23, 8'd9, 16'hbbb0 + 16'(k)});
      wr32(19'h40000 + 4*10, {1'b0, UUT.INSTR_FINISH, 24'd0});
      wr32(19'h0, 32'h1); // start FSM
      wr32(19'h0, 32'h0); // flag the FSM to stop later
      // read full register, make sure the full condition gets flagged, then cleared
      #200 rd32(19'h20, 'h800001);
      rd32(19'h14, 0);

      // Overflow a single buffer more severely, and record the error
      #1100 for (k = 0; k < 6; k = k + 1) wr32(19'h40000 + k*4, {1'b1, 7'd1, 8'd9, 16'hccc0 + 16'(k)});
      wr32(19'h40000 + 4*6, {1'b0, UUT.INSTR_FINISH, 24'd0});
      wr32(19'h0, 32'h1); // start FSM
      wr32(19'h0, 32'h0); // flag the FSM to stop later
      // read back error register, make sure the error gets flagged, then cleared
      #200 rd32(19'h1c, 'h2);
      rd32(19'h14, 0);

      // Direct writes to buffers
      #200 wr32(19'h8, {1'd0, 7'd0, 8'd0, 16'hdead});
      wr32(19'h8, {1'd0, 7'd12, 8'd0, 16'hbeef});
      wr32(19'h8, {1'd0, 7'd23, 8'd0, 16'hcafe});

      //// RX FIFO TESTS

      // Check initial status
      rd32(19'h28, 0);

      // FIRST TEST: pump a bunch of data into the FIFOs
      //
      for (k = 0; k < RX_FIFO_LENGTH/2; k = k + 1) begin
	 rx0_valid = 1;
	 rx1_valid = k % 2; // half the data rate
	 rx0_data <= 100 + k;
	 rx1_data <= 200 + k;
	 #10;
      end
      rx0_valid = 0;
      rx1_valid = 0;

      // check new status, after time has passed for FIFOs to update their fullness
      #30 rd32(19'h28, {16'(RX_FIFO_LENGTH/4), 16'(RX_FIFO_LENGTH/2)});

      // read out FIFOs (extra 10ns to take into account pipelining delay)
      for (k = 0; k < RX_FIFO_LENGTH/2; k = k + 1) #10 rd32(19'h2c, 100 + k);
      for (k = 0; k < RX_FIFO_LENGTH/2; k = k + 2) #10 rd32(19'h30, 201 + k);

      // Check final status (short delay for the data to update)
      #10 rd32(19'h28, 0);

      // NEXT TEST: pump a bunch of data into the FIFOs, overfilling them
      //
      for (k = 0; k < RX_FIFO_LENGTH+10; k = k + 1) begin
	 rx0_valid = 1;
	 rx1_valid = 1;
	 rx0_data <= 300 + k;
	 rx1_data <= 400 + k;
	 #10;
      end
      rx0_valid = 0;
      rx1_valid = 0;

      // check new status, after time has passed for FIFOs to update their fullness
      #30 rd32(19'h28, {16'(RX_FIFO_LENGTH-1), 16'(RX_FIFO_LENGTH-1)});

      // read out FIFOs (extra 10ns to take into account pipelining delay)
      for (k = 0; k < RX_FIFO_LENGTH-1; k = k + 1) #10 rd32(19'h2c, 300 + k);
      for (k = 0; k < RX_FIFO_LENGTH-1; k = k + 1) #10 rd32(19'h30, 400 + k);

      // Check final status (short delay for the data to update)
      #10 rd32(19'h28, 0);

      #5000 if (err) begin
	 $display("THERE WERE ERRORS");
	 $stop; // to return a nonzero error code if the testbench is later scripted at a higher level
      end
      $finish;
   end // initial begin

   // Output word checks at specific times
   integer n, p;
   wire [2:0] n_lsbs = n[2:0];
   initial begin
      // test timing/trigger instructions
      #185 check_state("PREPARE");
      #20 check_state("HALT");
      #150 check_state("HALT");
      #10 check_state("IDLE");

      #80 check_state("IDLE");
      #10 check_state("PREPARE");
      #50 check_state("HALT");
      #10 check_state("IDLE");

      #100 check_state("IDLE");
      #10 check_state("PREPARE");
      #100 check_state("COUNTDOWN");
      #30 check_state("HALT");
      #10 check_state("IDLE");

      #100 check_state("IDLE");
      #10 check_state("PREPARE");
      #110 check_state("COUNTDOWN");
      #30 check_state("HALT");
      #10 check_state("IDLE");

      #90 check_state("IDLE");
      #10 check_state("PREPARE");
      #20 check_state("COUNTDOWN");
      #60 check_state("HALT");
      #10 check_state("IDLE");

      #170 check_state("IDLE");
      #10 check_state("PREPARE");
      #120 check_state("TRIG");
      #30 check_state("HALT");
      #10 check_state("IDLE");

      #100 check_state("IDLE");
      #10 check_state("PREPARE");
      #120 check_state("TRIG");
      #30 check_state("HALT");
      #10 check_state("IDLE");

      #160 check_state("IDLE");
      #10 check_state("PREPARE");
      #120 check_state("TRIG_FOREV");
      #30 check_state("HALT");
      #10 check_state("IDLE");

      // test synchronised outputs via buffers
      #(40*BUFS + 260) for (k = 0; k < BUFS; k = k + 1) check_output(k, 16'hde00 + k);

      #(40*BUFS + 3210) for (k = 0; k < BUFS; k = k + 1) check_output(k, 16'h1100 + k);
      #10 for (k = 0; k < BUFS; k = k + 1) check_output(k, 16'h2200 + k);
      #10 for (k = 0; k < BUFS; k = k + 1) check_output(k, 16'h3300 + k);
      #10 for (k = 0; k < BUFS; k = k + 1) check_output(k, 16'h4400 + k);

      // check FIFO-full outputs
      #620 for (k = 0; k < 5; k = k + 1) begin
	 #50 check_output(0, 'haaa0 + k);
	 #50 check_output(23, 'hbbb0 + k);
      end

      // Check FIFO-overflown outputs
      #1220 check_output(1, 'hccc0);
      #100 check_output(1, 'hccc5);

      // check direct writes
      #350 check_output(0, 16'hdead);
      #30 check_output(12, 16'hbeef);
      #30 check_output(23, 16'hcafe);
   end // initial begin

   // Tasks for AXI bus reads and writes
   task wr32; //write to bus
      input [31:0] addr, data;
      begin
         #10 S_AXI_WDATA = data;
	 S_AXI_WSTRB = 'hf;
         S_AXI_AWADDR = addr;
         S_AXI_AWVALID = 1;
         S_AXI_WVALID = 1;
         fork
            begin: wait_axi_write
               wait(S_AXI_AWREADY && S_AXI_WREADY);
               disable axi_write_timeout;
            end
            begin: axi_write_timeout
               #10000 disable wait_axi_write;
	       $display("%d ns: AXI write timed out", $time);
            end
         join
         #13 S_AXI_AWVALID = 0;
         S_AXI_WVALID = 0;
      end
   endtask // wr32

   task rd32; //read from bus
      input [31:0] addr;
      input [31:0] expected;
      begin
         #10 S_AXI_ARVALID = 1;
         S_AXI_ARADDR = addr;
         wait(S_AXI_ARREADY);
         #13 S_AXI_ARVALID = 0;
         wait(S_AXI_RVALID);
         #13 if (expected !== S_AXI_RDATA) begin
            $display("%d ns: Bus read error, address %x, expected output %x, read %x.",
		     $time, addr, expected, S_AXI_RDATA);
            err <= 1'd1;
         end
         S_AXI_RREADY = 1;
         S_AXI_ARVALID = 0;
         #10 S_AXI_RREADY = 0;
      end
   endtask // rd32

   task check_output;
      input [$clog2(BUFS)-1:0] ch;
      input [15:0] data;
      begin
	 if (stb_o[ch] == 0) begin
	    $display("%d ns: stb_o[%d] low, expected high", $time, ch);
	    err <= 1;
	 end
	 if (data != data_o[ch]) begin
	    $display("%d ns: data_o[%d] expected 0x%x, saw 0x%x", $time, ch, data, data_o[ch]);
	    err <= 1;
	 end
      end
   endtask // check_output

   task check_state;
      input [79:0] expected;
      begin
	 if (state_ascii != expected) begin
	    $display("%d ns: state expected %s, saw %s", $time, expected, state_ascii);
	    err <= 1;
	 end
      end
   endtask

   mardecode #(/*AUTOINSTPARAM*/
	       // Parameters
	       .C_S_AXI_DATA_WIDTH	(C_S_AXI_DATA_WIDTH),
	       .C_S_AXI_ADDR_WIDTH	(C_S_AXI_ADDR_WIDTH),
	       .BUFS			(BUFS),
	       .RX_FIFO_LENGTH		(RX_FIFO_LENGTH))
   UUT(/*AUTOINST*/
       // Outputs
       .data_o				(data_o/*[15:0].[BUFS-1:0]*/),
       .stb_o				(stb_o[BUFS-1:0]),
       .rx0_ready			(rx0_ready),
       .rx1_ready			(rx1_ready),
       .S_AXI_AWREADY			(S_AXI_AWREADY),
       .S_AXI_WREADY			(S_AXI_WREADY),
       .S_AXI_BRESP			(S_AXI_BRESP[1:0]),
       .S_AXI_BVALID			(S_AXI_BVALID),
       .S_AXI_ARREADY			(S_AXI_ARREADY),
       .S_AXI_RDATA			(S_AXI_RDATA[C_S_AXI_DATA_WIDTH-1:0]),
       .S_AXI_RRESP			(S_AXI_RRESP[1:0]),
       .S_AXI_RVALID			(S_AXI_RVALID),
       // Inputs
       .trig_i				(trig_i),
       .status_i			(status_i[31:0]),
       .status_latch_i			(status_latch_i[31:0]),
       .rx0_data			(rx0_data[63:0]),
       .rx0_valid			(rx0_valid),
       .rx1_data			(rx1_data[63:0]),
       .rx1_valid			(rx1_valid),
       .S_AXI_ACLK			(S_AXI_ACLK),
       .S_AXI_ARESETN			(S_AXI_ARESETN),
       .S_AXI_AWADDR			(S_AXI_AWADDR[C_S_AXI_ADDR_WIDTH-1:0]),
       .S_AXI_AWPROT			(S_AXI_AWPROT[2:0]),
       .S_AXI_AWVALID			(S_AXI_AWVALID),
       .S_AXI_WDATA			(S_AXI_WDATA[C_S_AXI_DATA_WIDTH-1:0]),
       .S_AXI_WSTRB			(S_AXI_WSTRB[(C_S_AXI_DATA_WIDTH/8)-1:0]),
       .S_AXI_WVALID			(S_AXI_WVALID),
       .S_AXI_BREADY			(S_AXI_BREADY),
       .S_AXI_ARADDR			(S_AXI_ARADDR[C_S_AXI_ADDR_WIDTH-1:0]),
       .S_AXI_ARPROT			(S_AXI_ARPROT[2:0]),
       .S_AXI_ARVALID			(S_AXI_ARVALID),
       .S_AXI_RREADY			(S_AXI_RREADY));

   // Wires purely for debugging (since GTKwave can't access a single RAM word directly)
   wire [31:0] bram_a0 = UUT.mar_bram[0],
	       bram_a1 = UUT.mar_bram[1],
	       bram_a1024 = UUT.mar_bram[1024],
	       bram_a8000 = UUT.mar_bram[8000],
	       bram_amax = UUT.mar_bram[65535];

   wire [15:0] data0_o = data_o[0], data1_o = data_o[1], data2_o = data_o[2], data3_o = data_o[3],
	       data4_o = data_o[4], data5_o = data_o[5], data6_o = data_o[6], data7_o = data_o[7],
	       data8_o = data_o[8], data9_o = data_o[9], data10_o = data_o[10], data11_o = data_o[11],
	       data12_o = data_o[12], data13_o = data_o[13], data14_o = data_o[14], data15_o = data_o[15],
	       data16_o = data_o[16], data17_o = data_o[17], data18_o = data_o[18], data19_o = data_o[19],
	       data20_o = data_o[20], data21_o = data_o[21], data22_o = data_o[22], data23_o = data_o[23];

   reg [79:0]  state_ascii = 0;
   always @(UUT.state) begin
      case (UUT.state)
	UUT.IDLE: state_ascii = "IDLE";
	UUT.PREPARE: state_ascii = "PREPARE";
	UUT.RUN: state_ascii = "RUN";
	UUT.COUNTDOWN: state_ascii = "COUNTDOWN";
	UUT.TRIG: state_ascii = "TRIG";
	UUT.TRIG_FOREVER: state_ascii = "TRIG_FOREV";
	UUT.HALT: state_ascii="HALT";
	default: state_ascii="UNKNOWN?";
      endcase // case (UUT.state)
   end
endmodule // mardecode_tb
`endif //  `ifndef _MARDECODE_TB_
