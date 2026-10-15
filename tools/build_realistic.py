#!/usr/bin/env python3
"""Build sheets 01-03 and an additional Fritzing-style physical harness view."""
from build_design import *
import re, copy
E.register_namespace('',NS)
ASSETS=OUT/'assets'
def rect(x,y,w,h,fill,stroke='none',rx=0,sw=1):return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def circle(x,y,r,fill,stroke='none',sw=1):return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def line(x1,y1,x2,y2,color='#bcbec1',width=3):return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>'
def text(x,y,s,size=16,color='white',anchor='start',weight='normal'):return txt(x,y,s,size,color,anchor,weight)
def holes(w,h):return ''.join(circle(x,y,8,'#f7f8fa','#a1a5aa',4) for x,y in [(25,25),(w-25,25),(25,h-25),(w-25,h-25)])
def socket(x,y,w=55,h=40,label=None):
 z=rect(x,y,w,h,'#c9cccd','#858b91',3,2)+rect(x+7,y+8,w-14,h-14,'#252a30',rx=2)+line(x+12,y+h-11,x+w-12,y+h-11,'#c1aa67',3)
 if label:z+=text(x+w/2,y+h+17,label,11,'#ecf1ee','middle')
 return z
def ic(x,y,w,h,name):
 z=''
 for i in range(10):
  yy=y+10+i*(h-20)/9
  z+=rect(x-10,yy-4,14,8,'#bec1c4')+rect(x+w-4,yy-4,14,8,'#bec1c4')
 z+=rect(x,y,w,h,'#282d33','#111820',4,2)+f'<path d="M{x+w/2-8} {y} a8 8 0 0 0 16 0" fill="#12171b"/>'
 z+=circle(x+10,y+12,3,'#6e7479')+text(x+w/2,y+h/2,name,13,'#d8dde0','middle')
 return z
class RealPart(Part):
 def __init__(self,key,title,w,h,pins,art,buses=()):self.art=art;super().__init__(key,title,w,h,pins,kind='real',buses=buses)
 def svg(self,layer):
  w,h=self.w,self.h
  z=[f'<svg xmlns="{NS}" width="{w/90:.7f}in" height="{h/90:.7f}in" viewBox="0 0 {w} {h}"><g id="{layer}">',self.art]
  for k,p in self.pins.items():
   x,y,c=p['x'],p['y'],p['id']
   z += [f'<circle id="{c}pin" cx="{x}" cy="{y}" r="3.4" fill="#d7af63" stroke="#8d733d" stroke-width=".8"/>',f'<rect id="{c}terminal" x="{x-.5}" y="{y-.5}" width="1" height="1" fill="none"/>']
  return ''.join(z)+'</g></svg>'
def stock_art(filename,width,prefix):
 root=E.parse(ASSETS/filename).getroot();v=[float(n) for n in root.get('viewBox').split()];factor=width/v[2]
 # Original nested groups are retained; ids are prefixed to avoid collisions.
 src=''.join(E.tostring(c,encoding='unicode') for c in root if c.tag.rsplit('}',1)[-1] not in ['referenceFile','metadata'])
 ids=re.findall(r'\bid="([^"]+)"',src)
 for old in sorted(set(ids),key=len,reverse=True):
  src=src.replace('id="'+old+'"','id="'+prefix+old+'"').replace('url(#'+old+')','url(#'+prefix+old+')').replace('href="#'+old+'"','href="#'+prefix+old+'"')
 return f'<g transform="scale({factor})">{src}</g>',width*v[3]/v[2]
