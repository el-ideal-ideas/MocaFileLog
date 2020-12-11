# -- Imports --------------------------------------------------------------------------

from sanic import __version__
from sys import version_info
from .. import moca_modules as mzk
from .. import core

# -------------------------------------------------------------------------- Imports --

# -- Console --------------------------------------------------------------------------

console = mzk.typer_console


@console.command('version')
def version(only_number: bool = False) -> None:
    """Show the version info of MocaSystem."""
    if only_number:
        mzk.tsecho(core.VERSION)
    else:
        mzk.tsecho(f'MocaFileLog ({core.VERSION})')


@console.command('update')
def update() -> None:
    """Update modules."""
    path = mzk.TMP_DIR.joinpath('moca_commands_installed_modules.txt')
    mzk.call(f'{mzk.executable} -m pip freeze > {path}', shell=True)
    mzk.call(f'{mzk.executable} -m pip uninstall -r {path} -y', shell=True)
    mzk.install_requirements_file(core.TOP_DIR.joinpath('requirements.txt'))


@console.command('update-system')
def update_system() -> None:
    """Update system, get latest code from github."""
    mzk.update_use_github(
        core.TOP_DIR,
        'https://github.com/el-ideal-ideas/MocaFileLog',
        [
            core.CONFIG_DIR,
            core.LOG_DIR,
            core.CLIENT_LOG_DIR,
            core.TOP_DIR.joinpath('keep'),
            core.TOP_DIR.joinpath('atexit.py'),
            core.TOP_DIR.joinpath('atexit.sh'),
            core.TOP_DIR.joinpath('startup.py'),
            core.TOP_DIR.joinpath('startup.sh'),
        ]
    )


@console.command('reset-system')
def reset_system() -> None:
    """Reset this system."""
    mzk.update_use_github(
        core.TOP_DIR,
        'https://github.com/el-ideal-ideas/MocaFileLog',
        []
    )


@console.command('__run', hidden=True)
def run_server(name: str) -> None:
    """Run server."""
    config = core.LOG_CONFIG.get(name)
    if config is None:
        mzk.print_error(f'Unknown log config. <{name}>')
        mzk.sys_exit(1)
    try:
        from ..server import run_app
        run_app(name, config['host'], int(config['port']), config['use_ipv6'], config['file'], config['level'])
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as error:
        mzk.print_critical(str(error))
        mzk.print_exc()
        mzk.append_str_to_file(core.LOG_DIR.joinpath('critical.log'), str(error))
        mzk.append_str_to_file(core.LOG_DIR.joinpath('critical.log'), mzk.format_exc())


@console.command('run')
def run(name: str, sleep: float = 0) -> None:
    """Run MocaFileLog."""
    try:
        mzk.sleep(sleep)
        # run startup script.
        mzk.call(f'{mzk.executable} "{core.TOP_DIR.joinpath("startup.py")}"', shell=True)
        mzk.call(
            f'chmod +x "{core.TOP_DIR.joinpath("startup.sh")}";sh "{core.TOP_DIR.joinpath("startup.sh")}"', shell=True
        )
        mzk.call(
            f'{mzk.executable} "{core.TOP_DIR.joinpath("moca.py")}" __run {name}',
            shell=True
        )
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as error:
        mzk.print_critical(str(error))
        mzk.print_exc()
        mzk.append_str_to_file(core.LOG_DIR.joinpath('critical.log'), str(error))
        mzk.append_str_to_file(core.LOG_DIR.joinpath('critical.log'), mzk.format_exc())
    finally:
        # run atexit script.
        mzk.call(f'{mzk.executable} "{core.TOP_DIR.joinpath("atexit.py")}"', shell=True)
        mzk.call(
            f'chmod +x "{core.TOP_DIR.joinpath("atexit.sh")}";sh "{core.TOP_DIR.joinpath("atexit.sh")}"', shell=True
        )


@console.command('start')
def start(sleep: float = 0) -> None:
    """Run MocaFileLog in background."""
    mzk.sleep(sleep)
    for name in core.LOG_CONFIG:
        mzk.call(
            f'nohup {mzk.executable} {core.TOP_DIR.joinpath("moca.py")} __run {name} &> /dev/null &',
            shell=True
        )


@console.command('stop')
def stop(sleep: float = 0) -> None:
    """Stop MocaFileLog."""
    mzk.sleep(sleep)
    pid = []
    for line in mzk.check_output('ps -ef | grep MocaFileLog', shell=True).decode().splitlines():
        pid.append(line.split()[1])
    mzk.call(f'kill {" ".join(pid)} &> /dev/null &', shell=True)


@console.command('restart')
def restart(sleep: float = 0) -> None:
    """Restart MocaFileLog."""
    mzk.sleep(sleep)
    mzk.call(f'nohup {mzk.executable} {core.TOP_DIR.joinpath("moca.py")} stop &> /dev/null &', shell=True)
    mzk.sleep(3)
    mzk.call(f'nohup {mzk.executable} {core.TOP_DIR.joinpath("moca.py")} start &> /dev/null &', shell=True)
    mzk.sleep(3)


@console.command('status')
def show_running_process() -> None:
    """Show all MocaFileLog process."""
    print('++++++++++++++++++++++++++++++++++++++++++++++')
    print(f'Python: {version_info.major}.{version_info.minor}.{version_info.micro}')
    print(f'MocaSystem: {core.VERSION}')
    print(f'MocaModules: {mzk.VERSION}')
    print(f'MocaSanic: {mzk.MocaSanic.VERSION}')
    print(f'Sanic: {__version__}')
    print('++++++++++++++++++++++++++++++++++++++++++++++')
    print('PID\tPPID\tNAME')
    for line in mzk.check_output('ps -ef | grep MocaFileLog', shell=True).decode().splitlines():
        items = line.split()
        if items[7].startswith('MocaFileLog'):
            print(f"{items[1]}\t{items[2]}\t{' '.join(items[7:])}")
    print('++++++++++++++++++++++++++++++++++++++++++++++')


@console.command('turn-on')
def turn_on() -> None:
    """Stop maintenance mode."""
    core.system_config.set_config('maintenance_mode', False)
    mzk.tsecho('Stopped maintenance mode. MocaSanic is working.', fg=mzk.tcolors.GREEN)


@console.command('turn-off')
def turn_off() -> None:
    """Start maintenance mode."""
    core.system_config.set_config('maintenance_mode', True)
    mzk.tsecho('MocaSystem is currently undergoing maintenance. All requests will receive 503.', fg=mzk.tcolors.GREEN)


@console.command('clear-logs')
def clear_logs() -> None:
    """Clear log files."""
    mzk.call(f'rm -rf {core.LOG_DIR}/*', shell=True)

# -------------------------------------------------------------------------- Console --