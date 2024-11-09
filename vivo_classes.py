from pydantic import BaseModel
from dotenv import find_dotenv, load_dotenv
import openai
import json
import time
import re
import logging

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
	
	def retrieve_file(self, file_id:str):
		'''
			If you already have a file_id for a file that has been uploaded, you can attach the file object to self.file and self.file_id
		'''
		existing_file = client.files.retrieve(file_id)
		self.file = existing_file
		self.file_id = self.file.id
		print(self.file.model_dump_json(indent=2))
		print(self.file_id)
	
	def file_upload(self, file:str=None):
		'''
			Uploads the file and assigns the file object to self.file
				1. File must be the (str) of the path relative to the directory
				2. .pdf files must be uploaded with purpose='assistants' compared to purpose='vision' for images
				3. If a file is already assigned to self.file and self.file_id, then these attributes will be overwritten!
		'''
		# Checks if a file object is attached to instance
		if self.file:
			print("You chose not to override the file that is attached to instance")

		# Attaches new file to object - checks the file extension to understand what type of upload to execute 
		if file.split('.')[1] in ['pdf']:
			try:
				file = self.client.files.create(
					file=open(file, "rb"),
					purpose="assistants"
					)
				self.file = file
				self.file_id = self.file.id
				print("File upload was successful!")
				print(f"File ID: {self.file_id}")
			except Exception:
				print("File upload was unsuccessful. Please try again.")
		elif file.split('.')[1] in ['jpeg', 'jpg', 'png']: 
			try:
				file = self.client.files.create(
					file=open(file, "rb"),
					purpose="vision"
					)
				self.file = file
				self.file_id = self.file.id
				print("Image upload was successful!")
				print(f"File ID: {self.file_id}")
			except Exception:
				print("Image upload was unsuccessful. Please try again.")
	
	def new_thread_run(self):
		'''
			Creates new thread and runs the message; assisgns run and thread objects to respective attributes
				Context:
					1. A file has to be assigned to instance. If this is the case, utilize file_retrieve() or file_upload() methods to assign file object or upload file to be assigned to self.file and self.file_id. 
					2. There are two types of runs: runs based on .pdf files or runs based on .jpeg, .png, or .jpg files - the configuration of the run will vary depending on the file extension

				Overview:
					1. A new thread will be created with a designated message added to thread.
					2. This message will be ran against the assistant to produce a response.
					3. This method then assigns the run and thread objects to self.run and self.thread respectively 
					4. Now a chain reaction will occur if the run is successful: wait_for_completed(), process_message(), message_output()
						a) wait_for_completed() - will check every 5 seconds if run is complete. This loop will continue for 60secs.
						b) process_message() - The response given by the assistant will be in JSON format - this method processes the JSON into Python dictionaries. 
						c) message_output() - Processes the Python dictionaries into palatable f-stirngs
		'''
		if not self.file and not self.file_id:
			return print("You need to upload a file via file_upload() method")
		
		if self.file.purpose == 'assistants':
			try:
				run_thread = self.client.beta.threads.create_and_run(
					assistant_id=self.assistant_id,
					thread={
						"messages": [
						{"role": "user", "content": "Breakdown the lab report attached to this message into the 'lab_output' schema that is defined in the instructions of the assistant. Do not return the original schema in the final response. Begin the output of the result with the string 'EXTRACTED DATA:'. Be sure to capture every test that is documented in the report. A test will be in a column marked as 'analyte', 'test' or 'result'. Ensure that the response that you return can be processed by the json.dumps() method. The 'testConclusion' attribute must be 'Low', 'Normal', 'High' or 'Undefined' based on the reference interval.", "attachments":[{
						"file_id": self.file_id,
						"tools": [{"type": "file_search"}]} ]}
							]
						}
					)
				self.thread = client.beta.threads.retrieve(run_thread.thread_id)
				self.thread_id = self.thread.id
				print("Waiting for lab analysis to complete...")
				self.wait_for_completed(run_thread.id)
				self.print_thread(report=True)
			except Exception:
				print("Waiting for lab analysis to complete...")
		elif self.file.purpose == 'vision':
			try:
				run_thread = client.beta.threads.create_and_run(
					assistant_id=self.assistant_id,
					thread={
						"messages": [
							{
								"role": "user",
								"content": [
									{
										"type": "text",
										"text": "Breakdown the lab report attached to this message into the 'lab_output' schema that is defined in the instructions of the assistant. Do not return the original schema in the final response. Begin the output of the result with the string 'EXTRACTED DATA:'. Be sure to capture every test that is documented in the report. A test will be in a column marked as 'analyte', 'test' or 'result'. Ensure that the response that you return can be processed by the json.dumps() method. The 'testConclusion' attribute must be 'Low', 'Normal', 'High' or 'Undefined' based on the reference interval."
									},
									{
										"type": "image_file",
										"image_file": {
											"file_id": self.file_id,
											"detail": 'high'
										}
									}
								]
							}
						]
					}
				)
				self.thread = self.client.beta.threads.retrieve(run_thread.thread_id)
				self.thread_id = self.thread.id
				self.run = client.beta.threads.runs.retrieve(
					thread_id=self.thread.id,
					run_id=run_thread.id
					)
				print("Waiting for lab analysis to complete...")
				self.wait_for_completed(run_thread.id)
				self.print_thread(report=True)
			except Exception:
				print("There was an error in executing this run!")
	
	def wait_for_completed(self, run_id, report:bool=False, summary:bool=False):
		'''
			Executed via the new_thread_run() method. 
				1. Retrieves the status of the run object every 5 seconds (until 60 secs) to confirm that its complete
					1a. If the run is never completed, then the run_id and thread_id will be printed to reference later
				2. If run.status is 'complete', then the message will be printed 
					2a. Message will be printed by processing the JSON objects into Python dictionaries  from the Assistants response via process_message()
					2b. Python dictionary will then be processed via message_output()
				3. If you're analyzing lab report, API response has to be processed. If you're getting summary, API response does not need to be processed.
		'''
		if self.thread:
			count = 0
			while True:
				# Retrieves the run object every 5 seconds to confirm its current status
				time.sleep(5)
				self.run = client.beta.threads.runs.retrieve(
					thread_id=self.thread.id,
					run_id=run_id
					)
				if self.run.status == "completed":
					#Logic to calculate the time it took to execute run
					elapsed_time = self.run.completed_at - self.run.created_at
					formatted_elapsed_time = time.strftime(
						":%H:%M:%S", time.gmtime(elapsed_time)
					)
					print(f"Run completed in {formatted_elapsed_time}")
					logging.info(f"Run completed in {formatted_elapsed_time}")
					print('Your the run has completed!')
					break
				else:
					count += 1
					#Loops through while loop for a minute
					if count == 24:
						print(self.run.id)
						print(self.thread.id)
						break
		else:
			return print("Check if you have valid thread and run objects")
	
	def print_thread(self,report:bool=False, summary:bool=False):
		'''
			Prints the messages that exists within a thread. self.thread must exist to execute function call.
		'''

		if self.thread and report:
			#Logic to print
			print('Printing report...')
			thread_messages = client.beta.threads.messages.list(self.thread.id)
			message = thread_messages.data[0].content[0].text.value
			#json_objects will be used for backend
			json_objects = self.process_message(message)
			#message_output() is for terminal view in Python
			print(self.message_output(json_objects))
			return print('Lab report complete!')

		if self.thread and summary:
			print('Printing summary..')
			thread_messages = client.beta.threads.messages.list(self.thread.id)
			print(thread_messages.data[1].content[0].text.value)
			print(thread_messages.data[0].content[0].text.value)
			return print('Summary Complete')
	
	def process_message(self, input_string:str) -> list:
		'''
			Processes the JSON string from API response and converts it into a Python dictionary
		'''
		# Remove the unnecessary parts
		cleaned_string = re.sub(r'^EXTRACTED DATA:\s*```json\s*\[\s*', '', input_string)
		cleaned_string = re.sub(r'\s*\]\s*```\s*$', '', cleaned_string)
		
		# Find all JSON objects
		json_objects = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cleaned_string)
		
		# Parse each JSON object
		parsed_objects = []
		for obj in json_objects:
			try:
				parsed_obj = json.loads(obj)
				parsed_objects.append(parsed_obj)
			except json.JSONDecodeError:
				print(f"Error parsing JSON object: {obj}")
		
		return parsed_objects

	def message_output(self, input_array:list):
		'''
			Processes the Python dictionary and prints API response into a readable f-string format.
			This method is for terminal purposes only!
		'''
		for test in input_array:
				if len(test) == 3:
					good = test["goodResults"]
					concern = test["concernResults"]
					doctor = test["doctorConvo"]

					print()
					print("GOOD RESULTS:")
					for response1 in good:
						print(f"{response1}")
					print()

					print("RESULTS THAT REQUIRE ATTENTION:")
					for response2 in concern:
						print(f"{response2}")
					print()

					print("DOCTOR CONVOS:")
					for response3 in doctor:
						print(f"{response3}")
					print()      
				else:
					final_string = f"""
								Section: {test['labSection']}
								Test: {test['testName']}
								Result: {test['result']}
								Units: {test['units']}  
								Conclusion: {test['testConclusion']}      
								Explanation: {test['Explanation']}
								Context: {test['Context']}
								"""
					print(final_string)
						
					for i in range(len(test['referenceInterval'])):
						print(f'referenceIntervalStatus {test['referenceInterval'][i]['referenceIntervalStatus']}')
						print(f'referenceIntervalValue {test['referenceInterval'][i]['referenceIntervalValue']}')
					print()

	def summarize(self):
		'''
			Takes the previous API response of lab report analysis and provides a high-level summary. 
				1. Create a message by taking the thread.id from the existing thread
				2. Prompt the assistant to generate a high-level response
		'''
		thread_message = client.beta.threads.messages.create(
			thread_id=self.thread_id,
			role="user",
			content="Can you provide a high-level summary of the report that you just analyzed? What results are good, what results should I be concerned about and what are conversations should I have with my doctor concerning these results? Breakdown the lab report attached to this message into the 'summary_output' schema that is defined in the instructions of the assistant. When you provide your response, be very detailed. Ensure that the response that you return can be processed by the json.dumps() method. Make sure to assess the context of the results; a 'high' or 'low' result isn't always negative or postive, it depends on the test. Do not return the original schema in the final response.",
			)
		self.run = client.beta.threads.runs.create(
			thread_id=self.thread_id,
			assistant_id=self.assistant_id
			)
		print("Generating summary...")
		self.wait_for_completed(self.run.id)
		self.print_thread(summary=True)

