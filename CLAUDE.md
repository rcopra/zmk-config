# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a ZMK firmware configuration for split mechanical keyboards, based on urob's configuration. It features a 34-key base layout reused across multiple keyboards (Temper, Corneish Zen, Glove80, Planck). The configuration builds against ZMK v0.2 and uses several custom ZMK modules for enhanced functionality.

## Essential Commands

### Building Firmware

```bash
# Build firmware for all configured boards
just build all

# Build for specific keyboard (matches partial names)
just build temper
just build zen
just build glove80
just build planck

# List all available build targets
just list

# Clean build cache and artifacts
just clean

# Pristine build (clean + rebuild)
just build all -p
```

### Development Environment

```bash
# Initialize west workspace (first time setup)
just init

# Update ZMK dependencies from west.yml
just update

# Upgrade Zephyr SDK and Nix packages (use with caution)
just upgrade-sdk

# Draw keymap visualization
just draw
```

### Testing

```bash
# Run a specific test case
just test <path-to-test>

# Run test without rebuilding
just test <path> --no-build

# Show verbose output
just test <path> --verbose

# Auto-accept new test snapshot
just test <path> --auto-accept
```

## Architecture

### Directory Structure

```
zmk-workspace/
├── config/               # User configuration files
│   ├── base.keymap      # Shared 34-key base layout
│   ├── combos.dtsi      # Combo definitions
│   ├── leader.dtsi      # Leader key sequences
│   ├── mouse.dtsi       # Mouse emulation layer
│   ├── extra_keys.h     # Additional key definitions
│   ├── west.yml         # Build dependencies and modules
│   ├── boards/shields/  # Custom keyboard shields (e.g., temper)
│   └── *.keymap/*.conf  # Board-specific configs
├── build.yaml           # Defines build targets for CI/CD
├── Justfile             # Build automation recipes
├── modules/             # ZMK modules (created by west)
├── zephyr/              # Zephyr RTOS (created by west)
└── zmk/                 # ZMK firmware source (created by west)
```

### Key Configuration Files

**base.keymap**: The core 34-key layout using advanced ZMK features:
- Timeless homerow mods with `balanced` flavor, `require-prior-idle-ms`, and positional hold-taps
- Custom hold-tap behaviors (HRMs, nav cluster, magic shift/repeat)
- Layer definitions (DEF, NAV, FN, NUM, SYS, MOUSE)
- Includes combos.dtsi, leader.dtsi, mouse.dtsi, extra_keys.h

**Board-specific .keymap files**: Import base.keymap and adapt for physical layout:
- Define key position labels (LT0-LT4, LM0-LM4, etc.)
- Map physical matrix to logical layout
- Set keyboard-specific overrides

**Board-specific .conf files**: Configure ZMK settings:
- Combo counts (MAX_COMBOS_PER_KEY, MAX_KEYS_PER_COMBO)
- Bluetooth settings for wireless boards
- Display settings (e.g., nice!view)
- Power management

**west.yml**: Pins ZMK and all modules to v0.2:
- ZMK modules: zmk-adaptive-key, zmk-auto-layer, zmk-helpers, zmk-leader-key, zmk-tri-state
- Custom Zephyr revision for pending fixes
- Defines workspace topology

### ZMK Modules Used

This config requires these custom modules (automatically fetched by west):
- **zmk-helpers**: Simplified devicetree syntax macros (ZMK_HOLD_TAP, ZMK_COMBO, etc.)
- **zmk-auto-layer**: Auto-deactivating layers (Numword, Smart-mouse)
- **zmk-leader-key**: Leader key sequences for Unicode and system commands
- **zmk-tri-state**: One-handed Alt-Tab window switcher
- **zmk-adaptive-key**: Contextual key behavior (magic shift/repeat/capsword)

### Key Features

**Timeless Homerow Mods**:
- Use `balanced` flavor with 280ms tapping-term
- `require-prior-idle-ms = 150` eliminates typing delay
- `hold-trigger-on-release` prevents false positives when rolling
- Positional hold-tap prevents same-side HRM activation
- See config/base.keymap:48-65 for implementation

