import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import struct
import random

@cocotb.test()
async def matrixmul_spi_test(dut):
    """Test full SPI roundtrip: load A & B, wait for C, fetch C over SPI, compare."""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await Timer(100, units="ns")

    # Reset DUT
    dut.rst_n.value = 0
    dut.cs_n.value = 1
    dut.sclk.value = 0
    dut.mosi.value = 0
    dut.send_c.value = 0
    await Timer(100, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # Test size: small for verification
    M, K, N = 10, 10, 10
    dut.M_in.value = M
    dut.K_in.value = K
    dut.N_in.value = N

    # --- Helper functions ---
    def float_to_hex(f):
        return struct.unpack('<I', struct.pack('<f', f))[0]

    def hex_to_float(h):
        return struct.unpack('<f', struct.pack('<I', h))[0]

    def encode_word_as_int(f):
        return struct.unpack('<I', struct.pack('<I', f))[0]

    def make_header(tag, rows, cols):
        return (tag << 24) | ((rows & 0xFFF) << 12) | (cols & 0xFFF)

    # --- Prepare data ---
    matrix_A = [[random.uniform(-1, 1) for _ in range(K)] for _ in range(M)]
    matrix_B = [[random.uniform(-1, 1) for _ in range(N)] for _ in range(K)]

    # matrix_A = [[-0.36741, -0.73356], [0.49609, 0.17082]]
    # matrix_B = [[-0.75855, 0.12771], [0.84804, -0.66840]]

    # Compute golden C in software
    def matmul(A, B):
        return [[sum(A[i][k] * B[k][j] for k in range(K)) for j in range(N)] for i in range(M)]

    matrix_C_golden = matmul(matrix_A, matrix_B)

    A_flat = [float_to_hex(x) for row in matrix_A for x in row]
    B_flat = [float_to_hex(x) for row in matrix_B for x in row]

    for i, val in enumerate(A_flat):
        dut._log.info(f"[INFO] A[{i}] = {val:08x} = {hex_to_float(val):.5f}")
    
    # --- Send A ---
    await spi_send_word(dut, encode_word_as_int(make_header(0x0A, M, K)))
    for word in A_flat:
        await spi_send_word(dut, word)

    for _ in range(200000):
        await RisingEdge(dut.clk)
        if dut.A_loaded.value.integer == 1:
            dut._log.info("Matrix A loaded.")
            break

    for i, val in enumerate(B_flat):
        dut._log.info(f"[INFO] B[{i}] = {val:08x} = {hex_to_float(val):.5f}")
   
    # --- Send B ---
    await spi_send_word(dut, encode_word_as_int(make_header(0x0B, K, N)))
    for word in B_flat:
        await spi_send_word(dut, word)

    for _ in range(200000):
        await RisingEdge(dut.clk)
        if dut.B_loaded.value.integer == 1:
            dut._log.info("Matrix B loaded.")
            break

    # --- Wait for matrix multiplication to complete ---
    dut._log.info("Waiting for mul_done...")
    for _ in range(200000):
        await RisingEdge(dut.clk)
        if dut.mul_done.value.integer == 1:
            dut._log.info("Matrix multiplication complete.")
            break

    # --- Trigger matrix C transmission ---
    dut.send_c.value = 1
    await Timer(20, units="ns")
    dut.send_c.value = 0

    # --- Receive matrix C from SPI ---
    received_C = []
    for _ in range(M * N):
        word = await spi_receive_word(dut)
        received_C.append(hex_to_float(word))

    # --- Compare results ---
    passed = True
    for i in range(M):
        for j in range(N):
            expected = matrix_C_golden[i][j]
            received = received_C[i * N + j]
            dut._log.info(f"[INFO] C[{i}][{j}] = {float_to_hex(received):08x}, expected {float_to_hex(expected):08x}")
            if abs(expected - received) > 1e-3:
                dut._log.error(f"[FAIL] C[{i}][{j}] = {received:.5f}, expected {expected:.5f}")
                passed = False
            else:
                dut._log.info(f"[PASS] C[{i}][{j}] = {received:.5f}, OK")

    assert passed, "Matrix C mismatch detected!"
    dut._log.info("✅ Full SPI roundtrip test passed!")


# --- SPI helpers ---
async def spi_send_word(dut, data):
    dut.cs_n.value = 0
    dut.mosi.value = 0
    dut.sclk.value = 0
    await Timer(10, units="ns")
    dut.sclk.value = 1
    await Timer(10, units="ns")
    for i in range(32):
        bit = (data >> (31 - i)) & 1
        dut.mosi.value = bit
        dut.sclk.value = 0
        await Timer(10, units="ns")
        dut.sclk.value = 1
        await Timer(10, units="ns")
    dut.sclk.value = 0
    dut.cs_n.value = 1
    dut.mosi.value = 0
    await Timer(40, units="ns")


async def spi_receive_word(dut):
    """Simulate SPI master receive: clock bits and sample MISO."""
    result = 0
    dut.cs_n.value = 0
    await Timer(10, units="ns")

    for i in range(32):
        dut.sclk.value = 0
        await Timer(10, units="ns")

        dut.sclk.value = 1
        await Timer(10, units="ns")

        await Timer(10, units="ns")
        try:
            bit = int(dut.miso.value)
            result = (result << 1) | bit
        except ValueError:
            bit = 0
            result = (result << 1) | bit

    dut.sclk.value = 0
    dut.cs_n.value = 1
    await Timer(40, units="ns")
    return result
