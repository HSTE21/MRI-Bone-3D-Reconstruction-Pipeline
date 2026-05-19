import pyvista as pv
import numpy as np
import os

def create_bone_gif(stl_path, output_gif, label):
    print(f"Generating GIF for {label}...")
    
    if not os.path.exists(stl_path):
        print(f"Error: {stl_path} not found.")
        return

    # Load the mesh
    mesh = pv.read(stl_path)
    
    # Setup plotter
    plotter = pv.Plotter(off_screen=True, window_size=[600, 600])
    plotter.set_background("white")
    
    # Set camera position to fit the entire mesh
    plotter.add_mesh(
        mesh, 
        color="tan", 
        smooth_shading=True, 
        specular=0.5, 
        ambient=0.3
    )
    
    plotter.reset_camera()
    plotter.camera.zoom(0.9) # Slight zoom out to ensure padding around the bone
    
    # Create animation
    plotter.open_gif(output_gif)
    
    n_frames = 60
    for i in range(n_frames):
        # Rotate 360 degrees over n_frames
        plotter.camera.azimuth += 360 / n_frames
        plotter.render()
        plotter.write_frame()
        
    plotter.close()
    print(f"Successfully saved {output_gif}")

def main():
    # Paths to the STLs we generated
    radius_stl = "ProjectGroup1_Checkpoint2_Radius.stl"
    ulna_stl = "ProjectGroup1_Checkpoint2_Ulna.stl"
    
    # Generate GIFs
    create_bone_gif(radius_stl, "preview_radius.gif", "Radius")
    create_bone_gif(ulna_stl, "preview_ulna.gif", "Ulna")

if __name__ == "__main__":
    main()
