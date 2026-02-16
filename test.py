"""Given an integer n, for every positive integer i <= n, the task is to print,
§  "FizzBuzz" if i is divisible by 3 and 5,
§  "Fizz" if i is divisible by 3,
§  "Buzz" if i is divisible by 5
§  "i" as a string, if none of the conditions are true.


 n is positive
"""


def fizz2(n: int):
	for i in range(n+1):
		if i % 3 == 0 and i % 5 == 0:
			print("FizzBuzz")
		elif i % 3 == 0:
			print("Fizz")
		elif i % 5 == 0:
			print("Buzz")
		else:
			print(i)


def fizzbuzz(n: int):
	for i in range(n+1):
		s = ""
		if i % 3 == 0:
			s += "Fizz"
		if i % 5 == 0:
			s += "Buzz"
		
		if s == "":
			print(i)
		else:
			print(s)
		
fizzbuzz(15)
