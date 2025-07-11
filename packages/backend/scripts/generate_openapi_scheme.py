# /usr/bin/env python
import json

from wallstr.server import app

filename = "openapi.json"
with open(filename, "w") as f:
    json.dump(app.openapi_schema, f, indent=4)
    print(f"> Saved to {filename}")
