import os, sys, subprocess, atexit, shutil

g_enable_QT = False

g_git = None
g_cmake = None
g_mvs_link = None
g_msbuild = None

def NotBool(i):
	if i: return False
	return True
def Clean():
	if os.path.isdir("workspace"):
		print "Deleting old workspace..."
		#if shutil.rmtree("workspace"):
		if subprocess.call(("rmdir /s /q workspace"), shell = True):
			print "Unable to delete old workspace. Exiting..."
			sys.exit(1)

def FindDepencies():
	global g_git, g_cmake, g_mvs_link, g_msbuild
	
	#find depencies:
	for i in (os.environ["ProgramFiles"], os.environ["ProgramFiles(x86)"], "C:\Program Files (x86)", "C:\Program Files"):
		#git
		check = os.path.join(i, "Git\\bin\\git.exe")
		if os.path.exists(check) and os.path.isfile(check): g_git = check
		#CMake
		check = os.path.join(i, "CMake\\bin\\cmake.exe")
		if os.path.exists(check) and os.path.isfile(check): g_cmake = check
		#Microsoft Visual Studio 12.0 2013
		check = os.path.join(i, "Microsoft Visual Studio 12.0 2013\\VC\\bin\\link.exe")
		if os.path.exists(check) and os.path.isfile(check): g_mvs_link = os.path.split(check)[0]
		#MSBUILD
		check = os.path.join(i, "MSBuild\\12.0\\Bin\\MSBuild.exe")
		if os.path.exists(check) and os.path.isfile(check): g_msbuild = check
		
		if g_git and g_cmake and g_mvs_link and g_msbuild:
			break
	else:#error reporting
		if not g_git and not subprocess.call(("git", "version")):
			g_git = "git"
		
		if not g_git or not g_cmake or not g_mvs_link or not g_msbuild:
			print "Error"
			print ("Git, "*NotBool(g_git) + "CMake, "*NotBool(g_cmake) + "Microsoft Visual Studio 12.0 2013, "*NotBool(g_mvs_link) + "MSBuild, "*NotBool(g_msbuild)) [:-2] + " not found!"
			print "Exiting..."
			sys.exit(1)

def FetchCitra():
	global g_git
	prev = os.getcwd()
	os.chdir("workspace")
	
	#clone
	print "\nCloning citra repository..."
	ret = subprocess.call((g_git, "clone", "--recursive", "https://github.com/citra-emu/citra.git"))
	
	if not os.path.exists("citra") or ret:
		os.chdir(prev)
		print "\nCouldn't clone citra repository! Exiting..."
		sys.exit(1)
	
	os.chdir(prev)

def DoCMake():
	global g_cmake, g_enable_QT, g_mvs_link
	prev = os.getcwd()
	os.chdir("workspace\\build")
	
	#setup/generate
	print "\nGenerating CMake..."
	if subprocess.call((g_cmake, "-G", "Visual Studio 12 2013", os.path.join(prev, "workspace\\citra"))):
		print "ech"
	
		#configure
		print "\nConfiguring CMake..."
		f = open("CMakeCache.txt", "rb")
		Cache = f.read().replace("\r\n", "\n").replace("\r", "\n").split("\n")
		f.close()
		
		for i, line in enumerate(Cache):
			if line[:15] == "ENABLE_QT:BOOL=":
				Cache[i] = "ENABLE_QT:BOOL=" + ("ON" if g_enable_QT else "OFF")
			#if line[:22] == "CMAKE_LINKER:FILEPATH=":
			#	Cache[i] = "CMAKE_LINKER:FILEPATH=" + os.path.join(g_mvs_link, "link.exe").replace("\\", "/")
		
		f = open("CMakeCache.txt", "w")
		f.write("\n".join(Cache))
		f.close()
		
		#Generate:
		print "\nGenerating CMake..."
		if subprocess.call((g_cmake, "-G", "Visual Studio 12 2013", os.path.join(prev, "workspace\\citra"))):
			print "\n\nCMake generation failed!"
	
	os.chdir(prev)

def DoCompile():
	global g_msbuild
	prev = os.getcwd()
	os.chdir("workspace\\build")
	print "\nCompiling citra..."
	if subprocess.call((g_msbuild, "/t:citra", "citra.sln")):
		print "\nCompile failed!"
		sys.exit(1)
	os.chdir(prev)


#do:
FindDepencies()

Clean()
os.mkdir("workspace")
os.mkdir("workspace\\build")

FetchCitra()
DoCMake()
DoCompile()

shutil.make_archive("Citra", 'zip', "workspace\\build\\bin")