#!/usr/bin/env python3
"""Redraw the supplied JA mating-face reference as an original labeled SVG."""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'design' / 'previews' / 'ja-port.svg'
svg = ['''<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="930" viewBox="0 0 1440 930" role="img" aria-labelledby="title desc">
<title id="title">Nexys Video JA connector: arcade wiring</title>
<desc id="desc">Front mating face with PCB below. Upper row left to right: 6, 5, 4, 3, 2, 1. Lower row: 12, 11, 10, 9, 8, 7. Player 1 latch, pulse, data use JA1, JA2, JA3; player 2 uses JA7, JA8, JA9. JA4 is LED data.</desc>
<defs>
 <linearGradient id="housing" x2="0" y2="1"><stop stop-color="#515c69"/><stop offset="1" stop-color="#202a34"/></linearGradient>
 <linearGradient id="bezel" x2="0" y2="1"><stop stop-color="#d6dbe0"/><stop offset="1" stop-color="#87939f"/></linearGradient>
</defs>
<rect width="1440" height="930" rx="20" fill="#f5f7fa"/>
''']


def text(x, y, value, size=24, fill='#1b2b40', anchor='start', bold=False):
    return (f'<text x="{x}" y="{y}" font-family="DejaVu Sans,sans-serif" '
            f'font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{700 if bold else 400}">{escape(str(value))}</text>')


svg += [text(56, 65, 'JA  /  NEXYS VIDEO', 36, bold=True),
        text(56, 104, 'Front / mating face • look into the board socket with the PCB below', 24),
        text(56, 140, 'Orientation matches the supplied cabinet reference. Wire-side view is mirrored.', 21, '#53657a')]

colors = {'power': '#bc4141', 'ground': '#4568bc', 'p1': '#2177b6',
          'p2': '#8853aa', 'led': '#198467', 'spare': '#6c7887'}
functions = {
    6: ('3.3 V', 'power'), 5: ('GND', 'ground'), 4: ('LED DATA', 'led'),
    3: ('P1 DATA', 'p1'), 2: ('P1 PULSE', 'p1'), 1: ('P1 LATCH', 'p1'),
    12: ('3.3 V / NC', 'power'), 11: ('GND', 'ground'), 10: ('SPARE', 'spare'),
    9: ('P2 DATA', 'p2'), 8: ('P2 PULSE', 'p2'), 7: ('P2 LATCH', 'p2'),
}
svg += [text(330, 208, 'VCC', 23, colors['power'], 'middle', True),
        text(486, 208, 'GND', 23, colors['ground'], 'middle', True),
        text(876, 208, '8 SIGNALS', 23, '#445264', 'middle', True),
        '<path d="M620 235 V224 H1132 V235" fill="none" stroke="#627386" stroke-width="3"/>',
        '<rect x="155" y="448" width="1128" height="20" fill="#08784f" stroke="#044a31" stroke-width="3"/>',
        '<rect x="267" y="254" width="924" height="194" rx="6" fill="url(#housing)" stroke="#18222e" stroke-width="4"/>']
for row, numbers in enumerate(((6, 5, 4, 3, 2, 1), (12, 11, 10, 9, 8, 7))):
    for column, pin in enumerate(numbers):
        x, y = 330 + column * 156, 303 + row * 96
        label, kind = functions[pin]
        color = colors[kind]
        svg += [f'<rect x="{x-35}" y="{y-35}" width="70" height="70" rx="3" fill="url(#bezel)" stroke="#89939f" stroke-width="2"/>',
                f'<rect x="{x-25}" y="{y-25}" width="50" height="50" rx="2" fill="{color}"/>',
                f'<rect x="{x-13}" y="{y-13}" width="26" height="26" fill="#10171d" stroke="#d0b56b" stroke-width="3"/>',
                text(x+49, y+7, pin, 21, '#ffffff', 'middle', True),
                text(x, 247 if row == 0 else 509, label, 18, color, 'middle', True)]
svg += [text(247, 295, 'Pin 6', 23, anchor='end', bold=True),
        text(1213, 295, 'Pin 1', 23, bold=True),
        text(247, 407, 'Pin 12', 23, anchor='end', bold=True),
        text(1213, 407, 'Pin 7', 23, bold=True),
        text(155, 498, 'PCB', 18, '#08784f', bold=True)]

# Compact wiring legend: same rows and assignment order as the cabinet reference.
for x, player, pins, due in ((56, 1, (1, 2, 3), (2, 3, 4)), (740, 2, (7, 8, 9), (5, 6, 7))):
    color = colors[f'p{player}']
    svg += [f'<rect x="{x}" y="555" width="644" height="190" rx="12" fill="#ffffff" stroke="#d7dfe8" stroke-width="2"/>',
            text(x+24, 590, f'PLAYER {player}  /  NES CONTROLLER', 23, color, bold=True)]
    for i, (pin, dpin, label) in enumerate(zip(pins, due, ('Latch', 'Pulse / clock', 'Serial data'))):
        direction = '←' if i == 2 else '→'
        svg.append(text(x+24, 632+i*40, f'JA{pin}  ·  {label}  {direction}  Due D{dpin}', 24))

svg += [text(56, 791, 'JA4 → U1 A1: FPGA 3.3 V → LED 5 V data. JA10: spare.', 23, colors['led'], bold=True),
        text(56, 831, 'JA5 / JA11: common GND. JA6: 3.3 V for R6 / R7 (10 kΩ NES data pull-ups).', 23),
        text(56, 871, 'JA12: leave unconnected. Never apply 5 V to JA or join FPGA and Due 3.3 V rails.', 22),
        text(56, 907, 'Latch / pulse: FPGA → Due. Serial data: Due → FPGA, LOW or Hi-Z. Not a mechanical drawing.', 20, '#53657a'),
        '</svg>']
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text('\n'.join(svg) + '\n')
print(OUT)
