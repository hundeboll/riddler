import riddler_node as node

source = node.node("source", "rasp00.lab.es.aau.dk")
#helper = node.node("helper", "o101.personal.es.aau.dk")
dest = node.node("dest", "rasp02.lab.es.aau.dk")

source.add_dest(dest)
dest.add_source(source)
