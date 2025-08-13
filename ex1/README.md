# Fixed-Size Hash Table (Linear Probing with Recency Tracking)

This project implements a fixed-size hash table for string keys and integer values using:
- Linear probing for collision resolution
- Tombstones for efficient deletion
- Recency tracking for `get_last()` and `get_first()`

**Note**: Additional comments are indicated in this README as "**Note**".

## Features

- `insert(key, value)`
    Inserts a new key–value pair or updates an existing key’s value.
    Insertion or update moves the key to most recently used position.

- `get(key)`
    Returns the value for key. Does not affect recency.

- `remove(key)`
    Removes the key–value pair and marks its slot as a tombstone.

- `get_last()`
    Returns (key, value) for the most recently inserted or updated entry.

- `get_first()`
    Returns (key, value) for the least recently inserted or updated entry.

- Fixed capacity:
    Size is set at initialization and never grows.
    Raises `RuntimeError` if the table is full and no tombstones are available.

## Running

Execute the hash table on the Gutenberg corpus:
```
python run_hashtable_gutenberg.py
```

The script loads the text, builds the fixed-size hash table, inserts all words, and prints basic stats.

## How It Works

### Hashing
Computes a hash of the key and maps it into a slot via

```
index = (hash(key) & 0x7FFFFFFF) % capacity
```

The built-in `hash()` is used because, in `sandbox/hash_function.ipynb`, I ran a small analysis of collision rate and execution time for a number of common hash functions on a set of words similar to those in the target text as a function of hash table capacity (loading factor in [0.3, 0.7] were tested).
Collision rates were all similar, but `hash()` was much faster.

The hash function can be switched out if needed.

This notebook has additional dependencies: `nltk, pandas, matplotlib, seaborn`.

**Note**: Python’s built-in `hash()` is salted per run, so slot positions will differ between executions. This can be replaced with a stable hash function if needed. One factor I did not take into consideration when evaluating the hash functions is cryptographic security. The use of Python’s built-in `hash()`, which has per-run salting, is not intentionally for security purposes but coincidental. However, depending on the application of the hash function, this would need to be considered.

### Linear Probing
If the target slot is occupied, the table probes sequentially (wrapping at the end) until it finds:

1. The same key (update in place),
2. The first tombstone (reusable slot), or
3. An empty slot.

### Tombstones
When removing, the slot is marked deleted rather than empty to preserve probe chains for other keys.

**Note**: There is a trade-off with tombstones to consider: they allow for quick deletions but can slow down future linear probes as tombstones accumulate.
An alternative is to shift subsequent elements backward to fill the gap, which avoids tombstones but makes deletion slower.

### Recency Tracking
Uses a doubly linked list over occupied slots for O(1) recency updates:
- Insert/update → move node to head
- `get_first()` → returns tail
- `get_last()` → returns head
- Remove → unlink node

### Space and Capacity Considerations
**Note**: Space usage was not a primary consideration in this solution. The `state` and `vals` lists could be combined by using unique sentinel values to represent empty and deleted states.

**Note**: "Fixed size" is not a native Python concept. Here, list entries are preallocated to simulate fixed capacity, but because Python lists are dynamically sized and this is not strictly enforced, the structure is not truly fixed size.

## Example Usage
```
from fixed_hash_table import FixedHashTable

ht = FixedHashTable(capacity=10)

ht.insert("apple", 5)
ht.insert("banana", 3)

print(ht.get("apple"))     # 5
print(ht.get_last())       # ('banana', 3)
print(ht.get_first())      # ('apple', 5)

ht.remove("apple")

try:
    ht.get("apple")
except KeyError:
    print("apple not found")
```

## Testing

Brief manual testing was conducted in `sandbox/hash_table.ipynb` to weakly verify correctness. Extensive testing can/should be conducted on full set of features:
- Basic inserts, updates, and removals
- Collision chains, tombstone reuse, wrap-around probes
- Saturation handling (full table)
- Recency list correctness
- Edge cases: empty table, all tombstones

## Note on Corpus Processing
A brief corpus exploration was conducted in `sandbox/corpus.ipynb` to verify that the source text was generally well-behaved.

Processing choices:
- Remove digits and punctuation (roman numerals not removed)
- Convert all text to lowercase
- Split hyphenated words into separate tokens
- Remove empty strings
- Sentence-structure tokens were not generated
- Typos present in the original text as well as those introduced by processing (e.g., linebreak artifacts) remain
- Stemming and lemmatization considered but not implemented for this exercise

See `sandbox/corpus.ipynb` for the full exploration and processing workflow.