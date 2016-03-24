#!/usr/local/bin/python

from xml.etree import ElementTree

class ReportGenerator():
    @staticmethod
    def writeTable(outputFile, elements, is_header=False):
        outputFile.write('<tr>\n')
        for e in elements:
            if is_header:
                outputFile.write('<th>%s</th>\n' % e)
            else:
                outputFile.write('<td>%s</td>\n' % e)
        outputFile.write('</tr>\n')

    @staticmethod
    def generateReport(mutants, report_path):
        report = open("%s/result.html" % report_path, "w")
        report.write('''<style>
        table {
            border-collapse: collapse;
        }

        table, td, th {
            border: 1px solid black;
        }
        </style>''')
        report.write('<table>\n')
        ReportGenerator.writeTable(report, ['Id', 'Operator', 'Type', 'File', 'Line', 'Src Line', 'Method', 'Original', 'Mutant', 'Killed'], True)
        o2 = {'line_num': ''}

        killed_num = 0

        for o in mutants:
            if o['killed']:
                killed_num += 1
            if o2['line_num'] == o['line_num']:
                ReportGenerator.writeTable(report, [o['id'], '', '', '', '', '', '', o['line'], o['mutant'], o['killed']])
            else:
                ReportGenerator.writeTable(report, [o['id'], o['operator'], o['operator_type'], o['file'], o['line_num'], o['ori_line_num'], o['method'], o['line'], o['mutant'], o['killed']])
            o2 = o
        report.write('</table>\n')

        mutation_score = killed_num / len(mutants)

        report.write('Mutation Scort: %0.4f\n' % mutation_score)

if __name__ == "__main__":
    import sys, os, json
    directory = sys.argv[1]
    mutants_list = os.path.join(directory, 'mutants')
    with open(mutants_list, 'rb') as handle:
        mutants = json.load(handle)
    
    ReportGenerator.generateReport(mutants, directory)
