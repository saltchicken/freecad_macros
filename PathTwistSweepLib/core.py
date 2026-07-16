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

    if not hasattr(path_obj, "Shape") or len(path_obj.Shape.Edges) == 0:
        App.Console.PrintError("Error: The second selected object must have a valid curve/path.\n")
        return

    if num_sections < 2:
        App.Console.PrintError("Error: Need at least 2 sections.\n")
        return

    # 2. Setup the Path edge
    # We grab the first edge of the shape. For best results, users should use a single continuous B-Spline or Arc.
    path_edge = path_obj.Shape.Edges[0]
    if len(path_obj.Shape.Edges) > 1:
        App.Console.PrintWarning("Warning: Path has multiple edges. Only the first edge will be used. Consider using a single B-Spline for smooth paths.\n")

    # Get the parameter bounds for the curve to interpolate along its length
    u_min, u_max = path_edge.ParameterRange

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

    # 3. Loop through and duplicate Sketches along the curve
    for i in range(num_sections):
        # Calculate parametric interpolation
        t_ratio = float(i) / (num_sections - 1)
        t_param = u_min + (t_ratio * (u_max - u_min))
        angle = t_ratio * total_angle

        # Get the 3D Point and Tangent (Direction) at this exact spot on the curve
        point = path_edge.valueAt(t_param)
        tangent = path_edge.tangentAt(t_param)
        tangent.normalize()

        # Duplicate the sketch
        new_sketch = doc.copyObject(profile_obj)
        new_sketch.Label = f"{profile_obj.Label}_SweepLayer_{i+1}"
        
        # Calculate rotation: Align sketch Z-axis to the path's tangent
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
