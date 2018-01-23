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

import argparse,os,shutil
import fileUtils as fu
from config import Config
from Utils import run

def genJobArray(jobArrayPath,nbCmd,pathConf,cmdPathMerge):
    jobFile = open(jobArrayPath,"w")
    if nbCmd>1:
        jobFile.write('#!/bin/bash\n\
#PBS -N MergeSamples\n\
#PBS -J 0-%d:1\n\
#PBS -l select=ncpus=5:mem=40000mb\n\
#PBS -l walltime=20:00:00\n\
\n\
module load python/2.7.12\n\
module load gcc/6.3.0\n\
\n\
FileConfig=%s\n\
PYPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=pyAppPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "^((?!#).)*(?<=OTB_HOME\:).*" $FileConfig | cut -d "\'" -f 2)\n\
. $OTB_HOME/config_otb.sh\n\
TESTPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=outputPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
\n\
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=5\n\
cd $PYPATH\n\
echo $PYPATH\n\
j=0\n\
old_IFS=$IFS\n\
IFS=$\'%s\'\n\
for ligne in $(cat %s)\n\
do\n\
	cmd[$j]=$ligne\n\
	j=$j+1\n\
done\n\
IFS=$old_IFS\n\
\n\
echo ${cmd[${PBS_ARRAY_INDEX}]}\n\
#until eval ${cmd[${PBS_ARRAY_INDEX}]}; do echo $?; done\n\
eval ${cmd[${PBS_ARRAY_INDEX}]}\n\
'%(nbCmd-1,pathConf,'\\n',cmdPathMerge))
        jobFile.close()
    else:
        jobFile.write('#!/bin/bash\n\
#PBS -N MergeSamples\n\
#PBS -l select=ncpus=5:mem=40000mb\n\
#PBS -l walltime=20:00:00\n\
\n\
module load python/2.7.12\n\
module load gcc/6.3.0\n\
\n\
FileConfig=%s\n\
PYPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=pyAppPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
export ITK_AUTOLOAD_PATH=""\n\
export OTB_HOME=$(grep --only-matching --perl-regex "^((?!#).)*(?<=OTB_HOME\:).*" $FileConfig | cut -d "\'" -f 2)\n\
. $OTB_HOME/config_otb.sh\n\
TESTPATH=$(grep --only-matching --perl-regex "^((?!#).)*(?<=outputPath\:).*" $FileConfig | cut -d "\'" -f 2)\n\
\n\
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=5\n\
cd $PYPATH\n\
echo $PYPATH\n\
j=0\n\
old_IFS=$IFS\n\
IFS=$\'%s\'\n\
for ligne in $(cat %s)\n\
do\n\
	cmd[$j]=$ligne\n\
	j=$j+1\n\
done\n\
IFS=$old_IFS\n\
\n\
echo ${cmd[0]}\n\
#until eval ${cmd[${PBS_ARRAY_INDEX}]}; do echo $?; done\n\
eval ${cmd[0]}\n\
'%(pathConf,'\\n',cmdPathMerge))
        jobFile.close()  



def getAllModelsFromShape(PathLearningSamples):

    AllSample = fu.fileSearchRegEx(PathLearningSamples+"/*.sqlite")
    #region position when files in /learingSamples are splite by '_'
    region_pos = 2
    AllModels = []
    for currentSample in AllSample:
        try:
            model = currentSample.split("/")[-1].split("_")[region_pos]
            ind = AllModels.index(model)
        except ValueError:
            AllModels.append(model)
    return AllModels

def vectorSamplesMerge(cfg):
    
    outputPath = cfg.getParam('chain', 'outputPath')
    runs = cfg.getParam('chain', 'runs')
    mode = cfg.getParam('chain', 'executionMode')
    jobArrayPath = cfg.getParam('chain', 'jobsPath') + "/SamplesMerge.pbs"
    logPath = cfg.getParam('chain', 'logPath') 
    cmdPathMerge = outputPath+"/cmd/mergeSamplesCmd.txt"
    if os.path.exists(jobArrayPath):
        os.remove(jobArrayPath)

    AllModels = getAllModelsFromShape(outputPath+"/learningSamples")
    allCmd = []
    for seed in range(runs):
        for currentModel in AllModels:
            learningShapes = fu.fileSearchRegEx(outputPath+"/learningSamples/*_region_"+currentModel+"_seed"+str(seed)+"*Samples.sqlite")
            shapeOut = "Samples_region_"+currentModel+"_seed"+str(seed)+"_learn"
            folderOut = outputPath+"/learningSamples"
            if mode == "sequential":
                fu.mergeSQLite(shapeOut, folderOut,learningShapes)
            elif mode == "parallel": 
                allCmd.append("python -c 'import fileUtils;fileUtils.mergeSQLite_cmd(\""+shapeOut+"\",\""+folderOut+"\",\""+"\",\"".join(learningShapes)+"\")'")
            for currentShape in learningShapes:
                if mode == "sequential":
                    os.remove(currentShape)
    if mode == "parallel":
        fu.writeCmds(cmdPathMerge,allCmd,mode="w")
        genJobArray(jobArrayPath, len(allCmd), cfg.pathConf, cmdPathMerge)
        run("qsub -W block=true "+jobArrayPath)

if __name__ == "__main__":

    import serviceConfigFile as SCF
    parser = argparse.ArgumentParser(description = "This function merge sqlite to feed training")	
    parser.add_argument("-conf",help ="path to the configuration file (mandatory)",dest = "pathConf",required=True)	
    args = parser.parse_args()

    # load configuration file
    cfg = SCF.serviceConfigFile(args.pathConf)

    vectorSamplesMerge(cfg)
