"""Pure-stdlib teammate protocol; deliberately not wired into the bridge.

Model JSON is exactly {"text": string, "action": "none"|"follow"|"wait"}.
Duplicate/extra keys, type coercions, nonstandard constants and code are never
accepted. Model CR/LF and Unicode line separators become spaces; all other
controls/format characters are rejected, including beyond the truncation point.
Text is bounded to 512 UTF-8 bytes without splitting a code point.

Requests/replies have exactly five LF-separated key=value lines: session, seq,
npc_id, action, text. A final LF is optional; encoder emits it. Values may
contain '='. Unknown/duplicate/missing fields, CRLF, controls and oversized
wire text are rejected, not sanitized. session is 16..128 ASCII alphanumeric,
underscore or hyphen characters. seq is canonical positive decimal <=2**63-1.
npc_id is a canonical nonnegative decimal STRING, <=128 digits; never float.
The sole no-op action is 'none'. Field order on input is irrelevant.

Example integration::

    request = WireMessage(new_session_nonce(), 1, "123", "none", "Come here")
    atomic_write_wire(request_path, request)
    reply = make_reply(request, parse_model_json(model_output))
    atomic_write_wire(reply_path, reply)
    reply = parse_reply(reply_path.read_bytes(), request)  # BEFORE dispatch

Caller owns pending requests: consume once, never reuse sequence numbers, and
use a fresh nonce each session. Correlation is not authentication; keep the
mailbox private. parse_wire/parse_request alone do not check pending identity.
Atomic writes validate first, fsync and close a unique same-directory tempfile,
then os.replace. Readers see old or complete new content. Directory crash
durability and multi-writer arbitration are caller concerns. No credentials,
game APIs, configuration edits or third-party dependencies are involved.
"""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import secrets
import tempfile
import unicodedata

MAX_TEXT_BYTES = 512
MAX_MODEL_BYTES = 262144
MAX_WIRE_BYTES = 4096
MAX_SEQUENCE = (1 << 63) - 1
ACTIONS = frozenset(("none", "follow", "wait"))
_FIELDS = ("session", "seq", "npc_id", "action", "text")
_NONCE = re.compile(r"[A-Za-z0-9_-]{16,128}\Z", re.ASCII)
_DECIMAL = re.compile(r"(?:0|[1-9][0-9]*)\Z", re.ASCII)


class ProtocolError(ValueError):
    """Untrusted model/wire data violates the protocol."""


def _utf8(value, label):
    if type(value) is not str:
        raise ProtocolError(label + " must be a string")
    try:
        return value.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ProtocolError(label + " contains invalid Unicode") from exc


def _text(value):
    if len(_utf8(value, "text")) > MAX_TEXT_BYTES:
        raise ProtocolError("text exceeds UTF-8 byte limit")
    if any(unicodedata.category(c) in ("Cc", "Cf", "Cs", "Zl", "Zp") for c in value):
        raise ProtocolError("text contains a control or line separator")


def _action(value):
    if type(value) is not str or value not in ACTIONS:
        raise ProtocolError("unknown action; expected none, follow, or wait")


def _identity(session, seq, npc_id):
    if type(session) is not str or _NONCE.fullmatch(session) is None:
        raise ProtocolError("invalid session nonce")
    if type(seq) is not int or not 1 <= seq <= MAX_SEQUENCE:
        raise ProtocolError("seq must be a positive 63-bit integer")
    if type(npc_id) is not str or len(npc_id) > 128 or _DECIMAL.fullmatch(npc_id) is None:
        raise ProtocolError("npc_id must be an exact canonical decimal string")


@dataclass(frozen=True)
class ModelReply:
    """Validated decision; use parse_model_json for untrusted JSON."""
    text: str
    action: str

    def __post_init__(self):
        _text(self.text)
        _action(self.action)


@dataclass(frozen=True)
class WireMessage:
    """Validated request/reply; NPC identity never passes through float."""
    session: str
    seq: int
    npc_id: str
    action: str
    text: str

    def __post_init__(self):
        _identity(self.session, self.seq, self.npc_id)
        _action(self.action)
        _text(self.text)


def new_session_nonce():
    """Return a fresh 256-bit ASCII nonce for one session."""
    return secrets.token_hex(32)


