"""Lab 3: Recursion"""

LAB_SOURCE_FILE = "lab03.py"


# ANSWER QUESTION q1

# ANSWER QUESTION q2

# ANSWER QUESTION q3


def number_of_k(n, k):
    """Return the number of occurrences of k in each digit of a non-negative
    integer n.

    >>> number_of_k(999, 9)
    3
    >>> number_of_k(1234321, 2)
    2
    >>> # Do not use while/for loops!
    >>> from construct_check import check
    >>> # ban iteration
    >>> check(LAB_SOURCE_FILE, 'number_of_k', ['While', 'For'])
    True
    """
    """if n==0:
        if k==0:
            return 1
        else:
            return 0"""
    if n%10==k:
        if n//10!=0:
            return 1+number_of_k(n//10,k)
        return 1
    else:
        if n//10!=0:
            return number_of_k(n//10,k)
        return 0


def f91(n):
    """Takes a number n and returns n - 10 when n > 100,
    returns f91(f91(n + 11)) when n ≤ 100.

    >>> f91(1)
    91
    >>> f91(2)
    91
    >>> f91(100)
    91
    """
    if n>100:
        return n-10
    else:
        return f91(f91(n + 11))


def is_monotone(n):
    """Returns whether n has monotone digits.
    Implement using recursion!

    >>> is_monotone(22000130)
    False
    >>> is_monotone(1234)
    True
    >>> is_monotone(24555)
    True
    >>> # Do not use while/for loops!
    >>> from construct_check import check
    >>> # ban iteration
    >>> check(LAB_SOURCE_FILE, 'is_monotone', ['While', 'For'])
    True
    """
    if n<10:
        return True
    if n%10 < n//10%10:
        return False
    else:
        return is_monotone(n//10)


def count_stair_ways(n):
    """Returns the number of ways to climb up a flight of
    n stairs, moving either 1 step or 2 steps at a time.
    >>> count_stair_ways(3)
    3
    >>> count_stair_ways(4)
    5
    >>> count_stair_ways(10)
    89
    """
    if n==1 or n==0:
        return 1
    return count_stair_ways(n-1)+count_stair_ways(n-2)


def count_k(n, k):
    """Counts the number of paths to climb up a flight of n stairs,
    taking up to and including k steps at a time.
    >>> count_k(3, 3) # 3, 2 + 1, 1 + 2, 1 + 1 + 1
    4
    >>> count_k(4, 4)
    8
    >>> count_k(10, 3)
    274
    >>> count_k(300, 1) # Only one step at a time
    1
    >>> count_k(3, 5) # Take no more than 3 steps
    4
    """
    if n==0 or n==1:
        return 1
    if n<0:
        return 0
    sum=0
    for i in range(max(n-k,0),n):
        sum+=count_k(i,k)
    return sum


def paths(m, n):
    """Return the number of paths from one corner of an
    M by N grid to the opposite corner.

    >>> paths(2, 2)
    2
    >>> paths(5, 7)
    210
    >>> paths(117, 1)
    1
    >>> paths(1, 157)
    1
    """
    if m==0 or n==0:
        return 0
    if m==1 or n==1:
        return 1
    return paths(m-1,n)+paths(m,n-1)
