# Design Specification: [FEATURE NAME]

**Status**: Draft
**Related Spec**: [Link to spec.md]
**Design Strategy**: [e.g., "Minimalist Dashboard", "Playful E-commerce"]

## 1. Design System

### Color Palette ([Mode: Light/Dark])

| Role | Color Name | Hex Code | Tailwind Token | Usage |
|------|------------|----------|----------------|-------|
| Primary | [Name] | `#[Hex]` | `bg-primary` | Main actions, highlights |
| Secondary | [Name] | `#[Hex]` | `bg-secondary` | Accents, secondary actions |
| Background | [Name] | `#[Hex]` | `bg-background` | Page background |
| Surface | [Name] | `#[Hex]` | `bg-surface` | Cards, modals, panels |
| Text Main | [Name] | `#[Hex]` | `text-primary` | Headings, body text |
| Text Muted | [Name] | `#[Hex]` | `text-muted` | Metadata, subtitles |
| Border | [Name] | `#[Hex]` | `border-default` | Dividers, inputs |
| Success | [Name] | `#[Hex]` | `text-success` | Success states |
| Error | [Name] | `#[Hex]` | `text-error` | Error states |

### Typography

**Font Family**: `[Font Name]` (Headings) / `[Font Name]` (Body)
**Import**: `[Google Fonts Link]`

| Scale | Weight | Size (px/rem) | Token | Usage |
|-------|--------|---------------|-------|-------|
| H1 | [Bold] | [Size] | `text-4xl` | Page Titles |
| H2 | [Semi] | [Size] | `text-2xl` | Section Headings |
| Body | [Reg] | [Size] | `text-base` | Main Content |
| Small | [Reg] | [Size] | `text-sm` | Metadata, Labels |

### UI Elements & Effects

- **Border Radius**: `rounded-[size]` (e.g., `rounded-xl` for cards, `rounded-lg` for buttons)
- **Shadows**: `shadow-[size]` (e.g., `shadow-sm` for cards, `shadow-lg` for dropdowns)
- **Glassmorphism**: [Yes/No] (e.g., `bg-white/80 backdrop-blur-md`)
- **Spacing Scale**: [Tight/Relaxed] (Base unit: `4` or `1rem`)

## 2. Component Guidelines

### [Component Name 1] (e.g., "Action Card")

- **Structure**: [Describe layout, e.g., "Icon left, Text right"]
- **Interactions**:
    - Hover: [Effect, e.g., "Lift up, shadow increases"]
    - Click: [Effect, e.g., "Scale down 95%"]
- **States**: [Default, Active, Disabled]

### [Component Name 2] (e.g., "Data Table")

- **Structure**: [Describe layout]
- **Interactions**: [Row hover, sort headers]

## 3. Page Layouts & Flows

### [Page/Screen Name]

- **Layout Structure**:
    - Header: [Sticky/Fixed]
    - Sidebar: [Collapsible/Fixed]
    - Content Area: [Grid/List]
- **Key Sections**:
    1.  [Hero/Top Section]: [Description]
    2.  [Main Content]: [Description]
- **Responsive Behavior**:
    - Mobile: [Stacked, hidden sidebar]
    - Desktop: [Two columns]

## 4. Accessibility & UX Rules

- [ ] Interactive elements have `cursor-pointer`
- [ ] Contrast ratio meets WCAG AA (4.5:1)
- [ ] Images include `alt` text placeholders
- [ ] Focus rings visible for keyboard users
- [ ] No layout shift on hover
