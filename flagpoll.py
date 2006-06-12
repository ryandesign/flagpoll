#    -----------------------------------------------------------------
#
#    Flag Poll: A tool to extract flags from installed applications
#    for compiling, settting variables, etc.
#
#    Original Authors:
#       Daniel E. Shipton <dshipton@gmail.com>
#
#    Flag Poll is Copyright (C) 2006 by Daniel E. Shipton
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to:
#    Free SoftwareFoundation, Inc.
#    51 Franklin Street, Fifth Floor, 
#    Boston, MA  02110-1301  USA
#
#    -----------------------------------------------------------------




from optparse import OptionParser
from string import Template
import sys
import os
import glob

def GetFlagpollVersion():
   FLAGPOLL_MAJOR_VERSION = 0
   FLAGPOLL_MINOR_VERSION = 1
   FLAGPOLL_PATCH_VERSION = 1
   return ( FLAGPOLL_MAJOR_VERSION, FLAGPOLL_MINOR_VERSION, FLAGPOLL_PATCH_VERSION )

def GetOptionParser():
   parser = OptionParser()
   parser.add_option("--modversion", action="store_true", dest="modversion", help="output version for package")
   parser.add_option("--version", action="store_true", dest="version", help="output version of pkg-config")
   parser.add_option("--libs", action="store_true", dest="libs", help="output all linker flags")
   parser.add_option("--static", action="store_true", dest="static", help="output linker flags for static linking")
   parser.add_option("--short-errors", action="store_true", dest="short_errors", help="print short errors")
   parser.add_option("--libs-only-l", action="store_true", dest="libs_only_l", help="output -l flags")
   parser.add_option("--libs-only-other", action="store_true", dest="libs_only_other", help="output other libs (e.g. -pthread)")
   parser.add_option("--libs-only-L", action="store_true", dest="libs_only_L", help="output -L flags")
   parser.add_option("--cflags", action="store_true", dest="cflags", help="output all pre-processor and compiler flags")
   parser.add_option("--cflags-only-I", action="store_true", dest="cflags_only_I", help="output -I flags")
   parser.add_option("--cflags-only-other ", action="store_true", dest="cflags_only_other", help="output cflags not covered by the cflags-only-I option")
   parser.add_option("--exists", action="store_true", dest="exists", help="return 0 if the module(s) exist")
   parser.add_option("--list-all", action="store_true", dest="list_all", help="list all known packages")
   parser.add_option("--debug", action="store_true", dest="debug", help="show verbose debug information")
   parser.add_option("--print-errors", action="store_true", dest="print_errors", help="show verbose information about missing or conflicting packages")
   parser.add_option("--silence-errors", action="store_true", dest="silence_errors", help="show no information about missing or conflicting packages")
   parser.add_option("--uninstalled", action="store_true", dest="uninstalled", help="return 0 if the uninstalled version of one or more module(s) or their dependencies will be used")
   parser.add_option("--errors-to-stdout", action="store_true", dest="errors_to_stdout", help="print errors from --print-errors to stdout not stderr")
   parser.add_option("--print-provides", action="store_true", dest="print_provides", help="print which packages the package provides")
   parser.add_option("--print-requires", action="store_true", dest="print_requires", help="print which packages the package requires")
   parser.add_option("--atleast-version", dest="atleast_version", help="return 0 if the module is at least version VERSION")
   parser.add_option("--exact-version", dest="exact_version", help="return 0 if the module is exactly version VERSION")
   parser.add_option("--max-version", dest="max_version", help="return 0 if the module is at no newer than version VERSION")
   parser.add_option("--atleast-pkgconfig-version=VERSION", dest="atleast_pkgconfig_version", help="require given version of pkg-config")
   parser.add_option("--variable", dest="variable", help="get the value of a variable")
   parser.add_option("--define-variable", dest="define_variable", help="set the value of a variable")
   return parser

def GetPathList():
   return ["/usr/lib64/pkgconfig", "/usr/lib/pkgconfig", "/usr/share/pkgconfig"]



class PkgDB:
   """ Holds all the neccesary information to evaluate itself when needed.
   """

   def __init__(self):
      self.mPkgInfoList = []
      self.PopulatePkgInfoDB()

   def BuildPcFileDict(self):
      """ Builds up a dictionary of {name: list of files for name} """
      pc_dict = {}
      for p in GetPathList():
         glob_list = glob.glob(os.path.join(p, "*.pc")) # List of .pc files in that directory
         for g in glob_list: # Get key name and add file to value list in dictionary
            key = os.path.basename(g)[:-3] # Strip .pc off the filename
            if pc_dict.has_key(key):
               pc_dict[key].append(g)
            else:
               pc_dict[key]=[g]
      
      return pc_dict # { "key", [ "list", "of", "corresponding", "pc", "files"] }

   def PopulatePkgInfoDB(self):
      print "populating db"
      dict_to_pop_from = self.BuildPcFileDict()
      for pkg in dict_to_pop_from:
         print "adding: " + str(pkg)
         self.mPkgInfoList.append(PkgInfo(pkg[0],pkg[1]))

class PkgInfo:
   """ Holds the information for a package file on the system. These however
       are evaluated when the need arises.
   """

   def __init__(self, name, fileList):
      self.mName = name
      self.mFileList = fileList
      self.mIsEvaluated = False
      self.mVariableList = []

   def evaluate(self):
      # Currently only evaluates first file
      if !self.mIsEvaluated:
         self.mVariableList.extend(parse(self.mFileList[0]))
      return self.mVariableList
   
   def parse(filename):
      lines = open(filename).readlines()
      vars = {}
      locals = {}
      for line in lines:
       line = line.strip()
       if not line:
         continue
       elif ':' in line: # exported variable
         name, val = line.split(':')
         val = val.strip()
         if '$' in val:
           try:
             val = Template(val).substitute(locals)
           except ValueError:
             raise ValueError("Error in variable substitution!")
         vars[name] = val
       elif '=' in line: # local variable
         name, val = line.split('=')
         if '$' in val:
           try:
             val = Template(val).substitute(locals)
           except ValueError:
             raise ValueError("Error in variable substitution!")
         locals[name] = val
      return vars

   def GetVariables(name, pc_dict):
      if pc_dict.has_key(name):
         list_of_files = pc_dict[name]
         for f in list_of_files:
            print parse(f)

option_parser = GetOptionParser()
(options, args) = option_parser.parse_args()

if options.version:
   print "%s.%s.%s" % GetFlagpollVersion()
   sys.exit(0)

myPkgDB = PkgDB()

#my_pc_dict = BuildPcFileDict()

#if options.cflags:
#   GetVariables(args[0], my_pc_dict)


#if options.debug:
#   print my_pc_dict
