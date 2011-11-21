import riddler_node as node

alice = node.node("alice", "localhost")
alice.set_mesh("localhost")

bob = node.node("bob", "10.10.11.51")
bob.set_mesh("10.10.10.51")

alice.add_dest(bob)
bob.add_dest(alice)
