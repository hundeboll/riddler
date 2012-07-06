import riddler_node as node

n1  = node.node("n1",  "o101.personal.es.aau.dk")
n2  = node.node("n2",  "o102.personal.es.aau.dk")
n4  = node.node("n4",  "o104.personal.es.aau.dk")
n5  = node.node("n5",  "o105.personal.es.aau.dk")
n6  = node.node("n6",  "o106.personal.es.aau.dk")
n7  = node.node("n7",  "o107.personal.es.aau.dk")
n8  = node.node("n8",  "o108.personal.es.aau.dk")
#n9  = node.node("n9",  "o109.personal.es.aau.dk")
#n10 = node.node("n10", "o110.personal.es.aau.dk")

n1.add_dest(n8)
n8.add_dest(n1)
