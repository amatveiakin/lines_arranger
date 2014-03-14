#!/usr/bin/python3

# TODO: Keep self .h file header on top!

import argparse
import os
import re


parser = argparse.ArgumentParser ()
parser.add_argument ('source_folder', help='source files root folder')
args = parser.parse_args ()

srcRoot = args.source_folder

if not os.path.isdir (srcRoot):
  print ('Folder doesn\'t exist: ' + srcRoot)
  exit (1)


# TODO: Make it configurable
filenameMask = re.compile (r'.*\.(h|hpp|c|cpp|php)$')

class GroupProperties:
  def __init__ (self, name, regex, sort, keepVSpace, keepDup):
    self.name = name
    self.regex = re.compile (regex)
    self.sort = sort
    self.keepVSpace = keepVSpace
    self.keepDup = keepDup
    self.checkRules ()
  def checkRules (self):
    if self.sort and self.keepVSpace:
      raise RuntimeError ('sort and keepVSpace rules are incompatible')

groupProperties = [GroupProperties ('Empty', r' *$'                       , False, False, False),
                   GroupProperties ('C'    , r' *# *include *<.+\.h>'     , True , False, False),
                   GroupProperties ('C++'  , r' *# *include *<[a-z_0-9]+>', True , False, False),
                   GroupProperties ('Qt'   , r' *# *include *<Q.+>'       , True , False, False),
                   GroupProperties ('Local', r' *# *include *".*"'        , False, True , False)]

emptyGroupId = 0
anyIncludeRegex = re.compile (r' *# *include')

def classifyLine (line):
  matchingGroup = None
  for iGroup, props in enumerate (groupProperties):
    if re.match (props.regex, line):
      if matchingGroup != None:
        raise RuntimeError ('Line \n' + line + '\n matches both "' + matchingGroup + '" and "' + str (i) + '" rules')
      matchingGroup = iGroup
  return matchingGroup

class Group:
  def __init__ (self, props):
    self.props = props
    self.lines = []
    self.lineSet = set ()
  def addLine (self, line):
    if self.props.keepDup or (line not in self.lineSet):
      self.lines.append (line)
      self.lineSet.add (line)
  def addEmptyLine (self):
    if self.lines and self.lines[-1] != '\n' and self.props.keepVSpace:
      self.lines.append ('\n')
  def printGroup (self):
    if self.props.sort:
      self.lines.sort ()
    while self.lines and self.lines[-1] == '\n':
      self.lines = self.lines[:-1]
    return ''.join (self.lines)

class Chunk:
  def __init__ (self):
    self.trailingEmptyLines = 0
    self.groups = [Group (props) for props in groupProperties]
  def addLine (self, line, lineGroup):
    isEmpty = (lineGroup == emptyGroupId)
    if not isEmpty:
      chunk.trailingEmptyLines = 0
      chunk.groups[lineGroup].addLine (line)
    else:
      for gr in self.groups:
        gr.addEmptyLine ()
      chunk.trailingEmptyLines += 1
  def printChunk (self):
    allTexts = [gr.printGroup () for gr in self.groups]
    nonEmptyTexts = filter (None, allTexts)
    text = '\n'.join (nonEmptyTexts)
    trailingVSpace = '\n' * chunk.trailingEmptyLines
    return text + trailingVSpace


for root, dirs, files in os.walk (srcRoot):
  files = [f for f in files if not f.startswith ('.')]
  dirs[:] = [d for d in dirs if not d.startswith ('.')]
  for relname in files:
    if not re.match (filenameMask, relname):
      continue
    filename = os.path.join (root, relname)
    print ('Processing ' + filename + '...', end='')
    try:
      f = open (filename, 'r')
      oldContent = f.readlines ()
      newContent = []
      chunk = None
      for line in oldContent:
        lineGroup = classifyLine (line)
        isMatch = (lineGroup != None)
        isEmpty = (lineGroup == emptyGroupId)
        if lineGroup == None and re.match (anyIncludeRegex, line):
          raise RuntimeError ('Line \n' + line + '\n contains an #include, but doesn\'t match any known include group')
        if isMatch and (chunk or not isEmpty):
          if not chunk:
            chunk = Chunk ()
          chunk.addLine (line, lineGroup)
        else:
          if chunk:
            newContent += chunk.printChunk ()
            chunk = None
          newContent.append (line)
      f.close ()
      try:
        f = open (filename, 'w')
        f.writelines (newContent)
        f.close ()
        print (' Done.')
      except:
        print (' Locked.')
    except RuntimeError as err:
      print (' ERROR: {0}'.format (err))
    except:
      print (' Unknown ERROR')
