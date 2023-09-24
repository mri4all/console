//-----------------------------------------------------------------------------
// Title         : gpa_fhdo_iface
// Project       : ocra
//-----------------------------------------------------------------------------
// File          : gpa_fhdo_iface.sv
// Author        :   <benjamin.menkuec@fh-dortmund.de>
// Created       : 03.09.2020
// Last modified : 03.09.2020
//-----------------------------------------------------------------------------
// Description :
//
// Interface between gradient BRAM module and the GPA-FHDO board, with
// an SPI serialiser for the 4-channel DAC and associated FSM logic.
//
//-----------------------------------------------------------------------------
// Copyright (c) 2020 by OCRA developers This model is the confidential and
// proprietary property of OCRA developers and the possession or use of this
// file requires a written license from OCRA developers.
//------------------------------------------------------------------------------

`ifndef _GPA_FHDO_IFACE_
 `define _GPA_FHDO_IFACE_

 `timescale 1ns/1ns

module gpa_fhdo_iface(
		   input 	clk,

		   // data words from gradient memory core
		   input [31:0] data_i,

		   // data valid flag, should be held high for 1 cycle to initiate a transfer		   
		   input 	valid_i,
		   
		   // SPI clock divider
		   input [5:0] 	spi_clk_div_i,
		   
		   // ADC output
		   output reg [15:0] adc_value_o,

		   // GPA-FHDO interface
		   output reg 	fhd_clk_o,
		   output reg 	fhd_sdo_o,
		   output reg 	fhd_csn_o,
		   input 	fhd_sdi_i,

		   output reg 	busy_o // should be held high while module is carrying out an SPI transfer
		   );
		   
	reg [23:0] 			spi_output = 0;
    wire [15:0] 	    spi_payload = spi_output[15:0];	
	wire [3:0] 			spi_addr = spi_output[19:16];
	reg [7:0] 			spi_counter = 0;
    reg [23:0] 			datax_r = 0, datay_r = 0, dataz_r = 0, dataz2_r = 0;	
    reg [23:0] 			payload_r = 0;
    reg 				broadcast_r = 0;
	reg					select_adc = 0;
//    reg [1:0] 			channel_r = 0;	
	reg [5:0] 			spi_clk_div_r = 0;
	wire [4:0] 			spi_clk_edge_div = spi_clk_div_r[5:1]; // divided by 2
	reg [5:0] 			div_ctr = 0;
	// reg [15:0]			old_sync_reg = 16'hFF00; // default values after reset from dac80504 data sheet
	// reg [15:0]			new_sync_reg = 0;
	
	localparam			num_transfer = 1;
	reg [2:0]			current_transfer = 0;
	/*
		nr		data
		0		setup sync_reg
		1		transfer payload
	*/
	
	localparam			SIZE = 3;
	localparam 			IDLE = 3'b001,START_SPI = 3'b010,OUTPUT_SPI = 3'b011,END_SPI = 3'b100;
						
	reg [SIZE-1:0]			state = IDLE;
 
	initial begin
	   adc_value_o = 0;
	   fhd_clk_o = 0;
	   fhd_sdo_o = 0;
	end
	
	// Sequence Logic
	always @(posedge clk) begin
	   // VN: div_cntr should be synced to incoming data arrival
	   // in some way - otherwise the free-runing counter creates
	   // jitter in the gradient output
	  	if ( (div_ctr == spi_clk_div_i) || valid_i ) begin // VN: reset the divider phase with each input payload
			div_ctr <= 0;
		end 
		else begin
	      div_ctr <= div_ctr + 1;
		end
		if(valid_i && state == IDLE) begin
			spi_clk_div_r <= spi_clk_div_i;
			state <= START_SPI;
			payload_r <= data_i[23:0];
			broadcast_r <= data_i[24];
//			channel_r <= data_i[26:25];	
			select_adc <= data_i[30];
			// new_sync_reg <= 16'h0000; // broadcast off, sync (from ldac) off for all channels
		end
		else if (div_ctr == 0) begin
			if (!select_adc) begin
				case(state)
					START_SPI: begin
					   // VN: simplified this, because of the bug whereby if the GPA-FHDO
					   // is reset/loses power, the sync register gets cleared as well, but
					   // this core remains unaware - don't want false positives

						// load data for current transfer into spi_output
						// spi_output[23:20] <= 4'b0000;
						// if(new_sync_reg != old_sync_reg) begin
						//    current_transfer <= 0;
						//    spi_output[19:16] <= 4'b0010; // sync_reg
						//    spi_output[15:0] <= new_sync_reg;
						//    old_sync_reg <= new_sync_reg;
						//    current_transfer <= 0;
						// end
						// else begin
						//    // select dac_channel
						//    spi_output[19] <= 1'b1;
						//    spi_output[18] <= 1'b0;
						//    spi_output[17:16] <= channel_r; // VN: save some logic
						//    spi_output[15:0] <= payload_r[15:0];
						//    current_transfer <= 1;
						// end
						spi_output <= payload_r;
						state <= OUTPUT_SPI;
					end
					OUTPUT_SPI: begin
						// $display("state_logic spi_counterf %d",spi_counterf);
						if (spi_counter == 23) begin
						   state <= END_SPI;
						end
						else begin
						   state <= OUTPUT_SPI;
						end
					end
					END_SPI: begin
						// if (current_transfer < num_transfer) begin
						//    current_transfer <= current_transfer + 1;
						//    state <= START_SPI;
						// end
						// else begin
						//    state <= IDLE;
						// end
						state <= IDLE;
					end
					default:state <= IDLE;
				endcase		   
			end
			else begin
				case(state)
					START_SPI: begin
						// load data for current transfer into spi_output
						// spi_output[23:0] <= {payload_r[15:0],8'h00};
						spi_output <= payload_r;
						state <= OUTPUT_SPI;
					end
					OUTPUT_SPI: begin
						// $display("state_logic spi_counterf %d",spi_counterf);
						if (spi_counter == 31) begin
						   state <= END_SPI;
						end
						else begin
						   state <= OUTPUT_SPI;
						end
					end
					END_SPI: begin
					   state <= IDLE;
					end
					default:state <= IDLE;
				endcase		   
			end
		end
	end

   // Output Logic
   always @(posedge clk) begin
		if(div_ctr == 0) begin
			case(state)
				IDLE: begin
					busy_o <= 0;
					fhd_csn_o <= !select_adc;
					spi_counter <= 0;
					fhd_clk_o <= 0;
					end
				START_SPI: begin
					busy_o <= 1;
					fhd_csn_o <= !select_adc;
					spi_counter <= 0;
					fhd_clk_o <= 0;
				   end
				OUTPUT_SPI: begin
					fhd_clk_o <= 1;
					fhd_csn_o <= select_adc;
					spi_counter <= spi_counter + 1;
					if (select_adc & (spi_counter > 15 & spi_counter < 32)) begin
						adc_value_o <= {adc_value_o[14:0],fhd_sdi_i};
					end
					if (spi_counter < 24) begin
						fhd_sdo_o <= spi_output[23-spi_counter];
					end
					else begin
						fhd_sdo_o <= 0;
					end
				   end
				END_SPI: begin
					fhd_sdo_o <= 0;
					fhd_csn_o <= !select_adc;
				end
				default: begin // should never happen
					busy_o <= 0;
					fhd_csn_o <= !select_adc;
					spi_counter <= 0;
				   fhd_clk_o <= 0;
				end
			  endcase
		  end
		else if(div_ctr == {1'b0, spi_clk_edge_div}) begin
		   fhd_clk_o <= 0;
			// case(state)
			// 	START_SPI: 	fhd_clk_o <= 0;
			// 	OUTPUT_SPI:	fhd_clk_o <= 0;
			// 	END_SPI:	fhd_clk_o <= 0;
			// 	default: 	fhd_clk_o <= 0; 
			// endcase
		end
   end


endmodule // gpa_fhdo_iface
`endif //  `ifndef _GPA_FHDO_IFACE_
