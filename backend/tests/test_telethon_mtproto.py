"""Снимок MTProto для Telethon shadow raw_payload.mtproto."""
import json
from datetime import datetime

from telethon.tl import types
from telethon.tl.custom.message import Message

from app.services.telethon_collector import _json_safe_mtproto, telethon_message_to_mtproto_dict


def test_json_safe_mtproto_serializes_bytes_and_datetime():
    d = {"t": datetime(2024, 1, 2, 3, 4, 5), "b": b"ab\x00"}
    out = _json_safe_mtproto(d)
    json.dumps(out)
    assert isinstance(out["t"], str)
    assert out["b"]["_"] == "bytes_b64"
    assert out["b"]["b64"]


def test_telethon_message_to_mtproto_dict_regular_message():
    m = Message(
        id=7,
        peer_id=types.PeerChannel(99),
        date=datetime.utcnow(),
        message="hello",
        views=42,
        post=True,
    )
    d = telethon_message_to_mtproto_dict(m)
    json.dumps(d)
    assert d["_"] == "Message"
    assert d["id"] == 7
    assert d["views"] == 42
    assert d["peer_id"]["_"] == "PeerChannel"
    assert isinstance(d["date"], str)


def test_telethon_message_to_mtproto_dict_message_service():
    m = Message(
        id=2,
        peer_id=types.PeerChannel(1),
        date=datetime.utcnow(),
        action=types.MessageActionChannelCreate(title="chan"),
    )
    d = telethon_message_to_mtproto_dict(m)
    json.dumps(d)
    assert d["_"] == "MessageService"
    assert d["action"]["_"] == "MessageActionChannelCreate"


def test_telethon_message_to_mtproto_dict_document_file_reference_bytes():
    doc = types.Document(
        id=1,
        access_hash=2,
        file_reference=b"\x01\x02",
        date=datetime.utcnow(),
        mime_type="application/octet-stream",
        size=3,
        dc_id=1,
        attributes=[],
        thumbs=[],
        video_thumbs=[],
    )
    media = types.MessageMediaDocument(document=doc)
    m = Message(
        id=3,
        peer_id=types.PeerChannel(5),
        date=datetime.utcnow(),
        message="with doc",
        media=media,
    )
    d = telethon_message_to_mtproto_dict(m)
    json.dumps(d)
    assert d["media"]["_"] == "MessageMediaDocument"
    fr = d["media"]["document"]["file_reference"]
    assert fr["_"] == "bytes_b64"
