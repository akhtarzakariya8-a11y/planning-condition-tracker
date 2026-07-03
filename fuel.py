while True:
    try:
        fraction = input("Fraction: ")
        x, y = fraction.split("/")
        x = int(x)
        y = int(y)
        if x > y:
            raise ValueError          # more than full — invalid
        percent = round(x / y * 100)  # divide, scale, round
        break                         # input was good, exit loop
    except (ValueError, ZeroDivisionError):
        pass                          # bad input — loop again

if percent <= 1:
    print("E")
elif percent >= 99:
    print("F")
else:
    print(f"{percent}%")