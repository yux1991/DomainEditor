# HighDimEditor
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/yux1991/HighDimEditor/graphs/commit-activity) [![GitHub license](https://img.shields.io/github/license/yux1991/HighDimEditor.svg)](https://github.com/yux1991/PyRHEED/blob/master/LICENSE)[![Ask Me Anything !](https://img.shields.io/badge/Ask%20me-anything-1abc9c.svg)](mailto:yux1991@gmail.com)

## Table of Content
1. [Description](README.md#Description)
2. [Requirements](README.md#Requirements)
3. [Modules](README.md#Structure)
4. [Contact](README.md#Contact)

## Description
This project is used for editing the images in the curvelet domain. It allows visualization of the curvelet structure and applying threshold denoise for each wedge in the curvelet domain.

## Requirements
- matplotlib 3.3.1
- numpy 1.19.2
- pillow 7.2.0
- pyct 1.0
- pyqt5 5.15.1
- pyqtchart 5.15.1
- pyqtdatavisualization 5.15.1
- rawpy 0.15.0
- scipy 1.5.2
    
## Modules 
- browser: browse files inside the working directory
- canvas: display original image, processed image and their difference
- digital_tile: configure the number of scales and number of azimuth in digital tiling of the curvelet space
- dynamic_viewer: interactive visualization of the selected wedges in the curvelet domain
- main: the main module
- process: the backend processes

## Contact
Please contact Yu Xiang at [yux1991@gmail.com](mailto:yux1991@gmail.com) if you have any questions or suggestions.
