import logging
import os
from typing import Annotated, Optional

import vtk

import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)

from slicer import vtkMRMLScalarVolumeNode

import qt

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
        ScriptedLoadableModuleWidget.setup(self)

        # Create the Setup GroupBox
        setupGroupBox = qt.QGroupBox("Setup")
        setupGroupBoxLayout = qt.QVBoxLayout()

        # Volumes folder selection
        folderVolumesHBoxLayout = qt.QHBoxLayout()
        self.selectFolderButtonVolumes = qt.QPushButton("Select Volumes Folder")
        self.folderPathLineEditVolumes = qt.QLineEdit()
        folderVolumesHBoxLayout.addWidget(self.selectFolderButtonVolumes)
        folderVolumesHBoxLayout.addWidget(self.folderPathLineEditVolumes)
        setupGroupBoxLayout.addLayout(folderVolumesHBoxLayout)

        # Segmentations folder selection
        folderSegmentationsHBoxLayout = qt.QHBoxLayout()
        self.selectFolderButtonSegmentations = qt.QPushButton("Select Segmentations Folder")
        self.folderPathLineEditSegmentations = qt.QLineEdit()
        folderSegmentationsHBoxLayout.addWidget(self.selectFolderButtonSegmentations)
        folderSegmentationsHBoxLayout.addWidget(self.folderPathLineEditSegmentations)
        setupGroupBoxLayout.addLayout(folderSegmentationsHBoxLayout)

        # Start Experiment Button
        self.startExperimentButton = qt.QPushButton("Start Experiment")
        self.startExperimentButton.setEnabled(False)  # Initially disabled
        setupGroupBoxLayout.addWidget(self.startExperimentButton)

        setupGroupBox.setLayout(setupGroupBoxLayout)
        self.layout.addWidget(setupGroupBox)
        self.layout.addItem(qt.QSpacerItem(0, 0, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding))

        # Connections (qt.Qt)
        self.selectFolderButtonVolumes.clicked.connect(lambda: self.selectFolder(self.folderPathLineEditVolumes))
        self.selectFolderButtonSegmentations.clicked.connect(lambda: self.selectFolder(self.folderPathLineEditSegmentations))
        self.startExperimentButton.clicked.connect(self.onStartExperimentButton)

        # Connections (VTK)

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = SlicerLiverSegmentsLogic()

    def cleanup(self) -> None:
        """
        Called when the application closes and the module widget is destroyed.
        """
        self.removeObservers()

    def enter(self) -> None:
        """
        Called each time the user opens this module.
        """
        pass

    def exit(self) -> None:
        """
        Called each time the user opens a different module.
        """
        pass

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
        pass

    def selectFolder(self, targetLineEdit) -> None:
        selectedFolder = qt.QFileDialog.getExistingDirectory(None, 'Select Folder', './')
        if selectedFolder:
            targetLineEdit.setText(selectedFolder)

        # Check if all folders are set
        if self.folderPathLineEditVolumes.text and self.folderPathLineEditSegmentations.text:
            self.startExperimentButton.setEnabled(True)
        else:
            self.startExperimentButton.setEnabled(False)

    # def initializeParameterNode(self) -> None:
    #     """
    #     Ensure parameter node exists and observed.
    #     """
    #     # Parameter node stores all user choices in parameter values, node selections, etc.
    #     # so that when the scene is saved and reloaded, these settings are restored.

    #     self.setParameterNode(self.logic.getParameterNode())

    #     # Select default input nodes if nothing is selected yet to save a few clicks for the user
    #     if not self._parameterNode.inputVolume:
    #         firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
    #         if firstVolumeNode:
    #             self._parameterNode.inputVolume = firstVolumeNode

    # def setParameterNode(self, inputParameterNode: Optional[SlicerLiverSegmentsParameterNode]) -> None:
    #     """
    #     Set and observe parameter node.
    #     Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
    #     """

    #     if self._parameterNode:
    #         self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
    #         self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
    #     self._parameterNode = inputParameterNode
    #     if self._parameterNode:
    #         # Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each
    #         # ui element that needs connection.
    #         self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
    #         self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
    #         self._checkCanApply()

    # def _checkCanApply(self, caller=None, event=None) -> None:
    #     if self._parameterNode and self._parameterNode.inputVolume and self._parameterNode.thresholdedVolume:
    #         self.ui.applyButton.toolTip = "Compute output volume"
    #         self.ui.applyButton.enabled = True
    #     else:
    #         self.ui.applyButton.toolTip = "Select input and output volume nodes"
    #         self.ui.applyButton.enabled = False

    # def onApplyButton(self) -> None:
    #     """
    #     Run processing when user clicks "Apply" button.
    #     """
    #     with slicer.util.tryWithErrorDisplay("Failed to compute results.", waitCursor=True):

    #         # Compute output
    #         self.logic.process(self.ui.inputSelector.currentNode(), self.ui.outputSelector.currentNode(),
    #                            self.ui.imageThresholdSliderWidget.value, self.ui.invertOutputCheckBox.checked)

    #         # Compute inverted output (if needed)
    #         if self.ui.invertedOutputSelector.currentNode():
    #             # If additional output volume is selected then result with inverted threshold is written there
    #             self.logic.process(self.ui.inputSelector.currentNode(), self.ui.invertedOutputSelector.currentNode(),
    #                                self.ui.imageThresholdSliderWidget.value, not self.ui.invertOutputCheckBox.checked, showResult=False)


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

    def __init__(self) -> None:
        """
        Called when the logic class is instantiated. Can be used for initializing member variables.
        """
        ScriptedLoadableModuleLogic.__init__(self)

    def createAndSetLayout(self) -> None:

        trioMonitorFourUpView = """
        <viewports>

        <layout type="vertical">
        <item>
        <layout type="horizontal">
            <item>
            <view class="vtkMRMLSliceNode" singletontag="Red">
            <property name="orientation" action="default">Axial</property>
            <property name="viewlabel" action="default">R</property>
            <property name="viewcolor" action="default">#F34A33</property>
            </view>
            </item>
            <item>
            <view class="vtkMRMLViewNode" singletontag="1">
            <property name="viewlabel" action="default">1</property>
            </view>
            </item>
        </layout>
        </item>
        <item>
        <layout type="horizontal">
            <item>
            <view class="vtkMRMLSliceNode" singletontag="Green">
            <property name="orientation" action="default">Coronal</property>
            <property name="viewlabel" action="default">G</property>
            <property name="viewcolor" action="default">#6EB04B</property>
            </view>
            </item>
            <item>
            <view class="vtkMRMLSliceNode" singletontag="Yellow">
            <property name="orientation" action="default">Sagittal</property>
            <property name="viewlabel" action="default">Y</property>
            <property name="viewcolor" action="default">#EDD54C</property>
            </view>
            </item>
        </layout>
        </item>
        </layout>

        <layout name="views+" type="vertical" label="Views+" dockable="true" dockPosition="floating">
        <item>
        <layout type="horizontal">
            <item>
            <view class="vtkMRMLSliceNode" singletontag="Red+">
            <property name="orientation" action="default">Axial</property>
            <property name="viewlabel" action="default">R+</property>
            <property name="viewcolor" action="default">#f9a99f</property>
            <property name="viewgroup" action="default">1</property>
            </view>
            </item>
            <item>
            <view class="vtkMRMLViewNode" singletontag="1+" type="secondary">
            <property name="viewlabel" action="default">1+</property>
            <property name="viewgroup" action="default">1</property>
            </view>
            </item>
        </layout>
        </item>
        <item>
        <layout type="horizontal">
            <item>
            <view class="vtkMRMLSliceNode" singletontag="Green+">
            <property name="orientation" action="default">Coronal</property>
            <property name="viewlabel" action="default">G+</property>
            <property name="viewcolor" action="default">#c6e0b8</property>
            <property name="viewgroup" action="default">1</property>
            </view>
            </item>
            <item>
            <view class="vtkMRMLSliceNode" singletontag="Yellow+">
            <property name="orientation" action="default">Sagittal</property>
            <property name="viewlabel" action="default">Y+</property>
            <property name="viewcolor" action="default">#f6e9a2</property>
            <property name="viewgroup" action="default">1</property>
            </view>
            </item>
        </layout>
        </item>
        </layout>

        <layout name="views++" type="vertical" label="Views++" dockable="true" dockPosition="floating">
        <item>
        <layout type="horizontal">
            <item>
            <view class="vtkMRMLSliceNode" singletontag="Red++">
            <property name="orientation" action="default">Axial</property>
            <property name="viewlabel" action="default">R++</property>
            <property name="viewcolor" action="default">#f9a99f</property>
            <property name="viewgroup" action="default">1</property>
            </view>
            </item>
            <item>
            <view class="vtkMRMLViewNode" singletontag="1++" type="secondary">
            <property name="viewlabel" action="default">1++</property>
            <property name="viewgroup" action="default">1</property>
            </view>
            </item>
        </layout>
        </item>
        <item>
        <layout type="horizontal">
            <item>
            <view class="vtkMRMLSliceNode" singletontag="Green++">
            <property name="orientation" action="default">Coronal</property>
            <property name="viewlabel" action="default">G++</property>
            <property name="viewcolor" action="default">#c6e0b8</property>
            <property name="viewgroup" action="default">1</property>
            </view>
            </item>
            <item>
            <view class="vtkMRMLSliceNode" singletontag="Yellow++">
            <property name="orientation" action="default">Sagittal</property>
            <property name="viewlabel" action="default">Y++</property>
            <property name="viewcolor" action="default">#f6e9a2</property>
            <property name="viewgroup" action="default">1</property>
            </view>
            </item>
        </layout>
        </item>
        </layout>

        </viewports>
        """

        # Built-in layout IDs are all below 100, so you can choose any large random number
        # for your custom layout ID.
        customLayoutId=501

        layoutManager = slicer.app.layoutManager()
        layoutManager.layoutLogic().GetLayoutNode().AddLayoutDescription(customLayoutId,trioMonitorFourUpView )

        # Switch to the new custom layout
        layoutManager.setLayout(customLayoutId)


        # This is a snippet of code to access the different 3D Views
        # --extracted from script repository 3D Slicer
        layoutManager = slicer.app.layoutManager()
        for threeDViewIndex in range(layoutManager.threeDViewCount) :
            view = layoutManager.threeDWidget(threeDViewIndex).threeDView()
            threeDViewNode = view.mrmlViewNode()
            cameraNode = slicer.modules.cameras.logic().GetViewActiveCameraNode(threeDViewNode)
            print("View node for 3D widget " + str(threeDViewIndex))
            print("  Name: " + threeDViewNode .GetName())
            print("  ID: " + threeDViewNode .GetID())
            print("  Camera ID: " + cameraNode.GetID())


    def getParameterNode(self):
        return SlicerLiverSegmentsParameterNode(super().getParameterNode())

    def process(self,
                inputVolume: vtkMRMLScalarVolumeNode,
                outputVolume: vtkMRMLScalarVolumeNode,
                imageThreshold: float,
                invert: bool = False,
                showResult: bool = True) -> None:
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        :param outputVolume: thresholding result
        :param imageThreshold: values above/below this threshold will be set to 0
        :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
        :param showResult: show output volume in slice viewers
        """

        if not inputVolume or not outputVolume:
            raise ValueError("Input or output volume is invalid")

        import time
        startTime = time.time()
        logging.info('Processing started')

        # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
        cliParams = {
            'InputVolume': inputVolume.GetID(),
            'OutputVolume': outputVolume.GetID(),
            'ThresholdValue': imageThreshold,
            'ThresholdType': 'Above' if invert else 'Below'
        }
        cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
        # We don't need the CLI module node anymore, remove it to not clutter the scene with it
        slicer.mrmlScene.RemoveNode(cliNode)

        stopTime = time.time()
        logging.info(f'Processing completed in {stopTime-startTime:.2f} seconds')


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
