'''Simple include analyzer.
Can "compile" the given file with its dependencies into a big file.

Declare includes in comments like this:
(relative include) // include ./demo.ts
(relative include) // include ../lib/any.ts
(absolute include) // include bruh.ts

Absolute includes will be searched in the root path, and the first one found
will be used. Which one is found first is up to the behaviour of rglob().
When relative includes goes out of the root path, you will be warned but compilation
will go normally if the file really exists.
When a file eventually includes itself, a circular include is caused, and you will
be told by an error to fix it.

You don't need to care about namespace things because this is pure copy and paste.
You just need to include a file when you need some variable inside it.'''

from typing import Any
from functools import partial
from pathlib import Path
from warnings import warn

import sys
self_dir = Path(__file__).parent
sys.path.append(str(self_dir))

from lib.parsers import read_info
from lib.simple_tree import Node, Tree, bfs_map, dfs_map

read_include = partial(read_info, ["include"], ' ')

def search_name(fn: str, includer_fn: Path, root: Path) -> Path:
    '''Search for the corresponding file to a certain import name.'''
    relative = fn.startswith('.')
    
    if relative:
        cwd = includer_fn.parent
        includee_fn = cwd.joinpath(Path(fn))
        if not includee_fn.is_relative_to(root):
            warn('Relative include of %s in %s goes out of root folder!' % (fn, str(includer_fn)))
        if not includee_fn.exists():
            raise ValueError('Relative include of %s in %s not found!' % (fn, str(includer_fn)))
    else:
        try:
            includee_fn = next(root.rglob(fn))
        except StopIteration:
            raise ValueError('Absolute include of %s in %s not found!' % (fn, str(includer_fn)))
    
    return includee_fn


def load_file_lines(f: Path) -> list[str]:
    with open(f, 'r', encoding='utf8') as fp:
        ft = fp.readlines()
    return ft


def parse_include(f: Path):
    fls = load_file_lines(f)
    info, linenum = read_include(fls)
    incl_names, incl_linenum = info['include'], linenum['include']
    return fls, incl_linenum, incl_names


def form_tree_recursive(f: Path, t: Tree, history: dict[Path, tuple[Node, list[int], list[str]]], root: Path):
    try:
        fn, _, _ = history[f]
        t.append_node(fn)
    except KeyError:
        fls, incl_linenum, incl_names = parse_include(f)
        incl_paths = [search_name(fn, f, root) for fn in incl_names]
        fn = Node(f)
        history[f] = fn, incl_linenum, fls
        t.append_node(fn)
        for inclp in incl_paths:
            form_tree_recursive(inclp, t[-1], history, root)


def form_tree(init_f: Path, root: Path) -> tuple[Tree, dict[Path, tuple[list[int], list[str]]]]:
    init_f = init_f.absolute()
    root = root.absolute()

    t = Tree(); history = {}
    form_tree_recursive(init_f, t, history, root)
    # manual unbind
    t0 = t[0]
    t.init_node.child = []
    t0.init_node.father = None
    return t0, {k:v[1:] for k, v in history.items()}


def circuit_check(objs: list[Any]):
    try:
        circid = objs[:-1].index(objs[-1])
    except ValueError:
        circid = -1
    
    if circid != -1:
        raise ValueError('Circular include happens: %s'
            % ' -> '.join(str(obj) for obj in objs[circid:]))


dfs_circuit_check = partial(dfs_map, circuit_check)


def count_max_depth(record: dict[Any, int], objs: tuple[Any], depth: int):
    for obj in objs:
        last_depth = record[obj] if obj in record else -1
        record[obj] = max(depth, last_depth)


def bfs_count_max_depth(t: Tree) -> dict[Any, int]:
    record = {}
    bfs_map(partial(count_max_depth, record), t)
    return record

def main(tfpstr: str, rootdstr: str, outpstr: str):
    tfp = Path(tfpstr)
    rootd = Path(rootdstr)
    outp = Path(outpstr)
    
    incl_tree, file_data = form_tree(tfp, rootd)
    dfs_circuit_check(incl_tree)
    incl_count = bfs_count_max_depth(incl_tree)
    incl_order = sorted(incl_count.keys(), key=lambda x: incl_count[x], reverse=True)
    
    out_lines = ''
    for p in incl_order:
        incl_lines, data = file_data[p]
        out_lines += ''.join(l for i, l in enumerate(data) if not i in incl_lines) + '\n'

    with open(outp, 'w', encoding='utf8') as outfp:
        outfp.write(out_lines)


if __name__ == '__main__':
    main(*sys.argv[1:])