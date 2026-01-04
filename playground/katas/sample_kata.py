# Sample kata exercise: Implement a function to reverse a string and test it

def reverse_string(s: str) -> str:
    """Return the reverse of the input string."""
    return s[::-1]


def test_reverse_string() -> None:
    assert reverse_string('abc') == 'cba'
    assert reverse_string('') == ''
    assert reverse_string('a') == 'a'
    assert reverse_string('racecar') == 'racecar'


if __name__ == '__main__':
    test_reverse_string()
    print('Sample kata passed all tests.')
