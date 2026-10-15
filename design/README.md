# Arcade cabinet wiring design

The design now matches the Due pin assignments in [USAFA-ECE/ece383-arcade](https://github.com/USAFA-ECE/ece383-arcade) at commit `40c9750e68a3fcec678eb5b699f36182dd5195eb`. See `REPOSITORY-COMPATIBILITY.md` for the source review and unresolved issues.

**The silver arcade button switches HDMI directly. Neither Pi GPIO nor Due D9 drives the switch.** The switch's 5 V status goes through U2 to Due D8; the Due routes its controls exclusively to the selected device. HIGH is assumed to mean Pi until the actual switch is measured.

| File | Purpose |
| --- | --- |
| `01-arcade-system.fzz` | Cabinet cable and harness overview |
| `02-controls-and-ja.fzz` | Corrected individual controls, NES connections and external data pull-ups |
| `03-led-and-hdmi-interfaces.fzz` | LED/status translators and direct silver-button wiring |
| `04-realistic-breadboard.fzz` | Additional recognizable board/component artwork with physical harness wiring |
| `previews/*.svg` | Matching browser-viewable vector diagrams |
| `previews/04-realistic-breadboard.png` | Physical-view image |
| `BOM.csv`, `connections.csv` | Components and drawn wire endpoints |
| `reference/arcade-ja.xdc` | Vivado pin fragment |
| `reference/arcade_due_manual_switch/arcade_due_manual_switch.ino` | Revised local firmware draft for manual switching and exclusive routing |
| `reference/ArcadePins.h` | Pin/initialization reference |
| `reference/upstream/` | Frozen upstream controller pin baseline |

The four `.fzz` files embed their custom parts. Open Breadboard view for sheet 04. Sheets 01-03 retain the logical diagrams; they have been corrected for the repository and manual switch. The separate sketches do not share an electrical netlist across documents.

Sheet 04 uses actual Fritzing Arduino Due artwork and representative Pi 4B artwork, plus original illustrations for other components. The Nexys JA inset and interface assembly are connector references, not a mechanically accurate assembly layout. All images are not to scale. Internal interface wiring is defined by sheets 02/03. Complete USB/HDMI/audio cables use one logical connector, not individual conductors. None of these parts provide fabrication-ready PCB footprints. Artwork credits/license are in `assets/ATTRIBUTION.md`.

## Corrected controls and Due pin map

The previous direction-first button ordering was incompatible with the repository. Use this corrected mapping:

| Control | Player 1 Due pin | Player 2 Due pin |
| --- | --- | --- |
| A | D22 | D30 |
| B | D23 | D31 |
| Select | D24 | D32 |
| Start | D25 | D33 |
| Up | D26 | D34 |
| Down | D27 | D35 |
| Left | D28 | D36 |
| Right | D29 | D37 |

Each player has four mechanical joystick NO contacts plus one Start, Select, A and B button. There are eight player pushbuttons total, plus the separate silver HDMI button. Connect each control NO to its assigned input and COM to GND; leave NC terminals open. Configure **D22-D37 as `INPUT_PULLUP`**, pressed LOW. No external button pull-ups are required. The Due has 3.3 V I/O. [Arduino Due documentation](https://store.arduino.cc/products/arduino-due)

Pi USB host -> Due **Native USB**, for keyboard HID and Due power. Programming USB is not the HID connection. The Due's D8 receives translated HDMI status as `INPUT`, not `INPUT_PULLUP`. D9 remains unconnected and is left as an input. The silver button is not connected to the Due.

## JA pin map

Controller GPIO assignments match the repository; JA positions follow the supplied cabinet screenshot. No level translation is required between Due and FPGA 3.3 V GPIO.

| JA physical pin | FPGA package pin | Function | Due / destination | Direction at FPGA |
| --- | --- | --- | --- | --- |
| 1 | AB22 | Player 1 latch | D2 | Output |
| 2 | AB21 | Player 1 clock | D3 | Output |
| 3 | AB20 | Player 1 serial data | D4; R6 to JA6 | Input |
| 4 | AB18 | SK6812 data | U1 pin 2 / A1 | Output |
| 5 | - | GND | Common ground | Ground |
| 6 | - | FPGA +3.3 V | R6/R7 pull-ups only | Power |
| 7 | Y21 | Player 2 latch | D5 | Output |
| 8 | AA21 | Player 2 clock | D6 | Output |
| 9 | AA20 | Player 2 serial data | D7; R7 to JA6 | Input |
| 10 | AA18 | Spare | NC | Unused |
| 11 | - | GND | Common ground | Ground |
| 12 | - | Board +3.3 V | NC | Power |

Front/mating face, matching the owner's screenshot:

```text
3V3/R6,R7  GND   LED     P1 DATA  P1 CLK  P1 LATCH
    6       5     4        3        2       1
   12      11    10        9        8       7
 3V3/NC    GND   SPARE   P2 DATA  P2 CLK  P2 LATCH
```

R6 and R7 are 10 kohm each, pulling JA3 and JA9 to the **FPGA's** 3.3 V at JA6. The code uses open-drain data: LOW when asserted, otherwise Hi-Z. Do not drive data HIGH from the Due and do not connect the FPGA's positive rail to Due 3.3 V. These resistors are separate from the internal player-button pull-ups. Both NES players and LED data fit on JA; JA10 remains spare. [Digilent master XDC](https://raw.githubusercontent.com/Digilent/digilent-xdc/master/Nexys-Video-Master.xdc)

## LED interface - U1 SN74HCT245N

The invoice lists `SN74HCT245N` and `SN74LVC245AN`, 20 of each. Use one of each as shown. They are different devices, not interchangeable converters.

| Converter | Purpose |
| --- | --- |
| U1 - SN74HCT245N | **FPGA 3.3 V -> LED 5 V data**: raises JA4 data to the SK6812 input level. |
| U2 - SN74LVC245AN | **HDMI switch 5 V -> Due 3.3 V status**: reduces the selected-source status signal for Due D8. |

These translate logic signal levels; they do not convert supply power.

U1 is powered from the regulated **LED 5 V** rail. Its TTL input accepts the FPGA's 3.3 V data and drives a 5 V output. DIR HIGH selects A-to-B; /OE LOW enables it. [TI SN74HCT245 datasheet](https://www.ti.com/lit/ds/symlink/sn74hct245.pdf)

| U1 pin | Connection |
| --- | --- |
| 20 VCC | LED +5 V |
| 10 GND | Common GND |
| 1 DIR | LED +5 V |
| 19 /OE | Common GND |
| 2 A1 | JA4; also R4 10 kohm to GND |
| 18 B1 | R1 330 ohm, then LED1 DIN |
| 3-9 A2-A8 | GND, each |
| 11-17 B8-B2 | Leave open, each |

C1 is 100 nF ceramic directly between pins 20 and 10. C3 is 1000 uF, rated at least 10 V, across the LED input supply, positive lead to +5 V. Place R1 near the first pixel. R4 holds the input LOW while the FPGA is unconfigured. These practices follow the [Adafruit pixel wiring guidance](https://learn.adafruit.com/adafruit-neopixel-uberguide/best-practices).

All pixels receive +5 V and GND **in parallel**. Data chains LED1 DOUT -> LED2 DIN -> LED3 DIN -> optional LED4 DIN. The last DOUT is open. For three pixels, omit LED4 and leave LED3 DOUT open. Use a regulated 5 V supply with at least 1 A available for the LEDs and buffer; a conservative four-RGB-pixel allowance is 4 x 60 mA = 240 mA, plus buffer and margin. Check the actual pixel's maximum current. Add a 100 nF bypass at each bare LED if not included on its board.

These are specified as **RGB**, not RGBW. The bitstream must use the exact strip's byte order, bit count, pulse timing and reset interval. The SK6812 symbol labels +5 V/DIN/GND/DOUT rather than guessing a bare package or strip pad order. Follow its arrows and labels. Keep JA-to-U1 and U1-to-first-pixel wiring short.

Do not connect the new LED chain to the trackball's original color-changing LED controller. Do not join external LED +5 V to USB VBUS. Only grounds are shared.

## Manual HDMI button and 5 V status

The silver button's dry NO/COM contacts connect directly across the HDMI switch's active-low button contact and its matching common/ground. It alone changes source. Q1, R2, R3 and the D9 switching wire are removed. Do not connect a switch signal to a Pi GPIO. Any separate illumination terminals on the silver button are not button contacts and are not wired here.

The [supplied switch listing](https://www.amazon.com/dp/B0F6LM1578) does not establish internal tap locations or status polarity. The owner's stated 0/5 V status output goes to U2. Verify that it is a steady logic signal rather than a current-limited indicator LED or PWM node. A switch variant with more than two selectable inputs requires additional state sensing.

U2 SN74LVC245AN translates **HDMI switch 5 V -> Due 3.3 V status**, protecting D8. Its inputs tolerate 5 V while its output follows its 3.3 V supply. [TI SN74LVC245A datasheet](https://www.ti.com/lit/ds/symlink/sn74lvc245a.pdf)

| U2 pin | Connection |
| --- | --- |
| 20 VCC | Due 3.3 V |
| 10 GND | Common GND |
| 1 DIR | Due 3.3 V |
| 19 /OE | GND |
| 2 A1 | Switch STATUS_5V; R5 100 kohm to GND |
| 18 B1 | Due D8, configured INPUT |
| 3-9 A2-A8 | GND, each |
| 11-17 B8-B2 | Leave open, each |

C2 is 100 nF directly across U2 pins 20/10. Do not power U2 from 5 V. R5 biases a disconnected status wire LOW, but cannot distinguish an unplugged cable from a genuine LOW status.

The revised local firmware assumes **D8 HIGH = Pi, D8 LOW = FPGA**. Measure the actual switch and set `PI_SELECTED_LEVEL` to LOW if the status polarity is opposite. Changing source does not change physical USB connections; the Due gates which interface reports input.

| Selected source | Due behavior |
| --- | --- |
| Pi | Keyboard HID enabled; both NES data outputs remain Hi-Z/released |
| FPGA | HID keys released; two independent NES controller ports enabled |
| Status transition/bounce | Both destinations released until 20 stable 1 kHz samples |

Either player's controls can navigate the Pi using the repository key map: arrows, A=`a`, B=`b`, Start=Enter, Select=Space. The new draft combines the players' menu inputs. In FPGA mode each player remains independent. This differs from upstream, which only emits Player 1 HID and keeps NES active in both modes.

## Pi, monitor, speakers and trackball

Pi HDMI -> switch input 1; Nexys **HDMI OUT** -> switch input 2; switch output -> monitor. Nexys green LINE OUT -> powered speakers or amplifier. Passive speakers need amplification. The Nexys and Pi use their own normal supplies; do not parallel positive supply outputs.

Pi USB host -> Nexys **PROG/JTAG**, independent of Pi USB host -> Due Native. No Pi GPIO assignment appears in the reviewed repository. The loader uses:

```sh
openFPGALoader -b nexysVideo /absolute/path/to/game.bit
```

This is volatile loading; do not add `-f` for ordinary menu launches. The silver button selects displayed video manually; neither Pi nor Due toggles it. Source: [repository loader](https://github.com/USAFA-ECE/ece383-arcade/blob/40c9750e68a3fcec678eb5b699f36182dd5195eb/server/fpgaloader.php).

The repository's `kiosk/index.htm` is a keypress tester, not a working bitstream menu. `server/test.php` displays links but has no arrow-key/Start menu navigation or kiosk startup setup. The desired kiosk application still needs that integration. See the compatibility review.

The [3 inch RetroArcade.us trackball](https://www.amazon.com/dp/B0711TKGFV) stays on Nexys USB HOST J15. Digilent's host translates supported USB mouse events into PS/2 clock/data; a bitstream must initialize and decode that interface. The exact device's compatibility remains a bench check. Trackball input always goes to the FPGA, as physically requested; only Due-connected controls change destination. No USB hub is shown. [Nexys Video reference manual](https://digilent.com/reference/_media/reference/programmable-logic/nexys-video/nexys-video_rm.pdf)

## Firmware and compatibility limits

Open `reference/arcade_due_manual_switch/arcade_due_manual_switch.ino` as an Arduino Due Native USB project. It is a local revised draft; the GitHub repository was not changed. It contains the corrected pin order, internal button pull-ups, manual-switch status routing and open-drain NES serialization. `reference/upstream/` preserves the reviewed files.

The draft preserves upstream **RISING** latch and clock interrupts. That differs from the earlier design's falling-edge note. Raw serial order is A, B, Select, Start, Up, Down, Left, Right, LOW pressed. Latch presents A; rising clock callbacks advance; data stays released after eight bits. Verify the target bitstream's edge convention and service-time margin with a scope. Arduino interrupt handlers plus USB service are not a guarantee of original NES-speed response.

The repository includes compiled game bitstreams but no corresponding HDL/XDC. Their exact JA4 LED use, trackball support, audio initialization and sampling timing cannot be confirmed from those binaries. The artwork's kiosk screen is an illustration of the intended interface, not a claim that the repository implements it.

## Bring-up and validation

1. Check JA mating orientation, all ground connections and separation of Due 3.3 V, FPGA 3.3 V and LED 5 V. JA6 supplies only the two 10k data pull-ups; JA12 is open.
2. Confirm D22-D37 control order and HIGH released/LOW pressed with internal pull-ups.
3. Measure switch status polarity and voltage. Verify the silver button switches video without any Due or Pi output. Set firmware polarity accordingly.
4. Test exclusive routing and held-key release during source changes. Check both NES ports independently, including extra clocks and Hi-Z/released behavior.
5. Scope actual NES timing with the fastest supplied core; verify GPIO edge convention and rise times through the 10k pull-ups.
6. Test Pi JTAG loading, trackball mouse decoding, powered-speaker audio and the new kiosk navigation separately.
7. Test one low-brightness LED before adding three/four. Verify exact SK6812 byte order and timing.

File/connector graph checks pass for all four sheets. Host-compiled firmware behavior tests pass using mocked Arduino and Keyboard APIs; these do not replace compiling for the SAM3X board or measuring real interrupt timing. Previews are rendered and visually checked. Native Fritzing opening/export is still unverified because the available AppImage has a Qt conflict with the headless runtime.

Rebuild all four sheets and run the checks from the project root:

```sh
python3 tools/build_realistic.py
python3 tools/validate_design.py
python3 tools/test_due_firmware.py
```

`tools/build_design.py` rebuilds only logical sheets 01-03; `build_realistic.py` runs that builder and adds sheet 04.