# Actual library Due artwork and pin centers, including 3V3 at connector253.
art,dh=stock_art('arduino-due-fritzing.svg',740,'dueArt_')
dp=json.loads((ASSETS/'due-pin-centers.json').read_text())
pins=[(k,k,x,y,'R') for k,(x,y) in dp.items()]+[('usb','Native USB',0,113,'L')]
art+=text(48,102,'NATIVE USB',10,'white')
due=RealPart('real_due','Arduino Due - physical wiring',740,dh,pins,art,buses=[['gnd','gnd2']])
art,ph=stock_art('raspberry-pi-4b-fritzing.svg',500,'piArt_')
pi=RealPart('real_pi','Raspberry Pi - USB and HDMI',500,ph,[('usb_due','USB host / Due',500,255,'R'),('usb_jtag','USB host / JTAG',500,298,'R'),('hdmi','HDMI',155,ph-8,'B')],art)
# Illustrated Nexys Video, using the board's recognizable top-side arrangement.
w=h=700
art=rect(10,10,680,680,'#087e72','#075b55',12,3)+holes(w,h)
for i in range(28):
 x=100+i*18
 art+=f'<path d="M{x} 190 V{240+i*7} H{400+i*3} V600" fill="none" stroke="#17685b" stroke-width="2"/>'
# Top connectors: HDMI IN, HDMI OUT, Ethernet, DisplayPort, four audio jacks.
art+=socket(45,0,78,65,'HDMI IN')+socket(165,0,78,65,'HDMI OUT')+socket(280,0,90,92,'ETHERNET')+socket(395,0,45,65,'DP')
for x,c,l in [(465,'#4e96d2','LINE IN'),(520,'#dc5c75','MIC'),(575,'#6cae57','LINE OUT'),(630,'#282c31','HP')]:
 art+=rect(x-21,0,42,70,c,'#343f45',4,2)+circle(x,14,12,'#121a22')+text(x,89,l,9,'white','middle')
art+=rect(0,105,68,49,'#25272b',rx=6)+circle(8,129,15,'#101318','#727a7d',3)+text(78,135,'12 V IN',13)
# Other PMODs, USB host and two micro USBs along left edge.
for yy,label in [(210,'JC'),(310,'JB')]:
 art+=rect(0,yy,46,78,'#20282d',rx=3)
 for i in range(6):art+=circle(18,yy+10+i*11,3,'#c1aa67')+circle(30,yy+10+i*11,3,'#c1aa67')
 art+=text(54,yy+43,label,15)
art+=socket(0,440,70,66,'USB HOST')+socket(0,545,40,30,'UART')+socket(0,625,40,30,'PROG')
art+=ic(240,235,95,65,'DDR3')+ic(395,270,65,50,'PHY')
art+=rect(286,345,130,120,'#144783','#052b55',7,2)
for i in range(9):art+=rect(294+i*13,353,6,104,'#0a2847')
art+=text(351,491,'ARTIX-7 200T',15)+text(145,175,'XILINX',30)+text(425,440,'DIGILENT',25)+text(270,530,'NEXYS VIDEO',27)
art+=rect(235,550,190,65,'#262f35','#a0a697',2,3)+rect(246,560,168,44,'#0d171e')
# FMC connector and switches.
art+=rect(590,190,80,285,'#1e2830','#b2b8ba',2,3)
for i in range(30):
 for j in range(5):art+=circle(600+j*13,200+i*9,1.7,'#a89a6e')
for i in range(8):
 x=135+i*47;art+=rect(x,635,29,42,'#283036','#b1b6b9',2)+rect(x+7,639,15,17,'#15191e')+circle(x+14,622,4,'#70ca68')
# JA socket is represented by a labeled mating-face inset at the right edge.
art+=rect(625,515,75,145,'#222b30',rx=3)+text(614,510,'JA',18)
ja_pos={}
for row,nums in enumerate([[6,5,4,3,2,1],[12,11,10,9,8,7]]):
 for i,n in enumerate(nums):
  x=650+row*27;y=531+i*23;ja_pos[str(n)]=(x,y)
  art+=rect(x-7,y-7,14,14,'#0b1115','#b29b5b',1)+text(x-10 if row==0 else x+10,y+4,str(n),8,'#f4f1ce','end' if row==0 else 'start')
