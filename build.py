"""
Circle CI build script

A python build script to run php codesniffer only on files changed in a PR.
"""
from pprint import pprint
from pathlib import Path
import os
import sys
import subprocess
import re
import yaml

# External variables:
# - $CIRCLE_BRANCH is defined by CircleCI (https://circleci.com/docs/2.0/env-vars/)
# Other variables should be defined in the file [repo_root]/circleci/script_variables.yml
# Note that all commands are executed from the repository root directory.

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

def get_environment_variables():
    """Loads environment variables from an external file"""
    env_file = Path('.circleci/script_variables.yml')
    result = {}
    if env_file.exists():
        stream = open(str(env_file), "r")
        variables = yaml.load_all(stream)
        for var in variables:
            for key, value in var.items():
                result[key] = value
        if 'CODING_STANDARDS_DIRECTORIES' not in result.keys():
            sys.stderr.write("Required key 'CODING_STANDARDS_DIRECTORIES' was not present in the script_variables.yml file")
            sys.exit(1)
        return result
    sys.stderr.write("Enviroment file '" + str(env_file) + "' could not be found.")
    sys.exit(1)


def main():
    """Main executable"""
    env = get_environment_variables()
    print("Build starting.")
    skipped_files = set()
    php_files_visited = set()
    php_files_passed = set()
    php_files_failed = set()
    for myfile in get_changed_files():
        if not os.path.isfile(myfile):
            continue
        combined_fs_regex = "(" + ")|(".join(env['CODING_STANDARDS_DIRECTORIES']) + ")"

        if re.match(combined_fs_regex, myfile):
            if re.match(r".*\.(php|module|inc|install)$", myfile):
                fullpath = os.path.abspath(myfile)
                php_files_visited.add(fullpath)
                # Get the full path to the file.
                # Assert drupal coding standard.
                if coding_standards_check(fullpath):
                    php_files_passed.add(fullpath)
                else:
                    php_files_failed.add(fullpath)
        else:
            # Add to the output if a file was scipped because it failed the pattern match.
            # This may clue us into the fact if a directory was erroneously excluded.
            skipped_files.add(myfile)
    if len(php_files_visited) == 0:
        print("No linting required (no php files changed.)")
        sys.exit(0)
    else:
        print ("\n" + str(len(php_files_visited)) + " files visited:")
        print ("\n  - ".join(php_files_visited))
    if len(php_files_failed) > 0:
        print ("\n" + str(len(php_files_failed)) + " files skipped:")
        print ("\n  - ".join(skipped_files))
    if len(php_files_passed) > 0:
        print ("\n" + str(len(php_files_passed)) + " files passed:")
        print ("\n  - ".join(php_files_passed))
    if len(php_files_failed) > 0:
        print ("\n" + str(len(php_files_failed)) + " files failed:")
        print ("\n  - ".join(php_files_failed))
        sys.exit(1)

# Run main.
main()
