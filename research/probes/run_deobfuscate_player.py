with open(r'targets\dd-classico\extracted\dumped\flash_scripts\player.js', 'r', encoding='utf-8') as f:
    code = f.read()

# Let's extract xYp and execute in Node.js to get the decoded string!
import subprocess

js_code = """
const fs = require('fs');
const content = fs.readFileSync('targets/dd-classico/extracted/dumped/flash_scripts/player.js', 'utf8');

// Replace the final execution snT(2318) with console.log(RUD) or intercept Function/eval
const hooked = content.replace('var snT=iBJ(joP,RUD );snT(2318);', 'console.log("=== DEOBFUSCATED CODE ==="); console.log(RUD);');

eval(hooked);
"""

with open('scripts/probes/deobfuscate_player.js', 'w', encoding='utf-8') as f:
    f.write(js_code)

res = subprocess.run(['node', 'scripts/probes/deobfuscate_player.js'], capture_output=True, text=True)
print('STDOUT:')
print(res.stdout[:1500])
print('STDERR:', res.stderr)

if '=== DEOBFUSCATED CODE ===' in res.stdout:
    deob = res.stdout.split('=== DEOBFUSCATED CODE ===')[1].strip()
    with open(r'targets\dd-classico\extracted\dumped\flash_scripts\player_deobfuscated.js', 'w', encoding='utf-8') as f:
        f.write(deob)
    print(f'Saved player_deobfuscated.js ({len(deob)} chars)!')
