from os import getenv
from typing import Union
from typing_extensions import Annotated
from datetime import date as _date, datetime as _datetime
from json import loads
from socket import gethostname, gethostbyname
from traceback import print_exception

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


# init global objects

__version__ = '0.01'

ECHO = True

async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except ConnectionError as e:
        if ECHO:
            print_exception(e)
        return Response(f"Internal server error: {e}", status_code=500)


app = FastAPI(title='yieldcurves')


@app.get("/")
async def root():
    return {'detail': f'HCB API in version {__version__}'}


@app.get("/v01/prices/currency")
async def fx_rates(start: str, end: str, last: int):
    return ...

@app.get("/v01/prices/bond")
async def bond_prices(start: str, end: str, last: int):
    return ...

@app.get("/v01/prices/equity")
async def stock_prices(start: str, end: str, last: int):
    return ...

@app.get("/v01/prices/commodity")
async def stock_prices(start: str, end: str, last: int):
    return ...


@app.get("/v01/yields/bond")
async def yieldcurves(start: str, end: str, last: int):
    return ...

@app.get("/v01/volatilities/currency")
async def volatililities(start: str, end: str, last: int):
    return ...

@app.get("/v01/volatilities/interestrate")
async def volatililities(start: str, end: str, last: int):
    return ...

@app.get("/v01/volatilities/equity")
async def volatililities(start: str, end: str, last: int):
    return ...
