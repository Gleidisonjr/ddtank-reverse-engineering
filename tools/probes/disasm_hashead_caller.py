from find_hashead_idx import abc_data, read_u30
from decompile_loading_all import disasm

# Let's inspect bytes from 285380 to 285500
code = abc_data[285380:285500]
for l in disasm(code):
    print(l)
