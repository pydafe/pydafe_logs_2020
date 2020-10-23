import math

from functools import lru_cache


@lru_cache
def trib(n):
    if n < 3:
        return 1
    else:
        return trib(n - 1) + trib(n - 2) + trib(n - 3)


print(trib(10))
