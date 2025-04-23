import logging
import inspect
import os
import re
import random
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
    currentMethod: int

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

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)
        self._parameterNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.enableStartExperimentButtonIfPossible)


    def startExperiment(self) -> None:

        if self.logic.initializeExperiment():
            self.ui.startExperimentPushButton.setEnabled(False)
            self.ui.directoriesGroupBox.setEnabled(False)
            self.ui.parametersGroupBox.setEnabled(False)
            self.ui.q1GroupBox.setEnabled(True)
            self.ui.q2GroupBox.setEnabled(True)
            self.ui.q3GroupBox.setEnabled(True)
            self.ui.q4GroupBox.setEnabled(True)
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

    def onPrevButton(self) -> None:
        """
        Called upon Previous button is pressed.
        """
        self.logic.previousDataset()

        # Check if the currentDatasetIndex is at the start to disable the "Previous" button
        if self.logic.currentDatasetIndex == 0:
            self.prevButton.setEnabled(False)

        # Ensure the "Next" button is enabled (in case it was disabled after reaching the end)
        self.nextButton.setEnabled(True)

    def onNextButton(self) -> None:
        """
        Called upon Next button is pressed.
        """
        self.logic.nextDataset()

        # Check if the currentDatasetIndex is at the end to disable the "Next" button
        if self.logic.currentDatasetIndex == len(self.logic.loadingOrder) - 1:
            self.nextButton.setEnabled(False)

        # Ensure the "Previous" button is enabled (in case it was disabled after reaching the start)
        self.prevButton.setEnabled(True)

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
    # RANDOM_SEED= 10

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

        self._resultsTable = self._parameterNode.resultsTableNode.GetTable()
        sequenceNumberColumn = vtk.vtkIntArray()
        sequenceNumberColumn.SetName("Sequence")
        methodColumn = vtk.vtkIntArray()
        methodColumn.SetName("Method")
        q1ScoringColumn = vtk.vtkIntArray()
        methodColumn.SetName("Q1 Scoring")
        q2ScoringColumn = vtk.vtkIntArray()
        methodColumn.SetName("Q2 Scoring")
        q3ScoringColumn = vtk.vtkIntArray()
        methodColumn.SetName("Q3 Scoring")
        q4ScoringColumn = vtk.vtkIntArray()
        methodColumn.SetName("Q4 Scoring")

        self._resultsTable.AddColumn(sequenceNumberColumn)
        self._resultsTable.AddColumn(methodColumn)
        self._resultsTable.AddColumn(q1ScoringColumn)
        self._resultsTable.AddColumn(q2ScoringColumn)
        self._resultsTable.AddColumn(q3ScoringColumn)
        self._resultsTable.AddColumn(q4ScoringColumn)

        numRows = len(self._volumeFiles) * 4 # Files x methods
        self._resultsTable.SetNumberOfRows(numRows)

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

        # List all files in the directory, filter out any subdirectories, and filter by extension
        return [f for f in os.listdir(dirPath) if os.path.isfile(os.path.join(dirPath, f)) and f.endswith(self.VALID_EXTENSIONS)]

    def generateRandomLoadingOrder(self, numberOfFiles: int, seed: int = None) -> list:
        """
        Generate a vector of random numbers representing the loading order for files.

        :param numberOfFiles: Number of files for which to generate the loading order.
        :param seed: Optional seed for random number generation.
        """
        if seed is not None:
            random.seed(seed)

        return random.sample(range(numberOfFiles), numberOfFiles)

    def loadDataset(self, index: int) -> None:
        """
        Load a dataset (volume and segmentation) into the scene based on the given index.
        """
        if index < 0 or index >= len(self.loadingOrder):
            print(f"Index {index} is out of range!")
            return

        # Load the volume
        volumePath = os.path.join(self.volumesDirPath, self.volumeFiles[self.loadingOrder[index]])
        if not slicer.util.loadVolume(volumePath):
            print(f"Failed to load volume from {volumePath}")

        # Load the segmentation
        segmentationPath = os.path.join(self.segmentationsDirPath, self.segmentationFiles[self.loadingOrder[index]])
        segmentationNode = slicer.util.loadSegmentation(segmentationPath)
        if not segmentationNode:
            print(f"Failed to load segmentation from {segmentationPath}")
        else:
            segmentation = segmentationNode.GetSegmentation()

            # Convert the entire segmentation to have a closed surface representation
            segmentationNode.CreateClosedSurfaceRepresentation()

    def startExperiment(self,volumesDirPath, segmentationsDirPath) -> bool:
        """
        Called once the datasets are verified, in order to start the experiment
        """

        # Store the directory paths as attributes
        self.volumesDirPath = volumesDirPath
        self.segmentationsDirPath = segmentationsDirPath


        # 1. Get the list of files in volumes
        volumeFiles = self.getVolumeFiles(volumesDirPath)

        # 2. Get the list of files in segmentations
        segmentationFiles = self.getSegmentationFiles(segmentationsDirPath)

        if len(volumeFiles) != len(segmentationFiles):
            print("Volumes and segmentations directories do not have the same number of files!")
            return False

        # Keep track of the files and order for future use
        self.volumeFiles = volumeFiles
        self.segmentationFiles = segmentationFiles
        self.loadingOrder = self.generateRandomLoadingOrder(len(volumeFiles), self.RANDOM_SEED)

        self.resetExperiment()

        print("Volume Files:", volumeFiles)
        print("Segmentation Files:", segmentationFiles)
        print("Loading Order:", self.loadingOrder)

        # Clear the scene
        slicer.mrmlScene.Clear()

        # Load the first dataset
        self.loadDataset(self.currentDatasetIndex)

        return True

    def nextDataset(self) -> None:
        """
        Load the next dataset in the sequence into the scene.
        """
        self.currentDatasetIndex += 1
        if self.currentDatasetIndex >= len(self.loadingOrder):
            # Handle end of dataset list (maybe loop back to start or just stay on the last dataset)
            self.currentDatasetIndex = len(self.loadingOrder) - 1
            return

        # Clear the scene
        slicer.mrmlScene.Clear()

        # Load the next dataset
        self.loadDataset(self.currentDatasetIndex)

    def previousDataset(self) -> None:
        """
        Load the previous dataset in the sequence into the scene.
        """
        self.currentDatasetIndex -= 1
        if self.currentDatasetIndex < 0:
            # Handle start of dataset list (maybe loop back to end or just stay on the first dataset)
            self.currentDatasetIndex = 0
            return

        # Clear the scene
        slicer.mrmlScene.Clear()

        # Load the previous dataset
        self.loadDataset(self.currentDatasetIndex)

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
