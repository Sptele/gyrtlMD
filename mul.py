import pyrtl
import time

start = pyrtl.Input(bitwidth=1, name="start")  # shows that the program just started
factor0 = pyrtl.Input(bitwidth=32, name="factor0")  # m
factor1 = pyrtl.Input(bitwidth=32, name="factor1")  # n

flag = pyrtl.Register(bitwidth=1, name="flag")  # busy signal
valid = pyrtl.Output(bitwidth=1, name="valid")  # high when its done
result = pyrtl.Output(bitwidth=64, name="result")

def mul(m_start: pyrtl.Input, m_factor0: pyrtl.Input, m_factor1: pyrtl.Input, m_flag: pyrtl.Register,
		m_valid: pyrtl.Output) -> pyrtl.Register:
	"""
	Mul is a 32-bit variable-cycle shift-and-add multiplier. It terminates as soon as it completes the output, up to a total of 32 cycles.
	:param m_start: the 1b start flag
	:param m_factor0: the 32b multiplicand
	:param m_factor1: the 32b multiplier
	:param m_flag: a 1b output flag that, when high, indicates that the multiplier is busy
	:param m_valid: a 1b output flag that, when high, indicates that the output is finalized
	:return: the 64b result of multiplying the multiplicand and multiplier
	"""
	mul_a = pyrtl.Register(bitwidth=32, name="mul_a")
	mul_b = pyrtl.Register(bitwidth=32, name="mul_b")
	mul_r = pyrtl.Register(bitwidth=64, name="mul_r")

	mul_c_ONE = pyrtl.Const(val=1, bitwidth=32, name="mul_c_ONE")

	mul_counter = pyrtl.Register(bitwidth=6, name="mul_counter")

	with pyrtl.conditional_assignment:
		# Start State
		with (mul_counter == 0) & (m_start == 1):
			# Init registers
			# a should be greater than b

			mul_a.next |= m_factor0
			mul_b.next |= m_factor1

			# Init flags
			m_flag.next |= 1
			m_valid |= 0  # reset flag

			mul_counter.next |= mul_counter + 1

		# End State
		with (mul_b == 0) | (mul_counter > 31):
			m_flag.next |= 0
			m_valid |= 1

		# Run State
		with m_flag == 1:
			with mul_b[0] == 1:  # add
				mul_r.next |= pyrtl.signed_add(mul_r, mul_a)

			mul_a.next |= pyrtl.shift_left_logical(mul_a, mul_c_ONE)
			mul_b.next |= pyrtl.shift_right_logical(mul_b, mul_c_ONE)

			mul_counter.next |= mul_counter + 1

	return mul_r


out = mul(start, factor0, factor1, flag, valid)

result <<= out

num_iterations = 33

def run_iter(i_n, d):
	global num_iterations

	sim = pyrtl.FastSimulation()

	sim_inputs = {"start": [1 for _ in range(num_iterations)],
				  "factor0": [i_n for _ in range(num_iterations)],
				  "factor1": [d for _ in range(num_iterations)]}

	sim.step_multiple(sim_inputs)

	return pyrtl.val_to_signed_integer(sim.inspect("result"), bitwidth=32)


def test(n):
	num_fails = 0

	for i in range(n):
		for j in range(n):
			expected = i * j
			actual = run_iter(i, j)

			if expected != actual:
				print (f"TEST FAILED ({i} * {j}):\n\tExpected Result {expected}, but got {actual}!")
				num_fails += 1

	return num_fails

if __name__ == '__main__':
	print ("Beginning Multiplication Circuit Tests for all ordered pairs of natural numbers in 100 x 100")
	print ("This tester will only print if an error occurs.")

	print (f"Running tests...")

	start = time.perf_counter()
	fails = test(100)
	end = time.perf_counter()

	if fails > 0:
		print (f"{fails} tests failed. Check previous output for details.")
	else:
		print (f"All tests passed!")

	print (f"Completed tests in {end-start} seconds!")