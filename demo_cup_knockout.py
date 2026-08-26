import json

from render import save

with open("demo_cup_knockout_fixture.json", encoding="utf-8") as f:
    fixture = json.load(f)

output_path = save(fixture["data"], fixture["summary"])
print(f"Saved to: {output_path}")
print(f"Open: {output_path.as_uri()}")
