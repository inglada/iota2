#!/usr/bin/python
#-*- coding: utf-8 -*-

import argparse,os
import getModel as GM

def generateStatModel(pathShapes,pathToTiles,pathToStats,pathToCmdStats):

	AllCmd = []
	modTiles = GM.getModel(pathShapes)
	
	for mod, Tiles in modTiles:
		allpath = ""
		for tile in Tiles:
			contenu = os.listdir(pathToTiles+"/"+tile+"/Final")
			pathToFeat = pathToTiles+"/"+tile+"/Final/"+str(max(contenu))

			allpath = allpath+" "+pathToFeat+" "
		cmd = "otbcli_ComputeImagesStatistics -il "+allpath+"-out "+pathToStats+"/Model_"+str(mod)+".xml"
		AllCmd.append(cmd)
	

	#écriture du fichier de cmd
	cmdFile = open(pathToCmdStats+"/stats.txt","w")
	for i in range(len(AllCmd)):
		if i == 0:
			cmdFile.write("%s"%(AllCmd[i]))
		else:
			cmdFile.write("\n%s"%(AllCmd[i]))
	cmdFile.close()
	return AllCmd

#############################################################################################################################

if __name__ == "__main__":
	
	parser = argparse.ArgumentParser(description = "This function compute the statistics for a model compose by N tiles")

	parser.add_argument("-shapesIn",help ="path to the folder which ONLY contains shapes for the classification (learning and validation) (mandatory)",dest = "pathShapes",required=True)
	parser.add_argument("-tiles.path",dest = "pathToTiles",help ="path where tiles are stored (mandatory)",required=True)
	parser.add_argument("-Stats.out",dest = "pathToStats",help ="path where all statistics will be stored (mandatory)",required=True)
	parser.add_argument("-Stat.out.cmd",dest = "pathToCmdStats",help ="path where all statistics cmd will be stored in a text file(mandatory)",required=True)
	
	generateStatModel(args.pathShapes,args.pathToTiles,args.pathToStats,args.pathToCmdStats)






































