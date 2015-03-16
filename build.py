import os, sys, subprocess, atexit, shutil, glob


#todo: add Qt support, linux and possibly mac support aswell

#settings:
g_enable_QT = True
g_64bit = False#not yet implemented
g_debugbuild = False

#depencies paths
g_git = None
g_cmake = None
g_mvs_link = None
g_msbuild = None
g_qt5 = None

#helpers and init/cleanup
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
	global g_git, g_cmake, g_mvs_link, g_msbuild, g_qt5, g_enable_QT
	
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
	
	drives = (i[0].upper() for i in (os.environ["ProgramFiles"], os.environ["ProgramFiles(x86)"], "C"))
	for i in drives:
		if os.path.exists("%s:/Qt" % i):
			
			for dir in glob.glob("%s:/Qt/5*" % i):
				for ver in ("msvc2013_opengl",):#("msvc2013_64_opengl", "msvc2013_opengl"):
					if os.path.exists(os.path.join(dir, ver, "bin", "qmake.exe")):
						g_qt5 = os.path.join(dir, ver)
						break
				if g_qt5: break	
			if g_qt5:break
	else:
		if g_enable_QT:
			print "Error"
			print "Qt 5 not found!"
			print "Exiting..."
			sys.exit(1)

#Do the work
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
	global g_cmake, g_enable_QT, g_mvs_link, g_qt5
	prev = os.getcwd()
	os.chdir("workspace\\build")
	
	#setup/generate
	print "\nGenerating CMake..."
	args = [g_cmake,
	        "-G", "Visual Studio 12 2013",#32 bit?
	        "-D", "ENABLE_QT:BOOL=" + ("ON" if g_enable_QT else "OFF"),
	        os.path.join(prev, "workspace\\citra")]
	if g_enable_QT:
		args.insert(-1, "-D")
		args.insert(-1, "QT_QMAKE_EXECUTABLE:FILEPATH=" + os.path.join(g_qt5, "bin", "qmake.exe").replace("\\", "/"))
		args.insert(-1, "-D")
		args.insert(-1, "Qt5_DIR:PATH=" + os.path.join(g_qt5, "lib", "cmake", "Qt5").replace("\\", "/"))
	
	success = not subprocess.call(args)
	if not success and g_enable_QT:
		#sys.exit(1)#temp
		success = not subprocess.call((g_cmake, "-G", "Visual Studio 12 2013", "-D", "ENABLE_QT:BOOL=OFF", os.path.join(prev, "workspace\\citra")))
		if success:
			print "Qt not found, compiling without..."
			g_enable_QT = False
		else:
			print "cmake failed!"
			sys.exit(1)
	
	os.chdir(prev)
	return success
	
	#old method:
	if 0:
	#if subprocess.call((g_cmake, "-G", "Visual Studio 12 2013", os.path.join(prev, "workspace\\citra"))):
		#print "ech"
	
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
	global g_msbuild, g_debugbuild
	prev = os.getcwd()
	os.chdir("workspace\\build")
	print "\nCompiling Citra..."
	
	#msbuild  /t:citra /p:Configuration=Release citra.sln
	
	solution = "/p:Configuration=Debug" if g_debugbuild else "/p:Configuration=Release"
	output = os.path.join("bin", "Debug" if g_debugbuild else "Release")
	
	if subprocess.call((g_msbuild, "/t:citra", solution, "citra.sln")):
		print "\nCompile failed!"
		sys.exit(1)
	if g_enable_QT:
		print "\nCompiling Citra Qt..."
		if subprocess.call((g_msbuild, "/t:citra-qt", solution, "citra.sln")):
			print "\nCompile (qt) failed!"
			sys.exit(1)
		
		print "\nAdding Citra Qt DLLs..."
		files  = ["icudt53", "icuin53", "icuuc53"]
		files += [i + "d"*g_debugbuild for i in ("Qt5Core", "Qt5Gui", "Qt5OpenGL", "Qt5Widgets")]
		for i in files:
			shutil.copyfile(os.path.join(g_qt5, "bin", i+".dll"), os.path.join(output, i+".dll"))
		os.mkdir(os.path.join(output, "platforms"))
		shutil.copyfile(os.path.join(g_qt5, "plugins", "platforms", "qwindows.dll"), os.path.join(output, "platforms", "qwindows.dll"))
		
		
	os.chdir(prev)

def Main():
	FindDepencies()

	Clean()
	os.mkdir("workspace")
	os.mkdir("workspace\\build")

	FetchCitra()
	DoCMake()
	DoCompile()

	shutil.make_archive("Citra", 'zip', "workspace\\build\\bin")
if __name__ == "__main__":
	if len(sys.argv) >= 2:
		for i in sys.arg[1:]:
			if i.lower() == "no-qt":
				g_enable_QT = False
			if i.lower() == "debug":
				g_debugbuild = True
	Main()