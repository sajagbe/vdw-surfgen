import argparse
import numpy as np
import os,tempfile
from pathlib import Path
import matplotlib.pyplot as plt
from tqdm import tqdm
from colorama import init, Fore, Style, Back
from scipy.spatial import cKDTree
import time

# Initialize colorama for cross-platform colored terminal text
init(autoreset=True)

# Van der Waals radii (in Å) for elements Z = 1–103 (H through Lr).
#
# Primary Compilation Citation:
#   Mantina, M.; Valero, R.; Cramer, C. J.; Truhlar, D. G. "Atomic Radii of the
#   Elements." In CRC Handbook of Chemistry and Physics, 95th ed.; Haynes, W. M.,
#   Ed.; CRC Press: Boca Raton, FL, 2014; Section 9, pp 9-49–9-50.
#   ISBN: 978-1-4822-0867-2.
#
# Organization & Constituent Sources:
#   1. 28 Main-Group & Noble Gas Elements:
#      - Bondi, A. "van der Waals Volumes and Radii." J. Phys. Chem. 1964, 68 (3),
#        441–451 (DOI: 10.1021/j100785a001).
#      - Rowland, R. S.; Taylor, R. "Intermolecular Nonbonded Contact Distances in
#        Organic Crystal Structures: Comparison with Distances Expected from van der
#        Waals Radii." J. Phys. Chem. 1996, 100 (18), 7384–7391
#        (DOI: 10.1021/jp953141+) [refines H = 1.10 Å].
#   2. 16 Remaining Main-Group Elements (Be, B, Al, Ca, Ge, Rb, Sr, Sb, Cs, Ba,
#      Bi, Po, At, Rn, Fr, Ra):
#      - Mantina, M.; Chamberlin, A. C.; Valero, R.; Cramer, C. J.; Truhlar, D. G.
#        "Consistent van der Waals Radii for the Whole Main Group." J. Phys. Chem. A
#        2009, 113 (19), 5806–5812 (DOI: 10.1021/jp8111556).
#   3. 59 Transition Metals, Lanthanides, and Actinides (Sc–Zn, Y–Cd, La–Hg, Ac–Lr):
#      - Batsanov, S. S. "Van der Waals Radii of Elements." Inorg. Mater. 2001,
#        37 (9), 871–885 (DOI: 10.1023/A:1011625728803), harmonized onto the
#        Bondi scale in the CRC Handbook compilation.
VDW_RADII = {
    'H': 1.10, 'He': 1.40, 'Li': 1.82, 'Be': 1.53, 'B': 1.92, 'C': 1.70, 'N': 1.55, 'O': 1.52,
    'F': 1.47, 'Ne': 1.54, 'Na': 2.27, 'Mg': 1.73, 'Al': 1.84, 'Si': 2.10, 'P': 1.80, 'S': 1.80,
    'Cl': 1.75, 'Ar': 1.88, 'K': 2.75, 'Ca': 2.31, 'Sc': 2.15, 'Ti': 2.11, 'V': 2.07, 'Cr': 2.06,
    'Mn': 2.05, 'Fe': 2.04, 'Co': 2.00, 'Ni': 1.97, 'Cu': 1.96, 'Zn': 2.01, 'Ga': 1.87, 'Ge': 2.11,
    'As': 1.85, 'Se': 1.90, 'Br': 1.85, 'Kr': 2.02, 'Rb': 3.03, 'Sr': 2.49, 'Y': 2.32, 'Zr': 2.23,
    'Nb': 2.18, 'Mo': 2.17, 'Tc': 2.16, 'Ru': 2.13, 'Rh': 2.10, 'Pd': 2.10, 'Ag': 2.11, 'Cd': 2.18,
    'In': 1.93, 'Sn': 2.17, 'Sb': 2.06, 'Te': 2.06, 'I': 1.98, 'Xe': 2.16, 'Cs': 3.43, 'Ba': 2.68,
    'La': 2.43, 'Ce': 2.42, 'Pr': 2.40, 'Nd': 2.39, 'Pm': 2.38, 'Sm': 2.36, 'Eu': 2.35, 'Gd': 2.34,
    'Tb': 2.33, 'Dy': 2.31, 'Ho': 2.30, 'Er': 2.29, 'Tm': 2.27, 'Yb': 2.26, 'Lu': 2.24, 'Hf': 2.23,
    'Ta': 2.22, 'W': 2.18, 'Re': 2.16, 'Os': 2.16, 'Ir': 2.13, 'Pt': 2.13, 'Au': 2.14, 'Hg': 2.23,
    'Tl': 1.96, 'Pb': 2.02, 'Bi': 2.07, 'Po': 1.97, 'At': 2.02, 'Rn': 2.20, 'Fr': 3.48, 'Ra': 2.83,
    'Ac': 2.47, 'Th': 2.45, 'Pa': 2.43, 'U': 2.41, 'Np': 2.39, 'Pu': 2.43, 'Am': 2.44, 'Cm': 2.45,
    'Bk': 2.44, 'Cf': 2.45, 'Es': 2.45, 'Fm': 2.45, 'Md': 2.46, 'No': 2.46, 'Lr': 2.46,
}

