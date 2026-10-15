#!/usr/bin/env python3
"""Check generated archives and the electrical endpoint graph independently."""
from pathlib import Path
from xml.etree import ElementTree as E
from collections import defaultdict
import zipfile,json,re
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'design'
meta=json.loads((D/'design-data.json').read_text());report=[]
upstream=(D/'reference/upstream/controllers/due_interface.c').read_text()
control_order=['A','B','SELECT','START','UP','DOWN','LEFT','RIGHT']
upstream_pins={}
for player in [1,2]:
 match=re.search(r'C'+str(player)+r'_PINS\[8\]\s*=\s*\{([^}]+)\}',upstream)
 assert match
 upstream_pins[player]=dict(zip(control_order,[int(v.strip()) for v in match.group(1).split(',')]))
assert re.search(r'MODE_PIN\s*=\s*8',upstream)

class Graph:
 def __init__(self):self.parent={}
 def find(self,a):
  if a not in self.parent:self.parent[a]=a
  if self.parent[a]!=a:self.parent[a]=self.find(self.parent[a])
  return self.parent[a]
 def join(self,a,b):self.parent[self.find(a)]=self.find(b)
 def same(self,a,b):return self.find(a)==self.find(b)
def node(a,b):return(a,str(b))
for sh in meta:
 name=sh['sheet'];p=D/(name+'.fzz')
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None
  docs={n:E.fromstring(z.read(n)) for n in z.namelist()}
  root=docs[name+'.fz'];parts={r.get('moduleId'):r for n,r in docs.items() if n.endswith('.fzp')}
  items={r.get('modelIndex'):r for r in root.findall('./instances/instance')}
  assert len(items)==len(root.findall('./instances/instance')),'Duplicate model index'
  linkcount=0
  for idx,r in items.items():
   module=r.get('moduleIdRef')
   if module!='WireModuleID':
    assert module in parts,(name,module)
    part=parts[module]
    ids=[x.get('id') for x in part.findall('./connectors/connector')]
    assert len(ids)==len(set(ids))
    for view in ['breadboardView','schematicView']:
     image=part.find(f'./views/{view}/layers').get('image');archive='svg.'+image.replace('/','.')
     assert archive in docs,(name,archive)
     svg=docs[archive];svgids={x.get('id') for x in svg.iter() if x.get('id')}
     layer=part.find(f'./views/{view}/layers/layer').get('layerId');assert layer in svgids
     for c in part.findall('./connectors/connector'):
      pins=c.findall(f'./views/{view}/p');assert pins
      for pin in pins:
       assert pin.get('svgId') in svgids
       assert pin.get('terminalId') in svgids
   for view in ['breadboardView','schematicView']:
    for c in r.findall(f'./views/{view}/connectors/connector'):
     cid=c.get('connectorId')
     for link in c.findall('./connects/connect'):
      target=items[link.get('modelIndex')];tcid=link.get('connectorId')
      found=target.findall(f'./views/{view}/connectors/connector')
      reverse=[x for x in found if x.get('connectorId')==tcid]
      assert reverse,(name,idx,cid,link.attrib)
      assert any(l.get('modelIndex')==idx and l.get('connectorId')==cid for x in reverse for l in x.findall('./connects/connect')),(name,'not reciprocal',idx,cid,link.attrib)
      linkcount+=1
  g=Graph()
  for w in sh['wires']:
   a,b=tuple(w['a']),tuple(w['b']);assert a[0] in sh['items'] and a[1] in sh['items'][a[0]]['pins'];assert b[0] in sh['items'] and b[1] in sh['items'][b[0]]['pins'];g.join(a,b)
  for nameit,it in sh['items'].items():
   part=docs['part.'+it['part']+'.fzp']
   reverse={v['id']:k for k,v in it['pins'].items()}
   for bus in part.findall('./buses/bus'):
    members=[(nameit,reverse[n.get('connectorId')]) for n in bus.findall('nodeMember')]
    for n in members[1:]:g.join(members[0],n)
  if name.startswith('02'):
   for player in [1,2]:
    names=['A','B','SELECT','START','UP','DOWN','LEFT','RIGHT']
    pins=[]
    for i,n in enumerate(names):
     control=(f'P{player} joystick',n) if n in ['UP','DOWN','LEFT','RIGHT'] else (f'P{player} {n}','NO')
     dp=('Due','D'+str(upstream_pins[player][n]));assert g.same(control,dp)
     assert not g.same(dp,('Due','gnd'));pins.append(dp)
    for a in pins:
     for b in pins:
      assert (a==b)==g.same(a,b),'Control inputs shorted'
   for d,j in [(2,1),(3,2),(4,3),(5,7),(6,8),(7,9)]:assert g.same(node('Due','D'+str(d)),node('JA',j))
   assert g.same(node('Due','gnd'),node('JA',5)) and g.same(node('JA',5),node('JA',11))
   assert g.same(node('JA',6),node('R6 10 kohm',1)) and g.same(node('JA',6),node('R7 10 kohm',1))
   assert g.same(node('JA',3),node('R6 10 kohm',2)) and g.same(node('JA',9),node('R7 10 kohm',2))
   assert not g.same(node('JA',6),node('JA',3)) and not g.same(node('JA',6),node('JA',9))
   for player in [1,2]:
    assert g.same((f'P{player} joystick','COM'),('Due','gnd'))
    for n in ['START','SELECT','A','B']:assert g.same((f'P{player} {n}','COM'),('Due','gnd'))
  if name.startswith('03'):
   gp=node('LED power','gnd');v5=node('LED power',5);v3=node('Due','3v3')
   assert not g.same(gp,v5) and not g.same(gp,v3) and not g.same(v3,v5)
   for u,rail in [('U1',v5),('U2',v3)]:
    for pin in [20,1]:assert g.same(node(u,pin),rail),(u,pin,'supply/DIR')
    for pin in [10,19,3,4,5,6,7,8,9]:assert g.same(node(u,pin),gp),(u,pin,'GND')
    for pin in range(11,18):assert node(u,pin) not in g.parent,(u,pin,'unused output connected')
   assert g.same(node('JA',4),node('U1',2));assert g.same(node('JA',5),gp) and g.same(node('JA',11),gp)
   assert g.same(node('U1',18),node('R1 330 ohm',1));assert g.same(node('R1 330 ohm',2),node('LED1','din'))
   assert not g.same(node('LED1','din'),v5)
   for i in range(1,5):
    led=f'LED{i}' if i<4 else 'LED4 optional';assert g.same(node(led,5),v5);assert g.same(node(led,'gnd'),gp)
    if i<4:
     nextled=f'LED{i+1}' if i<3 else 'LED4 optional';assert g.same(node(led,'dout'),node(nextled,'din'))
   assert node('LED4 optional','dout') not in g.parent
   assert g.same(node('HDMI switch','status'),node('U2',2));assert g.same(node('U2',18),node('Due','D8'))
   assert not g.same(node('Due','D8'),node('HDMI switch','status'))
   assert 'Q1' not in sh['items'] and 'R2 1 kohm' not in sh['items'] and 'R3 100 kohm' not in sh['items']
   assert g.same(node('Silver button','NO'),node('HDMI switch','toggle'))
   assert g.same(node('Silver button','COM'),node('HDMI switch','gnd'))
   assert g.same(node('HDMI switch','gnd'),gp);assert g.same(node('Due','gnd'),gp)
   assert 'D9' not in sh['items']['Due']['pins']
  if name.startswith('04'):
   for player in [1,2]:
    for n,dpin in upstream_pins[player].items():
     endpoint=(f'P{player} joystick',n) if n in ['UP','DOWN','LEFT','RIGHT'] else (f'P{player} {n}','NO')
     assert g.same(endpoint,('Due','D'+str(dpin)))
     assert not g.same(endpoint,('Due','gnd'))
   for d,j in [(2,1),(3,2),(4,3),(5,7),(6,8),(7,9)]:assert g.same(node('Due','D'+str(d)),node('FPGA',j))
   assert node('Due','D9') not in g.parent
   assert g.same(node('Due','D8'),node('Interface','status_out'))
   assert g.same(node('HDMI switch','status'),node('Interface','status_in'))
   assert not g.same(node('Due','D8'),node('HDMI switch','status'))
   assert g.same(node('Silver button','NO'),node('HDMI switch','toggle'))
   assert g.same(node('Silver button','COM'),node('HDMI switch','gnd'))
   assert g.same(node('Due','gnd'),node('FPGA',5)) and g.same(node('Due','gnd'),node('Interface','swgnd'))
   assert not g.same(node('Due','3v3'),node('FPGA',6))
   assert not g.same(node('Due','3v3'),node('LED power',5))
   assert not g.same(node('FPGA',6),node('LED power',5))
   assert set(sh['items']['Pi']['pins'])=={'usb_due','usb_jtag','hdmi'}
  report.append(f'{name}: PASS; {len(parts)} embedded part types, {len(items)} instances, {linkcount} reciprocal view links checked')
(D/'validation.txt').write_text('\n'.join(report)+'\n\nElectrical and file checks passed. Native application export and hardware are not verified.\n')
print('\n'.join(report))
