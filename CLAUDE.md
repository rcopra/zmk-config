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
