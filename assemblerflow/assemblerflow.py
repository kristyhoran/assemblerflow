#!/usr/bin/env python3

__version__ = "1.0.0"
__build__ = "22012018"

import os
import sys
import shutil
import logging
import argparse
import logging.config

from distutils.dir_util import copy_tree

from os.path import join, dirname

try:
    from generator.engine import NextflowGenerator, process_map
    from generator.recipe import brew_recipe
    from generator.pipeline_parser import parse_pipeline, SanityError
    from generator.process_details import proc_collector, colored_print
except ImportError:
    from assemblerflow.generator.engine import NextflowGenerator, process_map
    from assemblerflow.generator.recipe import brew_recipe
    from assemblerflow.generator.pipeline_parser import parse_pipeline, \
        SanityError
    from assemblerflow.generator.process_details import proc_collector, \
        colored_print

logger = logging.getLogger("main")


def get_args(args=None):

    parser = argparse.ArgumentParser(
        description="Nextflow pipeline generator")

    group_lists = parser.add_mutually_exclusive_group()

    parser.add_argument("-t", "--tasks", type=str, dest="tasks",
                        help="Space separated tasks of the pipeline")
    parser.add_argument("-r", "--recipe", dest="recipe",
                        help="Use one of the available recipes")
    parser.add_argument("-o", dest="output_nf",
                        help="Name of the pipeline file")
    parser.add_argument("--include-templates", dest="include_templates",
                        action="store_const", const=True,
                        help="This will copy the necessary templates and lib"
                             " files to the directory where the nextflow"
                             " pipeline will be generated")
    parser.add_argument("-c", "--check-pipeline", dest="check_only",
                        action="store_const", const=True,
                        help="Check only the validity of the pipeline"
                             "string and exit.")
    group_lists.add_argument("-L", "--detailed-list", action="store_const",
                             dest="detailed_list", const=True,
                             help="Print a detailed description for all the "
                                  "currently available processes")
    group_lists.add_argument("-l", "--short-list", action="store_const",
                             dest="short_list", const=True,
                             help="Print a short list of the currently"
                                  " available processes")
    parser.add_argument("--debug", dest="debug", action="store_const",
                        const=True, help="Set log to debug mode")

    return parser.parse_args(args)


def check_arguments(args):

    # Check if no args are passed
    if len(sys.argv) == 1:
        logger.info(colored_print("Please provide one of the supported "
                                  "arguments!", "red_bold"))
        return False

    return True


def check_arguments(args):

    passed = True

    # Check if no args are passed
    if len(sys.argv) == 1:
        logger.info(colored_print("Please provide one of the supported "
                                  "arguments!", "red_bold"))
        passed = False

    # Check if output argument is valid
    # Check if output file was provided, if it is not a directory, and if
    # the directory exists
    if not args.output_nf \
            or os.path.isdir(args.output_nf) \
            or (os.path.dirname(args.output_nf) and
                not os.path.isdir(os.path.dirname(args.output_nf))):
        logger.info(colored_print("Please provide a valid output file and "
                                  "location!", "red_bold"))
        passed = False

    return passed


def copy_project(path):
    """

    Parameters
    ----------
    path

    Returns
    -------

    """

    # Get nextflow repo directory
    repo_dir = dirname(os.path.abspath(__file__))

    # Get target directory
    target_dir = dirname(path)

    # Copy templates
    copy_tree(join(repo_dir, "templates"), join(target_dir, "templates"))

    # Copy Helper scripts
    copy_tree(join(repo_dir, "lib"), join(target_dir, "lib"))

    # Copy bin scripts
    copy_tree(join(repo_dir, "bin"), join(target_dir, "bin"))

    # Copy default config file
    shutil.copy(join(repo_dir, "nextflow.config"),
                join(target_dir, "nextflow.config"))


def run(args):

    if args.debug:
        logger.setLevel(logging.DEBUG)

        # create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    else:
        logger.setLevel(logging.INFO)

        # create special formatter for info logs
        formatter = logging.Formatter('%(message)s')

    # create console handler and set level to debug
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)

    # add formatter to ch
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    welcome = [
        "========= A S S E M B L E R F L O W =========",
        "version: {}".format(__version__),
        "build: {}".format(__build__),
        "============================================="
    ]

    logger.info(colored_print("\n".join(welcome), "green_bold"))

    # If a recipe is specified, build pipeline based on the
    # appropriate recipe
    if args.recipe:
        pipeline_string, list_processes = brew_recipe(args)
    else:
        pipeline_string = args.tasks
        list_processes = None

    # used for lists print
    proc_collector(process_map, args, list_processes)

    # Validate arguments. This must be done after the process collector part
    passed = check_arguments(args)

    if not passed:
        return

    logger.info(colored_print("Resulting pipeline string:\n"))
    logger.info(colored_print(pipeline_string + "\n"))

    try:
        logger.info(colored_print("Checking pipeline for errors..."))
        pipeline_list = parse_pipeline(pipeline_string)
    except SanityError as e:
        logger.error(colored_print(e.value, "red_bold"))
        sys.exit(1)
    logger.debug("Pipeline successfully parsed: {}".format(pipeline_list))

    # Exit if only the pipeline parser needs to be checked
    if args.check_only:
        sys.exit()

    nfg = NextflowGenerator(process_connections=pipeline_list,
                            nextflow_file=args.output_nf)

    logger.info(colored_print("Building your awesome pipeline..."))

    # building the actual pipeline nf file
    nfg.build()

    # copy template to cwd, to allow for immediate execution
    if args.include_templates:
        copy_project(args.output_nf)

    logger.info(colored_print("DONE!", "green_bold"))


def main():

    args = get_args()
    run(args)


if __name__ == '__main__':

    main()
