import FreeCAD as App
import FreeCADGui as Gui
import Part
import Draft
import math

def generate_equation_taper(total_height=120.0, num_sections=12, equation_str="1.0 + sin(t * pi) * 0.5"):
    doc = App.ActiveDocument
    if doc is None:
        App.Console.PrintError("Error: No active document found.\n")
        return

    # 1. Grab selection
    selection = Gui.Selection.getSelection()
    if selection:
        base_obj = selection[0]
    elif doc.ActiveObject:
        base_obj = doc.ActiveObject
        App.Console.PrintWarning(f"Warning: Nothing selected. Guessing you meant '{base_obj.Name}'.\n")
    else:
        App.Console.PrintError("Error: Please select a Sketch in the Tree View first!\n")
        return

    if not hasattr(base_obj, "TypeId") or "Sketcher::SketchObject" not in base_obj.TypeId:
        App.Console.PrintError("Error: The selected object must be a Sketch.\n")
        return

    if num_sections < 2:
        App.Console.PrintError("Error: Need at least 2 sections.\n")
        return

    # 2. Setup the safe Math evaluation environment
    safe_env = {
        "math": math, "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "pi": math.pi, "e": math.e, "pow": pow, "abs": abs,
        "sqrt": math.sqrt, "log": math.log
    }

    # Find the Active Body
    active_body = None
    if Gui.ActiveDocument:
        active_body = Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")
    if not active_body:
        for parent in base_obj.InList:
            if parent.isDerivedFrom("PartDesign::Body"):
                active_body = parent
                break

    created_sketches = []

    # 3. Loop and generate mathematically scaled sketches
    for i in range(num_sections):
        # Calculate normalized time (t) and exact height (z)
        t = float(i) / (num_sections - 1)
        z = t * total_height

        # Evaluate the user's string equation
        local_env = safe_env.copy()
        local_env["t"] = t
        local_env["z"] = z
        
        try:
            # Evaluate safely without builtins
            scale_factor = eval(equation_str, {"__builtins__": {}}, local_env)
        except Exception as e:
            App.Console.PrintError(f"Math Evaluation Error at section {i+1}: {e}\n")
            return
            
        # Prevent zero or negative scaling which breaks geometry
        scale_factor = max(0.001, float(scale_factor))

        # Create a Transformation Matrix for scaling
        mat = App.Matrix()
        mat.scale(scale_factor, scale_factor, 1.0)
        
        # Apply matrix to the base shape (modifies the internal edges)
        scaled_shape = base_obj.Shape.copy()
        scaled_shape.transformShape(mat)

        # Let the Draft engine handle the conversion from raw 3D edges to finite Sketch geometry
        new_sketch = Draft.make_sketch(scaled_shape.Edges, autoconstraints=False)
        new_sketch.Label = f"{base_obj.Label}_EqLayer_{i+1}"

        # Position the sketch at the correct Z-height
        new_placement = App.Placement(App.Vector(0, 0, z), App.Rotation())
        if hasattr(new_sketch, "MapMode") and new_sketch.MapMode != 'Deactivated':
            new_sketch.AttachmentOffset = new_placement
        else:
            new_sketch.Placement = new_placement

        if active_body:
            active_body.addObject(new_sketch)
            
        created_sketches.append(new_sketch)

    # 4. Generate the Additive Loft
    if active_body and len(created_sketches) > 1:
        try:
            loft_label = f"EqLoft_{base_obj.Label}"
            loft = active_body.newObject("PartDesign::AdditiveLoft", loft_label)
            loft.Profile = created_sketches[0]
            loft.Sections = created_sketches[1:]
            
            # Hide intermediate sketches
            if Gui.ActiveDocument:
                for sk in created_sketches:
                    Gui.ActiveDocument.getObject(sk.Name).Visibility = False
                Gui.ActiveDocument.getObject(base_obj.Name).Visibility = False
                    
        except Exception as e:
            App.Console.PrintError(f"Error generating Additive Loft: {e}\n")

    doc.recompute()
    App.Console.PrintMessage("Successfully generated Equation Taper!\n")