**Combos Instead of Symbol Layer**:
- Vertical combos replicate number row symbols
- Horizontal combos for brackets/parens (with shift variants)
- `require-prior-idle-ms` on combos prevents misfires
- See config/combos.dtsi for all definitions

**Smart Layers**:
- **Numword**: Auto-layer that stays active while typing numbers
- **Smart-mouse**: Replaces nav cluster with mouse controls, auto-deactivates
- **Magic Shift/Repeat/Capsword**: Context-aware right thumb (tap after alpha = repeat, tap after other = sticky-shift, hold = shift, double-tap = capsword)

**Navigation Cluster**: Hold-taps on arrow keys provide cmd+arrow shortcuts (start/end of line/document)

**Leader Key**: Comboing S+T activates leader sequences for Umlauts, Greek letters, and system commands

## Important Notes

### Editing Configuration

1. **Always read existing files first** - This config uses advanced ZMK features and custom macros from zmk-helpers. Understanding the existing patterns is critical.

2. **Homerow mod parameters are carefully tuned** - Don't adjust `tapping-term-ms`, `require-prior-idle-ms`, `quick-tap-ms`, or `hold-trigger-key-positions` without understanding the timeless HRM design (see README sections).

3. **Combo counts must match** - The Justfile `_parse_combos` recipe auto-calculates and sets `CONFIG_ZMK_COMBO_MAX_COMBOS_PER_KEY` and `CONFIG_ZMK_COMBO_MAX_KEYS_PER_COMBO` in .conf files. Run `just build` to apply.

4. **Key position labels** - Each board defines position labels (e.g., LT0-LT4 for left top row). These MUST match the physical key matrix. Check zmk-helpers/key-labels/ for reference.

5. **Use zmk-helpers macros** - Prefer `ZMK_HOLD_TAP()`, `ZMK_COMBO()`, etc. over raw devicetree for consistency. See modules/zmk/helpers/ after running `just init`.

### Building

- **GitHub Actions**: Builds on push to config/ or build.yaml (currently disabled via comments in .github/workflows/build.yml)
- **Local builds**: Requires Nix + direnv (fully isolated environment)
- **Firmware output**: Generated UF2/BIN files go to `firmware/` directory
- **Build cache**: Located in `.build/`, cleared with `just clean`

### West Manifest

The west.yml manifest pins everything to v0.2 for stability. To update:
1. Edit config/west.yml revisions
2. Run `just update` to fetch changes
3. Test thoroughly - ZMK updates can break custom modules

### Custom Keyboards

To add a custom keyboard (like the included "temper" shield):
1. Create shield in config/boards/shields/<name>/
2. Add board+shield combo to build.yaml
3. Create config/<name>.conf and config/<name>.keymap
4. Define key position labels matching physical matrix
5. Import base.keymap and adapt as needed

## Common Patterns

**Defining a hold-tap behavior**:
```c
ZMK_HOLD_TAP(my_ht,
    flavor = "balanced";
    tapping-term-ms = <280>;
    quick-tap-ms = <175>;
    bindings = <&kp>, <&kp>;
)
```

**Using positional hold-tap**:
```c
hold-trigger-key-positions = <KEYS_R THUMBS>;
hold-trigger-on-release;
```

**Defining a combo**:
```c
ZMK_COMBO(name, &kp KEY, LT1 LT2, DEF NAV, COMBO_TERM_FAST, COMBO_IDLE_FAST)
```

**Creating a layer**:
```c
ZMK_LAYER(nav_layer,
    // 34-key layout
    &key1  &key2  ...
    ...
)
```

## Temper Keyboard Behavior Summary

The Temper is a 36-key wireless split keyboard with extensive custom functionality. This section documents its behavior for quick reference.

### Physical Layout

