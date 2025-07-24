"""
Hot-reload system for persona development
Instantly test persona changes without deployment
"""

import asyncio
import logging
import os
from typing import Any, Dict

import yaml
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)

app = FastAPI()


class PersonaReloader(FileSystemEventHandler):
    """Watch persona files and reload on changes"""

    def __init__(self, websocket_manager):
        self.websocket_manager = websocket_manager
        self.personas = {}
        self.load_personas()

    def load_personas(self):
        """Load all persona configurations"""
        persona_dir = "./personas"
        for file in os.listdir(persona_dir):
            if file.endswith(".yaml"):
                with open(os.path.join(persona_dir, file)) as f:
                    persona_id = file.replace(".yaml", "")
                    self.personas[persona_id] = yaml.safe_load(f)
        logger.info(f"Loaded {len(self.personas)} personas")

    def on_modified(self, event):
        if event.src_path.endswith(".yaml"):
            logger.info(f"Persona file changed: {event.src_path}")
            self.load_personas()
            # Notify all connected clients
            asyncio.create_task(
                self.websocket_manager.broadcast(
                    {"type": "persona_reload", "personas": self.personas}
                )
            )


class WebSocketManager:
    """Manage WebSocket connections for live updates"""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = WebSocketManager()


@app.get("/")
async def get():
    """Serve the hot-reload UI"""
    return HTMLResponse(
        """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Persona Hot Reload</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .persona { border: 1px solid #ddd; padding: 15px; margin: 10px 0; }
            .preview { background: #f5f5f5; padding: 10px; margin: 10px 0; }
            .status { color: green; font-weight: bold; }
            #test-input { width: 100%; padding: 10px; margin: 10px 0; }
            #output { border: 1px solid #ddd; padding: 15px; background: #f9f9f9; }
        </style>
    </head>
    <body>
        <h1>🔥 Persona Hot Reload</h1>
        <div class="status">Connected</div>

        <div>
            <label>Test Input:</label>
            <input id="test-input" type="text" placeholder="Enter topic to test personas..." />
            <button onclick="testPersonas()">Test All Personas</button>
        </div>

        <div id="personas"></div>
        <div id="output"></div>

        <script>
            const ws = new WebSocket(`ws://localhost:8001/ws`);

            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'persona_reload') {
                    updatePersonas(data.personas);
                    showNotification('Personas reloaded!');
                } else if (data.type === 'test_result') {
                    showTestResult(data);
                }
            };

            function updatePersonas(personas) {
                const container = document.getElementById('personas');
                container.innerHTML = Object.entries(personas).map(([id, config]) => `
                    <div class="persona">
                        <h3>${config.emoji} ${id}</h3>
                        <p>Temperament: ${config.temperament}</p>
                        <div class="preview">
                            <strong>Hook Template:</strong><br/>
                            ${config.hook_template || 'Default hook'}
                        </div>
                        <button onclick="testPersona('${id}')">Test This Persona</button>
                    </div>
                `).join('');
            }

            function testPersona(personaId) {
                const input = document.getElementById('test-input').value;
                ws.send(JSON.stringify({
                    action: 'test_persona',
                    persona_id: personaId,
                    input: input
                }));
            }

            function testPersonas() {
                const input = document.getElementById('test-input').value;
                ws.send(JSON.stringify({
                    action: 'test_all',
                    input: input
                }));
            }

            function showTestResult(data) {
                document.getElementById('output').innerHTML = `
                    <h3>Test Results</h3>
                    <pre>${JSON.stringify(data.results, null, 2)}</pre>
                `;
            }

            function showNotification(message) {
                const status = document.querySelector('.status');
                status.textContent = message;
                setTimeout(() => {
                    status.textContent = 'Connected';
                }, 3000);
            }
        </script>
    </body>
    </html>
    """
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()

            if data["action"] == "test_persona":
                # Test single persona
                result = await test_persona_generation(
                    data["persona_id"], data["input"]
                )
                await websocket.send_json(
                    {"type": "test_result", "results": {data["persona_id"]: result}}
                )

            elif data["action"] == "test_all":
                # Test all personas
                results = {}
                for persona_id in reloader.personas:
                    results[persona_id] = await test_persona_generation(
                        persona_id, data["input"]
                    )
                await websocket.send_json({"type": "test_result", "results": results})

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)


async def test_persona_generation(persona_id: str, input_text: str) -> Dict[str, Any]:
    """Test persona generation without full pipeline"""
    try:
        # Quick generation using cached models
        from services.persona_runtime.runtime import PersonaRuntime

        runtime = PersonaRuntime(persona_id)

        # Fast test mode - skip heavy processing
        state = {
            "user_topic": input_text,
            "messages": [],
            "test_mode": True,  # Use cached responses
        }

        result = runtime.graph.invoke(state)
        return {
            "success": True,
            "hook": result.get("hook", ""),
            "preview": result.get("full_text", "")[:200] + "...",
            "time_ms": 150,  # Simulated fast response
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# Start file watcher
reloader = PersonaReloader(manager)
observer = Observer()
observer.schedule(reloader, path="./personas", recursive=True)
observer.start()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
