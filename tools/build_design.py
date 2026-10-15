#!/usr/bin/env python3
"""Build self-contained Fritzing wiring documentation, custom parts and SVG previews."""
from pathlib import Path
from xml.etree import ElementTree as E
from html import escape
from collections import defaultdict
import zipfile, json, csv
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'design'; PARTS=OUT/'parts'; PRE=OUT/'previews'
for p in (PARTS,PRE): p.mkdir(parents=True,exist_ok=True)
NS='http://www.w3.org/2000/svg'
def sub(p,t,**a): return E.SubElement(p,t,{k:str(v) for k,v in a.items()})
def xml(r): return E.tostring(r,encoding='utf-8',xml_declaration=True)
def txt(x,y,s,size=14,fill='#17304b',anchor='start',weight='normal'):
 return f'<text x="{x}" y="{y}" font-family="Droid Sans,DejaVu Sans,sans-serif" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{escape(str(s))}</text>'
COLORS={'ground':'#445366','power5':'#d43c38','power3':'#d08222','p1':'#2177b6','p2':'#8a50b4','led':'#18977d','status':'#bc5d19','toggle':'#b65078','usb':'#336b97','hdmi':'#6c6caf','audio':'#489177','signal':'#5a7184'}
class Part:
 def __init__(self,key,title,w,h,pins,notes=(),color='#e8f1f8',kind='module',buses=()):
  self.key=key;self.title=title;self.w=w;self.h=h;self.notes=notes;self.color=color;self.kind=kind
  # pin entries: unique key, label, x, y, label side L/R/T/B
  self.pins={k:dict(id=f'connector{i}',label=l,x=x,y=y,side=s) for i,(k,l,x,y,s) in enumerate(pins)}
  self.buses=buses;self.module='arcade_'+key+'_v1';self.write()
 def svg(self,layer):
  w,h=self.w,self.h
  if self.key in ['resistor','nes_pullup','capacitor','electrolytic']:
   shape = '<rect x="35" y="40" width="80" height="26" fill="#fff4dc" stroke="#516b85" stroke-width="2"/>' if self.key in ['resistor','nes_pullup'] else '<path d="M68 32 V74 M82 32 V74" stroke="#516b85" stroke-width="3"/>'
   x1,x2=(35,115) if self.key in ['resistor','nes_pullup'] else (68,82)
   return f'<svg xmlns="{NS}" width="{w/90:.7f}in" height="{h/90:.7f}in" viewBox="0 0 {w} {h}"><g id="{layer}"><path d="M0 53 H{x1} M{x2} 53 H150" fill="none" stroke="#516b85" stroke-width="2"/>'+shape+(txt(50,38,'+',16) if self.key=='electrolytic' else '')+''.join(f'<circle id="{p["id"]}pin" cx="{p["x"]}" cy="53" r="4" fill="#dfb65c"/><rect id="{p["id"]}terminal" x="{p["x"]-.5}" y="52.5" width="1" height="1" fill="none"/>' for p in self.pins.values())+'</g></svg>'
  z=[f'<svg xmlns="{NS}" width="{w/90:.7f}in" height="{h/90:.7f}in" viewBox="0 0 {w} {h}"><g id="{layer}">']
  if self.kind=='note':
   z += [f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="8" fill="{self.color}" stroke="#adc0d1"/>',txt(16,29,self.title,18,weight='bold')]
  else:
   z += [f'<rect x="12" y="12" width="{w-24}" height="{h-24}" rx="9" fill="{self.color}" stroke="#516b85" stroke-width="1.7"/>',txt(w/2,39,'' if self.key=='button' else self.title,16,anchor='middle',weight='bold')]
  for i,n in enumerate(self.notes): z.append(txt(18,62+i*19,n,12,fill='#49627a'))
  for k,p in self.pins.items():
   x,y,s,c=p['x'],p['y'],p['side'],p['id']
   if s=='L': x2,y2=20,y; tx,ty,anc=26,y+4,'start'
   elif s=='R': x2,y2=w-20,y;tx,ty,anc=w-26,y+4,'end'
   elif s=='T': x2,y2=x,20;tx,ty,anc=x,35,'middle'
   else: x2,y2=x,h-20;tx,ty,anc=x,h-29,'middle'
   z += [f'<line x1="{x}" y1="{y}" x2="{x2}" y2="{y2}" stroke="#6c8297" stroke-width="2"/>',f'<circle id="{c}pin" cx="{x}" cy="{y}" r="4" fill="#dfb65c" stroke="#725b28" stroke-width="1"/>',f'<rect id="{c}terminal" x="{x-.5}" y="{y-.5}" width="1" height="1" fill="none"/>',txt(tx,ty,p['label'],12,anchor=anc)]
  if self.kind=='note': pass
  return ''.join(z)+ '</g></svg>'
 def write(self):
  root=E.Element('module',{'moduleId':self.module,'fritzingVersion':'1.0.1','referenceFile':self.key+'.fzp'})
  for t,v in [('version','1'),('author','Arcade cabinet design'),('title',self.title),('label',self.title),('date','2026-10-14'),('description','Logical wiring symbol. Connector labels identify real board pins or complete cables. Not a physical board footprint. PCB fabrication is not supported by this documentation part.')]: sub(root,t).text=v
  tags=sub(root,'tags');sub(tags,'tag').text='arcade'
  props=sub(root,'properties');sub(props,'property',name='family').text='Arcade documentation '+self.key
  vs=sub(root,'views')
  for view,layer in [('iconView','icon'),('breadboardView','breadboard'),('schematicView','schematic')]:
   folder=view.replace('View','');v=sub(vs,view);ls=sub(v,'layers',image=folder+'/'+self.key+'.svg');sub(ls,'layer',layerId=layer)
   (PARTS/f'{self.key}_{folder}.svg').write_text(self.svg(layer))
  # Deliberately no copper or PCB connectors: these are harness documentation symbols.
  v=sub(vs,'pcbView');ls=sub(v,'layers',image='pcb/'+self.key+'.svg');sub(ls,'layer',layerId='silkscreen')
  (PARTS/f'{self.key}_pcb.svg').write_text(f'<svg xmlns="{NS}" width="1in" height=".3in" viewBox="0 0 90 27"><g id="silkscreen">'+txt(1,12,'WIRING ONLY',8)+txt(1,23,'NO PCB FOOTPRINT',7)+'</g></svg>')
  cs=sub(root,'connectors')
  for k,p in self.pins.items():
   c=sub(cs,'connector',id=p['id'],type='male',name=p['label']);sub(c,'description').text=k;v=sub(c,'views')
   for view,layer in [('breadboardView','breadboard'),('schematicView','schematic')]: sub(sub(v,view),'p',layer=layer,svgId=p['id']+'pin',terminalId=p['id']+'terminal')
  if self.buses:
   bs=sub(root,'buses')
   for i,bus in enumerate(self.buses):
    b=sub(bs,'bus',id='bus'+str(i))
    for k in bus: sub(b,'nodeMember',connectorId=self.pins[k]['id'])
  (PARTS/(self.key+'.fzp')).write_bytes(xml(root))
  with zipfile.ZipFile(PARTS/(self.key+'.fzpz'),'w',zipfile.ZIP_DEFLATED) as z:
   z.write(PARTS/(self.key+'.fzp'),'part.'+self.key+'.fzp')
   for folder in ['icon','breadboard','schematic','pcb']: z.write(PARTS/f'{self.key}_{folder}.svg',f'svg.{folder}.{self.key}.svg')
 def files(self):
  return [('part.'+self.key+'.fzp',PARTS/(self.key+'.fzp'))]+[(f'svg.{f}.{self.key}.svg',PARTS/f'{self.key}_{f}.svg') for f in ['icon','breadboard','schematic','pcb']]
class Sheet:
 def __init__(self,name,title,subtitle,w,h): self.name=name;self.title=title;self.subtitle=subtitle;self.w=w;self.h=h;self.items={};self.wires=[];self.labels=[]
 def add(self,name,p,x,y): self.items[name]=dict(part=p,x=x,y=y,index=100+len(self.items)*10);return name
 def point(self,e):
  name,k=e;p=self.items[name];c=p['part'].pins[k];return (p['x']+c['x'],p['y']+c['y'])
 def wire(self,a,b,net,color='signal',via=()):
  self.wires.append(dict(a=a,b=b,net=net,color=COLORS.get(color,color),pts=[self.point(a),*via,self.point(b)]))
 def label(self,x,y,s,color='#516b85',size=12): self.labels.append(txt(x,y,s,size,fill=color))
 def save(self):
  root=E.Element('module',{'fritzingVersion':'1.0.1','icon':'.png'})
  views=sub(root,'views')
  for v,bg in [('breadboardView','#ffffff'),('schematicView','#ffffff'),('pcbView','#333333')]:sub(views,'view',name=v,backgroundColor=bg,gridSize='0.1in',showGrid='0',alignToGrid='0',viewFromBelow='0')
  ins=sub(root,'instances');refs={}; conns=defaultdict(list)
  for name,it in self.items.items():
   p=it['part'];r=sub(ins,'instance',moduleIdRef=p.module,modelIndex=it['index'],path=p.key+'.fzp');sub(r,'title').text=name;vs=sub(r,'views')
   for v,layer in [('breadboardView','breadboard'),('schematicView','schematic')]:
    vv=sub(vs,v,layer=layer);sub(vv,'geometry',x=it['x'],y=it['y'],z='2.0');refs[name,v]=sub(vv,'connectors')
    if p.key in ['resistor','nes_pullup','capacitor','electrolytic','button','joystick','panel','sk6812']:
     tg=sub(vv,'titleGeometry',visible='true',x=it['x']+(26 if p.key=='button' else 0),y=it['y']+(22 if p.key=='button' else -14),z=5.5,xOffset=(26 if p.key=='button' else 0),yOffset=(22 if p.key=='button' else -14),textColor='#17304b',fontSize=9);sub(tg,'displayKey',key='')
   v=sub(vs,'pcbView',layer='silkscreen');sub(v,'geometry',x=0,y=0,z=-1)
  # Wire instances are separate for each visible view, as required by Fritzing wireFlags.
  index=10000
  for wire in self.wires:
   pts=wire['pts']
   for target,flags in [('breadboardView',64),('schematicView',128)]:
    segments=[]
    for a,b in zip(pts,pts[1:]):
     if a!=b:segments.append((index,a,b));index+=1
    if not segments: raise ValueError('zero length wire')
    for j,(idx,a,b) in enumerate(segments):
     r=sub(ins,'instance',moduleIdRef='WireModuleID',modelIndex=idx,path=':/resources/parts/core/wire.fzp');sub(r,'title').text=wire['net'];vs=sub(r,'views')
     for view,layer,partlayer in [('breadboardView','breadboardWire','breadboard'),('schematicView','schematicTrace','schematic')]:
      v=sub(vs,view,layer=layer);sub(v,'geometry',x=a[0],y=a[1],x1=0,y1=0,x2=b[0]-a[0],y2=b[1]-a[1],z=3.5,wireFlags=flags)
      sub(v,'wireExtras',mils=12,color=wire['color'],opacity=1,banded=0)
      cs=sub(v,'connectors')
      for end in (0,1):
       c=sub(cs,'connector',connectorId='connector'+str(end),layer=layer);sub(c,'geometry',x=0,y=0);links=sub(c,'connects')
       if end==0 and j==0: ep=wire['a']
       elif end==1 and j==len(segments)-1: ep=wire['b']
       else: ep=None
       if ep:
        ni,k=ep;it=self.items[ni];cid=it['part'].pins[k]['id'];sub(links,'connect',connectorId=cid,modelIndex=it['index'],layer=partlayer)
        conns[ni,view,cid].append((idx,'connector'+str(end),layer))
       else:
        adjacent=segments[j-1][0] if end==0 else segments[j+1][0]
        sub(links,'connect',connectorId='connector1' if end==0 else 'connector0',modelIndex=adjacent,layer=layer)
     v=sub(vs,'pcbView',layer='copper1trace');sub(v,'geometry',x=a[0],y=a[1],z=-1,x1=0,y1=0,x2=b[0]-a[0],y2=b[1]-a[1],wireFlags=flags)
  for (name,v,cid),links in conns.items():
   layer='breadboard' if v=='breadboardView' else 'schematic';c=sub(refs[name,v],'connector',connectorId=cid,layer=layer);sub(c,'geometry',x=0,y=0);cs=sub(c,'connects')
   for idx,connector,wl in links:sub(cs,'connect',connectorId=connector,modelIndex=idx,layer=wl)
  fz=xml(root);(OUT/(self.name+'.fz')).write_bytes(fz)
  used={i['part'].key:i['part'] for i in self.items.values()}
  with zipfile.ZipFile(OUT/(self.name+'.fzz'),'w',zipfile.ZIP_DEFLATED) as z:
   z.writestr(self.name+'.fz',fz)
   for p in used.values():
    for name,path in p.files():z.write(path,name)
  # Readable preview drawn from exactly the same parts and wire endpoint data.
  z=[f'<svg xmlns="{NS}" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}"><rect width="100%" height="100%" fill="white"/>',txt(30,38,self.title,26,weight='bold'),txt(30,65,self.subtitle,14),'<line x1="30" y1="82" x2="'+str(self.w-30)+'" y2="82" stroke="#b9cad8"/>']
  for it in self.items.values():
   s=it['part'].svg('breadboard');inside=s[s.index('<g '):s.rindex('</svg>')];z.append(f'<g transform="translate({it["x"]},{it["y"]})">{inside}</g>')
  for wire in self.wires:
   z.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in wire['pts'])+f'" fill="none" stroke="{wire["color"]}" stroke-width="2.2" stroke-linejoin="round"/>')

  for name,it in self.items.items():
   if it['part'].key in ['resistor','nes_pullup','capacitor','electrolytic','button','joystick','panel','sk6812']: z.append(txt(it['x']+(125 if it['part'].key=='button' else 0),it['y']+(39 if it['part'].key=='button' else -8),name,16 if it['part'].key=='button' else 12,anchor='middle' if it['part'].key=='button' else 'start',weight='bold'))
  z+=self.labels
  z += [txt(30,self.h-22,'ARCADE | 2026-10-14 | Wiring documentation - logical connector positions; no PCB fabrication.',12),'</svg>']
  (PRE/(self.name+'.svg')).write_text(''.join(z))
  return dict(sheet=self.name,title=self.title,items={name:dict(part=it['part'].key,pins=it['part'].pins,index=it['index']) for name,it in self.items.items()},wires=self.wires)
