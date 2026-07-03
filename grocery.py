groceries = {}

while True:
    try:
        item = input().upper()      # normalize case (uppercase works since output is uppercase too)
    except EOFError:
        break                       # Ctrl+D — done collecting
    if item in groceries:
        groceries[item] += 1        # count it
    else:
        groceries[item] = 1

print()                             # newline after Ctrl+D, keeps output tidy
for item in sorted(groceries):      # alphabetical order
    print(groceries[item], item)    # "count ITEM"