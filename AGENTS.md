# AGENTS.md

Guidance for coding agents working in this `zmk-config` repository.

## Repository Profile

- Project type: ZMK firmware configuration (not a general application codebase).
- Primary domain: Devicetree keymap/config files, shield definitions, and build automation.
- Upstream base: `urob/zmk-config` patterns and helpers.
- Target user environment: macOS and Linux (no Windows assumptions).

## Source of Truth

- Read `CLAUDE.md` first; it contains project-specific constraints and keyboard layout context.
- Respect the existing macro-heavy style from `zmk-helpers`.
- Prefer existing repository conventions over generic ZMK examples.

## Build, Test, and Validation Commands

Run from repo root. Use `nix develop` when tools are unavailable on host.

### Environment setup

- `direnv allow` - activate pinned Nix dev environment automatically.
- `just init` - initialize west workspace (`.west`, `zmk`, `zephyr`, modules).
- `just update` - update west dependencies from pinned manifest.

### Build commands

- `just list` - list valid build targets from `build.yaml`.
- `just build temper` - build configured Temper targets.
- `just build all` - build every target in `build.yaml`.
- `just build <expr>` - build targets matching expression.
- `just clean` - remove `.build` and `firmware` artifacts.
- `just clean-all` - remove all generated west/zmk workspace content too.

### Draw/visualization

- `just draw` - regenerate keymap artifacts in `draw/`.

### Test commands

- `just test <testpath>` - run one test case from a test directory.
  - This recipe builds `native_posix_64` firmware for that test config and diffs logs.
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
- `nix develop --command just build planck`
- `nix develop --command just draw`

These mirror `.github/workflows/test-build-env.yml`.

## Lint/Format Reality

- No dedicated lint target exists in `Justfile`.
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

- `config/base.keymap` - core layers, behaviors, macros.
- `config/combos.dtsi` - combo definitions.
- `config/leader.dtsi` - leader sequences.
- `config/mouse.dtsi` - pointing behavior tuning.
- `config/temper.keymap` / `config/temper.conf` - shield-specific overrides.
- `config/west.yml` - pinned ZMK and module dependencies.
- `Justfile` - canonical local commands.

## Cursor and Copilot Rules Check

- `.cursor/rules/`: not present.
- `.cursorrules`: not present.
- `.github/copilot-instructions.md`: not present.
- Therefore, `CLAUDE.md` and in-repo conventions are the operative agent rules.

## Recommended Agent Workflow

1. Read `CLAUDE.md` and target files before editing.
2. Implement changes using helper macros and existing patterns.
3. Run focused validation (`just build <target>` and/or `just draw`).
4. If tests exist for your area, run one case with `just test <testpath>`.
5. Report what changed, what was run, and any follow-up needed.
