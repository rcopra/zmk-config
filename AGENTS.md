# AGENTS.md

Guidance for coding agents working in this `zmk-config` repository.

## Repository Profile

- Project type: ZMK firmware configuration (not a general application codebase).
- Primary domain: Devicetree keymap/config files, shield definitions, and build automation.
- Upstream base: `urob/zmk-config` patterns and helpers.
- Target user environment: macOS and Linux (no Windows assumptions).

## Source of Truth

- Read `CLAUDE.md` for orientation, then `docs/d50-map.md` for the canonical physical → emitted keymap map (layers, combos, behaviors, emitted global chords).
- Respect the existing macro-heavy style from `zmk-helpers`.
- Prefer existing repository conventions over generic ZMK examples.
- `draw/hillside_d50.yaml` is the generated machine-readable view; CI fails if it drifts from the keymap, so regenerate it when bindings change.

## Build, Test, and Validation Commands

Run from repo root. Use `nix develop` when tools are unavailable on host.

### Environment setup

- `direnv allow` - activate pinned Nix dev environment automatically.
- `just init` - initialize west workspace (`.west`, `zmk`, `zephyr`, modules).
- `just sync` - synchronize west dependencies from the pinned manifest.
- `just bump-nix` - bump the Nix toolchain (`flake.lock`).

### Build commands

- `just list` - list valid build targets from `build.yaml`.
- `just build hillside` - build the Hillside D50 targets (primary board).
- `just build temper` - build the legacy Temper targets.
- `just build all` - build every target in `build.yaml`.
- `just build <expr>` - build targets matching expression.
- `just flash <expr>` - build and flash targets matching expression.
- `just clean` - remove `.build` and `firmware` artifacts.
- `just clean-all` - remove all generated west/zmk workspace content too.

### Draw/visualization

- `just draw` - regenerate the 34-key base artifacts in `draw/`.
- `just draw-d50` - regenerate `draw/hillside_d50.yaml` + `.svg` (50-key D50),
  and the physical position card `draw/hillside_d50-positions.{md,svg}`.
- `just layout-card` - regenerate only the position card (called by `draw-d50`).
- CI enforces that tracked draw artifacts match a fresh regeneration.

### Test commands

- `just test <testpath>` - run one test case from a test directory.
  - This recipe builds `native_sim//zmk_test_mock` firmware for that test config and diffs logs.
  - `testpath` must point to a directory containing expected snapshot files.
- `just test <testpath> --verbose` - print reduced event log.
- `just test <testpath> --auto-accept` - update snapshot from latest output.
- `just test <testpath> --no-build` - reuse previous build and only re-run log diff.

### Single-test workflow (important)

- There are no test fixture directories checked into this repo currently.
- If you add tests, keep one directory per case with:
  - `keycode_events.snapshot`
  - `events.patterns`
  - any per-test config files required by ZMK.
- Then run exactly one case with:
  - `just test path/to/test-case`

### CI parity checks

- `nix develop --command just init`
- `nix develop --command just build settings_reset`
- `nix develop --command just draw`
- `nix develop --command just draw-d50`

These mirror `.github/workflows/test-build-env.yml`.

## Lint/Format Reality

- `just format <file|dir>` runs `dts-format` from the Nix dev shell over
  devicetree files. It does not reformat C-preprocessor macros, so the
  hand-aligned keymap grids are safe; plain devicetree will be normalized.
- No repo-local ESLint/Ruff/etc. is configured.
- Formatting signals present:
  - `.prettierrc` for prose wrapping (`proseWrap: always`, `editorconfig: true`).
  - Existing DTS/keymap formatting conventions in `config/`.
- Practical rule: format by matching surrounding file style exactly.

## Required Keymap Authoring Rules

These are critical and non-optional for this repository.

1. Never write raw Devicetree behavior/combo/layer nodes when helper macros exist.
2. Always use `zmk-helpers` macros (`ZMK_HOLD_TAP`, `ZMK_COMBO`, `ZMK_LAYER`, etc.).
3. Keep `#include <zmk-helpers/helper.h>` after `#include <behaviors.dtsi>`.
4. Use key-position labels (`LT*`, `LM*`, `LB*`, `LH*`, `RT*`, `RM*`, `RB*`, `RH*`), never raw integers for combos.
5. Do not retune homerow-mod timing unless explicitly requested.
6. Speak about keys with the shared physical aliases (`L_COL2_TOP`,
   `R_THUMB_LOWER_MID`, ...) defined in `config/key-labels/hillside_d50.h`, and
   restate the target as alias + position (e.g. `L_COL3_TOP`, pos 2) before
   editing a binding. `draw/hillside_d50-positions.md` is the exhaustive card.
7. Keep `LT*`/`X_*` labels and 0-49 positions as the machine-facing names in
   combos, draw tooling, and CI; aliases are additive, not a replacement.

## Imports and Include Ordering

