import { createHash } from 'node:crypto';
import { readdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const repository = 'Clonelis/TerraDivina-Modpack';
const branch = 'main';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const configRoot = path.join(root, 'config');
const manifestPath = path.join(root, 'manifest.json');

async function collect(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) files.push(...await collect(target));
    if (entry.isFile() && entry.name !== '.gitkeep') files.push(target);
  }
  return files;
}

const manifest = JSON.parse(await readFile(manifestPath, 'utf8'));
const previous = new Map((manifest.configFiles || []).map(file => [file.path, file]));
const files = await collect(configRoot);
manifest.configFiles = await Promise.all(files.sort().map(async file => {
  const relative = path.relative(root, file).replaceAll('\\', '/');
  const encoded = relative.split('/').map(encodeURIComponent).join('/');
  const contents = await readFile(file);
  return {
    path: relative,
    url: `https://raw.githubusercontent.com/${repository}/${branch}/${encoded}`,
    sha256: createHash('sha256').update(contents).digest('hex'),
    overwrite: previous.get(relative)?.overwrite !== false
  };
}));
await writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
