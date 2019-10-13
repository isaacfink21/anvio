# -*- coding: utf-8
# pylint: disable=line-too-long
"""Helper functions for the anvi'o snakemake workflows"""

import os
import sys
import json
import copy
import snakemake
from snakemake import *

def main(argv=None):
    """Main entry point."""
    parser = get_argument_parser()
    args = parser.parse_args(argv)

    if args.profile:
        # reparse args while inferring config file from profile
        parser = get_argument_parser(args.profile)
        args = parser.parse_args(argv)
        def adjust_path(f):
            if os.path.exists(f) or os.path.isabs(f):
                return f
            else:
                return get_profile_file(args.profile, f, return_default=True)

        # update file paths to be relative to the profile
        # (if they do not exist relative to CWD)
        if args.jobscript:
            args.jobscript = adjust_path(args.jobscript)
        if args.cluster:
            args.cluster = adjust_path(args.cluster)
        if args.cluster_sync:
            args.cluster_sync = adjust_path(args.cluster_sync)
        if args.cluster_status:
            args.cluster_status = adjust_path(args.cluster_status)

    if args.bash_completion:
        cmd = b"complete -o bashdefault -C snakemake-bash-completion snakemake"
        sys.stdout.buffer.write(cmd)
        sys.exit(0)

    try:
        resources = parse_resources(args)
        config = parse_config(args)
    except ValueError as e:
        print(e, file=sys.stderr)
        print("", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    if (args.cluster or args.cluster_sync or args.drmaa):
        if args.cores is None:
            if args.dryrun:
                args.cores = 1
            else:
                print(
                    "Error: you need to specify the maximum number of jobs to "
                    "be queued or executed at the same time with --jobs.",
                    file=sys.stderr)
                sys.exit(1)
    elif args.cores is None:
        args.cores = 1

    if args.drmaa_log_dir is not None:
        if not os.path.isabs(args.drmaa_log_dir):
            args.drmaa_log_dir = os.path.abspath(os.path.expanduser(args.drmaa_log_dir))

    if args.runtime_profile:
        import yappi
        yappi.start()

    if args.immediate_submit and not args.notemp:
        print(
            "Error: --immediate-submit has to be combined with --notemp, "
            "because temp file handling is not supported in this mode.",
            file=sys.stderr)
        sys.exit(1)

    if (args.conda_prefix or args.create_envs_only) and not args.use_conda:
        print(
            "Error: --use-conda must be set if --conda-prefix or "
            "--create-envs-only is set.",
            file=sys.stderr)
        sys.exit(1)

    if args.singularity_prefix and not args.use_singularity:
        print("Error: --use_singularity must be set if --singularity-prefix "
              "is set.", file=sys.stderr)
        sys.exit(1)

    if args.delete_all_output and args.delete_temp_output:
        print("Error: --delete-all-output and --delete-temp-output are mutually exclusive.", file=sys.stderr)
        sys.exit(1)

    if args.gui is not None:
        try:
            import snakemake.gui as gui
        except ImportError:
            print("Error: GUI needs Flask to be installed. Install "
                  "with easy_install or contact your administrator.",
                  file=sys.stderr)
            sys.exit(1)

        _logging.getLogger("werkzeug").setLevel(_logging.ERROR)

        _snakemake = partial(snakemake, os.path.abspath(args.snakefile))
        gui.register(_snakemake, args)

        if ":" in args.gui:
            host, port = args.gui.split(":")
        else:
            port = args.gui
            host = "127.0.0.1"

        url = "http://{}:{}".format(host, port)
        print("Listening on {}.".format(url), file=sys.stderr)

        def open_browser():
            try:
                webbrowser.open(url)
            except:
                pass

        print("Open this address in your browser to access the GUI.",
              file=sys.stderr)
        threading.Timer(0.5, open_browser).start()
        success = True

        try:
            gui.app.run(debug=False, threaded=True, port=int(port), host=host)

        except (KeyboardInterrupt, SystemExit):
            # silently close
            pass
    else:
        success = snakemake(args.snakefile,
                            report=args.report,
                            listrules=args.list,
                            list_target_rules=args.list_target_rules,
                            cores=args.cores,
                            local_cores=args.local_cores,
                            nodes=args.cores,
                            resources=resources,
                            config=config,
                            configfile=args.configfile,
                            config_args=args.config,
                            workdir=args.directory,
                            targets=args.target,
                            dryrun=args.dryrun,
                            printshellcmds=args.printshellcmds,
                            printreason=args.reason,
                            debug_dag=args.debug_dag,
                            printdag=args.dag,
                            printrulegraph=args.rulegraph,
                            printd3dag=args.d3dag,
                            touch=args.touch,
                            forcetargets=args.force,
                            forceall=args.forceall,
                            forcerun=args.forcerun,
                            prioritytargets=args.prioritize,
                            until=args.until,
                            omit_from=args.omit_from,
                            stats=args.stats,
                            nocolor=args.nocolor,
                            quiet=args.quiet,
                            keepgoing=args.keep_going,
                            cluster=args.cluster,
                            cluster_config=args.cluster_config,
                            cluster_sync=args.cluster_sync,
                            drmaa=args.drmaa,
                            drmaa_log_dir=args.drmaa_log_dir,
                            kubernetes=args.kubernetes,
                            kubernetes_envvars=args.kubernetes_env,
                            container_image=args.container_image,
                            jobname=args.jobname,
                            immediate_submit=args.immediate_submit,
                            standalone=True,
                            ignore_ambiguity=args.allow_ambiguity,
                            lock=not args.nolock,
                            unlock=args.unlock,
                            cleanup_metadata=args.cleanup_metadata,
                            cleanup_conda=args.cleanup_conda,
                            cleanup_shadow=args.cleanup_shadow,
                            force_incomplete=args.rerun_incomplete,
                            ignore_incomplete=args.ignore_incomplete,
                            list_version_changes=args.list_version_changes,
                            list_code_changes=args.list_code_changes,
                            list_input_changes=args.list_input_changes,
                            list_params_changes=args.list_params_changes,
                            list_untracked=args.list_untracked,
                            summary=args.summary,
                            detailed_summary=args.detailed_summary,
                            archive=args.archive,
                            delete_all_output=args.delete_all_output,
                            delete_temp_output=args.delete_temp_output,
                            print_compilation=args.print_compilation,
                            verbose=args.verbose,
                            debug=args.debug,
                            jobscript=args.jobscript,
                            notemp=args.notemp,
                            keep_remote_local=args.keep_remote,
                            greediness=args.greediness,
                            no_hooks=args.no_hooks,
                            overwrite_shellcmd=args.overwrite_shellcmd,
                            latency_wait=args.latency_wait,
                            wait_for_files=args.wait_for_files,
                            keep_target_files=args.keep_target_files,
                            allowed_rules=args.allowed_rules,
                            max_jobs_per_second=args.max_jobs_per_second,
                            max_status_checks_per_second=args.max_status_checks_per_second,
                            restart_times=args.restart_times,
                            attempt=args.attempt,
                            force_use_threads=args.force_use_threads,
                            use_conda=args.use_conda,
                            conda_prefix=args.conda_prefix,
                            list_conda_envs=args.list_conda_envs,
                            use_singularity=args.use_singularity,
                            singularity_prefix=args.singularity_prefix,
                            shadow_prefix=args.shadow_prefix,
                            singularity_args=args.singularity_args,
                            create_envs_only=args.create_envs_only,
                            mode=args.mode,
                            wrapper_prefix=args.wrapper_prefix,
                            default_remote_provider=args.default_remote_provider,
                            default_remote_prefix=args.default_remote_prefix,
                            assume_shared_fs=not args.no_shared_fs,
                            cluster_status=args.cluster_status,
                            log_handler=AnvioLogger.anvio_logger)

    if args.runtime_profile:
        with open(args.runtime_profile, "w") as out:
            profile = yappi.get_func_stats()
            profile.sort("totaltime")
            profile.print_all(out=out)

    sys.exit(0 if success else 1)

snakemake.main = main

import anvio
import anvio.utils as u
import anvio.errors as errors
import anvio.terminal as terminal
import anvio.filesnpaths as filesnpaths

from anvio.errors import ConfigError


__author__ = "Developers of anvi'o (see AUTHORS.txt)"
__copyright__ = "Copyleft 2015-2018, the Meren Lab (http://merenlab.org/)"
__credits__ = []
__license__ = "GPL 3.0"
__version__ = anvio.__version__
__maintainer__ = "Alon Shaiber"
__email__ = "alon.shaiber@gmail.com"
__status__ = "Development"


run = terminal.Run()
progress = terminal.Progress()
r = errors.remove_spaces

class AnvioLogger(object):
    quiet = False
    run = terminal.Run()
    progress = terminal.Progress()
    last_msg_was_job_info = False
    printreason = False

    first_log = True
    total_jobs = 0
    jobs_done = 0

    @classmethod
    def anvio_logger(cls, msg):
        """
        log_handler (function):
        redirect snakemake output to this custom log handler, a function
        that takes a log message dictionary (see below) as its only argument (default None). The log
        message dictionary for the log handler has to following entries:

            :level:
                the log level ("info", "error", "debug", "progress", "job_info")

            :level="info", "error" or "debug":
                :msg:
                    the log message
            :level="progress":
                :done:
                    number of already executed jobs

                :total:
                    number of total jobs

            :level="job_info":
                :input:
                    list of input files of a job

                :output:
                    list of output files of a job

                :log:
                    path to log file of a job

                :local:
                    whether a job is executed locally (i.e. ignoring cluster)

                :msg:
                    the job message

                :reason:
                    the job reason

                :priority:
                    the job priority

                :threads:
                    the threads of the job
        """
        if cls.first_log:
            cls.progress.new('anvi-run-workflow')
            cls.progress.update('Initializing')
            cls.first_log = False

        level = msg['level']

        timestamp = lambda cls: cls.run.info_single(terminal.get_date(), nl_before=1, nl_after=0, progress=cls.progress)
        format_value = lambda value, omit=None, valueformat=str: valueformat(value) if value != omit else None
        format_wildcards = lambda wildcards: ', '.join(['%s=%s' % (k, v) for k, v in wildcards.items()])
        format_resources = lambda resources: ', '.join(['%s=%s' % (k, v) for k, v in resources.items() if not k.startswith('_')])

        if level == 'job_info' and not cls.quiet:
            timestamp(cls)
            if msg['msg'] is not None:
                cls.run.info('Job %s' % msg['jobid'], msg['msg'], nl_before=nl_before, nl_after=0, progress=cls.progress)
                if cls.printreason:
                    cls.run.info('Reason', msg['reason'], nl_before=0, nl_after=0, progress=cls.progress)
            else:
                cls.run.warning('', header='%srule %s' % ('local' if msg['local'] else '', msg['name']), progress=cls.progress)

                for item in ['input', 'output', 'log']:
                    value = format_value(msg[item], omit=[], valueformat=', '.join)
                    if value is not None:
                        cls.run.info(item, value, progress=cls.progress)

                for item in ['jobid', 'benchmark'] + ([] if not cls.printreason else ['reason']):
                    value = format_value(msg[item], omit=None)
                    if value is not None:
                        cls.run.info(item, value, progress=cls.progress)

                wildcards = format_wildcards(msg["wildcards"])
                if wildcards:
                    cls.run.info('wildcards', wildcards, progress=cls.progress)

                for item, omit in zip("priority threads".split(), [0, 1]):
                    value = format_value(msg[item], omit=omit)
                    if value is not None:
                        cls.run.info(item, value, progress=cls.progress)

                resources = format_resources(msg["resources"])
                if resources:
                    cls.run.info('resources', resources, progress=cls.progress)

            cls.last_msg_was_job_info = True

        elif level == "group_info" and not cls.quiet:
            timestamp(cls)
            cls.run.info_single('group job %s (jobs in lexicogr. order):' % str(msg['groupid']), progress=cls.progress)

        elif level == "job_error":
            timestamp(cls)
            cls.run.warning('An error in rule %s (job ID %s) has occurred.' % (msg['name'], msg['jobid']), 
                            header = 'AnviWorkflowError', progress=cls.progress)
            if msg["output"]:
                cls.run.info('output', ", ".join(msg["output"]), progress=cls.progress)
            if msg["log"]:
                cls.run.info('log', ", ".join(msg["log"]), progress=cls.progress)
            if msg["conda_env"]:
                cls.run.info('conda-env', msg["conda_env"])
            for k, v in msg["aux"].items():
                cls.run.info(k, v, progress=cls.progress)

        elif level == "group_error":
            print('never tested:')
            timestamp(cls)
            cls.run.info_single('Error in group job {}:' % str(msg['groupid']), progress=cls.progress)

        else:
            if level == "info" and not cls.quiet:
                cls.run.info_single(msg["msg"], progress=cls.progress)
            if level == "warning":
                cls.run.warning(msg["msg"], header='warning', progress=cls.progress)
            elif level == "error":
                cls.run.warning(msg["msg"], header='AnviWorkflowError', raw=True, progress=cls.progress)
            elif level == "debug":
                if anvio.DEBUG:
                    cls.run.warning(msg["msg"], header='debug', raw=True, progress=cls.progress)
            elif level == "resources_info" and not cls.quiet:
                cls.run.info_single(msg["msg"], progress=cls.progress)
            elif level == "run_info":
                # we needed the total number of items from this string (I know) to start proper
                # progress object (I know)
                cls.total_jobs = int(msg['msg'].strip().split()[-1])
                cls.progress.end()
                cls.progress.new('anvi-run-workflow', progress_total_items=cls.total_jobs)
                cls.progress.update('%d of %d steps done' % (cls.jobs_done, cls.total_jobs))

                from colored import fore, style
                cls.progress.clear()
                print(fore.YELLOW + msg['msg'] + style.RESET)
                cls.progress.update(cls.progress.msg)
            elif level == "progress" and not cls.quiet:
                cls.total_jobs = msg['total']
                cls.jobs_done = msg['done']

                p = cls.jobs_done / cls.total_jobs
                percent_fmt = ("{:.3%}" if p < 0.01 else "{:.0%}").format(p)
                cls.progress.increment(increment_to=cls.jobs_done)
                cls.progress.update('%d of %d steps done' % (cls.jobs_done, cls.total_jobs))
            # elif level == "shellcmd":
            #     if cls.printshellcmds:
            #         cls.logger.warning(indent(msg["msg"]), progress=cls.progress)
            # elif level == "job_finished" and not cls.quiet:
            #     timestamp(cls)
            #     cls.logger.info("Finished job {}.".format(msg["jobid"]))
            #     pass
            # elif level == "rule_info":
            #     cls.logger.info(msg["name"])
            #     if msg["docstring"]:
            #         cls.logger.info("    " + msg["docstring"])
            # elif level == "d3dag":
            #     print(json.dumps({"nodes": msg["nodes"], "links": msg["edges"]}))
            # elif level == "dag_debug":
            #     if cls.debug_dag:
            #         job = msg["job"]
            #         cls.logger.warning(
            #             "{status} job {name}\n\twildcards: {wc}".format(
            #                 status=msg["status"],
            #                 name=job.rule.name,
            #                 wc=format_wildcards(job.wildcards)))

            cls.last_msg_was_job_info = False


class WorkflowSuperClass:
    def __init__(self):
        if 'args' not in self.__dict__:
            raise ConfigError("You need to initialize `WorkflowSuperClass` from within a class that\
                               has a member `self.args`.")

        A = lambda x: self.args.__dict__[x] if x in self.args.__dict__ else None
        # FIXME: it is redundant to have both config and config_file
        # Alon and Meren will discuss how to do this right.
        # but for now this is how it is so things would work.
        # basically, when this class is called from a snakefile
        # then a config (dictionary) will be provided.
        # When this class is called from anvi-run-snakemake-workflow
        # for sanity checks  and things like that, then a config file
        # will be provided.
        self.config = A('config')
        self.config_file = A('config_file')
        self.default_config_output_path = A('get_default_config')
        self.save_workflow_graph = A('save_workflow_graph')
        self.list_dependencies = A('list_dependencies')
        self.dry_run_only = A('dry_run')
        self.additional_params = A('additional_params')

        if self.additional_params:
            run.warning("OK, SO THIS IS SERIOUS, AND WHEN THINGS ARE SERIOUS THEN WE USE CAPS. \
                         WE SEE THAT YOU ARE USING --additional-params AND THAT'S GREAT, BUT WE \
                         WANT TO REMIND YOU THAT ANYTHING THAT FOLLOWS --additional-params WILL \
                         BE CONSIDERED AS A snakemake PARAM THAT IS TRANSFERRED TO snakemake DIRECTLY. \
                         So make sure that these don't include anything that you didn't mean to \
                         include as an additional param: %s." % ', '.join(str(i) for i in self.additional_params))

        if self.save_workflow_graph:
            self.dry_run_only = True

        # if this class is being inherited from a snakefile that was 'included' from
        # within another snakefile.
        self.slave_mode = A('slave_mode')

        if self.config_file:
            filesnpaths.is_file_json_formatted(self.config_file)
            self.config = json.load(open(self.config_file))

        self.rules = []
        self.rule_acceptable_params_dict = {}
        self.dirs_dict = {}
        self.general_params = []
        self.default_config = {}
        self.rules_dependencies = {}
        self.forbidden_params = {}


    def init(self):
        run.warning('We are initiating parameters for the %s workflow' % self.name)

        for rule in self.rules:
            if rule not in self.rule_acceptable_params_dict:
                self.rule_acceptable_params_dict[rule] = []

            params_that_all_rules_must_accept = ['threads']
            for param in params_that_all_rules_must_accept:
                if param not in self.rule_acceptable_params_dict[rule]:
                    self.rule_acceptable_params_dict[rule].append(param)

            general_params_that_all_workflows_must_accept = ['output_dirs', 'max_threads']
            for param in general_params_that_all_workflows_must_accept:
                if param not in self.general_params:
                    self.general_params.append(param)

        self.dirs_dict.update({"LOGS_DIR": "00_LOGS"})

        self.default_config = self.get_default_config()

        # the user requested to get a default config path for the workflow
        if self.default_config_output_path:
            self.save_default_config_in_json_format(self.default_config_output_path)
            sys.exit()
        elif not self.config:
            raise ConfigError("You need a config file to run this :/ If you need help to start preparing\
                               a config file for the anvi'o %s workflow, you can try the `--get-default-config`\
                               flag." % (self.name))

        self.dirs_dict.update(self.config.get("output_dirs", ''))

        # create log dir if it doesn't exist
        os.makedirs(self.dirs_dict["LOGS_DIR"], exist_ok=True)

        # lets check everything
        if not self.slave_mode:
            self.check_config()
            self.check_rule_params()


    def sanity_checks(self):
        ''' each workflow has its own sanity checks but we only run these when we go'''
        # each workflow will overide this function with specific things to check
        pass


    def go(self, skip_dry_run=False):
        """Do the actual running"""

        self.sanity_checks()

        if self.save_workflow_graph or (not skip_dry_run):
            self.dry_run()

        if self.dry_run_only:
            return

        # snakemake.main() accepts an `argv` parameter, but then the code has mixed responses to
        # that, and at places continues to read from sys.argv in a hardcoded manner. so we have to
        # overwrite our argv here.
        original_sys_argv = copy.deepcopy(sys.argv)

        sys.argv = ['snakemake',
                    '--snakefile',
                    get_workflow_snake_file_path(self.args.workflow),
                    '--configfile',
                    self.args.config_file]

        if self.additional_params:
            sys.argv.extend(self.additional_params)

        if self.list_dependencies:
            sys.argv.extend(['--dryrun', '--printshellcmds'])
            snakemake.main()
            sys.exit(0)
        else:
            sys.argv.extend(['-p'])
            snakemake.main()

        # restore the `sys.argv` to the original for the sake of sakity (totally made up word,
        # but you already know what it measn. you're welcome.)
        sys.argv = original_sys_argv


    def dry_run(self, workflow_graph_output_file_path_prefix='workflow'):
        """Not your regular dry run.

           The purpose of this function is to make sure there is a way to check for
           workflow program dependencies before the workflow is actually run. this way,
           if there is a `check_workflow_program_dependencies` call at the end of the
           snake file `get_workflow_snake_file_path(self.name)`, it can be called with
           a compiled snakemake `workflow` instance."""

        if self.slave_mode:
            return

        self.progress.new('Bleep bloop')
        self.progress.update('Quick dry run for an initial sanity check ...')
        args = ['snakemake', '--snakefile', get_workflow_snake_file_path(self.name), \
                '--configfile', self.config_file, '--dryrun', '--quiet']

        if self.save_workflow_graph:
            args.extend(['--dag'])

        log_file_path = filesnpaths.get_temp_file_path()
        u.run_command(args, log_file_path)
        self.progress.end()

        # here we're getting the graph info from the log file like a dirty hacker
        # we are (it still may be better to do it elsewhere more appropriate .. so
        # we can look more decent or whatever):
        if self.save_workflow_graph:
            lines = open(log_file_path, 'rU').readlines()

            try:
                line_of_interest = [line_no for line_no in range(0, len(lines)) if lines[line_no].startswith('digraph')][0]
            except IndexError:
                raise ConfigError("Oh no. Anvi'o was trying to generate a DAG output for you, but something must have\
                                   gone wrong in a step prior. Something tells anvi'o that if you take a look at the\
                                   log file here, you may be able to figure it out: '%s'. Sorry!" % log_file_path)
            open(workflow_graph_output_file_path_prefix + '.dot', 'w').write(''.join(lines[line_of_interest:]))

            self.run.info('Workflow DOT file', workflow_graph_output_file_path_prefix + '.dot')

            if u.is_program_exists('dot', dont_raise=True):
                dot_log_file = filesnpaths.get_temp_file_path()
                u.run_command(['dot', '-Tpng', workflow_graph_output_file_path_prefix + '.dot', '-o', workflow_graph_output_file_path_prefix + '.png'], dot_log_file)
                os.remove(dot_log_file)
                self.run.info('Workflow PNG file', workflow_graph_output_file_path_prefix + '.png')
            else:
                self.run.warning("Well, anvi'o was going to try to save a nice PNG file for your workflow\
                                  graph, but clearly you don't have `dot` installed on your system. That's OK. You\
                                  have your dot file now, and you can Google 'how to view dot file on [your operating\
                                  system goes here]', and install necessary programs (like .. `dot`).")

        os.remove(log_file_path)


    def check_workflow_program_dependencies(self, snakemake_workflow_object, dont_raise=True):
        """This function gets a snakemake workflow object and checks whether each shell command
           exists in the path.
        """

        if self.slave_mode:
            return

        shell_programs_needed = [r.shellcmd.strip().split()[0] for r in snakemake_workflow_object.rules if r.shellcmd]

        shell_programs_missing = [s for s in shell_programs_needed if not u.is_program_exists(s, dont_raise=dont_raise)]

        run.warning(None, 'Shell programs for the workflow', lc='yellow')
        run.info('Needed', ', '.join(shell_programs_needed))
        run.info('Missing', ', '.join(shell_programs_missing) or 'None', nl_after=1)

        if len(shell_programs_missing):
            if dont_raise:
                return
            else:
                raise ConfigError("This workflow will not run without those missing programs are no longer\
                                   missing :(")

    def check_config(self):
        acceptable_params = set(self.rules + self.general_params)
        wrong_params = [p for p in self.config if p not in acceptable_params]
        if wrong_params:
            raise ConfigError("some of the parameters in your config file are not familiar to us. \
                        Here is a list of the wrong parameters: %s. This workflow only accepts \
                        the following general parameters: %s. And these are the rules in this \
                        workflow: %s." % (wrong_params, self.general_params, self.rules))

        wrong_dir_names = [d for d in self.config.get("output_dirs", '') if d not in self.dirs_dict]
        if wrong_dir_names:
            raise ConfigError("some of the directory names in your config file are not familiar to us. \
                        Here is a list of the wrong directories: %s. This workflow only has \
                        the following directories: %s." % (" ".join(wrong_dir_names), " ".join(list(self.dirs_dict.keys()))))

        ## make sure max_threads is an integer number
        max_threads = self.get_param_value_from_config('max_threads')
        if max_threads:
            try:
                int(max_threads)
            except:
                raise ConfigError('"max_threads" must be an integer value. The value you provided in the config file is: "%s"' % max_threads)


    def get_default_config(self):
        c = self.fill_empty_config_params(self.default_config)
        c["output_dirs"] = self.dirs_dict
        return c


    def check_additional_params(self, rule):
        ''' Check if the user is trying to use additional_params to set a param that is hard coded'''
        params = []
        if 'additional_params' in self.config[rule].keys() and self.forbidden_params.get(rule):
            # if the rule has 'additional_params' we need to make sure
            # that the user didn't include forbidden params there as well
            params = self.config[rule]['additional_params'].split(' ')

            bad_params = [p for p in self.forbidden_params.get(rule) if p in params]
            if bad_params:
                raise ConfigError("You are not allowed to set the following parameter/s: \
                                   %s for rule %s. These parameters are hard-coded. If you \
                                   are confused or upset please refer to an anvi'o developer \
                                   or a friend for support." % (', '.join(bad_params), rule))


    def check_rule_params(self):
        for rule in self.rules:
            if rule in self.config:
                wrong_params = [p for p in self.config[rule] if p not in self.rule_acceptable_params_dict[rule]]
                if wrong_params:
                    raise ConfigError("some of the parameters in your config file for rule %s are not familiar to us. \
                                Here is a list of the wrong parameters: %s. The only acceptable \
                                parameters for this rule are %s." % (rule, wrong_params, self.rule_acceptable_params_dict[rule]))

                self.check_additional_params(rule)


    def save_empty_config_in_json_format(self, file_path='empty_config.json'):
        self.save_config_in_json_format(file_path, self.get_empty_config())
        self.run.info("Empty config file", "Stored for workflow '%s' as '%s'." % (self.name, file_path))


    def save_default_config_in_json_format(self, file_path='default_config.json'):
        self.save_config_in_json_format(file_path, self.default_config)
        self.run.info("Default config file", "Stored for workflow '%s' as '%s'." % (self.name, file_path))


    def save_config_in_json_format(self, file_path, config):
        filesnpaths.is_output_file_writable(file_path)
        open(file_path, 'w').write(json.dumps(config, indent=4))


    def get_empty_config(self):
        ''' This returns a dictionary with all the possible configurables for a workflow'''
        return self.fill_empty_config_params(config={})


    def fill_empty_config_params(self, config={}):
        ''' Takes a config dictionary and assigns an empty string to any parameter that wasnt defined in the config'''
        new_config = config.copy()

        for rule in self.rules:
            if rule not in config:
                new_config[rule] = {}
            for param in self.rule_acceptable_params_dict[rule]:
                new_config[rule][param] = new_config[rule].get(param, '')

        for param in self.general_params:
            if param not in config:
                new_config[param] = ''

        return new_config


    def set_config_param(self, _list, value):
        d = self.config
        if type(_list) is not list:
            # converting to list for the cases of only one item
            _list = [_list]
        while _list:
            a = _list.pop(0)
            if a not in d:
                d[a] = {}
            f = d
            d = d[a]
        f[a] = value


    def get_param_value_from_config(self, _list, repress_default=False):
        '''
            A helper function to make sense of config details.
            string_list is a list of strings (or a single string)

            this function checks if the strings in x are nested values in self.config.
            For example if x = ['a','b','c'] then this function checkes if the
            value self.config['a']['b']['c'] exists, if it does then it is returned

            repress_default - If there is a default defined for the parameter (it would be defined
            under self.default_config), and the user didn't supply a parameter
            then the default will be returned. If this flad (repress_default) is set to True
            then this behaviour is repressed and instead an empty string would be returned.

        '''
        d = self.config
        default_dict = self.default_config
        if type(_list) is not list:
            # converting to list for the cases of only one item
            _list = [_list]
        while _list:
            a = _list.pop(0)
            default_dict = default_dict[a]
            try:
                d = d.get(a, None)
            except:
                # we continue becuase we want to get the value from the default config
                continue

        if (d is not None) or repress_default:
            return d
        else:
            return default_dict


    def get_rule_param(self, _rule, _param):
        '''
            returns the parameter as an input argument

            this function works differently for two kinds of parameters (flags, vs. non-flags)
            For example the parameter --use-ncbi-blast is a flag hence if the config file contains
            "--use-ncbi-blast": true, then this function would return "--use-ncbi-blast"

            for a non-flag the value of the parameter would also be included, for example,
            if the config file contains "--min-occurence: 5" then this function will return
            "--min-occurence 5"
        '''
        val = self.get_param_value_from_config([_rule, _param])
        if val is not None and val is not '':
            if isinstance(val, bool):
                # the param is a flag so no need for a value
                if val:
                    return _param
            else:
                return _param + ' ' + str(val)
        return ''


    def T(self, rule_name):
        max_threads = self.get_param_value_from_config("max_threads")
        if not max_threads:
            max_threads = float("Inf")
        threads = self.get_param_value_from_config([rule_name,'threads'])
        if threads:
            try:
                if int(threads) > float(max_threads):
                    return int(max_threads)
                else:
                    return int(threads)
            except:
                raise ConfigError('"threads" must be an integer number. In your config file you provided "%s" for \
                                   the number of threads for rule "%s"' % (threads, rule_name))
        else:
            return 1


    def init_workflow_super_class(self, args, workflow_name):
        '''
            if a regular instance of workflow object is being generated, we
            expect it to have a parameter `args`. if there is no `args` given, we
            assume the class is being inherited as a base class from within another.

            For a regular instance of a workflow this function will set the args
            and init the WorkflowSuperClass.
        '''
        if args:
            if len(self.__dict__):
                raise ConfigError("Something is wrong. You are ineriting %s from \
                                   within another class, yet you are providing an `args` parameter.\
                                   This is not alright." % type(self))
            self.args = args
            self.name = workflow_name
            WorkflowSuperClass.__init__(self)
            self.run = run
            self.progress = progress
        else:
            if not len(self.__dict__):
                raise ConfigError("When you are *not* inheriting %s from within\
                                   a super class, you must provide an `args` parameter." % type(self))
            if 'name' not in self.__dict__:
                raise ConfigError("The super class trying to inherit %s does not\
                                   have a set `self.name`. Which means there may be other things\
                                   wrong with it, hence anvi'o refuses to continue." % type(self))


    def get_internal_and_external_genomes_files(self):
            internal_genomes_file = self.get_param_value_from_config('internal_genomes')
            external_genomes_file = self.get_param_value_from_config('external_genomes')

            fasta_txt_file = self.get_param_value_from_config('fasta_txt', repress_default=True)
            if fasta_txt_file and not external_genomes_file:
                raise ConfigError('You provided a fasta_txt, but didn\'t specify a path for an external-genomes file. \
                                   If you wish to use external genomes, you must specify a name for the external-genomes \
                                   file, using the "external_genomes" parameter in your config file. Just to clarify: \
                                   the external genomes file doesn\'t have to exist, since we will create it for you, \
                                   by using the information you supplied in the "fasta_txt" file, but you must specify \
                                   a name for the external-genomes file. For example, you could use "external_genomes": "external-genomes.txt", \
                                   but feel free to be creative.')

            if not internal_genomes_file and not external_genomes_file:
                raise ConfigError('You must provide either an external genomes file or internal genomes file')
            # here we do a little trick to make sure the rule can expect either one or both
            d = {"internal_genomes_file": external_genomes_file,
                                                              "external_genomes_file": internal_genomes_file}

            if internal_genomes_file:
                filesnpaths.is_file_exists(internal_genomes_file)
                d['internal_genomes_file'] = internal_genomes_file

            if external_genomes_file:
                if not filesnpaths.is_file_exists(external_genomes_file, dont_raise=True):
                    run.warning('There is no file %s. No worries, one will be created for you.' % external_genomes_file)
                d['external_genomes_file'] = external_genomes_file

            return d


# The config file contains many essential configurations for the workflow
# Setting the names of all directories
dirs_dict = {"LOGS_DIR"     : "00_LOGS"         ,\
             "QC_DIR"       : "01_QC"           ,\
             "FASTA_DIR"    : "02_FASTA"     ,\
             "CONTIGS_DIR"  : "03_CONTIGS"      ,\
             "MAPPING_DIR"  : "04_MAPPING"      ,\
             "PROFILE_DIR"  : "05_ANVIO_PROFILE",\
             "MERGE_DIR"    : "06_MERGED"       ,\
             "PAN_DIR"      : "07_PAN"          ,\
             "LOCI_DIR"     : "04_LOCI_FASTAS"   \
}


########################################
# Helper functions
########################################

def A(_list, d, default_value = ""):
    '''
        A helper function to make sense of config details.
        string_list is a list of strings (or a single string)
        d is a dictionary

        this function checks if the strings in x are nested values in y.
        For example if x = ['a','b','c'] then this function checkes if the
        value y['a']['b']['c'] exists, if it does then it is returned
    '''
    if type(_list) is not list:
        # converting to list for the cases of only one item
        _list = [_list]
    while _list:
        a = _list.pop(0)
        if a in d:
            d = d[a]
        else:
            return default_value
    return d


def B(config, _rule, _param, default=''):
    # helper function for params
    val = A([_rule, _param], config, default)
    if val:
        if isinstance(val, bool):
            # the param is a flag so no need for a value
            val = ''
        return _param + ' ' + str(val)
    else:
        return ''


def D(debug_message, debug_log_file_path=".SNAKEMAKEDEBUG"):
    with open(debug_log_file_path, 'a') as output:
            output.write(terminal.get_date() + '\n')
            output.write(str(debug_message) + '\n\n')


# a helper function to get the user defined number of threads for a rule
def T(config, rule_name, N=1): return A([rule_name,'threads'], config, default_value=N)


def get_dir_names(config, dont_raise=False):
    ########################################
    # Reading some definitions from config files (also some sanity checks)
    ########################################
    DICT = dirs_dict
    for d in A("output_dirs", config):
        # renaming folders according to the config file, if the user specified.
        if d not in DICT and not dont_raise:
            # making sure the user is asking to rename an existing folder.
            raise ConfigError("You define a name for the directory '%s' in your "\
                              "config file, but the only available folders are: "\
                              "%s" % (d, DICT))

        DICT[d] = A(d,config["output_dirs"])
    return DICT


def get_path_to_workflows_dir():
    # this returns a path
    base_path = os.path.dirname(__file__)
    return base_path


def get_workflow_snake_file_path(workflow):
    workflow_dir = os.path.join(get_path_to_workflows_dir(), workflow)

    if not os.path.isdir(workflow_dir):
        raise ConfigError("Anvi'o does not know about the workflow '%s' :/")

    snakefile_path = os.path.join(workflow_dir, 'Snakefile')

    if not os.path.exists(snakefile_path):
        raise ConfigError("The snakefile path for the workflow '%s' seems to be missing :/" % workflow)

    return snakefile_path


def warning_for_param(config, rule, param, wildcard, our_default=None):
    value = A([rule, param], config)
    if value:
        warning_message = 'You chose to define %s for the rule %s in the config file as %s.\
                           while this is allowed, know that you are doing so at your own risk.\
                           The reason this is risky is because this rule uses a wildcard/wildcards\
                           and hence is probably running more than once, and this might cause a problem.\
                           In case you wanted to know, these are the wildcards used by this rule: %s' % (param, rule, value, wildcard)
        if our_default:
            warning_message = warning_message + ' Just so you are aware, if you dont provide a value\
                                                 in the config file, the default value is %s' % wildcard
        run.warning(warning_message)


def get_fields_for_fasta_information():
    """ Return a list of legitimate column names for fasta.txt files"""
    # Notice we don't include the name of the first column because
    # utils.get_TAB_delimited_file_as_dictionary doesn't really care about it.
    return ["path", "external_gene_calls", "gene_functional_annotation"]

