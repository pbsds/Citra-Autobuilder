import os, sys

enable_QT = False

if os.path.exists("workspace"):
	print "deleting old workspace..."
	print os.system("rmdir /s /q workspace")

os.mkdir("workspace")
os.mkdir("workspace\\build")
#check if git is available:
if not os.system("git version"):
	git = "git"
else:
	for i in ("%PROGRAMFILES%", "%PROGRAMFILES(X86)%"):
		if os.path.isfile(os.path.join(i, "Git\\bin\\git.exe")):
			git = os.path.join(i, "Git\\bin\\git.exe")
			break
	else:
		print "Git not found, exiting..."
		sys.exit(1)
#check if CMake is available:
for i in ("%PROGRAMFILES%", "%PROGRAMFILES(X86)%"):
	if os.path.isfile(os.path.join(i, "CMake\\bin\\cmake.exe")):
		cmake = os.path.join(i, "CMake\\bin\\cmake.exe")
		break
else:
	print "CMake not found, exiting..."
	#cmake = "C:\Program Files (x86)\CMake\bin\cmake.exe"
	sys.exit(1)
#check if Microsoft Visual Studio 12.0 2013 is available:
for i in ("%PROGRAMFILES%", "%PROGRAMFILES(X86)%"):
	if os.path.isfile(os.path.join(i, "Microsoft Visual Studio 12.0 2013\\VC\\bin\\link.exe")):
		MVScompiler = os.path.join(i, "Microsoft Visual Studio 12.0 2013\\VC\\bin")
		break
else:
	print "Microsoft Visual Studio 12.0 2013 not found, exiting..."
	#MVScompiler = "D:/Programs x32/Microsoft Visual Studio 12.0 2013/VC/bin/link.exe"
	sys.exit(1)
	


#helpers:
def FetchCitra():
	global git
	prev = os.getcwd()
	os.chdir("workspace")
	
	#clone
	ret = os.system("%s clone --recursive https://github.com/citra-emu/citra.git" % git)
	if not os.path.exists("citra") or ret:
		os.chdir(prev)
		print "Couldn't clone citra repository! Exiting..."
		sys.exit(1)
	
	os.chdir(prev)

def DoCMake():
	global cmake, enable_QT, MVScompiler
	prev = os.getcwd()
	os.chdir("workspace/build")
	
	#setup
	
	print "Generating CMake..."
	if not os.system("\"%s\" \"%s\"" % (cmake, os.path.join(prev, "workspace\\citra"))):
		print "ech"
	
		#configure
		
		print "Configuring CMake..."
		f = open("CMakeCache.txt", "rb")
		Cache = f.read().replace("\r\n", "\n").replace("\r", "\n").split("\n")
		f.close()
		
		for i, line in enumerate(Cache):
			if line[:15] == "ENABLE_QT:BOOL=":
				Cache[i] = "ENABLE_QT:BOOL=" + ("ON" if enable_QT else "OFF")
			if line[:22] == "CMAKE_LINKER:FILEPATH=":
				Cache[i] = "CMAKE_LINKER:FILEPATH=" + os.path.join(MVScompiler, "link.exe").replace("\\", "/")
		
		f = open("CMakeCache.txt", "w")
		f.write("\n".join(Cache))
		f.close()
		
		#Generate:
		print "Generating CMake..."
		if not os.system("\"%s\" \"%s\"" % (cmake, os.path.join(prev, "workspace\\citra"))):
			print "CMake generation failed!"
	
#do:
FetchCitra()
DoCMake()