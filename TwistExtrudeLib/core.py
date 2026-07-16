import FreeCAD as App
import FreeCADGui as Gui

def generate_twisted_sketches(total_height=120.0, total_angle=100.0, num_sections=6):
    doc = App.ActiveDocument
    if doc is None:
        App.Console.PrintError("Error: No active document found.\n")
        return

    # 1. Grab selection, or fallback to the active object
    selection = Gui.Selection.getSelection()
    if selection:
        base_obj = selection[0]
    elif doc.ActiveObject:
        base_obj = doc.ActiveObject
        App.Console.PrintWarning(f"Warning: Nothing selected. Guessing you meant to use '{base_obj.Name}'.\n")
    else:
        App.Console.PrintError("Error: Please select a Sketch in the Tree View first!\n")
        return

    # Ensure the user actually selected a Sketch
    if not hasattr(base_obj, "TypeId") or "Sketcher::SketchObject" not in base_obj.TypeId:
        App.Console.PrintError("Error: The selected object must be a Sketch.\n")
        return

    # 2. Safely calculate sections_data
    if num_sections < 2:
        App.Console.PrintError("Error: Need at least 2 sections.\n")
        return
        
    sections_data = []
    for i in range(num_sections):
        t = float(i) / (num_sections - 1)
        z = t * total_height
        angle = t * total_angle
        sections_data.append((z, angle, i))

    # --- Find the Active Body ---
    active_body = None
    if Gui.ActiveDocument:
        # Ask the GUI for the currently active PartDesign Body
        active_body = Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")

    # Fallback: If no body is globally active, check if the source sketch is inside a Body
    if not active_body:
        for parent in base_obj.InList:
            if parent.isDerivedFrom("PartDesign::Body"):
                active_body = parent
                break
                
    if not active_body:
        App.Console.PrintWarning("Warning: No Active Body found. Sketches will be placed in the document root.\n")

    # 3. Loop through and duplicate the Sketches
    for z, angle, i in sections_data:
        # Ask FreeCAD to natively duplicate the Sketch object
        new_sketch = doc.copyObject(base_obj)
        new_sketch.Label = f"{base_obj.Label}_Layer_{i+1}"
        
        # Calculate the mathematical transformation
        new_placement = App.Placement(App.Vector(0, 0, z), App.Rotation(App.Vector(0, 0, 1), angle))
        
        # PartDesign compatibility check: 
        if hasattr(new_sketch, "MapMode") and new_sketch.MapMode != 'Deactivated':
            new_sketch.AttachmentOffset = new_placement
        else:
            new_sketch.Placement = new_placement
            
        # Add the new sketch to the Active Body
        if active_body:
            active_body.addObject(new_sketch)

    doc.recompute()
    App.Console.PrintMessage(f"Successfully generated {num_sections} sketches from {base_obj.Label}!\n")
