# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""Reporter foundation for coverage.py."""
import sys

from coverage import env
from coverage.files import prep_patterns, FnmatchMatcher
from coverage.misc import CoverageException, NoSource, NotPython, ensure_dir_for_file, file_be_gone


def render_report(output_path, reporter, morfs):
    """Run the provided reporter ensuring any required setup and cleanup is done

    At a high level this method ensures the output file is ready to be written to. Then writes the
    report to it. Then closes the file and deletes any garbage created if necessary.
    """
    file_to_close = None
    delete_file = False
    if output_path:
        if output_path == '-':
            outfile = sys.stdout
        else:
            # Ensure that the output directory is created; done here
            # because this report pre-opens the output file.
            # HTMLReport does this using the Report plumbing because
            # its task is more complex, being multiple files.
            ensure_dir_for_file(output_path)
            open_kwargs = {}
            if env.PY3:
                open_kwargs['encoding'] = 'utf8'
            outfile = open(output_path, "w", **open_kwargs)
            file_to_close = outfile
    try:
        return reporter.report(morfs, outfile=outfile)
    except CoverageException:
        delete_file = True
        raise
    finally:
        if file_to_close:
            file_to_close.close()
            if delete_file:
                file_be_gone(output_path)


def get_analysis_to_report(coverage, morfs):
    """Get the files to report on.

    For each morf in `morfs`, if it should be reported on (based on the omit
    and include configuration options), yield a pair, the `FileReporter` and
    `Analysis` for the morf.

    """
    file_reporters = coverage._get_file_reporters(morfs)
    config = coverage.config

    if config.report_include:
        matcher = FnmatchMatcher(prep_patterns(config.report_include))
        file_reporters = [fr for fr in file_reporters if matcher.match(fr.filename)]

    if config.report_omit:
        matcher = FnmatchMatcher(prep_patterns(config.report_omit))
        file_reporters = [fr for fr in file_reporters if not matcher.match(fr.filename)]

    if not file_reporters:
        raise CoverageException("No data to report.")

    for fr in sorted(file_reporters):
        try:
            analysis = coverage._analyze(fr)
        except NoSource:
            if not config.ignore_errors:
                raise
        except NotPython:
            # Only report errors for .py files, and only if we didn't
            # explicitly suppress those errors.
            # NotPython is only raised by PythonFileReporter, which has a
            # should_be_python() method.
            if fr.should_be_python():
                if config.ignore_errors:
                    msg = "Could not parse Python file {0}".format(fr.filename)
                    coverage._warn(msg, slug="couldnt-parse")
                else:
                    raise
        else:
            yield (fr, analysis)
