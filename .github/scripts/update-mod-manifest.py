import hashlib
import json
import os
import re
import sys
import tomllib
import zipfile
from pathlib import Path
from urllib.parse import quote


def update(root):
    manifest_path = root / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    previous = {mod['file']: mod for mod in manifest.get('mods', [])}
    mods = []
    seen = set()
    for jar in sorted((root / 'mods').glob('*.jar')):
        contents = jar.read_bytes()
        sha256 = hashlib.sha256(contents).hexdigest()
        old = previous.get(jar.name, {})
        with zipfile.ZipFile(jar) as archive:
            names = set(archive.namelist())
            metadata_path = next((name for name in ['META-INF/neoforge.mods.toml', 'META-INF/mods.toml'] if name in names), None)
            metadata = tomllib.loads(archive.read(metadata_path).decode('utf-8-sig')) if metadata_path else {}
            declaration = next(iter(metadata.get('mods', [])), {})
            mod_id = declaration.get('modId') or old.get('modId') or old.get('id')
            version = declaration.get('version') or old.get('version')
            if version and '${' in version:
                jar_manifest = archive.read('META-INF/MANIFEST.MF').decode('utf-8')
                match = re.search(r'^Implementation-Version:\s*(.+)$', jar_manifest, re.MULTILINE)
                version = match.group(1).strip() if match else None
            if not mod_id or not version:
                raise ValueError(f'Cannot identify mod ID/version: {jar.name}')
            unique_id = mod_id if mod_id not in seen else f'{mod_id}__{sha256[:12]}'
            seen.add(unique_id)
            mod = {**old, 'id': unique_id, 'name': declaration.get('displayName') or old.get('name') or mod_id,
                   'version': str(version), 'file': jar.name,
                   'url': f'https://raw.githubusercontent.com/Clonelis/TerraDivina-Modpack/main/mods/{quote(jar.name, safe="")}',
                   'sha256': sha256}
            revision = os.environ.get('GITHUB_SHA', '')
            pinned_url = old.get('url', '')
            if old.get('sha256') == sha256 and re.fullmatch(r'https://raw\.githubusercontent\.com/Clonelis/TerraDivina-Modpack/[a-f0-9]{40}/mods/[^?]+', pinned_url):
                mod['url'] = pinned_url
            elif re.fullmatch(r'[a-f0-9]{40}', revision):
                mod['url'] = f'https://raw.githubusercontent.com/Clonelis/TerraDivina-Modpack/{revision}/mods/{quote(jar.name, safe="")}'
            else:
                mod['url'] += f'?sha256={sha256}'
            if unique_id != mod_id:
                mod['modId'] = mod_id
            else:
                mod.pop('modId', None)
            if not declaration:
                mod['library'] = True
            website = declaration.get('displayURL') or metadata.get('displayURL')
            if not mod.get('pageUrl') and isinstance(website, str) and website.startswith('https://'):
                mod['pageUrl'] = website
            logo = declaration.get('logoFile')
            if logo and logo in names and not mod.get('iconUrl'):
                extension = Path(logo).suffix.lower()
                if extension in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                    icon_name = unique_id + extension
                    (root / 'icons').mkdir(exist_ok=True)
                    (root / 'icons' / icon_name).write_bytes(archive.read(logo))
                    mod['iconUrl'] = f'https://raw.githubusercontent.com/Clonelis/TerraDivina-Modpack/main/icons/{quote(icon_name)}'
            mods.append(mod)
    manifest['mods'] = mods
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Manifest updated: {len(mods)} JAR files')


if __name__ == '__main__':
    update(Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[2])
