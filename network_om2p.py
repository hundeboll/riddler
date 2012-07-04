import riddler_node as node

n1 = node.node("n1", "o101.personal.es.aau.dk")
n3 = node.node("n3", "o103.personal.es.aau.dk")
n4 = node.node("n4", "o104.personal.es.aau.dk")
n5 = node.node("n5", "o105.personal.es.aau.dk")
n6 = node.node("n6", "o106.personal.es.aau.dk")
n7 = node.node("n7", "o107.personal.es.aau.dk")

n1.add_dest(n7)
n7.add_dest(n1)