def read_xyz_file(filepath):
    print(f"📂 {Fore.CYAN}Reading XYZ file: {filepath}{Style.RESET_ALL}")
    with open(filepath) as f:
        lines = f.readlines()
    natoms = int(lines[0])
    atom_types = []
    coords = []
    
    print(f"🔍 {Fore.YELLOW}Found {natoms} atoms{Style.RESET_ALL}")
    for line in tqdm(lines[2:2 + natoms], desc="📍 Loading atoms", unit="atoms"):
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
    print(f"⚛️  {Fore.MAGENTA}Generating VDW surface points...{Style.RESET_ALL}")
    surface_points = []
    n_atoms = len(elements)
    coords_np = np.array(coordinates)
    vdw_radii = np.array([VDW_RADII.get(e, 1.5) * scale_factor for e in elements])

    for i, (pos, elem) in enumerate(tqdm(zip(coordinates, elements), desc="🌐 Building surface", unit="atoms", total=n_atoms)):
        r = vdw_radii[i]
        area = 4 * np.pi * r ** 2
        n_points = max(10, int(area * density*1000))
        directions = fibonacci_sphere(n_points)
        points = pos + directions * r

        # Occlusion/collision detection and filtering
        keep_mask = np.ones(points.shape[0], dtype=bool)
        for j in range(n_atoms):
            if j == i:
                continue
            other_pos = coords_np[j]
            other_r = vdw_radii[j]
            dists = np.linalg.norm(points - other_pos, axis=1)
            keep_mask &= (dists > other_r)
        filtered_points = points[keep_mask]
        surface_points.append(filtered_points)
        time.sleep(0.01)  # Small delay for visual effect

    if surface_points:
        result = np.concatenate(surface_points, axis=0)
    else:
        result = np.empty((0, 3))

    # Optimize for uniform density
    print(f"⚡ {Fore.YELLOW}Optimizing point distribution...{Style.RESET_ALL}")
    result = optimize_surface_density(result, density)
    
    print(f"✨ {Fore.GREEN}Generated {len(result)} surface points!{Style.RESET_ALL}")
    return result

