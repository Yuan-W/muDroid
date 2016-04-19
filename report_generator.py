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
        ReportGenerator.writeTable(report, ['Id', 'Operator', 'Type', 'File', 'Line', 'Src Line', 'Method', 'Original', 'Mutant', 'Killed', 'Crashed'], True)
        o2 = {'line_num': ''}

        killed_num = 0
        aor_num = 0
        ror_num = 0
        icr_num = 0
        uoi_num = 0
        lcr_num = 0
        rvr_num = 0
        crashed_num = 0

        for o in mutants:
            if o['killed']:
                killed_num += 1
                if o['crashed']:
                    crashed_num += 1
            else:
                o['crashed'] = ''
            
            if o['operator_type'] == 'ICR':
                icr_num += 1
            elif o['operator_type'] == 'NOI':
                uoi_num += 1
            elif o['operator_type'] == 'LCR':
                lcr_num += 1
            elif o['operator_type'] == 'AOR':
                aor_num += 1
            elif o['operator_type'] == 'ROR':
                ror_num += 1
            elif o['operator_type'] == 'RVR':
                rvr_num += 1

            if o2['line_num'] == o['line_num']:
                ReportGenerator.writeTable(report, [o['id'], '', '', '', '', '', '', o['line'], o['mutant'], o['killed'], o['crashed']])
            else:
                ReportGenerator.writeTable(report, [o['id'], o['operator'], o['operator_type'], o['file'], o['line_num'], o['ori_line_num'], o['method'], o['line'], o['mutant'], o['killed'], o['crashed']])
            o2 = o
        report.write('</table>\n')

        mutation_score = killed_num / float(len(mutants))
        report.write('<span style="display:block; height: 30;"></span>\n<table>\n')
        ReportGenerator.writeTable(report, ['ICR', icr_num, '%0.4f\n' % (icr_num / float(len(mutants)))])
        ReportGenerator.writeTable(report, ['NOI', uoi_num, '%0.4f\n' % (uoi_num / float(len(mutants)))])
        ReportGenerator.writeTable(report, ['LCR', lcr_num, '%0.4f\n' % (lcr_num / float(len(mutants)))])
        ReportGenerator.writeTable(report, ['AOR', aor_num, '%0.4f\n' % (aor_num / float(len(mutants)))])
        ReportGenerator.writeTable(report, ['ROR', ror_num, '%0.4f\n' % (ror_num / float(len(mutants)))])
        ReportGenerator.writeTable(report, ['RVR', rvr_num, '%0.4f\n' % (rvr_num / float(len(mutants)))])
        report.write('</table>\n')
        report.write('<span style="display:block; height: 30;"></span>\n')
        report.write('Killed: %d\n' % killed_num)
        report.write('Crashed: %d\n' % crashed_num)
        report.write('Mutation Score: %0.4f\n' % mutation_score)
        

if __name__ == "__main__":
    import sys, os, json
    directory = sys.argv[1]
    mutants_list = os.path.join(directory, 'mutants')
    with open(mutants_list, 'rb') as handle:
        mutants = json.load(handle)
    
    ReportGenerator.generateReport(mutants, directory)
