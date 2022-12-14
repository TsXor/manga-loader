from typing import Iterable, Any
from functools import partial

COMMENT_SYMBOL = r'//'

def uncomment_line(enum: tuple[int, str]):
    idx, line = enum
    is_comment = line.startswith(COMMENT_SYMBOL)
    return (idx, line[len(COMMENT_SYMBOL):].strip()) if is_comment else False

def match_lines(lines: Iterable[tuple[int, str]], sep: str, once: bool, key: str) \
        -> tuple[str, tuple[tuple[str, int]] | None]:
    try:
        klines = filter(lambda ll: ll[1].startswith(key), lines)
        first = next(klines)
        klines = (first, ) if once else (first, *klines)
        return key, tuple((line.split(sep, 1)[1].strip(), idx) for idx, line in klines)
    except StopIteration:
        # no matching lines
        return key, None

def read_info(keys: list[str], sep: str, lines: Iterable[str]) \
        -> tuple[dict[str, list[str]], dict[str, list[int]]]:
    info_lines = filter(None, map(uncomment_line, enumerate(lines)))
    info_kvs = map(partial(match_lines, info_lines, sep, False), keys)
    result = {}; lineids = {}
    for key, values in info_kvs:
        vs, lids = ([], []) if values is None else zip(*values)
        result[key] = vs
        lineids[key] = lids
    return result, lineids

def read_info_once(keys: list[str], sep: str, lines: Iterable[str]) \
        -> tuple[dict[str, str | None], dict[str, int]]:
    info_lines = filter(None, map(uncomment_line, enumerate(lines)))
    info_kvs = map(partial(match_lines, info_lines, sep, True), keys)
    result = {}; lineids = {}
    for key, values in info_kvs:
        vs, lids = zip(*values)
        result[key] = vs[0]
        lineids[key] = lids[0]
    return result, lineids