def calculate_molecular_surface_area(coordinates, elements, scale_factor=1.0, n_points=1000):
    """
    Calculate molecular VDW surface area using numpy-based spherical integration.
    Based on: https://gist.github.com/ljmartin/2daa60f58abccaf4696a2fdda1ef6737

    Args:
        coordinates: Atomic coordinates (N x 3 array)
        elements: Element symbols
        scale_factor: Scaling factor for VDW radii
        n_points: Number of points per atom sphere for integration

    Returns:
        Total surface area in Å²
    """
    coords_np = np.array(coordinates)
    vdw_radii = np.array([VDW_RADII.get(e, 1.5) * scale_factor for e in elements])
    n_atoms = len(elements)
    
    # Generate fibonacci sphere points for integration
    sphere_points = fibonacci_sphere(n_points)
    
    total_area = 0.0
    
    print(f"📐 {Fore.YELLOW}Calculating surface area with {n_points} points per atom...{Style.RESET_ALL}")
    
    for i in tqdm(range(n_atoms), desc="🔬 Integrating", unit="atoms"):
        r_i = vdw_radii[i]
        pos_i = coords_np[i]
        
        test_points = pos_i + sphere_points * r_i        
        accessible = np.ones(n_points, dtype=bool)
        
        for j in range(n_atoms):
            if i == j:
                continue
            
            r_j = vdw_radii[j]
            pos_j = coords_np[j]
            dists = np.linalg.norm(test_points - pos_j, axis=1)            
            accessible &= (dists > r_j)
        
        # Calculate exposed surface area for this atom
        # Area = (4πr²) × (fraction of accessible points)
        atom_area = 4 * np.pi * r_i**2 * np.sum(accessible) / n_points
        total_area += atom_area
    
    return total_area


def optimize_surface_density(surface_points, density):
    """Greedy sampling only - fast and preserves density."""

    if len(surface_points) == 0:
        return surface_points

    spacing = 1.0 / np.sqrt(density)
    tree = cKDTree(surface_points)
    indices = np.random.permutation(len(surface_points))
    kept = []
    remaining = set(range(len(surface_points)))

    current = indices[0]
    with tqdm(total=len(surface_points), desc="🔄 Optimizing density", unit="pts", dynamic_ncols=True, leave=False) as pbar:
        while remaining:
            kept.append(current)
            neighbors = tree.query_ball_point(surface_points[current], spacing)
            remaining -= set(neighbors)
            pbar.update(len(neighbors))
            if not remaining:
                break
            candidates = list(remaining)
            dists, _ = tree.query(surface_points[candidates], k=min(len(kept), 5))
            if len(kept) == 1:
                min_dists = dists
            else:
                min_dists = np.min(dists, axis=1) if dists.ndim > 1 else dists
            current = candidates[np.argmax(min_dists)]

    return surface_points[kept]



def save_txt(filename, coords):
    print(f"💾 {Fore.BLUE}Saving TXT file: {filename}{Style.RESET_ALL}")
    with open(filename, 'w') as f:
        for p in tqdm(coords, desc="💿 Writing TXT", unit="points"):
            f.write(f"{p[0]:.6f} {p[1]:.6f} {p[2]:.6f}\n")


def save_xyz(filename, coords, atom='H'):
    print(f"💾 {Fore.BLUE}Saving XYZ file: {filename}{Style.RESET_ALL}")
    with open(filename, 'w') as f:
        f.write(f"{len(coords)}\n")
        f.write("VDW surface points\n")
        for p in tqdm(coords, desc="🧬 Writing XYZ", unit="points"):
            f.write(f"{atom} {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}\n")


def save_surface_figure(coords, original_coords, output_path):
    print(f"🖼️  {Fore.CYAN}Creating 3D visualization: {output_path}{Style.RESET_ALL}")
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(projection='3d')
    
    # Add progress for plotting
    with tqdm(total=2, desc="📊 Plotting", unit="datasets") as pbar:
        ax.scatter(coords[:, 0], coords[:, 1], coords[:, 2], s=1, alpha=0.5, label='VDW surface')
        pbar.update(1)
        ax.scatter(original_coords[:, 0], original_coords[:, 1], original_coords[:, 2],
                   color='red', s=20, label='Atoms')
        pbar.update(1)
    
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="🌐 Generate VDW surface points from an XYZ file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{Fore.YELLOW}Examples:{Style.RESET_ALL}
  vsg molecule.xyz                    # Generate XYZ surface file only
  vsg molecule.xyz -t                 # Also save as TXT coordinates (short form)
  vsg molecule.xyz --txt              # Also save as TXT coordinates (long form)
  vsg molecule.xyz -i                 # Also save 3D visualization (short form)
  vsg molecule.xyz --img              # Also save 3D visualization (long form)
  vsg molecule.xyz -t -i              # Save all formats (short form)
  vsg molecule.xyz --txt --img        # Save all formats (long form)
  vsg molecule.xyz -s 1.2 -d 2.0      # Custom parameters (short form)
  vsg molecule.xyz --scale 1.2 --density 2.0  # Custom parameters (long form)

