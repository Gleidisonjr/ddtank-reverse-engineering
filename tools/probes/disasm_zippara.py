from find_hashead_idx import abc_data, read_u30
from decompile_loading_all import disasm

code = abc_data[284970:285450]
for l in disasm(code):
    print(l)
