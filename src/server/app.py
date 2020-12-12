# -- Imports --------------------------------------------------------------------------

from sanic import Sanic, Blueprint
from threading import Thread
from gspread import authorize
from oauth2client.service_account import ServiceAccountCredentials
from limits.strategies import FixedWindowElasticExpiryRateLimiter
from limits.storage import MemoryStorage, RedisStorage
from copy import copy
from .middlewares import middlewares
from .routes import blueprints
from .. import moca_modules as mzk
from .. import core

# -------------------------------------------------------------------------- Imports --

# -- App --------------------------------------------------------------------------

# Server header.
if 'server' not in map(lambda i: i.lower(), core.SERVER_CONFIG['headers'].keys()):
    core.SERVER_CONFIG['headers']['Server'] = f'MocaFileLog({core.VERSION})'
# Access-Control-Allow-Credentials header.
if core.SERVER_CONFIG['access_control_allowed_credentials']:
    core.SERVER_CONFIG['headers']['Access-Control-Allow-Credentials'] = True
else:
    pass
# Access-Control-Allow-Headers header.
if '*' in core.SERVER_CONFIG['access_control_allow_headers']:
    core.SERVER_CONFIG['headers']['Access-Control-Allow-Headers'] = '*'
else:
    core.SERVER_CONFIG['headers']['Access-Control-Allow-Headers'] = ', '.join(
        core.SERVER_CONFIG['access_control_allow_headers']
    )
# Access-Control-Allow-Methods header.
if '*' in core.SERVER_CONFIG['access_control_allowed_methods']:
    core.SERVER_CONFIG['headers']['Access-Control-Allow-Methods'] = '*'
else:
    core.SERVER_CONFIG['headers']['Access-Control-Allow-Methods'] = ', '.join(
        core.SERVER_CONFIG['access_control_allowed_methods']
    )
# Access-Control-Max-Age header.
core.SERVER_CONFIG['headers']['Access-Control-Allow-Methods'] = int(
    core.SERVER_CONFIG['access_control_max_age']
)
# Access-Control-Expose-Headers
if '*' in core.SERVER_CONFIG['access_control_expose_headers']:
    core.SERVER_CONFIG['headers']['Access-Control-Expose-Headers'] = '*'
else:
    core.SERVER_CONFIG['headers']['Access-Control-Expose-Headers'] = ', '.join(
        core.SERVER_CONFIG['access_control_expose_headers']
    )


# Sanic App
moca_sanic: mzk.MocaSanic = mzk.MocaSanic(
    f'MocaFileLog({core.VERSION})',
    app=None,
    host=None,
    port=None,
    unix=None,
    ssl=None,
    certfile=core.SERVER_CONFIG['ssl']['cert'],
    keyfile=core.SERVER_CONFIG['ssl']['key'],
    log_dir=core.LOG_DIR,
    internal_key=None,
    access_log=core.SERVER_CONFIG['access_log'],
    log_level=core.SERVER_CONFIG['log_level'],
    use_ipv6=None,
    workers=1,
    headers=core.SERVER_CONFIG['headers'],
    debug=core.SERVER_CONFIG['debug'],
    auto_reload=core.SERVER_CONFIG['auto_reload'],
    websocket=True,
    backlog=core.SERVER_CONFIG['backlog'],
    origins=core.SERVER_CONFIG['access_control_allowed_origins'],
)

moca_sanic.load_sanic_server_configs(core.SANIC_CONFIG)
app: Sanic = moca_sanic.app


def run_app(name: str, host: str, port: int, use_ipv6: bool, file: str, level: int) -> None:
    moca_sanic._host = host
    moca_sanic._port = port
    moca_sanic._use_ipv6 = use_ipv6
    moca_sanic.app._log_name = name
    moca_sanic.app._host = host
    moca_sanic.app._port = port
    moca_sanic.app._use_ipv6 = use_ipv6
    moca_sanic.app._log_file_path = file
    moca_sanic.app._log_level = level
    moca_sanic.run()


