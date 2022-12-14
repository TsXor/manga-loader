from __future__ import annotations
from typing import Any, Optional, Callable, Iterator, Generator
from itertools import chain
from textwrap import indent

class Node:
    def __init__(self, obj: Any = None, father: Optional[Node] = None,
    child: Optional[list[Node] | Node] = None) -> None:
        if child is None:
            child_list: list[Node] = []
        elif isinstance(child, self.__class__):
            child_list: list[Node] = [child]
        elif isinstance(child, list):
            child_list: list[Node] = child
        else:
            raise ValueError
        
        for c in child_list: c.father = self
        
        self.obj = obj
        self.father = father
        self.child = child_list
        self.tree: Optional[Tree] = None
    
    @property
    def have_father(self) -> bool:
        return self.father is None

    @property
    def have_child(self) -> bool:
        return bool(self.child)

    @property
    def n_children(self) -> int:
        return len(self.child)

    @property
    def detached(self) -> Node:
        '''Note: detached nodes cannot be found by its subnodes!'''
        return Node(obj=self.obj, child=self.child)

    def append_child(self, x: Node, detach: bool = True) -> None:
        if x.have_father and detach: x = x.detached
        self.child.append(x)

    def __eq__(self, x: Any) -> bool:
        try:
            return self.obj == x.obj
        except AttributeError:
            return False


class Tree:
    def __new__(cls: type[Tree], init_node: Optional[Node] = None) -> Tree:
        old_tree: 'Tree' | None = getattr(init_node, 'tree', None)
        return super().__new__(cls) if old_tree is None else old_tree

    def __init__(self, init_node: Optional[Node] = None) -> None:
        if init_node is None:
            init_node = Node()
        elif not (init_node.tree is None):
            return
        self.init_node = init_node
        self.init_node.tree = self

    @property
    def is_subtree(self) -> bool:
        return self.init_node.have_father
    
    @property
    def is_end(self) -> bool:
        return not self.init_node.have_child

    def __getitem__(self, i: int) -> Tree:
        child_node = self.init_node.child[i]
        return getattr(child_node, 'tree', Tree(child_node))
    
    def __iter__(self) -> Generator[Tree, None, None]:
        child_iter = iter(self.init_node.child)
        while True:
            try:
                child_node = next(child_iter)
                yield getattr(child_node, 'tree', Tree(child_node))
            except StopIteration:
                break
    
    def append_obj(self, x: Any) -> None:
        xn = Node(obj=x, father=self.init_node)
        self.init_node.child.append(xn)

    def append_node(self, x: Node, detach: bool = True) -> None:
        self.init_node.append_child(x, detach=detach)

    def append_tree(self, x: Tree, detach: bool = True) -> None:
        self.init_node.append_child(x.init_node, detach=detach)
    
    def getobj(self) -> Any:
        return self.init_node.obj
    
    def __repr__(self) -> str:
        if self.is_end:
            return repr(self.getobj())
        else:
            return repr(self.init_node.obj) + '\n' + indent('\n'.join([repr(s) for s in self]), ' '*4)


def dfs_map(f: Callable[[list[Any]], None], t: Tree):
    path: list[Tree] = [t]
    objs: list[Any] = [t.getobj()]
    iters: list[Iterator | Generator] = [iter(t)]
    while path:
        try:
            path.append(next(iters[-1]))
            objs.append(path[-1].getobj())
            iters.append(iter(path[-1]))
        except (StopIteration, GeneratorExit):
            path.pop()
            objs.pop()
            iters.pop()
            continue

        f(objs)

def bfs_map(f: Callable[[tuple[Any], int], None], t: Tree):
    f((t.getobj(),), 0)
    depth = 1; base = [t]
    while base:
        layer = chain(*base)
        objs = tuple(x.getobj() for x in layer)
        f(objs, depth)
        
        depth += 1
        base = tuple(x for x in layer if not x.is_end)