import riddler_node as node

"""
alice = node.node("alice", "localhost")
bob = node.node("bob", "localhost", 9988)
"""

"""
alice = node.node("alice", "panda5.personal.es.aau.dk")
bob = node.node("bob", "panda4.personal.es.aau.dk")
"""

alice = node.node("alice", "n52")
bob = node.node("bob", "n53")


alice.add_dest(bob)
bob.add_dest(alice)
