//-----------------------------------------------------------------------------
// Title         : ocra1_model
// Project       : ocra_grad_ctrl
//-----------------------------------------------------------------------------
// File          : ocra1_model.sv
// Author        :   <vlad@arch-ssd>
// Created       : 31.08.2020
// Last modified : 31.08.2020
//-----------------------------------------------------------------------------
// Description :
// Behavioural model of OCRA1 board, specifically its I/O and four AD5781 DACs
//-----------------------------------------------------------------------------
// Copyright (c) 2020 by OCRA developers This model is the confidential and
// proprietary property of OCRA developers and the possession or use of this
// file requires a written license from OCRA developers.
//------------------------------------------------------------------------------

`ifndef _OCRA1_MODEL_
 `define _OCRA1_MODEL_

 `include "ad5781_model.sv"

 `timescale 1ns/1ns

module ocra1_model(
		   input 	 clk,
		   input 	 syncn,
		   input 	 ldacn,
		   input 	 sdox,
		   input 	 sdoy,
		   input 	 sdoz,
		   input 	 sdoz2,

		   output [17:0] voutx, vouty, voutz, voutz2
		   );

   reg 				 clrn = 1, resetn = 1;
   wire 			 sdix, sdiy, sdiz, sdiz2; // inputs from DACs (not connected)
   
   ad5781_model DACX(
		     // Outputs
		     .sdo		(sdix),
		     .vout		(voutx),
		     // Inputs
		     .sdin		(sdox),
		     .sclk		(clk),
		     .syncn		(syncn),
		     .ldacn		(ldacn),
		     .clrn		(clrn),
		     .resetn		(resetn));

   ad5781_model DACY(
		     // Outputs
		     .sdo		(sdiy),
		     .vout		(vouty),
		     // Inputs
		     .sdin		(sdoy),
		     .sclk		(clk),
		     .syncn		(syncn),
		     .ldacn		(ldacn),
		     .clrn		(clrn),
		     .resetn		(resetn)); // not connected to RP by OCRA1 board

   ad5781_model DACZ(
		     // Outputs
		     .sdo		(sdiz),
		     .vout		(voutz),
		     // Inputs
		     .sdin		(sdoz),
		     .sclk		(clk),
		     .syncn		(syncn),
		     .ldacn		(ldacn),
		     .clrn		(clrn),
		     .resetn		(resetn));
   

   ad5781_model DACZ2(
		     // Outputs
		     .sdo		(sdiz2),
		     .vout		(voutz2),
		     // Inputs
		     .sdin		(sdoz2),
		     .sclk		(clk),
		     .syncn		(syncn),
		     .ldacn		(ldacn),
		     .clrn		(clrn),
		     .resetn		(resetn));

endmodule // ocra1_model
`endif //  `ifndef _OCRA1_MODEL_