def normalize_model_text(text, max_bytes=MAX_TEXT_BYTES):
    """Flatten newlines, reject controls, then truncate at a UTF-8 boundary."""
    if type(max_bytes) is not int or not 0 <= max_bytes <= MAX_TEXT_BYTES:
        raise ProtocolError("invalid text byte limit")
    _utf8(text, "text")
    text = text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    text = text.replace("\u2028", " ").replace("\u2029", " ")
    if any(unicodedata.category(c) in ("Cc", "Cf", "Cs") for c in text):
        raise ProtocolError("model text contains a control character")
    return text.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolError("duplicate JSON property: " + key)
        result[key] = value
    return result


def _reject_constant(value):
    raise ProtocolError("nonstandard JSON constant: " + value)


def _source(value, label, max_bytes):
    if type(value) is bytes:
        if len(value) > max_bytes:
            raise ProtocolError(label + " exceeds byte limit")
        try:
            value = value.decode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise ProtocolError(label + " is not UTF-8") from exc
    if len(_utf8(value, label)) > max_bytes:
        raise ProtocolError(label + " exceeds byte limit")
    return value


def parse_model_json(source, *, max_text_bytes=MAX_TEXT_BYTES):
    """Parse strict JSON (str or UTF-8 bytes) into a bounded ModelReply."""
    source = _source(source, "model JSON", MAX_MODEL_BYTES)
    try:
        obj = json.loads(source, object_pairs_hook=_unique_object,
                         parse_constant=_reject_constant)
    except (ValueError, RecursionError) as exc:
        raise ProtocolError("invalid model JSON: " + str(exc)) from exc
    if type(obj) is not dict or set(obj) != {"text", "action"}:
        raise ProtocolError("model JSON must contain exactly text and action")
    _action(obj["action"])
    return ModelReply(normalize_model_text(obj["text"], max_text_bytes), obj["action"])


def encode_wire(message):
    """Serialize a validated message to canonical LF-terminated UTF-8 bytes."""
    if type(message) is not WireMessage:
        raise ProtocolError("expected WireMessage")
    message.__post_init__()
    return "".join(k + "=" + str(getattr(message, k)) + "\n" for k in _FIELDS).encode("utf-8")


def parse_wire(source):
    """Validate wire syntax; use parse_reply to correlate before dispatch."""
    source = _source(source, "wire message", MAX_WIRE_BYTES)
    if source.endswith("\n"):
        source = source[:-1]
    fields = {}
    for line in source.split("\n"):
        key, separator, value = line.partition("=")
        if not separator or key not in _FIELDS or key in fields:
            raise ProtocolError("invalid, duplicate, or unknown wire field")
        fields[key] = value
    if set(fields) != set(_FIELDS):
        raise ProtocolError("missing wire field")
    seq = fields["seq"]
    if not re.fullmatch(r"[1-9][0-9]{0,18}", seq, flags=re.ASCII):
        raise ProtocolError("noncanonical or out-of-range sequence")
    return WireMessage(fields["session"], int(seq), fields["npc_id"],
                       fields["action"], fields["text"])


def parse_request(source):
    """Validate a request; requests and replies use the same schema."""
    return parse_wire(source)


def make_reply(request, decision):
    """Bind a model decision to the validated request's exact identity."""
    if type(request) is not WireMessage or type(decision) is not ModelReply:
        raise ProtocolError("expected WireMessage and ModelReply")
    request.__post_init__()
    return WireMessage(request.session, request.seq, request.npc_id,
                       decision.action, decision.text)


def parse_reply(source, expected_request):
    """Reject stale sessions and mismatched sequence/NPC before dispatch."""
    if type(expected_request) is not WireMessage:
        raise ProtocolError("expected a validated pending request")
    expected_request.__post_init__()
    reply = parse_wire(source)
    for field in ("session", "seq", "npc_id"):
        if getattr(reply, field) != getattr(expected_request, field):
            raise ProtocolError("reply " + field + " does not match pending request")
    return reply


def atomic_write_wire(path, message):
    """Validate, fsync/close a same-directory tempfile, then atomically replace.

    Parent must exist. Filesystem errors propagate; temporary files are cleaned
    on failure. A destination symlink is replaced, not followed by the writer.
    """
    data = encode_wire(message)
    destination = Path(path)
    fd, temporary = tempfile.mkstemp(prefix="." + destination.name + ".",
                                     suffix=".tmp", dir=destination.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            fd = None
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        if fd is not None:
            os.close(fd)
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
