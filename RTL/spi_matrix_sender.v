`timescale 1ns/1ps

module spi_matrix_sender #(
    parameter MAX_M = 784,
    parameter MAX_N = 64
)(
    input  wire        clk,
    input  wire        rst_n,

    // SPI interface
    input  wire        sclk,
    input  wire        mosi,
    input  wire        cs_n,
    output wire        miso,

    // Control
    input  wire        start_tx,
    input  wire [31:0] matrix_C [0:MAX_M*MAX_N-1],
    input  wire [15:0] C_size,   // total number of words to send
    output reg         done_tx
);

    // SPI slave interface
    wire [31:0] rx_data;
    wire        rx_valid;
    wire        rx_ready = 1'b0;

    reg  [31:0] tx_data;
    reg         tx_valid;
    wire        tx_ready;

    spi_slave spi_inst (
        .clk       (clk),
        .rst_n     (rst_n),
        .sclk      (sclk),
        .mosi      (mosi),
        .cs_n      (cs_n),
        .miso      (miso),
        .rx_data   (rx_data),
        .rx_valid  (rx_valid),
        .rx_ready  (rx_ready),
        .tx_data   (tx_data),
        .tx_valid  (tx_valid),
        .tx_ready  (tx_ready)
    );

    // FSM states
    localparam IDLE      = 0,
               SEND_DATA = 1,
               DONE      = 2;

    reg [1:0] state;
    reg [15:0] send_index;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state      <= IDLE;
            tx_data    <= 32'd0;
            tx_valid   <= 0;
            send_index <= 0;
            done_tx    <= 0;
        end else begin
            tx_valid <= 0;
            case (state)
                IDLE: begin
                    done_tx <= 0;
                    if (start_tx) begin
                        send_index <= 0;
                        tx_valid <= 1;
                        state <= SEND_DATA;
                    end
                end

                SEND_DATA: begin
                    if (tx_ready) begin
                        tx_data <= matrix_C[send_index];
                        tx_valid <= 1;
                        send_index <= send_index + 1;
                        if (send_index == (C_size - 1)) begin
                            state <= DONE;
                        end
                    end
                end

                DONE: begin
                    done_tx <= 1;
                    state <= IDLE;
                end
            endcase
        end
    end

endmodule
