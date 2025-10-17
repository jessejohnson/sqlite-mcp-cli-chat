import os
import sqlite3
import logging
import datetime
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("SQlite3 Server")
DB_PATH = os.environ["SERVER_DB_PATH"]
FILES_DIR = os.environ["SERVER_RESOURCE_DIR"]
LOG_FILE = os.environ["LOG_DIR"] + "sqlite-server.log"

def _query_db(query: str) -> list[str]:
    logging.info(f"Received query '{query}' ")
    with sqlite3.connect(DB_PATH) as connection:
        logging.info(f"Connected to {DB_PATH}")
        cursor = connection.cursor()
        cursor.execute(query)
        
        rows = cursor.fetchall()
        logging.info(f"Executed query with {len(rows)} results")
        results = [str(row) for row in rows]
        return results
    
def _get_schema() -> str:
    logging.info(f"Retrieving schema for {DB_PATH}")
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.cursor()
        query = "SELECT sql FROM sqlite_master WHERE type='table';"
        cursor.execute(query)

        result = cursor.fetchall()
        return str(result)

@mcp.tool()
def get_current_datetime() -> str:
    """Get current date and time for my locale."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@mcp.tool()
def select_query(query: str) -> list[str]:
    """Make a request to a connected SQlite database

    Args:
        query: a SQL SELECT query compatible with SQlite3
    """
    return _query_db(query=query)

@mcp.tool()
def get_database_schema() -> str:
    """Get the data base scheme to understand what tables and columns are available. This is useful when in doubt of what to look for. It takes no arguments. Run this before running the tool to query the database.
    """
    return _get_schema()

@mcp.tool()
def list_resource_files() -> list[str]:
    """Get a list of file paths from SERVER_RESOURCE_DIR
    """
    files = os.listdir(FILES_DIR)
    return files

@mcp.tool()
def read_resource_file(name: str) -> dict[str,str]:
    """Read a file given a specific name from SERVER_RESOURCE_DIR

    Args:
        name: a valid file name/path
    """
    full_path = FILES_DIR + name
    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()
    return {
        "mimeType": "text/plain",
        "text": content
    }

def main():
    mcp.run(transport="stdio")

def setup_basic_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s>    %(filename)s:line %(lineno)d %(message)s',       
         handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )

if __name__ == "__main__":
    setup_basic_logging()
    # res = get_database_schema()
    # print(res)
    main()