import riddler_node as node

alice = node.node("alice", "localhost")
alice.set_mesh("localhost")

bob = node.node("bob", "localhost", 9988)
bob.set_mesh("localhost", 7788)

alice.add_dest(bob)
bob.add_dest(alice)
