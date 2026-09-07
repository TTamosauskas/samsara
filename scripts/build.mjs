import { promises as fs } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const sourceDir = path.join(root, 'src', 'js');
const dist = path.join(root, 'dist');

await fs.rm(dist, { recursive: true, force: true });
await fs.mkdir(path.join(dist, 'assets', 'js'), { recursive: true });
await fs.mkdir(path.join(dist, 'assets', 'css'), { recursive: true });
await fs.mkdir(path.join(dist, 'assets', 'img'), { recursive: true });

const parts = (await fs.readdir(sourceDir))
  .filter(name => name.endsWith('.part.js'))
  .sort((a, b) => a.localeCompare(b, 'en'));
if (!parts.length) throw new Error('Nenhum fragmento JavaScript encontrado.');

const contents = [];
for (const part of parts) contents.push(await fs.readFile(path.join(sourceDir, part), 'utf8'));
const bundle = `/* Samsara — bundle gerado. Edite src/js/*.part.js, não este arquivo. */\n(async() => {\n  'use strict';\n${contents.join('\n')}\n})();\n`;
await fs.writeFile(path.join(dist, 'assets', 'js', 'app.js'), bundle);
await fs.copyFile(path.join(root, 'index.html'), path.join(dist, 'index.html'));
await fs.copyFile(path.join(root, 'assets', 'css', 'styles.css'), path.join(dist, 'assets', 'css', 'styles.css'));
for (const name of await fs.readdir(path.join(root, 'assets', 'img'))) {
  await fs.copyFile(path.join(root, 'assets', 'img', name), path.join(dist, 'assets', 'img', name));
}
console.log(`Samsara build: ${parts.length} fragmentos -> dist/assets/js/app.js`);