art+=text(35,680,'Illustrated board; JA inset is a connector reference, not a drilling template.',10)
npins=[(k,'JA'+k,*xy,'R') for k,xy in ja_pos.items() if k not in ['10','12']]+[('hdmi','HDMI OUT',204,0,'T'),('audio','LINE OUT',575,0,'T'),('usb','USB HOST',0,473,'L'),('jtag','PROG',0,640,'L')]
nexys=RealPart('real_nexys','Nexys Video - illustrated',700,700,npins,art,buses=[['5','11']])
# Arcade pushbuttons: top cap plus exposed microswitch terminals.
def make_button(key,color):
 a=circle(49,53,44,'#242931','#111820',3)+circle(49,51,37,color,'#a6adb3' if key=='silver' else '#20252b',3)+circle(43,43,28,color)+f'<path d="M24 40 A28 28 0 0 1 68 27" fill="none" stroke="#ffffff" opacity=".35" stroke-width="5"/>'
 a+=rect(36,100,62,35,'#272d33',rx=3)+rect(96,105,24,7,'#c9cdd1')+rect(96,125,24,7,'#c9cdd1')+text(94,102,'NO',10,'#37475b')+text(94,146,'COM',10,'#37475b')
 return RealPart('real_button_'+key,('Silver HDMI button' if key=='silver' else 'Arcade button'),125,153,[('NO','NO',120,108.5,'R'),('COM','COM',120,128.5,'R')],a)
buttons={k:make_button(k,c) for k,c in [('red','#bd3039'),('blue','#2e72b0'),('white','#e5e8e9'),('silver','#b9c0c8')]}
# Four microswitch joystick, with five-wire harness (COM fan-out shown on 02).
a=rect(15,55,175,150,'#aeb3b9','#737d87',7,3)+''.join(circle(x,y,7,'#f7f8fa') for x,y in [(30,70),(175,70),(30,190),(175,190)])
for x,y,ww,hh in [(63,66,85,28),(30,100,28,65),(144,100,28,65),(63,173,85,28)]:a+=rect(x,y,ww,hh,'#30353b',rx=3)+rect(x+5,y+5,max(6,ww-10),8,'#912e39')
a+=rect(93,65,19,88,'#a4abb2','#5e6670',3)+circle(103,64,43,'#ac222f','#5c1621',3)+f'<path d="M77 52 A28 28 0 0 1 111 35" fill="none" stroke="#e97c86" stroke-width="8"/>'
for i,k in enumerate(['UP','DOWN','LEFT','RIGHT','COM']):a+=rect(186,110+i*20,25,8,'#bcc1c6')+text(183,118+i*20,k,9,'#263f55','end')
joy=RealPart('real_joystick','Arcade joystick',215,230,[(k,k,211,114+i*20,'R') for i,k in enumerate(['UP','DOWN','LEFT','RIGHT','COM'])],a)
# Physical interface assembly. Its internal pin-by-pin circuit remains on 02/03.
a=rect(0,0,620,350,'#b89052','#74572b',8,3)
for y in range(15,340,15):
 for x in range(15,610,15):a+=circle(x,y,1.8,'#775a36')
a+=ic(100,80,150,150,'SN74HCT245N')+ic(340,80,165,150,'SN74LVC245AN')
a+=text(175,44,'U1: FPGA 3.3 V -> LED 5 V data',14,'#192b3d','middle')+text(420,65,'U2: HDMI 5 V -> Due 3.3 V status',13,'#192b3d','middle')
a+=rect(265,95,46,16,'#dac59b','#6f6450',5)+line(275,95,275,111,'#d67c2c',4)+line(286,95,286,111,'#d67c2c',4)+line(298,95,298,111,'#794a26',4)
a+=circle(285,185,25,'#303d4b','#b6bec4',4)+text(285,191,'+',17,'white','middle')+text(284,224,'C3',10,'#21384c','middle')
for x,y in [(80,250),(320,250)]:a+=rect(x,y,22,17,'#cf9e3c',rx=5)
a+=text(295,289,'R6 / R7: 10k NES DATA pull-ups to JA6',13,'#192b3d','middle')
a+=text(300,329,'Illustrative assembly - build internal wiring from sheets 02 and 03.',12,'#192b3d','middle')
apins=[]
left=[('led_in','JA4 LED',70),('gnd','GND',115),('status_out','D8 status',165),('3v3','Due 3V3',210),('fpga3v3','JA6 3V3',255),('data1','JA3 DATA1',285),('data2','JA9 DATA2',310)]
right=[('led_out','LED DIN',70),('led5','LED +5V',115),('ledgnd','LED GND',160),('status_in','SW STATUS',215),('swgnd','SW GND',260)]
for key,label,y in left:
 a+=rect(0,y-8,24,16,'#225c7a',rx=2)+text(30,y+4,label,10,'#152d42');apins.append((key,label,8,y,'L'))