{Fore.GREEN}✨ XYZ files are always saved automatically!{Style.RESET_ALL}
""")
    
    parser.add_argument("xyz_file", help="📁 Path to input XYZ file")
    parser.add_argument("-s", "--scale", type=float, default=1.0, 
                       help="⚖️  Scale factor for VDW radii (default: 1.0)")
    parser.add_argument("-d", "--density", type=float, default=1.0, 
                       help="🔬 Point density per Å² (default: 1.0)")
    parser.add_argument("-t", "--txt", action="store_true", 
                       help="💾 Save surface points as TXT file")
    parser.add_argument("-i", "--img", action="store_true", 
                       help="🖼️  Save 3D surface plot image")

    args = parser.parse_args()
    xyz_file = args.xyz_file

    if not os.path.isfile(xyz_file):
        print(f"❌ {Fore.RED}File not found: {xyz_file}{Style.RESET_ALL}")
        return

    print(f"🚀 {Fore.GREEN}Starting VDW surface generation...{Style.RESET_ALL}")
    print(f"📊 Scale factor: {Fore.YELLOW}{args.scale}{Style.RESET_ALL}")
    print(f"🔬 Density: {Fore.YELLOW}{args.density} points/Å²{Style.RESET_ALL}")
    print()

    name = Path(xyz_file).stem
    elements, coords = read_xyz_file(xyz_file)
    
    # Calculate TRUE surface area (independent of density)
    print(f"📐 {Fore.YELLOW}Calculating molecular surface area...{Style.RESET_ALL}")
    true_area = calculate_molecular_surface_area(coords, elements, scale_factor=args.scale)
    print(f"📐 {Fore.CYAN}Molecular VDW surface area: {true_area:.2f} Å²{Style.RESET_ALL}")
    

    surface = generate_surface(coords, elements, scale_factor=args.scale, density=args.density)
    # surface = poisson_disk_sampling(surface, density=args.density)

    actual_density = len(surface) / true_area
    print(f"✓ {Fore.GREEN}Point density: {actual_density:.2f} points/Å² (target: {args.density}){Style.RESET_ALL}")

    print(f"\n💾 {Fore.BLUE}Saving output files...{Style.RESET_ALL}")
    
    # Always save XYZ file
    xyz_output = f"{name}_vdw_surface.xyz"
    save_xyz(xyz_output, surface)

    saved_files = [xyz_output]
    
    if args.txt:
        txt_output = f"{name}_vdw_surface.txt"
        save_txt(txt_output, surface)
        saved_files.append(txt_output)
        
    if args.img:
        img_output = f"{name}_vdw_surface.png"
        save_surface_figure(surface, coords, img_output)
        saved_files.append(img_output)

    # Success message
    print(f"""
{Fore.GREEN}🎉 SUCCESS! Generated {len(surface)} surface points.{Style.RESET_ALL}

{Fore.CYAN}📂 Saved outputs:{Style.RESET_ALL}""")
    
    for i, file in enumerate(saved_files, 1):
        file_emoji = "🧬" if file.endswith('.xyz') else "💿" if file.endswith('.txt') else "🖼️"
        print(f"   {file_emoji} {Fore.WHITE}{file}{Style.RESET_ALL}")
    
    print(f"\n{Back.GREEN}{Fore.BLACK} ✅ VDW surface generation completed! ✅ {Style.RESET_ALL}\n")


def cli_entry():
    main()