def block(key,title,w,left=(),right=(),notes=(),color='#e8f1f8',h=None,start=100,pitch=24,buses=()):
 h=h or max(start+max(len(left),len(right))*pitch+15,130)
 pins=[(k,l,0,start+i*pitch,'L') for i,(k,l) in enumerate(left)]+[(k,l,w,start+i*pitch,'R') for i,(k,l) in enumerate(right)]
 return Part(key,title,w,h,pins,notes,color,buses=buses)
def note(key,title,lines,w=600,h=None):return Part(key,title,w,h or 83+19*len(lines),[],lines,'#fff5dd','note')
metadata=[]
# 01 - whole cabinet cable and harness overview.
s=Sheet('01-arcade-system','ARCADE / Cabinet interconnect','Complete cables are represented by one logical connector. Use sheets 02 and 03 for individual conductors.',1680,1420)
pi=block('pi','Raspberry Pi / kiosk',280,right=[('usb_due','USB host -> Due Native'),('usb_jtag','USB host -> FPGA PROG'),('hdmi','HDMI output')],notes=['Bitstream menu + loader','Model unspecified; normal Pi PSU'])
due=block('due_overview','Arduino Due',300,left=[('usb','Native USB / HID'),('p1','P1 / 8 inputs + GND'),('p2','P2 / 8 inputs + GND')],right=[('p1nes','P1 NES / D2 D3 D4'),('p2nes','P2 NES / D5 D6 D7'),('switch','Status / D8 GND')],notes=['USB powered by Pi','3.3 V I/O; INPUT_PULLUP'])
fpga=block('nexys_overview','Digilent Nexys Video',320,left=[('jtag','PROG micro-USB / JTAG'),('p1','JA1 / JA2 / JA3'),('p2','JA7 / JA8 / JA9')],right=[('hdmi','HDMI OUT'),('audio','Green LINE OUT'),('usb','J15 USB HOST'),('led','JA4 / LED data'),('gnd','JA5 + JA11 / GND')],notes=['Own board-rated power supply','JA6: NES pull-ups; JA12: NC'],h=250)
switch=block('hdmi_overview','HDMI switch',300,left=[('in1','Input 1 / Pi'),('in2','Input 2 / FPGA'),('control','Status 5 V + GND'),('button','Silver button / NO + COM')],right=[('out','HDMI to monitor')],notes=['ASIN B0F6LM1578','5 V controls per owner; verify taps'])
monitor=block('monitor','Monitor',210,left=[('hdmi','HDMI input')],notes=['Own power supply'])
track=block('trackball','3 inch USB trackball',280,left=[('usb','USB cable / mouse')],notes=['RetroArcade.us / B0711TKGFV','Original lighting is separate'])
speakers=block('speakers','Powered speakers',230,left=[('audio','3.5 mm stereo input')],notes=['Or amplifier + passive speakers'])
ledmod=block('led_module','LED interface / sheet 03',300,left=[('data','JA4 / 3.3 V data'),('gnd','GND')],right=[('strip','5 V + data + GND')],notes=['FPGA 3.3 V -> LED 5 V data','SN74HCT245N + 330 ohm'])
strip=block('strip_overview','3-4 SK6812 RGB pixels',300,left=[('in','5 V / DIN / GND')],notes=['Under trackball; daisy-chain data','Use four pixels; fourth optional'])
ctrlmod=block('switch_module','HDMI status / sheet 03',300,left=[('due','Due D8 / GND')],right=[('switch','STATUS_5V / GND')],notes=['HDMI 5 V -> Due 3.3 V status','SN74LVC245AN; status only'])
ctrl=block('panel','Player controls',290,right=[('bundle','8 NO contacts + common GND')],notes=['4 joystick directions','Start, Select, A, B'])
s.add('Pi',pi,50,140);s.add('Due',due,480,140);s.add('FPGA',fpga,950,140)
s.add('Player 1',ctrl,50,500);s.add('Player 2',ctrl,50,720)
s.add('HDMI switch',switch,480,960);s.add('Monitor',monitor,960,960)
s.add('Speakers',speakers,1400,140);s.add('Trackball',track,1320,460)
s.add('LED buffer',ledmod,950,710);s.add('Pixels',strip,1320,710)
s.add('Switch interface',ctrlmod,480,500)
silver=block('silver_overview','Silver HDMI button',290,right=[('pair','NO + COM / switch only')],notes=['Manual video source selection','Not connected to Pi or Due'])
s.add('Silver button',silver,50,970)
s.add('Read me',note('overview_note','Power and configuration',['Pi powers the Due through Native USB. FPGA has its own supply.','LEDs use a regulated 5 V supply; never use JA power pins for LEDs.','Join low-voltage grounds; never join independent 3.3 V / 5 V outputs.','The bitstream must implement NES input, PS/2 mouse, LEDs and audio.','The Pi needs a compatible ARM JTAG loader and board/cable support.'],w=700),50,1180)
s.wire(('Pi','usb_due'),('Due','usb'),'USB_HID','usb',[(400,240)])
s.wire(('Pi','usb_jtag'),('FPGA','jtag'),'USB_JTAG','usb',[(370,264),(370,110),(880,110),(880,240)])
s.wire(('Due','p1nes'),('FPGA','p1'),'P1_NES','p1',[(850,240),(850,264)])
s.wire(('Due','p2nes'),('FPGA','p2'),'P2_NES','p2',[(865,264),(865,288)])
s.wire(('Player 1','bundle'),('Due','p1'),'P1_CONTROLS','p1',[(390,600),(390,264)])
s.wire(('Player 2','bundle'),('Due','p2'),'P2_CONTROLS','p2',[(415,820),(415,288)])
s.wire(('Pi','hdmi'),('HDMI switch','in1'),'HDMI_PI','hdmi',[(355,288),(355,1060)])
s.wire(('FPGA','hdmi'),('HDMI switch','in2'),'HDMI_FPGA','hdmi',[(1290,240),(1290,920),(440,920),(440,1084)])
s.wire(('HDMI switch','out'),('Monitor','hdmi'),'HDMI_MONITOR','hdmi')
s.wire(('FPGA','audio'),('Speakers','audio'),'STEREO_AUDIO','audio',[(1350,264),(1350,240)])
s.wire(('FPGA','usb'),('Trackball','usb'),'USB_MOUSE','usb',[(1300,288),(1300,560)])
s.wire(('FPGA','led'),('LED buffer','data'),'LED_DATA_3V3','led',[(1280,312),(1280,670),(900,670),(900,810)])
s.wire(('FPGA','gnd'),('LED buffer','gnd'),'GROUND','ground',[(1265,336),(1265,650),(885,650),(885,834)])
s.wire(('LED buffer','strip'),('Pixels','in'),'LED_HARNESS','led')
s.wire(('Due','switch'),('Switch interface','due'),'SWITCH_DUE','status',[(820,288),(820,460),(450,460),(450,600)])
s.wire(('Switch interface','switch'),('HDMI switch','control'),'SWITCH_STATUS','status',[(805,600),(805,900),(455,900),(455,1108)])
s.wire(('Silver button','pair'),('HDMI switch','button'),'MANUAL_HDMI_BUTTON','toggle',[(430,1070),(430,1132)])
metadata.append(s.save())
# 02 - control wiring, exact screenshot connector mapping.
s=Sheet('02-controls-and-ja','ARCADE / Buttons, joysticks and NES interface','All controls are dry normally-open contacts to GND. No control contact connects to +5 V or +3.3 V.',1690,1870)
controls=['A','B','SELECT','START','UP','DOWN','LEFT','RIGHT']
duepins=[(f'D{22+i}',f'D{22+i} / P1 {n}') for i,n in enumerate(controls)]+[(f'D{30+i}',f'D{30+i} / P2 {n}') for i,n in enumerate(controls)]
duep=block('due_controls','Arduino Due / control pins',340,left=duepins+[('gnd','GND / switch commons')],right=[('D2','D2 / P1 latch IN'),('D3','D3 / P1 clock IN'),('D4','D4 / P1 data OUT'),('D5','D5 / P2 latch IN'),('D6','D6 / P2 clock IN'),('D7','D7 / P2 data OUT'),('gnd2','GND / FPGA reference')],notes=['D22-D37 = INPUT_PULLUP','Pressed = LOW; released = HIGH'],h=550,buses=[['gnd','gnd2']])
ja=block('ja_controls','Nexys Video / JA',320,left=[('1','JA1 / P1 LATCH ->'),('2','JA2 / P1 CLOCK ->'),('3','JA3 / P1 DATA <-'),('7','JA7 / P2 LATCH ->'),('8','JA8 / P2 CLOCK ->'),('9','JA9 / P2 DATA <-'),('5','JA5 / GND'),('11','JA11 / GND')],right=[('6','JA6 / 3.3 V / R6 R7')],notes=['3.3 V logic in both directions','JA4 is LED data on sheet 03'],h=335,buses=[['5','11']])
s.add('Due',duep,650,520);s.add('JA',ja,1240,520)
joystick=block('joystick','4-way joystick contacts',300,right=[('UP','UP / NO'),('DOWN','DOWN / NO'),('LEFT','LEFT / NO'),('RIGHT','RIGHT / NO'),('COM','All COM terminals / GND')],notes=['Mechanical microswitches','Leave NC terminals unused'],h=240)
button=block('button','NO pushbutton',250,right=[('NO','NO / signal'),('COM','COM / GND')],notes=['Normally open contact'],h=120,start=70,pitch=25)
for player,ybase in [(1,150),(2,930)]:
 jn=f'P{player} joystick';s.add(jn,joystick,60,ybase)
 for i,n in enumerate(['UP','DOWN','LEFT','RIGHT']):
  dp=22+(player-1)*8+controls.index(n);s.wire((jn,n),('Due',f'D{dp}'),f'P{player}_{n}',f'p{player}',[(430+i*13,ybase+100+i*24),(430+i*13,620+((player-1)*8+controls.index(n))*24)])
 for i,n in enumerate(['START','SELECT','A','B']):
  bn=f'P{player} {n}';y=ybase+260+i*110;s.add(bn,button,110,y)
  dp=22+(player-1)*8+controls.index(n);desty=620+((player-1)*8+controls.index(n))*24
  s.wire((bn,'NO'),('Due',f'D{dp}'),f'P{player}_{n}',f'p{player}',[(500+i*15,y+70),(500+i*15,desty)])
  s.wire((bn,'COM'),('Due','gnd'),f'GND_P{player}_{n}','ground',[(390,y+95),(390,1760),(610,1760),(610,1004)])
 s.wire((jn,'COM'),('Due','gnd'),f'GND_P{player}_JOY','ground',[(390,ybase+196),(390,1760),(610,1760),(610,1004)])
