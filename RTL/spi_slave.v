`timescale 1ns/1ps

module spi_slave (
    input  clk,
    input  rst_n,
    input  sclk,
    input  mosi,
    input  cs_n,
    output reg miso,

    output reg [31:0] rx_data,
    output reg rx_valid,
    input wire rx_ready,

    input wire [31:0] tx_data,
    input wire tx_valid,
    output reg tx_ready
);

    reg [5:0] bit_cnt;
    reg [31:0] shift_reg_rx;
    reg [31:0] shift_reg_tx;
    reg sclk_d, sclk_prev;

    wire sclk_rising = (sclk == 1'b1 && sclk_prev == 1'b0);
    wire sclk_falling = (sclk == 1'b0 && sclk_prev == 1'b1);

    // Delay for detecting edges
    // always @(posedge clk) begin
    //     sclk_d <= sclk;
    //     sclk_prev <= sclk_d;
    // end

    // Reset and CS edge detection
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            bit_cnt     <= 0;
            shift_reg_rx <= 0;
            shift_reg_tx <= 0;
            rx_valid    <= 0;
            tx_ready    <= 0;
            miso        <= 0;
            sclk_d <= 0;
        end else begin
            sclk_d <= sclk;
            sclk_prev <= sclk_d;
            if (cs_n == 0) begin
                // Receiving on SCLK rising edge
                if (sclk_rising) begin
                    shift_reg_rx <= {shift_reg_rx[30:0], mosi};
                    bit_cnt <= bit_cnt + 1;
                end

                // Transmitting on SCLK falling edge
                if (sclk_falling) begin
                    miso <= shift_reg_tx[31];
                    shift_reg_tx <= {shift_reg_tx[30:0], 1'b0};
                end

                // Complete one word
                if (bit_cnt == 6'd31) begin
                    bit_cnt <= 0;
                    rx_data <= shift_reg_rx;
                    rx_valid <= 1;
                end else begin
                    rx_valid <= 0;
                end

                // Load new tx word when needed
                if (bit_cnt == 0 && tx_valid) begin
                    shift_reg_tx <= tx_data;
                    tx_ready <= 1;
                end else begin
                    tx_ready <= 0;
                end
            end else begin
                bit_cnt <= 0;
                rx_valid <= 0;
                tx_ready <= 0;
                miso <= 0;
            end
        end
    end
endmodule
