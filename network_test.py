import riddler_node as node

alice = node.node("alice", "localhost")
alice.set_mesh("localhost")

bob = node.node("bob", "localhost", 9988)
bob.set_mesh("localhost", 7788)

"""
alice = node.node("alice", "panda0.personal.es.aau.dk")
alice.set_mesh("10.10.12.50")

bob = node.node("bob", "10.10.11.51")
bob.set_mesh("10.10.12.51")
"""

alice.add_dest(bob)
bob.add_dest(alice)
