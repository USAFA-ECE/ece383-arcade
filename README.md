# ece383-arcade
Applied Reconfigurable Computing And Digital Electronics

flowchart LR
    C1[Controller 1 Buttons]
    C2[Controller 2 Buttons]
    DUE[Arduino Due]
    FPGA[Nexys Video FPGA]
    PI[Raspberry Pi]
    HDMI[HDMI Switch]

    C1 --> DUE
    C2 --> DUE
    DUE -->|LATCH/CLOCK/DATA| FPGA
    DUE -->|USB HID| PI
    DUE -->|Simulated Button Press| HDMI
