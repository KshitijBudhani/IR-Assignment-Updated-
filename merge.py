import sys
import os
f=open('big',"a")
path='/home/harnish/Desktop/IR/wikiextractor-master/text/AA/'
for filename in os.listdir('/home/harnish/Desktop/IR/wikiextractor-master/text/AA/'):
	try:
		file=open(path+str(filename),"r")
		for line in file:
			f.write(line)
		file.close()
	except:
		continue;
