import asyncpg
import typing
import urllib.parse

from fastapi import FastAPI
from settings import *


class ConfigureAsyncpg:
    def __init__(
        self,
        app: FastAPI,
        dsn: str,
        *,
        init_db: typing.Callable = None,  # callable for running sql on init
        pool=None,  # usable on testing
        **options,
    ):
        """This is the entry point to configure an asyncpg pool with fastapi.
        Arguments
            app: The fastapp application that we use to store the pool
                and bind to it's initialitzation events
            dsn: A postgresql desn like postgresql://user:password@postgresql:5432/db
            init_db: Optional callable that receives a db connection,
                for doing an initialitzation of it
            pool: This is used for testing to skip the pool initialitzation
                an just use the SingleConnectionTestingPool
            **options: connection options to directly pass to asyncpg driver
                see: https://magicstack.github.io/asyncpg/current/api/index.html#connection-pools
        """
        self.app = app
        self.dsn = dsn
        self.init_db = init_db
        self.con_opts = options
        self._pool = pool
        self.app.router.add_event_handler("startup", self.on_connect)
        self.app.router.add_event_handler("shutdown", self.on_disconnect)

    async def on_connect(self):
        """handler called during initialitzation of asgi app, that connects to
        the db"""
        # if the pool is comming from outside (tests), don't connect it
        if self._pool:
            self.app.state.pool = self._pool
            return
        pool = await asyncpg.create_pool(dsn=self.dsn, **self.con_opts)
        async with pool.acquire() as db:
            await self.init_db(db)
        self.app.state.pool = pool

    async def on_disconnect(self):
        # if the pool is comming from outside, don't desconnect it
        # someone else will do (usualy a pytest fixture)
        if self._pool:
            return
        await self.app.state.pool.close()

    def on_init(self, func):
        self.init_db = func
        return func

    @property
    def pool(self):
        return self.app.state.pool

    async def connection(self):
        """
        A ready to use connection Dependency just usable
        on your path functions that gets a connection from the pool
        Example:
            db = configure_asyncpg(app, "dsn://")
            @app.get("/")
            async def get_content(db = Depens(db.connection)):
                await db.fetch("SELECT * from pg_schemas")
        """
        async with self.pool.acquire() as db:
            yield db


def get_dsn() -> str:
    escape = lambda x: urllib.parse.quote(x.encode('utf8'))
    username = escape(DB_USERNAME)
    password = escape(DB_PASSWORD)
    db_name = escape(DB_NAME)
    return f"postgres://{username}:{password}@{DB_HOST}:{DB_PORT}/{db_name}"


async def __establish_connection():
    return await asyncpg.connect(get_dsn())


async def fetch_row_simple(command: str) -> asyncpg.Record:
    conn = await __establish_connection()
    row = await conn.fetchrow(command)
    await conn.close()
    return row


async def execute_simple(command: str) -> None:
    conn = await __establish_connection()
    await conn.execute(command)
    await conn.close()
