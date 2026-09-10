# Migrating the custom shields from `chosen zmk,kscan` to `zmk,physical-layout`

Research note, 2026-09-10. Applies to branch `physical-layout-migration`, based on
`058f547`. Pinned sources: ZMK `641514a97db345f499dd50b0360e594270f008fe`
(`config/west.yml:36`), Zephyr `10ba6d0c` (v4.1.0+zmk-fixes), zmk-helpers
`95edb8f15ef1d1bd8332810555f8cf5837fbdd27`. Sections 1–7 are research; section 8
was applied on this branch. Everything below was verified against the local west
workspace (`zmk/`, `zephyr/`, `modules/`) unless marked **unverified**.

## TL;DR

- The build warning `Deprecated symbol KSCAN is enabled.` is Zephyr's Kconfig
  deprecation for its `KSCAN` symbol. ZMK's `ZMK_KSCAN` is `default y` and
  `select KSCAN`, so **the warning survives a physical-layout migration**; it is
  upstream cosmetic noise, not a signal about `chosen zmk,kscan`.
- `chosen zmk,kscan = &kscan0;` is **not deprecated**. Physical layouts use it
  as a fallback when a layout omits `kscan`; official split shields (corne, etc.)
  still set both `zmk,kscan` and `zmk,physical-layout` in `chosen`
  (`zmk/app/boards/shields/corne/corne.dtsi:9-24`).
