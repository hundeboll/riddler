import riddler_node as node

alice = node.node("alice",  "panda7.personal.es.aau.dk")
n4    = node.node("relay1", "cwn4.personal.es.aau.dk")
n5    = node.node("relay2", "cwn5.personal.es.aau.dk")
n6    = node.node("relay3", "cwn6.personal.es.aau.dk")
n7    = node.node("relay4", "cwn7.personal.es.aau.dk")
n8    = node.node("relay5", "cwn8.personal.es.aau.dk")
n9    = node.node("relay6", "cwn9.personal.es.aau.dk")
bob   = node.node("bob",    "panda6.personal.es.aau.dk")

alice.add_dest(bob)
bob.add_dest(alice)
