import networkx
import matplotlib.pyplot

flows = [
    ("A", "X", 5),
    ("A", "Y", 7),
    ("B", "X", 3),
    ("B", "Y", 2),
    ("C", "X", 8),
    ("X", "M", 5),
    ("Y", "M", 7),
    ("X", "N", 3),
    ("Y", "N", 2),
    ("X", "O", 8),
    ("Y", "O", 9),
]


def main(flows):
    gag = networkx.DiGraph()
    gag.add_weighted_edges_from(flows)
    virtual_edges = []
    for node in gag.nodes():
        #print(node, gag.out_edges(node))
        i_w = 0
        o_w = 0
        for edge in gag.in_edges(node, data=True):
            s, e, w = edge
            i_w += w['weight']
        for edge in gag.out_edges(node, data=True):
            s, e, w = edge
            o_w += w['weight']
        print(node, i_w, o_w)
        if o_w > i_w and i_w > 0:
            virtual_edges.append(("<S>", node, o_w - i_w))
        networkx.set_node_attributes(gag, {node: {"amout": max(i_w, o_w)}})

    gag.add_weighted_edges_from(virtual_edges)

    for node in networkx.topological_generations(gag):
        print(node)
    networkx.draw(gag, with_labels=True)
    matplotlib.pyplot.show()



if __name__ == "__main__":
    main(flows)
