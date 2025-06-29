from unittest import mock

from cloud.nextcloud_uploader import NextcloudUploader


def test_upload_file_simple(tmp_path):
    src = tmp_path / "data.txt"
    src.write_bytes(b"hello world")
    uploader = NextcloudUploader("https://nc", "alice", "token")

    with mock.patch.object(uploader, "_list_existing_chunks", return_value=[]), \
         mock.patch.object(uploader, "_make_request") as m_req:
        uploader.upload_file(str(src), "dest/data.txt")
        # first chunk upload
        assert m_req.call_args_list[0][0][0] == "PUT"
        assert "/remote.php/dav/uploads/alice/" in m_req.call_args_list[0][0][1]
        # final MOVE
        assert m_req.call_args_list[-1][0][0] == "MOVE"
        assert "/remote.php/dav/uploads/alice/" in m_req.call_args_list[-1][0][1]


def test_upload_resume(tmp_path):
    src = tmp_path / "data.bin"
    src.write_bytes(b"foobar" * 2)
    uploader = NextcloudUploader("https://nc", "bob", "pwd")

    with mock.patch.object(uploader, "_list_existing_chunks", return_value=[0]), \
         mock.patch.object(uploader, "_make_request") as m_req:
        uploader.upload_file(str(src), "dst.bin", chunk_size=3)
        # Should skip chunk 0 and start from chunk 1
        uploaded = [call[0][1] for call in m_req.call_args_list if call[0][0] == "PUT"]
        assert any(part.endswith("/1") for part in uploaded)
        assert not any(part.endswith("/0") for part in uploaded)
