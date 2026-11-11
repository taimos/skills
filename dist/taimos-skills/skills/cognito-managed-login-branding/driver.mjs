#!/usr/bin/env node
// Validate Cognito Managed Login branding assets against AWS's accepted+enforced
// rules BEFORE `cdk deploy`, so you don't burn a 5-minute deploy on a 400 from
// AWS::Cognito::ManagedLoginBranding.
//
// Rule sources:
//  - AWS API (AssetType): categories, extensions, colorModes, base64 <= 1,000,000,
//    total request <= 2 MB.
//    https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_AssetType.html
//  - Server-enforced, UNDOCUMENTED, discovered from real deploy 400s:
//      * SVG assets may not carry `role` or `aria-*` attributes ("element
//        [svg#role|aria-label] is not allowed").
//      * LOGO-subtype assets must have width:height ratio between 1:1 and 4:1
//        ("Assets of SubType LOGO must have a width:height ratio between 1:1 and 4:1").
//
// Usage:
//   node driver.mjs <file> [--category CAT] [--color-mode MODE] ...
//   node driver.mjs --manifest assets.json     # [{file,category,colorMode,extension}]
//   node driver.mjs --self-test                # runs built-in good/bad fixtures
//
// Category defaults to inference from the filename when --category is omitted.
// Exit code 0 = all pass, 1 = at least one ERROR, 2 = bad invocation.

import { readFileSync, existsSync, mkdtempSync, writeFileSync } from 'node:fs';
import { basename, join } from 'node:path';
import { tmpdir } from 'node:os';

const CATEGORIES = new Set([
  'FAVICON_ICO', 'FAVICON_SVG', 'EMAIL_GRAPHIC', 'SMS_GRAPHIC', 'AUTH_APP_GRAPHIC',
  'PASSWORD_GRAPHIC', 'PASSKEY_GRAPHIC', 'PAGE_HEADER_LOGO', 'PAGE_HEADER_BACKGROUND',
  'PAGE_FOOTER_LOGO', 'PAGE_FOOTER_BACKGROUND', 'PAGE_BACKGROUND', 'FORM_BACKGROUND',
  'FORM_LOGO', 'IDP_BUTTON_ICON',
]);
const EXTENSIONS = new Set(['ICO', 'JPEG', 'PNG', 'SVG', 'WEBP']);
const COLOR_MODES = new Set(['LIGHT', 'DARK', 'DYNAMIC']);
// Categories AWS treats as "LOGO" subtype (ratio 1:1..4:1). FORM_LOGO is
// confirmed by a real 400; the two PAGE_*_LOGO are inferred as the same subtype.
const LOGO_CATEGORIES = new Set(['FORM_LOGO', 'PAGE_HEADER_LOGO', 'PAGE_FOOTER_LOGO']);
const FAVICON_CATEGORIES = new Set(['FAVICON_ICO', 'FAVICON_SVG']);
const MAX_BASE64_LEN = 1_000_000;   // per-asset, AWS AssetType.Bytes length constraint
const MAX_REQUEST_BYTES = 2_000_000; // whole CreateManagedLoginBranding request

function inferCategory(file) {
  const n = basename(file).toLowerCase();
  const ext = n.split('.').pop();
  if (n.includes('favicon')) return ext === 'ico' ? 'FAVICON_ICO' : 'FAVICON_SVG';
  if (n.includes('logo') || n.includes('lockup')) return 'FORM_LOGO';
  if (n.includes('background') || n.includes('bg')) return 'PAGE_BACKGROUND';
  return undefined;
}
function extFromFile(file) {
  const e = basename(file).split('.').pop().toUpperCase();
  return e === 'JPG' ? 'JPEG' : e;
}

