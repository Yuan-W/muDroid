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
  logicalConnector={'name':LCR, 'operators':['((if-nez|if-eqz).*)(:.*)']}

  arithmeticOperator={'name':AOR, 'operators':['add-', 'rsub-', 'sub-', 'div-', 'mul-', 'rem-']}
  relationalOperator={'name':ROR, 'operators':['if-eq', 'if-ne', 'if-lt', 'if-ge', 'if-gt', 'if-le']} 
  #TODO: Verify if-eqz will be used when b is 0 in a == b
  
  unaryOperator={'name':UOI, 'operators':['not-', 'neg-']} # TODO: a=!b
  returnOperator={'name':RVR, 'operators':['return-object', 'return v']}

  mutation_operators = [arithmeticOperator, relationalOperator, unaryOperator, valueOperator, returnOperator]

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
    section = ''
    indent = ' '*20
    sec_num = 1
    with open(file_path, 'r') as f:
      for num, line in enumerate(f, 1):
        if '.method' in line:
          method = line
        if '.line' in line:
          indent = line.split('.')[0]
          lcr_match = re.findall(self.logicalConnector['operators'][0], section)
          if(len(lcr_match) == 2):
            # print '*'*40
            # print section
            # print '*'*40
            original_key = {'file': file_path, 'section': section, 'line_num': sec_num, 'operator': self.logicalConnector['operators'][0], 'operator_type': self.LCR, 'method': method, 'killed': False}
            mutants += self.generateMutants(original_key)
            print original_key
          sec_num = num
          section = ''
        if line.startswith(indent) or line == '\n':
          section = section + line
        for operator in self.mutation_operators:
          if operator['name'] == self.ICR:
            for o in operator['operators']:
              if re.match(o, line):
                if not ('string' in line or 'Y' in line):
                  original_key = {'file': file_path, 'line': line, 'line_num': num, 'operator': o, 'operator_type': operator['name'], 'method': method, 'killed': False}
                  mutants += self.generateMutants(original_key)    
          else:
            for o in operator['operators']:
              if o in line:
                original_key = {'file': file_path, 'line': line, 'line_num': num, 'operator': o, 'operator_type': operator['name'], 'method': method, 'killed': False}
                mutants += self.generateMutants(original_key)
                break
    lcr_match = re.findall(self.logicalConnector['operators'][0], section)
    if(len(lcr_match) == 2):
      original_key = {'file': file_path, 'section': section, 'line_num': sec_num, 'operator': o, 'operator_type': self.LCR, 'method': method, 'killed': False}
      mutants += self.generateMutants(original_key)
    return mutants

  def newMutant(self, key, content):
    mutant = key.copy()
    mutant['id'] = self.id
    self.id = self.id + 1
    mutant['mutant'] = content
    return mutant

  def generateMutants(self, key):
    results = []
    operator_type = key['operator_type']

    # if operator_type != self.LCR:
    #   return []

    if operator_type == self.UOI:
      results.append(self.newMutant(key, key['line']*2))
    elif operator_type == self.LCR:
      print '-'*20
      match = re.findall(self.logicalConnector['operators'][0], key['section'])
      first_line = match[0][0] + match[0][2]
      for s in (key['section'].split('\n')):
        # print repr(s.strip())
        if(s.strip() == first_line):
          key['line'] = s+'\n'
          break
        key['line_num'] = key['line_num'] + 1
      if(match[0][1] != match[1][1]):
        replacement = key['line'].replace(match[0][2], match[1][2])
        if('nez') in replacement:
          replacement = replacement.replace('nez','eqz')
        else:
          replacement = replacement.replace('eqz','nez')
        results.append(self.newMutant(key, replacement))
      else:
        return []

      print '-'*20
      
      # if key['operator'] == 'if-nez':
      #   results.append(self.newMutant(key, key['line'].replace(key['operator'], 'if-eqz')))
      # elif key['operator'] == 'if-eqz':
      #   results.append(self.newMutant(key, key['line'].replace(key['operator'], 'if-nez')))
    elif operator_type == self.ICR:
      old, new = self.processConst(key['line'])
      results.append(self.newMutant(key, key['line'].replace(old, new)))
    elif operator_type == self.RVR:
      results.append(self.newMutant(key, 'return-void'))
    elif operator_type == self.AOR:
      return self.processAOR(key)
    else: #ROR
      mutants = [operator for operator in self.relationalOperator['operators'] if operator != key['operator']]
      for mutant in mutants:
        results.append(self.newMutant(key, key['line'].replace(key['operator'], mutant)))
    return results

  def processConst(self, line):
    neg = False
    value_raw = line.split(',')[-1].split(' ')[1].strip()
    if value_raw[0] == '-':
      neg = True
      value_raw = value_raw[1:]
    # print line, value_raw
    if('#' in line):
      if('L' in line):
        value = struct.unpack('!d', value_raw[2:][:-1].decode("hex"))[0]
        if(value != 0):
          new_value = hex(struct.unpack('<Q', struct.pack('<d', value+1))[0])+'L'
        else:
          new_value = '0x3ff0000000000000L' # 1.0
      elif('f' in line):
        value = struct.unpack('!f', value_raw[2:].decode("hex"))[0]
        if(value != 0):
          new_value = hex(struct.unpack('<I', struct.pack('<f', value+1))[0])
        else:
          new_value = '0x3f800000' # 1.0
    else:
      value = int(value_raw, 16)
      if(value == 0):
        new_value = '0x1'
      elif(value == 1):
        new_value = '0x0'
      else:
        new_value = hex(value+1)
        
    if neg:
      new_value = '-'+new_value
    return value_raw, new_value
  
  def processAOR(self, key):
    operators = self.arithmeticOperator['operators']
    results = []
    if key['operator'] == 'rsub-':
        rev_line = self.invertVariables(key['line'])
        mutants = [operator for operator in operators if (operator != key['operator'] and operator != 'sub-')]
        op = key['operator']
        if 'lit' not in key['line']:
          print '*'*40
          op = 'rsub-int'
          mutants = [m + 'int/lit16' for m in mutants]
        for mutant in mutants:
          results.append(self.newMutant(key, rev_line.replace(op, mutant)))
    elif 'lit' in key['line']:
      mutants = [operator for operator in operators if operator not in [key['operator'], 'sub-', 'rsub-']]
      for mutant in mutants:
        results.append(self.newMutant(key, key['line'].replace(key['operator'], mutant)))
      rev_line = self.invertVariables(key['line'])
      if 'lit16' in key['line']:
        results.append(self.newMutant(key, rev_line.replace(key['operator'], 'rsub-').replace('/lit16', '')))
      else:
        results.append(self.newMutant(key, rev_line.replace(key['operator'], 'rsub-')))
    else:
      mutants = [operator for operator in operators if (operator != key['operator'] and operator != 'rsub-')]
      for mutant in mutants:
        results.append(self.newMutant(key, key['line'].replace(key['operator'], mutant)))
    
    return results

  def invertVariables(self, line):
    split_line = line.split(',')

    split_line[1] = split_line[1].strip()
    split_line[2] = split_line[2].strip()
    if split_line[1][0] == '-':
      split_line[1] = split_line[1][1:]
    else:
      split_line[1] = '-'+split_line[1]

    if split_line[2][0] == '-':
      split_line[2] = split_line[2][1:]
    else:
      split_line[2] = '-'+split_line[2]

    rev_line = ','.join(split_line)
    return rev_line