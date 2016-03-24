#!/usr/local/bin/python

import argparse
import sys, os
import json
import pexpect
from xml.etree import ElementTree
import subprocess
from mutation_analyser import MutationAnalyser

def readAndroidManifest(source_directory):
  manifest = ElementTree.parse(os.path.join(source_directory, 'AndroidManifest.xml')).getroot()
  package = manifest.get('package')
  activities = manifest.find('application').findall('activity')
  for activity in activities:
    if 'android.intent.action.MAIN' in ElementTree.tostring(activity):
      start_activity = activity.get('{http://schemas.android.com/apk/res/android}name')
  start_activity = start_activity.replace(package, '')
  return package, start_activity

def compress(file_path, id):
  output = os.path.join(file_path, '{}_{}.apk'.format(file_path, id))
  command = ["./apktool", "b", os.path.join(file_path, 'src'), '-o{}'.format(output)]
  subprocess.call(command)
  return output

def decompress(file_path, is_force=False):
  source_directory = os.path.join(file_path[:-4], 'src')
  command = ["./apktool", "d", file_path, '-o%s' % source_directory]
  if is_force:
    command.append('-f')
  subprocess.call(command)
  return source_directory

def signApk(file_path):
  child = pexpect.spawn('jarsigner -verbose -keystore debug.keystore {} testKey'.format(file_path))
  child.expect('Enter Passphrase for keystore:')
  child.sendline('123456')
  child.expect('jar signed')

def instrument(file_path, line, mutant, lable_line=None, lable=None):
  with open(file_path) as f:
    content = f.readlines()
  original = list(content)
  content[line-1] = mutant
  if lable_line != None:
    content[lable_line-1] = lable
  with open(file_path, 'w') as f:
    f.writelines(content)
  return original

def generateMutants(file):
  if not file.endswith('.apk'):
    print 'Input must be an Android Apk file!'
    sys.exit(2)
  
  source_directory = decompress(file, True)

  config = {}
  config['file'] = file[:-4]
  config['package'], config['start_activity'] = readAndroidManifest(source_directory)

  config_file = os.path.join(config['file'], 'config')

  with open(config_file, 'wb') as handle:
    json.dump(config, handle)

  path = os.path.join(source_directory, 'smali', *config['package'].split('.')) #TODO: Take paramater or read from file

  mutation_analyser = MutationAnalyser()
  mutants = mutation_analyser.checkMutations(path)
        
  print "\nNumber of mutants generated: %d\n" % len(mutants)

  mutants_list = os.path.join(config['file'], 'mutants')
  with open(mutants_list, 'wb') as handle:
    json.dump(mutants, handle)

  for m in mutants:
    if 'label' in m:
      file_original = instrument(m['file'], m['line_num'], m['mutant'], m['label_line'], m['label'])
    else:
      file_original = instrument(m['file'], m['line_num'], m['mutant'])
    new_apk_path = compress(file.split('.')[0], m['id'])
    with open(m['file'], 'w') as f:
      f.writelines(file_original)
    signApk(new_apk_path)

  return config['file']

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('apk', help='apk file')
  args = parser.parse_args()
  apk_file = args.apk

  generateMutants(apk_file)
  