for i,(d,j) in enumerate([('D2','1'),('D3','2'),('D4','3'),('D5','7'),('D6','8'),('D7','9')]):s.wire(('Due',d),('JA',j),'NES_'+d,'p1' if i<3 else 'p2')
s.wire(('Due','gnd2'),('JA','5'),'GND_JA5','ground')
s.wire(('JA','5'),('JA','11'),'GND_JA11','ground',[(1190,764),(1190,788)])
pullup=Part('nes_pullup','10 kohm NES pull-up',150,75,[('1','1',0,53,'L'),('2','2',150,53,'R')],color='#fff1df')
s.add('R6 10 kohm',pullup,1030,860);s.add('R7 10 kohm',pullup,1030,965)
s.wire(('JA','6'),('R6 10 kohm','1'),'NES_PULLUP_3V3','power3',[(1625,620),(1625,870),(1000,870),(1000,913)])
s.wire(('R6 10 kohm','1'),('R7 10 kohm','1'),'NES_PULLUP_RAIL','power3',[(1000,913),(1000,1018)])
s.wire(('R6 10 kohm','2'),('JA','3'),'P1_DATA_PULLUP','p1',[(1190,913),(1190,668)])
s.wire(('R7 10 kohm','2'),('JA','9'),'P2_DATA_PULLUP','p2',[(1205,1018),(1205,740)])
s.add('JA orientation',note('ja_orientation','JA - front / mating face, as in your screenshot',['Upper row, left to right: 6 | 5 | 4 | 3 | 2 | 1','Lower row, left to right: 12 | 11 | 10 | 9 | 8 | 7','JA6 feeds R6/R7 (10k NES pull-ups); JA12 remains NC.','JA4 = LED data (sheet 03). JA10 = spare / NC.','Use pin numbers and silkscreen; rear cable view is mirrored.'],w=630),1030,1090)
s.add('NES behavior',note('nes_behavior','Firmware contract',['Separate latch and clock lines for each player, exactly as shown.','Due sends active-low serial bits: A, B, Select, Start, Up, Down, Left, Right.','Repository firmware advances on RISING clock edges; verify core timing.','Data outputs are open-drain: LOW or Hi-Z; R6/R7 provide HIGH.','Use a measured timing budget; interrupt-based Arduino code may not','meet a fast core. Slow the FPGA poll clock or use hardware serialization.','USB service and switch debouncing must never block the NES interface.'],w=820),650,1320)
s.add('Contact note',note('contact_note','Controls and ground',['Each joystick uses 4 NO contacts and a shared GND common.','Each player has one Start, Select, A and B: 8 pushbuttons total.','Configure all 16 inputs with INPUT_PULLUP; debounce in firmware.','Due Native USB goes to the Pi USB host. Do not use Programming USB','for HID. Use short signal/common pairs for long cabinet harnesses.'],w=840),650,1560)
metadata.append(s.save())
# 03 - exact LED and status level shifters; independent manual HDMI button.
s=Sheet('03-led-and-hdmi-interfaces','ARCADE / LED and HDMI electrical interfaces','U1 and U2 are the exact DIP-20 parts on the DigiKey invoice. Grounds are shared; positive rails stay separate.',2100,2040)
# Parts use real IC pin numbers and names, arranged by function for readability.
u1=block('hct245','U1 / SN74HCT245N / 5 V',330,left=[('1','1 DIR / tie +5 V'),('2','2 A1 / LED data IN'),('3','3 A2 / GND'),('4','4 A3 / GND'),('5','5 A4 / GND'),('6','6 A5 / GND'),('7','7 A6 / GND'),('8','8 A7 / GND'),('9','9 A8 / GND'),('10','10 GND')],right=[('20','20 VCC / +5 V LED'),('19','19 /OE / GND'),('18','18 B1 / 5 V data OUT')]+[(str(i),f'{i} B{19-i} / NC') for i in range(17,10,-1)],notes=['FPGA 3.3 V -> LED 5 V data','A -> B; A2-A8 GND; B2-B8 NC'],h=370)
u2=block('lvc245','U2 / SN74LVC245AN / 3.3 V',350,left=[('1','1 DIR / tie Due 3.3 V'),('2','2 A1 / status 5 V IN')]+[(str(i),f'{i} A{i-1} / GND') for i in range(3,10)]+[('10','10 GND')],right=[('20','20 VCC / Due 3.3 V'),('19','19 /OE / GND'),('18','18 B1 / 3.3 V OUT')]+[(str(i),f'{i} B{19-i} / NC') for i in range(17,10,-1)],notes=['HDMI 5 V -> Due 3.3 V status','A -> B; A2-A8 GND; B2-B8 NC'],h=370)
res=Part('resistor','Resistor',150,75,[('1','1',0,53,'L'),('2','2',150,53,'R')],['Value in instance / guide'],color='#fff1df')
cap=Part('capacitor','Capacitor',150,75,[('p','+ / rail',0,53,'L'),('n','- / GND',150,53,'R')],['Value in instance / guide'],color='#e5f4f5')
electro=Part('electrolytic','Capacitor',150,85,[('p','+ / rail',0,53,'L'),('n','- / GND',150,53,'R')],color='#e5f4f5')
# Removed automatic HDMI toggle circuit.
ja_led=block('ja_led','Nexys Video / JA',290,right=[('4','JA4 / AB18 / LED data'),('5','JA5 / GND'),('11','JA11 / GND')],notes=['Only three conductors here','JA10 remains spare'],h=200,buses=[['5','11']])
power=block('led_power','Regulated LED supply',280,right=[('5','+5 V LED'),('gnd','GND')],notes=['5 V / >=1 A suggested','4 RGB pixels budget <=240 mA'],h=175)
pixel=block('sk6812','SK6812 RGB pixel',220,left=[('5','+5 V'),('din','DIN'),('gnd','GND')],right=[('dout','DOUT')],notes=['24-bit RGB / typically GRB','Check exact LED data sheet'],h=190)
dueif=block('due_interface','Arduino Due / interface',310,right=[('3v3','3.3 V for U2 only'),('gnd','GND'),('D8','D8 / status INPUT')],notes=['D8 has no internal pull-up','D9 unused / no switch output'],h=230)
hdmimod=block('hdmi_mods','HDMI switch / modification taps',355,left=[('status','STATUS_5V / measured logic'),('toggle','TOGGLE_N / active low'),('gnd','GND / switch logic return')],notes=['ASIN B0F6LM1578','Polarity and tap locations: verify'],h=210)
s.add('JA',ja_led,35,140);s.add('LED power',power,35,430);s.add('U1',u1,580,140)
s.add('R1 330 ohm',res,1030,235)
for i,x in enumerate([1250,1510,1770]):s.add(f'LED{i+1}',pixel,x,140)
s.add('LED4 optional',pixel,1770,440)
s.add('C1 100 nF',cap,350,475);s.add('C3 1000 uF 10 V',electro,350,580);s.add('R4 10 kohm',res,350,290)
# LED reference connections: y=240/264/288; U1 A1 y264, DIR240, VCC240, OE264, B1288.
s.wire(('JA','4'),('U1','2'),'LED_DATA_3V3','led',[(325,240),(325,264)])
s.wire(('JA','4'),('R4 10 kohm','1'),'LED_IDLE_PULLDOWN','led',[(325,240),(325,343)])
s.wire(('R4 10 kohm','2'),('U1','10'),'LED_PULLDOWN_GND','ground',[(530,343),(530,456)])
s.wire(('U1','18'),('R1 330 ohm','1'),'LED_DATA_5V','led',[(960,288)])
s.wire(('R1 330 ohm','2'),('LED1','din'),'LED_DIN','led',[(1210,288),(1210,264)])
s.wire(('LED1','dout'),('LED2','din'),'LED_CHAIN_1','led',[(1490,240),(1490,264)])
s.wire(('LED2','dout'),('LED3','din'),'LED_CHAIN_2','led',[(1750,240),(1750,264)])
s.wire(('LED3','dout'),('LED4 optional','din'),'LED_CHAIN_3','led',[(2010,240),(2010,410),(1730,410),(1730,564)])
s.wire(('LED power','5'),('U1','20'),'LED_5V','power5',[(520,530),(520,110),(1000,110),(1000,240)])
s.wire(('LED power','5'),('U1','1'),'HCT_DIR_HIGH','power5',[(520,530),(520,240)])
s.wire(('LED power','gnd'),('JA','5'),'COMMON_GND','ground',[(315,554),(315,264)])
s.wire(('JA','11'),('JA','5'),'JA_GROUNDS','ground',[(310,288),(310,264)])
# All LED grounds go to one bottom rail; all 5V go to one top rail.
for i in range(1,5):
 name=f'LED{i}' if i<4 else 'LED4 optional';px,py=s.point((name,'5'));gx,gy=s.point((name,'gnd'))
 s.wire(('LED power','5'),(name,'5'),f'LED{i}_5V','power5',[(520,530),(520,110),(px-15,110),(px-15,py)])
 s.wire(('LED power','gnd'),(name,'gnd'),f'LED{i}_GND','ground',[(315,554),(315,680),(gx-25,680),(gx-25,gy)])
