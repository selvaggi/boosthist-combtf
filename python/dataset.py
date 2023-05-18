

import os

class Dataset:

    def __init__(self, dataset):
    
        self.name = dataset['name']
        self.datadir = dataset['datadir']
        self.xsec = dataset['xsec']
        self.rootfiles = self.findROOTFiles(self.datadir)
        

    def findROOTFiles(self, basedir, regex = ""):
        
        if ".root" in basedir: return [basedir]
        
        if regex != "":
        
            if basedir[-1] == "/": basedir = basedir[:-1]
            regex = basedir + "/" + regex

        files = []
        for root, directories, filenames in os.walk(basedir):
        
            for f in filenames:
           
                filePath = os.path.join(os.path.abspath(root), f)
                if regex == "" or fnmatch.fnmatch(filePath, regex): files.append(filePath)
                
        return files