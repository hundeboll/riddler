import riddler_node as node

"""
alice = node.node("alice", "localhost")
bob = node.node("bob", "localhost", 9988)
"""

alice = node.node("alice", "panda5.personal.es.aau.dk")
bob = node.node("bob", "panda2.personal.es.aau.dk")


alice.add_dest(bob)
bob.add_dest(alice)
