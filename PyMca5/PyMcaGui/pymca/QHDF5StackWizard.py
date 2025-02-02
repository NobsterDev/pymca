#/*##########################################################################
# Copyright (C) 2004-2018 V.A. Sole, European Synchrotron Radiation Facility
#
# This file is part of the PyMca X-ray Fluorescence Toolkit developed at
# the ESRF by the Software group.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#############################################################################*/
__author__ = "V.A. Sole - ESRF Data Analysis"
__contact__ = "sole@esrf.fr"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
import sys
import os
import posixpath
from PyMca5.PyMcaGui import PyMcaQt as qt
safe_str = qt.safe_str
from PyMca5.PyMcaGui.io.hdf5 import QNexusWidget
from PyMca5.PyMcaCore import NexusDataSource
from PyMca5 import PyMcaDirs


class IntroductionPage(qt.QWizardPage):
    def __init__(self, parent):
        qt.QWizardPage.__init__(self, parent)
        self.setTitle("HDF5 Stack Selection Wizard")
        text  = "This wizard will help you to select the "
        text += "appropriate dataset(s) belonging to your stack"
        self.setSubTitle(text)


class FileListPage(qt.QWizardPage):
    def __init__(self, parent):
        qt.QWizardPage.__init__(self, parent)
        self.setTitle("HDF5 Stack File Selection")
        text  = "The files below belong to your stack"
        self.setSubTitle(text)
        self.fileList = []
        self.inputDir = None
        self.mainLayout= qt.QVBoxLayout(self)
        listlabel   = qt.QLabel(self)
        listlabel.setText("Input File list")
        self._listView = qt.QTextEdit(self)
        self._listView.setMaximumHeight(30*listlabel.sizeHint().height())
        self._listView.setReadOnly(True)

        self._listButton = qt.QPushButton(self)
        self._listButton.setText('Browse')
        self._listButton.setAutoDefault(False)

        self.mainLayout.addWidget(listlabel)
        self.mainLayout.addWidget(self._listView)
        self.mainLayout.addWidget(self._listButton)

        self._listButton.clicked.connect(self.browseList)

    def setFileList(self, filelist):
        text = ""
        #filelist.sort()
        for ffile in filelist:
            text += "%s\n" % ffile
        self.fileList = filelist
        self._listView.setText(text)

    def validatePage(self):
        if not len(self.fileList):
            return False
        return True

    def browseList(self):
        if self.inputDir is None:
            self.inputDir = PyMcaDirs.inputDir
        if not os.path.exists(self.inputDir):
            self.inputDir =  os.getcwd()
        wdir = self.inputDir
        filedialog = qt.QFileDialog(self)
        filedialog.setWindowTitle("Open a set of files")
        filedialog.setDirectory(wdir)
        if hasattr(filedialog, "setFilters"):
            filedialog.setFilters(["HDF5 Files (*.nxs *.h5 *.hdf *.hdf5)",
                                   "HDF5 Files (*.h5)",
                                   "HDF5 Files (*.hdf)",
                                   "HDF5 Files (*.hdf5)",
                                   "HDF5 Files (*.nxs)",
                                   "HDF5 Files (*)"])
        else:
            filedialog.setNameFilters(["HDF5 Files (*.nxs *.h5 *.hdf *.hdf5)",
                                       "HDF5 Files (*.h5)",
                                       "HDF5 Files (*.hdf)",
                                       "HDF5 Files (*.hdf5)",
                                       "HDF5 Files (*.nxs)",
                                       "HDF5 Files (*)"])
        filedialog.setModal(1)
        filedialog.setFileMode(filedialog.ExistingFiles)
        ret = filedialog.exec()
        if  ret == qt.QDialog.Accepted:
            filelist0=filedialog.selectedFiles()
        else:
            self.raise_()
            return
        filelist = []
        for f in filelist0:
            filelist.append(safe_str(f))
        if len(filelist):
            self.setFileList(filelist)
        PyMcaDirs.inputDir = os.path.dirname(filelist[0])
        self.inputDir = os.path.dirname(filelist[0])
        self.raise_()


class StackIndexWidget(qt.QWidget):
    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)
        self.mainLayout = qt.QHBoxLayout(self)
        #self.mainLayout.setContentsMargins(0, 0, 0, 0)
        #self.mainLayout.setSpacing(0)

        self.buttonGroup = qt.QButtonGroup(self)
        i = 0
        for text in ["1D data is first dimension", "1D data is last dimension"]:
            rButton = qt.QRadioButton(self)
            rButton.setText(text)
            self.mainLayout.addWidget(rButton)
            self.buttonGroup.addButton(rButton, i)
            i += 1
        rButton.setChecked(True)
        self._stackIndex = -1
        self.buttonGroup.buttonPressed.connect(self._slot)

    def _slot(self, button):
        if "first" in safe_str(button.text()).lower():
            self._stackIndex =  0
        else:
            self._stackIndex = -1

    def setIndex(self, index):
        if index == 0:
            self._stackIndex = 0
            self.buttonGroup.button(0).setChecked(True)
        else:
            self._stackIndex = -1
            self.buttonGroup.button(1).setChecked(True)


