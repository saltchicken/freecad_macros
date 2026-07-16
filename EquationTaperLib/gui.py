import FreeCAD as App
import FreeCADGui as Gui
from PySide6 import QtWidgets, QtCore
from EquationTaperLib import core

class EquationTaperDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Equation Taper Generator")
        self.resize(360, 240)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        instruction_text = (
            "1. Select a Base Sketch.\n"
            "2. Define scaling formula using 't' (0.0 to 1.0).\n"
            "   Example: 1.0 + sin(t * pi) * 0.5"
        )
        label = QtWidgets.QLabel(instruction_text)
        layout.addWidget(label)
        
        form_layout = QtWidgets.QFormLayout()
        
        self.height_spin = QtWidgets.QDoubleSpinBox()
        self.height_spin.setRange(0.1, 10000.0)
        self.height_spin.setValue(100.0)
        self.height_spin.setSuffix(" mm")
        form_layout.addRow("Total Height:", self.height_spin)
        
        self.sections_spin = QtWidgets.QSpinBox()
        self.sections_spin.setRange(2, 500)
        self.sections_spin.setValue(12)
        form_layout.addRow("Number of Sections:", self.sections_spin)
        
        self.equation_input = QtWidgets.QLineEdit()
        # Default equation creates a nice belly bulge
        self.equation_input.setText("1.0 + sin(t * pi) * 0.5")
        self.equation_input.setToolTip("Available variables: t (time 0-1), z (height). Available math: sin, cos, pi, etc.")
        form_layout.addRow("Scale Formula:", self.equation_input)
        
        layout.addLayout(form_layout)
        
        self.btn_gen = QtWidgets.QPushButton("Generate Equation Loft")
        self.btn_gen.setStyleSheet("font-weight: bold; padding: 10px;")
        self.btn_gen.clicked.connect(self.generate)
        layout.addWidget(self.btn_gen)

    def generate(self):
        total_height = self.height_spin.value()
        num_sections = self.sections_spin.value()
        equation_str = self.equation_input.text()
        
        core.generate_equation_taper(total_height, num_sections, equation_str)

def run():
    global dialog
    dialog = EquationTaperDialog()
    dialog.show()