- In keymap files, follow the existing top-of-file pattern:
  1) behavior includes,
  2) host/module defines,
  3) helper includes,
  4) dt-bindings includes,
  5) conditional wireless includes.
- Keep local includes (`"combos.dtsi"`, `"leader.dtsi"`, etc.) after macro prerequisites.
- Avoid duplicate includes unless guarded by existing patterns.

## Naming Conventions

- Macros/constants: `UPPER_SNAKE_CASE` (`DEF`, `NAV`, `QUICK_TAP_MS`).
- Custom behavior instances: `snake_case` (`magic_shift`, `smart_num`, `tab_swapper`).
- Combo names: short `snake_case` identifiers (`esc`, `ldr`, `plus`, `pipe`).
- Use descriptive names for new behaviors; avoid single-letter identifiers.
- Reuse established aliases (`XXX`, `___`) rather than inventing alternatives.

## Formatting Conventions

- Follow existing indentation and wrapping in each file (do not reformat unrelated blocks).
- Keep aligned matrix comments in layer definitions when modifying those sections.
- Prefer one macro invocation per logical unit for readability.
- Keep line length readable; preserve hand-aligned columns where present.
- Use ASCII unless a file already requires unicode glyph comments.

## Types and Value Conventions (Devicetree/C-preprocessor context)

- Use explicit Devicetree cell syntax (`<...>`) for numeric properties.
- Keep key bindings in canonical ZMK token form (`&kp`, `&mo`, `&sk`, etc.).
- Prefer symbolic keycodes/macros over hardcoded numeric values.
- Treat layer IDs and timing values as configuration constants, not scattered literals.

## Error Handling and Safety

- For bash/just scripts, keep `set -euo pipefail` in script blocks.
- Fail fast when required inputs are missing (see existing `just build` behavior).
- Preserve existing artifact copy logic (`.uf2` vs `.bin`) unless change is required.
- Avoid destructive git operations; never discard user changes.

## Change Scope Discipline

- Make minimal, targeted edits.
- Do not refactor broad sections unless requested.
- Keep comments concise and only for non-obvious rationale.
- Do not add new dependencies or modules without clear justification.

## Files and Areas to Know

- `docs/d50-map.md` - canonical map of the Hillside D50 keymap (layers, combos, behaviors, emitted chords).
- `config/base.keymap` - core layers, behaviors, macros.
- `config/hillside_d50.keymap` - D50 layer wrapper and the 16 extra keys (primary board).
- `config/key-labels/hillside_d50.h` - D50 position labels and the shared
  physical aliases used to talk about keys with the owner.
- `scripts/layout_card.py` - generates `draw/hillside_d50-positions.{md,svg}`.
- `scripts/photo_card.py` - annotates the board photo (local Pillow tool,
  output `docs/hillside50dactyl-annotated.png`).
- `config/boards/shields/hillside_d50/` - D50 shield, dongle, and physical layout definitions.
- `config/combos.dtsi` - combo definitions.
- `config/leader.dtsi` - leader sequences.
- `config/mouse.dtsi` - pointing behavior tuning.
- `config/temper.keymap` / `config/temper.conf` - legacy Temper shield overrides.
- `config/west.yml` - pinned ZMK and module dependencies.
- `Justfile` - canonical local commands.

## Related Repository (Dotfiles)

This repo owns the physical → emitted half of the interaction model. The
handler half (OmniWM, Karabiner, Ghostty, tmux, zsh, Neovim) lives in the
chezmoi dotfiles repo at `~/.local/share/chezmoi`; start with its `AGENTS.md`.
When a change alters an emitted chord, check the handler side before finalizing.

## Changing a Binding

1. Identify the physical origin: layer, key-position label, combo, or leader sequence.
2. Trace the chord: physical key/layer → emitted chord → global interceptor (Karabiner/OmniWM/Ghostty) → application action.
3. Pick a single owner for the change; do not duplicate logic across ZMK and handler configs.
4. Edit with helper macros only (see rules above). Note D50 quirks: extras are layer-independent and the left bottom thumbs are hardcoded in `hillside_d50.keymap` (`docs/d50-map.md`).
5. Verify: `just draw-d50`, then `just build hillside` (or the specific target).
6. If the cross-tool contract changed, update `docs/d50-map.md` and the dotfiles `AGENTS.md`.

## Cursor and Copilot Rules Check

- `.cursor/rules/`: not present.
- `.cursorrules`: not present.
- `.github/copilot-instructions.md`: not present.
- Therefore, `AGENTS.md`, `CLAUDE.md`, and in-repo conventions are the operative agent rules.

## Recommended Agent Workflow

1. Read `AGENTS.md`, `CLAUDE.md`, `docs/d50-map.md`, and target files before editing.
2. Implement changes using helper macros and existing patterns.
3. Run focused validation (`just build <target>`, `just draw-d50`, and/or `just draw`).
4. If tests exist for your area, run one case with `just test <testpath>`.
5. Report what changed, what was run, and any follow-up needed.
