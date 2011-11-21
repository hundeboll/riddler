import riddler_node as node

alice = node.node("alice", "localhost", 8899)
alice.set_mesh("localhost", 7788)

bob = node.node("bob", "localhost", 9988)
bob.set_mesh("localhost", 8877)

relay = node.node("relay", "localhost", 9999)

alice.add_dest(bob)
bob.add_dest(alice)
