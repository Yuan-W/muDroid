import unittest

from mutation_analyser import MutationAnalyser

class MutantionAnalyzerTest(unittest.TestCase):
  def testFloatConst(self):
    mutation_analyser = MutationAnalyser()
    test_line = 'const/high16 v2, 0x40e00000    # 7.0f'
    mutation = mutation_analyser.processConst(test_line)
    result = 'const/high16 v2, 0x41000000    # 7.0f'
    self.assertEqual(mutation, result)

  def testIntegerConst(self):
    mutation_analyser = MutationAnalyser()
    test_line = 'const/16 v0, 0x8'
    mutation = mutation_analyser.processConst(test_line)
    result = 'const/16 v0, 0x9'
    self.assertEqual(mutation, result)

  def testShortIntegerConst(self):
    mutation_analyser = MutationAnalyser()
    test_line = 'const/4 v0, 0x7'
    mutation = mutation_analyser.processConst(test_line)
    result = 'const/4 v0, -0x8'
    self.assertEqual(mutation, result)

  def testDoubleHigh16Const(self):
    mutation_analyser = MutationAnalyser()
    test_line = 'const-wide/high16 v4, 0x4059000000000000L    # 100.0'
    mutation = mutation_analyser.processConst(test_line)
    result = 'const-wide v4, 0x4059400000000000L    # 100.0'
    self.assertEqual(mutation, result)

  def testZeroDoubleConst(self):
    mutation_analyser = MutationAnalyser()
    test_line = 'const-wide/high16 v4, 0x0000000000000000L    # 0.0'
    mutation = mutation_analyser.processConst(test_line)
    result = 'const-wide/high16 v4, 0x3ff0000000000000L    # 0.0'
    self.assertEqual(mutation, result)

  def testDoubleConst(self):
    mutation_analyser = MutationAnalyser()
    test_line = 'const-wide/high16 v4, 0x4020000000000000L    # 8.0'
    mutation = mutation_analyser.processConst(test_line)
    result = 'const-wide/high16 v4, 0x4022000000000000L    # 8.0'
    self.assertEqual(mutation, result)

  def testNormalAOR(self):
    mutation_analyser = MutationAnalyser()
    key = {'line':'add-int/lit8 v8, v8, -0x2', 'operator':'add-'}
    result = mutation_analyser.processAOR(key)
    self.assertEqual(4, len(result))
    no_add = False
    for m in result:
      no_add = not 'add-' in m['mutant']
      if not no_add:
        break
    self.assertEqual(no_add, True)    

  def testRsubAOR(self):
    mutation_analyser = MutationAnalyser()
    key = {'line':'rsub-int v8, v8, -0x2', 'operator':'rsub-'}
    result = mutation_analyser.processAOR(key)
    self.assertEqual(4, len(result))
    with_lit16 = False
    for m in result:
      with_lit16 = 'lit16' in m['mutant']
      self.assertEqual(with_lit16, True)

  def testNormalLit16AOR(self):
    mutation_analyser = MutationAnalyser()
    key = {'line':'add-int/lit16 v8, v8, -0x2', 'operator':'add-'}
    result = mutation_analyser.processAOR(key)
    self.assertEqual(4, len(result))
    no_add = False
    for m in result:
      no_add = not 'add-' in m['mutant']
      self.assertEqual(no_add, True)
      if 'rsub-' in m['mutant']:
        self.assertEqual('lit16' not in m['mutant'], True)
    

if __name__ == '__main__':
  unittest.main()