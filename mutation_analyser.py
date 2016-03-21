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

  methodConds={}

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
    lcr_keys = []
    method = ''
    section = ''
    indent = ' '*20
    sec_num = 1
    max_conds = -1
    with open(file_path, 'r') as f:
      for num, line in enumerate(f, 1):
        if '.method' in line:
          method = line
          max_conds = -1
        elif '.end method' in line:
          if max_conds >=0:
            hashkey = file_path+':'+method
            self.methodConds[hashkey]=max_conds
        elif ':cond' in line:
          cond_num = int(re.search(':cond_([0-9]*)', line).group(1))
          if cond_num > max_conds:
            max_conds = cond_num
          # print line, cond_num, max_conds
        elif '.line' in line:
          indent = line.split('.')[0]
          lcr_match = re.findall(self.logicalConnector['operators'][0], section)
          if(len(lcr_match) == 2):
            lcr_keys.append({'file': file_path, 'section': section, 'line_num': sec_num, 'operator': self.logicalConnector['operators'][0], 'operator_type': self.LCR, 'method': method, 'killed': False})
            # mutants += self.generateMutants(original_key)
            # print original_key
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
      lcr_keys.append({'file': file_path, 'section': section, 'line_num': sec_num, 'operator': o, 'operator_type': self.LCR, 'method': method, 'killed': False})
    for key in lcr_keys:
      mutants += self.generateMutants(key)
    return mutants

  def newMutant(self, key, content):
    mutant = key.copy()
    mutant['id'] = self.id
    self.id = self.id + 1
    mutant['mutant'] = content
    return mutant

  def generateMutants(self, key):
    operator_type = key['operator_type']

    if operator_type == self.UOI:
      return [self.newMutant(key, key['line']*2)]
    elif operator_type == self.LCR:
      return [self.processLCR(key)]
    elif operator_type == self.ICR:
      old, new = self.processConst(key['line'])
      return [self.newMutant(key, key['line'].replace(old, new))]
    elif operator_type == self.RVR:
      return [self.newMutant(key, 'return-void')]
    elif operator_type == self.AOR:
      return self.processAOR(key)
    else: #ROR
      results = []
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
        if '/4' in line and value == 7:
          new_value = '-0x8'
        else:
          new_value = hex(value+1)
        
    if neg:
      new_value = '-'+new_value
    return value_raw, new_value
  
  def processAOR(self, key):
    operators = self.arithmeticOperator['operators']
    results = []
    if key['operator'] == 'rsub-':
        rev_line = key['line']
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
      rev_line = key['line']
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

    split_line[2] = split_line[2].strip()

    if split_line[2][0] == '-':
      split_line[2] = split_line[2][1:]
    else:
      split_line[2] = '-'+split_line[2]

    inv_line = ','.join(split_line)
    return inv_line

  def processLCR(self, key):
    match = re.findall(self.logicalConnector['operators'][0], key['section'])
    section_start = key['line_num']
    first_line = match[0][0] + match[0][2]
    splitted_lines = (key['section'].split('\n'))
    for s in splitted_lines:
      # print repr(s.strip())
      if(s.strip() == first_line):
        key['line'] = s+'\n'
        break
      key['line_num'] = key['line_num'] + 1

    # || to &&
    if(match[0][1] != match[1][1]): 
      replacement = key['line'].replace(match[0][2], match[1][2])
      if('nez') in replacement:
        replacement = replacement.replace('nez','eqz')
      else:
        replacement = replacement.replace('eqz','nez')
      return self.newMutant(key, replacement)

    # && to ||
    else:
      hashkey = key['file']+':'+key['method']
      cond_num = self.methodConds[hashkey] + 1
      replacement = key['line'].replace(match[0][2], ':cond_%d' % cond_num)
      new_mutant = self.newMutant(key, replacement)
      second_line = match[1][0] + match[1][2]
      second_line_num = key['line_num']
      diff = key['line_num'] - section_start
      indent = ''
      for i in range(diff, len(splitted_lines)):
        if splitted_lines[i].strip() == second_line:
          indent = splitted_lines[i].split('if')[0]
          break
        second_line_num += 1
      new_mutant['label_line'] = second_line_num + 1
      new_mutant['label'] = '%s:cond_%d\n' % (indent, cond_num)
      # print new_mutant['label_line'], new_mutant['lable']
      return new_mutant