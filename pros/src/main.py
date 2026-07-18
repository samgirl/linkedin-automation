"""PROS - Personal Reputation Operating System."""

import uvicorn

from pros.src.api.app import create_app


def main():
    """Run the PROS application."""
    app = create_app()
    
    uvicorn.run(
        app,
        host="localhost",
        port=8000,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
