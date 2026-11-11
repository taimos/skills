# Cognito Managed Login — asset catalog

Every asset category from the AWS
[AssetType](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_AssetType.html)
API, what it's for, and the specs to author against. **Enforced** = AWS returns a
400 at deploy if violated (some undocumented — see the validator). **Recommended**
= safe design guidance, not enforced.

| Category | What it is | Subtype / ratio | Recommended source | Color modes |
|----------|-----------|-----------------|--------------------|-------------|
| `FORM_LOGO` | Logo inside the sign-in card | LOGO — ratio **1:1–4:1** (enforced) | SVG or PNG, ~600×200 | LIGHT + DARK |
| `PAGE_HEADER_LOGO` | Logo in the page header bar | LOGO — ratio 1:1–4:1 (apply same) | SVG/PNG, ~600×200 | LIGHT + DARK |
| `PAGE_FOOTER_LOGO` | Logo in the page footer | LOGO — ratio 1:1–4:1 (apply same) | SVG/PNG | LIGHT + DARK |
| `FAVICON_SVG` | Browser-tab icon (vector) | FAVICON — **square 1:1** | SVG, 64×64 viewBox | DYNAMIC |
| `FAVICON_ICO` | Browser-tab icon (raster fallback) | FAVICON — square | ICO (16/32/48 px) | DYNAMIC |
| `IDP_BUTTON_ICON` | Icon on a federated IdP button | ICON — square-ish | SVG/PNG, ~48×48 | LIGHT + DARK |
| `PAGE_BACKGROUND` | Full-page background | BACKGROUND — wide | PNG/WEBP/JPEG, large | LIGHT + DARK |
| `FORM_BACKGROUND` | Background of the sign-in card | BACKGROUND | PNG/WEBP/JPEG | LIGHT + DARK |
| `PAGE_HEADER_BACKGROUND` | Header bar background | BACKGROUND | PNG/WEBP/JPEG | LIGHT + DARK |
| `PAGE_FOOTER_BACKGROUND` | Footer bar background | BACKGROUND | PNG/WEBP/JPEG | LIGHT + DARK |
| `EMAIL_GRAPHIC` | Header graphic in emails | graphic | PNG | LIGHT/DYNAMIC |
| `SMS_GRAPHIC` | Graphic for SMS-related screens | graphic | PNG/SVG | LIGHT/DYNAMIC |
| `AUTH_APP_GRAPHIC` | TOTP authenticator-app screen | graphic | PNG/SVG | LIGHT/DYNAMIC |
| `PASSWORD_GRAPHIC` | Password screen illustration | graphic | PNG/SVG | LIGHT/DYNAMIC |
| `PASSKEY_GRAPHIC` | Passkey screen illustration | graphic | PNG/SVG | LIGHT/DYNAMIC |

## Hard limits (all categories)

- **Extensions:** `ICO JPEG PNG SVG WEBP`. `FAVICON_ICO`→`ICO`, `FAVICON_SVG`→`SVG`.
- **Per-asset size:** base64 ≤ 1,000,000 chars (~750 KB binary).
- **Whole request:** CSS settings + all assets ≤ ~2 MB.
- **Color modes:** `LIGHT` / `DARK` / `DYNAMIC`. Provide LIGHT **and** DARK for
  logos/backgrounds so the page looks right in both themes; `DYNAMIC` for a mark
  that works unchanged in both (favicons).

## SVG rules (Cognito sanitizes SVGs — undocumented, enforced)

- **No `role` and no `aria-*` attributes** on any element (they cause
  `element [svg#role|aria-label] is not allowed`).
- No `<script>`, no inline event handlers (`on*=`).
- Avoid `<foreignObject>` and external `href`/`xlink:href` references.
- Dimensions are read from `width`/`height`, or the `viewBox` when those are
  absent — so a viewBox-only logo is measured by its viewBox ratio.

## Design guidance

- Logos: give the wordmark horizontal breathing room; target ratio ~3:1 (safely
  inside 1:1–4:1). If it's too wide, pad the viewBox **height** rather than
  cropping — keeps artwork centred and undistorted.
- Prefer SVG for logos/favicons: crisp at any DPI and tiny. Use PNG/WEBP only
  for photographic backgrounds.
- Keep contrast: LIGHT-mode assets sit on a light card (dark ink); DARK-mode
  assets on a dark card (near-white ink).
