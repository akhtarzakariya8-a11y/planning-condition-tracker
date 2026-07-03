total = 0

while total < 50:
    print("Amount Due:", 50 - total)
    coin = int(input("Insert Coin: "))
    if coin in [25, 10, 5]:
        total += coin

print("Change Owed:", total - 50)