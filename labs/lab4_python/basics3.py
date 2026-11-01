import math


def celsius_to_fahrenheit(c):
    return c * 9 / 5 + 32


def describe_temperature(c):
    if c < 50:
        return "cool"
    elif c < 70:
        return "warm"
    return "hot"


for t in [35, 48.5, 62, 85]:
    f = celsius_to_fahrenheit(t)
    print(f"{t} C = {f:.1f} F ({describe_temperature(t)})")

print("Square root of 2:", math.sqrt(2))

with open("readings.txt", "w") as file:
    for t in [35, 48.5, 62, 85]:
        file.write(f"{t}\n")

with open("readings.txt") as file:
    values = [float(line) for line in file]
print("Read back:", values)
print("Average:", sum(values) / len(values))

try:
    number = int("abc")
except ValueError:
    print("That is not a number")