class LabChat:
	'''
		Use Case #2

		1. Class - LabChat
		2. Purpose - Allows user to initiate a 'chatbot' (a thread with subsequent messages) from a specific test from a lab report
		3. Assistant - Medical GPT Generalist (added by default)
			3a. Assistant will be updated with an summary of the test result to have context on its 'temporary' expertise
		4. Thread: N/A - A new thread will be created to initate the chatbot; subsequent messages will be added to the existing thread for further follow-up questions and responses 

		Use Case #3: To continue a chat from an existing thread, you will need to grab the LabChat() instance, load the thread via print_thread() [optional] and execute new_message() to continue a chat from an existing thread from a lab test result 

		Potential feature? - Have GPT ask common questions so users are met with responses in the thread - implemented
	'''

	def __init__(self, model:str=model, client=client) -> None:
		self.client = client
		self.model = model
		self.assistant = None
		self.thread = None
		self.run = None
		
	thread_id = None
	file_id = None
	assistant_id = mgeneralist_assist_id

	def update_assist(self, context):
		'''
			Updates the Medical GPT Generalist Assistant to a specific 'domain' based on test results
				1. Updates the instruction of the assistant to reflect the summary of the results
		'''
		my_updated_assistant = client.beta.assistants.update(
			assistant_id=self.assistant_id,
			instructions=f"You will provide responses to messages in a thread based on bloodwork results. The context of the specific bloodwork results are here: {context}. It is possible that you will be asked questions outside of this domain, if so, remind the user that this chat specifically for the context provided. If they insist, then you can still answer them, disregarding your specialization. Keep in mind, that your responses short be short and succinct. If a user wants additional information, they will ask further questions where you can elaborate further."
			)
		self.assistant = my_updated_assistant
		print("Your assistant has been modified! The results are below:")
		print(self.assistant.model_dump_json(indent=2))
	
	def new_thread_run(self):
		'''
			This method will be used to run 'general' questions by default to the assistant based on the context of a lab test result. These questions include:
				1. What can I do to improve these results, if necessary? 
				2. Is there additional context that you can provide to help me understand these results better?
			
			Overview:
				** You must run update_assist() prior to this method to ensure the instructions within the assistant is updated! **
				1. A new thread will be created with 3 messages - these messages will be added to the thread and ran to get the assistant's response. 
				2. self.thread and self.run will be updated to relect the new thread and to capture the run object. The LASTEST run executed will be assigned to self.run
				3. wait_for_completed() will be executed to wait until run completed for an assistant response.
		'''
		try:
			# You want to add the messages to the thread one by one
			self.thread = client.beta.threads.create()
			self.thread_id = self.thread.id
			content = ["What can I do to improve these results, if necessary?", "Is there additional context that you can provide to help me understand these results better?"]
			
			# Loop through the content array to run assistant for each question 
			for message in content:
				client.beta.threads.messages.create(
				thread_id=self.thread.id,
				role="user",
				content=message,
				)

				self.run = client.beta.threads.runs.create(
					thread_id=self.thread_id,
					assistant_id=self.assistant_id
					)
				print("Waiting for assistant to respond to question(s)...")
				self.wait_for_complete(self.run.id)
			print("Questions are complete!")
			self.wait_for_complete(self.run.id, run_complete=True)
		except Exception:
			print('There was an error in executing this run')
	
	def new_message(self, message:str):
		'''
			new_message() allows a user to ask a question to the Medical GPT Generalist assistant that has context on their lab results
				1. A new message will be created
				2. The message will be added to an existing thread and then a run will begin
		'''
		if self.thread:
			client.beta.threads.messages.create(
				thread_id=self.thread.id,
				role="user",
				content=message,
				)
			self.run = client.beta.threads.runs.create(
						thread_id=self.thread_id,
						assistant_id=self.assistant_id
						)
			print("Waiting for assistant to respond to new question...")
			self.wait_for_complete(self.run.id)
			print('Question Complete!')
			print()
			thread_messages = client.beta.threads.messages.list(self.thread_id)
			new_response = thread_messages.data[0].content[0].text.value
			new_message = thread_messages.data[1].content[0].text.value
			print(new_message)
			print()
			print(new_response)
	
	def print_thread(self):
		'''
			Prints the messages that exists within a thread. self.thread must exist to execute function call.
		'''
		if self.thread:
			thread_messages = client.beta.threads.messages.list(self.thread.id)
			for message in thread_messages.data[::-1]:
				print(message.content[0].text.value)
				print()
			return print('Thread complete!')
	
	def wait_for_complete(self, run_id:str=None, run_complete:bool=None):
		'''
			Executed via the new_thread_run() method. 
				1. Retrieves the status of the run object every 5 seconds (until 60 secs) to confirm that its complete
					1a. If the run is never completed, then the run_id and thread_id will be printed to reference later
				2. If run.status is 'complete', then the message will be printed 
					2a. Message will be printed by processing the JSON objects into Python dictionaries  from the Assistants response via process_message()
					2b. Python dictionary will then be processed via message_output()
				3. If you're analyzing lab report, API response has to be processed. If you're getting summary, API response does not need to be processed.
		'''
		if self.thread:
			if run_complete:
				self.print_thread()

			count = 0
			while True:
				# Retrieves the run object every 5 seconds to confirm its current status
				time.sleep(5)
				self.run = client.beta.threads.runs.retrieve(
					thread_id=self.thread.id,
					run_id=run_id
					)
				if self.run.status == "completed":
					#Logic to calculate the time it took to execute run
					elapsed_time = self.run.completed_at - self.run.created_at
					formatted_elapsed_time = time.strftime(
						":%H:%M:%S", time.gmtime(elapsed_time)
					)
					print(f"Run completed in {formatted_elapsed_time}")
					logging.info(f"Run completed in {formatted_elapsed_time}")
					print('Your run has completed!')	
					break
				else:
					count += 1
					#Loops through while loop for a minute
					if count == 24:
						print(self.run.id)
						print(self.thread.id)
						break
		else:
			return print("Check if you have valid thread and run objects")

