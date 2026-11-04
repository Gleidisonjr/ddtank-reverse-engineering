import sys; sys.path.insert(0, 'scripts/probes')
from find_hashead_idx import abc_data, read_u30
from decompile_loading_all import disasm

# Find string index of __onZipParaComplete
p = 4
int_count, p = read_u30(abc_data, p)
for _ in range(1, int_count): _, p = read_u30(abc_data, p)
uint_count, p = read_u30(abc_data, p)
for _ in range(1, uint_count): _, p = read_u30(abc_data, p)
double_count, p = read_u30(abc_data, p)
if double_count > 0: p += (double_count - 1) * 8
string_count, p = read_u30(abc_data, p)
strings = ['']
target_sidx = None
for sidx in range(1, string_count):
    slen, p = read_u30(abc_data, p)
    s = abc_data[p:p+slen].decode('utf-8', errors='ignore')
    p += slen
    strings.append(s)
    if s == '__onZipParaComplete':
        target_sidx = sidx

print('target_sidx:', target_sidx)

# Find multiname for target_sidx
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
target_mns = []
for mn_idx in range(1, multiname_count):
    kind = abc_data[p]; p += 1
    if kind in (0x07, 0x0D):
        ns, p = read_u30(abc_data, p)
        name, p = read_u30(abc_data, p)
        if name == target_sidx: target_mns.append(mn_idx)
    elif kind in (0x09, 0x0E):
        name, p = read_u30(abc_data, p)
        ns_set, p = read_u30(abc_data, p)
        if name == target_sidx: target_mns.append(mn_idx)
    elif kind in (0x1B, 0x1C):
        ns_set, p = read_u30(abc_data, p)
    elif kind in (0x17,): p += 2

print('target_mns:', target_mns)

# Now find method trait
# Search in abc_data for target_mns
for mn in target_mns:
    # search trait with tname = mn
    needle = bytes([mn & 0x7F, (mn >> 7) & 0x7F]) if mn >= 128 else bytes([mn])
    pos = 0
    while True:
        pos = abc_data.find(needle, pos)
        if pos == -1: break
        # check if preceded by trait kind
        print(f'Match for mn {mn} at {pos}')
        pos += 1
