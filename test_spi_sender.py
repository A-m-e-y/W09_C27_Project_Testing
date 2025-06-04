import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import struct


@cocotb.test()
async def test_spi_matrix_sender(dut):
    """Test: Send matrix C from DUT to Python using SPI."""

    # Matrix dimensions
    M, N = 4, 4
    C_size = M * N

    # Start DUT clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await Timer(100, units="ns")

    # Reset DUT
    dut.rst_n.value = 0
    dut.sclk.value = 0
    dut.cs_n.value = 1
    dut.mosi.value = 0
    dut.start_tx.value = 0
    await Timer(100, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # === Helper ===
    def float_to_hex(f):
        return struct.unpack('<I', struct.pack('<f', f))[0]

    # === Prepare Matrix C and Load into DUT ===
    matrix_C = [[float(i * N + j + 1) for j in range(N)] for i in range(M)]
    matrix_C_flat = [float_to_hex(x) for row in matrix_C for x in row]

    for i, val in enumerate(matrix_C_flat):
        dut.matrix_C[i].value = val

    dut.C_size.value = C_size

    # === Trigger Start ===
    dut.start_tx.value = 1
    await RisingEdge(dut.clk)
    dut.start_tx.value = 0

    await Timer(200, units="ns")

    # === Read Matrix C over SPI ===
    received_data = []
    for i in range(C_size):
        word = await spi_receive_word(dut)
        received_data.append(word)
        dut._log.info(f"Received word {i}: 0x{word:08X}, Expected: 0x{matrix_C_flat[i]:08X}")

    dut._log.info("✅ Matrix C successfully received from DUT over SPI.")

    for i in range(C_size):
        assert received_data[i] == matrix_C_flat[i], f"Mismatch at index {i}: {received_data[i]} != {matrix_C_flat[i]}"

# === SPI Receive Bit-Bang Function ===
async def spi_receive_word(dut):
    """Simulate SPI master receive: clock bits and sample MISO."""
    result = 0
    dut.cs_n.value = 0
    await Timer(20, units="ns")

    for i in range(32):
        dut.sclk.value = 0
        await Timer(10, units="ns")

        dut.sclk.value = 1
        await Timer(10, units="ns")

        await Timer(10, units="ns")
        bit = int(dut.miso.value)
        result = (result << 1) | bit

    dut.sclk.value = 0
    dut.cs_n.value = 1
    await Timer(40, units="ns")
    return result