class DatasetSelectionPage(qt.QWizardPage):
    def __init__(self, parent):
        qt.QWizardPage.__init__(self, parent)
        self.setTitle("HDF5 Dataset Selection")
        text  = "Double click on the datasets you want to consider "
        text += "and select the role they will play at the end by "
        text += "selecting the appropriate checkbox(es)"
        self.selection = None
        self.setSubTitle(text)
        self.mainLayout = qt.QVBoxLayout(self)
        self.nexusWidget = LocalQNexusWidget(self)
        self.nexusWidget.buttons.hide()
        self.mainLayout.addWidget(self.nexusWidget, 1)

        self.stackIndexWidget = StackIndexWidget(self)
        self.mainLayout.addWidget(self.stackIndexWidget, 0)

    def setFileList(self, filelist):
        self.dataSource = NexusDataSource.NexusDataSource(filelist[0])
        self.nexusWidget.setDataSource(self.dataSource)
        phynxFile = self.dataSource._sourceObjectList[0]
        keys = list(phynxFile.keys())
        if len(keys) != 1:
            return

        #check if it is an NXentry
        entry = phynxFile[keys[0]]
        attrs = list(entry.attrs)
        if 'NX_class' in attrs:
            attr = entry.attrs['NX_class']
            if hasattr(attr, "decode"):
                try:
                    attr = attr.decode('utf-8')
                except:
                    print("WARNING: Cannot decode NX_class attribute")
                    attr = None
        else:
            attr = None
        if attr is None:
            return
        if attr not in ['NXentry', b'NXentry']:
            return

        #check if there is only one NXdata
        nxDataList = []
        for key in entry.keys():
            attr = entry[key].attrs.get('NX_class', None)
            if attr is None:
                continue
            if hasattr(attr, "decode"):
                try:
                    attr = attr.decode('utf-8')
                except:
                    print("WARNING: Cannot decode NX_class attribute")
                    continue
            if attr in ['NXdata', b'NXdata']:
                nxDataList.append(key)
        if len(nxDataList) != 1:
            return
        nxData = entry[nxDataList[0]]

        ddict = {'counters': [],
                 'aliases': []}
        signalList = []
        axesList = []
        interpretation = ""

        signal_key = nxData.attrs.get("signal")
        if signal_key is not None:
            # recent NXdata specification
            if hasattr(signal_key, "decode"):
                try:
                    signal_key = signal_key.decode('utf-8')
                except AttributeError:
                    print("WARNING: Cannot decode NX_class attribute")

            signal_dataset = nxData.get(signal_key)
            if signal_dataset is None:
                return

            interpretation = signal_dataset.attrs.get("interpretation", "")
            if hasattr(interpretation, "decode"):
                try:
                    interpretation = interpretation.decode('utf-8')
                except AttributeError:
                    print("WARNING: Cannot decode interpretation")

            axesList = list(nxData.attrs.get("axes", []))
            if not axesList:
                # try the old method, still documented on nexusformat.org:
                # colon-delimited "array" of dataset names as a signal attr
                axes = signal_dataset.attrs.get('axes')
                if axes is not None:
                    if hasattr(axes, "decode"):
                        try:
                            axes = axes.decode('utf-8')
                        except AttributeError:
                            print("WARNING: Cannot decode axes")
                    axes = axes.split(":")
                    axesList = [ax for ax in axes if ax in nxData]
            signalList.append(signal_key)
        else:
            # old specification
            for key in nxData.keys():
                if 'signal' in nxData[key].attrs.keys():
                    if int(nxData[key].attrs['signal']) == 1:
                        signalList.append(key)
                        if len(signalList) == 1:
                            if 'interpretation' in nxData[key].attrs.keys():
                                interpretation = nxData[key].attrs['interpretation']
                                if sys.version > '2.9':
                                    try:
                                        interpretation = interpretation.decode('utf-8')
                                    except:
                                        print("WARNING: Cannot decode interpretation")

                            if 'axes' in nxData[key].attrs.keys():
                                axes = nxData[key].attrs['axes']
                                if sys.version > '2.9':
                                    try:
                                        axes = axes.decode('utf-8')
                                    except:
                                        print("WARNING: Cannot decode axes")
                                axes = axes.split(":")
                                for axis in axes:
                                    if axis in nxData.keys():
                                        axesList.append(axis)

            if not len(signalList):
                return

        if interpretation in ["image", b"image"]:
            self.stackIndexWidget.setIndex(0)

        for signal_key in signalList:
            path = posixpath.join("/", nxDataList[0], signal_key)
            ddict['counters'].append(path)
            ddict['aliases'].append(posixpath.basename(signal_key))

        for axis in axesList:
            path = posixpath.join("/", nxDataList[0], axis)
            ddict['counters'].append(path)
            ddict['aliases'].append(posixpath.basename(axis))

        if sys.platform == "darwin" and\
           len(ddict['counters']) > 3 and\
           qt.qVersion().startswith('4.8'):
            # workaround a strange bug on Mac:
            # when the counter list has to be scrolled
            # the selected button also changes!!!!
            return

        self.nexusWidget.setWidgetConfiguration(ddict)

        if axesList and (interpretation in ["image", b"image"]):
            self.nexusWidget.cntTable.setCounterSelection({'y': [0], 'x': [1]})
        elif axesList and (interpretation in ["spectrum", b"spectrum"]):
            self.nexusWidget.cntTable.setCounterSelection({'y': [0], 'x': [len(axesList)]})
        else:
            self.nexusWidget.cntTable.setCounterSelection({'y': [0]})

    def validatePage(self):
        cntSelection = self.nexusWidget.cntTable.getCounterSelection()
        cntlist = cntSelection['cntlist']
        if not len(cntlist):
            text = "No dataset selection"
            self.showMessage(text)
            return False
        if not len(cntSelection['y']):
            text = "No dataset selected as y"
            self.showMessage(text)
            return False
        selection = {}
        selection['x'] = []
        selection['y'] = []
        selection['m'] = []
        selection['index'] = self.stackIndexWidget._stackIndex
        for key in ['x', 'y', 'm']:
            if len(cntSelection[key]):
                for idx in cntSelection[key]:
                    selection[key].append(cntlist[idx])
        self.selection = selection
        return True

    def showMessage(self, text):
        msg = qt.QMessageBox(self)
        msg.setIcon(qt.QMessageBox.Information)
        msg.setText(text)
        msg.exec()


