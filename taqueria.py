menu = {
    "Baja Taco": 4.25,
    "Burrito": 7.50,
    "Bowl": 8.50,
    "Nachos": 11.00,
    "Quesadilla": 8.50,
    "Super Burrito": 8.50,
    "Super Quesadilla": 9.50,
    "Taco": 3.00,
    "Tortilla Salad": 8.00
}

total = 0

while True:
    try:
        item = input("Item: ").title()   # normalize case
    except EOFError:
        break                            # Ctrl+D ends the program
    if item in menu:                     # ignore items not on the menu
        total += menu[item]              # add this item's price
        print(f"Total: ${total:.2f}")    # running total, 2 decimals