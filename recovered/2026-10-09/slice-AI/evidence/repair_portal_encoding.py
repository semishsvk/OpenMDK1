import pathlib
p=pathlib.Path(r'F:\Remaster Framework\work\OpenMDK1-HMO1-Slice-BF11AI-20261006\project\main.gd')
b=p.read_bytes();s=b.decode('utf-8','surrogateescape')
for v in range(128,256):
 s=s.replace(chr(0xdc00+v),bytes([v]).decode('cp1252')) if chr(0xdc00+v) in s else s
p.write_text(s.replace('\r\n','\n').replace('\r',''),encoding='utf-8',newline='\n');print('UTF8_REPAIR',p)
