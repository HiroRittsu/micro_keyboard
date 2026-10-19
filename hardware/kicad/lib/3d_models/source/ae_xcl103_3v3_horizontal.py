"""Generate the AE-XCL103-3V3 flat-mounted assembly (mm).

Requires CadQuery 2.8.0.  The JSON file alongside this script is the source
of dimensions and provenance. STEP coordinates: parent PCB top = Z0;
X right and Y up when viewing the module component side. KiCad footprint
coordinates use Y down, so pad Y is negated only when constructing this model.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cadquery as cq


def build(parameters: dict) -> tuple[cq.Assembly, dict]:
    board = parameters['board']
    header = parameters['header']
    board_bottom = header['body_height']
    board_top = board_bottom + board['thickness']
    component_z = board_top + parameters['assembly']['solder_gap']
    model = cq.Assembly(name='AE-XCL103-3V3_Horizontal')
    shapes = []
    named_shapes = {}
    colors = {
        'fr4': (0.43, 0.57, 0.37), 'mask': (0.025, 0.36, 0.19),
        'gold': (0.82, 0.65, 0.24), 'black': (0.055, 0.065, 0.065),
        'ferrite': (0.18, 0.20, 0.20), 'ceramic': (0.62, 0.43, 0.24),
        'silver': (0.72, 0.74, 0.74), 'white': (0.89, 0.89, 0.82),
    }

    def add(name, shape, color):
        if not shape.val().isValid():
            raise ValueError(f'Invalid solid: {name}')
        model.add(shape, name=name, color=cq.Color(*colors[color]))
        shapes.append(shape.val())
        named_shapes[name] = shape.val()

    def box(l, w, h, x, y, z):
        return cq.Workplane('XY').box(l, w, h, centered=(True, True, False)).translate((x, y, z))

    def ring(x, y, z, od, id_, h):
        return cq.Workplane('XY').circle(od / 2).circle(id_ / 2).extrude(h).translate((x, y, z))

    def drill_module(shape, z, thickness):
        for pad in parameters['pads']:
            hole = cq.Workplane('XY').circle((board['module_hole_diameter'] + 0.04) / 2).extrude(thickness + 0.02)
            shape = shape.cut(hole.translate((pad['x'], -pad['y'], z - 0.01)))
        return shape

    mask = 0.015
    add('module_fr4_10x7_5x1_6', drill_module(box(board['length'], board['width'], board['thickness'] - 2 * mask, 0, 0, board_bottom + mask), board_bottom, board['thickness']), 'fr4')
    for name, z in [('bottom', board_bottom), ('top', board_top - mask)]:
        add('soldermask_' + name, drill_module(box(board['length'], board['width'], mask, 0, 0, z), z, mask), 'mask')

    for pad in parameters['pads']:
        x, y = pad['x'], -pad['y']
        number = pad['number']
        for side, z in [('top', board_top), ('bottom', board_bottom - 0.025)]:
            add(f'pad_{number}_{side}', ring(x, y, z, 1.7, board['module_hole_diameter'], 0.025), 'gold')
        add(f'barrel_{number}', ring(x, y, board_bottom, 0.84, board['module_hole_diameter'], board['thickness']), 'gold')
        housing = box(header['body_width'], header['pitch'], header['body_height'], x, y, 0).edges('|Z').chamfer(0.20)
        housing = housing.cut(box(0.52, 0.52, header['body_height'] + 0.02, x, y, -0.01))
        add(f'header_housing_{number}', housing, 'black')
        pin_height = header['lower_pin_length'] + header['body_height'] + header['upper_pin_length']
        pin = box(header['pin_square'], header['pin_square'], pin_height, x, y, -header['lower_pin_length'])
        pin = pin.faces('>Z or <Z').edges().chamfer(0.07)
        add(f'header_pin_{number}_{pad["function"]}', pin, 'gold')
        add(f'pin_solder_{number}', ring(x, y, board_top + 0.025, 1.18, 0.60, 0.12), 'silver')

    def silk_rect(name, x, y, length, width):
        # Silk dimensions are photo-derived visual approximations.
        outer = box(length, width, 0.01, x, y, board_top + 0.001)
        inner = box(length - 0.12, width - 0.12, 0.03, x, y, board_top - 0.005)
        add(name, outer.cut(inner), 'white')

    for component in parameters['components']:
        ref = component['reference']
        x, y = component['x'], -component['y']
        length, width, height = component['length'], component['width'], component['height']
        if component['kind'] == 'mlcc':
            termination = 0.30
            add(ref + '_ceramic_1608', box(length - 2 * termination, width, height, x, y, component_z), 'ceramic')
            for side in [-1, 1]:
                add(f'{ref}_termination_{side}', box(termination, width, height, x + side * (length - termination) / 2, y, component_z), 'silver')
            silk_rect(ref + '_silk', x, y, length + 0.55, width + 0.30)
        elif component['kind'] == 'resistor':
            # RK73B1E long axis is along footprint Y (photo-derived position).
            termination = 0.20
            add(ref + '_ceramic_1005', box(width, length - 2 * termination, height, x, y, component_z), 'white')
            add(ref + '_resistive_top', box(width, length - 2 * termination, 0.025, x, y, component_z + height - 0.025), 'black')
            for side in [-1, 1]:
                add(f'{ref}_termination_{side}', box(width, termination, height, x, y + side * (length - termination) / 2, component_z), 'silver')
            silk_rect(ref + '_silk', x, y, width + 0.35, length + 0.4)
        elif component['kind'] == 'inductor_ic':
            # Published external envelope is 2.5 x 2.0 x 1.04 mm.
            # The split into the lower IC body and ferrite is cosmetic.
            base_height = 0.20
            add(ref + '_ic_base_CL_2025_02', box(length, width, base_height, x, y, component_z), 'black')
            coil = box(length - 0.20, width - 0.16, height - base_height, x, y, component_z + base_height)
            add(ref + '_integrated_inductor', coil.edges('|Z').fillet(0.09), 'ferrite')
            for end in [-1, 1]:
                for offset in [-0.65, 0, 0.65]:
                    add(f'{ref}_terminal_{end}_{offset}', box(0.30, 0.30, 0.10, x + offset, y + end * (width / 2 - 0.15), component_z), 'silver')
            silk_rect(ref + '_silk', x, y, length + 0.38, width + 0.35)

    compound = cq.Compound.makeCompound(shapes)
    bounds = compound.BoundingBox()
    component_envelopes = {}
    for component in parameters['components']:
        ref = component['reference']
        bodies = [shape for name, shape in named_shapes.items() if name.startswith(ref + '_') and name != ref + '_silk']
        b = cq.Compound.makeCompound(bodies).BoundingBox()
        actual = [b.xlen, b.ylen, b.zlen]
        expected = [component['length'], component['width'], component['height']]
        if component['kind'] == 'resistor':
            expected[0], expected[1] = expected[1], expected[0]
        assert all(abs(a - e) < 0.00001 for a, e in zip(actual, expected)), (ref, actual, expected)
        component_envelopes[ref] = {'part': component['part'], 'xyz_size_mm': [round(v, 6) for v in actual]}
    report = {
        'solid_count': len(shapes),
        'all_solids_valid': all(s.isValid() for s in shapes),
        'bbox_mm': {'xmin': bounds.xmin, 'xmax': bounds.xmax, 'ymin': bounds.ymin, 'ymax': bounds.ymax, 'zmin': bounds.zmin, 'zmax': bounds.zmax},
        'module_board_bottom_above_host_mm': board_bottom,
        'module_board_top_above_host_mm': board_top,
        'highest_component_above_host_mm': component_z + max(c['height'] for c in parameters['components']),
        'verified_component_envelopes': component_envelopes,
        'pin_mapping_top_view': parameters['pads'],
    }
    return model, report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--parameters', type=Path, default=Path(__file__).with_name('ae_xcl103_3v3_dimensions.json'))
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent.parent / 'AE-XCL103-3V3_Horizontal.step')
    args = parser.parse_args()
    parameters = json.loads(args.parameters.read_text(encoding='utf-8'))
    assembly, report = build(parameters)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    assembly.export(str(args.output), exportType='STEP', mode='default')
    report['step_file'] = args.output.name
    args.output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
