#!/usr/bin/python
#-*- coding: utf-8 -*-

# =========================================================================
#   Program:   iota2
#
#   Copyright (c) CESBIO. All rights reserved.
#
#   See LICENSE for details.
#
#   This software is distributed WITHOUT ANY WARRANTY; without even
#   the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the above copyright notices for more information.
#
# =========================================================================

import argparse
import fileUtils as fu
import serviceConfigFile as SCF
import otbApplication as otb
import os
import join_sqlites as jsq
import shutil
import string
import glob

def GetAvailableFeatures(inputSampleFileName, numberOfMetaDataFields, firstLevel = 'sensor', secondLevel = 'band'):
    """Assumes that the features are named following a pattern like
    sensor_date_band : S2_b1_20170324. Returns a dictionary containing
    the available features in a 3 level data structure (dict of dicts
    of lists). For example, if first level is sensor and second level
    is band:

    {'S2' : { 'b1' : {'20170324', '20170328'}, 
              'ndvi' : {'20170324', '20170328'}, }, 
     'L8' : ...} 

    The number of meta data fields is needed to eliminate the first
    fields in the file.

    """
    featureList = fu.getAllFieldsInShape(inputSampleFileName, 'SQLite')[numberOfMetaDataFields:]
    features = dict()
    for feat in featureList:
        try:
            (sensor, band, date) = string.split(feat, '_')
            fl = sensor
            sl = band
            tl = date
            if firstLevel=='sensor':
                fl = sensor
                if secondLevel=='band':
                    sl = band
                    tl = date
                else:
                    sl = date
                    tl = band
            elif firstLevel=='band':
                fl = band
                if secondLevel=='date':
                    sl = date
                    tl = sensor
                else:
                    sl = sensor
                    tl = date
            elif firstLevel=='date':
                fl = date
                if secondLevel=='band':
                    sl = band
                    tl = sensor
                else:
                    sl = sensor
                    tl = band
            if fl not in features.keys():
                features[fl] = dict()
            if sl not in features[fl].keys():
                features[fl][sl] = list()
            features[fl][sl].append(tl)
        except:
            pass
    return features
            
def BuildFeaturesLists(inputSampleFileName, numberOfMetaDataFields, 
                       reductionMode='global'):
    """Build a list of lists of the features containing the features to be
    used for each reduction.

    'global' reduction mode selects all the features

    'sensor_band' reduction mode selects all the dates for each
    feature of each sensor (we don't mix L8 and S2 ndvi)

    'sensor_date' reduction mode selects all the features for each
    date for each sensor (we don't mix sensors if the have common
    dates)

    'date' reduction mode selects all the features for each date (we
    mix sensors if the have common dates)

    'sensor' reduction mode selects all the features for a particular
    sensor

    'band' all the dates for each band (we mix L8 and S2 ndvi)

    """
    allFeatures = fu.getAllFieldsInShape(inputSampleFileName, 
                                         'SQLite')[numberOfMetaDataFields:]
    fl = list()
    if reductionMode == 'global':
        fl = list(allFeatures)
    elif reductionMode == 'sensor_date':
        fd = GetAvailableFeatures(inputSampleFileName, numberOfMetaDataFields,
                                  'date', 'sensor')
        for date in sorted(fd.keys()):
            tmpfl = list()
            for sensor in sorted(fd[date].keys()):
                tmpfl += ["%s_%s_%s"%(sensor,band,date) for band in fd[date][sensor]]
            fl.append(tmpfl)
    elif reductionMode == 'date':
        fd = GetAvailableFeatures(inputSampleFileName, numberOfMetaDataFields,
                                  'date', 'sensor')
        for date in sorted(fd.keys()):
            tmpfl = list()
            for sensor in sorted(fd[date].keys()):
                tmpfl += ["%s_%s_%s"%(sensor,band,date) for band in fd[date][sensor]]
            fl.append(tmpfl)
    elif reductionMode == 'sensor_band':
        fd = GetAvailableFeatures(inputSampleFileName, numberOfMetaDataFields,
                                  'sensor', 'band')
        for sensor in sorted(fd.keys()):
            for band in sorted(fd[sensor].keys()):
                fl.append(["%s_%s_%s"%(sensor,band,date) for date in fd[sensor][band]])
    elif reductionMode == 'band':
        fd = GetAvailableFeatures(inputSampleFileName, numberOfMetaDataFields,
                                  'band', 'sensor')
        for band in sorted(fd.keys()):
            tmpfl = list()
            for sensor in sorted(fd[band].keys()):
                tmpfl += ["%s_%s_%s"%(sensor,band,date) for date in fd[band][sensor]]
            fl.append(tmpfl)
    elif reductionMode == 'sensor_date':
        fd = GetAvailableFeatures(inputSampleFileName, numberOfMetaDataFields,
                                  'sensor', 'date')
        for sensor in sorted(fd.keys()):
            for date in sorted(fd[sensor].keys()):
                fl.append(["%s_%s_%s"%(sensor,band,date) for band in fd[sensor][date]])
    else:
        raise RuntimeError("Unknown reduction mode")
    if len(fl) == 0:
        raise Exception("Did not find any valid features in "+inputSampleFileName)
    return fl

