const path = require('path');
const fs = require('fs');

console.log('process.execPath:', process.execPath);
console.log('process.version:', process.version);
console.log('process.versions.electron:', process.versions ? process.versions.electron : 'none');

const nodePath = path.resolve('targets/dd-classico/extracted/app/native/ddclassico_native.node');
try {
  const native = require(nodePath);
  console.log('Native module loaded successfully!');
  console.log('Exports:', Object.keys(native));
} catch (e) {
  console.error('Error loading native module:', e);
}
