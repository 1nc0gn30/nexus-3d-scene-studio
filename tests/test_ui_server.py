"""Comprehensive Unit Tests for Nexus 3D Scene Studio UI Server & REST APIs."""

from __future__ import annotations

import base64
import io
import json
import socket
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from http.server import ThreadingHTTPServer

from nexus_3d_scene_studio.mcp_server import SERVER_NAME, SERVER_VERSION
from nexus_3d_scene_studio.ui_server import (
    NexusStudioRequestHandler,
    get_default_presets,
    start_ui_server,
)


def _find_free_port() -> int:
    """Find an available ephemeral TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestUIServer(unittest.TestCase):
    """Test suite for HTTP UI server and REST API endpoints."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.port = _find_free_port()
        cls.host = "127.0.0.1"
        cls.base_url = f"http://{cls.host}:{cls.port}"

        # Create temporary public directory with mock files
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.public_path = cls.temp_dir.name

        cls.httpd = start_ui_server(
            host=cls.host,
            port=cls.port,
            public_dir=cls.public_path,
            open_browser=False,
        )

        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.temp_dir.cleanup()

    def _http_request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> tuple[int, Dict[str, str], bytes]:
        """Perform HTTP request to test server and return (status, headers, body_bytes)."""
        url = f"{self.base_url}{path}"
        req_headers = {"User-Agent": "Nexus-Test-Client"}
        if headers:
            req_headers.update(headers)

        body_bytes = None
        if data is not None:
            body_bytes = json.dumps(data).encode("utf-8")
            req_headers["Content-Type"] = "application/json"

        req = urllib.request.Request(
            url=url,
            data=body_bytes,
            headers=req_headers,
            method=method,
        )

        try:
            with urllib.request.urlopen(req) as resp:
                resp_headers = {k.lower(): v for k, v in resp.getheaders()}
                return resp.status, resp_headers, resp.read()
        except urllib.error.HTTPError as he:
            resp_headers = {k.lower(): v for k, v in he.headers.items()}
            return he.code, resp_headers, he.read()

    def test_api_health(self) -> None:
        """Test GET /api/health endpoint."""
        status, headers, body = self._http_request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertIn("application/json", headers.get("content-type", ""))
        self.assertEqual(headers.get("access-control-allow-origin"), "*")

        data = json.loads(body.decode("utf-8"))
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], SERVER_NAME)
        self.assertEqual(data["version"], SERVER_VERSION)
        self.assertIn("uptime_seconds", data)

    def test_api_presets(self) -> None:
        """Test GET /api/presets endpoint."""
        status, headers, body = self._http_request("GET", "/api/presets")
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))
        self.assertIn("categories", data)
        cat_ids = {c["id"] for c in data["categories"]}
        self.assertIn("tesseract", cat_ids)
        self.assertIn("torus_knot", cat_ids)
        self.assertIn("superquadric", cat_ids)
        self.assertIn("solid", cat_ids)
        self.assertIn("terrain", cat_ids)

    def test_api_mcp_config(self) -> None:
        """Test GET /api/mcp/config with various client queries."""
        # Claude client config
        status, _, body = self._http_request("GET", "/api/mcp/config?client=claude")
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))
        self.assertIn("mcpServers", data)

        # Zed client config
        status, _, body = self._http_request("GET", "/api/mcp/config?client=zed")
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))
        self.assertIn("context_servers", data)

    def test_api_diagnostics(self) -> None:
        """Test GET /api/diagnostics endpoint."""
        status, _, body = self._http_request("GET", "/api/diagnostics")
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))
        self.assertIn("platform", data)
        self.assertIn("cpu_count", data)

    def test_api_generate_success(self) -> None:
        """Test POST /api/generate endpoint with valid parameters."""
        payload = {
            "shape": "torus_knot",
            "params": {"p": 2, "q": 3, "major_radius": 1.8, "tube_radius": 0.3},
        }
        status, _, body = self._http_request("POST", "/api/generate", data=payload)
        self.assertEqual(status, 200)
        res = json.loads(body.decode("utf-8"))
        self.assertEqual(res["status"], "success")
        self.assertIn("mesh", res)
        self.assertIn("threejs", res)
        self.assertIn("audit", res)
        self.assertGreater(len(res["mesh"]["vertices"]), 100)

    def test_api_generate_error(self) -> None:
        """Test POST /api/generate with invalid shape returns 400."""
        payload = {"shape": "invalid_shape_name", "params": {}}
        status, _, body = self._http_request("POST", "/api/generate", data=payload)
        self.assertEqual(status, 400)
        res = json.loads(body.decode("utf-8"))
        self.assertEqual(res["status"], "error")

    def test_api_export_formats(self) -> None:
        """Test POST /api/export endpoint for OBJ, STL, Three.js, and HTML."""
        # 1. OBJ
        status, _, body = self._http_request("POST", "/api/export", data={"shape": "icosahedron", "format": "obj"})
        self.assertEqual(status, 200)
        res = json.loads(body.decode("utf-8"))
        self.assertEqual(res["format"], "obj")
        self.assertIn("v ", res["content"])

        # 2. STL
        status, _, body = self._http_request("POST", "/api/export", data={"shape": "tetrahedron", "format": "stl"})
        self.assertEqual(status, 200)
        res = json.loads(body.decode("utf-8"))
        self.assertEqual(res["format"], "stl")
        self.assertIn("solid ", res["content"])

        # 3. HTML
        status, _, body = self._http_request("POST", "/api/export", data={"shape": "tesseract", "format": "html"})
        self.assertEqual(status, 200)
        res = json.loads(body.decode("utf-8"))
        self.assertEqual(res["format"], "html")
        self.assertIn("<!DOCTYPE html>", res["content"])

        # 4. glTF
        status, _, body = self._http_request("POST", "/api/export", data={"shape": "cube", "format": "gltf"})
        self.assertEqual(status, 200)
        res = json.loads(body.decode("utf-8"))
        self.assertEqual(res["format"], "gltf")
        self.assertIn("asset", json.loads(res["content"]))

        # 5. PLY
        status, _, body = self._http_request("POST", "/api/export", data={"shape": "cube", "format": "ply"})
        self.assertEqual(status, 200)
        res = json.loads(body.decode("utf-8"))
        self.assertEqual(res["format"], "ply")
        self.assertTrue(res["content"].startswith("ply\n"))

    def test_api_audit(self) -> None:
        """Test POST /api/audit endpoint."""
        payload = {"shape": "buckyball", "params": {"radius": 2.0}}
        status, _, body = self._http_request("POST", "/api/audit", data=payload)
        self.assertEqual(status, 200)
        res = json.loads(body.decode("utf-8"))
        self.assertEqual(res["status"], "success")
        self.assertIn("audit", res)
        self.assertEqual(res["audit"]["vertex_count"], 60)
        self.assertIn("performance_grade", res["audit"])

    def test_api_export_zip_json_and_binary(self) -> None:
        """Test POST /api/export-zip returning base64 ZIP and raw binary stream."""
        # 1. Base64 JSON response
        status, _, body = self._http_request(
            "POST",
            "/api/export-zip",
            data={"shape": "torus_knot", "params": {"p": 2, "q": 3}},
        )
        self.assertEqual(status, 200)
        res = json.loads(body.decode("utf-8"))
        self.assertEqual(res["status"], "success")
        self.assertIn("data_base64", res)

        zip_bytes = base64.b64decode(res["data_base64"])
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            file_names = zf.namelist()
            self.assertIn("model.obj", file_names)
            self.assertIn("material.mtl", file_names)
            self.assertIn("model.stl", file_names)
            self.assertIn("model.gltf", file_names)
            self.assertIn("model.ply", file_names)
            self.assertIn("model.json", file_names)
            self.assertIn("viewer.html", file_names)
            self.assertIn("audit.json", file_names)
            self.assertIn("README.md", file_names)

        # 2. Binary ZIP response via Accept header
        status, headers, binary_body = self._http_request(
            "POST",
            "/api/export-zip",
            data={"shape": "icosahedron"},
            headers={"Accept": "application/zip"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(headers.get("content-type"), "application/zip")
        with zipfile.ZipFile(io.BytesIO(binary_body)) as zf:
            self.assertIn("model.obj", zf.namelist())

    def test_options_cors(self) -> None:
        """Test OPTIONS pre-flight request returns CORS headers."""
        status, headers, _ = self._http_request("OPTIONS", "/api/generate")
        self.assertIn(status, [200, 204])
        self.assertEqual(headers.get("access-control-allow-origin"), "*")
        self.assertIn("POST", headers.get("access-control-allow-methods", ""))

    def test_root_embedded_ui_fallback(self) -> None:
        """Test GET / returns standalone HTML fallback when index.html is missing."""
        status, headers, body = self._http_request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers.get("content-type", ""))
        self.assertIn("<!DOCTYPE html>", body.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