def ComputeFeatureStatistics(inputSampleFileName, outputStatsFile, featureList):
    """Computes the mean and the standard deviation of a set of features
    of a file of samples. It will be used for the dimensionality
    reduction training and reduction applications.
    """
    CStats = otb.Registry.CreateApplication("ComputeOGRLayersFeaturesStatistics")
    CStats.SetParameterString("inshp", inputSampleFileName)
    CStats.SetParameterString("outstats", outputStatsFile)
    CStats.UpdateParameters()
    CStats.SetParameterStringList("feat", featureList)
    CStats.ExecuteAndWriteOutput()


def TrainDimensionalityReduction(inputSampleFileName, outputModelFileName, 
                                 featureList, targetDimension, statsFile = None):

    DRTrain = otb.Registry.CreateApplication("TrainDimensionalityReduction")
    DRTrain.SetParameterString("io.vd",inputSampleFileName)
    DRTrain.SetParameterStringList("feat",featureList)
    if statsFile is not None:
        DRTrain.SetParameterString("io.stats",statsFile)
    DRTrain.SetParameterString("io.out", outputModelFileName)
    DRTrain.SetParameterString("algorithm","pca")
    DRTrain.SetParameterInt("algorithm.pca.dim", targetDimension)
    DRTrain.ExecuteAndWriteOutput()

def ApplyDimensionalityReduction(inputSampleFileName, reducedOutputFileName,
                                 modelFileName, inputFeatures, 
                                 outputFeatures, inputDimensions,
                                 statsFile = None, 
                                 pcaDimension = None, 
                                 writingMode = 'overwrite'):
    DRApply = otb.Registry.CreateApplication("VectorDimensionalityReduction")
    DRApply.SetParameterString("in",inputSampleFileName)
    DRApply.SetParameterString("out", reducedOutputFileName)
    DRApply.SetParameterString("model", modelFileName)
    DRApply.UpdateParameters()
    DRApply.SetParameterStringList("feat",inputFeatures)
    DRApply.SetParameterStringList("featout", outputFeatures)
    DRApply.SetParameterInt("indim", inputDimensions)
    if statsFile is not None:
        DRApply.SetParameterString("instat",statsFile)
    if pcaDimension is not None:
        DRApply.SetParameterInt("pcadim", pcaDimension)
    DRApply.SetParameterString("mode", writingMode)
    DRApply.ExecuteAndWriteOutput()


def JoinReducedSampleFiles(inputFileList, outputSampleFileName, 
                           component_list=None, renaming=None):
    """Join the columns of several sample files assuming that they all
    correspond to the same samples and that they all have the same
    names for the fields to copy (component_list). They are joined
    using the ogc_fid field which is supposed to uniquely identify the
    samples.

    """

    # Copy the first file to merge as de destination
    shutil.copyfile(inputFileList[0], outputSampleFileName) 

    jsq.join_sqlites(outputSampleFileName, inputFileList[1:],
                     'ogc_fid', component_list, 
                     renaming=renaming)
    

