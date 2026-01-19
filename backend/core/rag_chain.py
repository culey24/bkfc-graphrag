from backend.core.embedding_engine import EmbeddingEngine
import torch

class GraphRAG:
    def __init__(self, graph_data, llm_engine, embedder, neo4j_driver):
        self.graph_data = graph_data
        self.llm = llm_engine
        self.embedder = embedder
        self.driver = neo4j_driver

    def retrieve_context(self, query):
        # 1. Tìm node gần nhất bằng FAISS
        indices = self.embedder.search(query, k=2)
        relevant_ids = []
        for idx in indices:
            if idx != -1 and idx < len(self.graph_data['nodes']):
                relevant_ids.append(self.graph_data['nodes'][idx]['id'])

        # 2. Dùng Neo4j lấy thông tin node đó và các node liên quan (neighbors)
        context_parts = []
        all_related_ids = set(relevant_ids)

        with self.driver.session() as session:
            for node_id in relevant_ids:
                result = session.run("""
                    MATCH (n:Entity {id: $id})
                    OPTIONAL MATCH (n)-[r:RELATION]-(neighbor)
                    RETURN n.user as name, n.desc as desc, 
                           neighbor.user as nb_name, r.label as rel, neighbor.desc as nb_desc
                """, id=node_id)
                
                for record in result:
                    context_parts.append(f"- {record['name']}: {record['desc']}")
                    if record['nb_name']:
                        context_parts.append(f"  (Quan hệ: {record['rel']} với {record['nb_name']}: {record['nb_desc']})")
        
        return "\n".join(set(context_parts)), list(all_related_ids)

    def query(self, user_question):
        context, node_ids = self.retrieve_context(user_question)
        answer = self.llm.generate_answer(user_question, context)
        return answer, node_ids