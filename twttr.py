text = input("Input: ")
result = ""
for c in text:
    if c.lower() not in "aeiou":   # keep it only if it's NOT a vowel
        result += c
print(result)