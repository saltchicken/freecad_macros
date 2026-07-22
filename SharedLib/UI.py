import FreeCAD as App
import FreeCADGui as Gui

# Cross-compatible Qt import for FreeCAD 0.21 (Qt5) and FreeCAD 1.0+ (Qt6)
try:
    from PySide6 import QtCore, QtWidgets
except ImportError:
    from PySide2 import QtCore, QtWidgets


class BaseTaskPanel:
    """
    A reusable base class for FreeCAD Task Panels.
    Handles UI loading, debounced previews, and safe undo transactions.
    """

    def __init__(self, ui_file_path, has_preview=True):
        self.form = Gui.PySideUic.loadUi(ui_file_path)
        self.has_preview = has_preview
        self.preview_obj = None

        if self.has_preview:
            # Setup Debouncer (QTimer) to prevent FreeCAD freezing during slider drags
            self.preview_timer = QtCore.QTimer()
            self.preview_timer.setSingleShot(True)
            self.preview_timer.setInterval(150)  # 150ms delay
            self.preview_timer.timeout.connect(self._trigger_preview)

            # Create a temporary object for the live preview without holding a transaction open
            self.preview_obj = App.ActiveDocument.addObject("Part::Feature", "PreviewObject")

        self.setup_ui()

        if self.has_preview:
            self.queue_preview()

    def setup_ui(self):
        """Override this in your child class to connect UI signals."""
        pass

    def queue_preview(self, *args):
        """Call this from UI signals instead of updating directly."""
        if self.has_preview:
            self.preview_timer.start()

    def _trigger_preview(self):
        """Internal method executed when the timer finishes."""
        if hasattr(self.form, "live_preview_cb") and not self.form.live_preview_cb.isChecked():
            return

        try:
            shape = self.calculate_preview()
            if shape and not shape.isNull() and self.preview_obj:
                self.preview_obj.Shape = shape
                App.ActiveDocument.recompute()
        except Exception as e:
            App.Console.PrintWarning(f"Preview calculation error: {e}\n")

    def calculate_preview(self):
        """Override this in your child class. Must return a Part.Shape."""
        return None

    def generate_final(self):
        """Override this in your child class to generate parametric objects."""
        pass

    # --- FreeCAD Task Panel Hooks ---

    def getStandardButtons(self):
        return (QtWidgets.QDialogButtonBox.Ok |
                QtWidgets.QDialogButtonBox.Cancel).value

    def accept(self):
        # 1. Clean up the temporary preview object safely
        if self.has_preview and self.preview_obj:
            App.ActiveDocument.removeObject(self.preview_obj.Name)

        # 2. Open a clean transaction for the actual generation
        App.ActiveDocument.openTransaction("Apply Tool")
        try:
            self.generate_final()
            App.ActiveDocument.commitTransaction()
        except Exception as e:
            App.ActiveDocument.abortTransaction()
            App.Console.PrintError(f"Generation failed: {e}\n")

        Gui.Control.closeDialog()

    def reject(self):
        # Clean up the temporary preview object on cancellation
        if self.has_preview and self.preview_obj:
            App.ActiveDocument.removeObject(self.preview_obj.Name)
            App.ActiveDocument.recompute()
            
        Gui.Control.closeDialog()
