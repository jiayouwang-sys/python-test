"""
创建一个函数，用来判断一个数字是否为素数。
"""

from math import isqrt


def is_prime(n: int) -> bool:
    """Return True if ``n`` is a prime number.

    A prime number is a natural number greater than 1 that has no
    positive divisors other than 1 and itself.
    """
    if n <= 1:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False

    limit = isqrt(n)
    for i in range(3, limit + 1, 2):
        if n % i == 0:
            return False
    return True


if __name__ == "__main__":
    for num in range(1, 21):
        print(f"{num} is prime: {is_prime(num)}")
