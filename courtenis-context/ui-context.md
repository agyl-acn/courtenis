# UI Context

## Theme

Light only. The design language is a premium sports booking platform —
full-bleed hero photography, a floating white booking card, and a navy +
yellow palette that nods to tennis ball energy. All interactions feel
snappy (150ms transitions).

## Colors

All components must use CSS custom properties — no hardcoded hex values.

| Role                | CSS Variable          | Value                    |
| ------------------- | --------------------- | ------------------------ |
| Page background     | `--bg-base`           | `#FFFFFF`                |
| Surface / input bg  | `--bg-surface`        | `#F5F5F7`                |
| Card translucent    | `--bg-card`           | `rgba(255,255,255,0.93)` |
| Navy dark           | `--color-navy`        | `#1E2A6E`                |
| Yellow primary      | `--color-yellow`      | `#F5D000`                |
| Logo green          | `--color-logo-green`  | `#4CAF70`                |
| Text primary        | `--text-primary`      | `#1A1A2E`                |
| Text secondary      | `--text-secondary`    | `#555570`                |
| Text muted          | `--text-muted`        | `#9999AA`                |
| Text on hero        | `--text-on-hero`      | `#FFFFFF`                |
| Text on yellow      | `--text-on-yellow`    | `#1A1A2E`                |
| Border input        | `--border-input`      | `#E0E0EA`                |
| Border divider      | `--border-divider`    | `#E8E8EE`                |
| Section label       | `--text-section-label`| `#888899`                |
| Hero overlay        | `--hero-overlay`      | `rgba(0,0,0,0.22)`       |
| State error         | `--state-error`       | `#E24B4A`                |
| State success       | `--state-success`     | `#3B6D11`                |

## Typography

| Role            | Font              | Variable       |
| --------------- | ----------------- | -------------- |
| Hero headlines  | Playfair Display  | `--font-serif` |
| UI / everything else | Inter        | `--font-sans`  |

Fonts loaded via Google Fonts. Serif is used for hero headlines only —
all UI elements use sans-serif.

## Type Scale

| Role           | Size  | Weight | Notes                                  |
| -------------- | ----- | ------ | -------------------------------------- |
| Hero headline  | 52px  | 700    | Serif, white, with strikethrough       |
| Section title  | 32px  | 700    | Sans, centered, max-width 640px        |
| Card heading   | 22px  | 600    | Sans                                   |
| Body           | 14px  | 400    | Sans                                   |
| Nav item       | 14px  | 500    | Sans                                   |
| Input label    | 12px  | 500    | Sans, muted                            |
| Section label  | 12px  | 500    | Uppercase, letter-spacing 2px          |
| CTA button     | 15px  | 700    | Sans                                   |

## Border Radius

| Context              | Value  | Variable          |
| -------------------- | ------ | ----------------- |
| Pill (navbar, badge) | 999px  | `--radius-pill`   |
| Booking card         | 24px   | `--radius-card-lg`|
| Card internal group  | 16px   | `--radius-card-md`|
| Input fields         | 8px    | `--radius-input`  |
| CTA Book button      | 12px   | `--radius-btn`    |

## Shadows

| Variable         | Value                                     | Used on               |
| ---------------- | ----------------------------------------- | --------------------- |
| `--shadow-nav`   | `0 2px 16px rgba(0,0,0,0.08)`            | Navbar                |
| `--shadow-card`  | `0 8px 40px rgba(0,0,0,0.12)`            | Booking card          |
| `--shadow-focus` | `0 0 0 3px rgba(30,42,110,0.12)`         | Input focus state     |
| `--shadow-cta`   | `0 4px 16px rgba(245,208,0,0.35)`        | Book Court Now button |

## Component Library

No external component library — pure CSS with custom properties.
Reusable components live in `frontend/src/components/`.

## Layout Patterns

- **Hero**: Full-bleed background photo, `min-height: 80vh`, navbar
  floating on top. Left column: copy. Right column: booking card (~400px).
- **Navbar**: Pill shape, `width: 84%`, centered, `position: sticky top: 16px`
- **Admin layout**: Fixed left sidebar (240px) + main content area
- **Chatbot**: Fixed position bottom-right, `bottom: 24px; right: 24px`
- **Section**: `padding: 64px 6%`, white background, centered title

## Chatbot Widget

- Toggle button: 52px circle, background `--color-yellow`, chat icon
- Panel: `width: 360px; height: 480px`, card with shadow-card, radius-card-lg
- User bubble: background `--color-navy`, white text, right-aligned
- Agent bubble: background `--bg-surface`, primary text, left-aligned
- Input: full-width at panel bottom, border-top divider

## Icons

Lucide React. Stroke-based, `strokeWidth={1.5}`.
- Inline form fields: `size={16}`, color `var(--text-muted)`
- Buttons: `size={18}`
- Nav active dot: not an icon — a `<span>` element, 6px circle, `--color-navy`

## Animations

All transitions `150ms ease`. No animation longer than `300ms`.
- Input focus: box-shadow glow via `--shadow-focus`
- CTA hover: `filter: brightness(0.95)` + `transform: scale(1.01)`
- Chatbot panel: `transform: translateY` slide up/down on toggle
- Dropdown: `opacity + translateY` slide down

## Do's and Don'ts

1. Use `--color-yellow` only for the primary CTA and welcome badge
2. Use `--color-navy` for secondary CTAs and brand elements
3. Never hardcode hex values — always use CSS variables
4. Navbar must always be pill-shaped — it's a core brand differentiator
5. The strikethrough on the first line of the hero headline is intentional
6. Serif font is for hero headlines only
7. No border on input focus — use box-shadow glow instead
8. Section labels are always uppercase and muted
