import sys
import re

def fileToMap(fileName):
  fp = open(fileName)
  info = fp.read()
  regex = re.compile('<public type="\w+" name="(\w+)" id="(\w+)" />')
  res = regex.findall(info)
  fp.close()

  m = {}
  for node in res:
    m[node[0]] = node[1]

  return m


if len(sys.argv) != 3:
  print "%s <old-file> <new-file>" % sys.argv[0]
  sys.exit(1)

m1 = fileToMap(sys.argv[1])
m2 = fileToMap(sys.argv[2])

fp = open("out", "w")
for k in m1:
  if k in m2:
    fp.write("%s,%s,%s\n" % (k, m1[k], m2[k]))
  else:
    print "[-] %s has not in new file" % k

fp.close()