for key,label,y in right:
 a+=rect(596,y-8,24,16,'#225c7a',rx=2)+text(590,y+4,label,10,'#152d42','end');apins.append((key,label,612,y,'R'))
for key,x,label in [('5',540,'5V IN'),('pgnd',580,'GND')]:a+=rect(x-10,0,20,25,'#225c7a',rx=2)+text(x,40,label,9,'#152d42','middle');apins.append((key,label,x,8,'T'))
adapter=RealPart('real_adapter','LED and status interface assembly',620,350,apins,a,buses=[['gnd','pgnd','ledgnd','swgnd'],['5','led5']])
# Monitor.
a=rect(0,0,600,340,'#232c37','#101924',15,4)+rect(22,22,556,293,'#0b1523',rx=5)+rect(262,340,76,40,'#343e4b',rx=3)+rect(185,375,230,17,'#434d58',rx=8)
a+=text(56,70,'ARCADE',30,'#74ded0',weight='bold')+text(56,100,'SELECT FPGA BITSTREAM',14,'#a9bace')
for i,game in enumerate(['NES Mario','Breakout','Flappy Bird']):
 a+=rect(54,125+i*54,488,42,'#1c6573' if i==0 else '#1b2838',rx=5)+text(76,153+i*54,game,18)
a+=text(300,331,'HDMI',10,'#b2becb','middle')
mon=RealPart('real_monitor','Monitor',600,395,[('hdmi','HDMI',300,340,'B')],a)
# Switch and manual silver contact terminals.
a=rect(15,5,370,170,'#323d49','#16212e',9,3)+rect(24,15,352,150,'#75808c',rx=6)
a+=socket(0,37,45,40)+socket(0,106,45,40)+socket(355,70,45,40)
a+=text(73,61,'IN 1 / PI',15,'#eef3f8')+text(73,131,'IN 2 / FPGA',15,'#eef3f8')+text(315,96,'OUT',15,'#eef3f8','end')
a+=circle(219,79,18,'#29323b','#d5dce2',2)+text(218,125,'HDMI SWITCH',16,'#f1f5f7','middle')
for x,l in [(170,'STATUS'),(240,'BTN'),(310,'COM')]:a+=rect(x-10,162,20,18,'#353f49')+text(x,157,l,10,'#f3f6f9','middle')
hdmi=RealPart('real_hdmi','HDMI switch - illustrative',400,185,[('in1','HDMI 1',0,57,'L'),('in2','HDMI 2',0,126,'L'),('out','HDMI out',400,90,'R'),('status','STATUS 5V',170,180,'B'),('toggle','Button NO',240,180,'B'),('gnd','Switch GND',310,180,'B')],a)
# Trackball and a separate SK6812 RGB strip.
a=rect(15,30,280,260,'#242d36','#111b26',16,3)+holes(310,320)+circle(155,155,117,'#151d26','#5f6b78',5)+circle(155,147,105,'#dde4ea','#91a4b5',3)+circle(139,130,82,'#eaf1f4')+f'<path d="M83 108 A80 80 0 0 1 172 64" fill="none" stroke="white" stroke-width="20" opacity=".7"/>'
a+=text(155,279,'3 inch USB TRACKBALL',15,'white','middle')+rect(0,249,42,14,'#293440',rx=3)
track=RealPart('real_trackball','Trackball - illustrative',310,320,[('usb','USB mouse cable',0,256,'L')],a)
a=rect(0,0,320,85,'#f0eee5','#a5a99d',3,2)
for i in range(4):
 x=45+i*75;a+=rect(x-23,12,46,46,'#e1e5df','#b3b9b0',3)+circle(x,35,15,'#d5dbd2')+circle(x-7,32,5,'#dd5b60')+circle(x+7,32,5,'#62a772')+circle(x,42,5,'#6394cf')+text(x,75,'LED'+str(i+1),10,'#314458','middle')
