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

VDW_RADII = {  # shortened for brevity
    'H': 1.20, 'C': 1.70, 'N': 1.55, 'O': 1.52, 'F': 1.47, 'P': 1.80, 'S': 1.80, 'Cl': 1.75,
    'Br': 1.85, 'I': 1.98, 'He': 1.40, 'Ne': 1.54, 'Ar': 1.88, 'Kr': 2.02, 'Xe': 2.16,
    'Li': 1.82, 'Na': 2.27, 'K': 2.75, 'Rb': 3.03, 'Cs': 3.43, 'Fr': 3.48, 'Be': 2.00,
    'Mg': 1.73, 'Ca': 2.31, 'Sr': 2.49, 'Ba': 2.68, 'Ra': 2.83, 'B': 1.92, 'Al': 1.84,
    'Si': 2.10, 'Ti': 2.15, 'Fe': 2.00, 'Zn': 2.10, 'Cu': 1.95, 'Mn': 2.05, 'Hg': 2.05,
    'Pb': 2.02, 'U': 1.86
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

def calculate_molecular_surface_area(coordinates, elements, scale_factor=1.0):
    """
    Calculate molecular VDW surface area using FreeSASA library with Lee-Richards algorithm.

    Args:
        coordinates: Atomic coordinates
        elements: Element symbols
        scale_factor: Scaling factor for VDW radii

    Returns:
        Total surface area in Å²

    Raises:
        ImportError: If FreeSASA is not installed
    """
    try:
        import freesasa
    except ImportError:
        raise ImportError(
            "FreeSASA library not found. Install it with:\n"
            "  pip install freesasa\n"
        )

    freesasa.setVerbosity(freesasa.silent)

    # Build PDB-like string for FreeSASA
    pdb_lines = []
    for i, (coord, elem) in enumerate(zip(coordinates, elements)):
        radius = VDW_RADII.get(elem, 1.5) * scale_factor
        # PDB ATOM format with radius in the B-factor column
        line = f"ATOM  {i+1:5d}  {elem:<2s}  MOL A   1    {coord[0]:8.3f}{coord[1]:8.3f}{coord[2]:8.3f}  1.00{radius:6.2f}           {elem:>2s}"
        pdb_lines.append(line)

    pdb_string = "\n".join(pdb_lines) + "\nEND\n"

    # Write to temporary PDB file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pdb', delete=False) as tmp:
        tmp.write(pdb_string)
        tmp_path = tmp.name

    try:
        structure = freesasa.Structure(tmp_path)

        # Calculate surface area using Lee-Richards algorithm with 1000 slices
        # Use probe_radius=0 to get VDW surface (not solvent accessible surface)
        result = freesasa.calc(structure,
                              freesasa.Parameters({'algorithm': freesasa.LeeRichards,
                                                  'n-slices': 1000,
                                                  'probe-radius': 0.0}))

        return result.totalArea()
    finally:
        os.unlink(tmp_path)


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
