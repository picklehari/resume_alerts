**README**
=====================================================

Overview
--------

The tool provided is  designed to monitor job postings from YCombinator Hackernews, compare them against a resume, and generate SMS alerts for potential job opportunities. This system utilizes various libraries and APIs to fetch job postings, extract relevant information from job descriptions and resumes, and assess job applicability based on resume content.

# Functionality
-------------

### Job Data Retrieval

Fetches job postings from Hackernews YCombinator JobBoard, including details like job posted date, subject, application URL, and description.

### Resume Processing

Extracts text content from a PDF resume file for comparison with job descriptions.

### Job-Resume Comparison

Evaluate the resume's applicability for each job by comparing the resume content with the job description and generating an applicability score out of 10.

### SMS Alert Generation

Drafts SMS messages notifying about new job openings that match the resume, specifying links to apply and how well the job matches your resume.

Usage
-----
## Make a .env file using the .env_example as a Template
Replace the placeholders in the code with your actual parameters for Twilio and Mistral along the path to your resume.

- `Twilio` : You may find the authentication tokens [here](https://www.twilio.com/console/runtime/api-keys) and phone numbers [here](https://www.twilio.com/try-twilio)
- `Mistral` : You can create api keys [here](https://console.mistral.ai/api-keys/)
- `Resume` : Provide path to the resume file. 

If using in local mode. Comment the necessary sections in the `resume_alerts.py` file. Additionally, you would have to setup `ollama` and pull the `llama3` model.

- Ollama can be downloaded by clicking [here](https://ollama.com/download)
- llama3 can be setup by running by `ollama pull llama3`

### Run the Code

Execute the code to fetch job postings, process the resume, compare job descriptions with the resume, and generate SMS alerts.

Dependencies
------------

- `dotenv` for environment variable management
- `twilio` for SMS messaging
- `requests` and `BeautifulSoup` for web scraping
- `tqdm` for progress bar management
- `pypdf` for PDF file processing
- `mistralai` or `ollama` for job applicability assessment
