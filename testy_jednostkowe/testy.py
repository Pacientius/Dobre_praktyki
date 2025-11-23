import re
import pytest


#   func

def palindrome(text: str) -> bool:
    cleaned = ''.join(c.lower() for c in text if c.isalnum())
    return cleaned == cleaned[::-1]


def fibonacci(n: int) -> int:
    if n < 0:
        raise ValueError("n must be >= 0")
    if n == 0:
        return 0
    if n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def c_vowels(text: str) -> int:
    vowels = set('aąeęiouyó')
    return sum(1 for c in text.lower() if c in vowels)


def c_discount(price: float, discount: float) -> float:
    if not (0 <= discount <= 1):
        raise ValueError("Discount must be between 0 and 1.")
    return price * (1 - discount)


def flatten_list(nested_list: list) -> list:
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result


def word_frequencies(text: str) -> dict:
    words = re.findall(r'\b\w+\b', text.lower())
    freq = {}
    for word in words:
        freq[word] = freq.get(word, 0) + 1
    return freq

def prime(n: int) -> bool:
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

#   testy:

def test_palindrome():
    assert palindrome("kajak")
    assert palindrome("Kobyła ma mały bok")
    assert not palindrome("python")
    assert palindrome("")
    assert palindrome("A")


def test_fibonacci():
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1
    assert fibonacci(5) == 5
    assert fibonacci(10) == 55
    with pytest.raises(ValueError):
        fibonacci(-1)


def test_c_vowels():
    assert c_vowels("Python") == 2
    assert c_vowels("AEIOUY") == 6
    assert c_vowels("bcd") == 0
    assert c_vowels("") == 0
    assert c_vowels("Próba żółwia") == 5


def test_c_discount():
    assert c_discount(100, 0.2) == 80.0
    assert c_discount(50, 0) == 50.0
    assert c_discount(200, 1) == 0.0

    with pytest.raises(ValueError):
        c_discount(100, -0.1)

    with pytest.raises(ValueError):
        c_discount(100, 1.5)


def test_flatten_list():
    assert flatten_list([1, 2, 3]) == [1, 2, 3]
    assert flatten_list([1, [2, 3], [4, [5]]]) == [1, 2, 3, 4, 5]
    assert flatten_list([]) == []
    assert flatten_list([[[1]]]) == [1]
    assert flatten_list([1, [2, [3, [4]]]]) == [1, 2, 3, 4]


def test_word_frequencies():
    assert word_frequencies("To be or not to be") == {
        "to": 2, "be": 2, "or": 1, "not": 1
    }
    assert word_frequencies("Hello, hello!") == {"hello": 2}
    assert word_frequencies("") == {}
    assert word_frequencies("Python Python python") == {"python": 3}
    assert word_frequencies("Ala ma kota, a kot ma Ale.") == {
        "ala": 1,
        "ma": 2,
        "kota": 1,
        "a": 1,
        "kot": 1,
        "ale": 1,
    }


def test_prime():
    assert prime(2)
    assert prime(3)
    assert not prime(4)
    assert not prime(0)
    assert not prime(1)
    assert prime(97)
