import FreeCAD as App
import FreeCADGui as Gui
from PySide6 import QtWidgets, QtCore
from PathTwistSweepLib import core

class PathTwistSweepDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Path Twist Sweep Generator")
        self.resize(320, 200)
        
        # Main layout
        layout = QtWidgets.QVBoxLayout(self)
        
        # Instructions (Updated for Path Selection)
        instruction_text = (
            "1. Select the Profile Sketch.\n"
            "2. Ctrl+click the Path Sketch.\n"
            "3. Set your parameters below.\n"
            "4. Click Generate."
        )
        label = QtWidgets.QLabel(instruction_text)
        layout.addWidget(label)
        
        # Form Layout for Inputs
        form_layout = QtWidgets.QFormLayout()
        
        # Total Height is removed because length is governed by the Path length!
        
        self.angle_spin = QtWidgets.QDoubleSpinBox()
        self.angle_spin.setRange(-3600.0, 3600.0)
        self.angle_spin.setValue(360.0)
        self.angle_spin.setSuffix(" °")
        form_layout.addRow("Total Twist Angle:", self.angle_spin)
        
        self.sections_spin = QtWidgets.QSpinBox()
        self.sections_spin.setRange(2, 500)
        self.sections_spin.setValue(24)
        form_layout.addRow("Number of Sections:", self.sections_spin)
        
        layout.addLayout(form_layout)
        
        # Generate Button
        self.btn_gen = QtWidgets.QPushButton("Generate Sweep")
        self.btn_gen.setStyleSheet("font-weight: bold; padding: 10px;")
        self.btn_gen.clicked.connect(self.generate)
        layout.addWidget(self.btn_gen)

    def generate(self):
        total_angle = self.angle_spin.value()
        num_sections = self.sections_spin.value()
        
        # Call the core logic
        core.generate_path_twist_sketches(total_angle, num_sections)

# Create a launch function
def run():
    global dialog
    dialog = PathTwistSweepDialog()
    dialog.show()
