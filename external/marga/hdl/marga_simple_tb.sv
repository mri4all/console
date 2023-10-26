//-----------------------------------------------------------------------------
// Title         : marga_simple_tb
// Project       : marga
//-----------------------------------------------------------------------------
// File          : marga_simple_tb.sv
// Author        :   <vlad@vlad-laptop>
// Created       : 25.12.2020
// Last modified : 25.12.2020
//-----------------------------------------------------------------------------
// Description :
//
// Low-level testbench for marga, mainly to help with HDL design
// rather to exercise all possible functionality. Only uses 'immediate
// output' functionality to test the system features; see more
// advanced testbenches for streaming tests.
//
//-----------------------------------------------------------------------------
// Copyright (c) 2020 by OCRA developers This model is the confidential and
// proprietary property of OCRA developers and the possession or use of this
// file requires a written license from OCRA developers.
//------------------------------------------------------------------------------

`ifndef _MARGA_SIMPLE_TB_
 `define _MARGA_SIMPLE_TB_

 `include "marga.sv"
 `include "ocra1_model.sv"
 `include "gpa_fhdo_model.sv"
 `include "rx_chain_model.sv"

 `timescale 1ns/1ns

module marga_simple_tb;
   localparam C_S0_AXI_ADDR_WIDTH = 19, C_S0_AXI_DATA_WIDTH = 32;

   reg err = 0;
   wire fhdo_sdi_i;
   /*AUTOREGINPUT*/
   // Beginning of automatic reg inputs (for undeclared instantiated-module inputs)
   reg [31:0]		dds0_iq_axis_tdata_i;	// To UUT of marga.v
   reg			dds0_iq_axis_tvalid_i;	// To UUT of marga.v
   reg [31:0]		dds1_iq_axis_tdata_i;	// To UUT of marga.v
   reg			dds1_iq_axis_tvalid_i;	// To UUT of marga.v
   reg [31:0]		dds2_iq_axis_tdata_i;	// To UUT of marga.v
   reg			dds2_iq_axis_tvalid_i;	// To UUT of marga.v
   reg [63:0]		rx0_axis_tdata_i;	// To UUT of marga.v
   reg			rx0_axis_tvalid_i;	// To UUT of marga.v
   reg [63:0]		rx1_axis_tdata_i;	// To UUT of marga.v
   reg			rx1_axis_tvalid_i;	// To UUT of marga.v
   reg			s0_axi_aclk;		// To UUT of marga.v
   reg [C_S0_AXI_ADDR_WIDTH-1:0] s0_axi_araddr;	// To UUT of marga.v
   reg			s0_axi_aresetn;		// To UUT of marga.v
   reg [2:0]		s0_axi_arprot;		// To UUT of marga.v
   reg			s0_axi_arvalid;		// To UUT of marga.v
   reg [C_S0_AXI_ADDR_WIDTH-1:0] s0_axi_awaddr;	// To UUT of marga.v
   reg [2:0]		s0_axi_awprot;		// To UUT of marga.v
   reg			s0_axi_awvalid;		// To UUT of marga.v
   reg			s0_axi_bready;		// To UUT of marga.v
   reg			s0_axi_rready;		// To UUT of marga.v
   reg [C_S0_AXI_DATA_WIDTH-1:0] s0_axi_wdata;	// To UUT of marga.v
   reg [(C_S0_AXI_DATA_WIDTH/8)-1:0] s0_axi_wstrb;// To UUT of marga.v
   reg			s0_axi_wvalid;		// To UUT of marga.v
   reg			trig_i;			// To UUT of marga.v
   // End of automatics
   /*AUTOWIRE*/
   // Beginning of automatic wires (for undeclared instantiated-module outputs)
   wire [23:0]		dds0_phase_axis_tdata_o;// From UUT of marga.v
   wire			dds0_phase_axis_tvalid_o;// From UUT of marga.v
   wire [23:0]		dds1_phase_axis_tdata_o;// From UUT of marga.v
   wire			dds1_phase_axis_tvalid_o;// From UUT of marga.v
   wire [23:0]		dds2_phase_axis_tdata_o;// From UUT of marga.v
   wire			dds2_phase_axis_tvalid_o;// From UUT of marga.v
   wire			fhdo_clk_o;		// From UUT of marga.v
   wire			fhdo_sdo_o;		// From UUT of marga.v
   wire			fhdo_ssn_o;		// From UUT of marga.v
   wire [7:0]		leds_o;			// From UUT of marga.v
   wire			ocra1_clk_o;		// From UUT of marga.v
   wire			ocra1_ldacn_o;		// From UUT of marga.v
   wire			ocra1_sdox_o;		// From UUT of marga.v
   wire			ocra1_sdoy_o;		// From UUT of marga.v
   wire			ocra1_sdoz2_o;		// From UUT of marga.v
   wire			ocra1_sdoz_o;		// From UUT of marga.v
   wire			ocra1_syncn_o;		// From UUT of marga.v
   wire			rx0_axis_tready_o;	// From UUT of marga.v
   wire [31:0]		rx0_dds_iq_axis_tdata_o;// From UUT of marga.v
   wire			rx0_dds_iq_axis_tvalid_o;// From UUT of marga.v
   wire			rx0_en_o;		// From UUT of marga.v
   wire [15:0]		rx0_rate_axis_tdata_o;	// From UUT of marga.v
   wire			rx0_rate_axis_tvalid_o;	// From UUT of marga.v
   wire			rx0_rst_n_o;		// From UUT of marga.v
   wire			rx1_axis_tready_o;	// From UUT of marga.v
   wire [31:0]		rx1_dds_iq_axis_tdata_o;// From UUT of marga.v
   wire			rx1_dds_iq_axis_tvalid_o;// From UUT of marga.v
   wire			rx1_en_o;		// From UUT of marga.v
   wire [15:0]		rx1_rate_axis_tdata_o;	// From UUT of marga.v
   wire			rx1_rate_axis_tvalid_o;	// From UUT of marga.v
   wire			rx1_rst_n_o;		// From UUT of marga.v
   wire			rx_gate_o;		// From UUT of marga.v
   wire			s0_axi_arready;		// From UUT of marga.v
   wire			s0_axi_awready;		// From UUT of marga.v
   wire [1:0]		s0_axi_bresp;		// From UUT of marga.v
   wire			s0_axi_bvalid;		// From UUT of marga.v
   wire [C_S0_AXI_DATA_WIDTH-1:0] s0_axi_rdata;	// From UUT of marga.v
   wire [1:0]		s0_axi_rresp;		// From UUT of marga.v
   wire			s0_axi_rvalid;		// From UUT of marga.v
   wire			s0_axi_wready;		// From UUT of marga.v
   wire			trig_o;			// From UUT of marga.v
   wire [31:0]		tx0_axis_tdata_o;	// From UUT of marga.v
   wire			tx0_axis_tvalid_o;	// From UUT of marga.v
   wire [31:0]		tx1_axis_tdata_o;	// From UUT of marga.v
   wire			tx1_axis_tvalid_o;	// From UUT of marga.v
   wire			tx_gate_o;		// From UUT of marga.v
   // End of automatics

   wire signed [17:0] 		ocra1_voutx, ocra1_vouty, ocra1_voutz, ocra1_voutz2;
   wire [15:0] 		fhdo_voutx, fhdo_vouty, fhdo_voutz, fhdo_voutz2;

   wire 		clk = s0_axi_aclk;
   always #5 s0_axi_aclk = !s0_axi_aclk;
   integer k;

   initial begin
      $dumpfile("icarus_compile/000_marga_simple_tb.lxt");
      $dumpvars(0, marga_simple_tb);

      // rx0_axis_tdata_i = 0;
      // rx0_axis_tvalid_i = 0;
      // rx1_axis_tdata_i = 0;
      // rx1_axis_tvalid_i = 0;
      s0_axi_aclk = 1;
      s0_axi_araddr = 0;
      s0_axi_aresetn = 0;
      s0_axi_arprot = 0;
      s0_axi_arvalid = 0;
      s0_axi_awaddr = 0;
      s0_axi_awprot = 0;
      s0_axi_awvalid = 0;
      s0_axi_bready = 0;
      s0_axi_rready = 0;
      s0_axi_wdata = 0;
      s0_axi_wstrb = 0;
      s0_axi_wvalid = 0;
      trig_i = 0;

      #7 s0_axi_aresetn = 1; // extra 7ns to ensure that TB stimuli occur a bit before the positive clock edges
      s0_axi_bready = 1; // TODO: make this more fine-grained if bus reads/writes don't work properly in hardware

      // enable ocra1, disable gpa-fhdo, set SPI clock div to 5, reset ocra1
      #10 wr32(19'h8, {1'b0, 7'd0, 8'd0, {4'd0, 1'd0, 1'd0, 6'd5, 1'd0, 1'd1}});
      wr32(19'h8, {1'b0, 7'd0, 8'd0, {4'd0, 1'd0, 1'd1, 6'd1, 1'd0, 1'd1}}); // un-reset ocra1

      // ocra1 control words
      wr32(19'h8, {1'b0, 7'd2, 8'd0, 16'h0020}); // MSBs for SPI out, ch0
      wr32(19'h8, {1'b0, 7'd1, 8'd0, 16'h0010}); // LSBs for SPI out, ch0

      wr32(19'h8, {1'b0, 7'd2, 8'd0, 16'h0220}); // MSBs for SPI out, ch1
      wr32(19'h8, {1'b0, 7'd1, 8'd0, 16'h0010}); // LSBs for SPI out, ch1

      wr32(19'h8, {1'b0, 7'd2, 8'd0, 16'h0420}); // MSBs for SPI out, ch2
      wr32(19'h8, {1'b0, 7'd1, 8'd0, 16'h0010}); // LSBs for SPI out, ch2

      wr32(19'h8, {1'b0, 7'd2, 8'd0, 16'h0720}); // MSBs for SPI out, ch3
      wr32(19'h8, {1'b0, 7'd1, 8'd0, 16'h0010}); // LSBs for SPI out, ch3

      check_ocra1(0, 0, 0, 0);
      check_fhdo('h8000, 'h8000, 'h8000, 'h8000);

      // ocra1 DAC words
      #500;
      wr32(19'h8, {1'b0, 7'd2, 8'd0, 16'h001f}); // MSBs for SPI out, ch0
      wr32(19'h8, {1'b0, 7'd1, 8'd0, 16'hfffc}); // LSBs for SPI out, ch0

      wr32(19'h8, {1'b0, 7'd2, 8'd0, 16'h021f}); // MSBs for SPI out, ch1
      wr32(19'h8, {1'b0, 7'd1, 8'd0, 16'hfff8}); // LSBs for SPI out, ch1

      wr32(19'h8, {1'b0, 7'd2, 8'd0, 16'h041f}); // MSBs for SPI out, ch2
      wr32(19'h8, {1'b0, 7'd1, 8'd0, 16'hfff4}); // LSBs for SPI out, ch2

      wr32(19'h8, {1'b0, 7'd2, 8'd0, 16'h071f}); // MSBs for SPI out, ch3
      wr32(19'h8, {1'b0, 7'd1, 8'd0, 16'hfff0}); // LSBs for SPI out, ch3

      // enable GPA-FHDO
      wr32(19'h8, {1'b0, 7'd0, 8'd0, {14'd0, 1'd0, 6'd2, 1'd1, 1'd0}});

      // GPA-FHDO control word
      wr32(19'h8, {1'b0, 7'd2, 8'd0, 16'h0002}); // MSBs
      wr32(19'h8, {1'b0, 7'd1, 8'd0, 16'h0000}); // LSBs

      // GPA-FHDO DAC words
      #800 wr32(19'h8, {1'b0, 7'd2, 8'd0, 16'h0008});
      wr32(19'h8, {1'b0, 7'd1, 8'd0, 16'hfffe});

      #800 wr32(19'h8, {1'b0, 7'd2, 8'd0, 16'h0009});
      wr32(19'h8, {1'b0, 7'd1, 8'd0, 16'hfffd});

      #800 wr32(19'h8, {1'b0, 7'd2, 8'd0, 16'h000a});
      wr32(19'h8, {1'b0, 7'd1, 8'd0, 16'hfffc});

      #800 wr32(19'h8, {1'b0, 7'd2, 8'd0, 16'h000b});
      wr32(19'h8, {1'b0, 7'd1, 8'd0, 16'hfffb});

      // check gradient core outputs
      #500 check_ocra1(-1, -2, -3, -4);
      #500 check_fhdo(65534, 65533, 65532, 65531);

      // RX 0 and RX 1 settings control
      // #800 wr32(19'8, {1'b0, 7'd3, 8'd0, })
      // TODO Continue here

      #5000 if (err) begin
	 $display("THERE WERE ERRORS");
	 $stop; // to return a nonzero error code if the testbench is later scripted at a higher level
      end
      $finish;
   end // initial begin

   // Timed checks
   initial begin
   end

   // Tasks for AXI bus reads and writes
   task wr32; //write to bus
      input [31:0] addr, data;
      begin
         #10 s0_axi_wdata = data;
	 s0_axi_wstrb = 'hf;
         s0_axi_awaddr = addr;
         s0_axi_awvalid = 1;
         s0_axi_wvalid = 1;
         fork
            begin: wait_axi_write
               wait(s0_axi_awready && s0_axi_wready);
               disable axi_write_timeout;
            end
            begin: axi_write_timeout
               #10000 disable wait_axi_write;
	       $display("%d ns: AXI write timed out", $time);
            end
         join
         #13 s0_axi_awvalid = 0;
         s0_axi_wvalid = 0;
      end
   endtask // wr32

   task rd32; //read from bus
      input [31:0] addr;
      input [31:0] expected;
      begin
         #10 s0_axi_arvalid = 1;
         s0_axi_araddr = addr;
         wait(s0_axi_arready);
         #13 s0_axi_arvalid = 0;
         wait(s0_axi_rvalid);
         #13 if (expected !== s0_axi_rdata) begin
            $display("%d ns: Bus read error, address %x, expected output %x, read %x.",
		     $time, addr, expected, s0_axi_rdata);
            err <= 1'd1;
         end
         s0_axi_rready = 1;
         s0_axi_arvalid = 0;
         #10 s0_axi_rready = 0;
      end
   endtask // rd32

   task check_ocra1;
      input signed [17:0] vx, vy, vz, vz2;
      begin
	 if (vx != ocra1_voutx) begin
	    $error("ocra1 voutx %d, expected %d", ocra1_voutx, vx);
	    err <= 1;
	 end
	 if (vy != ocra1_vouty) begin
	    $error("ocra1 vouty %d, expected %d", ocra1_vouty, vy);
	    err <= 1;
	 end
	 if (vz != ocra1_voutz) begin
	    $error("ocra1 voutz %d, expected %d", ocra1_voutz, vz);
	    err <= 1;
	 end
	 if (vz2 != ocra1_voutz2) begin
	    $error("ocra1 voutz2 %d, expected %d", ocra1_voutz2, vz2);
	    err <= 1;
	 end
      end
   endtask // check_ocra1

   task check_fhdo;
      input signed [15:0] vx, vy, vz, vz2;
      begin
	 if (vx != fhdo_voutx) begin
	    $error("fhdo voutx %d, expected %d", fhdo_voutx, vx);
	    err <= 1;
	 end
	 if (vy != fhdo_vouty) begin
	    $error("fhdo vouty %d, expected %d", fhdo_vouty, vy);
	    err <= 1;
	 end
	 if (vz != fhdo_voutz) begin
	    $error("fhdo voutz %d, expected %d", fhdo_voutz, vz);
	    err <= 1;
	 end
	 if (vz2 != fhdo_voutz2) begin
	    $error("fhdo voutz2 %d, expected %d", fhdo_voutz2, vz2);
	    err <= 1;
	 end
      end
   endtask

   ocra1_model
   ocra1(
	 // Outputs
	 .voutx				(ocra1_voutx[17:0]),
	 .vouty				(ocra1_vouty[17:0]),
	 .voutz				(ocra1_voutz[17:0]),
	 .voutz2			(ocra1_voutz2[17:0]),
	 // Inputs
	 .clk				(ocra1_clk_o),
	 .syncn				(ocra1_syncn_o),
	 .ldacn				(ocra1_ldacn_o),
	 .sdox				(ocra1_sdox_o),
	 .sdoy				(ocra1_sdoy_o),
	 .sdoz				(ocra1_sdoz_o),
	 .sdoz2				(ocra1_sdoz2_o));

   gpa_fhdo_model
   fhdo(
	// Outputs
	.sdi				(fhdo_sdi_i),
	.voutx				(fhdo_voutx[15:0]),
	.vouty				(fhdo_vouty[15:0]),
	.voutz				(fhdo_voutz[15:0]),
	.voutz2				(fhdo_voutz2[15:0]),
	// Inputs
	.clk				(fhdo_clk_o),
	.csn				(fhdo_ssn_o),
	.sdo				(fhdo_sdo_o));

   rx_chain_model rx0(
		      // Outputs
		      .axis_tvalid_o(rx0_axis_tvalid_i),
		      .axis_tdata_o(rx0_axis_tdata_i),
		      // Inputs
		      .clk(s0_axi_aclk),
		      .rst_n(rx0_rst_n_o),
		      .rate_axis_tdata_i(rx0_rate_axis_tdata_o),
		      .rate_axis_tvalid_i(rx0_rate_axis_tvalid_o),

		      .rx_iq_axis_tdata_i(rx0_dds_iq_axis_tdata_o),
		      .rx_iq_axis_tvalid_i(rx0_dds_iq_axis_tvalid_o),

		      .axis_tready_i(rx0_axis_tready_o)
		      );

   rx_chain_model rx1(// Outputs
		      .axis_tvalid_o(rx1_axis_tvalid_i),
		      .axis_tdata_o(rx1_axis_tdata_i),
		      // Inputs
		      .clk(s0_axi_aclk),
		      .rst_n(rx1_rst_n_o),
		      .rate_axis_tdata_i(rx1_rate_axis_tdata_o),
		      .rate_axis_tvalid_i(rx1_rate_axis_tvalid_o),

		      .rx_iq_axis_tdata_i(rx1_dds_iq_axis_tdata_o),
		      .rx_iq_axis_tvalid_i(rx1_dds_iq_axis_tvalid_o),

		      .axis_tready_i(rx1_axis_tready_o)
		      );

   marga #(/*AUTOINSTPARAM*/
	    // Parameters
	    .C_S0_AXI_DATA_WIDTH	(C_S0_AXI_DATA_WIDTH),
	    .C_S0_AXI_ADDR_WIDTH	(C_S0_AXI_ADDR_WIDTH))
   UUT(/*AUTOINST*/
       // Outputs
       .ocra1_clk_o			(ocra1_clk_o),
       .ocra1_syncn_o			(ocra1_syncn_o),
       .ocra1_ldacn_o			(ocra1_ldacn_o),
       .ocra1_sdox_o			(ocra1_sdox_o),
       .ocra1_sdoy_o			(ocra1_sdoy_o),
       .ocra1_sdoz_o			(ocra1_sdoz_o),
       .ocra1_sdoz2_o			(ocra1_sdoz2_o),
       .fhdo_clk_o			(fhdo_clk_o),
       .fhdo_sdo_o			(fhdo_sdo_o),
       .fhdo_ssn_o			(fhdo_ssn_o),
       .tx_gate_o			(tx_gate_o),
       .rx_gate_o			(rx_gate_o),
       .dds0_phase_axis_tdata_o		(dds0_phase_axis_tdata_o[23:0]),
       .dds1_phase_axis_tdata_o		(dds1_phase_axis_tdata_o[23:0]),
       .dds2_phase_axis_tdata_o		(dds2_phase_axis_tdata_o[23:0]),
       .dds0_phase_axis_tvalid_o	(dds0_phase_axis_tvalid_o),
       .dds1_phase_axis_tvalid_o	(dds1_phase_axis_tvalid_o),
       .dds2_phase_axis_tvalid_o	(dds2_phase_axis_tvalid_o),
       .rx0_rst_n_o			(rx0_rst_n_o),
       .rx1_rst_n_o			(rx1_rst_n_o),
       .rx0_en_o			(rx0_en_o),
       .rx1_en_o			(rx1_en_o),
       .rx0_rate_axis_tdata_o		(rx0_rate_axis_tdata_o[15:0]),
       .rx1_rate_axis_tdata_o		(rx1_rate_axis_tdata_o[15:0]),
       .rx0_rate_axis_tvalid_o		(rx0_rate_axis_tvalid_o),
       .rx1_rate_axis_tvalid_o		(rx1_rate_axis_tvalid_o),
       .trig_o				(trig_o),
       .rx0_axis_tready_o		(rx0_axis_tready_o),
       .rx1_axis_tready_o		(rx1_axis_tready_o),
       .rx0_dds_iq_axis_tdata_o		(rx0_dds_iq_axis_tdata_o[31:0]),
       .rx1_dds_iq_axis_tdata_o		(rx1_dds_iq_axis_tdata_o[31:0]),
       .rx0_dds_iq_axis_tvalid_o	(rx0_dds_iq_axis_tvalid_o),
       .rx1_dds_iq_axis_tvalid_o	(rx1_dds_iq_axis_tvalid_o),
       .tx0_axis_tdata_o		(tx0_axis_tdata_o[31:0]),
       .tx0_axis_tvalid_o		(tx0_axis_tvalid_o),
       .tx1_axis_tdata_o		(tx1_axis_tdata_o[31:0]),
       .tx1_axis_tvalid_o		(tx1_axis_tvalid_o),
       .leds_o				(leds_o[7:0]),
       .s0_axi_awready			(s0_axi_awready),
       .s0_axi_wready			(s0_axi_wready),
       .s0_axi_bresp			(s0_axi_bresp[1:0]),
       .s0_axi_bvalid			(s0_axi_bvalid),
       .s0_axi_arready			(s0_axi_arready),
       .s0_axi_rdata			(s0_axi_rdata[C_S0_AXI_DATA_WIDTH-1:0]),
       .s0_axi_rresp			(s0_axi_rresp[1:0]),
       .s0_axi_rvalid			(s0_axi_rvalid),
       // Inputs
       .fhdo_sdi_i			(fhdo_sdi_i),
       .trig_i				(trig_i),
       .rx0_axis_tvalid_i		(rx0_axis_tvalid_i),
       .rx0_axis_tdata_i		(rx0_axis_tdata_i[63:0]),
       .rx1_axis_tvalid_i		(rx1_axis_tvalid_i),
       .rx1_axis_tdata_i		(rx1_axis_tdata_i[63:0]),
       .dds0_iq_axis_tdata_i		(dds0_iq_axis_tdata_i[31:0]),
       .dds1_iq_axis_tdata_i		(dds1_iq_axis_tdata_i[31:0]),
       .dds2_iq_axis_tdata_i		(dds2_iq_axis_tdata_i[31:0]),
       .dds0_iq_axis_tvalid_i		(dds0_iq_axis_tvalid_i),
       .dds1_iq_axis_tvalid_i		(dds1_iq_axis_tvalid_i),
       .dds2_iq_axis_tvalid_i		(dds2_iq_axis_tvalid_i),
       .s0_axi_aclk			(s0_axi_aclk),
       .s0_axi_aresetn			(s0_axi_aresetn),
       .s0_axi_awaddr			(s0_axi_awaddr[C_S0_AXI_ADDR_WIDTH-1:0]),
       .s0_axi_awprot			(s0_axi_awprot[2:0]),
       .s0_axi_awvalid			(s0_axi_awvalid),
       .s0_axi_wdata			(s0_axi_wdata[C_S0_AXI_DATA_WIDTH-1:0]),
       .s0_axi_wstrb			(s0_axi_wstrb[(C_S0_AXI_DATA_WIDTH/8)-1:0]),
       .s0_axi_wvalid			(s0_axi_wvalid),
       .s0_axi_bready			(s0_axi_bready),
       .s0_axi_araddr			(s0_axi_araddr[C_S0_AXI_ADDR_WIDTH-1:0]),
       .s0_axi_arprot			(s0_axi_arprot[2:0]),
       .s0_axi_arvalid			(s0_axi_arvalid),
       .s0_axi_rready			(s0_axi_rready));
endmodule // marga_simple_tb
`endif //  `ifndef _MARGA_SIMPLE_TB_
