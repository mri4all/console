from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from pydantic import ValidationError  # type: ignore

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
        if (index.column() > 0 and index.data(1) is None) or (
            index.column() == 0 and index.data(1) == "name"
        ):
            return super(MyDelegate, self).createEditor(parent, option, index)
        return None


def editable(i):
    i.setFlags(i.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled)
    return i


class ConfigurationWindow(QDialog):
    tree: QTreeWidget
    settingsWidget: QTreeWidget

    def __init__(self):
        super(ConfigurationWindow, self).__init__()
        uic.loadUi(f"{rt.get_console_path()}/services/ui/forms/configuration.ui", self)
        self.setWindowTitle("Console Configuration")
        self.saveButton.clicked.connect(self.save_clicked)
        self.cancelButton.clicked.connect(self.cancel_clicked)
        self.tree = self.findChild(QTreeWidget, "dicomTargetWidget")
        self.findChild(QPushButton, "deleteTargetButton").clicked.connect(
            self.delete_target_clicked
        )
        self.findChild(QPushButton, "addTargetButton").clicked.connect(
            self.add_target_clicked
        )

        self.config = Configuration.load_from_file()

        delegate = MyDelegate()
        self.tree.setItemDelegate(delegate)
        for n, target in enumerate(self.config.dicom_targets):
            item = self.make_target_item(target)
            self.tree.insertTopLevelItem(n, item)

        self.settingsWidget = self.findChild(QTreeWidget, "generalSettingsWidget")
        self.settingsWidget.setItemDelegate(delegate)

        for n, (key, value) in enumerate(Configuration.model_fields.items()):
            if value.annotation in (str, int):
                self.settingsWidget.insertTopLevelItem(
                    n, editable(QTreeWidgetItem([key, str(getattr(self.config, key))]))
                )

        self.tree.currentItemChanged.connect(self.start_edit)
        self.settingsWidget.currentItemChanged.connect(self.start_edit)

    def start_edit(self):
        tree: QTreeWidget = self.sender()
        if tree.currentItem().childCount() == 0:
            tree.edit(tree.currentIndex().siblingAtColumn(1))

    def make_target_item(self, target: DicomTarget):
        item = editable(QTreeWidgetItem([target.name]))
        item.setData(0, 1, "name")
        item.setData(1, 1, "name")
        for c in ["ip", "port", "aet_target", "aet_source"]:
            item.addChild(editable(QTreeWidgetItem([c, str(getattr(target, c))])))

        return item

    def cancel_clicked(self):
        self.close()

    def save_clicked(self) -> None:
        targets = []
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            target = {}
            target["name"] = item.data(0, 0)
            for j in range(item.childCount()):
                child = item.child(j)
                target[child.data(0, 0)] = child.data(1, 0)
            try:
                targets.append(DicomTarget(**target))
            except ValidationError as e:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("Validation Error")
                msg.setText(f"Error in {target['name']}: \n {e}")
                msg.exec_()
                return

        settingsWidget: QTreeWidget = self.findChild(
            QTreeWidget, "generalSettingsWidget"
        )
        new_config = {}
        for i in range(settingsWidget.topLevelItemCount()):
            item = settingsWidget.topLevelItem(i)
            new_config[item.data(0, 0)] = item.data(1, 0)

        try:
            self.config.update(new_config)
        except ValidationError as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Validation Error")
            msg.setText(str(e))
            msg.exec_()
            return

        self.config.dicom_targets = targets

        self.config.save_to_file()
        self.close()

    def delete_target_clicked(self):
        items = self.tree.selectedItems()
        item = items[0]
        if item.childCount() == 0:
            item = item.parent()
        index = self.tree.indexOfTopLevelItem(item)
        self.tree.takeTopLevelItem(index)

    def add_target_clicked(self):
        item = self.make_target_item(
            DicomTarget(
                name="New Target", ip="", port=11112, aet_target="", aet_source=""
            )
        )
        self.tree.insertTopLevelItem(self.tree.topLevelItemCount(), item)
