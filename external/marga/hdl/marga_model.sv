//-----------------------------------------------------------------------------
// Title         : marga_model
// Project       : marga
//-----------------------------------------------------------------------------
// File          : marga_model.sv
// Author        :   <vlad@vlad-laptop>
// Created       : 25.12.2020
// Last modified : 25.12.2020
//-----------------------------------------------------------------------------
// Description :
//
// Top-level model of the FPGA code running on the STEMlab, including
// the marga core, serialisers and a few dummy models of the TX and
// RX chain. Entirely RTL-based for use with Verilator.
//
//-----------------------------------------------------------------------------
// Copyright (c) 2020 by OCRA developers This model is the confidential and
// proprietary property of OCRA developers and the possession or use of this
// file requires a written license from OCRA developers.
//------------------------------------------------------------------------------

`ifndef _MARGA_MODEL_
 `define _MARGA_MODEL_

 `include "marga.sv"
 `include "ocra1_model.sv"
 `include "gpa_fhdo_model.sv"
 `include "rx_chain_model.sv"

 `timescale 1ns/1ns

module marga_model(/*AUTOARG*/
   // Outputs
   s0_axi_arready, s0_axi_awready, s0_axi_bresp, s0_axi_bvalid,
   s0_axi_rdata, s0_axi_rresp, s0_axi_rvalid, s0_axi_wready,
   ocra1_voutx, ocra1_vouty, ocra1_voutz, ocra1_voutz2, fhdo_voutx,
   fhdo_vouty, fhdo_voutz, fhdo_voutz2, dds0_phase_axis_tdata_o,
   dds1_phase_axis_tdata_o, dds2_phase_axis_tdata_o,
   dds0_phase_axis_tvalid_o, dds1_phase_axis_tvalid_o,
   dds2_phase_axis_tvalid_o, tx0_i, tx0_q, tx1_i, tx1_q, rx_gate_o,
   trig_o, tx0_axis_tdata_o, tx0_axis_tvalid_o, tx1_axis_tdata_o,
   tx1_axis_tvalid_o, tx_gate_o, rx0_rst_n_o, rx1_rst_n_o, rx0_en_o,
   rx1_en_o, rx0_rate, rx1_rate, rx0_rate_valid, rx1_rate_valid,
   leds_o,
   // Inputs
   trig_i, s0_axi_wvalid, s0_axi_wstrb, s0_axi_wdata, s0_axi_rready,
   s0_axi_bready, s0_axi_awvalid, s0_axi_awprot, s0_axi_awaddr,
   s0_axi_arvalid, s0_axi_arprot, s0_axi_aresetn, s0_axi_araddr,
   s0_axi_aclk, dds2_iq_axis_tvalid_i, dds2_iq_axis_tdata_i,
   dds1_iq_axis_tvalid_i, dds1_iq_axis_tdata_i, dds0_iq_axis_tvalid_i,
   dds0_iq_axis_tdata_i
   );
   localparam C_S0_AXI_ADDR_WIDTH = 19, C_S0_AXI_DATA_WIDTH = 32;

   /*AUTOINPUT*/
   // Beginning of automatic inputs (from unused autoinst inputs)
   input [31:0]		dds0_iq_axis_tdata_i;	// To UUT of marga.v
   input		dds0_iq_axis_tvalid_i;	// To UUT of marga.v
   input [31:0]		dds1_iq_axis_tdata_i;	// To UUT of marga.v
   input		dds1_iq_axis_tvalid_i;	// To UUT of marga.v
   input [31:0]		dds2_iq_axis_tdata_i;	// To UUT of marga.v
   input		dds2_iq_axis_tvalid_i;	// To UUT of marga.v
   input		s0_axi_aclk;		// To UUT of marga.v
   input [C_S0_AXI_ADDR_WIDTH-1:0] s0_axi_araddr;// To UUT of marga.v
   input		s0_axi_aresetn;		// To UUT of marga.v
   input [2:0]		s0_axi_arprot;		// To UUT of marga.v
   input		s0_axi_arvalid;		// To UUT of marga.v
   input [C_S0_AXI_ADDR_WIDTH-1:0] s0_axi_awaddr;// To UUT of marga.v
   input [2:0]		s0_axi_awprot;		// To UUT of marga.v
   input		s0_axi_awvalid;		// To UUT of marga.v
   input		s0_axi_bready;		// To UUT of marga.v
   input		s0_axi_rready;		// To UUT of marga.v
   input [C_S0_AXI_DATA_WIDTH-1:0] s0_axi_wdata;// To UUT of marga.v
   input [(C_S0_AXI_DATA_WIDTH/8)-1:0] s0_axi_wstrb;// To UUT of marga.v
   input		s0_axi_wvalid;		// To UUT of marga.v
   input		trig_i;			// To UUT of marga.v
   // End of automatics

   output 		s0_axi_arready;		// From UUT of marga.v
   output 		s0_axi_awready;		// From UUT of marga.v
   output [1:0] 	s0_axi_bresp;		// From UUT of marga.v
   output 		s0_axi_bvalid;		// From UUT of marga.v
   output [C_S0_AXI_DATA_WIDTH-1:0] s0_axi_rdata;	// From UUT of marga.v
   output [1:0] 		    s0_axi_rresp;		// From UUT of marga.v
   output 			    s0_axi_rvalid;		// From UUT of marga.v
   output 			    s0_axi_wready;		// From UUT of marga.v

   output signed [17:0] ocra1_voutx, ocra1_vouty, ocra1_voutz, ocra1_voutz2;
   output signed [15:0] fhdo_voutx, fhdo_vouty, fhdo_voutz, fhdo_voutz2;

   output [23:0] 	dds0_phase_axis_tdata_o, dds1_phase_axis_tdata_o, dds2_phase_axis_tdata_o;
   output 		dds0_phase_axis_tvalid_o, dds1_phase_axis_tvalid_o, dds2_phase_axis_tvalid_o;

   output [15:0] 	tx0_i, tx0_q, tx1_i, tx1_q;
   assign {tx0_q, tx0_i, tx1_q, tx1_i} = {tx0_axis_tdata_o, tx1_axis_tdata_o};

   output 		rx_gate_o;

   output 		trig_o;
   output [31:0] 	tx0_axis_tdata_o;
   output 		tx0_axis_tvalid_o;
   output [31:0] 	tx1_axis_tdata_o;
   output 		tx1_axis_tvalid_o;
   output 		tx_gate_o;

   output 		rx0_rst_n_o, rx1_rst_n_o;
   output 		rx0_en_o, rx1_en_o;

   output [15:0] 	rx0_rate, rx1_rate;
   assign rx0_rate = rx0_rate_axis_tdata_o[15:0], rx1_rate = rx1_rate_axis_tdata_o[15:0];
   output 		rx0_rate_valid, rx1_rate_valid;
   assign rx0_rate_valid = rx0_rate_axis_tvalid_o, rx1_rate_valid = rx1_rate_axis_tvalid_o;

   output [7:0]		leds_o;

   wire 		fhdo_sdi_i;
   wire [63:0] 		rx0_axis_tdata_i, rx1_axis_tdata_i;
   wire 		rx0_axis_tvalid_i, rx1_axis_tvalid_i;
   wire [15:0]		rx0_rate_axis_tdata_o, rx1_rate_axis_tdata_o;
   wire 		rx0_rate_axis_tvalid_o, rx1_rate_axis_tvalid_o;

   /*AUTOWIRE*/
   // Beginning of automatic wires (for undeclared instantiated-module outputs)
   wire			fhdo_clk_o;		// From UUT of marga.v
   wire			fhdo_sdo_o;		// From UUT of marga.v
   wire			fhdo_ssn_o;		// From UUT of marga.v
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
   wire			rx1_axis_tready_o;	// From UUT of marga.v
   wire [31:0]		rx1_dds_iq_axis_tdata_o;// From UUT of marga.v
   wire			rx1_dds_iq_axis_tvalid_o;// From UUT of marga.v
   // End of automatics

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

   // Just map the RX inputs to the TX I/Q outputs for now
   wire [31:0]		rx0_iq_axis_tdata = tx0_axis_tdata_o;
   wire [31:0]		rx1_iq_axis_tdata = tx1_axis_tdata_o;
   wire 		rx0_iq_axis_tvalid = rx0_dds_iq_axis_tvalid_o, rx1_iq_axis_tvalid = rx1_dds_iq_axis_tvalid_o;

   rx_chain_model rx0(
		      // Outputs
		      .axis_tvalid_o(rx0_axis_tvalid_i),
		      .axis_tdata_o(rx0_axis_tdata_i),
		      // Inputs
		      .clk(s0_axi_aclk),
		      .rst_n(rx0_rst_n_o),
		      .rate_axis_tdata_i(rx0_rate_axis_tdata_o),
		      .rate_axis_tvalid_i(rx0_rate_axis_tvalid_o),

		      .rx_iq_axis_tdata_i(rx0_iq_axis_tdata),
		      .rx_iq_axis_tvalid_i(rx0_iq_axis_tvalid),

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

		      .rx_iq_axis_tdata_i(rx1_iq_axis_tdata),
		      .rx_iq_axis_tvalid_i(rx1_iq_axis_tvalid),

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
endmodule // marga_model
`endif //  `ifndef _MARGA_MODEL_