// --- dimension readers -----------------------------------------------------
function svgDimensions(text) {
  const open = text.match(/<svg\b[^>]*>/i);
  if (!open) return undefined;
  const tag = open[0];
  const num = (s) => (s == null ? undefined : parseFloat(String(s).replace(/px$/i, '')));
  const w = num((tag.match(/\bwidth\s*=\s*"([^"]+)"/i) || [])[1]);
  const h = num((tag.match(/\bheight\s*=\s*"([^"]+)"/i) || [])[1]);
  if (Number.isFinite(w) && Number.isFinite(h) && w > 0 && h > 0) return { w, h, from: 'width/height' };
  const vb = (tag.match(/\bviewBox\s*=\s*"([^"]+)"/i) || [])[1];
  if (vb) {
    const p = vb.trim().split(/[\s,]+/).map(Number);
    if (p.length === 4 && p[2] > 0 && p[3] > 0) return { w: p[2], h: p[3], from: 'viewBox' };
  }
  return undefined;
}
function pngDimensions(buf) {
  // PNG signature + IHDR: width/height are big-endian uint32 at bytes 16 and 20.
  if (buf.length < 24 || buf.readUInt32BE(0) !== 0x89504e47) return undefined;
  return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20), from: 'IHDR' };
}

// --- one asset -------------------------------------------------------------
function validateAsset({ file, category, colorMode, extension }) {
  const errors = [];
  const warns = [];
  const info = [];

  if (!existsSync(file)) return { file, errors: [`file not found: ${file}`], warns, info };
  const buf = readFileSync(file);
  const b64len = buf.toString('base64').length;

  category = category || inferCategory(file);
  extension = (extension || extFromFile(file)).toUpperCase();

  if (!category) errors.push(`cannot infer category from filename; pass --category (one of ${[...CATEGORIES].join(', ')})`);
  else if (!CATEGORIES.has(category)) errors.push(`invalid category "${category}"`);
  if (!EXTENSIONS.has(extension)) errors.push(`invalid extension "${extension}" (allowed: ${[...EXTENSIONS].join(', ')})`);
  if (colorMode && !COLOR_MODES.has(colorMode)) errors.push(`invalid colorMode "${colorMode}" (allowed: ${[...COLOR_MODES].join(', ')})`);

  // category/extension coherence
  if (category === 'FAVICON_ICO' && extension !== 'ICO') errors.push('FAVICON_ICO requires extension ICO');
  if (category === 'FAVICON_SVG' && extension !== 'SVG') errors.push('FAVICON_SVG requires extension SVG');

  // size
  info.push(`base64 length ${b64len.toLocaleString()} / ${MAX_BASE64_LEN.toLocaleString()}`);
  if (b64len > MAX_BASE64_LEN) errors.push(`base64 length ${b64len} exceeds AWS max ${MAX_BASE64_LEN}`);

  // dimensions
  let dims;
  if (extension === 'SVG') dims = svgDimensions(buf.toString('utf8'));
  else if (extension === 'PNG') dims = pngDimensions(buf);

  if (dims) {
    const ratio = dims.w / dims.h;
    info.push(`dimensions ${dims.w}x${dims.h} (from ${dims.from}), ratio ${ratio.toFixed(3)}:1`);
    if (LOGO_CATEGORIES.has(category)) {
      if (ratio < 1 || ratio > 4) {
        errors.push(`LOGO ratio ${ratio.toFixed(3)}:1 outside AWS-enforced 1:1..4:1 (w=${dims.w}, h=${dims.h}). Pad the viewBox/canvas.`);
      }
    } else if (FAVICON_CATEGORIES.has(category)) {
      if (Math.abs(ratio - 1) > 0.05) warns.push(`favicon ratio ${ratio.toFixed(3)}:1 is not square; AWS expects ~1:1`);
    }
  } else if ((LOGO_CATEGORIES.has(category) || FAVICON_CATEGORIES.has(category)) && (extension === 'SVG' || extension === 'PNG')) {
    warns.push('could not determine dimensions (no width/height or viewBox on SVG root); ratio not checked');
  }

  // SVG content sanitization (server-enforced, undocumented)
  if (extension === 'SVG') {
    const svg = buf.toString('utf8');
    if (/\brole\s*=/.test(svg)) errors.push('SVG contains a `role` attribute — Cognito rejects it ("element [svg#role|aria-label] is not allowed"). Remove it.');
    if (/\baria-[a-z-]+\s*=/i.test(svg)) errors.push('SVG contains an `aria-*` attribute — Cognito rejects it. Remove it.');
    if (/<script[\s>]/i.test(svg)) errors.push('SVG contains a <script> element — not allowed.');
    if (/\son[a-z]+\s*=/i.test(svg)) errors.push('SVG contains an inline event handler (on*=) — not allowed.');
    if (/<foreignObject[\s>]/i.test(svg)) warns.push('SVG contains <foreignObject> — Cognito may reject it.');
    if (/(?:xlink:)?href\s*=\s*"(?:https?:)?\/\//i.test(svg)) warns.push('SVG references an external URL (href) — Cognito may reject or strip it.');
  }

  return { file, category, colorMode, extension, b64len, errors, warns, info };
}

// --- reporting -------------------------------------------------------------
function report(results) {
  let failed = 0;
  let total = 0;
  for (const r of results) {
    total += r.b64len || 0;
    const ok = r.errors.length === 0;
    if (!ok) failed++;
    const tag = ok ? (r.warns.length ? 'WARN ' : 'PASS ') : 'FAIL ';
    console.log(`${tag} ${r.file}  [${r.category || '?'} / ${r.colorMode || 'any'} / ${r.extension || '?'}]`);
    for (const i of r.info) console.log(`       · ${i}`);
    for (const w of r.warns) console.log(`       ! ${w}`);
    for (const e of r.errors) console.log(`       ✗ ${e}`);
  }
  console.log(`\nTotal base64 across ${results.length} asset(s): ${total.toLocaleString()} / request cap ~${MAX_REQUEST_BYTES.toLocaleString()}`);
  if (total > MAX_REQUEST_BYTES) console.log('✗ combined assets exceed the ~2 MB CreateManagedLoginBranding request limit');
  console.log(failed ? `\n${failed} asset(s) FAILED` : `\nAll ${results.length} asset(s) OK`);
  return failed === 0;
}

// --- self test -------------------------------------------------------------
function selfTest() {
  const dir = mkdtempSync(join(tmpdir(), 'cognito-branding-'));
  const bad = join(dir, 'bad-logo.svg');
  const good = join(dir, 'good-logo.svg');
  // 643x128 ~= 5:1 AND role/aria-label -> both real errors we hit.
  writeFileSync(bad, '<svg viewBox="0 0 643 128" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="X"><rect width="643" height="128"/></svg>');
  // 640x160 = 4:1, no forbidden attrs.
  writeFileSync(good, '<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg"><rect width="640" height="160"/></svg>');
  console.log('# self-test: a deliberately-bad FORM_LOGO (should FAIL with 3 errors)');
  const b = validateAsset({ file: bad, category: 'FORM_LOGO', colorMode: 'LIGHT' });
  report([b]);
  const gotRatio = b.errors.some((e) => e.includes('ratio'));
  const gotRole = b.errors.some((e) => e.includes('`role`'));
  const gotAria = b.errors.some((e) => e.includes('aria-'));
  console.log('\n# self-test: a valid FORM_LOGO (should PASS)');
  const g = validateAsset({ file: good, category: 'FORM_LOGO', colorMode: 'LIGHT' });
  report([g]);
  const pass = gotRatio && gotRole && gotAria && g.errors.length === 0;
  console.log(`\nself-test ${pass ? 'PASSED' : 'FAILED'} (bad→ratio:${gotRatio} role:${gotRole} aria:${gotAria}, good→clean:${g.errors.length === 0})`);
  return pass;
}

// --- argv ------------------------------------------------------------------
function main(argv) {
  const args = argv.slice(2);
  if (args.length === 0 || args.includes('-h') || args.includes('--help')) {
    console.log('usage: node driver.mjs <file> [--category CAT] [--color-mode MODE] [more files...]');
    console.log('       node driver.mjs --manifest assets.json');
    console.log('       node driver.mjs --self-test');
    return 2;
  }
  if (args.includes('--self-test')) return selfTest() ? 0 : 1;

  if (args[0] === '--manifest') {
    const manifest = JSON.parse(readFileSync(args[1], 'utf8'));
    const results = manifest.map((a) => validateAsset(a));
    return report(results) ? 0 : 1;
  }

  // positional files with optional --category/--color-mode that apply to the
  // file(s) that follow them.
  const results = [];
  let category, colorMode;
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === '--category') { category = args[++i]; continue; }
    if (a === '--color-mode') { colorMode = args[++i]; continue; }
    results.push(validateAsset({ file: a, category, colorMode }));
  }
  if (results.length === 0) { console.error('no files given'); return 2; }
  return report(results) ? 0 : 1;
}

process.exit(main(process.argv));
