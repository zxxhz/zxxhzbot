all = []

for n in range(10, 32):
    a = [0] * 4
    j = 0
    for i in range(2, n):
        while n % i == 0:
            a[j] = i
            j += 1
            n = n // i
    if a not in all:
        all.append(a)
        
for i in all:
    print(i)
