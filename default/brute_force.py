import argparse
import itertools
import hashlib
import sys
import time
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, Optional


def generate_combinations(charset: str, min_length: int, max_length: int,
                          prefix: str = "", suffix: str = "") -> Iterable[str]:
    """Yield candidate passwords given charset and length bounds.

    Prefix and suffix are prepended/appended to every candidate.
    """
    for length in range(min_length, max_length + 1):
        for tup in itertools.product(charset, repeat=length):
            yield f"{prefix}{''.join(tup)}{suffix}"


def _get_hasher(name: str) -> Callable[[bytes], str]:
    """Return a function accepting bytes and returning a hex digest.

    Supported names are passed through ``hashlib.new``; raise ``ValueError``
    if the algorithm is unavailable.
    """
    try:
        h = hashlib.new(name)
    except ValueError as exc:
        raise
    def hasher(data: bytes) -> str:
        return hashlib.new(name, data).hexdigest()
    return hasher


def crack_hash(target_hash: str,
               candidates: Iterable[str],
               algorithm: str = "md5",
               verbose: bool = True) -> Optional[str]:
    """
    Brute-force a hash (default MD5) by trying each candidate string.

    ``algorithm`` may be any name supported by :mod:`hashlib` (md5,
    sha1, sha256, etc.).

    ``candidates`` is an iterable of plaintexts; it can be a generator.

    Returns the recovered plaintext or ``None`` if not found.
    """
    hasher = _get_hasher(algorithm)
    target = target_hash.lower()
    start_time = time.time()
    total = 0

    if verbose:
        print(f"🔍 Starting {algorithm} attack against {target_hash}")
        print("-" * 60)

    for pw in candidates:
        total += 1
        if hasher(pw.encode("utf-8")) == target:
            if verbose:
                elapsed = time.time() - start_time
                print(f"\n🎉 SUCCESS! Password found: '{pw}'")
                print(f"   Attempts     : {total:,}")
                print(f"   Time taken   : {str(timedelta(seconds=int(elapsed)))}")
            return pw
        if verbose and total % 1_000_000 == 0:
            elapsed = time.time() - start_time
            print(f"   tried {total:,} candidates; elapsed {int(elapsed)}s", end="\r")

    if verbose:
        elapsed = time.time() - start_time
        print(f"\n❌ Exhausted candidates after {total:,} attempts ({str(timedelta(seconds=int(elapsed)))})")
    return None


def crack_hash_threaded(target_hash: str,
                              candidates: Iterable[str],
                              algorithm: str = "md5",
                              workers: int = 8,
                              verbose: bool = True) -> Optional[str]:
    """Threaded version of :func:`crack_hash`.

    Splits work across ``workers`` threads. The iterable is consumed by a
    shared iterator; threads stop as soon as a match is found.
    """
    hasher = _get_hasher(algorithm)
    target = target_hash.lower()
    start_time = time.time()
    total = 0
    found: Optional[str] = None

    if verbose:
        print(f"🔍 Starting threaded {algorithm} attack (workers={workers}) against {target_hash}")
        print("-" * 60)

    def worker(it):
        nonlocal total, found
        for pw in it:
            if found is not None:
                return None
            total += 1
            if hasher(pw.encode("utf-8")) == target:
                found = pw
                return pw
        return None

    iterator = iter(candidates)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(worker, iterator) for _ in range(workers)]
        for future in futures:
            if future.result():
                break

    if found and verbose:
        elapsed = time.time() - start_time
        print(f"\n🎉 SUCCESS! Password found: '{found}'")
        print(f"   Attempts     : {total:,}")
        print(f"   Time taken   : {str(timedelta(seconds=int(elapsed)))}")
    elif verbose:
        elapsed = time.time() - start_time
        print(f"\n❌ Exhausted candidates after {total:,} attempts ({str(timedelta(seconds=int(elapsed)))})")

    return found


# ========================== COMMAND‑LINE INTERFACE ==========================


def parse_args():
    parser = argparse.ArgumentParser(
        description="Simple MD5 brute-force cracker (educational use only).",
        epilog="Use responsibly; do not attack systems for which you lack authorization.")

    parser.add_argument("hash", help="Target hash to crack (e.g. 32 hex for MD5)")
    parser.add_argument("-a", "--algorithm", default="md5",
                        choices=hashlib.algorithms_available,
                        help="Hash algorithm (md5, sha1, sha256, etc.)")
    parser.add_argument("-c", "--charset", default="abcdefghijklmnopqrstuvwxyz0123456789",
                        help="Characters to use for brute forcing (default: lowercase+digits)")
    parser.add_argument("-m", "--max-length", type=int, default=6,
                        help="Maximum password length to brute-force")
    parser.add_argument("--min-length", type=int, default=1,
                        help="Minimum password length to try (default: 1)")
    parser.add_argument("-p", "--prefix", default="",
                        help="Optional prefix prepended to every candidate")
    parser.add_argument("-s", "--suffix", default="",
                        help="Optional suffix appended to every candidate")
    parser.add_argument("-w", "--wordlist", type=argparse.FileType('r'),
                        help="Path to file containing candidate passwords (one per line)")
    parser.add_argument("-t", "--threads", type=int, default=1,
                        help="Number of worker threads (1 = no threading)")
    parser.add_argument("--workers", dest="threads",
                        help=argparse.SUPPRESS)  # legacy name
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress progress output (still prints result)")
    return parser.parse_args()


def main(argv=None):
    """Command-line entry point for setuptools/script usage."""
    args = parse_args() if argv is None else parse_args(argv)

    # build candidate iterator
    if args.wordlist:
        candidates = (line.strip() for line in args.wordlist if line.strip())
    else:
        candidates = generate_combinations(
            args.charset, args.min_length, args.max_length,
            prefix=args.prefix, suffix=args.suffix)

    verbose = not args.quiet

    if args.threads > 1:
        result = crack_hash_threaded(args.hash, candidates,
                                     algorithm=args.algorithm,
                                     workers=args.threads,
                                     verbose=verbose)
    else:
        result = crack_hash(args.hash, candidates,
                             algorithm=args.algorithm,
                             verbose=verbose)

    if result is None:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
