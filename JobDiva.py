import requests
import os
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()
API_KEY = os.environ.get('OPENAI_KEY')
def extract_job_description_with_openai(job_description):
    client = OpenAI(api_key=API_KEY)
 
    # Define the prompt for ChatGPT
    prompt = f"Extract just the job description and rewrite in good way in all detail without heading: '{job_description}'"
 
    # Generate completion using ChatGPT
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Extract job description"},
            {"role": "user", "content": prompt}
        ]
    )
 
    # Extract the job description text from the completion
    job_desc_text = completion.choices[0].message.content
 
    return job_desc_text
 
def extract_skills(job_description):
    client = OpenAI(api_key=API_KEY)
 
    # Define the prompt for ChatGPT
    prompt = f"Given the job description '{job_description}', list the required skills and desired skills as comma-separated values. They should be none overlapping and more than zero in each.Keep the gap of one line between required and desired skills.First list required skills comma separated without mentioning heading then space of one line and then dsired skills.Limit the individual skill to maximum three words "
 
    # Generate completion using ChatGPT
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Extract skills"},
            {"role": "user", "content": prompt}
        ]
    )
 
    completion_text = completion.choices[0].message.content
    # Split the content into required and desired skills
    skills = completion_text.split('\n')
    # Extract required skills
    required_skills = skills[0]
    # Extract desired skills
    desired_skills = skills[2]
    # print(completion_text)
    # print("skills",completion_text)
    return required_skills, desired_skills
 
def quick_job_search(api_url, client_id, username, password, search_value, max_returned):
    login_url = f"{api_url}/apiv2/v2/login"
    search_url = f"{api_url}/apiv2/jobdiva/quickJobSearch"
 
    # Log in to JobDiva
    payload = {
        "clientId": client_id,
        "userName": username,
        "password": password
    }
    response = requests.post(login_url, json=payload)
    # print("response",response)
    if response.status_code == 200:
        access_token = response.json().get("token")
 
        # Make quick job search request
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"value": search_value, "maxReturned": max_returned}
        search_response = requests.get(search_url, headers=headers, params=params)
        if search_response.status_code == 200:
            # print("search_response",search_response)
            response_json = search_response.json()
            json_jd = response_json[0]['job description']
            # print("json_jd",json_jd)
            human_written_job_description = extract_job_description_with_openai(json_jd)
            # print("human_written_job_description",human_written_job_description)
            required_skills, desired_skills = extract_skills(human_written_job_description)
            # print("required_skills, desired_skills",required_skills, desired_skills)
            return {"JobTitle": response_json[0]['job title'],"City": response_json[0]['city'],"State": response_json[0]['state'],"ZipCode": response_json[0]['zipcode'],"JobType": response_json[0]['job type'],"HourlyRate": response_json[0]['minimum rate'],"JobDescription": human_written_job_description,"required_skills": required_skills, "desired_skills": desired_skills}
            # return search_response.json()
        else:
            return {"error": "Failed to search jobs"}
    else:
        return {"error": "Failed to log in to JobDiva"}
 
# # Example usage
# api_url = "https://api.jobdiva.com"
# client_id = int(os.getenv("client_id"))
# username = os.getenv("jobdiva_username")
# password = os.getenv("password")
# search_value = "11957095"  # Example search value
# max_returned = 1  # Example max returned results
 
# search_results = quick_job_search(api_url, client_id, username, password, search_value, max_returned)
# print(search_results)
