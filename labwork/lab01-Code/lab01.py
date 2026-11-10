# ANSWER QUESTION q1

# ANSWER QUESTION q2

# ANSWER QUESTION q3


def factorial(n):
    """Return the factorial of a non-negative integer n.

    >>> factorial(3)
    6
    >>> factorial(5)
    120
    """
    ans=1
    if n==0 or n==1:
        return 1
    while(n>=1):
        ans*=n
        n-=1
    return ans


def is_right_triangle(a, b, c):
    """Given three integers (maybe non-positive), judge whether the three
    integers can form the three sides of a right triangle.

    >>> is_right_triangle(2, 1, 3)
    False
    >>> is_right_triangle(5, -3, 4)
    False
    >>> is_right_triangle(5, 3, 4)
    True
    """
    if a<=0 or b<=0 or c<=0:
        return False
    if a>b:
        a,b=b,a
    if b>c:
        b,c=c,b
    if a>b:
        a,b=b,a
    if a+b<=c:
        return False
    if a**2+b**2==c**2:
        return True
    return False


def number_of_k(n, k):
    """Return the number of occurrences of k in each digit of a non-negative
    integer n.

    >>> number_of_k(999, 9)
    3
    >>> number_of_k(1234321, 2)
    2
    """
    if n==0:
        if k==0:
            return 1
        return 0
    i=0
    while n!=0:
        if n%10==k:
            i+=1
        n//=10
    return i
        


def count_squares(a, b):
    """Count squares cut from an a-by-b rectangle, taking the largest each time.

    a and b are positive integers.

    >>> count_squares(13, 5)
    6
    >>> count_squares(1, 5)
    5
    """
    i=0
    while a!=b:
        if a>b:
            a,b=b,a
        a,b=b-a,a
        i+=1

    return i+1