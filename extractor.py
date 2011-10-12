"""
Author: Grischa Meyer
Email: grischa@gmail.com
"""

bugslist = dict()
import regex
import urllib2
import sys
from multiprocessing import Pool

def loadBugs():
    """
    parse bugs list from json, return list
    """
    import json
    bugsfilename = "bugs.js"
    bugsfile = open(bugsfilename, 'r')
    global bugslist
    bugslist = json.load(bugsfile)
    bugsfile.close()
    #build regexp dictionary in memory:
    bugsdb = dict()
    for bug in bugslist["bugs"]:
        #print(bug["pattern"])
        bugsdb[bug["id"]] = {"pattern": regex.compile(bug["pattern"],
                                                      flags=regex.IGNORECASE),
                             "name": bug["name"]}
    return bugsdb


def loadWebPage(url):
    """
    load webpage using Chrome Linux User-agent string
    """
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; ' +
                          'WOW64) AppleWebKit/535.2 (KHTML, like Gecko)' +
                          ' Chrome/15.0.874.83 Safari/535.2')]
    page = opener.open("http://" + url, timeout=2)
    src = page.read()
    page.close()
    return src


def evalUrl(url):
    """
    function that evaluates one page and returns bugids found on it
    """
    src = loadWebPage(url)
    bugsdb = loadBugs()
    foundapps = []
    for id, data in bugsdb.iteritems():
        if data["pattern"].search(src):
            foundapps.append((id, data["name"]))
    return foundapps


def loadUrlList():
    """
    reads file with hosts, return list of tuples with rank and hostname
    """
    filename = "mylist.csv"
    listfile = open(filename, 'r')
    lines = listfile.readlines()
    listfile.close()
    hosts = [(line.split(',')[0], line.split(',')[1].strip())
             for line in lines]
    return hosts


def process(lineitem):
    """
    call evaluator and format results.
    write results to file, one each result, to avoid collisions when using
    multiprocessing
    """
    rank, url = lineitem
    resultstring = "%s,%s," % (rank, url)
    try:
        result = evalUrl(url)
        resultlist = [":".join(app) for app in result]
        resultstring += ";".join(resultlist)
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except:
        resultstring += "error: " + str(sys.exc_info()[1])
    dirname = "results/"
    ofile = open(dirname + rank, 'w')
    ofile.write(resultstring + "\n")
    ofile.close()

if __name__ == "__main__":
    urllist = loadUrlList()
    # process url list in parallel (6 processes)
    mypool = Pool(6)
    mypool.map(process, urllist)
    # combine all results into single file
    ofile = open("results.csv", 'w')
    for rank, url in urllist:
        ifile = open("results/" + rank, 'r')
        ofile.write(ifile.read())
        ifile.close()
    ofile.close()