**36-key split layout:**
```
╭─────────────────────╮ ╭─────────────────────╮
│  Q   W   F   P   B  │ │  J   L   U   Y   '  │  Top row (LT/RT)
│  A   R   S   T   G  │ │  M   N   E   I   O  │  Middle/home row (LM/RM)
│  Z   X   C   D   V  │ │  K   H   ,   .   ?  │  Bottom row (LB/RB)
╰───────╮ Cmd Spc Ret │ │ Num Sft Mse ╭───────╯  Thumb keys (LH/RH)
        ╰─────────────╯ ╰─────────────╯
```

**Hardware features:**
- nice!view displays
- 30-minute sleep timeout
- Enhanced Bluetooth with experimental connections
- Mouse emulation with smooth scrolling
- Optimized for 3840x2160 displays

### Base Layer (Colemak-DH)

**Alpha keys:** Q W F P B / J L U Y '  (top row)
- Uses Colemak-DH layout optimized for typing comfort

**Timeless homerow mods:**
- Left hand: Ctrl(A), Alt(R), Cmd(S), Shift(T)
- Right hand: Shift(N), Cmd(E), Alt(I), Ctrl(O)
- 280ms tapping-term with 150ms require-prior-idle-ms
- Positional hold-tap prevents accidental same-side activation

**Punctuation (right bottom):**
- H key position: H
- Comma key: `,` (tap) / `;` (shift) / `<` (ctrl+shift)
- Dot key: `.` (tap) / `:` (shift) / `>` (ctrl+shift)
- Right pinky: `?` (tap) / `!` (shift)

### Thumb Keys (Left to Right)

**Left side:**
1. **Cmd/Super** - Left-most thumb (36-key addition)
2. **Space / NAV layer** - Hold for NAV layer; Shift+tap = `. ` + sticky shift
3. **Return / FN layer** - Tap for Enter, hold for FN layer

**Right side:**
1. **NUM layer** - Tap for numword, double-tap for sticky NUM, hold for NUM layer
2. **Magic Shift** - Tap for one-shot shift, double-tap for caps-word, hold for shift
3. **Smart-mouse** - Right-most thumb (36-key addition), auto-deactivates when not in use

### Layers

**NAV (Navigation):**
- Arrow cluster (HJKL-style on right hand) with cmd+arrow on hold
- Page Up/Down, Home/End
- Tab navigation (Tab, Shift+Tab)
- Cmd+Tab swapper for window switching
- Ctrl+Tab / Ctrl+Shift+Tab for browser tab switching
- Sticky mods on left hand (Ctrl, Alt, Cmd, Shift)
- Backspace/Delete with word-deletion on hold (Ctrl+Del)

**FN (Function keys):**
- F1-F12 arranged by columns (F12/F11/F10 top, F7/F4/F1 middle, F8/F5/F2 right middle, F9/F6/F3 far right middle)
- Media controls (prev/next track, vol up/down, play/pause, mute)
- Desktop management (prev/next desktop, pin window/app, desktop manager)
- Function key homerow mods on left hand

**NUM (Numbers):**
- Number pad layout: 7 8 9 (top), 0 4 5 6 (home), 1 2 3 (bottom)
- Number homerow mods on left hand (0 has Ctrl, 4 has Alt, 5 has Cmd, 6 has Shift)
- Auto-layer (numword) keeps layer active while typing numbers

**SYS (System - accessed via FN+NUM):**
- Bluetooth profiles 0-4 on top row, BT clear
- Bootloader and reset buttons

**MOUSE (Mouse emulation):**
- Mouse movement (HJKL-style: up/down/left/right)
- Mouse buttons (left/middle/right click)
- Scroll wheel (up/down/left/right)
- Page Up/Down on top row
- Speed adjustments: 3x speed on NAV layer, 0.5x precision on FN layer

### Combo System

The Temper uses combos instead of a dedicated symbol layer. All combos work on DEF, NAV, and NUM layers.

**Horizontal combos - Left hand:**
- W+F: Esc
- F+P: Smart-mouse toggle
- A+R: Tab (or Shift+Alt+Tab when shifted)
- R+S: Leader key
- A+R+S: Leader key + shift
- X+C: Cut (Cmd+X)
- X+Z: Copy (Cmd+C)
- C+Z: Paste (Cmd+V)

