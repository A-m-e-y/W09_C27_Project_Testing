import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import struct
import random

@cocotb.test()
async def spi_matrix_loader_test(dut):
    """Test SPI loader that reconstructs 784x288 matrix A and 288x64 matrix B in DUT."""

    # Start clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await Timer(100, units="ns")

    # Reset DUT
    dut.rst_n.value = 0
    dut.cs_n.value = 1
    dut.sclk.value = 0
    dut.mosi.value = 0
    await Timer(100, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # Matrix sizes
    # M, K, N = 784, 288, 64  # A is MxK, B is KxN
    M, K, N = 10, 10, 10  # A is MxK, B is KxN

    # Helpers
    def float_to_hex(f):
        return struct.unpack('<I', struct.pack('<f', f))[0]

    def encode_word_as_int(f):
        return struct.unpack('<I', struct.pack('<I', f))[0]

    # Generate random float data
    matrix_A = [[random.uniform(-1, 1) for _ in range(K)] for _ in range(M)]
    matrix_B = [[random.uniform(-1, 1) for _ in range(N)] for _ in range(K)]

    A_flat = [float_to_hex(x) for row in matrix_A for x in row]
    B_flat = [float_to_hex(x) for row in matrix_B for x in row]

    # Header encoding: upper 8 bits = type (0x0A or 0x0B), next 12 bits = rows, last 12 bits = cols
    def make_header(tag, rows, cols):
        return (tag << 24) | ((rows & 0xFFF) << 12) | (cols & 0xFFF)

    # --- Send matrix A ---
    header_A = make_header(0x0A, M, K)
    await spi_send_word(dut, encode_word_as_int(header_A))
    for word in A_flat:
        await spi_send_word(dut, word)

    # --- Send matrix B ---
    header_B = make_header(0x0B, K, N)
    await spi_send_word(dut, encode_word_as_int(header_B))
    for word in B_flat:
        await spi_send_word(dut, word)

    await Timer(1000, units="ns")
    dut._log.info("Finished sending large matrices A (784x288) and B (288x64) over SPI.")
    dut._log.info("Verify internal DUT storage or hook next-stage logic.")

# SPI send function (bit-bang mode)
async def spi_send_word(dut, data):
    """Bit-bang one 32-bit word into the DUT over SPI."""
    dut.cs_n.value = 0
    await Timer(20, units="ns")

    for i in range(32):
        bit = (data >> (31 - i)) & 1
        dut.mosi.value = bit

        # Rising edge (sample MOSI)
        dut.sclk.value = 0
        await Timer(10, units="ns")
        dut.sclk.value = 1
        await Timer(10, units="ns")

    dut.sclk.value = 0
    dut.cs_n.value = 1
    await Timer(40, units="ns")
