import re

for filepath in [r'targets\district-187\client\S2\TheRaw.exe', r'targets\district-187\client\S2\Game\GameClient.dll', r'targets\district-187\client\S2\Game\GameServer.dll']:
    with open(filepath, 'rb') as f:
        data = f.read()
    print('='*50)
    print(filepath)
    # Match +word or -word
    matches = set(re.findall(rb'[+-][a-zA-Z_][a-zA-Z0-9_]{2,30}', data))
    sorted_matches = sorted([m.decode('latin1') for m in matches])
    print('Clean options count:', len(sorted_matches))
    print(', '.join(sorted_matches))
