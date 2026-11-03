import struct, capstone

with open(r'targets/district-187/client-rebirth/Game/GameClient.dll', 'rb') as f:
    dll = f.read()

# Let's search for packet header parsing in GameClient.dll
# Earlier we saw in CGameServerConnectMgr::Connecting() at 0x100529b8:
# mov ecx, eax
# call edx (NetClient::Connect)
# Where is NetClient defined?
# In CGameServerConnectMgr, let's see what is at [eax] (NetClient vtable)
# At 0x100529a2: mov edx, [eax + 0x188] -> call edx
# Let's inspect NetClient methods around 0x100529a0!

import re
matches = set(re.findall(rb'[a-zA-Z0-9_]*Packet[a-zA-Z0-9_]*', dll))
print("Packet symbols in GameClient.dll:")
for m in sorted(matches):
    if len(m) < 40 and not m.startswith(b'__'):
        print(' ', m.decode('latin1'))