- The old "physical layout broke split BLE" surprise is explained by ZMK history:
  PR #2397 (Sep 2024) caused BT signing failures on mismatched firmware
  (issue #2461), was reverted via #2462, and re-landed as #2482 with a
  security-gated write. All of that is in the pinned revision. Issue #3156 is a
  *different*, still partially open dongle GATT-discovery race; our dongle
  enables battery fetching, so it remains a confounder for hardware retests.
- Recommended migration: put one `zmk,physical-layout` node in
  `hillside_d50-layouts.dtsi` (no `kscan` property), include it from
  `hillside_d50_common.dtsi` so all five H50 targets see the same node, mirror
  a minimal layout in `temper_common.dtsi`, keep `chosen zmk,kscan = <local
  kscan>` in each part, and delete every `chosen zmk,matrix_transform`. Reusing
  one layout means split layout index 0 everywhere and no position-map work.
- Also drop the local `KEYS_L`/`KEYS_R`/`THUMBS` from `config/base.keymap`
  (upstream did the same in `395f46b`) after adding group macros to
  `config/key-labels/hillside_d50.h`; this also removes the current
  `"THUMBS" redefined` warning on Temper builds.

## 1. Exact DTS syntax for a `zmk,physical-layout` node

Binding file: `zmk/app/dts/bindings/zmk,physical-layout.yaml:10-29`.

| Property | Type | Required | Notes |
| --- | --- | --- | --- |
| `compatible` | string | yes (implicit) | `"zmk,physical-layout"` |
| `display-name` | string | yes (`required: true`) | UI name |
| `transform` | phandle | yes (`required: true`) | matrix transform for this layout |
| `kscan` | phandle | no | chosen `zmk,kscan` fallback if omitted |
| `input` | phandle | no | Input device; chosen `zmk,matrix-input` is the fallback |
| `keys` | phandle-array | no | key physical attributes; required for ZMK Studio |

The `keys` elements have the shape `<&key_physical_attrs w h x y r rx ry>`.
`display-name` and `transform` are the only `required: true` properties; the
`kscan`/`input` fallbacks are spelled out in
`zmk/app/dts/bindings/zmk,physical-layout.yaml:21-26`. The
`key_physical_attrs` node lives in `zmk/app/dts/physical_layouts.dtsi:8-11` and
must be pulled in with:

```dts
#include <physical_layouts.dtsi>
```

as done today in `config/boards/shields/hillside_d50/hillside_d50-layouts.dtsi:1`.
Rotation cells are only stored when `CONFIG_ZMK_PHYSICAL_LAYOUT_KEY_ROTATION` is
set; it defaults to `y` (`zmk/app/Kconfig:515-517`).

Current repo layout node for reference
(`config/boards/shields/hillside_d50/hillside_d50-layouts.dtsi:19-24`):

```dts
physical_layout0: physical_layout_0 {
    compatible = "zmk,physical-layout";
    display-name = "Default Layout";
    kscan = <&kscan0>;                 // must be dropped for the dongle
    transform = <&default_transform>;
    keys = ...;
};
```

Official examples: `zmk/app/boards/shields/a_dux/a_dux-layouts.dtsi` (keys +
transform assigned in `a_dux.dtsi:9-21`), and the shared corne layouts imported
from `zmk/app/dts/layouts/foostan/corne/{5,6}column.dtsi` and used by
`zmk/app/boards/shields/corne/corne.dtsi:8-24`.

## 2. How the active layout is selected (central/peripheral/dongle)

Source: `zmk/app/src/physical_layouts.c`.

- Physical layouts are used only when at least one `zmk,physical-layout` node is
  `okay` **and** no `chosen zmk,matrix_transform` exists:

  ```c
  #define USE_PHY_LAYOUTS \
      (DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT) && !DT_HAS_CHOSEN(zmk_matrix_transform))
  ```

  (`physical_layouts.c:41-42`)
- Initial layout: `chosen zmk,physical-layout = &<layout>;` if present, otherwise
  the first node in DTS order (`physical_layouts.c:305-315`). A `.keymap` can
  override the shield's `chosen` (section 7).
- `kscan` per layout: the layout macro resolves `kscan` from the layout property
  or falls back to `chosen zmk,kscan` (`physical_layouts.c:86-90`). Same pattern
  for `input` and `chosen zmk,matrix-input`.
- Every part that has a keyboard matrix must define an active kscan. A dongle
  still needs a kscan; its mock kscan is selected through
  `chosen zmk,kscan = &mock_kscan;` and a layout that does not hard-code a kscan.
  ZMK's dongle guide says exactly this: "If the `kscan` property is set on the
  physical layout node, remove it so the dongle uses the mock kscan instead"
  (`zmk/docs/docs/hardware-integration/dongle.mdx:190-243`).
- `zmk,matrix_transform` chosen still exists and still wins at runtime, but only
  by *disabling* physical layouts: `physical_layouts.c:143-160` emits a compile
  warning `"Ignoring the physical layouts and using the chosen matrix transform.
  Consider setting a chosen physical layout instead."`. One subtlety: if any
  physical layout node exists, `ZMK_KEYMAP_LEN` is computed from the physical
  layouts' transforms even when the chosen transform is used
  (`zmk/app/include/zmk/matrix.h:14-25`). Do not mix the two schemes.
- Split behavior: on connect, the central discovers the peripheral's "select
  physical layout" characteristic (`service.c:205-209`), and after the
  characteristic is found and security reaches L2, writes the central's selected
  index to each peripheral (`central.c:498-536`, `central.c:989-1003`,
  `central.c:1161-1168`). The peripheral applies it via
  `zmk_physical_layouts_select()` (`zmk/app/src/split/peripheral.c:61`,
  `service.c:106-141`). Because positions are computed on the peripheral with its
  own active layout, **all parts must enumerate the same layouts in the same
  order**. ZMK's dongle docs stress this (`dongle.mdx:116` and `:154-158`), and
  PR #3405 (merged 2026-07-17, in the pinned revision) reiterates it.
  Mismatched include order is a real reported footgun: see
  <https://github.com/perrwa/zmk-config/pull/31> (position scramble because the
  central's layout index 1 resolved to the peripheral's 5-column transform).
- Studio persists a selection under the settings key `physical_layouts/selected`
  (`physical_layouts.c:407-440`, `:526-548`); split/dongle changes can leave a
  stale index in NVS, which `settings_reset` clears.

