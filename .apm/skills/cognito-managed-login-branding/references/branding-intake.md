# Branding intake — questions to author Cognito Managed Login assets

Use this when helping a user create branding assets from scratch or from a brand
guide. Ask what you can't already read from a supplied brand guide / style doc;
fill the rest from the guide. Convert every colour to a hex value.

## 1. Identity
- **Brand / product name** (the wordmark text): …
- **Icon glyph** — a single letter, monogram, or an existing icon SVG path? …
- Do you have an **existing logo file** (SVG/PNG/AI)? If yes, we validate/adapt it
  instead of using a template.

## 2. Colours (hex)
- **Accent / primary** (icon fill, buttons): `#…`
- **Foreground light mode** (ink on the light card): `#…` (default `#111827`)
- **Foreground dark mode** (ink on the dark card): `#…` (default `#F9FAFB`)
- **Card / form background** light / dark: `#…` / `#…`
- **Page background** light / dark: `#…` / `#…`

## 3. Scope — which assets are needed?
- [ ] `FORM_LOGO` (almost always) — light + dark
- [ ] `FAVICON_SVG` (+ optional `FAVICON_ICO` raster fallback)
- [ ] `PAGE_HEADER_LOGO` / `PAGE_FOOTER_LOGO`
- [ ] Backgrounds (`PAGE_BACKGROUND` / `FORM_BACKGROUND`)
- [ ] `IDP_BUTTON_ICON` (only if you show federated sign-in buttons)
- Dark mode required? (yes → produce DARK variants of every logo/background)

## 4. Logo composition
- Layout: **icon + wordmark** / wordmark-only / icon-only?
- Approx. wordmark length (chars) — drives the logo viewBox width so the ratio
  stays ≤ 4:1.

## From answers → assets

1. Start from [svg-templates/form-logo.svg](svg-templates/form-logo.svg) and
   [svg-templates/favicon.svg](svg-templates/favicon.svg).
2. Substitute `{{BRAND}}`, `{{INITIAL}}`, `{{ACCENT}}`, `{{FG}}`.
3. Duplicate the logo for LIGHT and DARK, swapping `{{FG}}` (and accent if it
   differs per mode). Name them e.g. `logo-light.svg` / `logo-dark.svg`.
4. Keep each logo's viewBox ratio in **1:1–4:1**; widen the viewBox width for a
   long wordmark, or pad height to reduce the ratio.
5. Validate every file with `driver.mjs` (see SKILL.md) — do not deploy until it
   passes.
6. Map colours into the branding `settings` object (form/page background,
   button colours) and list the files in the `assets` array with the right
   `category` / `colorMode` / `extension`. See [asset-catalog.md](asset-catalog.md).
