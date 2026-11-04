import re

with open(r'targets\district-187\client\S2\Game\GameClient.dll', 'rb') as f:
    data = f.read()

# Find occurrences of LoginDevMode
for match in re.finditer(rb'LoginDevMode', data):
    start = max(0, match.start() - 1000)
    end = min(len(data), match.end() + 2000)
    chunk = data[start:end]
    # Extract strings from chunk
    strings = re.findall(rb'[\x20-\x7E]{3,}', chunk)
    print("Found LoginDevMode at offset:", hex(match.start()))
    print("Surrounding strings:")
    for s in strings:
        print(" ", s.decode('latin1'))
    print("-" * 50)