## 3. The `Deprecated symbol KSCAN is enabled` warning

- The text comes from Zephyr's Kconfig deprecation check:
  `zephyr/scripts/kconfig/kconfig.py:248-257` warns for any symbol selecting
  `DEPRECATED`.
- `CONFIG_KSCAN` does exactly that: `menuconfig KSCAN` ... `select DEPRECATED`
  (`zephyr/drivers/kscan/Kconfig:6-8`).
- ZMK turns it on unconditionally: `menuconfig ZMK_KSCAN` is `default y` and
  `select KSCAN` (`zmk/app/Kconfig:519-522`); the sideband-behavior integration
  also selects it (`zmk/app/Kconfig:532-536`). There is no condition on chosen
  nodes, so any ZMK build warns.
- Reproduced locally on the pinned revision: `nix develop --command just build
  hillside_d50_dongle` prints `warning: Deprecated symbol KSCAN is enabled.`
  during Kconfig parsing, and the generated `.config` contains `CONFIG_KSCAN=y`
  and `CONFIG_ZMK_KSCAN=y`. Removing `chosen zmk,kscan` would disable kscan
  drivers, so the warning cannot be fixed in this repo. Upstream `main` fetched
  2026-09-10 still has `ZMK_KSCAN default y select KSCAN`.
- The stale/replaced chosen nodes behave as follows at the pinned revision:
  `zmk,kscan` is fully supported (fallback path above, plus
  `matrix.h:11` / `matrix_transform.c:62`), and `zmk,matrix_transform` is still
  tolerated but warns when physical layouts also exist. Nothing in
  `physical_layouts.c` removes or deprecates the chosen kscan handling.

## 4. The previous split-BLE surprise

### 4.1 Local history

There is **no committed physical-layout attempt or revert** in this repo.
`git log --all -S "zmk,physical-layout"` and `-S "physical_layout"` only find the
draw-tooling layout file and `config/corneish_zen.keymap`. The only record is the
code comment added in `2fa96df` (2026-05-04, "add hillside"):

```
config/boards/shields/hillside_d50/hillside_d50_common.dtsi:7-10
We deliberately use the older chosen `zmk,kscan` + `zmk,matrix_transform`
approach (mirroring temper's working dongle setup) instead of
zmk,physical-layout -- Studio support isn't needed and physical-layout
has surprised us in split BLE mode.
```

The external handoff note of the same work (`zmk-upstream-migration-handoff.md`,
item 6) repeats it without a date or log. Treat the original failure as
**unverified**, but ZMK's own history offers the two most likely causes below.

### 4.2 ZMK history: physical layout selection sync (2024)

- `feat: Split physical layout selection sync` first merged as PR #2397
  (2024-09-06, commit `03b5b38b`). It made centrals write the selected layout to
  peripherals on connect.
