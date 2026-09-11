# Prospector Dongle

> **Status: overhauled for ZMK 4.1.** The central dongle targets run
> [rcopra/prospector-zmk-module](https://github.com/rcopra/prospector-zmk-module)
> branch `vaporwave` (a fork of
> [carrefinho/prospector-zmk-module](https://github.com/carrefinho/prospector-zmk-module)
> `feat/new-status-screens`, pinned in `west.yml`) with the `prospector_adapter`
> shield and five selectable layouts — Classic, Field, Operator, Radii, Vaporwave.
> YADS was retired (it does not build on Zephyr 4.1); the gotchas below keep the
> parts of its history that still matter.
>
> **Legacy/fallback board.** Temper is no longer the daily driver; it is kept
> as a fallback build. The Hillside D50 uses the same dongle architecture — see
> [d50-map.md](d50-map.md) for the current board.

Working reference for the Prospector dongle (Seeed XIAO nRF52840 + ST7789V 1.69"
LCD) integrated into the Temper ZMK setup. The dongle runs the keymap as a BLE
central; both halves bond to it as peripherals.

## Display design workspace

Personal layouts are authored in `~/personal/prospector-zmk-module`, a separate
clone of the fork. Start with its [design workflow](../../prospector-zmk-module/design/README.md)
and [display rules](../../prospector-zmk-module/design/display-rules.md).
The `prospector-display` skill at `~/.agents/skills/prospector-display` guides
future layout design and debugging.

Run `just preview` in that checkout for native LVGL captures and clipping
checks, then `just firmware` for the Hillside Vaporwave build. The latter uses
a local module override and leaves the manifest pin unchanged; the workflow
document explains how to clear the cached override and publish a pinned release.

## Hardware

- Carrefinho's Prospector PCB, BOM **without** the APDS9960 ambient light sensor
  (fixed brightness used instead).
- Dongle MCU: **Seeed XIAO nRF52840** (`xiao_ble//zmk` on ZMK main / Zephyr 4.1).
- Firmware module: [carrefinho/prospector-zmk-module](https://github.com/carrefinho/prospector-zmk-module)
  `feat/new-status-screens`, pinned in `west.yml`; `prospector_adapter` shield
  provides the ST7789 driver, LVGL status screens, and themes.
- No ambient light sensor (BOM without APDS9960) → fixed brightness.

## Architecture

| | Standalone split | Dongle mode |
|---|---|---|
| USB host | left half | dongle |
| Central (runs keymap) | left | dongle |
| Left half | central | peripheral |
| Right half | peripheral | peripheral |

Consequences:

- The keyboard **does not work without the dongle plugged in**. The standalone
  `temper_left` / `temper_right` targets remain in `build.yaml` as a fallback.
- On-board nice!view displays keep working but only show peripheral-side info
  (connection status). Layer/mods/WPM live on the dongle's ST7789.
- The keymap (`base.keymap`, combos, leader, Magic Shift) is unchanged — it
  runs on the dongle, halves just report key positions.

## Build targets

```bash
cd zmk-workspace
just sync                          # pulls the Prospector module into modules/
just build temper_dongle           # dongle firmware (XIAO)
just build temper_left_dongle      # left half as peripheral
just build temper_right_dongle     # right half as peripheral
just build settings_reset          # optional bond-wipe one-shots
```

Artifacts land in `zmk-workspace/firmware/`.

## Flash + pair

First time:

1. Unplug both halves.
2. Plug the dongle into USB. It advertises as a scanning BLE central.
3. Flash `temper_left_dongle.uf2` → left (double-tap reset on the nice_nano,
   drag UF2 onto `NICENANO` drive). It advertises; dongle discovers → slot 0.
4. Flash `temper_right_dongle.uf2` → right. Slot 1.
5. Type into any text field on the Mac to verify.

Flashing left first keeps slot 0 = left on the dongle screen's battery indicators.

If anything refuses to bond, flash `settings_reset_nice_nano_v2.uf2` onto the
stuck half (or `settings_reset_xiao_ble.uf2` on the dongle), wait ~5s, then
reflash the normal firmware over it. The `CONFIG_BT_SMP_ALLOW_UNAUTH_OVERWRITE`
flag in `config/temper.conf` means you rarely need this — stale bonds are
overwritten automatically.

### Reverting to standalone split

1. Flash `temper_left+nice_view_adapter+nice_view-nice_nano@2.0.0__zmk.uf2` onto left.
2. Flash `temper_right+nice_view_adapter+nice_view-nice_nano@2.0.0__zmk.uf2` onto right.
3. The halves re-pair to each other on boot.

## Gotchas learned the hard way

### CDC ACM + USB HID composite breaks HID on Zephyr 3.5

**Do not enable `CONFIG_USB_CDC_ACM=y` on the dongle.** On ZMK v0.3 / Zephyr
3.5 with the XIAO board, adding CDC alongside HID in the USB composite
descriptor causes HID to never reach the `USB_DC_CONFIGURED` state. Symptom:
device enumerates on macOS, `ioreg` shows the device node but no child
interfaces, keys route to BLE (with `Not sending, not connected to active
profile` warnings), typing doesn't work.

CDC was useful for debugging with `tio`, but it has to come out before the
firmware is usable. If you need logs again, consider Segger RTT over SWD
instead, or temporarily disable HID. Not re-verified on ZMK 4.1 — if you
re-add CDC for debugging, check HID enumeration first.

### `cmake-args:` support

The Justfile now parses `cmake-args` from `build.yaml` (synced from upstream),
so the shortcut works. We still use real shield variants
(`temper_left_dongle`, `temper_right_dongle`) to override
`ZMK_SPLIT_ROLE_CENTRAL=n` — no reason to revisit a working setup.

### `temper_common.dtsi` exists because of XIAO vs nice_nano labels

`temper.dtsi` references `&pro_micro_i2c` for the on-board SSD1306. That
label exists on nice_nano but not on xiao_ble, so including
`temper.dtsi` from the dongle overlay fails at DT parse. The matrix transform
is extracted into `temper_common.dtsi` so the dongle overlay can pull only
the transform without dragging in nice_nano-specific nodes.

### Peripheral position via `col-offset`, not Kconfig

Peripherals self-identify through the `col-offset` in their shield's matrix
transform — left defaults to 0, right overrides to 5. Bond order doesn't affect
keymap correctness; it only affects which slot shows which battery bar on the
dongle screen.

## File layout

| File | Role |
|---|---|
| `config/west.yml` | Prospector module added |
| `config/temper.conf` | `BT_SMP_ALLOW_UNAUTH_OVERWRITE` for re-pairing |
| `config/temper_dongle.keymap` | Keymap entry point for the dongle |
| `config/boards/shields/temper/Kconfig.shield` | Registers dongle + peripheral shields |
| `config/boards/shields/temper/Kconfig.defconfig` | Role + keyboard name per shield |
| `config/boards/shields/temper/temper_common.dtsi` | Shared matrix transform |
| `config/boards/shields/temper/temper.dtsi` | nice_nano OLED + kscan, includes common |
| `config/boards/shields/temper/temper_dongle.overlay` | Mock kscan, includes common only |
| `config/boards/shields/temper/temper_dongle.conf` | 2 peripherals, no sleep, Prospector flags |
| `config/boards/shields/temper/temper_left_dongle.overlay` | Left half, peripheral role |
| `config/boards/shields/temper/temper_right_dongle.overlay` | Right half, peripheral role |
| `build.yaml` | Central dongle + peripheral + settings-reset targets |

The Hillside D50 mirrors this layout under `config/boards/shields/hillside_d50/`
with the same `.conf` knobs.

## Prospector config knobs

Set in `config/boards/shields/{temper,hillside_d50}/*_dongle.conf`; the module
[README](https://github.com/carrefinho/prospector-zmk-module/tree/feat/new-status-screens)
has the full list. Notable ones:

- `CONFIG_PROSPECTOR_STATUS_SCREEN_{CLASSIC,FIELD,OPERATOR,RADII,VAPORWAVE}` —
  layout choice; Classic is the default. Vaporwave is selected by the
  `hillside_d50_dongle_vaporwave` target in `build.yaml` via `cmake-args`
  (Vaporwave is only defined in the fork); the standard dongle target stays on
  Classic unless one option here is uncommented.
- `CONFIG_PROSPECTOR_ROTATE_DISPLAY_180` — 180° rotate (set: `y`)
- `CONFIG_PROSPECTOR_USE_AMBIENT_LIGHT_SENSOR` — set `n` on this BOM
- `CONFIG_PROSPECTOR_FIXED_BRIGHTNESS` — 1–100 when the sensor is off
- `CONFIG_PROSPECTOR_SHOW_MODIFIERS`,
  `CONFIG_PROSPECTOR_SHOW_INACTIVE_MODIFIERS`, `CONFIG_PROSPECTOR_MODIFIER_ORDER`
  (`GACS`), `CONFIG_PROSPECTOR_MODIFIER_OS_{GENERIC,WINDOWS,MAC}` (set: `MAC`)
- `CONFIG_PROSPECTOR_LAYER_NAME_UPPERCASE`
- If the build reports a RAM overflow: `CONFIG_LV_Z_VDB_SIZE=25`

The new module has no screen-idle timeout and no keyboard-controlled
brightness, so the reserved F22–F24 keys are currently unused by the dongle.
