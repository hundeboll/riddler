import riddler_node as node

source = node.node("source", "o102.personal.es.aau.dk")
helper = node.node("helper", "o101.personal.es.aau.dk")
dest = node.node("dest", "o105.personal.es.aau.dk")

source.add_dest(dest)
dest.add_source(source)
