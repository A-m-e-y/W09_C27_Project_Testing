import numpy as np
import struct
import subprocess
import os
import time

def float_to_hex(f):
    return struct.unpack('<I', struct.pack('<f', f))[0]

def hex_to_float(h):
    return struct.unpack('<f', struct.pack('<I', h))[0]

def matrix_mul_hw(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """
    Calls cocotb to perform matrix multiplication in Verilog via SPI.
    Returns the resulting matrix C.
    """
    assert A.shape[1] == B.shape[0], "Matrix multiplication not valid: A.cols != B.rows"
    M, K = A.shape
    K2, N = B.shape
    assert K == K2

    # Flatten data and write to input_buffer.txt
    with open("input_buffer.txt", "w") as f:
        f.write(f"M {M}\n")
        f.write(f"K {K}\n")
        f.write(f"N {N}\n")
        f.write("A " + " ".join(map(str, A.flatten())) + "\n")
        f.write("B " + " ".join(map(str, B.flatten())) + "\n")

    # Run cocotb (make sure you're in correct directory)
    print("🔧 Launching cocotb testbench via make...")
    result = subprocess.run(["make"], capture_output=True, text=True)
    # print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("❌ Cocotb simulation failed.")

    # Read output matrix

    # Wait for output_buffer.txt
    while not os.path.exists("output_buffer.txt"):
        time.sleep(0.1)

    # Read result matrix C
    with open("output_buffer.txt", "r") as f:
        line = f.readline()
        assert line.startswith("C ")
        values = list(map(float, line.strip().split()[1:]))
        C = np.array(values).reshape(M, N)

    return C
