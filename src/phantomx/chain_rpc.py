from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.error import URLError
from urllib.request import Request, urlopen


class RpcError(RuntimeError):
    """Raised when an RPC response is unusable or untrustworthy."""


class RpcTransport(Protocol):
    def request(self, method: str, params: list[Any]) -> Any: ...


class JsonRpcTransport:
    def __init__(self, endpoint: str, timeout_seconds: float = 5.0) -> None:
        if not endpoint.startswith(("http://", "https://")):
            raise ValueError("RPC endpoint must be HTTP(S)")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._endpoint = endpoint
        self._timeout = timeout_seconds
        self._next_id = 1

    def request(self, method: str, params: list[Any]) -> Any:
        request_id = self._next_id
        self._next_id += 1
        payload = json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}).encode("utf-8")
        request = Request(self._endpoint, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=self._timeout) as response:
                body = response.read()
        except (OSError, URLError) as exc:
            raise RpcError(f"RPC transport failure: {exc}") from exc
        try:
            message = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RpcError("RPC returned invalid JSON") from exc
        if message.get("error") is not None:
            raise RpcError(f"RPC error: {message['error']}")
        if "result" not in message:
            raise RpcError("RPC response missing result")
        return message["result"]


@dataclass(frozen=True)
class ChainHead:
    chain_id: int
    block_number: int


class ChainRpcAdapter:
    def __init__(self, transport: RpcTransport) -> None:
        self._transport = transport

    def chain_id(self) -> int:
        return _hex_int(self._transport.request("eth_chainId", []))

    def block_number(self) -> int:
        return _hex_int(self._transport.request("eth_blockNumber", []))

    def head(self) -> ChainHead:
        return ChainHead(chain_id=self.chain_id(), block_number=self.block_number())

    def code_at(self, address: str, block_tag: str = "latest") -> bytes:
        _validate_address(address)
        result = self._transport.request("eth_getCode", [address, block_tag])
        if not isinstance(result, str) or not result.startswith("0x"):
            raise RpcError("eth_getCode returned malformed result")
        try:
            return bytes.fromhex(result[2:])
        except ValueError as exc:
            raise RpcError("eth_getCode returned invalid hex") from exc

    def eth_call(self, to: str, data: str, block_tag: str = "latest") -> bytes:
        _validate_address(to)
        if not data.startswith("0x") or len(data) % 2 != 0:
            raise ValueError("call data must be even-length 0x-prefixed hex")
        result = self._transport.request("eth_call", [{"to": to, "data": data}, block_tag])
        if not isinstance(result, str) or not result.startswith("0x"):
            raise RpcError("eth_call returned malformed result")
        try:
            return bytes.fromhex(result[2:])
        except ValueError as exc:
            raise RpcError("eth_call returned invalid hex") from exc


def encode_address_argument(address: str) -> str:
    _validate_address(address)
    return address[2:].lower().rjust(64, "0")


def encode_get_pair(token_a: str, token_b: str) -> str:
    return "0xe6a43905" + encode_address_argument(token_a) + encode_address_argument(token_b)


def decode_address(raw: bytes) -> str:
    if len(raw) < 32:
        raise RpcError("address response is too short")
    return "0x" + raw[-20:].hex()


def decode_uint256(raw: bytes) -> int:
    if len(raw) < 32:
        raise RpcError("uint256 response is too short")
    return int.from_bytes(raw[-32:], "big")


def decode_get_reserves(raw: bytes) -> tuple[int, int, int]:
    if len(raw) < 96:
        raise RpcError("getReserves response is too short")
    return (int.from_bytes(raw[0:32], "big"), int.from_bytes(raw[32:64], "big"), int.from_bytes(raw[64:96], "big"))


def _hex_int(value: Any) -> int:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise RpcError("expected 0x-prefixed integer")
    try:
        return int(value, 16)
    except ValueError as exc:
        raise RpcError("invalid hexadecimal integer") from exc


def _validate_address(address: str) -> None:
    if not isinstance(address, str) or len(address) != 42 or not address.startswith("0x"):
        raise ValueError(f"invalid EVM address: {address!r}")
    try:
        int(address[2:], 16)
    except ValueError as exc:
        raise ValueError(f"invalid EVM address: {address!r}") from exc
