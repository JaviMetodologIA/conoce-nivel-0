import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
const dist = path.join(root, 'dist');
const spec = JSON.parse(fs.readFileSync(path.join(root, 'src/intrapage-navigation-spec-v1.json'), 'utf8'));

function walk(dir) {
  return fs.readdirSync(dir, {withFileTypes: true}).flatMap((entry) => {
    const target = path.join(dir, entry.name);
    return entry.isDirectory() ? walk(target) : [target];
  });
}

function occurrences(source, fragment) {
  return source.split(fragment).length - 1;
}

const pages = walk(dist).filter((file) => file.endsWith('.html'));
if (pages.length !== 54) throw new Error(`Expected 54 HTML pages, found ${pages.length}`);

for (const file of pages) {
  const html = fs.readFileSync(file, 'utf8');
  const page = html.match(/<body data-page="([^"]+)"/)?.[1];
  if (!page || !spec.pages[page]) throw new Error(`Unknown page type: ${file}`);
  if (occurrences(html, 'data-intrapage-nav') !== 1) throw new Error(`Sidebar count drift: ${file}`);
  if (occurrences(html, 'data-intrapage-open') !== 1) throw new Error(`Trigger count drift: ${file}`);
  const expected = spec.pages[page].items.map((item) => item.anchor);
  const nav = html.match(/<aside class="intrapage-nav"[\s\S]*?<\/aside>/)?.[0] ?? '';
  const rendered = [...nav.matchAll(/href="#([^"]+)" data-intrapage-link/g)].map((match) => match[1]);
  if (JSON.stringify(rendered) !== JSON.stringify(expected)) throw new Error(`Sidebar order drift: ${file}`);
  for (const anchor of expected) {
    if (occurrences(html, `id="${anchor}"`) !== 1) throw new Error(`Target count drift (${anchor}): ${file}`);
  }
  if (occurrences(html, '<link rel="canonical"') !== 1) throw new Error(`Canonical drift: ${file}`);
  if (page === 'playbook') {
    const complete = html.match(/<details class="playbook-toc">[\s\S]*?<\/details>/)?.[0] ?? '';
    if (occurrences(complete, '<a href="#') !== 22) throw new Error(`Playbook complete index drift: ${file}`);
  }
}

const manifest = JSON.parse(fs.readFileSync(path.join(dist, 'build-manifest.json'), 'utf8'));
const receipt = JSON.parse(fs.readFileSync(path.join(dist, 'build-receipt.json'), 'utf8'));
if (manifest.state !== 'RENDERED_DRAFT' || receipt.state !== 'RENDERED_DRAFT') throw new Error('State escalation detected');
if (manifest.intrapage_navigation?.rendered_pages !== 54) throw new Error('Manifest navigation binding missing');
if (receipt.intrapage_navigation?.source_sha256 !== manifest.intrapage_navigation.source_sha256) throw new Error('Receipt navigation binding drift');

console.log('INTRAPAGE_NAVIGATION_OK 54/54');
