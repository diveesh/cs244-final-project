
with open('data.out', 'r') as f:
    lines = f.readlines()

print "timestamp,src_ip,dst_ip,cwnd"
for l in lines:
    items = l.split()
    srcip, dstip = items[1], items[2]
    if "5201" in dstip:
        print ",".join([items[0], items[1], items[2], items[6]])

