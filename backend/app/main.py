"""LandSight AI - FastAPI Application Entrypoint."""

# Placeholder FastAPI app definition
# Note: Dependencies will be installed in subsequent steps

def get_app_info():
    """Returns basic service metadata."""
    return {
        "service": "LandSight AI API",
        "problem_statement": "SIH26017",
        "status": "scaffolded",
        "version": "0.1.0"
    }

if __name__ == "__main__":
    print(get_app_info())
