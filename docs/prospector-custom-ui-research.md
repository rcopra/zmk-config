# Custom Prospector UI research

> Update 2026-09-10: implemented. The Vaporwave layout lives on
> [rcopra/prospector-zmk-module](https://github.com/rcopra/prospector-zmk-module)
> branch `vaporwave` (pinned in `config/west.yml`); the
> `hillside_d50_dongle_vaporwave` target in `build.yaml` selects it via
> `cmake-args`.

Investigated 2026-09-10 against the local module pinned at
`ed98221f3b52b7066dbb10ba3af8a29150b93a5a` and the linked
[`feat/new-status-screens` branch][branch]. No firmware changes or fresh builds
were made. The branch describes itself as work in progress for Zephyr 4.1.

## What is practical

An original status screen is feasible: the module already supplies display
hardware support and keyboard-state widgets. The UI is C using LVGL. A new
composition therefore means changing firmware source, building and flashing;
there is no existing HTML/CSS or JSON screen loader. The local manifest pins
LVGL `f1db87ee98f1810328a8419572fa42a3b5f352ae`, whose version header identifies
it as **9.3.0-dev**. Match that checkout when writing UI code or generating
assets. Sources: [manifest](../config/west.yml), [LVGL version][lvgl-version],
[screen implementation][radii-screen], [build wiring][cmake].

| Desired change | Work required |
| --- | --- |
| Select Classic, Field, Operator or Radii | Set one `CONFIG_PROSPECTOR_STATUS_SCREEN_*` option and rebuild. |
| Brightness, rotation, modifier ordering/style/visibility | Existing `.conf` options; no new C. |
| Change Radii's palette | Devicetree theme selection or palette overrides; no new C. |
| Rearrange widgets, change fonts, add a new visual style | LVGL C changes in the module. |
| Switch between designs from a key at runtime | New navigation/state handling and build changes. |
| Show active app, track title, calendar, system metrics | New host software/data transport plus firmware UI work. |

These boundaries follow the [Kconfig choice][kconfig], [layout dispatcher][dispatcher],
[Radii theme header][radii-colors] and [widget source tree][layouts]. Layout
selection currently happens at compile time: only one layout's widgets are
compiled. The reserved F22-F24 bindings have no screen-switching handler in this
module; the local [dongle notes](prospector-dongle.md#prospector-config-knobs)
also record this.

Radii uses the `zmk,prospector-theme` chosen node, falling back to
`prospector_blue_theme`. The module includes blue, green, red and purple themes
with nine configurable colors. Operator has hardcoded color constants; Classic
and Field largely set colors in their widget C files. Sources:
[theme definitions][themes], [theme schema][theme-schema],
[Radii colors][radii-colors], [Operator colors][operator-colors], [layouts][layouts].

## Implementation route

Recommended approach: maintain a small fork of the current pinned module and
add a fifth layout while retaining the four upstream choices. Point this
repository's module manifest to a pinned commit in that fork. This fits the
existing layout wiring and makes the change reproducible; edits only inside
the downloaded `modules/` checkout would not be captured by this config repo.
Sources: [manifest](../config/west.yml), [module build wiring][cmake].

1. Add a layout option in module-root `Kconfig`.
2. Add `boards/shields/prospector_adapter/src/layouts/<name>/status_screen.c`
   implementing `lv_obj_t *zmk_display_status_screen()` and its widgets.
3. Extend `src/custom_status_screen.c` and the shield's `CMakeLists.txt` to
   select the new layout. Its `Kconfig.defconfig` enables the LVGL components
   and optional ZMK features it needs; those files are already discovered with
   a wildcard.
4. Reuse the existing widget event subscriptions, changing presentation first.
   `ZMK_DISPLAY_WIDGET_LISTENER` forwards widget updates onto the display work
   queue. New animated work should respect that threading model.

Sources: [Kconfig][kconfig], [dispatcher][dispatcher], [CMake][cmake],
[shield defaults][defaults], [simple layer widget][layer-widget],
[ZMK display listener](../zmk/app/include/zmk/display.h).

Already available data includes active layer/name, peripheral battery and
connection status, USB/BLE output/profile, active modifiers and Caps Word.
Operator also renders WPM; Field uses WPM for animation. Reusing those events
avoids changing the split protocol. Host application information is absent
from these widget sources; requiring a companion data channel is an engineering
inference from that boundary. Sources: [layout widgets][layouts],
[WPM widget][wpm], [Field animation][field-animation].

## Design and validation constraints

- Design for **280 x 240 landscape pixels**. The panel is natively 240 x 280,
  but the module rotates it 90 or 270 degrees; the `ROTATE_DISPLAY_180` setting
  chooses between those landscape orientations. Sources:
  [hardware overlay][hardware], [rotation initialization][rotation].
- Favor readable text, simple shapes and restrained animation. The existing
  dongle build allocates about 229.6 KiB of its 256 KiB RAM according to
  `_image_ram_size` in the local [linker map](../.build/hillside_d50_dongle/zephyr/zmk.map).
  That is an existing artifact, not a fresh measurement. Its
  [generated config](../.build/hillside_d50_dongle/zephyr/.config) uses RGB565,
  two 50% display buffers and a 16 KiB LVGL memory pool. Reducing
  `CONFIG_LV_Z_VDB_SIZE` to 25 is the module's documented RAM workaround.
  Sources: [defaults][defaults], [README][branch].
- Fonts are already compiled C assets. New fonts should contain only required
  glyphs/sizes; images can likewise become LVGL C assets. Budget image buffers
  and decoding before choosing animation-heavy artwork. Sources:
  [existing fonts][fonts], [LVGL fonts][font-docs], [LVGL images][image-docs].
- No Prospector simulator/preview harness was found in the inspected module.
  A 280 x 240 browser mockup is a useful proposed design step; an LVGL desktop
  simulator with mocked keyboard state would be additional implementation,
  not an existing command. LVGL documents SDL simulator options for macOS and
  Linux. Sources: [module tree][branch], [LVGL simulator][simulator].

For a first design, keep active layer prominent, both batteries visible, and
modifiers/Caps Word easy to distinguish. Decide whether WPM merits the remaining
space. Validate idle, typing, each layer, held modifiers, low/disconnected
batteries and both output modes. Build with `just build hillside_d50_dongle`,
inspect memory use, then check readability and typing responsiveness on the
actual dongle. The target already exists in [build.yaml](../build.yaml); the
current [dongle configuration](../config/boards/shields/hillside_d50/hillside_d50_dongle.conf)
selects Classic by default, fixed brightness 50 and Mac modifier styling.

[branch]: https://github.com/carrefinho/prospector-zmk-module/tree/feat/new-status-screens
[lvgl-version]: https://github.com/zmkfirmware/lvgl/blob/f1db87ee98f1810328a8419572fa42a3b5f352ae/lv_version.h
[kconfig]: https://github.com/carrefinho/prospector-zmk-module/blob/ed98221f3b52b7066dbb10ba3af8a29150b93a5a/Kconfig
[cmake]: https://github.com/carrefinho/prospector-zmk-module/blob/ed98221f3b52b7066dbb10ba3af8a29150b93a5a/boards/shields/prospector_adapter/CMakeLists.txt
[dispatcher]: https://github.com/carrefinho/prospector-zmk-module/blob/ed98221f3b52b7066dbb10ba3af8a29150b93a5a/boards/shields/prospector_adapter/src/custom_status_screen.c
[defaults]: https://github.com/carrefinho/prospector-zmk-module/blob/ed98221f3b52b7066dbb10ba3af8a29150b93a5a/boards/shields/prospector_adapter/Kconfig.defconfig
[layouts]: https://github.com/carrefinho/prospector-zmk-module/tree/ed98221f3b52b7066dbb10ba3af8a29150b93a5a/boards/shields/prospector_adapter/src/layouts
[radii-screen]: https://github.com/carrefinho/prospector-zmk-module/blob/ed98221f3b52b7066dbb10ba3af8a29150b93a5a/boards/shields/prospector_adapter/src/layouts/radii/status_screen.c
[radii-colors]: https://github.com/carrefinho/prospector-zmk-module/blob/ed98221f3b52b7066dbb10ba3af8a29150b93a5a/boards/shields/prospector_adapter/src/layouts/radii/display_colors.h
[operator-colors]: https://github.com/carrefinho/prospector-zmk-module/blob/ed98221f3b52b7066dbb10ba3af8a29150b93a5a/boards/shields/prospector_adapter/src/layouts/operator/display_colors.h
[themes]: https://github.com/carrefinho/prospector-zmk-module/blob/ed98221f3b52b7066dbb10ba3af8a29150b93a5a/boards/shields/prospector_adapter/prospector_adapter.overlay
[theme-schema]: https://github.com/carrefinho/prospector-zmk-module/blob/ed98221f3b52b7066dbb10ba3af8a29150b93a5a/dts/bindings/zmk,prospector-theme.yaml
[layer-widget]: https://github.com/carrefinho/prospector-zmk-module/blob/ed98221f3b52b7066dbb10ba3af8a29150b93a5a/boards/shields/prospector_adapter/src/layouts/field/layer_label.c
[wpm]: https://github.com/carrefinho/prospector-zmk-module/blob/ed98221f3b52b7066dbb10ba3af8a29150b93a5a/boards/shields/prospector_adapter/src/layouts/operator/wpm_meter.c
[field-animation]: https://github.com/carrefinho/prospector-zmk-module/blob/ed98221f3b52b7066dbb10ba3af8a29150b93a5a/boards/shields/prospector_adapter/src/layouts/field/line_segments.c
[hardware]: https://github.com/carrefinho/prospector-zmk-module/blob/ed98221f3b52b7066dbb10ba3af8a29150b93a5a/boards/shields/prospector_adapter/boards/xiao_ble_zmk.overlay
[rotation]: https://github.com/carrefinho/prospector-zmk-module/blob/ed98221f3b52b7066dbb10ba3af8a29150b93a5a/boards/shields/prospector_adapter/src/display_rotate_init.c
[fonts]: https://github.com/carrefinho/prospector-zmk-module/tree/ed98221f3b52b7066dbb10ba3af8a29150b93a5a/boards/shields/prospector_adapter/src/fonts
[font-docs]: https://docs.lvgl.io/9.3/details/main-modules/font.html
[image-docs]: https://docs.lvgl.io/9.3/details/main-modules/image.html
[simulator]: https://docs.lvgl.io/9.3/details/integration/ide/pc-simulator.html
