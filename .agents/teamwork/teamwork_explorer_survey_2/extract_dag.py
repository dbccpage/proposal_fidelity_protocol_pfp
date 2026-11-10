import json

with open("workflows/dag/workflow_dag.json", encoding="utf-8") as f:
    dag = json.load(f)

print(f"Total nodes in DAG: {len(dag['nodes'])}")
print("ID | Name | Status | Kind | Depends On | Calls | Pattern | Host Check")
print("-" * 120)
for node in dag["nodes"]:
    nid = node["id"]
    name = node["name"]
    status = node["status"]
    kind = node["kind"]
    dep = ",".join(node.get("depends_on", []))
    calls = str(node.get("model_calls_normal_path", "N/A"))
    pattern = node.get("team", {}).get("pattern", "N/A")
    hc = str(node.get("host_check", "N/A"))
    print(f"{nid} | {name} | {status} | {kind} | {dep} | {calls} | {pattern} | {hc}")
