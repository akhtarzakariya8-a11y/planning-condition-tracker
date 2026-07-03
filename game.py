import random

# Phase 1: get a valid level n
while True:
    try:
        n = int(input("Level: "))
        if n > 0:
            break
    except ValueError:
        pass

# Generate the secret number
secret = random.randint(1, n)

# Phase 2: guessing loop
while True:
    try:
        guess = int(input("Guess: "))
    except ValueError:
        continue              # not a number — re-prompt
    if guess < 1:
        continue              # not positive — re-prompt
    if guess < secret:
        print("Too small!")
    elif guess > secret:
        print("Too large!")
    else:
        print("Just right!")
        break