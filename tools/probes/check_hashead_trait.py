from find_hashead_idx import abc_data, read_u30

# In methods, let's find the method trait for hasHead
pos = abc_data.find(b'hasHead')
# Let's inspect bytes around 38337
print(abc_data[38300:38400])