def SampleFilePCAReduction(inputSampleFileName, outputSampleFileName, 
                           reductionMode, targetDimension,
                           numberOfMetaDataFields, tmpDir = '/tmp', 
                           removeTmpFiles = 'True'):
    """usage : Apply a PCA reduction 

    IN:
    inputSampleFileName [string] : path to a vector file containing training samples
    reductionMode [string] : 'date', 'band', 'global' modes of PCA application
    numberOfMetaDataFields [int] : initial attributes like area, land cover type, etc.

    The names of the fields containing the features are supposed to follow the pattern

    sensor_band_date

    OUT:
    outputSampleFileName [string] : name of the resulting reduced sample file

    """

    featureList = BuildFeaturesLists(inputSampleFileName, 
                                     numberOfMetaDataFields, reductionMode)

    reduced_features = ['value_'+str(pc_number) 
                        for pc_number in range(targetDimension)]

    filesToRemove = list()
    reducedFileList = list()
    fl_counter = 0
    inputDimensions = len(fu.getAllFieldsInShape(inputSampleFileName, 
                                             'SQLite')[numberOfMetaDataFields:])
    for fl in featureList:
        statsFile = tmpDir+'/stats_'+str(fl_counter)+'.xml'
        modelFile = tmpDir+'/model_'+str(fl_counter)
        reducedSampleFile = tmpDir+'/reduced_'+str(fl_counter)+'.sqlite'
        filesToRemove.append(statsFile)
        filesToRemove.append(modelFile)
        filesToRemove.append(reducedSampleFile)
        reducedFileList.append(reducedSampleFile)
        fl_counter += 1
        ComputeFeatureStatistics(inputSampleFileName, statsFile, fl)
        TrainDimensionalityReduction(inputSampleFileName, modelFile, fl, 
                                     targetDimension, statsFile)
        ApplyDimensionalityReduction(inputSampleFileName, reducedSampleFile, 
                                     modelFile, fl, reduced_features, 
                                     inputDimensions,
                                     statsFile)
        
    JoinReducedSampleFiles(reducedFileList, outputSampleFileName, 
                           reduced_features, renaming=('value', targetDimension))

    if removeTmpFiles:
        for f in filesToRemove:
            os.remove(f)

def SampleFileDimensionalityReduction(inSampleFile, outSampleFile, configurationFile):        
    """Applies the dimensionality reduction on a file of samples and gets
    the parameters from the configuration file"""
    cfg = SCF.serviceConfigFile(configurationFile)
    targetDimension = cfg.getParam('dimRed', 'targetDimension')
    reductionMode = cfg.getParam('dimRed', 'reductionMode')
    numberOfMetaDataFields = cfg.getParam('dimRed', 'nbMetaDataFields')
    SampleFilePCAReduction(inSampleFile, outSampleFile, reductionMode, 
                           targetDimension, numberOfMetaDataFields)

def SampleDimensionalityReduction(ioFilePair, configurationFile):        
    """Applies the dimensionality reduction to all sample files and gets
    the parameters from the configuration file"""
    (inSampleFile, outSampleFile) = ioFilePair
    SampleFileDimensionalityReduction(inSampleFile, outSampleFile, configurationFile)

def BuildIOSampleFileLists(configFile):
    cfg = SCF.serviceConfigFile(configFile)
    sampleFileDir = cfg.getParam('chain', 'outputPath')+'/learningSamples/'
    result = list()
    for inputSampleFile in glob.glob(sampleFileDir+'/*sqlite'):
        basename = inputSampleFile[:-(len('sqlite')+1)]
        outputSampleFile = basename+'_reduced.sqlite'
        result.append((inputSampleFile, outputSampleFile))
    return result

    
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description=
                                     "Apply dimensionality reduction to a sample file")
    parser.add_argument("-in", dest="inSampleFile", 
                        help="path to the input sample file",
                        default=None, required=True)
    parser.add_argument("-out", dest="outSampleFile", 
                        help="path to the output sample file",
                        default=None, required=True)
    parser.add_argument("-conf",help ="path to the configuration file (mandatory)",
                        dest = "pathConf",required=False)	
    args = parser.parse_args()

    if args.conf :
        SampleFileDimensionalityReduction(args.inSampleFile, args.outSampleFile, 
                                          args.conf)
    else:
        SampleFilePCAReduction(args.inSampleFile, args.outSampleFile, 'date', 
                               6, 5)
        


