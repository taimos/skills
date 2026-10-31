---
name: cognito-managed-login-branding
description: >-
  Create, validate, and fix Amazon Cognito Managed Login branding assets
  (FORM_LOGO, FAVICON, page/background logos; SVG/PNG/ICO). Authors new logos and
  favicons from a brand guide or an interactive chat using Cognito-safe templates,
  and validates them BEFORE `cdk deploy` — catching the server-enforced rules
  CfnManagedLoginBranding fails on (SVG `role`/`aria-*` attributes, the LOGO
  1:1–4:1 aspect-ratio limit) plus the documented category/extension/size limits.
  Use when creating or changing a Cognito login logo/favicon, building branding
  from a style guide, or when a ManagedLoginBranding deploy returns
  "Invalid assets provided".
---

# Cognito Managed Login branding validator

`AWS::Cognito::ManagedLoginBranding` validates uploaded assets **server-side at
deploy time** and returns a generic 400 (`Invalid assets provided`) that fails
the whole CloudFormation stack after a multi-minute deploy. Several of the rules
are **not in the AWS docs** — they were reverse-engineered from real 400s. This
skill's driver checks assets locally in <1s so you catch them before deploying.

Driver: [driver.mjs](driver.mjs) (Node, no dependencies). The `driver.mjs` and
`references/` paths below are relative to this skill directory; asset paths (e.g.
`src/brand/…`) are relative to your **repo root**.

## Prerequisites

Node 18+ (this repo used v26). No install, no packages:

```bash
node --version
```

## Create branding assets (from a brand guide or interactively)

When the user needs new logos/favicons — from a supplied brand guide or by
chatting it through — author them from the Cognito-safe templates, then validate.

1. **Gather inputs.** Walk the user through
   [references/branding-intake.md](references/branding-intake.md) (skip anything a
   supplied brand guide already answers). You mainly need: brand/wordmark text,
   an icon glyph, accent colour, and light/dark foreground colours — all as hex.
2. **Pick categories.** See [references/asset-catalog.md](references/asset-catalog.md)
   for every category, its enforced ratio/extension, and which color modes to ship.
   Almost every pool needs `FORM_LOGO` (LIGHT + DARK) and a favicon.
3. **Instantiate the templates.** Start from
   [references/svg-templates/form-logo.svg](references/svg-templates/form-logo.svg)
   and [references/svg-templates/favicon.svg](references/svg-templates/favicon.svg)
   (both are pre-validated: no `role`/`aria`, ratios inside the limits). Substitute
   the placeholders and produce a LIGHT and a DARK logo variant. Example:

   ```bash
   TPL=references/svg-templates
   mkdir -p /tmp/brand-out
   sed -e 's/{{ACCENT}}/#4F46E5/g' -e 's/{{FG}}/#111827/g' -e 's/{{INITIAL}}/A/g' -e 's/{{BRAND}}/Acme/g' \
     "$TPL/form-logo.svg" > /tmp/brand-out/logo-light.svg
   sed -e 's/{{ACCENT}}/#4F46E5/g' -e 's/{{FG}}/#F9FAFB/g' -e 's/{{INITIAL}}/A/g' -e 's/{{BRAND}}/Acme/g' \
     "$TPL/form-logo.svg" > /tmp/brand-out/logo-dark.svg
   sed -e 's/{{ACCENT}}/#4F46E5/g' -e 's/{{FG}}/#F9FAFB/g' -e 's/{{INITIAL}}/A/g' \
     "$TPL/favicon.svg" > /tmp/brand-out/favicon.svg
   ```

   (For a real logo file the user already has, skip the template and validate their
   file directly.)
4. **Validate before wiring in** — the templates keep the ratio safe, but any hand
   edit can break it, so always re-run the driver:

   ```bash
   node driver.mjs \
     --category FORM_LOGO --color-mode LIGHT /tmp/brand-out/logo-light.svg \
     --color-mode DARK /tmp/brand-out/logo-dark.svg \
     --category FAVICON_SVG --color-mode DYNAMIC /tmp/brand-out/favicon.svg
   ```
5. **Wire into the stack.** Copy the passing files into your app's brand dir
   (e.g. `src/brand/`) and list them in the
   `CfnManagedLoginBranding` `assets` array with matching
   `category`/`colorMode`/`extension`. For the page colours/buttons/layout, start
   from [references/branding-settings.example.json](references/branding-settings.example.json)
   (a complete, brand-neutral `settings` object) — recolour it and pass it as
   `settings`. Colours there are `RRGGBBAA` hex **without** `#` (e.g. `#4F46E5`
   → `4f46e5ff`); see [references/branding-settings.md](references/branding-settings.md)
   for the format and which knobs map to which intake colour. Then deploy.

## Run (agent path) — validate before you deploy

**Always start with the self-test** — it builds a deliberately-bad FORM_LOGO and
proves the driver still catches the two undocumented rules (ratio + `role`/`aria`):

```bash
node driver.mjs --self-test
```

Expected tail: `self-test PASSED (bad→ratio:true role:true aria:true, good→clean:true)`.

**Validate specific assets.** Flags (`--category`, `--color-mode`) apply to the
files that follow and are sticky until changed, so put them *before* the file:

```bash
node driver.mjs \
  --category FORM_LOGO --color-mode DARK  src/brand/logo-horizontal-dark.svg \
                       --color-mode LIGHT src/brand/logo-horizontal-light.svg \
  --category FAVICON_SVG --color-mode DYNAMIC src/brand/favicon.svg \
  --category FAVICON_ICO src/brand/favicon.ico
```

