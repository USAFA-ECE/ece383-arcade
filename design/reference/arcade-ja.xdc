# Nexys Video JA mapping from Digilent Nexys-Video-Master.xdc.
# Port names are a proposed interface; adapt them to each core.
# Latch and clock are FPGA outputs. Serial data is FPGA input.
set_property -dict {PACKAGE_PIN AB22 IOSTANDARD LVCMOS33} [get_ports nes1_latch]
set_property -dict {PACKAGE_PIN AB21 IOSTANDARD LVCMOS33} [get_ports nes1_clock]
set_property -dict {PACKAGE_PIN AB20 IOSTANDARD LVCMOS33} [get_ports nes1_data_n]
set_property -dict {PACKAGE_PIN Y21  IOSTANDARD LVCMOS33} [get_ports nes2_latch]
set_property -dict {PACKAGE_PIN AA21 IOSTANDARD LVCMOS33} [get_ports nes2_clock]
set_property -dict {PACKAGE_PIN AA20 IOSTANDARD LVCMOS33} [get_ports nes2_data_n]
set_property -dict {PACKAGE_PIN AB18 IOSTANDARD LVCMOS33} [get_ports trackball_led_data]
# Released state while the Due output is disconnected/reset.
set_property PULLUP TRUE [get_ports {nes1_data_n nes2_data_n}]
# JA10 / AA18 is unused. JA5/JA11 are ground; JA12 remains unconnected.
# JA6 supplies R6/R7 external 10k pull-ups to nes1_data_n / nes2_data_n.
# Due data outputs must be LOW or Hi-Z, never actively HIGH.
# Optional on-board mouse interface, enable only if these top-level ports exist:
# set_property -dict {PACKAGE_PIN W17 IOSTANDARD LVCMOS33 PULLUP TRUE} [get_ports ps2_clk]
# set_property -dict {PACKAGE_PIN N13 IOSTANDARD LVCMOS33 PULLUP TRUE} [get_ports ps2_data]
# This is a pin fragment, not complete timing constraints or a full core XDC.
