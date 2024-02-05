from typing import Dict
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, Response
from tabor_client import TaborClient, TaborClientSocketException

api = FastAPI()

global ACTIVE_CLIENTS
ACTIVE_CLIENTS: Dict[str, TaborClient] = {}


def get_client(hostname: str = None, port: int = 5025):
    con_str = f"{hostname}:{port}"
    client: TaborClient = ACTIVE_CLIENTS.get(con_str, None)
    if client is None:
        client = TaborClient(host=hostname, port=port)
        ACTIVE_CLIENTS[con_str] = client
    return client


def to_error_response(ex: TaborClientSocketException):
    return Response(
        content=f"{ex.message}:{ex.code}",
        status_code=502,
    )


@api.get("/")
def tabor_client_redirect_root():
    return RedirectResponse("/docs#")


@api.get("/connect")
def tabor_client_connect(hostname: str, port: int = 5025, query: str = "*IDN?"):
    client = get_client(hostname, port)
    try:
        client.connect()
        return client.query(query)
    except TaborClientSocketException as ex:
        return to_error_response(ex)


@api.get("/query")
def tabor_client_query(
    hostname: str,
    query: str,
    port: int = 5025,
):
    try:
        return get_client(hostname, port).query(query)
    except TaborClientSocketException as ex:
        return to_error_response(ex)


@api.get("/command")
def tabor_client_command(
    hostname: str,
    command: str,
    port: int = 5025,
):
    try:
        return get_client(hostname, port).command(command)
    except TaborClientSocketException as ex:
        return to_error_response(ex)


if __name__ == "__main__":
    from uvicorn import run
    import logging

    run(
        api,
        host="0.0.0.0",
        port=9090,
        log_level=logging.ERROR,
    )
