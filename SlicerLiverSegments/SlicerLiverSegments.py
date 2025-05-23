import logging
import inspect
import os
import re
import random
import itertools
from typing import Annotated, Optional

import vtk

import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
    Validator
)

from slicer import vtkMRMLScalarVolumeNode
from slicer import vtkMRMLTableNode

import qt

class MatchesInteger(Validator):
   def validate(self, value):
      if re.match("[0-9]+", value) is None:
          raise ValueError("Did not match integer value")

@parameterNodeWrapper
class SlicerLiverSegmentsParameterNode:
    volumesDirectory: str = ""
    method1Directory: str = ""
    method2Directory: str = ""
    method3Directory: str = ""
    method4Directory: str = ""
    orderSeed: Annotated[str, MatchesInteger()] = str(random.randint(0,65535))
    outputFileName: str = ""
    resultsTableNode: vtkMRMLTableNode = None
    question1Score:  Annotated[int, WithinRange(1,5)] = 1
    question2Score:  Annotated[int, WithinRange(1,5)] = 1
    question3Score:  Annotated[int, WithinRange(1,5)] = 1
    question4Score:  Annotated[int, WithinRange(1,5)] = 1
    totalEvaluations: int
    currentEvaluation: int

#
# SlicerLiverSegments
#

class SlicerLiverSegments(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "SlicerLiverSegments"  # TODO: make this more human readable by adding spaces
        self.parent.categories = ["Evaluation"]  # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["Rafael Palomar (Oslo University Hospital)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        self.parent.helpText = """
        This module helps evaluating liver segments classification
        """

        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = """
        This file was originally developed by Rafael Palomar
        """

        # Additional initialization step after application startup is complete
        #slicer.app.connect("startupCompleted()", registerSampleData)

#
# SlicerLiverSegmentsWidget
#

class SlicerLiverSegmentsWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.__init__(self, parent)

    def setup(self) -> None:
        """
        Called when the user opens the module the first time and the widget is initialized.
        """

        self.logic = SlicerLiverSegmentsLogic()
        self._parameterNode = self.logic.getParameterNode()

        ScriptedLoadableModuleWidget.setup(self)

        uiWidget = slicer.util.loadUI(self.resourcePath("UI/SlicerLiverSegments.ui"))
        uiWidget.setMRMLScene(slicer.mrmlScene)
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Manage directory selection
        self.ui.volumesDirPushButton.clicked.connect(
            lambda:
            self.ui.volumesDirLineEdit.setText(
                qt.QFileDialog.getExistingDirectory(None, "Select Volumes Directory"))
            )

        self.ui.method1DirPushButton.clicked.connect(
            lambda:
            self.ui.method1DirLineEdit.setText(
                qt.QFileDialog.getExistingDirectory(None, "Select Method 1 Segmentations Directory"))
            )

        self.ui.method2DirPushButton.clicked.connect(
            lambda:
            self.ui.method2DirLineEdit.setText(
                qt.QFileDialog.getExistingDirectory(None, "Select Method 2 Segmentations Directory"))
            )

        self.ui.method3DirPushButton.clicked.connect(
            lambda:
            self.ui.method3DirLineEdit.setText(
                qt.QFileDialog.getExistingDirectory(None, "Select Method 3 Segmentations Directory"))
            )

        self.ui.method4DirPushButton.clicked.connect(
            lambda:
            self.ui.method4DirLineEdit.setText(
                qt.QFileDialog.getExistingDirectory(None, "Select Method 4 Segmentations Directory"))
            )

        self.ui.outputFilePushButton.clicked.connect(
            lambda:
            self.ui.outputFileLineEdit.setText(
                qt.QFileDialog.getSaveFileName(None, "Output file", ".", "CSV Files (*.csv);; All Files (*)"))
            )

        # Qt event connections
        self.ui.startExperimentPushButton.clicked.connect(self.startExperiment)
        self.ui.saveAndNextPushButton.clicked.connect(self.onSaveAndNext)
        self.ui.previousPushButton.clicked.connect(self.onPrevious)
        self.ui.firstPushButton.clicked.connect(self.onFirst)
        self.ui.lastPushButton.clicked.connect(self.onLast)
        self.ui.orderSeedPushButton.clicked.connect(self.onGenerateNewOrderSeed)

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)
        self._parameterNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.enableStartExperimentButtonIfPossible)


    def onGenerateNewOrderSeed(self) -> None:
        # Generate a new random seed
        new_seed = str(random.randint(0, 65535))
        # Update the parameter node
        self._parameterNode.orderSeed = new_seed
        # Update the UI
        self.ui.orderSeedLineEdit.setText(new_seed)

    def onFirst(self) -> None:
        # Save current data before proceeding
        self.logic.saveCurrentDataToTable()

        reply = qt.QMessageBox.question(
            self.parent,
            'Confirmation',
            'Are you sure you want to go to the first dataset?',
            qt.QMessageBox.Yes | qt.QMessageBox.No
        )
        if reply == qt.QMessageBox.Yes:
            self.logic.firstDataset()
            # Update button states
            self.ui.firstPushButton.setEnabled(False)
            self.ui.previousPushButton.setEnabled(False)
            self.ui.lastPushButton.setEnabled(True)
            self.ui.saveAndNextPushButton.setEnabled(True)
            if self.logic.isLastDataset():
                self.ui.saveAndNextPushButton.setText("Save")
            else:
                self.ui.saveAndNextPushButton.setText("Save and Next")
            # Update progress bar
            self.ui.progressBar.setValue(
                self._parameterNode.currentEvaluation /
                self._parameterNode.totalEvaluations * 100
            )

    def onLast(self) -> None:
        # Save current data before proceeding
        self.logic.saveCurrentDataToTable()

        reply = qt.QMessageBox.question(
            self.parent,
            'Confirmation',
            'Are you sure you want to go to the last dataset?',
            qt.QMessageBox.Yes | qt.QMessageBox.No
        )
        if reply == qt.QMessageBox.Yes:
            self.logic.lastDataset()
            # Update button states
            self.ui.firstPushButton.setEnabled(True)
            self.ui.previousPushButton.setEnabled(True)
            self.ui.lastPushButton.setEnabled(False)
            self.ui.saveAndNextPushButton.setEnabled(True)
            self.ui.saveAndNextPushButton.setText("Save")
            # Update progress bar
            self.ui.progressBar.setValue(
                self._parameterNode.currentEvaluation /
                self._parameterNode.totalEvaluations * 100
            )


    def onSaveAndNext(self) -> None:
        # Save current data
        self.logic.saveCurrentDataToTable()

        if not self.logic.isLastDataset():
            reply = qt.QMessageBox.question(
                self.parent,
                'Confirmation',
                'Are you sure you want to proceed to the next dataset?',
                qt.QMessageBox.Yes | qt.QMessageBox.No
            )
            if reply == qt.QMessageBox.Yes:
                self.logic.nextDataset()
                self.ui.previousPushButton.setEnabled(True)
                self.ui.firstPushButton.setEnabled(True)

                # Update button text and states
                if self.logic.isLastDataset():
                    self.ui.saveAndNextPushButton.setText("Save")
                    self.ui.lastPushButton.setEnabled(False)
                else:
                    self.ui.saveAndNextPushButton.setText("Save and Next")
                    self.ui.lastPushButton.setEnabled(True)
        else:
            # We are on the last dataset
            # Inform the user that they've reached the end
            qt.QMessageBox.information(
                self.parent,
                'Information',
                'You are on the last dataset. Your responses have been saved. You can navigate back to review or modify your responses.'
            )
            # Keep navigation buttons enabled
            self.ui.saveAndNextPushButton.setText("Save")
            self.ui.saveAndNextPushButton.setEnabled(True)
            self.ui.lastPushButton.setEnabled(False)
            self.ui.previousPushButton.setEnabled(True)
            self.ui.firstPushButton.setEnabled(True)

        # Update progress
        self.ui.progressBar.setValue(
            self._parameterNode.currentEvaluation /
            self._parameterNode.totalEvaluations * 100
        )

    def onPrevious(self) -> None:
        self.ui.saveAndNextPushButton.setEnabled(True)
        self.logic.previousDataset()
        # Adjust button text if not on last dataset
        if self.logic.isLastDataset():
            self.ui.saveAndNextPushButton.setText("Save")
            self.ui.lastPushButton.setEnabled(False)
        else:
            self.ui.saveAndNextPushButton.setText("Save and Next")
            self.ui.lastPushButton.setEnabled(True)
        if self.logic.isPreviousFirstDataset():
            self.ui.previousPushButton.setEnabled(False)
            self.ui.firstPushButton.setEnabled(False)
        else:
            self.ui.previousPushButton.setEnabled(True)
            self.ui.firstPushButton.setEnabled(True)
        # Update progress bar
        self.ui.progressBar.setValue(
            self._parameterNode.currentEvaluation /
            self._parameterNode.totalEvaluations * 100
        )

    def startExperiment(self) -> None:

        if self.logic.initializeExperiment():
            self.ui.startExperimentPushButton.setEnabled(False)
            self.ui.directoriesGroupBox.setEnabled(False)
            self.ui.parametersGroupBox.setEnabled(False)
            self.ui.q1GroupBox.setEnabled(True)
            self.ui.q2GroupBox.setEnabled(True)
            self.ui.q3GroupBox.setEnabled(True)
            self.ui.q4GroupBox.setEnabled(True)
            self.ui.saveAndNextPushButton.setEnabled(True)
            self.ui.lastPushButton.setEnabled(True)
            self.logic.startExperiment()
        else:
           raise ValueError("Number of files in volume and methods directory must be equal")

    def enableStartExperimentButtonIfPossible(self, caller, event) -> None:
        self.ui.startExperimentPushButton.setEnabled(self.logic.canExperimentStart())

    def initializeParameterNode(self) -> None:
        self._parameterNode =  self.logic.getParameterNode()

    def cleanup(self) -> None:
        """
        Called when the application closes and the module widget is destroyed.
        """
        self.removeObservers()


    def enter(self) -> None:
        """
        Called each time the user opens this module.
        """
        self.initializeParameterNode()
        self._parameterNodeConnectionTag = self._parameterNode.connectGui(self.ui)

    def exit(self) -> None:
        """
        Called each time the user opens a different module.
        """
        self._parameterNode.disconnectGui(self._parameterNodeConnectionTag)
        self._parameterNodeConnectionTag = None


    def onSceneStartClose(self, caller, event) -> None:
        """
        Called just before the scene is closed.
        """
        pass

    def onSceneEndClose(self, caller, event) -> None:
        """
        Called just after the scene is closed.
        """
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            pass

    def onStartExperimentButton(self) -> None:
        """
        Called upon start experiment button is pressed
        """
        success = self.logic.startExperiment(self.folderPathLineEditVolumes.text, self.folderPathLineEditSegmentations.text)
        if success:

            # Update button states
            self.prevButton.setEnabled(False)
            self.nextButton.setEnabled(True)

    def selectFolder(self, targetLineEdit) -> None:
        selectedFolder = qt.QFileDialog.getExistingDirectory(None, 'Select Folder', './')
        if selectedFolder:
            targetLineEdit.setText(selectedFolder)

        # Check if all folders are set
        if self.folderPathLineEditVolumes.text and self.folderPathLineEditSegmentations.text:
            self.startExperimentButton.setEnabled(True)
        else:
            self.startExperimentButton.setEnabled(False)

#
# SlicerLiverSegmentsLogic
#

class SlicerLiverSegmentsLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    # Define a tuple of valid file extensions
    VALID_EXTENSIONS = ("nii.gz", ".nii", ".dcm", ".nrrd", ".seg.nrrd" )

    def __init__(self) -> None:
        """
        Called when the logic class is instantiated. Can be used for initializing member variables.
        """
        ScriptedLoadableModuleLogic.__init__(self)
        # self.currentDatasetIndex = -1  # Initializing with -1 to denote no dataset loaded
        # self.loadingOrder = []
        # self.volumeFiles = []
        # self.segmentationFiles = []

        self._parameterNode = self.getParameterNode()
        self._currentMethod = 0
        self._currentSequence = 0
        self._currentVolumeFileName = None
        self._currentSegmentsFileName = None
        self._currentDatasetIndex = 0
        self._currentVolumeNode = None
        self._currentSegmentationNode = None

    def initializeExperiment(self) -> bool:

        # Store and check dataset files and consistency
        self._volumeFiles = self.getFilesInDirectory(self._parameterNode.volumesDirectory)
        self._method1Files = self.getFilesInDirectory(self._parameterNode.method1Directory)
        self._method2Files = self.getFilesInDirectory(self._parameterNode.method2Directory)
        self._method3Files = self.getFilesInDirectory(self._parameterNode.method3Directory)
        self._method4Files = self.getFilesInDirectory(self._parameterNode.method4Directory)

        if (len(self._volumeFiles) != len(self._method1Files) or
            len(self._volumeFiles) != len(self._method2Files) or
            len(self._volumeFiles) != len(self._method3Files) or
            len(self._volumeFiles) != len(self._method4Files)):
            return False

        # Update progress values
        self._parameterNode.totalEvaluations = len(self._volumeFiles) * 4
        self._parameterNode.currentEvaluation = 1

        self._resultsTable = self._parameterNode.resultsTableNode.GetTable()
        sequenceNumberColumn = vtk.vtkIntArray()
        sequenceNumberColumn.SetName("Sequence")
        methodColumn = vtk.vtkIntArray()
        methodColumn.SetName("Method")
        volumeFileName = vtk.vtkStringArray()
        volumeFileName.SetName("Volume File")
        segmentsFileName = vtk.vtkStringArray()
        segmentsFileName.SetName("Segmentation File")
        q1ScoringColumn = vtk.vtkIntArray()
        q1ScoringColumn.SetName("Q1 Scoring")
        q2ScoringColumn = vtk.vtkIntArray()
        q2ScoringColumn.SetName("Q2 Scoring")
        q3ScoringColumn = vtk.vtkIntArray()
        q3ScoringColumn.SetName("Q3 Scoring")
        q4ScoringColumn = vtk.vtkIntArray()
        q4ScoringColumn.SetName("Q4 Scoring")

        self._resultsTable.AddColumn(sequenceNumberColumn)
        self._resultsTable.AddColumn(methodColumn)
        self._resultsTable.AddColumn(volumeFileName)
        self._resultsTable.AddColumn(segmentsFileName)
        self._resultsTable.AddColumn(q1ScoringColumn)
        self._resultsTable.AddColumn(q2ScoringColumn)
        self._resultsTable.AddColumn(q3ScoringColumn)
        self._resultsTable.AddColumn(q4ScoringColumn)

        numRows = len(self._volumeFiles) * 4 # Files x methods
        self._resultsTable.SetNumberOfRows(numRows)

        # Initialize table data (-1 for integers, "N/A" for strings)
        for colIndex in range(self._resultsTable.GetNumberOfColumns()):
            column = self._resultsTable.GetColumn(colIndex)
            columnType = column.GetDataType()
            if columnType in [vtk.VTK_INT, vtk.VTK_UNSIGNED_INT, vtk.VTK_LONG, vtk.VTK_UNSIGNED_LONG, vtk.VTK_SHORT, vtk.VTK_UNSIGNED_SHORT, vtk.VTK_CHAR, vtk.VTK_UNSIGNED_CHAR]:
                # Integer types
                for rowIndex in range(numRows):
                    column.SetValue(rowIndex, -1)
            elif columnType == vtk.VTK_STRING:
                # String type
                for rowIndex in range(numRows):
                    column.SetValue(rowIndex, "N/A")

        return True

    def getParameterNode(self):
        return SlicerLiverSegmentsParameterNode(super().getParameterNode())

    def canExperimentStart(self) -> bool:
        """
        Returns whether the conditions are met to start the experiment
        """

        properties = [name for name,value in inspect.getmembers(self._parameterNode.__class__) if isinstance(value,property)]

        for prop_name in properties:
            prop_value = getattr(self._parameterNode, prop_name)
            if prop_value is None or prop_value == "":
                return False
        return True

    def getFilesInDirectory(self, dirPath: str) -> list:
        """
        Returns a list of all files in the given directory filtered by valid extensions.
        """
        if not os.path.exists(dirPath):
            print(f"Directory {dirPath} does not exist!")
            return []

        # List all files in the directory, filter out any subdirectories,
        # filter by extension, and then sort them
        return sorted([f for f in os.listdir(dirPath)
                       if os.path.isfile(os.path.join(dirPath, f))
                       and f.endswith(self.VALID_EXTENSIONS)])

    def loadDataset(self, index) -> None:
        if index < 0 or index >= len(self._loadingOrder):
            print(f"Index {index} is out of range!")
            return

        try:
            # Change cursor to busy indicator
            qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)

            method_idx, sequence_idx = self._loadingOrder[index]

            # Load the volume
            volume_filename = self._volumeFiles[sequence_idx]
            volume_path = os.path.join(self._parameterNode.volumesDirectory, volume_filename)
            self._currentVolumeNode = slicer.util.loadVolume(volume_path)
            if not self._currentVolumeNode:
                print(f"Failed to load volume from {volume_path}")

            # Load the segmentation
            segmentationDirectories = [
                self._parameterNode.method1Directory,
                self._parameterNode.method2Directory,
                self._parameterNode.method3Directory,
                self._parameterNode.method4Directory,
            ]
            segmentationFiles = [
                self._method1Files,
                self._method2Files,
                self._method3Files,
                self._method4Files,
            ]
            segmentation_filename = segmentationFiles[method_idx][sequence_idx]
            segmentation_path = os.path.join(segmentationDirectories[method_idx], segmentation_filename)
            self._currentSegmentationNode = slicer.util.loadSegmentation(segmentation_path)
            if not self._currentSegmentationNode:
                print(f"Failed to load segmentation from {segmentation_path}")
            else:
                self._currentSegmentationNode.CreateClosedSurfaceRepresentation()

            # Load existing data if available
            self.loadDataFromTable()

        finally:
            # Restore the cursor
            qt.QApplication.restoreOverrideCursor()

            # Reset the 3D view to center on the loaded data
            layoutManager = slicer.app.layoutManager()
            threeDView = layoutManager.threeDWidget(0).threeDView()
            threeDView.resetFocalPoint()
            threeDView.renderWindow().Render()


    def startExperiment(self) -> None:
        """
        Called once the datasets are verified, to start the experiment
        """
        # Set the random seed from the parameter node
        random_seed = int(self._parameterNode.orderSeed)
        random.seed(random_seed)

        # Prepare methods and sequences
        methods = list(range(0, 4))  # Methods from 0 to 3
        sequences = list(range(0, len(self._volumeFiles)))  # Sequence indices
        random.shuffle(sequences)

        # Create the loading order and shuffle it
        self._loadingOrder = list(itertools.product(methods, sequences))
        random.shuffle(self._loadingOrder)

        # Load the first dataset
        self.loadDataset(self._currentDatasetIndex)


    def isLastDataset(self) -> bool:
        return self._currentDatasetIndex == len(self._loadingOrder) - 1


    def isNextLastDataset(self) -> bool:
        """
        Returns whether the next dataset will be the last one
        """
        if self._currentDatasetIndex + 1 == len(self._loadingOrder):
            return True
        else:
            return False

    def isPreviousFirstDataset(self) -> bool:
        """
        Returns whether the previous dataset was the first one
        """
        if self._currentDatasetIndex == 0:
            return True
        else:
            return False

    def cleanScene(self) -> None:

        slicer.mrmlScene.RemoveNode(self._currentVolumeNode)
        slicer.mrmlScene.RemoveNode(self._currentSegmentationNode)


    def firstDataset(self) -> None:
        self.cleanScene()
        self._currentDatasetIndex = 0
        self._parameterNode.currentEvaluation = 1
        self.loadDataset(self._currentDatasetIndex)

    def lastDataset(self) -> None:
        self.cleanScene()
        self._currentDatasetIndex = len(self._loadingOrder) - 1
        self._parameterNode.currentEvaluation = self._parameterNode.totalEvaluations
        self.loadDataset(self._currentDatasetIndex)

    def nextDataset(self) -> None:
        if self._currentDatasetIndex + 1 < len(self._loadingOrder):
            self._currentDatasetIndex += 1
            self._parameterNode.currentEvaluation += 1
            # Clear the scene
            self.cleanScene()
            # Load the next dataset
            self.loadDataset(self._currentDatasetIndex)
        else:
            print("No more datasets to load.")


    def previousDataset(self) -> None:
        if self._currentDatasetIndex > 0:
            self._currentDatasetIndex -= 1
            self._parameterNode.currentEvaluation -= 1
            # Clear the scene
            self.cleanScene()
            # Load the previous dataset
            self.loadDataset(self._currentDatasetIndex)
        else:
            print("This is the first dataset.")


    def saveCurrentDataToTable(self) -> None:
        currentRowIndex = self._currentDatasetIndex
        method_idx, sequence_idx = self._loadingOrder[self._currentDatasetIndex]

        # Get data to save
        sequenceNumber = sequence_idx
        methodNumber = method_idx
        volumeFileName = self._volumeFiles[sequence_idx]
        segmentationDirectories = [
            self._parameterNode.method1Directory,
            self._parameterNode.method2Directory,
            self._parameterNode.method3Directory,
            self._parameterNode.method4Directory,
        ]
        segmentationFiles = [
            self._method1Files,
            self._method2Files,
            self._method3Files,
            self._method4Files,
        ]
        segmentationFileName = segmentationFiles[method_idx][sequence_idx]

        q1Score = self._parameterNode.question1Score
        q2Score = self._parameterNode.question2Score
        q3Score = self._parameterNode.question3Score
        q4Score = self._parameterNode.question4Score

        # Save values to the table
        self._resultsTable.GetColumnByName("Sequence").SetValue(currentRowIndex, sequenceNumber)
        self._resultsTable.GetColumnByName("Method").SetValue(currentRowIndex, methodNumber)
        self._resultsTable.GetColumnByName("Volume File").SetValue(currentRowIndex, volumeFileName)
        self._resultsTable.GetColumnByName("Segmentation File").SetValue(currentRowIndex, segmentationFileName)
        self._resultsTable.GetColumnByName("Q1 Scoring").SetValue(currentRowIndex, q1Score)
        self._resultsTable.GetColumnByName("Q2 Scoring").SetValue(currentRowIndex, q2Score)
        self._resultsTable.GetColumnByName("Q3 Scoring").SetValue(currentRowIndex, q3Score)
        self._resultsTable.GetColumnByName("Q4 Scoring").SetValue(currentRowIndex, q4Score)

        self._resultsTable.Modified()

        # Save the table to the CSV file
        fileName = self._parameterNode.outputFileName
        slicer.util.saveNode(self._parameterNode.resultsTableNode, fileName)

    def loadDataFromTable(self):
        currentRowIndex = self._currentDatasetIndex

        def safeInt(value):
            try:
                return int(value)
            except ValueError:
                return -1

        q1Score = safeInt(self._resultsTable.GetColumnByName("Q1 Scoring").GetValue(currentRowIndex))
        q2Score = safeInt(self._resultsTable.GetColumnByName("Q2 Scoring").GetValue(currentRowIndex))
        q3Score = safeInt(self._resultsTable.GetColumnByName("Q3 Scoring").GetValue(currentRowIndex))
        q4Score = safeInt(self._resultsTable.GetColumnByName("Q4 Scoring").GetValue(currentRowIndex))

        if q1Score == -1:
            # No data saved previously
            # Set default scores in parameter node
            self._parameterNode.question1Score = 1
            self._parameterNode.question2Score = 1
            self._parameterNode.question3Score = 1
            self._parameterNode.question4Score = 1
        else:
            # Data was saved, update parameter node
            self._parameterNode.question1Score = q1Score
            self._parameterNode.question2Score = q2Score
            self._parameterNode.question3Score = q3Score
            self._parameterNode.question4Score = q4Score

#
# SlicerLiverSegmentsTest
#

class SlicerLiverSegmentsTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_SlicerLiverSegments1()

    def test_SlicerLiverSegments1(self):
        """ Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # Get/create input data

        import SampleData
        registerSampleData()
        inputVolume = SampleData.downloadSample('SlicerLiverSegments1')
        self.delayDisplay('Loaded test data set')

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = SlicerLiverSegmentsLogic()

        # Test algorithm with non-inverted threshold
        logic.process(inputVolume, outputVolume, threshold, True)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], threshold)

        # Test algorithm with inverted threshold
        logic.process(inputVolume, outputVolume, threshold, False)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay('Test passed')
