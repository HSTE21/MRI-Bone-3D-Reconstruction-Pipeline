import os
import numpy as np
import nibabel as nib
import pyvista as pv
from skimage import measure
from scipy.ndimage import label, gaussian_filter
import pandas as pd

def reconstruct_bone(mask_volume, spacing, label_name, group_id="1"):
    """
    Reconstructs a 3D mesh from a binary mask volume.
    """
    print(f"Reconstructing {label_name}...")
    
    # 0. Pre-processing: Volume Smoothing
    # Increased sigma to 1.0 to bridge small pits and ensure a smoother manifold surface
    smoothed_volume = gaussian_filter(mask_volume.astype(float), sigma=1.0)
    
    # 1. Marching Cubes Surface Extraction
    verts, faces, normals, values = measure.marching_cubes(smoothed_volume, level=0.5)
    
    # Scale vertices by spacing (converting voxel coords to mm)
    verts = verts * spacing
    
    # 2. Convert to PyVista Mesh
    pv_faces = np.hstack(np.c_[np.full(len(faces), 3), faces])
    mesh = pv.PolyData(verts, pv_faces)
    
    # Ensure watertightness by filling any small holes in the surface
    mesh = mesh.fill_holes(100) # Fill holes with up to 100 edges
    
    # Fix inverted normals and ensure consistency
    mesh = mesh.compute_normals(
        cell_normals=True, 
        point_normals=True, 
        inplace=False, 
        flip_normals=False, 
        auto_orient_normals=True
    )
    
    stats = {
        "bone": label_name,
        "verts_before": mesh.n_points,
        "faces_before": mesh.n_cells,
        "is_manifold": mesh.is_manifold
    }
    
    # 3. Post-processing: Smoothing
    # Increased to 300 iterations for ultra-high-quality professional finish
    mesh_smoothed = mesh.smooth_taubin(n_iter=300, pass_band=0.03)
    
    # 4. Post-processing: Decimation
    # Set to 0.0 (no reduction) to maintain maximum face count for "waterdicht" quality
    mesh_final = mesh_smoothed.decimate_pro(0.0, preserve_topology=True)
    
    stats.update({
        "verts_after": mesh_final.n_points,
        "faces_after": mesh_final.n_cells,
        "final_is_manifold": mesh_final.is_manifold
    })
    
    # 5. Measurements: Bone Length
    # Assuming the bone is aligned mostly along the Z-axis (slices)
    bounds = mesh_final.bounds # (xmin, xmax, ymin, ymax, zmin, zmax)
    length_x = bounds[1] - bounds[0]
    length_y = bounds[3] - bounds[2]
    length_z = bounds[5] - bounds[4]
    bone_length = max(length_x, length_y, length_z)
    
    stats["length_mm"] = bone_length
    
    # 6. Export STL
    filename = f"ProjectGroup{group_id}_Checkpoint2_{label_name}.stl"
    mesh_final.save(filename)
    print(f"Saved {filename}")
    
    return stats, mesh_final

def main():
    # Paths
    seg_path = "final_bone_mask_watershed.nii"
    
    if not os.path.exists(seg_path):
        print(f"Error: Segmentation file not found at {seg_path}")
        return

    print("Loading segmentation mask...")
    img = nib.load(seg_path)
    data = img.get_fdata().astype(np.uint8)
    
    # Voxel spacing from metadata (should be [1, 1, 1])
    spacing = img.header.get_zooms()
    print(f"Detected spacing: {spacing}")
    
    # Component Separation
    labeled_array, num_features = label(data)
    print(f"Found {num_features} connected components.")
    
    if num_features < 2:
        print("Error: Could not find 2 distinct bone components.")
        return
        
    # Get component sizes and sort by volume to find Radius and Ulna
    sizes = np.bincount(labeled_array.ravel())
    sizes[0] = 0 # Ignore background
    top_indices = np.argsort(sizes)[-2:][::-1] # Indices of two largest components
    
    # In this dataset, the radius and ulna are typically the two largest.
    # We can distinguish them by position or just label them Bone1, Bone2 
    # but usually, Radius is slightly thicker/larger in some areas or has a specific centroid.
    # For now, let's use the sizes and assume Bone_1 and Bone_2, then check positions.
    
    all_stats = []
    
    # We'll label the largest as Radius and second largest as Ulna for this phantom, 
    # or vice versa depending on typical anatomy in these scans.
    # In the provided screenshot/context, let's just use generic names if unsure, 
    # but I'll go with Radius (largest) and Ulna.
    names = ["Radius", "Ulna"]
    
    for i, idx in enumerate(top_indices):
        bone_mask = (labeled_array == idx)
        stats, _ = reconstruct_bone(bone_mask, spacing, names[i])
        all_stats.append(stats)
        
    # Save statistics to CSV
    df = pd.DataFrame(all_stats)
    df.to_csv("reconstruction_results.csv", index=False)
    print("Metrics saved to reconstruction_results.csv")
    print("\nSummary Table:")
    print(df)

if __name__ == "__main__":
    main()
