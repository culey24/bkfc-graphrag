from pyneo4j import Graph # uv add pyneo4j

graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))

def upload_json_to_neo4j(json_data):
    # Tạo các Node
    for node in json_data['nodes']:
        graph.run("MERGE (n:Entity {id: $id}) SET n.user = $user, n.desc = $desc", 
                  id=node['id'], user=node['user'], desc=node['desc'])
    
    # Tạo các Link
    for link in json_data['links']:
        graph.run("""
            MATCH (a:Entity {id: $src}), (b:Entity {id: $tgt})
            MERGE (a)-[r:RELATION {label: $label}]->(b)
        """, src=link['source'], tgt=link['target'], label=link['label'])