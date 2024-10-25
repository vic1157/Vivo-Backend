from pydantic import BaseModel
import openai
from dotenv import find_dotenv, load_dotenv
import json
import time
import re
import logging

load_dotenv()
model = "gpt-4o"