from typing import Optional
import typing
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import qtawesome as qta  # type: ignore
from pydantic import BaseModel, ValidationError  # type: ignore

from common.version import mri4all_version

from common.config import Configuration, DicomTarget
import common.runtime as rt
import common.logger as logger
from services.ui import ui_runtime
import common.config as config

log = logger.get_logger()


def show_configuration():
    configuration_window = ConfigurationWindow()
    configuration_window.exec_()


class dicomEditDelegate(QItemDelegate):
    def createEditor(self, parent, option, index):
        if (index.column() > 0 and index.data(1) is None) or (
            index.column() == 0 and index.data(1) == "name"
        ):
            return super(dicomEditDelegate, self).createEditor(parent, option, index)
        return None

    def sizeHint(self, option, index):
        width = option.rect.width()
        height = 30
        return QSize(width, height)


class settingsEditDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        if index.column() > 1:
            return super(settingsEditDelegate, self).createEditor(parent, option, index)
        return None

    def sizeHint(self, option, index):
        width = option.rect.width() + 20
        height = 30
        return QSize(width, height)


def editable(i):
    i.setFlags(i.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled)
    return i


class ConfigurationWindow(QDialog):
    dicomWidget: QTreeWidget
    settingsWidget: QTreeWidget

    def __init__(self):
        super(ConfigurationWindow, self).__init__()
        uic.loadUi(f"{rt.get_console_path()}/services/ui/forms/configuration.ui", self)
        self.setWindowTitle("Configuration")
        self.saveButton.clicked.connect(self.save_clicked)
        self.saveButton.setProperty("type", "highlight")
        self.saveButton.setIcon(qta.icon("fa5s.check"))
        self.saveButton.setIconSize(QSize(20, 20))
        self.saveButton.setText(" Save")

        self.cancelButton.clicked.connect(self.cancel_clicked)
        self.cancelButton.setIcon(qta.icon("fa5s.times"))
        self.cancelButton.setIconSize(QSize(20, 20))
        self.cancelButton.setText(" Cancel")

        self.dicomWidget = self.findChild(QTreeWidget, "dicomTargetWidget")
        self.findChild(QPushButton, "deleteTargetButton").clicked.connect(
            self.delete_target_clicked
        )
        self.findChild(QPushButton, "addTargetButton").clicked.connect(
            self.add_target_clicked
        )

        self.config = config.get_config()

        # Setup widget for editing DICOM targets
        self.dicomWidget.setItemDelegate(dicomEditDelegate())
        for n, target in enumerate(self.config.dicom_targets):
            item = self.make_target_item(target)
            self.dicomWidget.insertTopLevelItem(n, item)
        self.dicomWidget.currentItemChanged.connect(self.dicom_start_edit)
        self.dicomTargetWidget.setStyleSheet("QLineEdit{background-color: #181e36;}")

        # Setup widget for general settings
        self.settingsWidget = self.findChild(QTreeWidget, "generalSettingsWidget")
        self.settingsWidget.setItemDelegate(settingsEditDelegate())

        n = 0
        for key, value in Configuration.model_fields.items():
            if value.annotation in (str, int, float):
                # Derive description that is shown in the first visible column. If the field
                # does not provide a description, the field name is used
                key_description = Configuration.model_fields[key].description
                if not key_description:
                    key_description = key
                else:
                    if key_description == "hidden":
                        continue
                new_item = QTreeWidgetItem(
                    [
                        key,
                        key_description,
                        str(getattr(self.config, key)),
                    ]
                )
                self.settingsWidget.insertTopLevelItem(
                    n,
                    editable(new_item),
                )
                n = n + 1

        self.settingsWidget.setColumnHidden(0, True)
        self.settingsWidget.currentItemChanged.connect(self.general_start_edit)
        self.generalSettingsWidget.setStyleSheet(
            "QLineEdit { background-color: #181e36; } QHeaderView::section { height: 30px; font-weight: normal; color: #E0A526; }"
        )
        self.tabWidget.setTabText(0, "General")
        self.tabWidget.setTabText(1, "DICOM Export")
        self.tabWidget.setTabText(2, "Maintenance")
        self.tabWidget.setCurrentIndex(0)
        self.setStyleSheet(
            """
            QTabBar::tab {
                margin-left:0px;
                margin-right:10px;          
            }
            """
        )

    def dicom_start_edit(self):
        tree: QTreeWidget = self.sender()
        if tree.currentItem():
            if tree.currentItem().childCount() == 0:
                tree.edit(tree.currentIndex().siblingAtColumn(1))

    def general_start_edit(self):
        tree: QTreeWidget = self.sender()
        if tree.currentItem():
            if tree.currentColumn() != 2:
                tree.edit(tree.currentIndex().siblingAtColumn(2))

    def make_target_item(self, target: DicomTarget):
        item = editable(QTreeWidgetItem([target.name]))
        item.setToolTip(0, "Double click to edit name")
        item.setData(0, 1, "name")
        item.setData(1, 1, "name")
        for c in ["ip", "port", "aet_target", "aet_source"]:
            item.addChild(editable(QTreeWidgetItem([c, str(getattr(target, c))])))
        return item

    def cancel_clicked(self):
        self.close()

    def save_clicked(self) -> None:
        targets = []
        for i in range(self.dicomWidget.topLevelItemCount()):
            item = self.dicomWidget.topLevelItem(i)
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
            new_config[item.data(0, 0)] = item.data(2, 0)

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
        items = self.dicomWidget.selectedItems()
        if len(items) == 0:
            return
        item = items[0]
        if item.childCount() == 0:
            item = item.parent()
        index = self.dicomWidget.indexOfTopLevelItem(item)
        self.dicomWidget.takeTopLevelItem(index)

    def add_target_clicked(self):
        item = self.make_target_item(
            DicomTarget(
                name="New Target",
                ip="",
                port=11112,
                aet_target="",
                aet_source="mri4all",
            )
        )
        self.dicomWidget.insertTopLevelItem(self.dicomWidget.topLevelItemCount(), item)
