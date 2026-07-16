import FreeCAD as App
import FreeCADGui as Gui

def generate_path_twist_sketches(total_angle=360.0, num_sections=24):
    doc = App.ActiveDocument
    if doc is None:
        App.Console.PrintError("Error: No active document found.\n")
        return

    # 1. Grab selection (requires Profile Sketch AND Path Object)
    selection = Gui.Selection.getSelection()
    if len(selection) < 2:
        App.Console.PrintError("Error: Please select the Profile Sketch, then Ctrl+click the Path Sketch.\n")
        return

    profile_obj = selection[0]
    path_obj = selection[1]

    # Type validation
    if not hasattr(profile_obj, "TypeId") or "Sketcher::SketchObject" not in profile_obj.TypeId:
        App.Console.PrintError("Error: The first selected object must be a Sketch (Profile).\n")
        return

    if not hasattr(path_obj, "Shape") or len(path_obj.Shape.Wires) == 0:
        App.Console.PrintError("Error: The path object must contain a connected continuous curve.\n")
        return

    if num_sections < 2:
        App.Console.PrintError("Error: Need at least 2 sections.\n")
        return

    # 2. Extract the continuous Wire and map our points
    # Wires[0] contains the correctly ordered sequence of all lines/arcs in the path
    path_wire = path_obj.Shape.Wires[0]
    
    # Discretize evaluates the entire wire length and returns evenly spaced points
    points = path_wire.discretize(Number=num_sections)
    
    # Calculate tangents (direction vectors) based on the adjacent points
    tangents = []
    for i in range(num_sections):
        if i == 0:
            t_vec = points[1] - points[0]
        elif i == num_sections - 1:
            t_vec = points[-1] - points[-2]
        else:
            # Central difference for a smoother normal transition across corners
            t_vec = points[i+1] - points[i-1]
            
        t_vec.normalize()
        tangents.append(t_vec)

    # --- Find the Active Body ---
    active_body = None
    if Gui.ActiveDocument:
        active_body = Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")

    if not active_body:
        for parent in profile_obj.InList:
            if parent.isDerivedFrom("PartDesign::Body"):
                active_body = parent
                break
                
    if not active_body:
        App.Console.PrintWarning("Warning: No Active Body found. Sketches will be placed in the document root.\n")

    created_sketches = []

    # 3. Loop through and duplicate Sketches along the entire discretized curve
    for i in range(num_sections):
        point = points[i]
        tangent = tangents[i]
        
        # Calculate proportional angle
        t_ratio = float(i) / (num_sections - 1)
        angle = t_ratio * total_angle

        # Duplicate the sketch
        new_sketch = doc.copyObject(profile_obj)
        new_sketch.Label = f"{profile_obj.Label}_SweepLayer_{i+1}"
        
        # Calculate rotation: Align sketch Z-axis to the path's local tangent
        z_vec = App.Vector(0, 0, 1)
        
        # Handle mathematical edge cases where the path is completely vertical
        if z_vec.dot(tangent) < -0.9999:
            align_rot = App.Rotation(App.Vector(1, 0, 0), 180)
        elif z_vec.dot(tangent) > 0.9999:
            align_rot = App.Rotation(0, 0, 0)
        else:
            align_rot = App.Rotation(z_vec, tangent)
        
        # Apply our twist angle around the new Z-axis
        twist_rot = App.Rotation(App.Vector(0, 0, 1), angle)
        
        # Combine the alignments (Twist first, then align to path)
        final_rot = align_rot.multiply(twist_rot)
        new_placement = App.Placement(point, final_rot)
        
        # PartDesign compatibility check
        if hasattr(new_sketch, "MapMode") and new_sketch.MapMode != 'Deactivated':
            new_sketch.AttachmentOffset = new_placement
        else:
            new_sketch.Placement = new_placement
            
        # Add to body and tracking list
        if active_body:
            active_body.addObject(new_sketch)
            
        created_sketches.append(new_sketch)

    # 4. Generate the Additive Loft
    if active_body and len(created_sketches) > 1:
        try:
            loft_label = f"PathLoft_{profile_obj.Label}"
            loft = active_body.newObject("PartDesign::AdditiveLoft", loft_label)
            loft.Profile = created_sketches[0]
            loft.Sections = created_sketches[1:]
            
            # Clean up the viewport: hide duplicated sketches and original profile
            if Gui.ActiveDocument:
                for sk in created_sketches:
                    Gui.ActiveDocument.getObject(sk.Name).Visibility = False
                Gui.ActiveDocument.getObject(profile_obj.Name).Visibility = False
                    
        except Exception as e:
            App.Console.PrintError(f"Error generating Additive Loft: {e}\n")
            
    elif not active_body:
        App.Console.PrintWarning("Skipped Additive Loft: Cannot create a loft because the sketches are not inside a PartDesign Body.\n")

    doc.recompute()
    App.Console.PrintMessage(f"Successfully generated 3D twisted path sweep from {num_sections} sections!\n")
