from rag_tool import process_file_and_get_query_engine
import os
csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'Sugar_Spend_Data.csv'))
with open(csv_path, 'rb') as file:
    file_content = file.read()
engine = process_file_and_get_query_engine(file_content, 'Sugar_Spend_Data.csv')
print(engine.query("What is the top supplier for Raw Sugar?"))