'''
    Author: Kshitij Budhani
    Course: Information Retrieval
    Contact: f2013083@pilani.bits-pilani.ac.in
'''

''' Kshitij is avoiding using Nltk as much as possible for now as the searches will be very slow otherwise '''

import sys
import re
import gc
from porterStemmer import PorterStemmer
from collections import defaultdict
from array import array
from math import log,sqrt
import operator
from fuzzywuzzy import fuzz


index_porter = PorterStemmer()

class Index:
    N=4718
    token_set= set()                            #to store the tokens without stemming for correction
    id_title={}                                 #to store the corresponding title for docId
    def __init__(self):
        self.index = defaultdict(list)

    def remove_stop_words(self):
        file = open(self.stopwordsFile, 'rw')
        stop_words = [line.rstrip() for line in file]
        '''rstrip removes whitespace characters(by default)'''
        self.stop_words_dict = dict.fromkeys(stop_words)
        file.close()

    def process_text(self, line):
        line = line.lower()
        line=re.sub(r'[^a-z0-9 ]',' ',line)
        '''need to revisit this as Kshitij is not including any other character other than alphanumerics'''
        line = line.split()
        '''desi tokenizer(no NLTK) :P'''
        line = [word for word in line if word not in self.stop_words_dict]
        temp=set(line)
        self.token_set=self.token_set | temp
        line = [index_porter.stem(word , 0 , len(word) - 1) for word in line]
        return line

    def parse_wiki(self):
        doc = []
        for line in self.collFile:
            if line == '</doc>\n':
                break
            doc.append(line)

        Page = ' '.join(doc)
	#print(Page)
        pageid=re.search('<doc id="(.*?)"', Page, re.DOTALL)
        pagetitle=re.search('<doc.* title="(.*?)"', Page, re.DOTALL)
        pagetext=re.search('<doc.*>(.*)', Page, re.DOTALL)
        

        if pageid==None or pagetitle==None or pagetext==None:
       	    #print(pageid,pagetitle,pagetext)
            return {}

        self.id_title[pageid.group(1)]=(pagetitle.group(1),pagetext.group(1))

        d={}
        d['id']=pageid.group(1)
        d['title']=pagetitle.group(1)
        d['text']=pagetext.group(1)
	#print(d['text'])
	#sys.exit();	
	#print("hello")

        return d
    def index_to_file(self):
        f = open(self.indexFile, 'w')
        for term in self.index.iterkeys():
            postinglist=[]
            for p in self.index[term]:
                docID=p[0]
                positions=p[1]
                postinglist.append(':'.join([str(docID) ,','.join(map(str,positions))]))
            print >> f, ''.join((term,'|',';'.join(postinglist)))

        f.close()

    def get_param(self):
        param = sys.argv
        self.stopwordsFile = param[1]
        self.collectionFile = param[2]
        self.indexFile = param[3]

    def create_index(self):
        self.get_param()
        self.collFile = open(self.collectionFile,'r')
        self.remove_stop_words()

        gc.disable()

        pagedict = {}
        pagedict=self.parse_wiki()


        while pagedict!={}:
            lines = '\n'.join((pagedict['title'],pagedict['text']))
            pageid = int(pagedict['id'])
            terms = self.process_text(lines)

            termdictpage = {}
            for position,term in enumerate(terms):
                try:
                    termdictpage[term][1].append(position)
                except:
                    termdictpage[term]=[pageid,array('I',[position])]

            for termpage,postingpage in termdictpage.iteritems():
                self.index[termpage].append(postingpage)

            pagedict = self.parse_wiki()

        gc.enable()

        self.index_to_file()

    def create_mat(self):
        self.mat={}
        self.length={}
        for term,post in self.index.iteritems():
            df=len(post)
            for doc in post:
                tf=len(doc[1])
                try:
                    self.mat[doc[0]][term]=(1+log(tf))*log(self.N/float(df))
                except:
                    self.mat[doc[0]]={term:(1+log(tf))*log(self.N/float(df))}
                
                try:
                    self.length[doc[0]]=self.length[doc[0]]+(1+log(tf))*log(self.N/float(df))*(1+log(tf))*log(self.N/float(df))
                except:
                    self.length[doc[0]]=(1+log(tf))*log(self.N/float(df))*(1+log(tf))*log(self.N/float(df))
        
        for k,v in self.length.iteritems():
            v=sqrt(v)
        #print(self.mat)
        #print(len(self.mat))



    def rank_doc(self,query):
        scores={}
        for q in query:
        
            post=self.index[q]
            
            df=len(post)

            if df == 0 : 
                continue
            
            w=log(self.N/float(df))
        #    print("hellllo",q,"asdas",df,w)
            for doc in post:
                try:
                    temp=self.mat[doc[0]][q]
                except:
                    temp=0
                try:
                    scores[doc[0]]= scores[doc[0]] + w*(temp)
                except:
                    scores[doc[0]]= w*(temp)

            for d,s in scores.iteritems():
                scores[d]=float(s)/(self.length[d])
        #print(scores)
        rank=sorted(scores.items(), key=operator.itemgetter(1),reverse=True)
        return rank                         #this is list of tuples (docId,score) sorted by score

    def find_match(self,token): 
        maxy=0
        token_list=list(self.token_set)
        if(token in self.token_set):
            return 100,token
        else:    
            for k in token_list:
                temp=fuzz.ratio(token,k)
                if temp>maxy:
                    maxy=temp
                    return_token=k
            #print("value of match",maxy)
            return maxy,return_token

    def get_similar(self,docId):
        scores={}
        for doc in self.mat.iterkeys():
            if(doc == docId):
                continue
            if(len(self.mat[doc]) < len(self.mat[docId])):
                first=self.mat[doc]
                second=self.mat[docId]
            else:
                first=self.mat[docId]
                second=self.mat[doc]
            for k,v in first.iteritems():
                try:
                    scores[doc]
                except:
                    scores[doc]=0                        #if this key not initialised ,it is initialised here
                try:
                    scores[doc]=scores[doc]+second[k]*v   #check if the key is present in second
                except:
                    continue
        for d,s in scores.iteritems():
            scores[d]=float(s)/(self.length[d]*self.length[docId])

        rank=sorted(scores.items(), key=operator.itemgetter(1),reverse=True)
        return rank                         #this is list of tuples (docId,score) sorted by score


