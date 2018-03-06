"""
Circle CI build script

A python build script to run php codesniffer only on files changed in a PR.
"""
import os
import sys
import subprocess
import re
from pprint import pprint

# External variables:
# - $CIRCLE_BRANCH is defined by CircleCI (https://circleci.com/docs/2.0/env-vars/)

def which(program):
    """Simulates unix 'which' command"""
    def is_exe(fpath):
        """Returns if the fiie is present and executable"""
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file


def get_changed_files():
    """Returns an array of files changed between the PR commit and the develop branch"""
    # Currently, we perform all diffs between the PR and the develop branch of the repo.
    # Note that this script expects the build tooling to have fetched the origin/develop
    # branch previously in a separate step.
    return subprocess.check_output(['git',
                                    'diff',
                                    '--name-only',
                                    'origin/develop',
                                    'HEAD']).strip().split("\n")

def coding_standards_check(fullpath):
    """Confirms that a file meets Drupal coding standards"""
    # Returns True if the file meets standards, False otherwise.
    try:
        subprocess.check_call([which('vendor/bin/phpcs'), '--standard=Drupal', fullpath]) 
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Main executable"""
    print "Build starting.  Current git branch: $CIRCLE_BRANCH"
    if not which('phpcs'):
        sys.stderr.write("phpcs is not available")
        sys.exit(1)
    if not which('composer'):
        sys.stderr.write("composer is not available")
        sys.exit(1)
    # if not which('npm'):
    #     sys.stderr.write("npm is not available")
    #     sys.exit(1)
    print "All dependencies found."
    php_files_visited = set()
    php_files_passed = set()
    php_files_failed = set()
    for myfile in get_changed_files():
        if(os.path.isfile(myfile)):
            if re.match(r"sites/all/modules/features", myfile):
                continue;
            if re.match(r"sites/all/modules/contrib", myfile):
                continue;
            if re.match(r".*\.(php|module|inc|install)$", myfile):
                fullpath = os.path.abspath(myfile)
                php_files_visited.add(fullpath)
                # Get the full path to the file.
                # Assert drupal coding standard.
                if coding_standards_check(fullpath):
                    php_files_passed.add(fullpath)
                else subprocess.CalledProcessError:
                    php_files_failed.add(fullpath)
    if len(php_files_visited) == 0:
        print "No linting required (no php files changed.)"
        sys.exit(0)
    else:
        print "\n" + str(len(php_files_visited)) + " files visited:"
        print "\n  - ".join(php_files_visited)
    if len(php_files_passed) > 0:
        print "\n" + str(len(php_files_passed)) + " files passed:"
        print "\n  - ".join(php_files_passed)
    if len(php_files_failed) > 0:
        print "\n" + str(len(php_files_failed)) + " files failed:"
        print "\n  - ".join(php_files_failed)
        sys.exit(1)
# Run main.
main()