"""Debug server entrypoint with debugpy support."""
import os
import debugpy

# Enable debugpy if requested
if os.getenv("ENABLE_DEBUGPY", "false").lower() == "true":
    debugpy.listen(("0.0.0.0", 5678))
    print("🐛 Debugpy listening on port 5678 - attach your debugger now!")
    # Optionally wait for debugger to attach
    # debugpy.wait_for_client()

# Start uvicorn normally
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["/app"]
    )