if __name__ == "__main__" :
        i=Index()
        i.create_index()
        i.create_mat()
        #print(i.id_title)
        #print(i.token_set)
        while True: 
            st=raw_input("search karo: ")
            st=st.lower()
            l=st.split();
            main=[]
            for token in l:
                match,index=i.find_match(token)
                if match== 100:
                    main.append(token)
                else:
                    main.append(index)
                
            line = [index_porter.stem(word , 0 , len(word) - 1) for word in main]

            #print("asdadsasd",line)
            rank_list=i.rank_doc(line)

            if len(rank_list)==0:
                print("NO RESULTS FOUND")
            else:
                print("SHOWING RESULTS FOR "+ " ".join(main))
                

            for x in rank_list:
                print(x[0],x[1])
                print(i.id_title[str(x[0])][0])
                #print(str(i.id_title[str(x[0])][1]))
                h1='https://en.wikipedia.org/wiki?curid=' + str(x[0])
                for q in main:
                    #print(q)
                    pass1='\.(.*?)'+str(q)+'(.*?)\.'
                    st=(i.id_title[str(x[0])])[1].lower()
                    str1=re.search( pass1 ,st)
                    if str1 !=None:
                        print(str1.group())
                    
                    

                print(h1)
                print("\n")
            response=raw_input("SEARCH FOR " + " ".join(l) + " INSTEAD ? y/n ? ")
            if response == "y":
                line = [index_porter.stem(word , 0 , len(word) - 1) for word in l]
                    #print("asdadsasd",line)
                rank_list=i.rank_doc(line)
                for x in rank_list:
                    print(x[0],x[1])
                    print(i.id_title[str(x[0])][0])
                    h1='https://en.wikipedia.org/wiki?curid=' + str(x[0])
                    print(h1)
                    print("\n")
                    similar_docs=i.get_similar(rank_list[0][0])
                    print("**** SIMILAR DOCS****")
                    for d in similar_docs[:5]:
                        print(d[0])
                        print(i.id_title[str(d[0])][0])
                        h1='https://en.wikipedia.org/wiki?curid=' + str(d[0])
                        print(h1)
                        print("\n")
                        
            similar_docs=i.get_similar(rank_list[0][0])
            print("**** SIMILAR DOCS****")
            for x in similar_docs[:5]: 
                print(x[0],x[1])
                print(i.id_title[str(x[0])][0])
                h1='https://en.wikipedia.org/wiki?curid=' + str(x[0])
                print(h1)
                print("\n")






