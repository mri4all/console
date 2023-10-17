from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # type: ignore

from common.version import mri4all_version

from common.config import Configuration, DicomTarget
import common.runtime as rt
import common.logger as logger

log = logger.get_logger()


def show_configuration():
    configuration_window = ConfigurationWindow()
    configuration_window.exec_()

class MyDelegate(QItemDelegate):

    def createEditor(self, parent, option, index):
        if (index.column() > 0 and index.data(1) is None) or (index.column() == 0 and index.data(1) == "name"):
            return super(MyDelegate, self).createEditor(parent, option, index)
        return None
    
class ConfigurationWindow(QDialog):
    tree: QTreeWidget
    def __init__(self):
        super(ConfigurationWindow, self).__init__()
        uic.loadUi(f"{rt.get_console_path()}/services/ui/forms/configuration.ui", self)
        self.setWindowTitle("Console Configuration")
        self.saveButton.clicked.connect(self.save_clicked)
        self.cancelButton.clicked.connect(self.cancel_clicked)
        self.tree = self.findChild(QTreeWidget)


        self.config = Configuration.load_from_file()
        
        delegate = MyDelegate()
        self.tree.setItemDelegate(delegate)
        for n,target in enumerate(self.config.dicom_targets):
            item = QTreeWidgetItem([target.name])
            item.setData(0,1,"name")
            item.setData(1,1,"name")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled)
            item.addChild(child := QTreeWidgetItem(["ip",target.ip]))
            child.setFlags(child.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled)
            item.addChild(child := QTreeWidgetItem(["port",str(target.port)]))
            child.setFlags(child.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled)
            item.addChild(child := QTreeWidgetItem(["aet_target",target.aet_target]))
            child.setFlags(child.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled)

            if target.aet_source is not None:
                item.addChild(child:=QTreeWidgetItem(["aet_source",target.aet_source]))
                child.setFlags(child.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled)

            self.tree.insertTopLevelItem(n, item)


    def cancel_clicked(self):
        self.close()

    def save_clicked(self):
        log.info("=======")

        targets = []
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            target = {}
            target["name"] = item.data(0,0)
            for j in range(item.childCount()):
                child = item.child(j)
                target[child.data(0,0)] = child.data(1,0)
            targets.append(DicomTarget(**target))
        self.config.dicom_targets = targets
        self.config.save_to_file()
        self.close()
