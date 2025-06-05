def shift_in_bits(initial_hex, input_bits):
    # Convert initial value to 32-bit integer
    reg = int(initial_hex, 16) & 0xFFFFFFFF

    if len(input_bits) != 32:
        raise ValueError("You must provide exactly 32 input bits.")

    print(f"Initial: 0x{reg:08X}")
    for i, bit in enumerate(input_bits):
        bit = int(bit) & 1  # Ensure it's 0 or 1
        reg = ((reg << 1) | bit) & 0xFFFFFFFF  # Shift left and insert bit
        print(f"After bit {i+1} ({bit}): 0x{reg:08X}")

# Example usage:
if __name__ == "__main__":
    # Initial value
    initial_hex = "0xb3e97a60f"

    # Bits to shift in from LSB side (enter as list of 0s and 1s)
    input_bits = [
        0, 0, 1, 1, 1, 1, 1, 0,
        0, 0, 0, 0, 1, 1, 1, 1,
        1, 0, 0, 0, 0, 0, 0, 0,
        1, 0, 0, 1, 0, 1, 1, 1
    ]

    shift_in_bits(initial_hex, input_bits)
