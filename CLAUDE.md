# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a ZMK firmware configuration for the Temper split mechanical keyboard, based on [urob's zmk-config](https://github.com/urob/zmk-config). The owner is a fullstack web developer using macOS and Linux (no Windows).

**Key customizations from upstream:**
- macOS-style navigation shortcuts (Cmd+arrows, Option+Backspace)
- Temper keyboard shield with nice!view displays
- Simplified Magic Shift (no repeat key functionality)
- Removed unused features (Greek letters, Windows shortcuts)

The configuration builds against ZMK v0.3 with custom modules.

## Essential Commands

```bash
# Build firmware for Temper keyboard
just build temper

# Build all configured targets
just build all

# List available build targets
just list

# Clean build cache
just clean

# Draw keymap visualization to draw/base.svg
just draw

# Initialize west workspace (first time setup)
just init

# Update ZMK dependencies
just update
```

## Directory Structure

```
zmk-config/
├── config/
│   ├── base.keymap          # Core 34-key layout (all layers, behaviors)
│   ├── combos.dtsi          # Combo definitions (symbols, shortcuts)
│   ├── leader.dtsi          # Leader key sequences (umlauts, system)
│   ├── mouse.dtsi           # Mouse emulation layer
│   ├── extra_keys.h         # Additional key definitions
│   ├── west.yml             # Build dependencies and ZMK modules
│   ├── temper.keymap        # Temper-specific layout (imports base.keymap)
│   ├── temper.conf          # Temper hardware settings
│   └── boards/shields/temper/  # Temper shield definition
├── build.yaml               # CI/CD build targets
├── draw/                    # Keymap visualization output
└── Justfile                 # Build automation
```

## Keymap Overview

### Physical Layout (34 keys + 2 thumb keys = 36 total)

```
╭─────────────────────╮ ╭─────────────────────╮
│  Q   W   F   P   B  │ │  J   L   U   Y   '  │
│  A   R   S   T   G  │ │  M   N   E   I   O  │  (homerow mods)
│  Z   X   C   D   V  │ │  K   H   ,   .   ?  │
╰───────╮ Gui Spc Ret │ │ Num Sft Mse ╭───────╯
        ╰─────────────╯ ╰─────────────╯
```

### Layers

| Layer | Activation | Purpose |
|-------|------------|---------|
| DEF (0) | Default | Colemak-DH with homerow mods |
| NAV (1) | Hold Space | Navigation, window/tab switching |
| FN (2) | Hold Return | F-keys, media controls |
| NUM (3) | Tap/Hold right thumb | Numpad with numword |
| SYS (4) | FN + NUM | Bluetooth, bootloader |
| MOUSE (5) | Combo W+P or right thumb | Mouse emulation |

### Key Behaviors

**Homerow Mods (timeless configuration):**
- Left: Ctrl(A), Alt(R), Cmd(S), Shift(T)
- Right: Shift(N), Cmd(E), Alt(I), Ctrl(O)
- 280ms tapping-term, 150ms require-prior-idle-ms
- Positional hold-tap prevents same-hand misfires

**Thumb Keys:**
- Space: Hold for NAV layer; Shift+tap = `. ` + sticky shift (sentence end)
- Return: Hold for FN layer
- Smart Num: Tap for numword, double-tap for sticky NUM, hold for NUM
- Magic Shift: Tap for sticky shift, double-tap for caps-word, hold for shift

**Navigation Cluster (NAV layer, macOS shortcuts):**
- Arrows with Cmd+arrow on hold (line/document navigation)
- Backspace/Delete with Option+key on hold (word deletion)

**Punctuation Morphs:**
- `,` → `;` (shift) → `<` (ctrl+shift)
- `.` → `:` (shift) → `>` (ctrl+shift)
- `?` → `!` (shift)

### Combos (symbols without a layer)

**Left hand vertical:**
- W+R: `@`, F+S: `#`, P+T: `$`, B+G: `%`
- R+X: `` ` ``, S+C: `\`, T+D: `=`, G+V: `~`

**Right hand vertical:**
- J+M: `^`, L+N: `+`, U+E: `*`, Y+I: `&`
- M+K: `_`, N+H: `-`, E+,: `/`, I+.: `|`

**Horizontal:**
- W+F: Esc, L+U: Backspace, U+Y: Delete
- N+E: `(`, E+I: `)`, H+,: `[`, ,+.: `]`
- R+S: Leader key, X+C: Cut, X+Z: Copy, C+Z: Paste

### Leader Key Sequences

Activate with R+S combo, then type:
- **German umlauts:** A→ä, O→ö, U→ü, S→ß
- **System:** USB, BLE, RESET, BOOT

## Editing Guidelines

1. **Read files before editing** - Uses zmk-helpers macros extensively
2. **Don't touch HRM timing** - Parameters are carefully tuned for "timeless" feel
3. **Use zmk-helpers macros** - `ZMK_HOLD_TAP()`, `ZMK_COMBO()`, `ZMK_LAYER()`
4. **Key positions use labels** - LT0-LT4 (left top), LM0-LM4 (left middle), etc.

## Common Patterns

**Adding a combo:**
```c
ZMK_COMBO(name, &kp KEY, POS1 POS2, DEF NAV, COMBO_TERM_FAST, COMBO_IDLE_FAST)
```

**Adding a leader sequence:**
```c
ZMK_LEADER_SEQUENCE(name, &uc UC_CODE, K E Y S)
```

**Creating a hold-tap:**
```c
ZMK_HOLD_TAP(name,
    flavor = "balanced";
    tapping-term-ms = <280>;
    quick-tap-ms = <175>;
    bindings = <&kp>, <&kp>;
)
```

## Integration with Dotfiles

This ZMK config complements the user's development environment:

- **macOS shortcuts** align with system defaults (Cmd+arrows, Option+Delete)
- **No Windows-specific keys** (Alt+F4, Win key behaviors removed)
- **Web dev friendly** - Easy access to brackets, parens, common symbols via combos
- **Leader sequences** available for extending with project-specific shortcuts

When suggesting keyboard shortcuts in other contexts, prefer:
- Cmd-based shortcuts (not Ctrl) for macOS compatibility
- Combos over layer-switching for frequently used symbols
- Leader sequences for infrequent but memorable actions
