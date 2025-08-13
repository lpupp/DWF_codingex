from typing import Optional, Tuple, Iterator


class FixedHashTable:
    """Fixed-size hash table (string -> int) using linear probing and tombstones."""
    __slots__ = ("capacity", "keys", "vals", "state", "prev", "next", "head", "tail", "size")

    EMPTY = 0
    OCCUPIED = 1
    DELETED = 2

    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("capacity must be positive")

        self.capacity = capacity

        self.keys: list[Optional[str]] = [None] * capacity
        self.vals: list[Optional[int]] = [None] * capacity
        self.state: list[int] = [self.EMPTY] * capacity  # EMPTY, OCCUPIED, DELETED

        # Doubly-linked list over OCCUPIED indices to track recency
        self.prev: list[Optional[int]] = [None] * capacity
        self.next: list[Optional[int]] = [None] * capacity
        self.head: Optional[int] = None
        self.tail: Optional[int] = None
        self.size = 0

    def _idx(self, key: str) -> int:
        # Python's hash is salted per run
        return (hash(key) & 0x7FFFFFFF) % self.capacity

    def _probe(self, key: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Linear probe for key.

        Returns (found_idx, insert_idx).
        - found_idx: index if key exists, else None.
        - insert_idx: first tombstone else first empty seen, else None if table saturated.
        """
        start = self._idx(key)
        first_tombstone = None
        i = start
        while True:
            st = self.state[i]
            if st == self.EMPTY:
                # Key not present
                return (None, first_tombstone if first_tombstone is not None else i)
            if st == self.OCCUPIED:
                if self.keys[i] == key:
                    return (i, None)
            else:  # DELETED
                if first_tombstone is None:
                    first_tombstone = i

            i += 1
            if i == self.capacity:
                i = 0
            if i == start:
                # Full cycle: key not found; only insert if we saw a tombstone
                return (None, first_tombstone)
        
    # --- Recency helpers ---
    def _link_to_head(self, i: int) -> None:
        """Insert node i at head of recency list."""
        self.prev[i] = None
        self.next[i] = self.head
        if self.head is not None:
            self.prev[self.head] = i
        self.head = i
        if self.tail is None:
            self.tail = i

    def _move_to_head(self, i: int) -> None:
        """Move existing node i to head."""
        if i == self.head:
            return
        self._unlink(i)
        self._link_to_head(i)

    def _unlink(self, i: int) -> None:
        """Remove node i from recency list (does not change table state)."""
        p, n = self.prev[i], self.next[i]
        if p is not None:
            self.next[p] = n
        else:
            self.head = n
        if n is not None:
            self.prev[n] = p
        else:
            self.tail = p
        self.prev[i] = self.next[i] = None

    # --- Public API ---
    def insert(self, key: str, value: int) -> None:
        """
        Insert key->value or replace existing value.

        Recency rule: any insertion or value change becomes most recent.
        Raises RuntimeError if table is full.
        """
        found_idx, insert_idx = self._probe(key)

        if found_idx is not None:
            self.vals[found_idx] = value
            self._move_to_head(found_idx)
            return
    
        if insert_idx is None:
            raise RuntimeError("Hash table is full")
        
        # insert at insert_idx (tombstone or empty)
        self.keys[insert_idx] = key
        self.vals[insert_idx] = value
        self.state[insert_idx] = self.OCCUPIED
        self._link_to_head(insert_idx)
        self.size += 1

    def get(self, key: str) -> int:
        """
        Return value for key. 
        
        Recency rule: Does NOT affect recency.
        Raises KeyError if not found.
        """
        found_idx, _ = self._probe(key)
        if found_idx is None:
            raise KeyError(key)
        return self.vals[found_idx]  # type: ignore[return-value]

    def remove(self, key: str) -> None:
        """
        Remove key from table. Uses tombstones to keep probing correctness.

        Recency rule: does not affect recency unless removed key was most recent.
        Raises KeyError if key not found.
        """
        found_idx, _ = self._probe(key)
        if found_idx is None:
            raise KeyError(key)

        self._unlink(found_idx)

        self.keys[found_idx] = None
        self.vals[found_idx] = None
        self.state[found_idx] = self.DELETED  # tombstone
        self.size -= 1

    def get_last(self) -> Tuple[str, int]:
        """Most recently inserted or changed key-value pair."""
        if self.head is None:
            raise KeyError("empty")
        i = self.head
        return self.keys[i], self.vals[i]  # type: ignore[return-value]

    def get_first(self) -> Tuple[str, int]:
        """Least recently inserted or changed key-value pair."""
        if self.tail is None:
            raise KeyError("empty")
        i = self.tail
        return self.keys[i], self.vals[i]  # type: ignore[return-value]

    def items(self) -> Iterator[Tuple[str, int]]:
        """Iterate over all occupied key-value pairs for debugging."""
        for i in range(self.capacity):
            if self.state[i] == self.OCCUPIED:
                yield self.keys[i], self.vals[i]  # type: ignore[misc]

