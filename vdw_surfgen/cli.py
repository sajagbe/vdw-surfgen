import argparse
import numpy as np
import os
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
    """Calculate actual molecular VDW surface area analytically."""
    from scipy.spatial import cKDTree
    
    coords_np = np.array(coordinates)
    vdw_radii = np.array([VDW_RADII.get(e, 1.5) * scale_factor for e in elements])
    tree = cKDTree(coords_np)
    
    total_area = 0.0
    n_samples = 1000  # Sample points to estimate occlusion
    
    for i, r in enumerate(vdw_radii):
        # Full sphere area
        sphere_area = 4 * np.pi * r ** 2
        
        # Estimate exposed fraction via sampling
        directions = fibonacci_sphere(n_samples)
        test_points = coords_np[i] + directions * r
        
        # Check occlusion
        exposed = 0
        for pt in test_points:
            occluded = False
            for j in range(len(coordinates)):
                if i == j:
                    continue
                dist = np.linalg.norm(pt - coords_np[j])
                if dist < vdw_radii[j]:
                    occluded = True
                    break
            if not occluded:
                exposed += 1
        
        # Add exposed area
        fraction_exposed = exposed / n_samples
        total_area += sphere_area * fraction_exposed
    
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
  vsg molecule.xyz --txt              # Also save as TXT coordinates
  vsg molecule.xyz --img              # Also save 3D visualization
  vsg molecule.xyz --txt --img        # Save all formats
  vsg molecule.xyz --scale 1.2 --density 2.0  # Custom parameters

{Fore.GREEN}✨ XYZ files are always saved automatically!{Style.RESET_ALL}
""")
    
    parser.add_argument("xyz_file", help="📁 Path to input XYZ file")
    parser.add_argument("--scale", type=float, default=1.0, 
                       help="⚖️  Scale factor for VDW radii (default: 1.0)")
    parser.add_argument("--density", type=float, default=1.0, 
                       help="🔬 Point density per Å² (default: 1.0)")
    parser.add_argument("--txt", action="store_true", 
                       help="💾 Save surface points as TXT file")
    parser.add_argument("--img", action="store_true", 
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
    print(f"📐 {Fore.CYAN}Molecular VDW surface area: {true_area:.2f} Ų{Style.RESET_ALL}")
    


    surface = generate_surface(coords, elements, scale_factor=args.scale, density=args.density)
    # surface = poisson_disk_sampling(surface, density=args.density)

    actual_density = len(surface) / true_area
    print(f"✓ {Fore.GREEN}Point density: {actual_density:.2f} points/Ų (target: {args.density}){Style.RESET_ALL}")

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
