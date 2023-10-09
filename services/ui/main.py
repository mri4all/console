import sys
import os

from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore

import qdarktheme # type: ignore
import qtawesome as qta # type: ignore


class RegistrationWindow(QMainWindow):
    def __init__(self):
        super(RegistrationWindow, self).__init__()

        dir_name = os.path.dirname(__file__)
        form_name = os.path.join(dir_name, 'forms/mainwindow.ui')

        uic.loadUi(form_name, self)   
        self.setWindowTitle('MRI4ALL')
        fa5_icon = qta.icon('fa5s.play')
        self.pushButton.setIcon(fa5_icon)
        self.pushButton.setProperty("type", "highlight") 
        self.pushButton.clicked.connect(self.button_clicked)
        self.label.setText("This is someething with a <a href=\"https://www.google.com\">link</a>.");
        print("Initiated")

    def button_clicked(self):
        msg = QMessageBox()
        msg.setText("This is a message box This is a message box This is a message box This is a message box")
        msg.setInformativeText("This is additional information")
        msg.setDetailedText("This is additional information")
        msg.setWindowTitle("MessageBox demo")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.setWindowIcon(QIcon('assets/mri4all_icon.png'))
        msg.exec_()


if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


def run():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('assets/mri4all_icon.png'))

    qss = """
    QPushButton {
        color: #FFFFFF;
        background-color: #FFFFFF;    
    }
    QPushButton:hover {
        color: #FFFFFF;
        background-color: #E0A526;    
    }    
    QPushButton[type = "highlight"] {
         color: #FFFFFF;
         background-color: rgba(224, 165, 38, 120); 
    }  
    QPushButton[type = "highlight"]:hover {
         color: #FFFFFF;
         background-color: #E0A526;    
    }         
    """

    qdarktheme.setup_theme(corner_shape="sharp", 
                           custom_colors={"primary": "#E0A526", "background": "#040919", "border": "#FFFFFF22", "input.background": "#00000022", "statusBar.background": "#040919", 
                                          "foreground": "#FFFFFF", "primary>button.hoverBackground": "#E0A52645", "tableSectionHeader.background": "#262C44", "linkVisited": "#E0A526"}, 
                           additional_qss=qss)

    window = RegistrationWindow()    
    window.showFullScreen()

    sys.exit(app.exec_())


if __name__ == '__main__':
    run()