for y,l in [(15,'5V'),(40,'DIN'),(65,'GND')]:a+=rect(0,y-5,15,10,'#d4b267')
strip=RealPart('real_strip','SK6812 RGB strip - 3 or 4 pixels',320,85,[('5','+5 V',8,15,'L'),('din','DIN',8,40,'L'),('gnd','GND',8,65,'L')],a)
# Powered stereo pair.
a=''
for x in [0,125]:
 a+=rect(x,0,105,260,'#28313c','#111a24',12,3)+circle(x+52,67,27,'#131d2a','#697786',3)+circle(x+52,165,42,'#131b26','#697786',3)+circle(x+52,165,18,'#3c4855')
a+=rect(0,239,16,13,'#3c8d70')
spk=RealPart('real_speakers','Powered speakers',230,270,[('audio','3.5mm stereo',8,245,'L')],a)
a=rect(0,0,230,110,'#343d49','#192432',8,3)+text(18,34,'REGULATED 5 V',18)+text(18,62,'LED SUPPLY',15)+text(18,89,'>=1 A',16)
for y,col in [(36,'#ce4b4b'),(80,'#222a34')]:a+=rect(205,y-10,25,20,col,'#a7b0b8',2)
psu=RealPart('real_led_supply','LED 5 V supply',230,110,[('5','5 V',223,36,'R'),('gnd','GND',223,80,'R')],a)
# Compose the fourth sheet.
s=Sheet('04-realistic-breadboard','ARCADE / Physical wiring view','Fritzing-style board artwork and physical harnesses. Not to scale. Detailed pin and component wiring: sheets 02 / 03.',2800,2380)
for name,p,x,y in [('Monitor',mon,1020,140),('Pi',pi,150,620),('HDMI switch',hdmi,1100,700),('FPGA',nexys,1950,500),('Speakers',spk,2450,100),('Due',due,700,1110),('Interface',adapter,1600,1560),('Trackball',track,2360,1370),('Pixels',strip,2350,1850),('LED power',psu,1600,2050),('Silver button',buttons['silver'],1570,850)]:s.add(name,p,x,y)
for player,jx,bx in [(1,90,330),(2,800,1040)]:
 s.add(f'P{player} joystick',joy,jx,1740)
 for name,xx,yy,col in [('START',bx,1720,'white'),('SELECT',bx+160,1720,'white'),('A',bx,1920,'red'),('B',bx+160,1920,'blue')]:s.add(f'P{player} {name}',buttons[col],xx,yy)
 s.label(jx,1665,f'PLAYER {player} / internal INPUT_PULLUP on all 8 contacts',size=18)
 for n in ['A','B','SELECT','START','UP','DOWN','LEFT','RIGHT']:
  i=['A','B','SELECT','START','UP','DOWN','LEFT','RIGHT'].index(n);dpin='D'+str(22+(player-1)*8+i)
  endpoint=(f'P{player} joystick',n) if n in ['UP','DOWN','LEFT','RIGHT'] else (f'P{player} {n}','NO')
  ax,ay=s.point(endpoint);dx,dy=s.point(('Due',dpin));corridor=(655 if player==1 else 1345)+i*9;top=1530+i*10
  s.wire(endpoint,('Due',dpin),f'P{player}_{n}',f'p{player}',[(corridor,ay),(corridor,top),(1460+i*9,top),(1460+i*9,dy)])
 for name in [f'P{player} joystick',*[f'P{player} {n}' for n in ['START','SELECT','A','B']]]:
  x,y=s.point((name,'COM'));s.wire((name,'COM'),('Due','gnd2'),name+'_GND','ground',[(x+12,y),(x+12,2150+player*18),(1430,2150+player*18),(1430,s.point(('Due','gnd2'))[1])])
