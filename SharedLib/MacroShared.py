import FreeCAD as App
import FreeCADGui as Gui


def get_single_sketch(doc):
    """Safely retrieves and validates a single sketch selection."""
    selection = Gui.Selection.getSelection()
    if selection:
        base_obj = selection[0]
    elif doc.ActiveObject:
        base_obj = doc.ActiveObject
        App.Console.PrintWarning(
            f"Warning: Nothing selected. Guessing '{base_obj.Name}'.\n")
    else:
        App.Console.PrintError(
            "Error: Please select a Sketch in the Tree View first!\n")
        return None

    if not hasattr(base_obj,
                   "TypeId") or "Sketcher::SketchObject" not in base_obj.TypeId:
        App.Console.PrintError("Error: The selected object must be a Sketch.\n")
        return None

    return base_obj


def get_active_body(base_obj=None):
    """Finds the active PartDesign Body, falling back to the base object's parent."""
    active_body = None
    if Gui.ActiveDocument:
        active_body = Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")

    if not active_body and base_obj:
        for parent in base_obj.InList:
            if parent.isDerivedFrom("PartDesign::Body"):
                active_body = parent
                break

    if not active_body:
        App.Console.PrintWarning(
            "Warning: No Active Body found. Placing objects in root.\n")

    return active_body


def build_additive_loft(active_body, loft_label, profile, sections, hide_list):
    """Generates an Additive Loft inside the active body and hides intermediate sketches."""
    if not active_body or not sections:
        App.Console.PrintWarning(
            "Skipped Additive Loft: No Active Body or insufficient sections.\n")
        return None

    try:
        loft = active_body.newObject("PartDesign::AdditiveLoft", loft_label)
        loft.Profile = profile
        loft.Sections = sections

        # Clean up the viewport
        if Gui.ActiveDocument:
            for obj in hide_list:
                doc_obj = Gui.ActiveDocument.getObject(obj.Name)
                if doc_obj:
                    doc_obj.Visibility = False
        return loft

    except Exception as e:
        App.Console.PrintError(f"Error generating Additive Loft: {e}\n")
        return None
