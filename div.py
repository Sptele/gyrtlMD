import pyrtl
import time

start = pyrtl.Input(bitwidth=1, name="start")
divisor = pyrtl.Input(bitwidth=32, name="divisor")  # D - 32b
dividend = pyrtl.Input(bitwidth=64, name="dividend")  # N - 64b

flag = pyrtl.Register(bitwidth=1, name="flag")
valid = pyrtl.Output(bitwidth=1, name="valid")
quotient_output = pyrtl.Output(bitwidth=64, name="quotient_output")
remainder_output = pyrtl.Output(bitwidth=32, name="remainder_output")

def div(d_start: pyrtl.Input, d_divisor: pyrtl.Input, d_dividend: pyrtl.Input, d_flag: pyrtl.Register,
		d_valid: pyrtl.Output) -> tuple[pyrtl.Register, pyrtl.Register]:
	"""
	A 32-bit divider that produces both the quotient and remainder. It runs for 33 cycles before returning.
	Division: Dividend (N) / Divisor (D)
	:param d_start: the 1b start flag
	:param d_divisor: the 32b divisor (which divides the dividend)
	:param d_dividend: the 64b dividend (the number that is being divided)
	:param d_flag: a 1b output flag that, when high, indicates that the divider is busy
	:param d_valid: a 1b output flag that, when high, indicates that the output is finalized
	:return: a tuple containing (in order) the 64b quotient and the 32b remainder
	"""
	# divided / divisor

	q = pyrtl.Register(bitwidth=64, name="div_q")
	r = pyrtl.Register(bitwidth=32, name="div_r")

	d = pyrtl.Register(bitwidth=64, name="div_d")  # D = divisor

	div_c_ONE = pyrtl.Const(val=1, bitwidth=32, name="div_c_ONE")

	counter = pyrtl.Register(bitwidth=6, name="div_counter")

	with pyrtl.conditional_assignment:
		# Start State
		with (counter == 0) & (d_start == 1):
			r.next |= d_dividend  # The remainder
			d.next |= pyrtl.concat(d_divisor, pyrtl.Const(0, bitwidth=32))  # The divisor

			# Flags
			d_flag.next |= 1
			d_valid |= 0

			counter.next |= counter + 1

		# End State
		with (counter > 33):
			d_flag.next |= 0
			d_valid |= 1

		# Run State
		with d_flag == 1:
			diff = pyrtl.signed_sub(r, d)
			with diff[-1] == 0: # MSB indicates the signedness
				r.next |= diff

				q.next |= pyrtl.concat(q[0:31], pyrtl.Const(val=1, bitwidth=1))
			with diff[-1] == 1:
				q.next |= pyrtl.shift_left_logical(q, div_c_ONE)

			d.next |= pyrtl.shift_right_logical(d, div_c_ONE)

			counter.next |= counter + 1

	return q, r


out = div(start, divisor, dividend, flag, valid)

quotient_output <<= out[0]
remainder_output <<= out[1]

num_iterations = 36

def run_iter(i_n, d):
	global num_iterations

	sim = pyrtl.FastSimulation()

	sim_inputs = {"start": [1 for _ in range(num_iterations)],
				  "dividend": [i_n for _ in range(num_iterations)],
				  "divisor": [d for _ in range(num_iterations)]}

	sim.step_multiple(sim_inputs)

	return pyrtl.val_to_signed_integer(sim.inspect("quotient_output"), bitwidth=32), pyrtl.val_to_signed_integer(sim.inspect("remainder_output"), bitwidth=32)


def test(n):
	num_fails = 0

	for i in range(0, n):
		for j in range(1, n):
			expected_quotient, expected_remainder = i // j, i % j
			actual_quotient, actual_remainder = run_iter(i, j)


			if expected_quotient != actual_quotient:
				print (f"TEST FAILED ({i} / {j}):\n\tExpected Quotient {expected_quotient}, but got {actual_quotient}!")
				num_fails += 1
			if expected_remainder != actual_remainder:
				print (f"TEST FAILED ({i} / {j}):\n\tExpected Remainder {expected_remainder}, but got {actual_remainder}!")
				num_fails += 1

	return num_fails

if __name__ == '__main__':
	print ("Beginning Division Circuit Tests for all ordered pairs (Nat x Positive Integer) in 100 x 100 (starting (0, 1)")
	print ("To reduce runtime, this tester will only print if an error occurs.")

	print (f"Running tests...")

	start = time.perf_counter()
	fails = test(100)
	end = time.perf_counter()

	if fails > 0:
		print (f"{fails} tests failed. Check previous output for details.")
	else:
		print (f"All tests passed!")

	print (f"Completed tests in {end-start} seconds!")




