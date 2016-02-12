#!/usr/bin/python

import os
import re
import struct

class MutationAnalyser:

  ICR = 'ICR' #'Inline Constant Replacement'
  UOI = 'UOI' #'Unary Operator Insertion'
  LCR = 'LCR' #'Logical Connector Replacement'
  AOR = 'AOR' #'Arithmetic Operator Replacement'
  ROR = 'ROR' #'Relational Operator Replacement'
  RVR = 'RVR' #'Return Value Replacement'

  valueOperator = {'name':ICR, 'operators':['\s*const.*\/.*#.*', '\s*const/(4|16)']}
  logicalConnector={'name':LCR, 'operators':['if-eqz|if-nez']}

  arithmeticOperator={'name':AOR, 'operators':['add-', 'rsub-', 'div-', 'mul-', 'rem-']}
  relationalOperator={'name':ROR, 'operators':['if-eq', 'if-ne', 'if-lt', 'if-ge', 'if-gt', 'if-le']}
  
  unaryOperator={'name':UOI, 'operators':['not-', 'neg-']}
  returnOperator={'name':RVR, 'operators':['return-object', 'return v']}

  mutation_operators = [arithmeticOperator, logicalConnector, relationalOperator, unaryOperator, valueOperator, returnOperator]

  id = 1

  def checkMutations(self, directory):
    mutant_list = []
    for root, dirs, files in os.walk(directory):
      for f in files:
        if f.endswith(".smali"):
          mutant_list += self.findMutations(os.path.join(root, f))
    return mutant_list

  def findMutations(self, file_path):
    mutants = []
    method = ''
    with open(file_path) as f:
      for num, line in enumerate(f, 1):
        if '.method' in line:
          method = line
        for operator in self.mutation_operators:
          if operator['name'] == self.ICR or operator['name'] == self.LCR:
            for o in operator['operators']:
              if re.match(o, line):
                if not 'string' in line:
                  # print 'Match: ', line
                  original_key = {'file': file_path, 'line': line, 'line_num': num, 'operator': o, 'operator_type': operator['name'], 'method': method, 'killed': False}
                  mutants += self.generateMutants(original_key)    
          else:
            for o in operator['operators']:
              if o in line:
                original_key = {'file': file_path, 'line': line, 'line_num': num, 'operator': o, 'operator_type': operator['name'], 'method': method, 'killed': False}
                mutants += self.generateMutants(original_key)    
    return mutants

  def newMutant(self, key, content):
    mutant = key.copy()
    mutant['id'] = self.id
    self.id = self.id + 1
    mutant['mutant'] = content
    return mutant

  def parseConst(self, line):
    neg = False
    print line
    value_raw = line.split(',')[-1].split(' ')[1].strip()
    if value_raw[0] == '-':
      neg = True
      value_raw = value_raw[1:]
    print value_raw
    if('#' in line):
      if('L' in line):
        value = struct.unpack('!d', value_raw[2:][:-1].decode("hex"))[0]
        if(value != 0):
          new_value = hex(struct.unpack('<Q', struct.pack('<d', value+1))[0])+'L'
        else:
          new_value = '0x3ff0000000000000L' # 1.0
      else:
        value = struct.unpack('!f', value_raw[2:].decode("hex"))[0]
        if(value != 0):
          new_value = hex(struct.unpack('<I', struct.pack('<f', value+1))[0])
        else:
          new_value = '0x3f800000' # 1.0
    else:
      value = int(value_raw, 16)
      if(value != 0):
        new_value = hex(value+1)
      else:
        new_value = '0x1'
    # print value_raw
    # print new_value
    if neg:
      new_value = '-'+new_value
    return value_raw, new_value

  def generateMutants(self, key):
    results = []
    operator_type = key['operator_type']
    operators = None
    for mutation_operator in self.mutation_operators:
      if mutation_operator['name'] == operator_type:
        operators = mutation_operator['operators']
        break

    if operator_type == self.UOI:
      results.append(self.newMutant(key, key['line']*2))
    elif operator_type == self.LCR:
      return []
      # if key['operator'] == 'if-nez':
      #   results.append(self.newMutant(key, key['line'].replace(key['operator'], 'if-eqz')))
      # elif key['operator'] == 'if-eqz':
      #   results.append(self.newMutant(key, key['line'].replace(key['operator'], 'if-nez')))
    elif operator_type == self.ICR:
      old, new = self.parseConst(key['line'])
      results.append(self.newMutant(key, key['line'].replace(old, new)))
    elif operator_type == self.RVR:
      results.append(self.newMutant(key, 'return-void'))
    else: #AOR, ROR
      mutants = [operator for operator in operators if operator != key['operator']]
      for mutant in mutants:
          results.append(self.newMutant(key, key['line'].replace(key['operator'], mutant)))
    return results