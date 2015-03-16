import sys, time, subprocess, glob, os, urllib2, json
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
def MakeIndexTableRow(link, size, commits, hash, success, debuglink, date):
	for i, p in enumerate(("", "K", "M", "G", "T")):
		if float(size)/(1024**i) >= 900: continue
		size = "%.2f%sB" % (float(size)/(1024**i), p)
		break
		
	link = "<a href=\"%s\">Download Citra.zip</a>" % link if success else "None"
	debuglink = "<a href=\"%s\">output.log</a>" % debuglink
	
	success = ("Failed", "Successful")[1*success]
	
	if hash:
		commits = "<a href=\"https://github.com/citra-emu/citra/commit/%s\">%s</a>" % (hash, commits)
		hash = "<a href=\"https://github.com/citra-emu/citra/commit/%s\">%s</a>" % (hash, hash)
	
	return "\t\t\t<tr>\n%s\n\t\t\t</tr>" % ("\n".join(("\t\t\t\t<td>%s</td>" % i for i in (link, size, commits, hash, success, debuglink, date))))
def CheckUpdate():
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
	
	#check if already compiled:
	if not os.path.exists("nightlybuild"):
		return True
	gitfolder = g_repository.split("/")[-1][:-4]
	if not os.path.exists(os.path.join("nightlybuild", gitfolder)):
		return True
	if not os.path.exists(os.path.join("nightlybuild", gitfolder, "citra nightlies")):
		return True
	if not len(glob.glob(os.path.join("nightlybuild", gitfolder, "citra nightlies", "%i-%s-*" % (commits, hash)))):
		return True
	else:
		return False
	
#doers
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
		#todo: find the git info on failed build
		return False, ["output.log"], 0, ""
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
		Say("Unable to get has and commit count")
		Say("\n"+str(e))
		return False, ["output.log"], 0, ""
	
	os.chdir(prev)
	return True, ["Citra.zip", "output.log"], commits, hash
def AddToSite(success, files, commits, hash):
	global g_repository, g_git
	prev = os.getcwd()
	if not os.path.exists("nightlybuild"): os.mkdir("nightlybuild")
	os.chdir("nightlybuild")
	
	gitfolder = g_repository.split("/")[-1][:-4]
	if os.path.isdir(gitfolder):
		os.chdir(gitfolder)
		subprocess.call((g_git, "pull"))
	else:
		subprocess.call((g_git, "clone", g_repository))
		os.chdir(gitfolder)
		subprocess.call((g_git, "config", "credential.helper", "store"))#store usrname and password in plaintext, but makes sure you don't have to type it again
	
	if not os.path.isdir("citra nightlies"): os.mkdir("citra nightlies")
	os.chdir("citra nightlies")
	
	#if previous build of same version exists
	if len(glob.glob("%i-%s-*" % (commits, hash))):
		pass#remove citra and output.log
		return
	
	#move to proper place:
	dir = "%i-%s-%s-%s" % (commits, hash, success, time.strftime("%H-%M-%S-%d-%m-%Y"))
	os.mkdir(dir)
	for i in files:
		os.rename(i, os.path.join(dir, os.path.basename(i)))
	
	#sort what i want:
	buildlist = []
	for folder in (os.path.basename(i) for i in glob.glob("*") if os.path.isdir(i)):
		index, hash, success, H, M, S, d, m, Y = folder.split("-")
		date = "%s:%s:%s %s/%s-%s" % (H, M, S, d, m, Y)
		success = success == "True"
		index = int(index)
		link = "%s/Citra.zip" % folder
		debuglink = "%s/output.log" % folder
		
		if success:
			size = os.path.getsize(os.path.join(folder, "Citra.zip"))
		else:
			size = 0
		
		#filter here?
		pass
		
		buildlist.append((index, MakeIndexTableRow(link, size, index, hash, success, debuglink, date)))
	
	#i want about 40?
	pass
	
	#make index file
	f = open("index.html", "wb")
	f.write(g_template.replace("<!--SPLIT-->", "\n".join(map(lambda x: x[1], sorted(buildlist, key=lambda x: -x[0])))))
	f.close()
	
	#commit:
	os.chdir(os.path.join(prev, "nightlybuild", gitfolder))
	subprocess.call((g_git, "add", "."))
	subprocess.call((g_git, "commit", "--author=\"%s\"" % g_author, "-m", "Added build for citra commit number %i" % commits))#, "--dry-run"))
	subprocess.call((g_git, "commit", "--author=\"%s\"" % g_author, "-m", "Added build for citra commit number %i" % commits))#, "--dry-run"))
	
	subprocess.call((g_git, "push", "origin", "master"))
	#cmd = subprocess.Popen((g_git, "push", "origin", "master"), stdin=subprocess.PIPE)
	#time.sleep(5)
	#cmd.stdin.write("%s\n"%g_username)
	#time.sleep(1)
	#cmd.stdin.write("%s\n"%g_password)
	#cmd.wait()
	#while not cmd.poll():
	#	time.sleep(0.2)
	
	os.chdir(prev)
#daemon
#def Mainloop(usr, psw, author, repo):
def Mainloop(author, repo):
	global g_repository, g_author
	g_repository = repo
	g_author = author
	
	jobs = []#i = (time, "job")
	
	#add jobs:
	H, M, S = map(int,time.strftime("%H %M %S").split(" "))
	nHour = 60*(59 - M) + (59 - S) + 5#next hour
	
	jobs.append((time.time()+60*5, "flush"))
	jobs.append((time.time()+nHour, "HandleUpdate"))
	jobs.append((time.time()+nHour+5-(H+1)%6, "Compile"))
	
	
	#while 1:
	#	for t, c in jobs:
	#		if time.time() >= t:
	#			
	if 1:	
		
		
		
		if CheckUpdate():
			success, files, commits, hash = DoCompile()
			if hash:
				files = [os.path.join(os.getcwd(), i) for i in files]
				AddToSite(success, files, commits, hash)
		else:
			Say("no new version")
		
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