class newChat:
	'''
		Use Case #4

		1. Class - newChat
		2. Purpose - Allows user to initiate a 'chatbot' (a thread with subsequent messages) from the 'chats' page - this serves as a general purpose chat where the assistant is not specialized based on lab test results 
		3. Assistant - Medical GPT Generalist (added by default)
			3a. Assistant will be updated with general instructions vs. specialization from a specific lab test
		4. Thread: N/A - A new thread will be created to initate the chatbot; subsequent messages will be added to the existing thread for further follow-up questions and responses 
	'''

	def __init__(self, model:str=model, client=client) -> None:
		self.client = client
		self.model = model
		self.assistant = None
		self.thread = None
		self.run = None
		

	thread_id = None
	file_id = None
	assistant_id = mgeneralist_assist_id

	def update_assist(self):
		'''
			Updates the Medical GPT Generalist Assistant to be a 'generalist' where there is not a specialization based on lab test results
		'''
		my_updated_assistant = client.beta.assistants.update(
			assistant_id=self.assistant_id,
			instructions="You will provide responses to users who will be asking general medical questions. Keep in mind, that your responses short be short and succinct. If a user wants additional information, they will ask further questions where you can elaborate further."
			)
		self.assistant = my_updated_assistant
		print("Your assistant has been modified! The results are below:")
		print(self.assistant.model_dump_json(indent=2))