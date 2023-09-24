//-----------------------------------------------------------------------------
// Title         : gpa_fhdo_model
// Project       : ocra_grad_ctrl
//-----------------------------------------------------------------------------
// File          : gpa_fhdo_model.sv
// Author        :   <vlad@arch-ssd>
// Created       : 19.11.2020
// Last modified : 19.11.2020
//-----------------------------------------------------------------------------
// Description :
// Behavioural model of GPA-FHDO board, specifically its I/O, DAC and ADC
//-----------------------------------------------------------------------------
// Copyright (c) 2020 by OCRA developers This model is the confidential and
// proprietary property of OCRA developers and the possession or use of this
// file requires a written license from OCRA developers.
//------------------------------------------------------------------------------

`ifndef _GPA_FHDO_MODEL_
 `define _GPA_FHDO_MODEL_

 `include "dac80504_model.sv"
 `include "ads8684_model.sv"

 `timescale 1ns/1ns

module gpa_fhdo_model(
		      input clk,
		      input csn,
		      input sdo,
		      output sdi,

		      output [15:0] voutx, vouty, voutz, voutz2
		      );

   dac80504_model dac(
		      .ldacn(1'b0),
		      .csn(csn),
		      .sclk(clk),
		      .sdi(sdo),
		      .sdo(),

		      .vout0(voutx),
		      .vout1(vouty),
		      .vout2(voutz),
		      .vout3(voutz2)
		      );

   ads8684_model adc(
		     .csn(!csn),
		     .sclk(clk),
		     .sdi(sdo),
		     .sdo(sdi),
		     
		     .ain_0p(voutx),
		     .ain_1p(vouty),
		     .ain_2p(voutz),
		     .ain_3p(voutz2));
		     
endmodule // gpa_fhdo_model
`endif //  `ifndef _GPA_FHDO_MODEL_
