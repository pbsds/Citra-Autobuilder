import sys, time, subprocess, glob, os
#requires that python2 and git is available in the PATH, or that they lie in their default install directory


#globals:
g_repository = None
g_username = None
g_password = None
g_author = None

g_template = None

g_git = None
g_python = None

#helpers:
def Say(text):
	print time.strftime("[%H:%M:%S]"), text
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
	f.write(g_template.replace("<!--SPLIT-->", "\n".join(map(lambda x: x[1], sorted(buildlist, lambda x: -x[0])))))
	f.close()
	
	#commit:
	os.chdir(os.path.join(prev, "nightlybuild", gitfolder))
	subprocess.call((g_git, "add", "."))
	subprocess.call((g_git, "commit", "--author=\"%s\"" % g_author, "-m", "Added build for citra commit number %i" % commits))#, "--dry-run"))
	subprocess.call((g_git, "commit", "--author=\"%s\"" % g_author, "-m", "Added build for citra commit number %i" % commits))#, "--dry-run"))
	
	subprocess.call((g_git, "push"))
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
def Mainloop(usr, psw, author, repo):
	global g_repository, g_username, g_password, g_author
	g_repository = repo
	g_username = usr
	g_password = psw
	g_author = author
	
	#while 1:
	if 1:
		success, files, commits, hash = DoCompile()
		#success, files, commits, hash = True, ("Citra.zip", "output.log"), 123123, "asdasdasdasdasd"
		if hash:
			files = [os.path.join(os.getcwd(), i) for i in files]
			AddToSite(success, files, commits, hash)
		
		
#do:
def Main():
	global g_template
	if len(sys.argv) < 5:
		#print "Usage: bleh.py <git username> <git password> <name <email>> <github.io repository>"
		print "Usage: bleh.py <name <email>> <github.io repository>"
	else:
		#usr, psw, author, repo = sys.argv[1:5]
		author, repo = sys.argv[1:5]
	
	f = open("template.html", "rb")
	g_template = f.read().replace("\r\n", "\n").replace("\r", "\n")
	f.close()
	
	FindPythonGit()
	Mainloop(usr, psw, author, repo)
if __name__ == "__main__":
	Main()