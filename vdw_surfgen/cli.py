import argparse
import numpy as np
import os
from pathlib import Path
import matplotlib.pyplot as plt

VDW_RADII = {  # shortened for brevity
    'H': 1.20, 'C': 1.70, 'N': 1.55, 'O': 1.52, 'F': 1.47, 'P': 1.80, 'S': 1.80, 'Cl': 1.75,
    'Br': 1.85, 'I': 1.98, 'He': 1.40, 'Ne': 1.54, 'Ar': 1.88, 'Kr': 2.02, 'Xe': 2.16,
    'Li': 1.82, 'Na': 2.27, 'K': 2.75, 'Rb': 3.03, 'Cs': 3.43, 'Fr': 3.48, 'Be': 2.00,
    'Mg': 1.73, 'Ca': 2.31, 'Sr': 2.49, 'Ba': 2.68, 'Ra': 2.83, 'B': 1.92, 'Al': 1.84,
    'Si': 2.10, 'Ti': 2.15, 'Fe': 2.00, 'Zn': 2.10, 'Cu': 1.95, 'Mn': 2.05, 'Hg': 2.05,
    'Pb': 2.02, 'U': 1.86
}

def read_xyz_file(filepath):
    with open(filepath) as f:
        lines = f.readlines()
    natoms = int(lines[0])
    atom_types = []
    coords = []
    for line in lines[2:2 + natoms]:
        parts = line.split()
        atom_types.append(parts[0])
        coords.append([float(x) for x in parts[1:4]])
    return atom_types, np.array(coords)


def fibonacci_sphere(samples):
    indices = np.arange(0, samples, dtype=float) + 0.5
    phi = np.arccos(1 - 2 * indices / samples)
    theta = np.pi * (1 + 5 ** 0.5) * indices
    x = np.cos(theta) * np.sin(phi)
    y = np.sin(theta) * np.sin(phi)
    z = np.cos(phi)
    return np.stack((x, y, z), axis=1)


def generate_surface(coordinates, elements, scale_factor=1.0, density=1.0):
    surface_points = []
    for pos, elem in zip(coordinates, elements):
        r = VDW_RADII.get(elem, 1.5) * scale_factor
        area = 4 * np.pi * r ** 2
        n_points = max(10, int(area * density))
        directions = fibonacci_sphere(n_points)
        points = pos + directions * r
        surface_points.append(points)
    return np.concatenate(surface_points, axis=0)


def save_txt(filename, coords):
    with open(filename, 'w') as f:
        for p in coords:
            f.write(f"{p[0]:.6f} {p[1]:.6f} {p[2]:.6f}\n")


def save_xyz(filename, coords, atom='X'):
    with open(filename, 'w') as f:
        f.write(f"{len(coords)}\n")
        f.write("VDW surface points\n")
        for p in coords:
            f.write(f"{atom} {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}\n")


def save_surface_figure(coords, original_coords, output_path):
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(projection='3d')
    ax.scatter(coords[:, 0], coords[:, 1], coords[:, 2], s=1, alpha=0.5, label='VDW surface')
    ax.scatter(original_coords[:, 0], original_coords[:, 1], original_coords[:, 2],
               color='red', s=20, label='Atoms')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Generate VDW surface points from an XYZ file.")
    parser.add_argument("xyz_file", help="Path to input XYZ file")
    parser.add_argument("--scale", type=float, default=1.0, help="Scale factor for VDW radii (default: 1.0)")
    parser.add_argument("--density", type=float, default=1.0, help="Point density per Å² (default: 1.0)")
    parser.add_argument("--save_txt", action="store_true", help="Save surface points as TXT file")
    parser.add_argument("--save_xyz", action="store_true", help="Save surface points as XYZ file")
    parser.add_argument("--save_img", action="store_true", help="Save 3D surface plot image")

    args = parser.parse_args()
    xyz_file = args.xyz_file

    if not os.path.isfile(xyz_file):
        print(f"File not found: {xyz_file}")
        return

    name = Path(xyz_file).stem
    elements, coords = read_xyz_file(xyz_file)
    surface = generate_surface(coords, elements, scale_factor=args.scale, density=args.density)

    if args.save_txt:
        save_txt(f"{name}_vdw_surface.txt", surface)
    if args.save_xyz:
        save_xyz(f"{name}_vdw_surface.xyz", surface)
    if args.save_img:
        save_surface_figure(surface, coords, f"{name}_vdw_surface.png")

    print(f"Generated {len(surface)} surface points.")
    if args.save_txt or args.save_xyz or args.save_img:
        print("Saved outputs:")
        if args.save_txt:
            print(f" - {name}_vdw_surface.txt")
        if args.save_xyz:
            print(f" - {name}_vdw_surface.xyz")
        if args.save_img:
            print(f" - {name}_vdw_surface.png")


def cli_entry():
    main()
