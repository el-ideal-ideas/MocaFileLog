# -- Imports --------------------------------------------------------------------------

from typing import (
    Any, List, Dict, Tuple, Optional, Union
)
from aioredis import create_pool
from ssl import SSLContext
from ..moca_utils import moca_dumps as dumps, moca_loads as loads, get_random_string

# -------------------------------------------------------------------------- Imports --

# -- Moca Redis --------------------------------------------------------------------------


class MocaRedis:
    """
    Redis database.

    Attributes
    ----------
    self._host: str
        the host ip address for the redis database.
    self._port: int
        the port number for the redis database.
    self._db: int
        the index number for the redis database.
    self._password: str
        the password for the redis database.
    self._minsize: int
        minimum size of the connection pool.
    self._maxsize: int
        maximum size of the connection pool.
    self._ssl: Optional[SSLContext]
         ssl context for the redis database.
    self._pool
        the async redis connection pool.
    """

    def __init__(
            self,
            host: str,
            port: int,
            db: int,
            password: str,
            minsize: int = 1,
            maxsize: int = 10,
            ssl: Optional[SSLContext] = None):
        """
        :param host: the host ip address for the redis database.
        :param port: the port number for the redis database.
        :param db: the index number for the redis database.
        :param password: the password for the redis database.
        :param minsize: minimum size of the connection pool.
        :param maxsize: maximum size of the connection pool.
        :param ssl: ssl context for the redis database.
        """
        # set parameters
        self._host: str = host
        self._port: int = port
        self._db: int = db
        self._password: str = password
        self._minsize: int = minsize
        self._maxsize: int = maxsize
        self._ssl: Optional[SSLContext] = ssl
        self._pool = None

    @property
    def url(self) -> str:
        return f'redis://{":" if self._password != "" else ""}{self._password}' \
               f'@{self._host}' \
               f':{self._port}' \
               f'/{self._db}'

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def db(self) -> int:
        return self._db

    @property
    def minsize(self) -> int:
        return self._minsize

    @property
    def maxsize(self) -> int:
        return self._maxsize

    @property
    def ssl(self) -> Optional[SSLContext]:
        return self._ssl

    async def get_aio_pool(self):
        """Return a async connection pool, if not exists, create a new onw."""
        if self._pool is None:
            pool = await create_pool((self._host, self._port),
                                     db=self._db,
                                     password=self._password if self._password != '' else None,
                                     minsize=self._minsize,
                                     maxsize=self._maxsize,
                                     ssl=self._ssl)
            self._pool = pool
        else:
            pool = self._pool
        return pool

    async def create_aio_pool(self):
        """Create a new async connection pool."""
        pool = await create_pool((self._host, self._port),
                                 db=self._db,
                                 password=self._password if self._password != '' else None,
                                 minsize=self._minsize,
                                 maxsize=self._maxsize,
                                 ssl=self._ssl)
        if self._pool is None:
            self._pool = pool
        return pool

    async def execute(self, command, *args, **kwargs):
        """Execute a redis command."""
        pool = await self.get_aio_pool()
        async with pool.get() as redis:
            result = await redis.execute(command, *args, **kwargs)
            return result

    async def set(self, key: str, value: Any, expiration: int = -1):
        if expiration == -1:
            await self.execute('SET', 'mr-' + key, dumps(value))
        else:
            await self.execute('SETEX', 'mr-' + key, expiration, dumps(value))

    async def set_multi(self, data: List[Tuple[str, Any]], expiration: int = -1):
        if expiration == -1:
            tmp: List[Union[str, bytes]] = []
            for value in data:
                tmp.append('mr-' + value[0])
                tmp.append(dumps(value[1]))
            await self.execute('MSET', *tmp)
        else:
            pool = await self.get_aio_pool()
            async with pool.get() as redis:
                for value in data:
                    await redis.execute('SETEX', 'mr-' + value[0], expiration, dumps(value[1]))

    async def get(self, key: str, default: Any = None) -> Any:
        data = await self.execute('GET', 'mr-' + key)
        if data is None:
            return default
        else:
            return loads(data)

    async def get_multi(self, keys: List[str]) -> Dict:
        data_list = await self.execute('MGET', *['mr-' + value for value in keys])
        result: Dict = {}
        index = 0
        for data in data_list:
            if data is None:
                result[keys[index]] = None
            else:
                result[keys[index]] = loads(data)
            index += 1
        return result

    async def rpush(self, key: str, value: Any):
        await self.execute('RPUSH', 'mr-' + key, dumps(value))

    async def lpush(self, key: str, value: Any):
        await self.execute('LPUSH', 'mr-' + key, dumps(value))

    async def rpop(self, key: str) -> Any:
        return loads(await self.execute('RPOP', 'mr-' + key))

    async def lpop(self, key: str) -> Any:
        return loads(await self.execute('LPOP', 'mr-' + key))

    async def lrange(self, key: str, start: int, end: int) -> Any:
        data = await self.execute('LRANGE', 'mr-' + key, start, end)
        return [loads(item) for item in data]

    async def lindex(self, key: str, index: int) -> Any:
        return loads(await self.execute('LINDEX', 'mr-' + key, index))

    async def llen(self, key: str) -> int:
        return await self.execute('LLEN', 'mr-' + key)

    async def ltrim(self, key: str, start: int, end: int) -> None:
        await self.execute('LTRIM', 'mr-' + key, start, end)

    async def delete(self, key: str):
        await self.execute('DEL', 'mr-' + key)

    async def delete_multi(self, keys: List[str]):
        await self.execute('DEL', *['mr-' + value for value in keys])

    async def flush_db(self):
        await self.execute('FLUSHDB', 'ASYNC')

    async def get_db_size(self):
        return await self.execute('DBSIZE')

    async def get_db_info(self):
        return (await self.execute('INFO')).decode()

    async def get_last_save_time(self):
        return await self.execute('LASTSAVE')

    async def save_db(self):
        await self.execute('BGSAVE')

    async def increment(self, key: str):
        return await self.execute('INCR', 'mr-' + key)

    async def increment_by(self, key: str, value: int):
        return await self.execute('INCRBY', 'mr-' + key, value)

    async def decrement(self, key: str):
        return await self.execute('DECR', 'mr-' + key)

    async def decrement_by(self, key: str, value: int):
        return await self.execute('DECRBY', 'mr-' + key, value)

    async def test_con(self) -> None:
        key = 'moca_modules_connection_test_key' + get_random_string(32)
        await self.set(key, 0)
        await self.delete(key)

# -------------------------------------------------------------------------- Moca Redis --
