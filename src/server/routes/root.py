# -- Imports --------------------------------------------------------------------------

from pathlib import Path
from sanic import Blueprint
from sanic.request import Request
from sanic.exceptions import Forbidden
from sanic.response import HTTPResponse, text, json as original_json, file
from orjson import dumps as orjson_dumps
from functools import partial
json = partial(original_json, dumps=orjson_dumps)
from ... import moca_modules as mzk
from .utils import check_root_pass

# -------------------------------------------------------------------------- Imports --

# -- Blueprint --------------------------------------------------------------------------

root: Blueprint = Blueprint('root', None)


@root.route('/details', {'GET', 'POST', 'OPTIONS'})
async def details(request: Request) -> HTTPResponse:
    check_root_pass(request)
    size = int(mzk.check_output(f'wc -c < "{request.app.moca_log.filename}"', shell=True).decode().strip())
    count = int(mzk.check_output(f'wc -l "{request.app.moca_log.filename}"', shell=True).decode().strip().split()[0])
    return json({
        'name': request.app._log_name,
        'host': request.app._host,
        'port': request.app._port,
        'use_ipv6': request.app._use_ipv6,
        'file': request.app._log_file_path,
        'count': count,
        'size': size,
        'size(MB)': round(size / 1024 / 1024, 2)
    })


@root.route('/save-log', {'GET', 'POST', 'OPTIONS'})
async def save_log(request: Request) -> HTTPResponse:
    level, msg = mzk.get_args(
        request,
        ('level', int, 1, {'is_in': [0, 1, 2, 3, 4]}),
        ('message|msg', str, None, {'max_length': 8192}),
    )
    if msg is None:
        raise Forbidden('message parameter format error.')
    request.app.log_list.append((level, mzk.get_time_string(), msg))
    request.app.moca_log.write_log(msg, level)
    return text('success.')


@root.route('/save-logs', {'GET', 'POST', 'OPTIONS'})
async def save_logs(request: Request) -> HTTPResponse:
    logs, *_ = mzk.get_args(
        request,
        ('logs', list, None, {'max_length': 1024}),
    )
    if logs is None:
        raise Forbidden('logs parameter format error.')
    for log in logs:
        try:
            level, msg = log['level'], log.get('message', log['msg'])
            if level in [0, 1, 2, 3, 4] and isinstance(msg, str) and len(msg) <= 8192:
                request.app.log_list.append((level, mzk.get_time_string(), msg))
                request.app.moca_log.write_log(msg, level)
            else:
                raise Forbidden('logs parameter format error.')
        except KeyError:
            raise Forbidden('logs parameter format error.')
    return text('success.')


@root.route('/download-logs', {'GET', 'POST', 'OPTIONS'})
async def download_logs(request: Request) -> HTTPResponse:
    check_root_pass(request)
    return await file(
        request.app.moca_log.filename,
        mime_type='text/plain',
        filename=Path(request.app.moca_log.filename).name
    )


@root.route('/get-logs', {'GET', 'POST', 'OPTIONS'})
async def get_logs(request: Request) -> HTTPResponse:
    check_root_pass(request)
    return text(
        await mzk.aio_get_str_from_file(request.app.moca_log.filename)
    )


@root.route('/get-latest-logs', {'GET', 'POST', 'OPTIONS'})
async def get_latest_logs(request: Request) -> HTTPResponse:
    check_root_pass(request)
    res = mzk.check_output(f'cat "{request.app.moca_log.filename}" | tail -n 1024', shell=True).decode().splitlines()
    res.reverse()
    return json(res)


@root.route('/clear-logs', {'GET', 'POST', 'OPTIONS'})
async def clear_log(request: Request) -> HTTPResponse:
    check_root_pass(request)
    request.app.moca_log.clear_log()
    return text('success.')

# -------------------------------------------------------------------------- Blueprint --
