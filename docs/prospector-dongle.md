# Prospector Dongle

Working reference for the Prospector dongle (Seeed XIAO nRF52840 + ST7789V 1.69"
LCD) integrated into the Temper ZMK setup. The dongle runs the keymap as a BLE
central; both halves bond to it as peripherals.

## Hardware

- Carrefinho's Prospector PCB, BOM **without** the APDS9960 ambient light sensor
  (fixed brightness used instead).
- Dongle MCU: **Seeed XIAO nRF52840** (`seeeduino_xiao_ble` board on ZMK v0.3).
- Firmware module: [janpfischer/zmk-dongle-screen](https://github.com/janpfischer/zmk-dongle-screen)
  (YADS), `main` branch — pinned to ZMK v0.3 / Zephyr 3.5 alongside the rest of
  our `west.yml`.

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
just update                        # pulls YADS into modules/
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

1. Flash `temper_left+nice_view_adapter+nice_view-nice_nano_v2.uf2` onto left.
2. Flash `temper_right+nice_view_adapter+nice_view-nice_nano_v2.uf2` onto right.
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
instead, or temporarily disable HID.

### `cmake-args:` in `build.yaml` is silently ignored by urob's Justfile

The Justfile parses `[.board, .shield, .snippet, .artifact-name]` and drops
`cmake-args`. We use real shield variants (`temper_left_dongle`,
`temper_right_dongle`) to override `ZMK_SPLIT_ROLE_CENTRAL=n` instead of the
cmake-args shortcut the ZMK docs suggest.

### `temper_common.dtsi` exists because of XIAO vs nice_nano labels

`temper.dtsi` references `&pro_micro_i2c` for the on-board SSD1306. That
label exists on nice_nano but not on seeeduino_xiao_ble, so including
`temper.dtsi` from the dongle overlay fails at DT parse. The matrix transform
is extracted into `temper_common.dtsi` so the dongle overlay can pull only
the transform without dragging in nice_nano-specific nodes.

### Peripheral position via `col-offset`, not Kconfig

ZMK v0.3 has no `CONFIG_ZMK_SPLIT_BLE_PERIPHERAL_POSITION`. Peripherals
self-identify through the `col-offset` in their shield's matrix transform —
left defaults to 0, right overrides to 5. Bond order doesn't affect keymap
correctness; it only affects which slot shows which battery bar on the dongle
screen.

## File layout

| File | Role |
|---|---|
| `config/west.yml` | YADS module added |
| `config/temper.conf` | `BT_SMP_ALLOW_UNAUTH_OVERWRITE` for re-pairing |
| `config/temper_dongle.keymap` | Keymap entry point for the dongle |
| `config/boards/shields/temper/Kconfig.shield` | Registers dongle + peripheral shields |
| `config/boards/shields/temper/Kconfig.defconfig` | Role + keyboard name per shield |
| `config/boards/shields/temper/temper_common.dtsi` | Shared matrix transform |
| `config/boards/shields/temper/temper.dtsi` | nice_nano OLED + kscan, includes common |
| `config/boards/shields/temper/temper_dongle.overlay` | Mock kscan, includes common only |
| `config/boards/shields/temper/temper_dongle.conf` | 2 peripherals, no sleep, YADS flags |
| `config/boards/shields/temper/temper_left_dongle.overlay` | Left half, peripheral role |
| `config/boards/shields/temper/temper_right_dongle.overlay` | Right half, peripheral role |
| `build.yaml` | All 5 dongle-mode targets + 2 settings-reset targets |

## YADS config knobs

Set in `config/boards/shields/temper/temper_dongle.conf`. Other options live in
the YADS [README](https://github.com/janpfischer/zmk-dongle-screen) — notable
ones:

- `CONFIG_DONGLE_SCREEN_IDLE_TIMEOUT_S` — 0 = never off (default 600)
- `CONFIG_DONGLE_SCREEN_BRIGHTNESS_KEYBOARD_CONTROL` — keymap-driven brightness
  via F22/F23/F24
- `CONFIG_DONGLE_SCREEN_FLIPPED` — 180° rotate
- `CONFIG_DONGLE_SCREEN_{WPM,MODIFIER,LAYER,OUTPUT,BATTERY}_ACTIVE` — toggle
  individual widgets
