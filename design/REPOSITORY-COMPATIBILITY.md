# Repository compatibility review and requested revision

Reviewed https://github.com/USAFA-ECE/ece383-arcade at commit **40c9750e68a3fcec678eb5b699f36182dd5195eb**, main branch, on 2026-10-14. The frozen controller source used for pin-map validation is under `reference/upstream/`; other reviewed files are linked below. This change adds a separate manual-switch firmware sketch and preserves the legacy controller example. The tree contains controller firmware, a kiosk key tester, PHP loader/menu experiments and three compiled bitstreams. It contains no HDL/XDC sources for those bitstreams.

## Due assignments

[Controller source, pins and mode](https://github.com/USAFA-ECE/ece383-arcade/blob/40c9750e68a3fcec678eb5b699f36182dd5195eb/controllers/due_interface.c#L5-L27) establishes:

| Signal | Player 1 | Player 2 |
| --- | --- | --- |
| A | D22 | D30 |
| B | D23 | D31 |
| Select | D24 | D32 |
| Start | D25 | D33 |
| Up | D26 | D34 |
| Down | D27 | D35 |
| Left | D28 | D36 |
| Right | D29 | D37 |
| Latch from FPGA | D2 | D5 |
| Clock from FPGA | D3 | D6 |
| Serial DATA to FPGA | D4 | D7 |

D8 is MODE_PIN: HIGH enables Pi USB HID in upstream. D9 is an automatic HDMI pulse output in upstream; **D9 is unconnected and unused in the revised design**. All 16 button contacts remain `INPUT_PULLUP` to GND. No Pi GPIO is part of this controller wiring.

The previous design's direction-first button assignment was incompatible with the code. All current diagrams and reference headers now use the table above. D2-D8 assignments already matched; the JA mapping still follows the owner's screenshot.

## Differences that affect behavior

| Finding in upstream | Revised design / consequence |
| --- | --- |
| Both Start buttons trigger a D9 transistor pulse | Removed. Silver button directly operates HDMI switch; Q1/R2/R3 and D9 wiring removed. |
| D8 gates HID but does not stop NES emulation | New local firmware draft makes the two destinations exclusive. In Pi mode NES data stays Hi-Z; in FPGA mode all HID keys are released. |
| NES data is LOW or Hi-Z, relying on external 10k pull-ups | Added R6/R7: JA3/JA9 to JA6 (FPGA 3.3 V). Original push-pull-HIGH initialization is removed. These are NES data resistors, not external button pull-ups. |
| Both NES CLOCK interrupts use RISING | Preserved in revised firmware; corrected earlier falling-edge documentation. Actual bitstream sampling/timing still requires a scope test. |
| Only Player 1 emits keyboard keys | New draft lets either player navigate the Pi using the same key map. Inputs are combined so one player's release cannot cancel the other's held key. |
| Mode HIGH is assumed to mean Pi | Preserved as default `PI_SELECTED_LEVEL=HIGH`; measure switch status and change the constant to LOW if polarity is reversed. No automatic polarity inference is possible. |
| Filename is `.c` but code uses Arduino/C++ constructs | Use the supplied `.ino` project with Arduino Due Native USB support. The upstream file is not valid plain C. |

The proposed local implementation is `reference/arcade_due_manual_switch/arcade_due_manual_switch.ino`. It requires 20 stable 1 kHz status samples before enabling either destination, and releases both routes immediately when status changes. It preserves the upstream serial bit order and uses open-drain data. Serial bit counters saturate after eight bits, avoiding wraparound on excessive clocks. Status is `INPUT`, not `INPUT_PULLUP`, because U2 drives it and R5 provides an unplugged-line bias.

## Pi wiring and software

[Pi-side files](https://github.com/USAFA-ECE/ece383-arcade/tree/40c9750e68a3fcec678eb5b699f36182dd5195eb/server) use `openFPGALoader -b nexysVideo`. The required physical paths are Pi USB host -> Due Native USB, Pi USB host -> Nexys PROG/JTAG, and Pi HDMI -> switch. No BCM/physical GPIO pin assignments appear in the reviewed Pi web/server sources. The realistic view uses representative Pi 4B artwork; the actual Pi model remains unspecified.

[kiosk/index.htm](https://github.com/USAFA-ECE/ece383-arcade/blob/40c9750e68a3fcec678eb5b699f36182dd5195eb/kiosk/index.htm) displays the most recent key press. It is not a working game-selection kiosk. `server/test.php` generates game links, but supplies no joystick arrow/Start navigation logic or kiosk startup setup. The Due emits arrow keys, `a`, `b`, Enter and Space, matching upstream; the Pi application still needs to handle those keys for the desired menu behavior. Neither the Pi nor revised Due drives the HDMI switch.

## Limits and unresolved compatibility

- The switch's actual status polarity and tap locations have not been measured. The design assumes one valid 0/5 V status bit distinguishes Pi and FPGA. A variant with more selectable inputs needs additional state sensing.
- Compiled `.bit` files do not establish readable HDL pin constraints, clock edge expectations, LED support, mouse decoding or codec initialization. The screenshot establishes the cabinet JA convention, but compatibility of every supplied binary with JA4 LEDs and the exact trackball cannot be certified from this repository alone.
- The existing fast Arduino ISR approach is preserved but is not a guarantee of original NES-speed timing. Host tests check logic, not SAM3X latency, GPIO slew or FPGA sampling.
- The trackball remains physically connected to the FPGA, as requested. Only Due-connected buttons/joysticks change logical destination; the trackball does not move to the Pi when video changes.
- Switching video does not automatically program a core. The Pi can load a selected bitstream over its independent JTAG cable; the silver button then changes the displayed source.

Host-compiled behavior tests pass for pin setup, internal pull-ups, mode debouncing, exclusive routing, both-player HID menu input, serial data order, post-eight-clock release and mode-transition key/data release. Native Due compilation and hardware timing have not been tested. File structure/electrical graph checks pass; native Fritzing opening remains unverified due to the local Qt runtime conflict.