# set event listener
async def before_server_start(app_: Sanic, loop):
    mzk.set_process_name(f'MocaFileLog --- {app_._log_name}')
    mzk.print_info(f'Starting Sanic server. -- {mzk.get_my_pid()}')

    app_.system_config: mzk.MocaConfig = mzk.MocaConfig(
        core.SYSTEM_CONFIG, manual_reload=True
    )
    app_.ip_blacklist: mzk.MocaSynchronizedJSONListFile = mzk.MocaSynchronizedJSONListFile(
        core.IP_BLACKLIST_FILE, manual_reload=True, remove_duplicates=True,
    )
    app_.api_key_config: mzk.MocaSynchronizedJSONListFile = mzk.MocaSynchronizedJSONListFile(
        core.API_KEY_FILE, manual_reload=True
    )
    app_.dict_cache = {}
    if app_._log_file_path.startswith('/'):
        file = app_._log_file_path
    else:
        file = core.CLIENT_LOG_DIR.joinpath(app_._log_file_path)
    app_.moca_log = mzk.MocaFileLog(file, app_._log_level)
    app_.secure_log = mzk.MocaFileLog(core.LOG_DIR.joinpath('secure.log'))
    app_.scheduler = mzk.MocaScheduler()
    app_.log_list = []
    if core.SERVER_CONFIG['rate_limiter_redis_storage'] is None:
        app_._storage_for_rate_limiter = MemoryStorage()
    else:
        app_._storage_for_rate_limiter = RedisStorage(core.SERVER_CONFIG['rate_limiter_redis_storage'])
    app_.rate_limiter = FixedWindowElasticExpiryRateLimiter(app_._storage_for_rate_limiter)

    if core.LOG_CONFIG[app_._log_name].get('google_spread_sheets_auth', None) is not None:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        app_._credentials = ServiceAccountCredentials.from_json_keyfile_name(
            str(core.CONFIG_DIR.joinpath(core.LOG_CONFIG[app_._log_name].get('google_spread_sheets_auth'))),
            scope,
        )
        app_._gc = authorize(app_._credentials)
        app_.workbook = app_._gc.open_by_key(core.LOG_CONFIG[app_._log_name].get('spread_sheets_key'))
    else:
        app_.workbook = None

    def __reload_timer(application: Sanic) -> None:
        while True:
            mzk.sleep(1)
            application.system_config.reload_file()
            application.ip_blacklist.reload_file()
            application.api_key_config.reload_file()

    app_._timer_thread = Thread(target=__reload_timer, args=(app_,), daemon=True)
    app_._timer_thread.start()


async def after_server_start(app_: Sanic, loop):
    mzk.print_info(f'Started Sanic server. -- {mzk.get_my_pid()}')

    # run scheduled tasks.
    def dos_detect():
        info = copy(app_.dict_cache.get('dos-detect'))
        app_.dict_cache['dos-detect'] = {}
        if info is None:
            return None
        for ip, count in info.items():
            if count > core.system_config.get_config('dos_detect', int, 5000):
                app_.ip_blacklist.append(ip)
                app_.secure_log.write_log(
                    f"Add {ip} to the blacklist. <dos_detection>",
                    mzk.LogLevel.WARNING
                )

    def sync_with_spread_sheets():
        if len(app_.log_list) == 0:
            return None
        if app_.workbook is not None:
            workbook = app_.workbook
            if len(workbook.worksheets()) == 1 and not workbook.worksheets()[0].title.startswith('1-'):
                workbook.add_worksheet(title='1-0', rows=5001, cols=3)
                workbook.del_worksheet(workbook.worksheets()[0])
                a1, b1, c1 = workbook.worksheets()[0].range('A1:C1')
                a1.value, b1.value, c1.value = 'Level', 'Timestamp', 'Message'
                workbook.worksheets()[0].update_cells([a1, b1, c1])
            else:
                latest = workbook.worksheets()[-1]
                start, end = int(latest.title.split('-')[0]), int(latest.title.split('-')[1])
                index = end - start + 3
                if index == 5002:
                    workbook.add_worksheet(title=f'{end+1}-{end}', rows=5001, cols=3)
                    a1, b1, c1 = workbook.worksheets()[-1].range('A1:C1')
                    a1.value, b1.value, c1.value = 'Level', 'Timestamp', 'Message'
                    workbook.worksheets()[-1].update_cells([a1, b1, c1])
                    latest = workbook.worksheets()[-1]
                    start, end = int(latest.title.split('-')[0]), int(latest.title.split('-')[1])
                    index = end - start + 3
                if (index + len(app_.log_list)) <= 5002:
                    log_list = app_.log_list
                    app_.log_list = []
                else:
                    log_list = app_.log_list[:5002-index]
                    app_.log_list[:5002 - index] = []
                cell_list = latest.range(f'A{index}:C{index + len(log_list)-1}')
                i = 0
                for level, timestamp, message in log_list:
                    cell_list[i].value, cell_list[i+1].value, cell_list[i+2].value = level, timestamp, message
                    i += 3
                latest.update_cells(cell_list)
                index += len(log_list)
                latest.update_title(f'{start}-{index + start - 3}')

    app_.scheduler.add_event_per_second('Dos-detect', dos_detect, 5)
    app_.scheduler.add_event_per_second('Sync-With-Spread-Sheets', sync_with_spread_sheets, 5)


async def before_server_stop(app_: Sanic, loop):
    mzk.print_info(f'Stopping Sanic server. -- {mzk.get_my_pid()}')


async def after_server_stop(app_: Sanic, loop):
    mzk.print_info(f'Stopped Sanic server. -- {mzk.get_my_pid()}')


moca_sanic.before_server_start = before_server_start
moca_sanic.after_server_start = after_server_start
moca_sanic.before_server_stop = before_server_stop
moca_sanic.after_server_stop = after_server_stop


# Middleware
for item in middlewares.values():
    moca_sanic.add_middleware(item[1], item[0])


# Blueprint
app.blueprint(Blueprint.group(*blueprints, url_prefix='/moca-file-log'))

# -------------------------------------------------------------------------- App --
