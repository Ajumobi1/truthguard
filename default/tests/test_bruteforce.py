import hashlib
import itertools
import pytest

from brute_force import (
    generate_combinations,
    crack_hash,
    crack_hash_threaded,
)


def test_generate_combinations_simple():
    # charset 'ab', lengths 1..2, no prefix/suffix
    result = list(generate_combinations('ab', 1, 2))
    assert result == ['a', 'b', 'aa', 'ab', 'ba', 'bb']


def test_crack_hash_md5():
    # create a small candidate list and a hash
    pw = 'test'
    h = hashlib.md5(pw.encode()).hexdigest()
    candidates = ['foo', 'bar', 'test', 'baz']
    assert crack_hash(h, candidates, algorithm='md5', verbose=False) == pw


def test_crack_hash_sha256():
    pw = 'hello'
    h = hashlib.sha256(pw.encode()).hexdigest()
    # simple explicit list containing the password
    candidates = ['foo', 'bar', 'hello', 'baz']
    assert crack_hash(h, candidates, algorithm='sha256', verbose=False) == pw


def test_threaded_matches_serial():
    pw = 'xyz'
    h = hashlib.sha1(pw.encode()).hexdigest()
    candidates = generate_combinations('xyz', 1, 3)
    serial = crack_hash(h, candidates, algorithm='sha1', verbose=False)
    # regenerate because generator was consumed
    candidates = generate_combinations('xyz', 1, 3)
    threaded = crack_hash_threaded(h, candidates, algorithm='sha1', workers=2, verbose=False)
    assert serial == threaded == pw
