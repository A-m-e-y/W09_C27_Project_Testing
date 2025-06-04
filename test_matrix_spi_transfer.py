import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import struct

@cocotb.test()
async def spi_matrix_loader_test(dut):
    """Test SPI loader that reconstructs 2x2 matrices A and B in DUT."""

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

    # 2x2 matrix A and B (as floats)
    matrix_A = [[1.0, 2.0], [3.0, 4.0]]
    matrix_B = [[5.0, 6.0], [7.0, 8.0]]

    # Flatten and convert to 32-bit hex
    def float_to_hex(f):
        return struct.unpack('<I', struct.pack('<f', f))[0]

    def encode_word_as_int(f):
        return struct.unpack('<I', struct.pack('<I', f))[0]  # note: packing as unsigned int, not float


    A_flat = [float_to_hex(x) for row in matrix_A for x in row]
    B_flat = [float_to_hex(x) for row in matrix_B for x in row]

    # Send control header: 0xAAAA5555 = Start, next=matrix A
    await spi_send_word(dut, encode_word_as_int(0x0A002002))

    # Send matrix A
    for word in A_flat:
        await spi_send_word(dut, word)

    # Send control header: 0xBBBB6666 = next=matrix B
    await spi_send_word(dut, encode_word_as_int(0x0B002002))

    # Send matrix B
    for word in B_flat:
        await spi_send_word(dut, word)

    await Timer(500, units="ns")
    dut._log.info("Finished sending matrix A and B over SPI.")
    dut._log.info("Please inspect waveform or internal DUT regs to verify matrix reconstruction.")

# SPI send function
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
