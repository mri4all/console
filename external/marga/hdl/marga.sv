//-----------------------------------------------------------------------------
// Title         : marga
// Project       : marga
//-----------------------------------------------------------------------------
// File          : marga.sv
// Author        :   <vlad@arch-ssd>
// Created       : 17.12.2020
// Last modified : 17.12.2020
//-----------------------------------------------------------------------------
// Description :
//
// Top-level marga core file.
//
// Outputs:
// - direct SPI lines to the gradient boards
// - direct SPI/I2C? lines to the attenuator core [TODO]
// - external trigger output
// - phase words to three external DDS cores
// - I/Q data to two external complex multipliers
// - LO source, decimation factor and reset gating to the two RX channels
//
// Inputs:
// - 2x 32-bit downconverted data streams
// - ADC line from GPA-FHDO
// - external trigger input
//
// Internal structure:
// - mardecode core, responsible for outputs and their timing, and RX FIFOs
// - resetting and phase offsetting/incrementing is handled here for
// the TX DDSes and their routing
//
// -----------------------------------------------------------------------------
// See LICENSE for GPL licensing information
// ------------------------------------------------------------------------------

`ifndef _MARGA_
 `define _MARGA_

 `include "mardecode.sv"
 `include "marbuffer.sv"
 `include "ocra1_iface.sv"
 `include "gpa_fhdo_iface.sv"

 `timescale 1ns / 1ns

module marga
  // #(
  //  // Users to add parameters here
  //  // User parameters ends
  //  parameter test_param = 0
  //  )
   (
    // Outputs to the OCRA1 board (concatenation on the expansion header etc will be handled in Vivado's block diagram)
    output 				  ocra1_clk_o, // SPI clock
    output 				  ocra1_syncn_o, // sync (roughly equivalent to SPI CS)
    output 				  ocra1_ldacn_o, // ldac
    output 				  ocra1_sdox_o, // data out, X DAC
    output 				  ocra1_sdoy_o, // data out, Y DAC
    output 				  ocra1_sdoz_o, // data out, Z DAC
    output 				  ocra1_sdoz2_o, // data out, Z2 DAC

    // I/O to the GPA-FHDO board
    output 				  fhdo_clk_o, // SPI clock
    output 				  fhdo_sdo_o, // data out
    output 				  fhdo_ssn_o, // SPI CS
    input 				  fhdo_sdi_i, // data in

    // Outputs to the attenuator chip on the ocra1
    // TODO

    // Outputs to the TX and RX digital gates
    output 				  tx_gate_o,
    output 				  rx_gate_o,

    // TX DDS phase control
    output reg [23:0] 			  dds0_phase_axis_tdata_o, dds1_phase_axis_tdata_o, dds2_phase_axis_tdata_o,
    output 				  dds0_phase_axis_tvalid_o, dds1_phase_axis_tvalid_o, dds2_phase_axis_tvalid_o,
    // output 				  dds0_phase_en, dds1_phase_en, dds2_phase_en;

    // RX reset, enable, CIC decimation ratio control
    output 				  rx0_rst_n_o, rx1_rst_n_o,
    output 				  rx0_en_o, rx1_en_o,
    output [15:0] 			  rx0_rate_axis_tdata_o, rx1_rate_axis_tdata_o,
    output 				  rx0_rate_axis_tvalid_o, rx1_rate_axis_tvalid_o,

    // External trigger output and input
    output 				  trig_o,
    input 				  trig_i,

    // streaming inputs to RX0 FIFO
    input 				  rx0_axis_tvalid_i,
    input [63:0] 			  rx0_axis_tdata_i,
    output 				  rx0_axis_tready_o,

    // streaming inputs to RX1 FIFO
    input 				  rx1_axis_tvalid_i,
    input [63:0] 			  rx1_axis_tdata_i,
    output 				  rx1_axis_tready_o,

    // RX LO source select
    input [31:0] 			  dds0_iq_axis_tdata_i, dds1_iq_axis_tdata_i, dds2_iq_axis_tdata_i,
    input 				  dds0_iq_axis_tvalid_i, dds1_iq_axis_tvalid_i, dds2_iq_axis_tvalid_i,
    output reg [31:0] 			  rx0_dds_iq_axis_tdata_o, rx1_dds_iq_axis_tdata_o,
    output 				  rx0_dds_iq_axis_tvalid_o, rx1_dds_iq_axis_tvalid_o,

    // streaming outputs to TX multipliers; I/Q 16-bit each
    output reg [31:0] 			  tx0_axis_tdata_o,
    output 				  tx0_axis_tvalid_o,

    output reg [31:0] 			  tx1_axis_tdata_o,
    output 				  tx1_axis_tvalid_o,

    // LEDs for monitoring/diagnostics
    output [7:0] 			  leds_o,

    // User ports ends
    // Do not modify the ports beyond this line

    // Ports of Axi Slave Bus Interface S0_AXI
    input 				  s0_axi_aclk,
    input 				  s0_axi_aresetn,
    input [C_S0_AXI_ADDR_WIDTH-1 : 0] 	  s0_axi_awaddr,
    input [2 : 0] 			  s0_axi_awprot,
    input 				  s0_axi_awvalid,
    output 				  s0_axi_awready,
    input [C_S0_AXI_DATA_WIDTH-1 : 0] 	  s0_axi_wdata,
    input [(C_S0_AXI_DATA_WIDTH/8)-1 : 0] s0_axi_wstrb,
    input 				  s0_axi_wvalid,
    output 				  s0_axi_wready,
    output [1 : 0] 			  s0_axi_bresp,
    output 				  s0_axi_bvalid,
    input 				  s0_axi_bready,
    input [C_S0_AXI_ADDR_WIDTH-1 : 0] 	  s0_axi_araddr,
    input [2 : 0] 			  s0_axi_arprot,
    input 				  s0_axi_arvalid,
    output 				  s0_axi_arready,
    output [C_S0_AXI_DATA_WIDTH-1 : 0] 	  s0_axi_rdata,
    output [1 : 0] 			  s0_axi_rresp,
    output 				  s0_axi_rvalid,
    input 				  s0_axi_rready
    );

   // General outputs from mardecode
   // 0: gradient control: grad SPI divisor and board selection settings
   // 1: gradient outputs, LSB (stb triggers grad cores)
   // 2: gradient outputs, MSB (stb also triggers grad cores, but only when bit 9 of gradient control is high)
   // 3: RX 0 CIC control: rate and auxiliary parameters for non-Xilinx CICs
   // 4: RX 1 CIC control: rate and auxiliary parameters for non-Xilinx CICs
   // 5: TX 0 i stream
   // 6: TX 0 q stream
   // 7: TX 1 i stream
   // 8: TX 1 q stream
   // 9: TX LO 0 phase increment, LSBs
   // 10: TX LO 0 phase increment, MSBs and clear bit
   // 11: TX LO 1 phase increment, LSBs
   // 12: TX LO 1 phase increment, MSBs and clear bit
   // 13: TX LO 2 phase increment, LSBs
   // 14: TX LO 2 phase increment, MSBs and clear bit
   // 15: TX and RX gate control, trigger output, LEDs
   // 16: RX configuration: RX0/RX1 rate settings bus valid, CIC reset and demodulation DDS source
   wire [15:0] 				      fld_data[23:0];
   wire [23:0] 				      fld_stb;
   wire [31:0] 				      fld_status, fld_status_latch;

   wire [15:0] 				      grad_ctrl = fld_data[0];
   wire [15:0] 				      grad_data_lsb = fld_data[1];
   wire [15:0] 				      grad_data_msb = fld_data[2];
   wire [15:0] 				      rx0_rate = fld_data[3];
   wire [15:0] 				      rx1_rate = fld_data[4];
   wire [15:0] 				      tx0_i = fld_data[5];
   wire [15:0] 				      tx0_q = fld_data[6];
   wire [15:0] 				      tx1_i = fld_data[7];
   wire [15:0] 				      tx1_q = fld_data[8];
   wire [15:0] 				      lo0_phase_lsb = fld_data[9];
   wire [15:0] 				      lo0_phase_msb = fld_data[10];
   wire [15:0] 				      lo1_phase_lsb = fld_data[11];
   wire [15:0] 				      lo1_phase_msb = fld_data[12];
   wire [15:0] 				      lo2_phase_lsb = fld_data[13];
   wire [15:0] 				      lo2_phase_msb = fld_data[14];
   wire [15:0] 				      gates_leds = fld_data[15];
   wire [15:0] 				      rx_ctrl = fld_data[16];

   // Parameters of Axi Slave Bus Interface S0_AXI
   parameter integer 			      C_S0_AXI_DATA_WIDTH = 32;
   parameter integer 			      C_S0_AXI_ADDR_WIDTH = 19;
   wire 				      clk = s0_axi_aclk;

   // Gradient control lines
   wire 				      ocra1_en = grad_ctrl[0];
   wire 				      fhdo_en = grad_ctrl[1];
   wire [5:0] 				      grad_spi_clk_div = grad_ctrl[7:2];
   wire 				      ocra1_rst_n = grad_ctrl[8];
   wire 				      grad_data_valid_msb_en = grad_ctrl[9];
   wire [31:0] 				      grad_data = {grad_data_msb, grad_data_lsb};

   wire 				      grad_data_valid = fld_stb[1] | ( fld_stb[2] & grad_data_valid_msb_en );
   wire 				      ocra1_data_valid = ocra1_en & grad_data_valid;
   wire 				      fhdo_data_valid = fhdo_en & grad_data_valid;
   wire [15:0] 				      fhdo_adc; // ADC data from GPA-FHDO
   wire 				      fhdo_busy;
   wire 				      ocra1_busy, ocra1_data_lost;
   wire 				      ocra1_err = ocra1_busy & ocra1_data_valid;
   wire 				      fhdo_err = fhdo_busy & fhdo_data_valid;
   assign fld_status = {14'd0, fhdo_busy, ocra1_busy, fhdo_adc};
   assign fld_status_latch = {29'd0, fhdo_err, ocra1_err, ocra1_data_lost};

   // RX control lines
   wire [1:0] rx0_dds_source = rx_ctrl[1:0], rx1_dds_source = rx_ctrl[3:2];
   assign rx0_rate_axis_tdata_o = rx0_rate[15:0], rx1_rate_axis_tdata_o = rx1_rate[15:0];
   assign rx0_rate_axis_tvalid_o = rx_ctrl[4], rx1_rate_axis_tvalid_o = rx_ctrl[5];
   assign rx0_rst_n_o = rx_ctrl[6], rx1_rst_n_o = rx_ctrl[7];
   assign rx0_en_o = rx_ctrl[8], rx1_en_o = rx_ctrl[9];

   // TX data buses
   assign tx0_axis_tvalid_o = 1, tx1_axis_tvalid_o = 1;
   always @(posedge clk) begin
      tx0_axis_tdata_o <= {tx0_q, tx0_i};
      tx1_axis_tdata_o <= {tx1_q, tx1_i};
   end

   // DDS phase control (31 bits)
   // TODO: parameterise all widths etc
   wire [30:0] dds0_phase_step = {lo0_phase_msb[14:0], lo0_phase_lsb},
	       dds1_phase_step = {lo1_phase_msb[14:0], lo1_phase_lsb},
	       dds2_phase_step = {lo2_phase_msb[14:0], lo2_phase_lsb};
   wire dds0_phase_clear = lo0_phase_msb[15],
	dds1_phase_clear = lo1_phase_msb[15],
	dds2_phase_clear = lo2_phase_msb[15];
   reg [30:0] dds0_phase_full = 0, dds1_phase_full = 0, dds2_phase_full = 0;
   assign dds0_phase_axis_tdata_o = dds0_phase_full[30:7],
     dds1_phase_axis_tdata_o = dds1_phase_full[30:7],
     dds2_phase_axis_tdata_o = dds2_phase_full[30:7];

   // RX LO source control
   reg [31:0] dds0_iq = 0, dds1_iq = 0, dds2_iq = 0, rx0_iq = 0, rx1_iq = 0;
   assign rx0_dds_iq_axis_tvalid_o = rx0_en_o, rx1_dds_iq_axis_tvalid_o = rx1_en_o; // if RX is disabled, halt flow of IQ samples to RX
   always @(posedge clk) begin
      dds0_iq <= dds0_iq_axis_tdata_i;
      dds1_iq <= dds1_iq_axis_tdata_i;
      dds2_iq <= dds2_iq_axis_tdata_i;
      rx0_dds_iq_axis_tdata_o <= rx0_iq;
      rx1_dds_iq_axis_tdata_o <= rx1_iq;

      case (rx0_dds_source)
	2'd0: rx0_iq <= dds0_iq;
	2'd1: rx0_iq <= dds1_iq;
	2'd2: rx0_iq <= dds2_iq;
	default: rx0_iq <= 32'h80007fff; // max negative and positive
      endcase // case (rx0_dds_source)

      case (rx1_dds_source)
	2'd0: rx1_iq <= dds0_iq;
	2'd1: rx1_iq <= dds1_iq;
	2'd2: rx1_iq <= dds2_iq;
	default: rx1_iq <= 32'h80007fff; // max negative and positive
      endcase // case (rx0_dds_source)
   end

   assign {dds0_phase_axis_tvalid_o, dds1_phase_axis_tvalid_o, dds2_phase_axis_tvalid_o} = 3'b111;

   always @(posedge clk) begin
      if (dds0_phase_clear) dds0_phase_full <= 0;
      else dds0_phase_full <= dds0_phase_full + {lo0_phase_msb[14:0], lo0_phase_lsb};

      if (dds1_phase_clear) dds1_phase_full <= 0;
      else dds1_phase_full <= dds1_phase_full + {lo1_phase_msb[14:0], lo1_phase_lsb};

      if (dds2_phase_clear) dds2_phase_full <= 0;
      else dds2_phase_full <= dds2_phase_full + {lo2_phase_msb[14:0], lo2_phase_lsb};
   end

   // TX and RX gates
   assign tx_gate_o = gates_leds[0], rx_gate_o = gates_leds[1], trig_o = gates_leds[2], leds_o = gates_leds[15:8];

   // wire [15:0]

   // for the ocra1, data can be written even while it's outputting to
   // SPI - for the fhd, this isn't the case. So don't use the
   // oc1_busy line in grad_bram, since it would mean that false
   // errors would get flagged - just fhd_busy for now.

   ocra1_iface ocra1_if (
			 // Outputs
			 .oc1_clk_o	(ocra1_clk_o),
			 .oc1_syncn_o	(ocra1_syncn_o),
			 .oc1_ldacn_o	(ocra1_ldacn_o),
			 .oc1_sdox_o	(ocra1_sdox_o),
			 .oc1_sdoy_o	(ocra1_sdoy_o),
			 .oc1_sdoz_o	(ocra1_sdoz_o),
			 .oc1_sdoz2_o	(ocra1_sdoz2_o),
			 .busy_o       	(ocra1_busy),
			 .data_lost_o   (ocra1_data_lost),
			 // Inputs
			 .clk		(clk),
			 .rst_n         (ocra1_rst_n), // purely for clearing data_lost for initial word
			 .data_i       	(grad_data),
			 .valid_i      	(ocra1_data_valid),
			 .spi_clk_div_i	(grad_spi_clk_div));

   gpa_fhdo_iface gpa_fhdo_if (
			       // Outputs
			       .fhd_clk_o	(fhdo_clk_o),
			       .fhd_sdo_o	(fhdo_sdo_o),
			       .fhd_csn_o	(fhdo_ssn_o),
			       .busy_o		(fhdo_busy),
			       .adc_value_o	(fhdo_adc),
			       // Inputs
			       .clk		(clk),
			       .data_i		(grad_data),
			       .spi_clk_div_i	(grad_spi_clk_div),
			       .valid_i		(fhdo_data_valid),
			       .fhd_sdi_i	(fhdo_sdi_i));


   ///////////////////////// MARDECODE ////////////////////////////

   mardecode #(.BUFS(24), .RX_FIFO_LENGTH(16384))
   fld (
	.trig_i(trig_i),
	.status_i(fld_status), // spare bits available for external status
	.status_latch_i(fld_status_latch),
	.data_o(fld_data),
	.stb_o(fld_stb),

	.rx0_data(rx0_axis_tdata_i[63:0]),
	.rx0_valid(rx0_axis_tvalid_i),
	.rx0_ready(rx0_axis_tready_o),

	.rx1_data(rx1_axis_tdata_i[63:0]),
	.rx1_valid(rx1_axis_tvalid_i),
	.rx1_ready(rx1_axis_tready_o),

	// bus inputs
	.S_AXI_ACLK			(s0_axi_aclk),
	.S_AXI_ARESETN			(s0_axi_aresetn),
	.S_AXI_AWADDR			(s0_axi_awaddr[C_S0_AXI_ADDR_WIDTH-1:0]),
	.S_AXI_AWPROT			(s0_axi_awprot[2:0]),
	.S_AXI_AWVALID			(s0_axi_awvalid),
	.S_AXI_WDATA			(s0_axi_wdata[C_S0_AXI_DATA_WIDTH-1:0]),
	.S_AXI_WSTRB			(s0_axi_wstrb[(C_S0_AXI_DATA_WIDTH/8)-1:0]),
	.S_AXI_WVALID			(s0_axi_wvalid),
	.S_AXI_BREADY			(s0_axi_bready),
	.S_AXI_ARADDR			(s0_axi_araddr[C_S0_AXI_ADDR_WIDTH-1:0]),
	.S_AXI_ARPROT			(s0_axi_arprot[2:0]),
	.S_AXI_ARVALID			(s0_axi_arvalid),
	.S_AXI_RREADY			(s0_axi_rready),

	// bus outputs
	.S_AXI_AWREADY			(s0_axi_awready),
	.S_AXI_WREADY			(s0_axi_wready),
	.S_AXI_BRESP			(s0_axi_bresp[1:0]),
	.S_AXI_BVALID			(s0_axi_bvalid),
	.S_AXI_ARREADY			(s0_axi_arready),
	.S_AXI_RDATA			(s0_axi_rdata[C_S0_AXI_DATA_WIDTH-1:0]),
	.S_AXI_RRESP			(s0_axi_rresp[1:0]),
	.S_AXI_RVALID			(s0_axi_rvalid)
	);

endmodule // marga
`endif //  `ifndef _MARGA_