- That immediately broke real splits: issue #2461 reports `bt_att: Error signing
  data` and one half dying when the other powered on, on firmware where only the
  central had the new feature. PR #2462 reverted it the next day (2024-09-07,
  `d52bb040`).
- Re-landed as PR #2482 (2024-09-23, commit `33e3b02d`) with the fix "only
  updating the peripheral physical layouts when we're sure the security is all
  set on the connection". That is the code in the pinned revision
  (`central.c:989-1003` checks `bt_conn_get_security >= BT_SECURITY_L2` and
  retries on `security_changed`).
- Conclusion: the "split BLE surprise" from 2024 is obsolete on the pinned
  revision if **all parts are flashed together**. Flashing new central firmware
  against old peripheral firmware can still produce version-skew problems
  (re-pair/`settings_reset` if that happens), but that is true for any split
  feature.

### 4.3 Issue #3156 (dongle discovery race)

- <https://github.com/zmkfirmware/zmk/issues/3156> (opened 2025-12-20, closed
  2026-02-18): in a dongle + 2 peripherals setup with
  `CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING=y`, one peripheral
  connects but never types. Cause: subscribing to the battery characteristic
  mid-discovery starts a nested CCC discovery that aborts the remaining
  characteristic walk, so the position-state characteristic is never subscribed.
  `select physical layout` is part of the same walk (the issue log shows it
  sometimes missing too).
- Partial fix merged: PR #3216 (2026-02-18, merge `9490391e`) sets
  `BT_ATT_TX_COUNT default 10 if ZMK_SPLIT_ROLE_CENTRAL`
  (`zmk/app/src/split/bluetooth/Kconfig:24-26`), which **is** in the pinned
  revision. The issue was closed by it.
- Full fix open: PR #3411 "Defer GATT subscriptions until discovery completes"
  (<https://github.com/zmkfirmware/zmk/pull/3411>) is still open as of
  2026-09-10 (`"state": "open", "merged": false`); its own 2026-07-15 update says
  it "hasn't completely solved the issue". Not in the pinned revision
  (`central.c` still subscribes inside `split_central_chrc_discovery_func`).
- Relevance to this migration: **the bug is not caused by physical layouts** and
  existed while the repo was on chosen kscan. But our dongle enables battery
  fetching via the `prospector_adapter` shield
  (`modules/zmk/prospector/boards/shields/prospector_adapter/Kconfig.defconfig:3-4`;
  target at `build.yaml:35-37`), so a hardware retest can still hit "one half
  deaf" independently. If that symptom appears after migrating, A/B it by
  setting `CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING=n` on the dongle
  (cost: no peripheral battery levels on the Prospector screen).

### 4.4 Other open physical-layout issues (context only)

- #2479 "Physical layouts' kscan drivers may conflict when CONFIG_PM_DEVICE=n"
  (open): multiple layouts with different kscans both initialize if PM device
  runtime is off. Our dongle sets `CONFIG_PM_DEVICE=n` in
  `hillside_d50_dongle.conf`, but a single layout / single kscan avoids this.
  Do not add alternate kscan-backed layouts on the dongle without enabling
  `PM_DEVICE`.
- #3228 "Combos are not renumbered using position_map with alternative layouts"
  (open): only meaningful with more than one layout. A single layout avoids it.
- #3156 is therefore "partially relevant": the layout characteristic lives in
  the same GATT walk, but the failure mode is battery-fetch related.

## 5. zmk-helpers group macros (`KEYS_L`, `KEYS_R`, `THUMBS`)

At the pinned zmk-helpers revision, every key-label header now defines the HRM
group macros in addition to the `LT*/LM*/LB*` position labels. Added by
`Add group macros to layouts (#100)` (commit `026a4c1`, 2026-03-04):

- `modules/zmk/helpers/include/zmk-helpers/key-labels/36.h:55-61`:
  `KEYS_L`, `KEYS_R`, `THUMBS_L LH0 LH1 LH2`, `THUMBS_R RH0 RH1 RH2`,
  `THUMBS THUMBS_L THUMBS_R`.
- 34-key `34.h:55-59` defines `LH0/LH1`, `RH0/RH1` and no `LH2`; its `THUMBS`
  is just the four thumb keys. This is what the legacy `#ifndef LH2` switch in
  `config/base.keymap:49-55` was emulating.
- `4x12_wide.h:61-65` and `glove80.h:124-128` follow the same pattern for their
  layouts.
- `helper.h` does not define them; the keymap must include its layout header
  before `base.keymap` (all current keymaps do: `config/hillside_d50.keymap:40-41`,
  `config/temper.keymap:12-13`, `config/temper_dongle.keymap`,
  `config/corneish_zen.keymap:11`, `config/glove80.keymap:14`,
  `config/planck_rev6.keymap:10`).

Consequences for this repo:

- Upstream urob deleted the local block in `395f46b` "Remove redundant keydefs"
  (2026-04-14, referencing zmk-helpers PR #100). Our fork of `base.keymap`
  still contains it (fork divergence).
- The current local `THUMBS` order (`LH2 LH1 LH0 RH0 RH1 RH2`) differs from
  `36.h`'s order, so Temper builds already emit a macro redefinition warning:
  reproduced locally with `nix develop --command just build temper_dongle`,
  which prints `config/base.keymap:54: warning: "THUMBS" redefined`.
  `hold-trigger-key-positions` is order-insensitive, so switching to the header
  definition is behavior-neutral.
- Hillside D50 cannot use `hillside46.h`/`hillside52.h`: D50 positions differ
  from `hillside46.h` from position 30 onward (raised pairs at 36-43 and lower
  thumbs at 44-49; local labels in `config/key-labels/hillside_d50.h:37-79`).
  Keep the local header and add the group macros there, mirroring the upstream
  header style, before deleting the block from `base.keymap`.

## 6. Reference implementations

- Official split shields now use physical layouts widely (28 in-tree shield
  directories, 47 files). Canonical patterns:
  - `corne.dtsi:8-24`: shared layouts imported, `&layout { transform = ...; }`,
    `chosen { zmk,kscan = &kscan0; zmk,physical-layout = &foostan_corne_6col_layout; }`,
    no `zmk,matrix_transform`.
  - `a_dux.dtsi:9-21`: dedicated `a_dux-layouts.dtsi` with `keys`, transform
    assigned from the shield file, both chosen nodes.
  - `jorne.dtsi` + `jorne-layouts.dtsi`: multiple layouts with position maps.
- Search for a mock-kscan dongle shield in tree: only
  `zmk/app/boards/shields/settings_reset/settings_reset.overlay:10-19` uses
  `zmk,kscan-mock`; there is no in-tree dongle shield. The mock-kscan dongle
  recipe is documented in `dongle.mdx:113-158` and matches our current overlay
  (`hillside_d50_dongle.overlay:9-20`, `temper_dongle.overlay:3-15`).
- `urob/zmk-config` (remote `upstream`) has no custom shields; its only
  layout-selection usage is `config/corneish_zen.keymap:14`
  (`/{ chosen { zmk,physical-layout = &foostan_corne_5col_layout; }; };`) and its
  `base.keymap` relies on header-provided group macros (commit `395f46b`).

## 7. Keymap-side selection

- Build-time selection is a devicetree `/ { chosen { ... }; };` override. A
  `.keymap` can select among layouts:

  ```dts
  /{ chosen { zmk,physical-layout = &physical_layout0; }; };
  ```

  seen in `config/corneish_zen.keymap:14` and documented in
  `zmk/docs/docs/hardware-integration/physical-layouts.md`. Keymap overlays are
  applied after shield overlays, so the keymap `chosen` wins.
- There is no keycode behavior to switch layouts at the pinned revision; runtime
  selection happens through ZMK Studio
  (`zmk/app/src/studio/keymap_subsystem.c:333-358`) or the split sync write from
  the central (`service.c:106-141`).
- Our D50 and Temper keymaps each need only one layout, so no keymap change is
  required; the shield's `chosen` is enough.

## 8. Migration recipe

Design: one layout per board, defined once in a shared file that every part
includes. The layout deliberately omits `kscan`, so each part's
`chosen zmk,kscan` supplies the right device (real matrix on halves, mock on the
dongle). Every `chosen zmk,matrix_transform` is removed.

### 8.1 Hillside D50

`config/boards/shields/hillside_d50/hillside_d50-layouts.dtsi`

- Delete line 23: `kscan = <&kscan0>;`.
- Keep `compatible`, `display-name`, `transform = <&default_transform>;`, `keys`.
- Update the comment block (lines 3-17): the file is now included by
  `hillside_d50_common.dtsi` for firmware builds and passed to keymap-drawer by
  `just draw-d50`; `kscan` is intentionally omitted so each part uses its chosen
  kscan (left/right: `&kscan0`; dongle: `&mock_kscan`).

`config/boards/shields/hillside_d50/hillside_d50_common.dtsi`

- After `#include <dt-bindings/zmk/matrix_transform.h>`, add:

  ```dts
  #include "hillside_d50-layouts.dtsi"
  ```

- Rewrite the comment at lines 7-10 (the old rationale no longer applies).

`config/boards/shields/hillside_d50/hillside_d50.dtsi`

- Replace the chosen block (lines 8-12) with:

  ```dts
  chosen {
      zmk,kscan = &kscan0;
      zmk,physical-layout = &physical_layout0;
  };
  ```

- Keep `kscan0` unchanged. `_left_dongle`/`_right_dongle` inherit this file and
  need no change.

`config/boards/shields/hillside_d50/hillside_d50_dongle.overlay`

- Replace the chosen block (lines 9-13) with:

  ```dts
  chosen {
      zmk,kscan = &mock_kscan;
      zmk,physical-layout = &physical_layout0;
  };
  ```

- Keep `mock_kscan` unchanged. `hillside_d50_common.dtsi` already brings in the
  layout.

### 8.2 Temper

`config/boards/shields/temper/temper_common.dtsi`

- Add below `default_transform` (no `keys`; Studio is off, and Temper stays
  kscan-only):

  ```dts
  physical_layout0: physical_layout_0 {
      compatible = "zmk,physical-layout";
      display-name = "Default Layout";
      transform = <&default_transform>;
  };
  ```

  If a separate `temper-layouts.dtsi` is preferred for convention, create it and
  include from common; either works because no draw tooling consumes it.

`config/boards/shields/temper/temper.dtsi`

- Chosen becomes `zmk,kscan = &kscan0;` + `zmk,physical-layout = &physical_layout0;`
  (drop `zmk,matrix_transform` at line 13). Keep `zephyr,display` and `kscan0`.
- `temper_left_dongle`/`temper_right_dongle` inherit and need no change.

`config/boards/shields/temper/temper_dongle.overlay`

- Chosen becomes `zmk,kscan = &mock_kscan;` + `zmk,physical-layout = &physical_layout0;`
  (drop `zmk,matrix_transform` at line 6). The file includes
  `temper_common.dtsi`, so the layout is present.

### 8.3 Keymap macros

`config/key-labels/hillside_d50.h`

- Add group macros at the bottom (keep current membership/order to make the
  change behavior-neutral):

  ```c
  #define KEYS_L LT0 LT1 LT2 LT3 LT4 LM0 LM1 LM2 LM3 LM4 LB0 LB1 LB2 LB3 LB4
  #define KEYS_R RT0 RT1 RT2 RT3 RT4 RM0 RM1 RM2 RM3 RM4 RB0 RB1 RB2 RB3 RB4
  #define THUMBS_L LH2 LH1 LH0
  #define THUMBS_R RH0 RH1 RH2
  #define THUMBS THUMBS_L THUMBS_R
  ```

`config/base.keymap`

- Delete the block at lines 49-55 (`#define KEYS_L ...`, `#define KEYS_R ...`,
  `#ifndef LH2 ... #endif`). The macros now come from the layout header each
  keymap includes first, matching upstream `395f46b`. No other include-order
  changes are needed (verified for all six keymaps listed in section 5).

### 8.4 What stays untouched

- `build.yaml`, `Kconfig.shield`, `Kconfig.defconfig`, all `.conf` and `.zmk.yml`
  files, `config/hillside_d50.keymap`, `config/temper*.keymap`, combos/leader.
- `Justfile:94-99` (`draw-d50`) and `scripts/layout_card.py:23-26`. The draw file
  keeps `transform` and `keys`; keymap-drawer already tolerates the undefined
  `&kscan0` reference today, so removing the property cannot break parsing. The
  layout card only regexes `key_physical_attrs`.
- `hillside_d50.zmk.yml`'s `studio` feature claim: with `keys` now compiled in,
  enabling `CONFIG_ZMK_STUDIO=y` would satisfy the layout asserts
  (`physical_layouts.c:44-50`, `:71-74`). Temper would need a `keys` property
  first.

## 9. Risks, verification, rollback

### Risks

1. Mixing schemes: any part that still has `chosen zmk,matrix_transform`
   silently ignores its physical layout (`#warning`) and, because `matrix.h`
   sees the physical layout, may compute `ZMK_KEYMAP_LEN` from it. Remove the
   chosen transform from every overlay.
2. Layout order/name mismatch across split parts -> scrambled positions on
   hardware (documented failure mode; see dongle.mdx:154-158 and
   perrwa/zmk-config#31). Our design keeps a single layout in a shared file, so
   index 0 everywhere; do not add per-part layout files.
3. Stale `physical_layouts/selected` in NVS: harmless with one layout (index 0),
   but a `settings_reset` flash clears it if weirdness appears.
4. Dongle discovery race (#3156/#3411): unrelated to layouts, but a retest can
   be misattributed. A/B with `ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING=n`.
5. Future multiple layouts on the dongle with different kscans and
   `CONFIG_PM_DEVICE=n` hits #2479.
6. Flash cost: D50 `keys` (50 x 7 cells) is small but non-zero; keeping it now
   avoids a second file/divergence later.

### Build/draw verification

```bash
nix develop --command just draw-d50          # draw drift check
git diff --exit-code -- draw/                # expected: clean
nix develop --command just build hillside    # all H50 targets
nix develop --command just build temper      # all Temper targets
```

- Expected warnings: `Deprecated symbol KSCAN is enabled.` (still, by design)
  and the CMake `config/boards folder is deprecated` note. There must be **no**
  `Ignoring the physical layouts and using the chosen matrix transform` and no
  devicetree parse errors.
- Inspect `.build/<target>/zephyr/zephyr.dts`: `chosen` contains
  `zmk,physical-layout` and no `zmk,matrix_transform`; a
  `compatible = "zmk,physical-layout"` node exists on all H50 and Temper
  targets (including the dongles).
- Inspect `.config`: halves have `CONFIG_ZMK_KSCAN_GPIO_MATRIX=y`, dongle has
  `CONFIG_ZMK_KSCAN_MOCK_DRIVER=y`; dongle still has
  `CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING=y` (from the Prospector
  module) unless deliberately overridden.

### Hardware verification (two firmware sets)

1. Standalone split (left central, right peripheral): every one of the 50
   positions types the expected key (use `draw/hillside_d50-positions.md`);
   combos, HRM rolls, sticky layers, Magic Shift, leader sequences, mouse.
2. Dongle split (dongle central + both halves as peripherals): same key checks
   from each half; display/battery screens still update.
3. BLE-specific: all allowed boot orders (both halves first, dongle first);
   sleep/wake reconnect; power-cycle one half; full power cycle; reflash one
   half while the central stays powered. In logs, watch for `Discover complete`
   before `Found position state characteristic` (the #3156 signature); if it
   appears, apply the A/B in section 4.3.
4. Optional: flash `settings_reset` on all parts once before the test to clear
   stale split/layout state.

### Rollback

- `git revert` the migration commit(s) and rebuild/flash; the DTS change is
  self-contained and no firmware persistent state is migrated. If an NVS layout
  index is suspected, flash `settings_reset_{nice_nano_v2,xiao_ble}` from the
  existing `build.yaml` targets, then re-pair.
- Keep the current `firmware/*.uf2` artifacts until hardware validation passes.

## 10. Open items / unverified

- The exact original "surprised us in split BLE mode" incident is **unverified**:
  no repo commit, log, or issue reference records it. Best available explanation
  is the #2397/#2461 firmware-skew breakage or the #3156 dongle race.
- PR #3411 was open and mergeable-clean at the time of writing; re-check before
  relying on it. Its author reports partial success.
- `BT_ATT_TX_COUNT=10` is confirmed by config/source in the pinned revision, but
  whether it fully prevents #3156 on the D50 hardware is **unverified** (the
  #3411 author reports it improves rather than eliminates the failure).
- Whether the Prospector module or its LVGL usage interacts with split timing is
  outside this note.

## References

Local (pinned workspace; `zmk/` at `641514a9`):

- `zmk/app/dts/bindings/zmk,physical-layout.yaml:10-29`
- `zmk/app/dts/physical_layouts.dtsi:8-11`
- `zmk/app/src/physical_layouts.c:41-42,44-50,86-90,143-160,305-315,334-380,407-440,526-548`
- `zmk/app/include/zmk/matrix.h:11-25`; `zmk/app/src/matrix_transform.c:38-66`
- `zmk/app/Kconfig:515-522,532-536`
- `zmk/app/src/split/bluetooth/Kconfig:24-26`
- `zmk/app/src/split/bluetooth/central.c:498-536,604-616,989-1003,1161-1168`
- `zmk/app/src/split/bluetooth/service.c:106-141,205-209`
- `zmk/docs/docs/hardware-integration/physical-layouts.md`; `.../dongle.mdx:113-158,190-243`;
  `zmk/docs/docs/config/layout.md` (Physical Layout section)
- `zmk/app/boards/shields/corne/corne.dtsi:8-24`; `.../a_dux/a_dux.dtsi:9-21`;
  `.../a_dux/a_dux-layouts.dtsi`
- `zephyr/drivers/kscan/Kconfig:6-8`; `zephyr/scripts/kconfig/kconfig.py:248-257`
- `modules/zmk/helpers/include/zmk-helpers/key-labels/{34,36,4x12_wide,glove80}.h`
  (group macros), zmk-helpers commit `026a4c1`

Repo:

- `config/boards/shields/hillside_d50/hillside_d50_common.dtsi:7-10`
- `config/boards/shields/hillside_d50/hillside_d50.dtsi:8-12`
- `config/boards/shields/hillside_d50/hillside_d50_dongle.overlay:9-20`
- `config/boards/shields/hillside_d50/hillside_d50-layouts.dtsi:1-24`
- `config/boards/shields/temper/{temper.dtsi,temper_common.dtsi,temper_dongle.overlay}`
- `config/base.keymap:49-55`; `config/key-labels/hillside_d50.h:37-79`
- `config/hillside_d50.keymap:40-41`; `build.yaml:35-37`
- `Justfile:94-99`; `scripts/layout_card.py:23-26`
- `config/west.yml:36` (ZMK pin); commit `2fa96df` (origin of the split-BLE comment)
- upstream `395f46b` "Remove redundant keydefs"; `config/corneish_zen.keymap:14`

GitHub:

- <https://github.com/zmkfirmware/zmk/issues/3156> (dongle discovery, closed)
- <https://github.com/zmkfirmware/zmk/pull/3216> (partial fix, merged 2026-02-18)
- <https://github.com/zmkfirmware/zmk/pull/3411> (full fix, open)
- <https://github.com/zmkfirmware/zmk/pull/2397>, <https://github.com/zmkfirmware/zmk/pull/2462>,
  <https://github.com/zmkfirmware/zmk/pull/2482>, <https://github.com/zmkfirmware/zmk/issues/2461>
- <https://github.com/zmkfirmware/zmk/issues/2479>, <https://github.com/zmkfirmware/zmk/issues/3228>
- <https://github.com/zmkfirmware/zmk/pull/3405> (dongle docs, merged 2026-07-17)
- <https://github.com/perrwa/zmk-config/pull/31> (layout-order scramble example)
