# Branding `settings` (the "brand.json") reference

`CfnManagedLoginBranding` takes two inputs: the **`assets`** array (logos/favicons —
covered by the templates + validator) and the **`settings`** object — the colours,
buttons, backgrounds, and layout of the login pages. This is the "brand.json".

A complete, brand-neutral starting point is
[branding-settings.example.json](branding-settings.example.json). Copy it, recolour
it to the brand, and pass it as `settings`.

## Colour format

Colours are **8-digit `RRGGBBAA` hex strings, no `#`** — e.g. `4f46e5ff`
(opaque indigo), `ffffffff` (opaque white). The trailing `ff` is alpha. This is
**not** the `#RRGGBB` you use in CSS or in the SVG assets, so convert:
`#4F46E5` → `4f46e5ff`.

## Top-level shape

```
{
  "components":       { ... per-component colours & layout (light/dark modes) ... },
  "componentClasses": { ... shared classes: input, buttons, links, idpButtons ... },
  "categories":       { form, auth, global, signUp }
}
```

## Knobs you'll usually change (map from the intake colours)

| Path | Meaning | Intake colour |
|------|---------|---------------|
| `components.form.lightMode.backgroundColor` / `darkMode` | sign-in card fill | card background |
| `components.form.borderRadius` | card corner radius | — |
| `components.form.logo.enabled` / `.position` / `.location` | show the `FORM_LOGO`, where | — |
| `components.pageBackground.lightMode.color` / `darkMode` | page background | page background |
| `components.pageText.lightMode.headingColor` / `bodyColor` | text ink | foreground |
| `components.primaryButton.lightMode.defaults.backgroundColor` / `textColor` | primary CTA | accent |
| `components.secondaryButton.*` | secondary button | accent / neutral |
| `components.favicon.enabledTypes` | which favicon assets to use (`["ICO","SVG"]`) | — |

Modes: every component has `lightMode` and `darkMode` — set both so the page
looks right in either theme.

## Getting a full, current document

The example here is a trimmed, recoloured copy. Cognito's schema evolves, so the
authoritative way to get a complete document is to design once in the Cognito
console (Managed login → branding designer) and export it:

```
aws cognito-idp describe-managed-login-branding \
  --user-pool-id <POOL_ID> --managed-login-branding-id <ID> \
  --query 'ManagedLoginBranding.Settings' --profile <PROFILE>
```

Then commit that JSON and edit its colours. Unset properties fall back to
Cognito's defaults.
