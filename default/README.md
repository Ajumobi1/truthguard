# Brute Force Hash Cracker (Python)

A simple, educational Python script for brute-forcing cryptographic
hashes such as MD5, SHA1, SHA256, etc.  It demonstrates basic
combinatorics, command-line parsing, and an optional threaded worker
pool. **Do not use this tool for any unauthorized activity**; it is
meant solely for learning and testing in controlled environments.

## Features

- Generate candidate passwords from a charset, with optional
  prefix/suffix and length range.
- Read candidates from a wordlist file.
- Support for **any hash algorithm** available in Python's
  `hashlib` (e.g. `md5`, `sha1`, `sha256`).
- Single-threaded or multi-threaded execution.
- Progress output and quiet mode.
- Return codes suitable for scripting (`0` if cracked, `1` otherwise).

## Usage

```bash
python brute_force.py HASH [options]
```

Run `python brute_force.py --help` for full option list. Examples:

```bash
# try lowercase+digits, lengths 1..6
python brute_force.py 482c811da5d5b4bc6d497ffa98491e38

# use sha256 and 4 threads
python brute_force.py -a sha256 -t 4 <hash>

# brute-force with a wordlist
python brute_force.py -w passwords.txt <hash>
```

## Development

Install `pytest` and run tests:

```bash
python -m pip install -U pytest
pytest
```

The `pyproject.toml` file is provided for packaging the tool; you can
install it into your environment with:

```bash
python -m pip install -e .
```

## License & Disclaimer

This code is public domain / MIT-style. Use at your own risk. Cracking
passwords or passcodes without permission is illegal. **It cannot be
used to bypass modern phone lock screens or other secure hardware; it
merely illustrates brute-force hashing.**

This repository is for educational purposes only (e.g. studying for
exams) and the author assumes no liability.
