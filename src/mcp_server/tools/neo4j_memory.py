from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

class Neo4jMemoryTool:
    """
    A tool for interacting with a Neo4j graph database to provide long-term memory.
    """

    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    def add_node(self, label: str, properties: dict) -> str:
        """
        Adds a node to the graph.
        """
        with self._driver.session() as session:
            result = session.execute_write(self._create_node, label, properties)
            return f"Created node: {result}"

    def add_relationship(self, start_node_label: str, start_node_properties: dict,
                         end_node_label: str, end_node_properties: dict,
                         relationship_type: str) -> str:
        """
        Adds a relationship between two nodes.
        """
        with self._driver.session() as session:
            result = session.execute_write(self._create_relationship, start_node_label, start_node_properties,
                                               end_node_label, end_node_properties, relationship_type)
            return f"Created relationship: {result}"

    def query(self, query: str) -> list:
        """
        Executes a Cypher query and returns the results.
        """
        with self._driver.session() as session:
            result = session.execute_read(self._execute_query, query)
            return result

    @staticmethod
    def _create_node(tx, label, properties):
        unique_properties = {k: v for k, v in properties.items() if k in ["id", "name", "path", "url", "sha"]}
        if not unique_properties:
             query = f"CREATE (n:{label} $props) RETURN n"
             result = tx.run(query, props=properties)
        else:
            merge_props_str = ", ".join([f'{k}: $props.{k}' for k in unique_properties])
            query = f"MERGE (n:{label} {{{merge_props_str}}}) ON CREATE SET n += $props ON MATCH SET n += $props RETURN n"
            result = tx.run(query, props=properties)
        return result.single()[0]

    @staticmethod
    def _create_relationship(tx, start_node_label, start_node_properties,
                             end_node_label, end_node_properties, relationship_type):
        start_unique_properties = {k: v for k, v in start_node_properties.items() if k in ["id", "name", "path", "url", "sha"]}
        end_unique_properties = {k: v for k, v in end_node_properties.items() if k in ["id", "name", "path", "url", "sha"]}

        start_merge_props_str = ", ".join([f'{k}: $start_props.{k}' for k in start_unique_properties])
        end_merge_props_str = ", ".join([f'{k}: $end_props.{k}' for k in end_unique_properties])
        
        query = (
            f"MERGE (a:{start_node_label} {{{start_merge_props_str}}}) ON CREATE SET a += $start_props ON MATCH SET a += $start_props "
            f"MERGE (b:{end_node_label} {{{end_merge_props_str}}}) ON CREATE SET b += $end_props ON MATCH SET b += $end_props "
            f"MERGE (a)-[r:{relationship_type}]->(b) "
            "RETURN type(r)"
        )
        result = tx.run(query, start_props=start_node_properties, end_props=end_node_properties)
        return result.single()[0]

    @staticmethod
    def _execute_query(tx, query):
        result = tx.run(query)
        return [record for record in result]