**Horizontal combos - Right hand:**
- L+U: Backspace
- U+Y: Delete
- N+E: `(` or `<` with shift (DEF/NUM only)
- E+I: `)` or `>` with shift (DEF/NUM only)
- N+E: `<` (NAV layer only)
- E+I: `>` (NAV layer only)
- H+,: `[` (DEF/NUM) or `{` (NAV)
- ,+.: `]` (DEF/NUM) or `}` (NAV)

**Vertical combos - Left hand (symbols):**
- W+R: `@`
- F+S: `#`
- P+T: `$`
- B+G: `%`
- R+X: `` ` `` (backtick)
- S+C: `\`
- T+D: `=`
- G+V: `~`

**Vertical combos - Right hand (symbols):**
- J+M: `^`
- L+N: `+`
- U+E: `*`
- Y+I: `&`
- M+K: `_`
- N+H: `-`
- E+,: `/`
- I+.: `|`

### Leader Key Sequences

Activate leader by combo (R+S), then type sequence:

**German umlauts:**
- A: ä
- O: ö
- U: ü
- S: ß

**Greek letters** (E + letter):
- E A: α (alpha)
- E B: β (beta)
- E G: γ (gamma)
- E D: δ (delta)
- E E: ε (epsilon)
- E Z: ζ (zeta)
- E H: η (eta)
- E V: θ (theta)
- E I: ι (iota)
- E K: κ (kappa)
- E L: λ (lambda)
- E M: μ (mu)
- E N: ν (nu)
- E X: ξ (xi)
- E O: ο (omicron)
- E P: π (pi)
- E R: ρ (rho)
- E S: σ (sigma)
- E T: τ (tau)
- E U: υ (upsilon)
- E F: ϕ (phi)
- E C: χ (chi)
- E Y: ψ (psi)
- E W: ω (omega)

**System commands:**
- U S B: Switch to USB output
- B L E: Switch to BLE output
- R E S E T: System reset
- B O O T: Enter bootloader

### Custom Behaviors

**Window/Tab Swapper (Tri-state):**
- Tap W on NAV layer to activate Cmd+Tab (hold Cmd, tap Tab repeatedly with W, release elsewhere)
- Tap X on NAV layer for Ctrl+Tab (next browser tab)
- Tap C on NAV layer for Ctrl+Shift+Tab (previous browser tab)

**Smart-mouse:**
- Auto-activates mouse layer when toggled via combo or thumb key
- Auto-deactivates when typing outside mouse/nav areas
- Ignores specific keys to keep mouse active while using them

**Magic Shift (right outer thumb):**
- Tap: One-shot shift (sticky shift for next key)
- Double-tap or Shift+tap: Caps-word
- Hold: Regular shift

**Numword:**
- Keeps NUM layer active while typing numbers
- Auto-deactivates when typing non-number keys

**Navigation cluster with cmd shortcuts:**
- Arrow keys (tap) become cmd+arrow (hold) for document navigation
- Left/Right: Start/end of line (Cmd+arrow)
- Up/Down: Start/end of document (Cmd+arrow)
- Backspace/Delete: Word deletion (Ctrl+Bspc/Del)

### Configuration Notes

**Combo settings:**
- Maximum 6 combos per key
- Maximum 3 keys per combo
- Fast combos: 18ms term, 150ms idle (typing combos)
- Slow combos: 30ms term, 50ms idle (vertical symbol combos)

**Timing parameters:**
- Homerow mods: 280ms tapping-term, 150ms require-prior-idle
- Layer taps: 200ms tapping-term
- Quick-tap: 175ms global default
- Sticky keys: 900ms release timeout

**Display configuration:**
- nice!view displays enabled
- Battery status shown
- Layer status display disabled (commented out)

This configuration emphasizes minimal finger travel, heavy use of combos for symbols, and context-aware behaviors that adapt based on typing patterns.