for pin in ['3','4','5','6','7','8','9','10','19']:
 x,y=s.point(('U1',pin));mid=555 if x==580 else 940
 s.wire(('U1',pin),('LED power','gnd'),'U1_GND_'+pin,'ground',[(mid,y),(mid,680),(315,680),(315,554)])
for name in ['C1 100 nF','C3 1000 uF 10 V']:
 x,y=s.point((name,'p'));s.wire(('LED power','5'),(name,'p'),name+'_5V','power5',[(330,530),(330,y)])
 x,y=s.point((name,'n'));s.wire((name,'n'),('LED power','gnd'),name+'_GND','ground',[(515,y),(515,680),(315,680),(315,554)])
s.label(1030,330,'Place R1 near LED1 DIN',size=12)
s.add('LED notes',note('led_notes','LED wiring',['U1 pin 18 is 5 V output: connect only to the LED chain.','U1 pin 20 = +5 V LED; pin 1 = +5 V; pin 19 = GND.','C1 = 100 nF ceramic directly across U1 pins 20 and 10.','C3 = 1000 uF / >=10 V across strip input (+ to +5 V).','Add 100 nF at each bare pixel if its board lacks decoupling.','Fourth pixel optional: for three pixels leave LED3 DOUT open.','Final pixel DOUT is always unconnected. Power is parallel.'],w=650),50,1670)
# HDMI circuit area.
s.add('Due',dueif,35,890);s.add('U2',u2,590,890);s.add('HDMI switch',hdmimod,1550,1050)
silver_detail=block('silver_button','Silver arcade button',320,right=[('NO','NO / normally open'),('COM','COM / switch ground')],notes=['Manually selects HDMI source','Dry contact; no Due / Pi connection'],h=180)
s.add('Silver button',silver_detail,1550,1330)
s.add('C2 100 nF',cap,1080,1005);s.add('R5 100 kohm',res,1250,1110)
s.wire(('Due','3v3'),('U2','20'),'DUE_3V3','power3',[(490,990),(490,850),(1010,850),(1010,990)])
s.wire(('Due','3v3'),('U2','1'),'LVC_DIR_HIGH','power3')
s.wire(('Due','gnd'),('LED power','gnd'),'SYSTEM_COMMON_GND','ground',[(355,1014),(355,780),(15,780),(15,700),(315,700)])
s.wire(('Due','gnd'),('U2','10'),'U2_GND','ground',[(470,1014),(470,1240),(560,1240),(560,1206)])
for pin in ['3','4','5','6','7','8','9','19']:
 x,y=s.point(('U2',pin));mid=565 if x==590 else 965
 s.wire(('U2',pin),('Due','gnd'),'U2_GND_'+pin,'ground',[(mid,y),(mid,1270),(470,1270),(470,1014)])
