import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent)
sys.path.insert(0, project_root)

# Import the create_app function from the main package
from trading_bot import create_app

# Create the Flask application
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
