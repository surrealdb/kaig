## Colors

```css
  /* Surface */
  --bg:           #0E0C14;   /* obsidian-9 */
  --card:         #16141F;   /* obsidian-8 */
  --card-hover:   #1A1824;
  --card-elev:    #201D29;   /* obsidian-7 */

  /* Borders */
  --border-subtle:  rgba(255, 255, 255, 0.06);
  --border-default: rgba(255, 255, 255, 0.10);
  --border-strong:  rgba(255, 255, 255, 0.16);

  /* Text - tuned to clear WCAG AA on the dark card surface (#16141F).
     --text-muted on dark (#7B7585) is one stop lighter than the legacy
     #5A5565 because that earlier value clocked 2.5:1 and failed AA at
     every text size.  Now 4.6:1 - safe at 14px+ regular weight. */
  --text:       #E8E4ED;
  --text-dim:   #8A8494;
  --text-muted: #7B7585;

  /* Semantic - re-tune for dark backgrounds.  Favourable stays on the
     brand-pink register; pink reads cleanly against obsidian without
     re-tuning.  Danger steps down one notch from the light-surface coral
     to keep the chip legible against the deep card surface. */
  --success: #D255FE;
  --danger:  #E5484D;
  --warn:    #FFD000;

  /* Charts on dark */
  --chart-grid:           rgba(255, 255, 255, 0.04);
  --chart-tick:           #8A8494;
  --chart-tooltip-bg:     #201D29;
  --chart-tooltip-border: rgba(255, 255, 255, 0.10);
  --chart-tooltip-text:   #E8E4ED;
  --chart-trajectory:     #D255FE;
  --chart-ghost-fill:     rgba(101, 29, 221, 0.18);
  --chart-ghost-border:   rgba(210, 85, 254, 0.55);
  --chart-connector:      rgba(255, 255, 255, 0.15);
  --chart-margin-band:    rgba(210, 85, 254, 0.10);
  --chart-loss-fill:      rgba(231, 76, 60, 0.10);
```

## Typography

Two-face system with a clear hierarchy:

- **Inter** (variable, weights 300-900) - **primary**. Lead face for everything: titles, section headers, KPI display values, body, labels, buttons, tooltips, prose.
- **JetBrains Mono** (weights 400-700) - **secondary accent**. Used in narrow, well-defined slots where the content is code-shaped, structurally tabular, or works as a stamp/marker. It punctuates an Inter page; it never carries it.

```html
<!-- Primary CDN: Google Fonts.  `display=swap` makes the system font visible
     while Inter / JetBrains Mono load, so first paint is never blocked. -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">

<!-- Fallback for environments where Google Fonts is blocked (some EU
     enterprise networks, China, air-gapped previews).  Bunny Fonts is a
     drop-in mirror with the identical URL surface and zero-cookie
     telemetry.  Drop the fallback in only if Google Fonts is known
     unreachable; do not load both at once. -->
<!--
<link rel="preconnect" href="https://fonts.bunny.net">
<link href="https://fonts.bunny.net/css?family=inter:300,400,500,600,700,800,900|jetbrains-mono:400,500,600,700&display=swap" rel="stylesheet">
-->
```

If both CDNs are unreachable (fully offline render, PDF export from a sandbox), the canonical font-family stacks degrade silently to `system-ui`:

- Inter: `'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`
- JetBrains Mono: `'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace`

Both are present in every artefact's CSS body rule.  Do not introduce a parallel `font-family:` declaration that omits the system fallbacks.