s.wire(('HDMI switch','status'),('U2','2'),'HDMI_STATUS_5V','status',[(1490,1150),(1490,825),(540,825),(540,1014)])
s.wire(('U2','18'),('Due','D8'),'HDMI_STATUS_3V3','status',[(990,1038),(990,810),(455,810),(455,1038)])
s.wire(('HDMI switch','gnd'),('Due','gnd'),'HDMI_COMMON_GND','ground',[(1510,1198),(1510,1600),(470,1600),(470,1014)])
s.wire(('Due','3v3'),('C2 100 nF','p'),'C2_3V3','power3',[(490,990),(490,850),(1050,850),(1050,1058)])
s.wire(('C2 100 nF','n'),('Due','gnd'),'C2_GND','ground',[(1240,1058),(1240,1600),(470,1600),(470,1014)])
s.wire(('HDMI switch','status'),('R5 100 kohm','2'),'STATUS_PULLDOWN_5V','status',[(1490,1150),(1490,1163)])
s.wire(('R5 100 kohm','1'),('Due','gnd'),'STATUS_PULLDOWN_GND','ground',[(1230,1163),(1230,1600),(470,1600),(470,1014)])
s.wire(('Silver button','NO'),('HDMI switch','toggle'),'MANUAL_HDMI_TOGGLE','toggle',[(1960,1430),(1960,1300),(1525,1300),(1525,1174)])
s.wire(('Silver button','COM'),('HDMI switch','gnd'),'MANUAL_HDMI_RETURN','ground',[(1975,1454),(1975,1280),(1510,1280),(1510,1198)])
s.add('HDMI notes',note('hdmi_notes','Manual switching and input routing',['The silver button connects directly across the switch button contacts.','No Pi GPIO, Due D9, NPN transistor, R2 or R3 is used for switching.','STATUS_5V -> U2 -> Due D8; verify HIGH means Pi is selected.','D8 HIGH: USB keyboard active; both NES data outputs released.','D8 LOW: USB keys released; two NES controller ports active.','If status polarity is opposite, invert the firmware polarity setting.'],w=870),1050,1670)
metadata.append(s.save())
(OUT/'design-data.json').write_text(json.dumps(metadata,indent=2))
with (OUT/'connections.csv').open('w',newline='') as f:
 w=csv.writer(f,lineterminator="\n");w.writerow(['sheet','net','from_part','from_pin','to_part','to_pin'])
 for sh in metadata:
  for wire in sh['wires']:w.writerow([sh['sheet'],wire['net'],*wire['a'],*wire['b']])
print('Built',len(metadata),'sheets;',sum(len(sh['wires']) for sh in metadata),'logical wire runs.')
