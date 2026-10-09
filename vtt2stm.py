
import numpy as np 
import os 
import sys 
import ntpath 
import collections

# Header :
# =======
# WEBVTT
# Kind: captions
# Language: fr-CA

def str2sec(time_string):
    parts = time_string.split(":")
    if(len(parts)==3):
        return int(parts[0])*(3600) + int(parts[1])*60 + float(parts[2])
    elif(len(parts)==2):
        return float(parts[0])*60 + float(parts[1])
    else:
        return time_string

def itv2tpl(timestamp):
    ts=timestamp.replace(' --> ',' ').split(' ')
    return (str2sec(ts[0]),str2sec(ts[1]))


# read file 
#dataf=np.loadtxt(sys.argv[1],dtype=str,delimiter='\r\n')
file1 = open(sys.argv[1], 'r')
dataf = file1.readlines()

fname=ntpath.basename(sys.argv[1]).split('.')[0]

data={}
hd_read=False
lastindex=None

for line in dataf :
    # skip header 
    if not (hd_read or ('-->' in line)) :
        continue 

    # read the rest as data 
    if '-->' in line:
        hd_read=True
        lastindex=itv2tpl(line)
        data[lastindex]=[]
    else:
        txt=line.rstrip()
        if (lastindex!=None) and (txt!=""):
            data[lastindex].append(txt)

# sort by timecode 
data = collections.OrderedDict(sorted(data.items()))

# print sentences 
for (s,e) in data.keys():
    print(fname, "{:.3f} {:.3f}".format(s,e),' '.join(data[(s,e)]))



