import sys, time, subprocess, glob, os, urllib, urllib2, json
try:
	import requests
except ImportError:
	print "requests not installed, exiting..."
#requires that python2 and git is available in the PATH, or that they lie in their default install directory


#globals:
g_repository = None
g_author = None

g_template = None

g_git = None
g_python = None

#helpers:
class Log:
	def __init__(self):
		#temp = map(int,time.strftime("%M %S").split(" "))
		#temp[0] = 59 - temp[0]
		#temp[1] = 59 - temp[1]
		#reactor.callLater(60*temp[0] + temp[1] + 5, self.HandleUpdate)
		#reactor.callLater(60*5, self.AutoFlush)
		if not os.path.exists("logs"):
			os.mkdir("logs")
		
		if not os.path.exists("logs/"+time.strftime("%Y")):
			os.mkdir("logs/"+time.strftime("%Y"))
		
		if not os.path.exists("logs/"+time.strftime("%Y/%B")):
			os.mkdir("logs/"+time.strftime("%Y/%B"))
		
		self.file = open("logs/"+time.strftime("%Y/%B")+"/"+time.strftime("%d %B")+".log","a")
		
		pass#self.file.write(time.strftime("[%H:%M:%S] ")+"Server start!\n")
	def HandleUpdate(self):#updates the handles for new filename (call new every hour)
		reactor.callLater(60*60, self.HandleUpdate)
		print time.strftime("[%H:%M:%S] Handle update")
		
		if not os.path.exists("logs/"+time.strftime("%Y")):
			os.mkdir("logs/"+time.strftime("%Y"))
		
		if not os.path.exists("logs/"+time.strftime("%Y/%B")):
			os.mkdir("logs/"+time.strftime("%Y/%B"))
		
		self.file.close()
		
		self.file = open("logs/"+time.strftime("%Y/%B")+"/"+time.strftime("%d %B")+".log","a")
	def Flush(self):#Flushes the filehandle (call every 5 minutes)
		self.file.flush()
		os.fsync(self.file.fileno())
	#=====
	def Say(self, string):
		out = time.strftime("[%H:%M:%S] %%s") % string
		self.file.write(out)
		self.file.write("\n")
		print out
Log = Log()
Say = Log.Say
def FindPythonGit():
	global g_git, g_python
	
	if not subprocess.call(("git", "version")):
		g_git = "git"
	else:
		for i in (os.environ["ProgramFiles"], os.environ["ProgramFiles(x86)"], "C:\Program Files (x86)", "C:\Program Files"):
			check = os.path.join(i, "Git\\bin\\git.exe")
			if os.path.exists(check) and os.path.isfile(check):
				g_git = check
				break
		else:
			Say("Git not found, exiting...")
			sys.exit(1)
	
	if not subprocess.call(("python", "--version")):
		g_python = "python"
	elif os.path.isfile("C:/Python27/python.exe"):
		g_python = "C:/Python27/python.exe"
	else:
		Say("Python not found, exiting...")
		sys.exit(1)
def MakeIndexTableRow((commits, hash, success, hour, minute, second, day, month, year, link, size, debuglink)):
	link = "<a href=\"%s\">Download Citra</a>" % link if success=="True" else "None"
	debuglink = "<a href=\"%s\">output log</a>" % debuglink
	
	date = "%s:%s:%s %s/%s-%s" % (hour, minute, second, day, month, year)
	
	success = ("Failed", "Successful")[1*success=="True"]
	
	if hash:
		commits = "<a href=\"https://github.com/citra-emu/citra/commit/%s\">%s</a>" % (hash, commits)
		hash = "<a href=\"https://github.com/citra-emu/citra/commit/%s\">%s</a>" % (hash, hash)
	
	return "\t\t\t<tr>\n%s\n\t\t\t</tr>" % ("\n".join(("\t\t\t\t<td>%s</td>" % i for i in (link, size, commits, hash, success, debuglink, date))))
def GetCitraCurrent():
	#get total number of commits
	total = []
	url = "https://api.github.com/repos/citra-emu/citra/contributors?anon=1"
	while 1:
		resp = urllib2.urlopen(urllib2.Request(url))
		js = json.loads(resp.read())
		
		total.append(sum((n["contributions"] for n in js)))
		
		links = resp.info()["link"].split(", ")
		if links[0].endswith("rel=\"next\""):
			url = links[0].split(";")[0][1:-1]
			continue
		break
	commits = sum(total)
	
	#get hash
	resp = urllib2.urlopen(urllib2.Request("https://api.github.com/repos/citra-emu/citra/commits"))
	js = json.loads(resp.read())
	hash = js[0]["sha"]
	
	return commits, hash
