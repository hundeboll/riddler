import riddler_node as node

core0 = node.node("core0", "ap-nb2.office.es.aau.dk")
core1 = node.node("core1", "core2.lab.es.aau.dk")
core2 = node.node("core2", "core3.lab.es.aau.dk")
core3 = node.node("core3", "core4.lab.es.aau.dk")
core4 = node.node("core4", "core5.lab.es.aau.dk")

core1.add_dest(core4)
core2.add_dest(core3)
core3.add_source(core2)
core4.add_source(core1)
