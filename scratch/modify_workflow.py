import json
import uuid

# Load the current workflow JSON
with open('/home/krit/my-office/workflow_md.json', 'r') as f:
    data = json.load(f)

# Extract nodes and connections
nodes = data['nodes']
connections = data['connections']

# Generate a UUID for the new node
node_id = str(uuid.uuid4())

# Create the new code node to split messages
split_node = {
    "parameters": {
        "jsCode": """const chunks = [];
const text = $json.output || "";
const maxLength = 1900;

if (text.length <= maxLength) {
  chunks.push(text);
} else {
  let currentChunk = "";
  const lines = text.split('\\n');
  for (const line of lines) {
    if ((currentChunk + "\\n" + line).length > maxLength) {
      if (currentChunk) chunks.push(currentChunk);
      currentChunk = line;
      while (currentChunk.length > maxLength) {
        chunks.push(currentChunk.substring(0, maxLength));
        currentChunk = currentChunk.substring(maxLength);
      }
    } else {
      currentChunk = currentChunk ? (currentChunk + "\\n" + line) : line;
    }
  }
  if (currentChunk) {
    chunks.push(currentChunk);
  }
}

return chunks.map(chunk => ({
  ...$json,
  output: chunk
}));"""
    },
    "type": "n8n-nodes-base.code",
    "typeVersion": 2,
    "position": [432, 80],
    "id": node_id,
    "name": "Split Message"
}

# Add the new node to the list of nodes
nodes.append(split_node)

# Update connections: AI Agent -> Split Message -> Send a message
# 1. Update AI Agent main output connection
if "AI Agent" in connections:
    connections["AI Agent"]["main"] = [[
        {
            "node": "Split Message",
            "type": "main",
            "index": 0
        }
    ]]

# 2. Add Split Message main output connection to Send a message
connections["Split Message"] = {
    "main": [[
        {
            "node": "Send a message",
            "type": "main",
            "index": 0
        }
    ]]
}

# Save back the modified JSON
data['nodes'] = nodes
data['connections'] = connections

with open('/home/krit/my-office/workflow_md_modified.json', 'w') as f:
    json.dump(data, f, indent=2)

print("Workflow modified successfully.")
