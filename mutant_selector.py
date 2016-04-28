import random

class MutantsSelector:
  invert_ror_dict = {}
  boundary_ror_dict = {}
  invert_aor_dict = {}

  def randomSampling(self, mutants):
    result = random.sample(mutants, len(mutants)/10)
    return result

  def inlineRandomSmali(self, mutants):
    result = []
    keys = {}
    for m in mutants:
      if not m['line_num'] in keys:
        keys[m['line_num']] = [m]
      else:
        keys[m['line_num']].append(m)

    for k in keys:
      r = random.randint(0, len(keys[k])-1)
      # print r, len(keys[k])
      result.append(keys[k][r])
      # print k, keys[k]
    return result

  def inlineRandomSource(self, mutants):
    result = []
    keys = {}
    for m in mutants:
      if not m['ori_line_num'] in keys:
        keys[m['ori_line_num']] = [m]
      else:
        keys[m['ori_line_num']].append(m)

    for k in keys:
      r = random.randint(0, len(keys[k])-1)
      # print r, len(keys[k])
      result.append(keys[k][r])
      # print k, keys[k]
    return result

  def equalization(self, mutants):
    result = []
    keys = {}
    numbers = {}
    for m in mutants:
      if not m['operator_type'] in numbers:
        numbers[m['operator_type']] = 1
      else:
        numbers[m['operator_type']] += 1
      if not m['ori_line_num'] in keys:
        keys[m['ori_line_num']] = [m]
      else:
        keys[m['ori_line_num']].append(m)

    # print numbers
    for k in keys:
      v =  keys[k]
      least = v[0]
      if len(v) > 1:
        for mutant in v[1:]:
          if numbers[least['operator_type']] > numbers[mutant['operator_type']]:
            numbers[least['operator_type']] -= 1
            least = mutant
          else:
            numbers[mutant['operator_type']] -= 1
      result.append(least)

    # print numbers
    return result

  def patternSelection(self, mutants):
    self.initDict()
    result = []
    for m in mutants:
      if m['operator_type'] == 'ROR':
        if self.isInvertROR(m) or self.isBoundaryROR(m):
          result.append(m)
      elif m['operator_type'] == 'AOR':
        if self.isInvertAOR(m):
          result.append(m)
      else:
        result.append(m)
    return result

  def addTwoWayDict(self, d, k, v):
    d[k] = v
    d[v] = k

  def initDict(self):
    operators_ror = ['if-lt', 'if-ge', 'if-gt', 'if-le', 'if-eq', 'if-ne']
    inverts_ror = ['if-ge', 'if-lt', 'if-le', 'if-gt', 'if-ne', 'if-eq']
    boundary_ror = ['if-le', 'if-gt', 'if-ge', 'if-lt']
    for i in range(len(operators_ror)):
      self.addTwoWayDict(self.invert_ror_dict, operators_ror[i], inverts_ror[i])
      self.addTwoWayDict(self.invert_ror_dict, operators_ror[i]+'z', inverts_ror[i]+'z')
      if i < len(boundary_ror):
        self.addTwoWayDict(self.boundary_ror_dict, operators_ror[i], boundary_ror[i])
        self.addTwoWayDict(self.boundary_ror_dict, operators_ror[i]+'z', boundary_ror[i]+'z')
    # print self.invert_ror_dict
    # print self.boundary_ror_dict

    operators_aor = ['add', 'sub', 'mul', 'div', 'rem']
    inverts_aor = ['sub', 'add', 'div', 'mul', 'mul']
    for i in range(len(operators_aor)):
      self.addTwoWayDict(self.invert_aor_dict, operators_aor[i], inverts_aor[i])

    # print self.invert_aor_dict
    

  def isInvertROR(self, mutant):
    ori_operator = mutant['line'].strip().split(' ')[0]
    mutant_operator = mutant['mutant'].strip().split(' ')[0]
    if self.invert_ror_dict[ori_operator] == mutant_operator:
      # print ori_operator, mutant_operator
      return True
    return False

  def isBoundaryROR(self, mutant):
    ori_operator = mutant['line'].strip().split(' ')[0]
    mutant_operator = mutant['mutant'].strip().split(' ')[0]
    if (ori_operator in self.boundary_ror_dict) and (self.boundary_ror_dict[ori_operator] == mutant_operator):
      # print ori_operator, mutant_operator
      return True
    return False

  def isInvertAOR(self, mutant):
    ori_operator = mutant['line'].strip().split('-')[0]
    mutant_operator = mutant['mutant'].strip().split('-')[0]
    # print ori_operator, mutant_operator
    if ori_operator == 'rsub':
      ori_operator = 'sub'
    if self.invert_aor_dict[ori_operator] in mutant_operator:
      # print ori_operator, mutant_operator
      return True
    return False

