from train import *
from joblib import Parallel, delayed
import os
import numpy as np
import argparse
import utils

# log_params = {"h_dim": (7, 9, 2),
# 	"initial_lr": (-5, -3, 10),
# 	"batch_size": (4, 7, 2),
# 	"lambda_l1" : (-6, -4, 2),
# 	"lambda_l2" : (-6, -2, 5)
# }

# lin_params = {
# 	"n_layers": (1,4,1),
# 	"encoder_input_dropout" : (0.3, 0.9, 0.2),
# 	"encoder_layer_dropout" : (0.3, 0.9, 0.2),
# 	"decoder_input_dropout" : (0.3, 0.9, 0.2),
# 	"decoder_layer_dropout" : (0.3, 0.9, 0.2)
# }
log_params = {"h_dim": (8, 8, 2),
	"initial_lr": (-4, -4, 10),
	"batch_size": (5, 5, 2),
	"lambda_l1" : (-5, -5, 2),
	"lambda_l2" : (-4, -4, 5)
}

lin_params = {
	"n_layers": (2,2,1),
	"encoder_input_dropout" : (0.5, 0.5, 0.2),
	"encoder_layer_dropout" : (0.5, 0.5, 0.2),
	"decoder_input_dropout" : (0.5, 0.5, 0.2),
	"decoder_layer_dropout" : (0.5, 0.5, 0.2)
}

def getSaveDir():
	saveDir = '../save/models/model0/'
	while os.path.isdir(saveDir):
		numStart = saveDir.rfind("model")+5
		numEnd = saveDir.rfind("/")
		saveDir = saveDir[:numStart] + str(int(saveDir[numStart:numEnd])+1) + "/"
	os.mkdir(saveDir)
	return saveDir

def getParams(args, saveDir):
	p = {}
	p["save_dir"] = saveDir
	p["model"] = args.model
	for key, vals in log_params.items():
		possib = np.logspace(vals[0], vals[1], base=vals[2], num=vals[1]-vals[0]+1)
		p[key] = np.random.choice(possib)

	for key, vals in lin_params.items():
		possib = np.arange(vals[0], vals[1]+vals[2], vals[2])
		p[key] = np.random.choice(possib)
	return p

def saveExp(params, res, args, gsSaveFile):
	with open(gsSaveFile, "w+") as f:
		f.write("Dataset: {}\tModel: {}\n".format(args.dataset, args.model))
		col = "Save Directory\tTrain Loss\tValidation Loss"
		sortedKeys = sorted(params.keys())
		for k in sortedKeys:
			if k not in ["model", "save_dir"]:
				col += "\t{}".format(k)
		col += "\n"
		f.write(col)
		row = "{}\t{:.3f}\t{:.3f}".format(res[4], res[0], res[2])
		for k in sortedKeys:
			if k not in ["model", "save_dir"]:
				v = params[k]
				row+="\t{}".format(v)
		row += "\n"
		f.write(row)

def runExperiment(args, saveDir, gsSaveDir, trialNum):
	gsSaveFile = gsSaveDir+"/trials/trial_{}.txt".format(trialNum)
	p = getParams(args, saveDir)
	res = trainF(suggestions=p)
	saveExp(p, res, args, gsSaveFile)
	return p, res

def getGSSaveDir():
	saveDir = '../save/gridSearch/gridSearch_1'
	if not os.path.isdir("../save/"):
		os.mkdir("../save/")
	if not os.path.isdir("../save/gridSearch/"):
		os.mkdir("../save/gridSearch/")
	while os.path.isdir(saveDir):
		numStart = saveDir.rfind("_")+1
		saveDir = saveDir[:numStart] + str(int(saveDir[numStart:])+1)
	os.mkdir(saveDir)
	os.mkdir(saveDir+"/trials")
	return saveDir

def loadData(args):
	print("loading data")
	if args.dataset == "traffic":
		dataDir = "/home/dan/data/traffic/trafficWithTime/"
		data = utils.load_traffic_dataset(
			dataDir,
			args.batch_size,
			down_sample=args.down_sample,
			load_test=args.predictOnTest,
			genLoaders=False)
	elif args.dataset == "human":
		dataDir = "/home/dan/data/human/Processed/"
		data = utils.load_human_dataset(
			dataDir,
			args.batch_size,
			down_sample=args.down_sample,
			load_test=args.predictOnTest,
			genLoaders=False)
	return data

def main():
	args = parser.parse_args()
	# data = loadData(args)
	tries = args.tries
	saveDirs = [getSaveDir() for i in range(tries)]
	gsSaveDir = getGSSaveDir()
	# results = []
	results = Parallel(n_jobs=4)(delayed(runExperiment)(args, saveDirs[i], gsSaveDir, i) for i in range(tries))
	# for i in range(tries):
	# 	results.append(runExperiment(args, saveDirs[i], data))
	# trainReconLosses, trainKLDLosses, valReconLosses, valKLDLosses, args.save_dir
	results = sorted(results, key=lambda x: x[1][2])
	saveFile = gsSaveDir+"/gridsearch.txt"
	if args.model == "rnn":
		with open(saveFile, "w+") as f:
			f.write("Dataset: {}\tModel: {}\n".format(args.dataset, args.model))
			col = "Save Directory\tTrain Loss\tValidation Loss"
			sortedKeys = sorted(results[0][0].keys())
			for k in sortedKeys:
				if k not in ["model", "save_dir"]:
					col += "\t{}".format(k)
			col += "\n"
			f.write(col)
			for res in results:
				tup = res[1]
				row = "{}\t{:.3f}\t{:.3f}".format(tup[4], tup[0], tup[2])
				for k in sortedKeys:
					if k not in ["model", "save_dir"]:
						v = res[0][k]
						row+="\t{}".format(v)
				row += "\n"
				f.write(row)
	elif args.model == "vrnn" or args.model=="sketch-rnn":
		with open(saveFile, "w+") as f:
			f.write("Dataset: {}, Model: {}".format(args.dataset, args.model))
			f.write("Save Directory\t\tTrain Recon Loss\tTrain KLD Loss\tValidation Recon Loss\tValidation KLD Loss\n")
			for res in results:
				tup = res[1]
				f.write("{}\t\t{:.3f}\t\t{:.3f}\t\t{:.3f}\t\t\t{:.3f}\n".format(tup[4], tup[0],tup[1],tup[2], tup[3]))
	else:
		assert False, "bad model"



if __name__ == '__main__':
	main()
