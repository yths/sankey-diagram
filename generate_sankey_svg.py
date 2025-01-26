import os
import itertools

import networkx
import cairo

import poly_point_isect


default_colors = {
    "background": "#010101",
    "node": "#2c4c9a",
    "edge": "#464545",
    "node_text": "#fffefd",
}

def color_str_to_tuple(color):
    return tuple(int(color[i : i + 2], 16) / 255 for i in (1, 3, 5))


def visualize(flows, output_path, colors, virtual_node_label="<S>", font="sans", output_width=1980, output_height=1080):

    for key, value in colors.items():
        colors[key] = color_str_to_tuple(value)

    gag = networkx.DiGraph()
    gag.add_weighted_edges_from(flows)
    virtual_edges = []
    for node in gag.nodes():
        i_w = 0
        o_w = 0
        for edge in gag.in_edges(node, data=True):
            s, e, w = edge
            i_w += w["weight"]
        for edge in gag.out_edges(node, data=True):
            s, e, w = edge
            o_w += w["weight"]
        if o_w > i_w and i_w > 0:
            virtual_edges.append((virtual_node_label, node, o_w - i_w))
        networkx.set_node_attributes(gag, {node: {"amount": max(i_w, o_w)}})

    gag.add_weighted_edges_from(virtual_edges)

    # calculate amount for virtual node
    for edge in gag.out_edges(virtual_node_label, data=True):
        s, e, w = edge
        o_w += w["weight"]
    networkx.set_node_attributes(gag, {virtual_node_label: {"amount": o_w}})

    max_amount = 0
    for node in gag.nodes():
        max_amount = max(max_amount, gag.nodes[node]["amount"])

    segments = []
    layers = list(networkx.topological_generations(gag))

    layer_permutations = []
    for layer in layers:
        layer_permutations.append(list(itertools.permutations(layer)))

    layer_combintations = list(itertools.product(*layer_permutations))
    intersections = 21e06
    best_layers = []
    for layers in layer_combintations:
        segments = []
        for i in range(len(layers) - 1):
            
            for edge in gag.edges():
                s, e = edge
                if s in layers[i] and e in layers[i + 1]:
                    segment = ((i, layers[i].index(s)), (i + 1, layers[i + 1].index(e)))
                    segments.append(segment)
        intersections_per_layer = len(poly_point_isect.isect_segments(segments))
        if intersections_per_layer < intersections:
            intersections = intersections_per_layer
            best_layers = layers

    best_layers_flattened = [x for xs in best_layers for x in xs]


    with cairo.SVGSurface(output_path, output_width, output_height) as surface:
        context = cairo.Context(surface)
        context.scale(output_width, output_height)

        context.set_line_cap(cairo.LINE_CAP_BUTT)
        context.set_line_join(cairo.LINE_JOIN_ROUND)

        context.set_source_rgb(*colors["background"])
        context.rectangle(0, 0, 1, 1)
        context.fill()

        positions = {}
        rectangles = []


        horizontal_offset_step = 1 / len(list(best_layers))
        for x, generation in enumerate(best_layers):
            vertical_offset_step = 1 / len(generation)
            for y, node in enumerate(generation):
                rectangles.append((node, [(x * horizontal_offset_step) + (horizontal_offset_step / 2), (y * vertical_offset_step)
                    + (vertical_offset_step / 2)
                    - (gag.nodes[node]["amount"] / max_amount) / 10,
                    0.01,
                    (gag.nodes[node]["amount"] / max_amount) / 5]))
            
                positions[node] = (
                    (x * horizontal_offset_step) + (horizontal_offset_step / 2),
                    (y * vertical_offset_step) + (vertical_offset_step / 2),
                    0.01,
                    (gag.nodes[node]["amount"] / max_amount) / 5,
                )

        offset_s = {}
        offset_e = {}
        offset_s_x = {}
        offset_e_x = {}
        context.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        context.set_font_size(0.01)
        for edge in sorted(list(gag.edges(data=True)), key=lambda x: (best_layers_flattened.index(x[0]), best_layers_flattened.index(x[1]))):
            s, e, w = edge
            if s not in offset_s:
                offset_s[s] = -(positions[s][3] / 2)
            if e not in offset_e:
                offset_e[e] = -(positions[e][3] / 2)
            if s not in offset_s_x:
                offset_s_x[s] = 0.1
            if e not in offset_e_x:
                offset_e_x[e] = 0.1

            line_width = (w["weight"] / max_amount) / 10
            context.move_to(
                positions[s][0], positions[s][1] + offset_s[s] + (line_width / 2)
            )
            context.line_to(
                positions[s][0] + offset_s_x[s], positions[s][1] + offset_s[s] + (line_width / 2)
            )
            context.line_to(
                positions[e][0] - offset_e_x[e], positions[e][1] + offset_e[e] + (line_width / 2)
            )
            context.line_to(
                positions[e][0], positions[e][1] + offset_e[e] + (line_width / 2)
            )
            context.set_line_width(line_width)
            context.set_source_rgba(*colors["edge"], 0.5)
            context.stroke()

            x_bearing, y_bearing, width, height, x_advance, y_advance = context.text_extents(f"{w['weight']}")
            context.move_to(positions[s][0] + 0.015, positions[s][1] + offset_s[s] + (line_width / 2) + height / 2)

            context.set_source_rgba(*colors["edge"], 1)
            context.show_text(f"{w['weight']}")

            offset_s[s] += (line_width * 2)
            offset_e[e] += (line_width * 2)
            offset_s_x[s] -= 0.025
            offset_e_x[e] -= 0.025

        context.set_line_width(0)
        for rectangle in rectangles:
            context.rectangle(*rectangle[1])

            context.set_source_rgba(*colors["node"], 1)
            context.fill()
            x_bearing, y_bearing, width, height, x_advance, y_advance = context.text_extents(f"{rectangle[0]} = {gag.nodes[rectangle[0]]['amount']}")
            context.move_to(rectangle[1][0] - (width /4 + x_bearing), rectangle[1][1] + rectangle[1][3] + 2 * (height + y_bearing) + 0.015)

            context.set_source_rgba(*colors["node_text"], 1)
            context.show_text(f"{rectangle[0]} = {gag.nodes[rectangle[0]]['amount']}")

if __name__ == "__main__":
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

    output_path = os.path.join("assets", "example.svg")
    visualize(flows, output_path, default_colors, font="JetBrains Mono ExtraLight")
