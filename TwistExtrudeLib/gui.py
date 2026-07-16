import FreeCAD as App
import FreeCADGui as Gui
from PySide6 import QtWidgets, QtCore

from TwistExtrudeLib import core

class TwistExtrudeDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TwistExtrude Generator")
        self.resize(300, 200)
        
        # Main layout
        layout = QtWidgets.QVBoxLayout(self)
        
        # Instructions
        label = QtWidgets.QLabel("1. Select a Sketch in the tree view.\n2. Set your parameters below.\n3. Click Generate.")
        layout.addWidget(label)
        
        # Form Layout for Inputs
        form_layout = QtWidgets.QFormLayout()
        
        self.height_spin = QtWidgets.QDoubleSpinBox()
        self.height_spin.setRange(-10000.0, 10000.0)
        self.height_spin.setValue(120.0)
        self.height_spin.setSuffix(" mm")
        form_layout.addRow("Total Height:", self.height_spin)
        
        self.angle_spin = QtWidgets.QDoubleSpinBox()
        self.angle_spin.setRange(-3600.0, 3600.0)
        self.angle_spin.setValue(360.0)
        self.angle_spin.setSuffix(" °")
        form_layout.addRow("Total Angle:", self.angle_spin)
        
        self.sections_spin = QtWidgets.QSpinBox()
        self.sections_spin.setRange(2, 500)
        self.sections_spin.setValue(24)
        form_layout.addRow("Number of Sections:", self.sections_spin)
        
        layout.addLayout(form_layout)
        
        # Generate Button
        self.btn_gen = QtWidgets.QPushButton("Generate Sketches")
        self.btn_gen.setStyleSheet("font-weight: bold; padding: 10px;")
        self.btn_gen.clicked.connect(self.generate)
        layout.addWidget(self.btn_gen)

    def generate(self):
        total_height = self.height_spin.value()
        total_angle = self.angle_spin.value()
        num_sections = self.sections_spin.value()
        
        # Call the core logic
        core.generate_twisted_sketches(total_height, total_angle, num_sections)
        
        # Optional: Close the dialog after successful generation
        # self.accept()

# Create a launch function
def run():
    # Keep a reference to the dialog so it isn't garbage collected immediately
    global dialog
    dialog = TwistExtrudeDialog()
    dialog.show()
