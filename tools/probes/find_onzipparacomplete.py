from find_hashead_idx import abc_data, read_u30
from decompile_loading_all import disasm

idx = abc_data.find(b'__onZipParaComplete')
print('__onZipParaComplete in abc_data at', idx)

# Let's search where __onZipParaComplete method body is
# pushstring / multiname search
