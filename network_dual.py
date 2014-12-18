import riddler_node as node

core0 = node.node("core0", "ap-nb2.office.es.aau.dk", 8899)
src1 = node.node("core1", "core2.lab.es.aau.dk", 8899)
src2 = node.node("core4", "core5.lab.es.aau.dk", 8899)
dst1 = node.node("core4", "core2.lab.es.aau.dk", 9988)
dst2 = node.node("core1", "core5.lab.es.aau.dk", 9988)

src1.add_dest(dst1)
src2.add_dest(src2)
dst1.add_source(src1)
dst2.add_source(dst2)