Exit code is `0` when every asset passes, `1` if any asset has an ERROR. Each
asset prints its detected dimensions, ratio, and base64 length.

**Manifest mode** (mirror the exact `assets:` array you pass to
`CfnManagedLoginBranding` — best for CI):

```bash
cat > /tmp/branding-assets.json <<'JSON'
[
  { "file": "src/brand/logo-horizontal-dark.svg",  "category": "FORM_LOGO",   "colorMode": "DARK",    "extension": "SVG" },
  { "file": "src/brand/logo-horizontal-light.svg", "category": "FORM_LOGO",   "colorMode": "LIGHT",   "extension": "SVG" },
  { "file": "src/brand/favicon.svg",               "category": "FAVICON_SVG", "colorMode": "DYNAMIC", "extension": "SVG" },
  { "file": "src/brand/favicon.ico",               "category": "FAVICON_ICO", "colorMode": "DYNAMIC", "extension": "ICO" }
]
JSON
node driver.mjs --manifest /tmp/branding-assets.json
```

Keep the branding assets in one directory (e.g. `src/brand/`) and wire them into
`CfnManagedLoginBranding` via its `assets` array in your stack. Keep the
manifest's `category`/`colorMode`/`extension` in sync with that array.

## Rules the driver enforces

Documented (AWS [AssetType](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_AssetType.html)):

| Field | Allowed |
|-------|---------|
| Category | `FAVICON_ICO FAVICON_SVG EMAIL_GRAPHIC SMS_GRAPHIC AUTH_APP_GRAPHIC PASSWORD_GRAPHIC PASSKEY_GRAPHIC PAGE_HEADER_LOGO PAGE_HEADER_BACKGROUND PAGE_FOOTER_LOGO PAGE_FOOTER_BACKGROUND PAGE_BACKGROUND FORM_BACKGROUND FORM_LOGO IDP_BUTTON_ICON` |
| ColorMode | `LIGHT DARK DYNAMIC` |
| Extension | `ICO JPEG PNG SVG WEBP` |
| Bytes (base64) | ≤ 1,000,000 per asset; whole request ≤ ~2 MB |

Undocumented, **server-enforced** (discovered from real deploy 400s):

- **SVG assets must not carry `role` or `aria-*` attributes.** Cognito's SVG
  sanitizer rejects them: `element [svg#role|aria-label] is not allowed`.
- **LOGO-subtype assets need a width:height ratio between 1:1 and 4:1.**
  Confirmed for `FORM_LOGO` (`Assets of SubType LOGO must have a width:height
  ratio between 1:1 and 4:1`); the driver applies it to `PAGE_HEADER_LOGO` and
  `PAGE_FOOTER_LOGO` too. Dimensions come from the SVG `width`/`height` attrs, or
  the `viewBox` when those are absent — which is exactly how Cognito measures them.

## Fixing the two common failures

**`role`/`aria-*` on an SVG** — strip them from the root `<svg>` (they're
decorative-only for Cognito):

```bash
perl -0pi -e 's/ role="img" aria-label="[^"]*"//' src/brand/logo-horizontal-dark.svg
```

**Ratio > 4:1** — pad the `viewBox` height (adds transparent margin, no
distortion, keeps artwork centered). Compute the padded viewBox first:

```bash
python3 -c "
W=642.7; minY=-93.1; H0=127.9; H=165.0   # target height -> ratio W/H
pad=(H-H0)/2; print('viewBox=\"-6.0 %.2f %s %s\"  ratio=%.3f' % (minY-pad, W, H, W/H))"
```

Then set that `viewBox` on the root `<svg>` and re-run the driver until it PASSes.

## Gotchas

- **The ratio and `role`/`aria` rules are NOT in AWS docs.** The only public
  source is the deploy error string. Don't expect to find them in the API
  reference — the driver encodes what AWS actually enforces.
- **Ratio is measured from `viewBox` when the SVG has no `width`/`height`.** A
  lockup with only a `viewBox` of `… 642.7 127.9` gets measured by Cognito as
  `width: 643.0; height: 128.0`. Padding the viewBox height is what fixes it.
- **`Bytes` is a base64-length limit (1,000,000), not raw bytes** (~750 KB of
  binary). The driver reports base64 length, not file size.
- **Flag ordering is sticky and forward-applying.** `--category X file` sets X
  for `file` and everything after it until the next `--category`. Putting the
  flag *after* the file applies it to the *next* file — a mislabel, not an error.
- **`FAVICON_ICO` requires extension `ICO`, `FAVICON_SVG` requires `SVG`.** The
  driver errors on a mismatch; other categories accept any allowed extension.
- The driver reads PNG dimensions from the IHDR chunk; ICO dimensions aren't
  parsed (only extension/size are checked for ICO).

## Troubleshooting

| Deploy error | Cause | Fix |
|--------------|-------|-----|
| `element [svg#role\|aria-label] is not allowed` | `role`/`aria-*` on an SVG | strip the attributes (see above), re-run driver |
| `Assets of SubType LOGO must have a width:height ratio between 1:1 and 4:1` | logo too wide/tall | pad the viewBox to ratio ≤ 4:1 (see above) |
| `Invalid assets provided` with no detail | usually one of the above, batched per colorMode | run the driver over every asset to localize it |
