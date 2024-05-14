from dotenv import dotenv_values
from twilio.rest import Client
import requests
from bs4 import BeautifulSoup
from bs4.element import Comment,NavigableString
from datetime import datetime
from urllib.request import Request, urlopen
import re
from tqdm import tqdm
from pypdf import PdfReader

from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
#Importing Keys

keys = dotenv_values()
account_sid = keys['TWILIO_AUTH_SID']
auth_token = keys['TWILIO_AUTH_TOKEN']

source_number = keys['TWILIO_NUMBER']
personal_number = keys['PERSONAL_NUMBER']

mistral_key = keys['MISTRAL_API_KEY'] #Comment if using ollama model
model = "mistral-large-latest" #Comment if using ollama model

client = MistralClient(api_key=mistral_key) #Comment if using ollama model
resume_path = keys['RESUME_PATH']

sms_prompt = '''Given the following jobs and it's appliability based on my resume. 

<job_description>

You are an assistant tasked with notifying any new potential job opening that are suitable.
Write me a SMS message notifying me about the job and about my applicability. Keep it short. Just draft the message. Don't specify links to apply.

'''


sms_client = Client(account_sid, auth_token)

def send_message(text):
    ''' Sends a SMS using a Twillio Account'''
    message = sms_client.messages.create(
            body=text,
            from_=source_number,
            to=personal_number
            )
    

def tag_visible(element):
    '''
    Function to identify visible text elements from a given webpage.
    These are text data part of the following parent tags.

    'style', 'script', 'head', 'title', 'meta', '[document]','i'

    Comments and Navigable Strings are also excluded. So are headings belonging to elements in 'dropdown-title' class
    '''
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]','i']:
        return False
    if 'class' in element.attrs:
        if "dropdown-title" in element.attrs['class']:
            return False
        if "btn" in element.attrs["class"]:
            return False
        if "nav__title" in element.attrs["class"]:
            return False
            return False
    if isinstance(element, Comment):
        return False
    if isinstance(element,NavigableString):
        return False
    return True


def text_from_html(body):
    '''
    Extracting text from webpage
    '''
    soup = BeautifulSoup(body, 'html.parser')
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    return u" ".join(t.strip() for t in visible_texts)

def extract_text_from_website(url:str) -> str:
    '''
    Function to extract text content from a given website. Takes the url as an input.

    It uses Mozilla User Agent to access webpages and returns texts that are part of 'h1', 'h2', 'h3', 'h4', 'h5', 'h6','p' tags.
    Filters out unwanted html content.
    '''
    try:
        req = Request(url,headers={'User-Agent':"Mozilla/5.0"})
        html = urlopen(req)
        soup = BeautifulSoup(html,'html.parser')
        text = soup.findAll(['h1', 'h2', 'h3', 'h4', 'h5', 'h6','p'])
        visible_texts = filter(tag_visible, text)
        return "\n".join([txt.text for txt in visible_texts])
    except:
        return ""
    
def fetch_pdf(path:str) -> str:
    '''Function that takes in a PDF file as returns the text content present in it.'''
    reader = PdfReader(path)
    content = ""
    number_of_pages = len(reader.pages)
    for pg in range(number_of_pages):
        content = content + reader.pages[pg].extract_text()
        content = content + "\n\n"
    return content

def hackernews_jobs():
    '''Function to fetch job from hackernews YCombinator JobBoard. The output schema contains the following information.
        Job Posted Date: The date on which the job was posted.
        Subject: The heading under which the job was posted.
        Apply At: The URL under which the job has to be applied. In somecases, some jobs donot have this. Instead a email is provided in the description.
        Description: The text associated with the job. Incase there is no description provided by the API, and the URL is for the company website. We scrap contents from the career page of the company.
    '''
    today = str(datetime.now().date())
    base = requests.get("https://hacker-news.firebaseio.com/v0/jobstories.json?print=pretty")
    base_value = base.json()
    base_value = ["https://hacker-news.firebaseio.com/v0/item/" + str(id) +".json?print=pretty" for id in base_value]
    jobs =  [requests.get(bv).json() for bv in base_value]
    jobs = [{"Job Posted Date": str(datetime.fromtimestamp(j["time"]).date()), "Subject": j["title"], "Apply at": j["url"], "Description": extract_text_from_website(j["url"])} if 'url' in j.keys() else {"Job Posted Date": str(datetime.fromtimestamp(j["time"]).date()), "Subject": j["title"], "Description": j.get("text", "")} for j in jobs]
    jobs = [jd for jd in jobs if jd["Job Posted Date"] == today] #Comment this line for not limiting to jobs posted current day or modify for required filtering condition.
    return jobs

#Using Mistral

def job_applicability(jd):
  '''
  Function that takes in a job description and compares the resume contents with the job description and generates an applicability score for the job.
  
  '''
  response = client.chat(
    model=model,
    messages=[ChatMessage(role="user", content='Given the following resume/n'+ resume_content +"/nEvalute the applicability of the resume provided for the job below.Show only an applicability score out of 10 for the job below with respect to the provided resume.Keep it short./n" + str(jd))]
)
  jd["Applicability"] = response.choices[0].message.content
  return jd


#Using llama3
# import ollama

# def job_applicability(jd):
#  '''
#  Function that takes in a job description and compares the resume contents with the job description and generates an applicability score for the job.
  
#  '''
#   response = ollama.chat(model='llama3', messages=[
#     {
#       'role': 'user',
#       'content': 'Given the following resume/n'+ resume_content +"/nEvalute the applicability of the resume provided for the job below.Show only an applicability score out of 10 for the job below with respect to the provided resume/n" + str(jd) ,
#      },
#     ])
#   jd["Applicability"] = response['message']['content']
#   return jd



job_data = hackernews_jobs()

#Fetching and cleaning data from resume. Resume should be a pdf file.
resume_content = fetch_pdf(resume_path)
resume_content = resume_content.split("\n \n")
resume_content = [re.sub(r'[^\x00-\x7F]+', '', txt) for txt in resume_content]
resume_content = "\n".join([rc.replace("\n"," ") for rc in resume_content if rc.replace(" ","").replace("\n","") !=""])

# Calculating applicability for each jobs.
job_data = [job_applicability(jd) for jd in tqdm(job_data)]

#Using Mistral
def make_sms(jd):
  '''Function to draft Alert SMS, given Job Details and Applicablity'''
  jd_text = "\n".join([key +" : " + value for key,value in jd.items()])
  response = client.chat(
    model=model,
    messages=[ChatMessage(role="user", content=sms_prompt.replace("<job_description>",jd_text))]
)
  return response.choices[0].message.content + "\nApply at " + jd["Apply at"] + "\nJob Posted at " +jd["Job Posted Date"] if "Apply at" in jd.keys() else response.choices[0].message.content + "\nApply at YCombinator Jobs\nJob Posted at " +jd["Job Posted Date"]


# Using llama3
# def make_sms(jd):
#  '''Function to draft Alert SMS, given Job Details and Applicablity'''
#   jd_text = "\n".join([key +" : " + value for key,value in job_data[0].items()])
#   response = ollama.chat(model='llama3', messages=[
#     {
#       'role': 'user',
#       'content':sms_prompt.replace("<job_description>",jd_text) ,
#      },
#     ])
#   return response["message"]["content"] + "\nApply at " + jd["Apply at"] + "\nJob Posted at " +jd["Job Posted Date"]

#Drafting and sending SMS for all jobs fetched
message_queue = [make_sms(jd) for jd in job_data]
[send_message(sms) for sms in message_queue]