cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(SlicerLiverSegmentsCompare)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://www.slicer.org/wiki/Documentation/Nightly/Extensions/SlicerLiverSegmentsCompare")
set(EXTENSION_CATEGORY "Evaluation")
set(EXTENSION_CONTRIBUTORS "Rafael Palomar (Oslo University Hospital)")
set(EXTENSION_DESCRIPTION "This extension helps doing subjective evaluation of liver segments classification")
set(EXTENSION_ICONURL "https://www.example.com/Slicer/Extensions/SlicerLiverSegmentsCompare.png")
set(EXTENSION_SCREENSHOTURLS "https://www.example.com/Slicer/Extensions/SlicerLiverSegmentsCompare/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(SlicerLiverSegments)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