# Controller serial lines from real Due pin centers to JA inset.
for i,(d,j) in enumerate([('D2','1'),('D3','2'),('D4','3'),('D5','7'),('D6','8'),('D7','9')]):
 x,y=s.point(('Due',d));jx,jy=s.point(('FPGA',j));s.wire(('Due',d),('FPGA',j),'NES_'+d,'p1' if i<3 else 'p2',[(x,1030-i*10),(1560+i*10,1030-i*10),(1560+i*10,1230+i*12),(2715+i*9,1230+i*12),(2715+i*9,jy)])
# Ground, translators and external NES pull-ups on the illustrative interface assembly.
s.wire(('Due','gnd2'),('Interface','gnd'),'COMMON_GND','ground',[(1450,s.point(('Due','gnd2'))[1]),(1450,1675)])
s.wire(('Due','3v3'),('Interface','3v3'),'DUE_3V3','power3',[(s.point(('Due','3v3'))[0],1505),(1550,1505),(1550,1770)])
s.wire(('Due','D8'),('Interface','status_out'),'HDMI_STATUS_3V3','status',[(s.point(('Due','D8'))[0],1050),(1560,1050),(1560,1725)])
for j,k in [('4','led_in'),('5','gnd'),('6','fpga3v3'),('3','data1'),('9','data2'),('11','gnd')]:
 x,y=s.point(('FPGA',j));dx,dy=s.point(('Interface',k));ix=list(['4','5','6','3','9','11']).index(j);route=2290+ix*9
 s.wire(('FPGA',j),('Interface',k),'JA'+j+'_INTERFACE','ground' if j in ['5','11'] else ('power3' if j=='6' else 'led' if j=='4' else 'p1' if j=='3' else 'p2'),[(2700+ix*9,y),(2700+ix*9,1270+ix*15),(route,1270+ix*15),(route,1510-ix*12),(1540-ix*9,1510-ix*12),(1540-ix*9,dy)])
# Complete cables: USB/HDMI/audio are bundled, not individual conductors.
s.wire(('Pi','usb_due'),('Due','usb'),'USB_HID','usb',[(680,875),(680,1223)])
s.wire(('Pi','usb_jtag'),('FPGA','jtag'),'USB_JTAG','usb',[(670,918),(670,985),(1875,985),(1875,1140)])
s.wire(('Pi','hdmi'),('HDMI switch','in1'),'HDMI_PI','hdmi',[(305,1000),(1020,1000),(1020,757)])
s.wire(('FPGA','hdmi'),('HDMI switch','in2'),'HDMI_FPGA','hdmi',[(2154,425),(1880,425),(1880,915),(1045,915),(1045,826)])
s.wire(('HDMI switch','out'),('Monitor','hdmi'),'HDMI_MONITOR','hdmi',[(1540,790),(1540,560),(1320,560)])
s.wire(('FPGA','audio'),('Speakers','audio'),'STEREO_AUDIO','audio',[(2525,410),(2420,410),(2420,345)])
s.wire(('FPGA','usb'),('Trackball','usb'),'USB_MOUSE','usb',[(1900,973),(1900,1280),(2320,1280),(2320,1626)])
s.wire(('HDMI switch','status'),('Interface','status_in'),'HDMI_STATUS_5V','status',[(1270,1010),(1850,1010),(1850,1340),(2240,1340),(2240,1775)])
s.wire(('HDMI switch','gnd'),('Interface','swgnd'),'HDMI_GND','ground',[(1410,1025),(1830,1025),(1830,1360),(2250,1360),(2250,1820)])
s.wire(('Silver button','NO'),('HDMI switch','toggle'),'SILVER_BUTTON_NO','toggle',[(1720,958),(1720,1020),(1530,1020),(1530,900),(1340,900)])
s.wire(('Silver button','COM'),('HDMI switch','gnd'),'SILVER_BUTTON_COM','ground',[(1735,978),(1735,1035),(1515,1035),(1515,925),(1410,925)])
for a,b,color in [('led_out','din','led'),('led5','5','power5'),('ledgnd','gnd','ground')]:
 x,y=s.point(('Interface',a));px,py=s.point(('Pixels',b));s.wire(('Interface',a),('Pixels',b),'STRIP_'+a,color,[(2300+(0 if a=='led_out' else 12 if a=='led5' else 24),y),(2300+(0 if a=='led_out' else 12 if a=='led5' else 24),py)])
