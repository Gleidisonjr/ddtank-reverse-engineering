
const fs = require('fs');
const content = fs.readFileSync('targets/dd-classico/extracted/dumped/flash_scripts/player.js', 'utf8');

// Replace the final execution snT(2318) with console.log(RUD) or intercept Function/eval
const hooked = content.replace('var snT=iBJ(joP,RUD );snT(2318);', 'console.log("=== DEOBFUSCATED CODE ==="); console.log(RUD);');

eval(hooked);
