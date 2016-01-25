"""This demo script is intended to show how this package's data
structures may be used to run the benchmark on the model results
cateloged in Mingquan's ftp site.
"""
from ILAMB.Scoreboard import Scoreboard
from ILAMB.ModelResult import ModelResult
from ILAMB import ilamblib as il
import numpy as np
import os,time,sys
from mpi4py import MPI

np.seterr(all='raise')

# MPI stuff
comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

# Some color constants for printing to the terminal
OK   = '\033[92m'
FAIL = '\033[91m'
ENDC = '\033[0m'

import argparse
parser = argparse.ArgumentParser(description='')
parser.add_argument('--root', dest="root", metavar='root', type=str, nargs=1,
                    help='root at which to search for models')
parser.add_argument('--config', dest="config", metavar='config', type=str, nargs=1,
                    help='path to configuration file to use')
parser.add_argument('--models', dest="models", metavar='m', type=str, nargs='+',
                    help='specify which models to run, list model names with no quotes and only separated by a space.')
parser.add_argument('--confrontations', dest="confront", metavar='c', type=str, nargs='+',
                    help='specify which confrontations to run, list confrontation names with no quotes and only separated by a space.')
parser.add_argument('--regions', dest="regions", metavar='r', type=str, nargs='+',
                    help='specify which regions to compute over')
parser.add_argument('--clean', dest="clean", metavar='c', type=bool, nargs=1, default=False,
                    help='enable to remove analysis files and recompute')
args = parser.parse_args()

if args.regions is None: args.regions = ['global']

# Initialize the models
M    = []
root = args.root[0]
if root[-1] == "/": root = root[:-1]
if rank == 0: print "\nSearching for model results in %s...\n" % root
maxML = 0
for subdir, dirs, files in os.walk(root):
    mname = subdir.replace(root,"")
    if mname.count("/") != 1: continue
    mname = mname.replace("/","")
    if args.models is not None:
        if mname not in args.models: continue
    maxML  = max(maxML,len(mname))
    M.append(ModelResult(subdir,modelname=mname))
M = sorted(M,key=lambda m: m.name.upper())
if rank == 0: 
    for m in M: 
        print ("    {0:<%d}" % (maxML)).format(m.name)
if len(M) == 0: sys.exit(0)

# Assign colors
clrs = il.GenerateDistinctColors(len(M))
for m in M:
    clr     = clrs.pop(0)
    m.color = clr

# Get confrontations
Conf = Scoreboard(args.config[0],regions=args.regions)

# Build work list, ModelResult+Confrontation pairs
W     = []
C     = Conf.list()
if args.confront is not None:
    tmp = []
    for c in C:
        for arg in args.confront:
            if arg in c.longname: tmp.append(c)
    C = tmp
if len(C) == 0: sys.exit(0)

maxCL = 0
for c in C:
    maxCL = max(maxCL,len(c.longname))
    for m in M:
        W.append([m,c])

if rank == 0:
    print "\nSearching for confrontations...\n"
    for c in C: 
        print ("    {0:<%d}" % (maxCL)).format(c.longname)

sys.stdout.flush()
if rank==0: print "\nRunning model-confrontation pairs...\n"
comm.Barrier()

# Divide work list 
wpp    = float(len(W))/size
begin  = int(round( rank   *wpp))
end    = int(round((rank+1)*wpp))
localW = W[begin:end]

# Determine who is the master of each confrontation
for c in C:
    sendbuf = np.zeros(size,dtype='int')
    for w in localW:
        if c is w[1]: sendbuf[rank] += 1
    recvbuf = None
    if rank == 0: recvbuf = np.empty([size, sendbuf.size],dtype='int')
    comm.Gather(sendbuf,recvbuf,root=0)
    if rank == 0: 
        numc = recvbuf.sum(axis=1)
    else:
        numc = np.empty(size,dtype='int')
    comm.Bcast(numc,root=0)
    if rank == numc.argmax():
        c.master = True
    else:
        c.master = False

# find confrontation names for relationships (move this elsewhere)
for c in C:
    if c.relationships is None: continue
    for i,longname in enumerate(c.relationships):
        found = False
        for cor in Conf.list():
            if longname.lower() == cor.longname.lower():
                c.relationships[i] = cor
                found = True

        
# Run analysis on your local work model-confrontation pairs
T0 = time.time()
for w in localW:
    m,c = w
    t0  = time.time()
    if os.path.isfile("%s/%s_%s.nc" % (c.output_path,c.name,m.name)) and args.clean == False:
        print ("    {0:>%d} {1:>%d} %sUsingCachedData%s " % (maxCL,maxML,OK,ENDC)).format(c.longname,m.name)
        continue
    try:
        c.confront(m)  
        dt = time.time()-t0
        print ("    {0:>%d} {1:>%d} %sCompleted%s {2:>5.1f} s" % (maxCL,maxML,OK,ENDC)).format(c.longname,m.name,dt)

    except (il.VarNotInModel,
            il.AreasNotInModel,
            il.VarNotMonthly,
            il.VarNotOnTimeScale,
            il.NotTemporalVariable,
            il.UnitConversionError,
            il.AnalysisError,
            il.VarsNotComparable) as ex:
        print ("    {0:>%d} {1:>%d} %s%s%s" % (maxCL,maxML,FAIL,ex,ENDC)).format(c.longname,m.name)
        continue
            
sys.stdout.flush()
comm.Barrier()

if rank==0: print "\nFinishing post-processing which requires collectives...\n"

sys.stdout.flush()
comm.Barrier()

for c in C: c.determinePlotLimits() # only confrontations on my processor

for w in localW:
    m,c = w
    t0  = time.time()    
    c.computeOverallScore(m)
    c.modelPlots(m)
    dt = time.time()-t0
    print ("    {0:>%d} {1:>%d} %sCompleted%s {2:>5.1f} s" % (maxCL,maxML,OK,ENDC)).format(c.longname,m.name,dt)
    
sys.stdout.flush()
comm.Barrier()

for c in C:
    c.compositePlots()
    c.generateHtml()
    sys.stdout.flush()
 
sys.stdout.flush()
comm.Barrier()

if rank==0:
    Conf.createHtml(M)
    Conf.createSummaryFigure(M)
    print "\nCompleted in {0:>5.1f} s\n".format(time.time()-T0)