def CheckUpdate():
	try:
		commits, hash = GetCitraCurrent()
	except:
		return False
	
	#check if already compiled:
	if not os.path.exists("nightlybuild"):
		return True
	gitfolder = g_repository.split("/")[-1][:-4]
	if not os.path.exists(os.path.join("nightlybuild", gitfolder)):
		return True
	if not os.path.exists(os.path.join("nightlybuild", gitfolder, "citra nightlies")):
		return True
	
	#read previously built citras:
	buildlist = []#i = (commits, hash, success, hour, minute, second, day, month, year, build url, size, log url, )
	if os.path.exists(os.path.join("nightlybuild", gitfolder, "citra nightlies", "builds.dat")):
		f = open(os.path.join("nightlybuild", gitfolder, "citra nightlies", "builds.dat"), "rb")
		content = f.read()
		f.close()
		if content:
			buildlist = [i.split("-") for i in content.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
	
	#check if already buildt:
	check = map(str, (commits, hash, "True"))
	for i in buildlist:#this could become very intensive after many compiles. maybe only read the first 5?
		if i[:3] == check:
			pass#remove citra and output.log?
			return False
	return True
def Upload(upload_filepath):#to pomf.se
	file = open(upload_filepath, "rb")
	try:
		response = requests.post(url="http://pomf.se/upload.php", files={"files[]":file})
	except Exception as e:
		file.close()
		print "error uploading", upload_filepath
		print e
		return False, ""
	file.close()
	
	js = json.loads(response.text)
	#print js["success"]
	#print js["files"][0]["url"]
	
	return js["success"], "http://a.pomf.se/" + js["files"][0]["url"]

#doers:
def DoCompile():
	global g_python
	Say("Building citra...")
	prev = os.getcwd()
	
	#import build
	#build.Main()
	
	f = open("output.log", "wb")
	if subprocess.call((g_python, "build.py"), stdout=f, stderr=f):#i hope this method will write to the file untill it crashes
		Say("build failed!")
		f.close()
		
		try:
			commits, hash = GetCitraCurrent()
		except:
			commits, hash = 0, ""
		
		return False, ["output.log"], commits, hash
	f.close()
	
	#get commitcount and hash
	os.chdir("workspace")
	os.chdir("citra")
	try:
		commits = int(subprocess.check_output(("git", "rev-list", "HEAD", "--count")))
		hash = subprocess.check_output(("git", "rev-parse", "HEAD"))
		if hash[-1] == "\n":
			hash = hash[:-1]
	except Exception as e:# subprocess.CalledProcessError:
		Say("Unable to get hash and commit count from local repository")
		Say("\n"+str(e))
		
		try:
			commits, hash = GetCitraCurrent()
		except:
			commits, hash = 0, ""
		
		return False, ["output.log"], commits, hash
	
	os.chdir(prev)
	return True, ["Citra.zip", "output.log"], commits, hash
def AddToSite(success, files, commits, hash):
	#upload files:
	citrabuild, logfile = "None", "None"
	buildsize = ""
	for i in files:
		uploaded, url = Upload(i)
		if uploaded:
			if i[-3:] == "log":
				logfile = url
			if i[-3:] == "zip":
				citrabuild = url
				
				buildsize = os.path.getsize(i)
				for i, p in enumerate(("", "K", "M", "G", "T")):
					if float(buildsize)/(1024**i) >= 900: continue
					buildsize = "%.2f%sB" % (float(buildsize)/(1024**i), p)
					break
	
	#update local github.io repository:
	global g_repository, g_git
	prev = os.getcwd()
	if not os.path.exists("nightlybuild"): os.mkdir("nightlybuild")
	os.chdir("nightlybuild")
	
	gitfolder = g_repository.split("/")[-1][:-4]
	if os.path.isdir(gitfolder):
		os.chdir(gitfolder)
		#subprocess.call((g_git, "pull"))
	else:
		subprocess.call((g_git, "clone", g_repository))
		os.chdir(gitfolder)
		subprocess.call((g_git, "config", "credential.helper", "store"))#store usrname and password in plaintext, but makes sure you don't have to type it again
	
	if not os.path.isdir("citra nightlies"): os.mkdir("citra nightlies")
	os.chdir("citra nightlies")
	
	#read previously built citras:
	buildlist = []#i = (commits, hash, success, hour, minute, second, day, month, year, build url, size, log url, )
	if os.path.exists("builds.dat"):
		f = open("builds.dat", "rb")
		content = f.read()
		f.close()
		if content:
			buildlist = [i.split("-") for i in content.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
	
	#check if previous build of same the version exists:
	check = map(str, (commits, hash, success))
	for i in buildlist: #this could become very intensive after many compiles. maybe only read the first 5? it's sorted anyway...
		if i[:3] == check:
			pass#remove citra and output.log?
			return False
	
	#add the new build:
	new = [commits, hash, success] + time.strftime("%H-%M-%S-%d-%m-%Y").split("-") + [citrabuild, buildsize, logfile]
	buildlist.insert(0, map(str, new))
	buildlist = sorted(buildlist, key=lambda x: -int(x[0]))#comment this out?
	
	#save to builds.dat:
	f = open("builds.dat", "wb")
	f.write("\n".join("-".join(i) for i in buildlist))
	f.close()
	
	#write the index files:
	pages = max(((len(buildlist)-1)//50 + 1, 1))
	for i in xrange(pages):
		navigation = []
		if i >= 1:
			if i == 1:
				navigation.append("<a href=\"index.html\">Previous page</a>")
			else:
				navigation.append("<a href=\"index-%s.html\">Previous page</a>" % (i))
		if i+1 < pages:
			navigation.append("<a href=\"index-%s.html\">Next page</a>" (i+2))
		
		table = g_template.replace("<!--BUILDS-->", "\n".join((MakeIndexTableRow(i) for i in buildlist[i*50:i*50+50]))).replace("<!--NAVIGATION-->", " ".join(navigation))
		
		f = open("index-%s.html" % (i+1) if i else "index.html", "wb")
		f.write(table)
		f.close()
	
	#commit:
	os.chdir(os.path.join(prev, "nightlybuild", gitfolder))
	subprocess.call((g_git, "add", "."))
	subprocess.call((g_git, "commit", "--author=\"%s\"" % g_author, "-m", "Added build for citra commit number %i" % commits))#, "--dry-run"))
	
	subprocess.call((g_git, "push", "origin", "master"))
	
	os.chdir(prev)

#daemon
def Mainloop(author, repo):
	global g_repository, g_author
	g_repository = repo
	g_author = author
	
	#queue
	jobs = []#i = (time, "job")
	
	#add jobs:
	M, S = map(int,time.strftime("%M %S").split(" "))
	nHour = 60*(59 - M) + (59 - S) + 5#next hour
	
	jobs.append((time.time()+60*5, "flush"))
	#jobs.append((time.time()+60*60, "HandleUpdate"))
	jobs.append((time.time()+nHour, "HandleUpdate"))
	# jobs.append((time.time()+60*60*6, "Compile"))
	jobs.append((0, "Compile"))
	
	while 1:
		rem = []
		for i, (t, c) in enumerate(jobs):
			if time.time() >= t:
				if c=="Compile":
					if CheckUpdate():
						Say("New citra version, compiling...")
						success, files, commits, hash = DoCompile()
						if hash:
							files = [os.path.join(os.getcwd(), i) for i in files]
							if not AddToSite(success, files, commits, hash):
								Say("Failed version already exists")#happens when it is unsuccessfull on same build twise
					else:
						Say("No new citra version, will not compile.")
					
					jobs.append((time.time()+60*60*6, "Compile"))#queue next job
				elif c=="flush":
					Log.Flush()
					jobs.append((time.time()+60*5, "flush"))#queue next job
				elif c=="HandleUpdate":
					Say("Handle update")
					Log.HandleUpdate()
					jobs.append((time.time()+60*60, "HandleUpdate"))#queue next job
				rem.append(i)
		for i in rem[::-1]: del jobs[i]
		
		time.sleep(5)
#do:
def Main():
	global g_template
	if len(sys.argv) < 3:
		print "Usage: bleh.py <name <email>> <github.io repository>"
		sys.exit()
	else:
		author, repo = sys.argv[1:3]
	
	f = open("template.html", "rb")
	g_template = f.read().replace("\r\n", "\n").replace("\r", "\n")
	f.close()
	
	FindPythonGit()
	
	#update github.io repository:
	if 1:
		prev = os.getcwd()
		if not os.path.exists("nightlybuild"): os.mkdir("nightlybuild")
		os.chdir("nightlybuild")
		gitfolder = repo.split("/")[-1][:-4]
		if os.path.isdir(gitfolder):
			os.chdir(gitfolder)
			subprocess.call((g_git, "pull"))
		else:
			subprocess.call((g_git, "clone", repo))
			os.chdir(gitfolder)
			subprocess.call((g_git, "config", "credential.helper", "store"))#store usrname and password in plaintext, but makes sure you don't have to type it again
		os.chdir(prev)
	
	Mainloop(author, repo)
if __name__ == "__main__":
	Main()