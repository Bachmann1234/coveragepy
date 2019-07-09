# coding: utf-8
# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Json reporting for coverage.py"""

import os
import os.path
import json
import sys
import time

from coverage import __version__, files
from coverage.backward import iitems
from coverage.misc import isolate_module
from coverage.report import Reporter

os = isolate_module(os)


def rate(hit, num):
    """Return the fraction of `hit`/`num`, as a string."""
    if num == 0:
        return "1"
    else:
        return "%.4g" % (float(hit) / num)


class JsonReporter(Reporter):
    """A reporter for writing JSON coverage results."""

    def __init__(self, coverage, config):
        super(JsonReporter, self).__init__(coverage, config)

        self.source_paths = set()
        if self.config.source:
            for src in self.config.source:
                if os.path.exists(src):
                    self.source_paths.add(files.canonical_filename(src))
        self.packages = {}
        self.report_data = {}
        self.data = coverage.get_data()
        self.has_arcs = self.data.has_arcs()

    def report(self, morfs, outfile=None):
        """Generate a json report for `morfs`.

        `morfs` is a list of modules or file names.

        `outfile` is a file object to write the json to

        """
        outfile = outfile or sys.stdout
        self.report_data["version"] = __version__
        self.report_data["timestamp"] = str(int(time.time()))
        self.report_data["has_arcs"] = self.coverage.data.has_arcs()
        measured_files = []
        for measured_file in self.coverage.data.measured_files():
            reported_file = {
                'measured_file': measured_file,
                'executed_lines': self.coverage.data.lines(measured_file),
                'file_tracer': self.coverage.data.file_tracer(measured_file)
            }
            if self.coverage.data.has_arcs():
                reported_file['arcs'] = self.coverage.data.arcs(measured_file)

            measured_files.append(reported_file)
        self.report_data["measured_files"] = measured_files

        # Write the output file.
        outfile.write(json.dumps(self.report_data, indent=4)) #todo pretty print option?

        # Return the total percentage.
        return 0

