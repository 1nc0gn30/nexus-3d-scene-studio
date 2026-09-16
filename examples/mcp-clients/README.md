# MCP Client Configurations for Nexus 3D Scene Studio

This directory contains configuration presets for connecting AI assistants and editors to **Nexus 3D Scene Studio** via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/).

---

## 🔌 Supported MCP Clients & Configuration Files

| Client | Config File | Platform Setup Location |
| :--- | :--- | :--- |
| **Claude Desktop** | [`claude_desktop_config.json`](./claude_desktop_config.json) | **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`<br>**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`<br>**Linux**: `~/.config/Claude/claude_desktop_config.json` |
| **Cursor IDE** | [`cursor_mcp.json`](./cursor_mcp.json) | Repository root: `.cursor/mcp.json` or Settings $\to$ Features $\to$ MCP |
| **Cline (VSCode)** | [`cline_mcp.json`](./cline_mcp.json) | VS Code Global Storage: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json` |
| **Zed Editor** | [`zed_settings.json`](./zed_settings.json) | `~/.config/zed/settings.json` under `"context_servers"` |

---

## 🛠️ Step-by-Step Setup Guides

### 1. Claude Desktop Setup
1. Open your Claude Desktop configuration file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`
2. Add the `nexus3d` server definition from [`claude_desktop_config.json`](./claude_desktop_config.json):
   ```json
   {
     "mcpServers": {
       "nexus3d": {
         "command": "python3",
         "args": ["-m", "nexus_3d_scene_studio.mcp_server"],
         "env": {
           "PYTHONPATH": "/path/to/nexus-3d-scene-studio/src"
         }
       }
     }
   }
   ```
3. Restart Claude Desktop. You will see a hammer icon 🔨 indicating available 3D tools!

### 2. Cursor IDE Setup
1. Create a `.cursor/mcp.json` file in your workspace root (or copy [`cursor_mcp.json`](./cursor_mcp.json)).
2. Configure the absolute or relative path to your Python environment and source directory.
3. Open Cursor Chat (Cmd+L / Ctrl+L) in Agent mode. You can now prompt:
   > *"Generate a 4D Hypercube tesseract with rotation 0.8 and export it as an OBJ mesh in ./models/"*

### 3. Cline (VS Code Extension) Setup
1. Click the MCP settings icon in Cline panel.
2. Paste the JSON from [`cline_mcp.json`](./cline_mcp.json).
3. Enable `autoApprove` for seamless agentic modeling workflows.

### 4. Zed Editor Setup
1. Open `~/.config/zed/settings.json`.
2. Add the `"context_servers"` block from [`zed_settings.json`](./zed_settings.json).

---

## 🧰 Available MCP Tools Reference

When connected, AI agents gain access to the following 5 procedural 3D tools:

1. `generate_mesh`: Generates 3D procedural primitives (tesseract, torus knot, superquadric, fibonacci sphere, buckyball, mobius strip, terrain).
2. `export_scene`: Exports active scene or mesh to OBJ, MTL, STL (ASCII/Binary), Three.js JSON, or Standalone HTML.
3. `transform_mesh`: Applies translation, rotation, scale, taper, bend, or twist deformations.
4. `inspect_geometry`: Returns precise geometric telemetry (vertex count, faces, bounding box dimensions, surface area, Euler characteristic).
5. `list_primitives`: Lists all supported parametric shape types and parameter ranges.
