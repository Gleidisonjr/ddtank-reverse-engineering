import struct
from find_hashead_idx import abc_data, read_u30, hashead_str_idx

p = 4
int_count, p = read_u30(abc_data, p)
for _ in range(1, int_count): _, p = read_u30(abc_data, p)
uint_count, p = read_u30(abc_data, p)
for _ in range(1, uint_count): _, p = read_u30(abc_data, p)
double_count, p = read_u30(abc_data, p)
if double_count > 0: p += (double_count - 1) * 8
string_count, p = read_u30(abc_data, p)
for _ in range(1, string_count):
    slen, p = read_u30(abc_data, p)
    p += slen

namespace_count, p = read_u30(abc_data, p)
namespaces = [None]
for _ in range(1, namespace_count):
    kind = abc_data[p]; p += 1
    name_idx, p = read_u30(abc_data, p)
    namespaces.append((kind, name_idx))

ns_set_count, p = read_u30(abc_data, p)
for _ in range(1, ns_set_count):
    count, p = read_u30(abc_data, p)
    for _ in range(count): _, p = read_u30(abc_data, p)

multiname_count, p = read_u30(abc_data, p)
hashead_mn_indices = []
for mn_idx in range(1, multiname_count):
    kind = abc_data[p]; p += 1
    if kind in (0x07, 0x0D):
        ns, p = read_u30(abc_data, p)
        name, p = read_u30(abc_data, p)
        if name == hashead_str_idx:
            hashead_mn_indices.append(mn_idx)
    elif kind in (0x09, 0x0E):
        name, p = read_u30(abc_data, p)
        ns_set, p = read_u30(abc_data, p)
        if name == hashead_str_idx:
            hashead_mn_indices.append(mn_idx)
    elif kind in (0x1B, 0x1C):
        ns_set, p = read_u30(abc_data, p)
    elif kind in (0x17,):
        p += 2

print(f"Multiname indices for hasHead: {hashead_mn_indices}")
