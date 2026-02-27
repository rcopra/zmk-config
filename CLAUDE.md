# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a ZMK firmware configuration for the Temper split mechanical keyboard, based on [urob's zmk-config](https://github.com/urob/zmk-config). The owner is a fullstack web developer using macOS and Linux (no Windows).

**Key customizations from upstream:**
- macOS-style navigation shortcuts (Cmd+arrows, Option+Backspace)
- Temper keyboard shield with nice!view displays
- Simplified Magic Shift (no repeat key functionality)
- Removed unused features (Greek letters, Windows shortcuts)

The configuration builds against ZMK v0.3 with custom modules. All build dependencies (ZMK, Zephyr, and ZMK modules) are pinned via the west manifest in `config/west.yml` and reproducible via `flake.lock`.

## ZMK Modules

Six upstream modules (all from urob, pinned to `v0.3`) extend base ZMK:

| Module | Purpose |
|--------|---------|
| `zmk-helpers` | Convenience macros for behaviors, combos, layers, morphs; key-position labels |
| `zmk-auto-layer` | Powers smart-num (numword) — auto-exits NUM layer on non-number keypresses |
| `zmk-tri-state` | Swapper behavior for app/window switching (used in NAV layer) |
| `zmk-leader-key` | Leader key sequences via `ZMK_LEADER_SEQUENCE()` |
| `zmk-unicode` | Unicode input helpers (`&uc`) for umlauts and special chars |
| `zmk-adaptive-key` | Adaptive/context-sensitive key behaviors |

## ZMK Helpers — Macro Reference

**This codebase is almost entirely written with `zmk-helpers` macros. Never write raw Devicetree nodes for behaviors, combos, or layers — always use the corresponding macro.** Mixing raw DTS with helpers causes subtle, hard-to-debug issues.

`helper.h` must be included **after** `behaviors.dtsi` (already correct in `base.keymap`).

### Behavior macros (replace raw `/ { behaviors { ... }; };` nodes)

| Macro | Replaces |
|-------|---------|
| `ZMK_HOLD_TAP(name, ...)` | `hold-tap` behavior node |
| `ZMK_MOD_MORPH(name, ...)` | `mod-morph` behavior node |
| `ZMK_MACRO(name, ...)` | `macro` behavior node |
| `ZMK_MACRO_ONE_PARAM(name, ...)` | parameterized macro (1 arg) |
| `ZMK_MACRO_TWO_PARAM(name, ...)` | parameterized macro (2 args) |
| `ZMK_TAP_DANCE(name, ...)` | `tap-dance` behavior node |
| `ZMK_STICKY_KEY(name, ...)` | `sticky-key` behavior node |
| `ZMK_CAPS_WORD(name, ...)` | `caps-word` behavior node |
| `ZMK_TRI_STATE(name, ...)` | tri-state behavior (zmk-tri-state module) |
| `ZMK_AUTO_LAYER(name, ...)` | auto-layer behavior (zmk-auto-layer module) |
| `ZMK_ADAPTIVE_KEY(name, ...)` | adaptive-key behavior (zmk-adaptive-key module) |

### Configuration macros

| Macro | Purpose |
|-------|---------|
| `ZMK_COMBO(name, binding, positions, layers, term, idle)` | Define a combo; use key-position labels (e.g. `LM1 LM2`) |
| `ZMK_COMBO(name, binding, positions, layers, term, idle, hold, trigger_pos)` | 8-arg variant for combos overlapping HRMs |
| `ZMK_LAYER(name, keys, ...)` | Define a keymap layer |
| `ZMK_CONDITIONAL_LAYER(if_layers, then_layer)` | Tri-layer (e.g. FN+NUM → SYS) |
| `ZMK_LEADER_SEQUENCE(name, binding, keys...)` | Leader key sequence (zmk-leader-key module) |
| `ZMK_UNICODE_SINGLE(name, ...)` | Single unicode character |
| `ZMK_UNICODE_PAIR(name, ...)` | Unicode pair (shifted/unshifted) |

### Key-position labels (from `zmk-helpers`)

```
LT4 LT3 LT2 LT1 LT0  |  RT0 RT1 RT2 RT3 RT4   (top row)
LM4 LM3 LM2 LM1 LM0  |  RM0 RM1 RM2 RM3 RM4   (middle/home row)
LB4 LB3 LB2 LB1 LB0  |  RB0 RB1 RB2 RB3 RB4   (bottom row)
        LH2 LH1 LH0  |  RH0 RH1 RH2            (thumbs)
```

Use these labels everywhere instead of raw integer positions.

### Docs

When in doubt, check the upstream source: https://github.com/urob/zmk-helpers

## Local Build Environment

The workspace uses **Nix + direnv + just** for a fully isolated, reproducible build environment. Dependencies are pinned in `flake.lock`.

### First-time setup

1. Install Nix (with flakes):
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | \
     sh -s -- install --no-confirm
   ```

2. Install direnv and nix-direnv:
   ```bash
   nix profile install nixpkgs#direnv nixpkgs#nix-direnv
   ```

3. Configure direnv (bash example — adjust for zsh/fish):
   ```bash
   echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
   mkdir -p ~/.config/direnv
   echo 'source $HOME/.nix-profile/share/nix-direnv/direnvrc' >> ~/.config/direnv/direnvrc
   ```

4. Allow direnv in the workspace (loads the Nix environment automatically):
   ```bash
   direnv allow
   ```

5. Initialize the west workspace:
   ```bash
   just init   # equivalent to: west init -l config && west update && west zephyr-export
   ```

Once set up, the build environment activates automatically on `cd` into the directory.

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

1. **Read files before editing** — the config uses zmk-helpers macros pervasively; understand what's there before changing anything
2. **Never write raw Devicetree nodes** — always use the zmk-helpers macro equivalent (see ZMK Helpers — Macro Reference above); mixing the two breaks builds in non-obvious ways
3. **Don't touch HRM timing** — parameters are carefully tuned for "timeless" feel
4. **Key positions use labels** — always use `LT0`–`LT4`, `LM0`–`LM4`, `LB0`–`LB4`, `LH0`–`LH2` and right-hand equivalents; never hardcode integers
5. **When in doubt, check the helpers docs** — https://github.com/urob/zmk-helpers before guessing macro signatures

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