for a,b in [('5','5'),('gnd','pgnd')]:
 x,y=s.point(('LED power',a));px,py=s.point(('Interface',b));s.wire(('LED power',a),('Interface',b),'LED_POWER_'+a,'power5' if a=='5' else 'ground',[(2240 if a=='5' else 2260,y),(2240 if a=='5' else 2260,1480),(px,1480)])
# Board labels and essential cautions are actual note parts, so they appear in Fritzing too.
notes=note('realistic_note','Physical view notes',['Silver button -> HDMI switch directly. D9 is unused.','HDMI 5 V status -> U2 -> Due D8 controls exclusive input routing.','JA6 feeds only R6/R7 NES pull-ups; external 5 V powers LEDs.','Pi 4B artwork is illustrative: actual Pi model is unspecified.','Nexys Video / trackball / interface artwork is illustrative.','JA pin numbers and internal assembly wiring: see sheets 02 / 03.'],w=900)
s.add('Physical view notes',notes,105,120)
s.label(700,1085,'ARDUINO DUE / NATIVE USB',size=21)
s.label(150,590,'RASPBERRY PI / USB HOST + HDMI',size=21)
s.label(1950,470,'NEXYS VIDEO / JA1-3 + JA7-9 / JA4 LED DATA',size=21)
s.label(1570,825,'SILVER HDMI BUTTON',size=16)
s.label(1600,1535,'INTERFACE ASSEMBLY / INTERNAL WIRING ON 02 AND 03',size=17)
s.label(2360,1340,'TRACKBALL',size=20)
s.label(2350,1830,'SK6812 / UNDER TRACKBALL',size=16)
s.label(105,2280,'Board illustration adapted from Fritzing artwork; CC BY-SA 3.0. See assets/ATTRIBUTION.md.',size=14)
# Small button instance labels.
for name,it in s.items.items():
 if name.startswith('P') and any(name.endswith(' '+n) for n in ['START','SELECT','A','B']):s.label(it['x'],it['y']-12,name,size=15)
meta4=s.save()
# Slightly thicker, rounded wires for the physical illustration and native breadboard view.
fz=E.parse(OUT/(s.name+'.fz')).getroot()
for w in fz.findall('./instances/instance'):
 if w.get('moduleIdRef')=='WireModuleID':
  for ex in w.findall('./views/breadboardView/wireExtras'):ex.set('mils','28')
# Label all physical instances where their source artwork is deliberately generic.
for inst in fz.findall('./instances/instance'):
 title=inst.findtext('title','')
 if title in s.items and title!='Physical view notes':
  it=s.items[title]
  for view in ['breadboardView','schematicView']:
   tg=sub(inst.find('./views/'+view),'titleGeometry',visible='true',x=it['x'],y=it['y']-20,z=5.5,xOffset=0,yOffset=-20,textColor='#17304b',fontSize=10);sub(tg,'displayKey',key='')
(OUT/(s.name+'.fz')).write_bytes(xml(fz))
with zipfile.ZipFile(OUT/(s.name+'.fzz'),'w',zipfile.ZIP_DEFLATED) as z:
 z.writestr(s.name+'.fz',xml(fz))
 for p in {it['part'].key:it['part'] for it in s.items.values()}.values():
  for name,path in p.files():z.write(path,name)
preview=PRE/(s.name+'.svg');r=E.parse(preview).getroot()
for child in list(r):
 if child.tag.rsplit('}',1)[-1]=='polyline':child.set('stroke-width','4');child.set('stroke-linecap','round')
preview.write_bytes(xml(r))
metadata.append(meta4);(OUT/'design-data.json').write_text(json.dumps(metadata,indent=2))
with (OUT/'connections.csv').open('w',newline='') as f:
 writer=csv.writer(f,lineterminator="\n");writer.writerow(['sheet','net','from_part','from_pin','to_part','to_pin'])
 for sh in metadata:
  for wire in sh['wires']:writer.writerow([sh['sheet'],wire['net'],*wire['a'],*wire['b']])
print('Added realistic breadboard sheet:',len(s.items),'parts and',len(s.wires),'wire runs.')
