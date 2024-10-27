# Vivo-Backend
Objective: Showcase all classes used in integrating the OpenAI Assistants API into the Vivo Hackathon Project. Vivo leverages the OpenAI Assistants API to analyze and make clinical lab results palatable to everyday people, empowering patients to ask more insightful questions and make informed decisions about their health.

## Table of Contents

- [Introduction](#introduction)
- [Purpose](#purpose)
- [Classes/Features](#classes)


## Introduction

According to the American Clinical Laboratory Association, more than 7 billion clinical lab tests are performed in the U.S. each year, providing critical data for a relatively 'small' expenditure. These clinical laboratory tests have an immesurable impact on diagnostic and treatment decisions made by health care providers. The result is earlier diagnosis and treatment, which lead to better prevention, and better therapy with fewer side effects. 

While these lab results provide an overview of a patients' current health, it doesn't take other variables into condition such as: diet, exercise, genetic conditions of a family, etc. Lab results/companies were not designed to account for these variables, yet they are essential to provide a holistic view of a patient.  

## Purpose

**Knowledge Empowerment**

Modern lab tests are an innovation in technology and science. With these innovations, oftentimes, patients who are reading the results may not directly understand the nuance or reasoning that leads to a finalized good/bad result. While patients should always consult with a physician regarding their lab test results, we seek to empower patients who are curious and want to explore all of their available options.

For example, a patient may receieve test results that indicates that their cholesterol is a little high. Understanding the meaning of the results means that an individual also understands the difference between good/bad cholesterol, genetic family history, diet, exercise, HDL, triglycerides, LDL and other contextual information. 

Let's say a patient understands the meaning of their results and has assessed various options that they can take to lower their cholesterol. If a physician suggests to perscribe medicine, the empowered patient can suggest 'natural' alternatives and see if they are viable before going on medication.  


**Vivo serves to:**

1. Assess a patients lab result and explain it in a palatable way
2. Leverage a patient's Apple Health information to personalize lab result explanations / next steps
3. Integrate an AI chatbot to each section of a lab result so that patients can ask add'l follow-up questions on a specific result

## Assistants

Two Assistants were created and fine-tuned for this project:

1. Lab Analyzer 3 - Data analyst that identifies whether a patient has uploaded a valid lab report and exports the results in JSON format
3. Medical GPT Generalist - Provides responses to general medical questions

## Classes

- **LabAnalyzer**
  - **Purpose:** Analyze lab reports into JSON objects with high-level summaries leveraging the Lab Analyzer 3 assistant 
  - **Methods:**
    - **retrieve_assist()** - Assigns the assistant object to self.assistant attribute
    - **retrieve_file()** - Prints the detail of an uploaded file based on file_id that is attached to class instance 
    - **file_upload()** - Uploads the file and assigns the file object to self.file attribute
    - **new_thread_run()** - Creates new thread and runs the message; assigns run and thread objects to self.run and self.thread attributes
    - **wait_for_completed()** - Checks the status of a run initiated by the new_thread_run() method until its complete. If a thread takes > 60secs to run, method completes 
    - **print_thread()** - Prints the messages that exists within a thread a thread object must be assigned to the self.thread attribute to execute function call
    - **process_message()** - Processes the JSON string from API response and converts it into a Python dictionary
    - **message_output()** - Processes the Python dictionary and prints API response into a readable f-string format. This method is for terminal purposes only!
    - **summarize()** - Provides a summary of granular lab report analysis

- **LabChat**
  - **Purpose:** Allows user to initiate a 'chatbot' (a thread with subsequent messages) from a specific test (section) from a lab report
  - **Methods:**
    - **update_assist()** - Updates the Medical GPT Generalist Assistant to ‘specialize’ based on the specific test result 
    - **new_thread_run()** - Default questions that the assistant answers based on the context of a lab test result
    - **new_message()** - Allows a user to ask a question to the assistant directly 
    - **print_thread()** - Prints the messages that exists within a thread. self.thread must exist to execute function call
    - **wait_for_complete()** - See notes for LabAnalyzer.wait_for_completed()