class ShapePage(qt.QWizardPage):
    def __init__(self, parent):
        qt.QWizardPage.__init__(self, parent)
        self.setTitle("HDF5 Map Shape Selection")
        text  = "Adjust the shape of your map if necessary"
        self.setSubTitle(text)


class LocalQNexusWidget(QNexusWidget.QNexusWidget):
    def __init__(self, parent=None, mca=False):
        QNexusWidget.QNexusWidget.__init__(self, parent=parent,
                                           mca=mca,
                                           buttons=True)

    def showInfoWidget(self, filename, name, dset=False):
        w = QNexusWidget.QNexusWidget.showInfoWidget(self, filename, name, dset)
        w.hide()
        w.setWindowModality(qt.Qt.ApplicationModal)
        w.show()


class QHDF5StackWizard(qt.QWizard):
    def __init__(self, parent=None):
        qt.QWizard.__init__(self, parent)
        self.setWindowTitle("HDF5 Stack Wizard")
        #self._introduction = self.createIntroductionPage()
        self._fileList     = self.createFileListPage()
        self._datasetSelection = self.createDatasetSelectionPage()
        #self._shape        = self.createShapePage()
        #self.addPage(self._introduction)
        self.addPage(self._fileList)
        self.addPage(self._datasetSelection)
        #self.addPage(self._shape)
        #self.connect(qt.SIGNAL("currentIdChanged(int"),
        #             currentChanged)

    def sizeHint(self):
        width = qt.QWizard.sizeHint(self).width()
        height = qt.QWizard.sizeHint(self).height()
        return qt.QSize(width, int(1.5 * height))

    def createIntroductionPage(self):
        return IntroductionPage(self)

    def setFileList(self, filelist):
        self._fileList.setFileList(filelist)

    def createFileListPage(self):
        return FileListPage(self)

    def createDatasetSelectionPage(self):
        return DatasetSelectionPage(self)

    def createShapePage(self):
        return ShapePage(self)

    def initializePage(self, value):
        if value == 1:
            #dataset page
            self._datasetSelection.setFileList(self._fileList.fileList)

    def getParameters(self):
        return self._fileList.fileList,\
               self._datasetSelection.selection,\
               [x[0] for x in self._datasetSelection.nexusWidget.getSelectedEntries()]


if __name__ == "__main__":
    import sys
    app = qt.QApplication(sys.argv)
    w = QHDF5StackWizard()
    ret = w.exec()
    if ret == qt.QDialog.Accepted:
        print(w.getParameters())
