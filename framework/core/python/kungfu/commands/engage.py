import click
import kungfu
import pkgutil
import os
import sys
import subprocess

from os.path import abspath, basename, dirname

from kungfu.commands import kfc, pass_ctx_from_parent as pass_ctx_from_root
from kungfu.commands import PrioritizedCommandGroup
from kungfu.yijinjing.log import create_logger


@kfc.group(cls=PrioritizedCommandGroup, help_priority=-1)
@click.help_option("-h", "--help")
@click.pass_context
def engage(ctx):
    pass_ctx_from_root(ctx)
    ctx.logger = create_logger("engage", ctx.log_level, ctx.console_location)


def pass_ctx_from_parent(ctx):
    pass_ctx_from_root(ctx)
    ctx.logger = ctx.parent.logger


@engage.command(
    help="Format python files with [Black](https://github.com/psf/black)",
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.pass_context
def black(ctx):
    pass_ctx_from_parent(ctx)

    sys.argv = [sys.argv[0], *ctx.args]
    from black.__main__ import patched_main as main

    main()


@engage.command(
    help="Manage python packages with [pdm](https://pdm.fming.dev)",
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.pass_context
def pdm(ctx):
    pass_ctx_from_parent(ctx)

    sys.argv = [sys.argv[0], *ctx.args]

    from pdm import core

    class Core(core.Core):
        def __init__(self):
            super().__init__()

        def init_parser(self):
            super().init_parser()
            try:
                from pdm.cli import commands

                next(pkgutil.iter_modules(commands.__path__))
            except StopIteration:
                self.register_cmds()

        def register_cmds(self):
            from pdm.cli.commands import add
            from pdm.cli.commands import build
            from pdm.cli.commands import cache
            from pdm.cli.commands import completion
            from pdm.cli.commands import config
            from pdm.cli.commands import export
            from pdm.cli.commands import import_cmd
            from pdm.cli.commands import info
            from pdm.cli.commands import init
            from pdm.cli.commands import install
            from pdm.cli.commands import list
            from pdm.cli.commands import lock
            from pdm.cli.commands import plugin
            from pdm.cli.commands import remove
            from pdm.cli.commands import run
            from pdm.cli.commands import search
            from pdm.cli.commands import show
            from pdm.cli.commands import sync
            from pdm.cli.commands import update
            from pdm.cli.commands import use

            for module in [
                add,
                build,
                cache,
                completion,
                config,
                export,
                import_cmd,
                info,
                init,
                install,
                list,
                lock,
                plugin,
                remove,
                run,
                search,
                show,
                sync,
                update,
                use,
            ]:
                try:
                    cmd = module.Command
                except AttributeError:
                    continue
                name = cmd.name or module.__name__.split(".").pop()
                core.register_command(cmd, name)

    core = Core()
    core.main()


@engage.command(
    help="Compile and bundle python files with [Nuitka](https://nuitka.net)",
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.pass_context
def nuitka(ctx):
    pass_ctx_from_parent(ctx)

    os.environ["PYTHONPATH"] = os.pathsep.join(sys.path)
    sys.argv = [sys.argv[0], *ctx.args]

    def runDataComposer(source_dir):
        data_composer_opts = (
            [] if basename(sys.executable).startswith("kfc") else ["-m", "kungfu"]
        )
        mapping = {
            "NUITKA_PACKAGE_HOME": dirname(abspath(sys.modules["nuitka"].__path__[0])),
            "PATH": os.environ["PATH"],
            "PYTHONPATH": os.pathsep.join(sys.path),
        }
        from nuitka.build import DataComposerInterface

        blob_filename = DataComposerInterface.getConstantBlobFilename(source_dir)
        with DataComposerInterface.withEnvironmentVarsOverriden(mapping):
            subprocess.check_call(
                [
                    sys.executable,
                    *data_composer_opts,
                    "engage",
                    "nuitka-data-composer",
                    source_dir,
                    blob_filename,
                ],
                shell=False,
            )
        return blob_filename

    def getSconsBinaryCall():
        os.environ["PYTHONPATH"] = (
            dirname(dirname(kungfu.__file__))
            + os.pathsep
            + dirname(kungfu.__bindings__.__file__)
        )
        scons_opts = (
            [] if basename(sys.executable).startswith("kfc") else ["-m", "kungfu"]
        )
        return [sys.executable, *scons_opts, "engage", "nuitka-scons"]

    from nuitka import PythonVersions

    PythonVersions.isStaticallyLinkedPython = lambda: False

    from nuitka.build import DataComposerInterface

    DataComposerInterface.runDataComposer = runDataComposer

    from nuitka.build import SconsInterface

    SconsInterface._getSconsBinaryCall = getSconsBinaryCall

    from nuitka.plugins import Plugins
    from nuitka.plugins.standard import AntiBloat
    from nuitka.plugins.standard import ConsiderPyLintAnnotationsPlugin
    from nuitka.plugins.standard import DataFileCollectorPlugin
    from nuitka.plugins.standard import DillPlugin
    from nuitka.plugins.standard import EnumPlugin
    from nuitka.plugins.standard import EventletPlugin
    from nuitka.plugins.standard import GeventPlugin
    from nuitka.plugins.standard import GlfwPlugin
    from nuitka.plugins.standard import ImplicitImports
    from nuitka.plugins.standard import MultiprocessingPlugin
    from nuitka.plugins.standard import NumpyPlugin
    from nuitka.plugins.standard import PbrPlugin
    from nuitka.plugins.standard import PkgResourcesPlugin
    from nuitka.plugins.standard import PmwPlugin
    from nuitka.plugins.standard import PySidePyQtPlugin
    from nuitka.plugins.standard import TensorflowPlugin
    from nuitka.plugins.standard import TkinterPlugin
    from nuitka.plugins.standard import TorchPlugin
    from nuitka.plugins.standard import ZmqPlugin

    for plugin_module in [
        AntiBloat,
        ConsiderPyLintAnnotationsPlugin,
        DataFileCollectorPlugin,
        DillPlugin,
        EnumPlugin,
        EventletPlugin,
        GeventPlugin,
        GlfwPlugin,
        ImplicitImports,
        MultiprocessingPlugin,
        NumpyPlugin,
        PbrPlugin,
        PkgResourcesPlugin,
        PmwPlugin,
        PySidePyQtPlugin,
        TensorflowPlugin,
        TkinterPlugin,
        TorchPlugin,
        ZmqPlugin,
    ]:
        plugin_classes = set(
            obj
            for obj in plugin_module.__dict__.values()
            if Plugins.isObjectAUserPluginBaseClass(obj)
        )

        detectors = [
            plugin_class
            for plugin_class in plugin_classes
            if hasattr(plugin_class, "detector_for")
        ]

        for detector in detectors:
            plugin_class = detector.detector_for
            assert detector.plugin_name is None, detector
            detector.plugin_name = plugin_class.plugin_name

            if plugin_class not in plugin_classes:
                Plugins.plugins_logger.sysexit(
                    "Plugin detector %r references unknown plugin %r"
                    % (detector, plugin_class)
                )

            plugin_classes.remove(detector)
            plugin_classes.remove(plugin_class)

            Plugins.plugin_name2plugin_classes[plugin_class.plugin_name] = (
                plugin_class,
                detector,
            )

        for plugin_class in plugin_classes:
            Plugins.plugin_name2plugin_classes[plugin_class.plugin_name] = (
                plugin_class,
                None,
            )

    from nuitka import Options

    Options.parseArgs(will_reexec=False)
    Options.commentArgs()

    from nuitka.MainControl import main

    main()


@engage.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
    help_priority=-1,
)
@click.pass_context
def nuitka_data_composer(ctx):
    pass_ctx_from_parent(ctx)

    sys.argv = [sys.argv[0], *ctx.args]

    from nuitka import PythonVersions

    PythonVersions.isStaticallyLinkedPython = lambda: False

    from nuitka.tools.data_composer.DataComposer import main

    main()


@engage.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
    help_priority=-1,
)
@click.pass_context
def nuitka_scons(ctx):
    pass_ctx_from_parent(ctx)

    sys.argv = [sys.argv[0], *ctx.args]

    from nuitka import PythonVersions

    PythonVersions.isStaticallyLinkedPython = lambda: False

    from nuitka.build import SconsUtils

    originCreateEnvironment = SconsUtils.createEnvironment

    def createEnvironment(**kwargs):
        env = originCreateEnvironment(**kwargs)
        env.Append(LIBPATH=dirname(kungfu.__bindings__.__file__))
        return env

    SconsUtils.createEnvironment = createEnvironment

    from SCons.Script import main

    main()