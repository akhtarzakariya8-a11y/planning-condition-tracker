name = input("camelCase: ")
snake = ""
for c in name:
    if c.isupper():
        snake += "_" + c.lower()
    else:
        snake += c
print(snake)