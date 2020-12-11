# -- Imports --------------------------------------------------------------------------

from pathlib import Path
from .. import moca_modules as mzk

# -------------------------------------------------------------------------- Imports --

# -- Variables --------------------------------------------------------------------------

# version
VERSION: str = mzk.get_str_from_file(Path(__file__).parent.joinpath('.version'))

# path
TOP_DIR: Path = Path(__file__).parent.parent.parent
CONFIG_DIR: Path = TOP_DIR.joinpath('configs')
LOG_DIR: Path = TOP_DIR.joinpath('logs')
CLIENT_LOG_DIR: Path = TOP_DIR.joinpath('client_logs')
SRC_DIR: Path = TOP_DIR.joinpath('src')

# create directories if not exists.
for __dir in [CONFIG_DIR, LOG_DIR, CLIENT_LOG_DIR]:
    __dir.mkdir(parents=True, exist_ok=True)
del __dir

# configs
SYSTEM_CONFIG: Path = CONFIG_DIR.joinpath('system.json')
SERVER_CONFIG: dict = mzk.load_json_from_file(CONFIG_DIR.joinpath('server.json'))
SANIC_CONFIG: dict = mzk.load_json_from_file(CONFIG_DIR.joinpath('sanic.json'))
LOG_CONFIG: dict = mzk.load_json_from_file(CONFIG_DIR.joinpath('log.json'))
IP_BLACKLIST_FILE: Path = CONFIG_DIR.joinpath('ip_blacklist.json')
API_KEY_FILE: Path = CONFIG_DIR.joinpath('api_key.json')
system_config: mzk.MocaConfig = mzk.MocaConfig(SYSTEM_CONFIG, manual_reload=True)
ip_blacklist: mzk.MocaSynchronizedJSONListFile = mzk.MocaSynchronizedJSONListFile(
    IP_BLACKLIST_FILE, manual_reload=True, remove_duplicates=True,
)
api_key_config: mzk.MocaSynchronizedJSONListFile = mzk.MocaSynchronizedJSONListFile(
    API_KEY_FILE, manual_reload=True
)

# -------------------------------------------------------------------------- Variables --
