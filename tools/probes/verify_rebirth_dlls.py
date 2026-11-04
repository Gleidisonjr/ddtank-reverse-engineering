import os, sys

rebirth_dir = os.path.abspath(r'targets/district-187/client-rebirth')

dlls = [f for f in os.listdir(rebirth_dir) if f.endswith('.dll')]
print(f"Total DLLs in root: {len(dlls)}")
for d in dlls:
    print(f"  {d} ({os.path.getsize(os.path.join(rebirth_dir, d))} bytes)")

game_dir = os.path.join(rebirth_dir, 'Game')
game_dlls = [f for f in os.listdir(game_dir) if f.endswith('.dll')]
print(f"Total DLLs in Game/: {len(game_dlls)}")
for d in game_dlls:
    print(f"  Game/{d} ({os.path.getsize(os.path.join(game_dir, d))} bytes)")
