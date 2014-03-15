#!/usr/bin/python3

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
  NORMAL = 0
  EMPTY = 1
  MY_HEADER = 2
  def __init__ (self, groupType, priority, name, regex, sort, keepVSpace, keepDup):
    self.groupType = groupType
    self.priority = priority
    self.name = name
    self.regex = re.compile (regex)
    self.sort = sort
    self.keepVSpace = keepVSpace
    self.keepDup = keepDup
    self.checkRules ()
  def setId (self, groupId):
    self.groupId = groupId
  def isEmpty (self):
    return self.groupType == self.EMPTY
  def checkRules (self):
    if self.groupType == self.NORMAL:
      if self.sort and self.keepVSpace:
        raise RuntimeError ('sort and keepVSpace rules are incompatible')
  def matches (self, line, filename):
    if self.groupType == self.NORMAL:
      return re.match (self.regex, line)
    elif self.groupType == self.EMPTY:
      return line.isspace ()
    elif self.groupType == self.MY_HEADER:
      return re.match (r' *# *include *".*\b{0}\.h"'.format (os.path.splitext (filename)[0]), line)

groupProperties = [GroupProperties (GroupProperties.EMPTY    , 4, 'Empty'   , r''                          , False, False, False),
                   GroupProperties (GroupProperties.MY_HEADER, 3, 'MyHeader', r''                          , False, False, False),
                   GroupProperties (GroupProperties.NORMAL   , 2, 'CStd'    , r' *# *include *<.+\.h>'     , True , False, False),
                   GroupProperties (GroupProperties.NORMAL   , 2, 'C++Std'  , r' *# *include *<[a-z_0-9]+>', True , False, False),
                   GroupProperties (GroupProperties.NORMAL   , 2, 'Qt'      , r' *# *include *<Q.+>'       , True , False, False),
                   GroupProperties (GroupProperties.NORMAL   , 1, 'OtherLib', r' *# *include *<.+>'        , False, True , False),
                   GroupProperties (GroupProperties.NORMAL   , 2, 'Local'   , r' *# *include *".+"'        , False, True , False)]

for iGroup, props in enumerate (groupProperties):
  props.setId (iGroup)

groupPropertiesByPriority = sorted (groupProperties, key = lambda props: -props.priority)

anyIncludeRegex = re.compile (r' *# *include')

def classifyLine (line, filename):
  matchingProps = None
  for props in groupPropertiesByPriority:
    if matchingProps != None and props.priority < matchingProps.priority:
      return matchingProps
    if props.matches (line, filename):
      if matchingProps != None:
        raise RuntimeError ('  Line \n  {0}  matches both "{1}" and "{2}" rules'.format (line, matchingProps.name, props.name))
      matchingProps = props
  return matchingProps

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
    if not lineGroup.isEmpty ():
      chunk.trailingEmptyLines = 0
      chunk.groups[lineGroup.groupId].addLine (line)
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
  print ('Entering folder "{0}"'.format (root))
  # TODO: Also print `Leaving folder' message with stas ('{0} files found, {1} changed, {2} were lock for writing'); do not write locked for writing messages
  for relname in files:
    if not re.match (filenameMask, relname):
      continue
    filename = os.path.join (root, relname)
    try:
      f = open (filename, 'r')
      oldContent = f.readlines ()
      newContent = []
      chunk = None
      for line in oldContent:
        lineGroup = classifyLine (line, relname)
        isMatch = (lineGroup != None)
        if lineGroup == None and re.match (anyIncludeRegex, line):
          raise RuntimeError ('  Line \n  {0}  contains an #include, but doesn\'t match any known include group'.format (line))
        if isMatch and (chunk or not lineGroup.isEmpty ()):
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
      except:
        print (' File "{0}" is locked for writing'.format (filename))
    except RuntimeError as err:
      print (' ERROR in file "{0}":\n{1}'.format (filename, err))
    except Exception as ex:
      print (' Unknown ERROR in file "{0}":'.format (filename))
      raise ex
