from pydantic import BaseModel
from dotenv import find_dotenv, load_dotenv
import openai
import json
import time
import re

load_dotenv()
model = "gpt-4o"

'''These are files that have already been uploaded to the OpenAI server'''
#Labcorp Immunity Lab Report
labcorp_id = "file-a3iKjawCF6nStHQwekL53ZOb"
#Quest Diagnostics Lab Report
quest_id = 'file-4xPbWCCBY8f9iocwbw28agIu'

#Lab Analyzer 3
lab_report_assistant_id = "asst_2V3TT9YQnsAwcBKHCblNypVj"
#Medical GPT Generalist
mgeneralist_assist_id = 'asst_9fm5NCQTo77ruSa7AtUsx0dN'

client = openai.OpenAI()
# LabAnalyzer Class is used to upload and process lab results 
# There are currently bugs in this class, but the main idea is present

class LabAnalyzer:
	'''
		Use Case #1   

		1. Class - LabAnalyzer()
		2. Purpose - Analyze lab reports into JSON objects with high-level summaries. Check comments within methods to gain additional insight into class functionality.
		3. Assistant - Lab Report Analyzer 3 (added by deafult)
			3a. The assistant has the temperature set to 0.1 to ensure predictable structure in its response
		4. Thread: N/A - A 'new' thread will be generated for EACH lab report to avoid model hallucinations
	'''
	
	def __init__(self, model:str=model, client=client) -> None:
		self.client = client
		self.model = model
		self.assistant = None
		self.thread = None
		self.run = None
		self.file = None

	thread_id = None
	file_id = None
	assistant_id = lab_report_assistant_id
	
	def retrieve_assist(self, assistant_id:str) -> None:
		'''
			Assigns the assistant object to self.assistant
				1. The Lab Analyzer 3 Assistant is added to the class by default (no need to execute method if you are using this assistant)
				2. If you want to assign a new assistant to class, this is when retrieve_assist() comes into play
		'''
		self.assistant = self.client.beta.assistants.retrieve(assistant_id)
		self.assistant_id = self.assistant.id
		print(f"The {self.assistant.name} assistant has been successfully added to your class!")
		print(f"Assistant ID: {self.assistant_id}")