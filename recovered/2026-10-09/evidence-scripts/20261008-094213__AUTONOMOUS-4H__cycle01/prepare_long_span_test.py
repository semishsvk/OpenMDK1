"""Extend only the already checked A0 kernel model to new unrolled-block boundaries.
Retain the short-span evidence unchanged; strict source reads/writes remain required.
"""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
p=ROOT/'verify_short_perspective_pixels.py';s=p.read_text()
s=s.replace('<=32 delta span','33..637 delta spans')
s=s.replace('if not 0<=n<=32','if not 33<=n<=637')
s=s.replace("state={'done':False,'instructions':0}","state={'done':False,'instructions':0,'unrolled_blocks':0}")
s=s.replace("  state['instructions']+=1\n  if a==STOP", "  state['instructions']+=1\n  if a==0x471027:state['unrolled_blocks']+=1\n  if a==STOP")
s=s.replace('timeout=150000,count=2000','timeout=300000,count=20000')
s=s.replace(" if bytes(u.mem_read(TEX,len(texture)))!=texture:"," if state['unrolled_blocks']!=(n-1)//32:raise ValueError('UNROLLED_BOUNDARY_COUNT')\n if bytes(u.mem_read(TEX,len(texture)))!=texture:")
s=s.replace("'instructions':state['instructions'],'pass':True", "'instructions':state['instructions'],'unrolled_blocks':state['unrolled_blocks'],'pass':True")
s=s.replace('(0,1,2,3,7,15,30,31,32)','(33,34,63,64,65,95,96,127,128,255,256,257,511,637)')
s=s.replace('OpenMDK1.ShortPerspectivePixelMechanism.v1','OpenMDK1.LongPerspectivePixelMechanism.v1')
s=s.replace('span_delta 0..32','span_delta 33..637')
s=s.replace('Does not establish long-span 32-pixel block transitions, alternate kernels, perspective triangle coverage or live variant selection.',
 'Establishes A0 unrolled block and tail transitions only; does not establish alternate kernels, perspective triangle coverage or live variant selection.')
s=s.replace("'short-perspective-pixel-verification.json'","'long-perspective-pixel-verification.json'")
s=s.replace("'short-perspective-counterexample.json'","'long-perspective-counterexample.json'")
s=s.replace('Compare long spans at the unrolled-block boundary; retain profile-specific behavior instead of replacing with ideal perspective interpolation.',
 'Close alternate perspective kernel flags and driver ABI before production integration; A0 span coverage is now bounded through reciprocal-table index639.')
with (ROOT/'verify_long_perspective_pixels.py').open('x',encoding='utf-8') as f:f.write(s)
with (ROOT/'long-span-test-provenance.json').open('x',encoding='utf-8') as f:json.dump({'source_short_test_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
 'new_domain':'delta33..637, across32-pixel unrolled boundaries','instruction_budget':20000,
 'new_assertion':'unrolled block entry count equals floor((delta-1)/32)','unchanged_assertions':['exact pixel bytes','exact source-read order','exact write order','all memory guards','unchanged source texture'],
 'old_tests_rerun':False},f,indent=2)
