/*
 * SPDX-License-Identifier: Apache-2.0
 */

(* blackbox *)
module SP6TSRAM128x8(a, d, we, clk, q);
  input wire [6:0] a;
  input wire [7:0] d;
  input wire [0:0] we;
  input wire clk;
  output wire [7:0] q;
endmodule

module tt_um_c4m_spsram_direct (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

assign uio_oe = 'b00000000;
assign uio_out = 'b00000000;

SP6TSRAM128x8 mem(
    .clk(clk),
    .a(ui_in[6:0]),
    .we(ui_in[7:7]),
    .d(uio_in),
    .q(uo_out)
);

endmodule