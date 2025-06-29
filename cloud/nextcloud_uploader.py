"""Nextcloud file uploader using WebDAV chunked uploads."""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import time
import uuid
from typing import List
from urllib import request

from utils.logger import get_logger


class NextcloudUploader:
    """Upload files to Nextcloud using WebDAV with chunked uploads."""

    def __init__(self, base_url: str, username: str, password: str, logger: logging.Logger | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.auth_header = self._build_auth(username, password)
        self.logger = logger or get_logger(__name__)

    @staticmethod
    def _build_auth(username: str, password: str) -> str:
        token = base64.b64encode(f"{username}:{password}".encode()).decode()
        return f"Basic {token}"

    def _make_request(
        self,
        method: str,
        path: str,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        retries: int = 3,
    ) -> bytes:
        url = f"{self.base_url}{path}"
        headers = headers or {}
        for attempt in range(retries):
            req = request.Request(url, data=data, method=method)
            req.add_header("Authorization", self.auth_header)
            for k, v in headers.items():
                req.add_header(k, v)
            try:
                with request.urlopen(req) as resp:
                    self.logger.debug("%s %s -> %s", method, url, getattr(resp, "status", "?"))
                    return resp.read()
            except Exception as exc:  # pylint: disable=broad-except
                self.logger.error("%s %s failed: %s", method, url, exc)
                if attempt + 1 == retries:
                    raise
                time.sleep(2 ** attempt)
        return b""

    def _list_existing_chunks(self, upload_id: str) -> List[int]:
        path = f"/remote.php/dav/uploads/{self.username}/{upload_id}/"
        try:
            data = self._make_request("PROPFIND", path, headers={"Depth": "1"})
        except Exception:
            return []
        import xml.etree.ElementTree as ET

        try:
            tree = ET.fromstring(data)
        except ET.ParseError:
            return []
        chunks: List[int] = []
        for resp in tree.findall("{DAV:}response"):
            href = resp.find("{DAV:}href")
            if href is None:
                continue
            name = os.path.basename(href.text.rstrip("/"))
            if name.isdigit():
                chunks.append(int(name))
        return sorted(chunks)

    def upload_file(self, local_path: str, remote_path: str, chunk_size: int = 10 * 1024 * 1024, verify: bool = False) -> None:
        """Upload ``local_path`` to ``remote_path`` in chunks."""
        upload_id = uuid.uuid4().hex
        existing = self._list_existing_chunks(upload_id)
        start_chunk = max(existing) + 1 if existing else 0

        chunk_dir = f"/remote.php/dav/uploads/{self.username}/{upload_id}"
        self.logger.info("Starting upload %s to %s", local_path, remote_path)

        with open(local_path, "rb") as fh:
            fh.seek(start_chunk * chunk_size)
            chunk_num = start_chunk
            while True:
                data = fh.read(chunk_size)
                if not data:
                    break
                self._make_request(
                    "PUT",
                    f"{chunk_dir}/{chunk_num}",
                    data=data,
                    headers={"OC-Chunked": "1"},
                )
                self.logger.debug("Uploaded chunk %s (%s bytes)", chunk_num, len(data))
                chunk_num += 1

        dest = f"{self.base_url}/remote.php/dav/files/{self.username}/{remote_path.lstrip('/')}"
        self._make_request(
            "MOVE",
            f"{chunk_dir}/.file",
            headers={"Destination": dest},
        )
        self.logger.info("Upload complete: %s", remote_path)

        if verify:
            local_hash = self._hash_file(local_path)
            remote_data = self._make_request("GET", f"/remote.php/dav/files/{self.username}/{remote_path.lstrip('/')}")
            remote_hash = hashlib.sha256(remote_data).hexdigest()
            if local_hash != remote_hash:
                raise ValueError("Hash mismatch after upload")

    @staticmethod
    def _hash_file(path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
