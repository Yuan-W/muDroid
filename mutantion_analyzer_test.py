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

  def testDoubleHigh16IntegerConst(self):
    mutation_analyser = MutationAnalyser()
    test_line = 'const-wide/high16 v4, 0x4059000000000000L    # 100.0'
    mutation = mutation_analyser.processConst(test_line)
    result = 'const-wide v4, 0x4059400000000000L    # 100.0'
    self.assertEqual(mutation, result)

  def testZeroDoubleIntegerConst(self):
    mutation_analyser = MutationAnalyser()
    test_line = 'const-wide/high16 v4, 0x0000000000000000L    # 0.0'
    mutation = mutation_analyser.processConst(test_line)
    result = 'const-wide/high16 v4, 0x3ff0000000000000L    # 0.0'
    self.assertEqual(mutation, result)

  def testDoubleIntegerConst(self):
    mutation_analyser = MutationAnalyser()
    test_line = 'const-wide/high16 v4, 0x0000000000000000L    # 0.0'
    mutation = mutation_analyser.processConst(test_line)
    result = 'const-wide/high16 v4, 0x3ff0000000000000L    # 0.0'
    self.assertEqual(mutation, result)

if __name__ == '__main__':
    unittest.main()