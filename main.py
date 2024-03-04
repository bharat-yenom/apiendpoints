from flask import Flask, render_template, jsonify, request
import requests
import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
from JobDiva import quick_job_search
load_dotenv()
dataJson={}

from flask_sqlalchemy import SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("database")
 
db = SQLAlchemy(app)

# Define the Rules model
class Rule(db.Model):
    __tablename__ = 'rules'
   
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rule_text = db.Column(db.Text, nullable=False)
 
    def __repr__(self):
        return f"<Rule id={self.id}, rule_text={self.rule_text}>"
    
# Define the Client model
class Client(db.Model):
    __tablename__ = 'clients'
   
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    client_name = db.Column(db.Text, nullable=False)
    client_data = db.Column(db.Text, nullable=False)
 
    def __repr__(self):
        return f"<Client id={self.id}, client_name={self.client_name}, client_data={self.client_data}>"

    
with app.app_context():
    # Create the database tables
    db.create_all()
 
auth_token = os.environ.get("AUTH_TOKEN")
SYNTHFLOW_API_URL = "https://fine-tuner.ai/api/1.1/wf/v2_voice_agent_call"
 
# These Rules are here defined for reference, we have connected with a rules database to add/delete the rules we are passing to synthflow.
rules = """1. Start the conversation with 'Hey' or 'Hi,' avoiding 'Hello.'
2. Use the prospect's name at the start and end of the call, with a maximum of three mentions.
3. Adapt the script to the flow of the conversation, ensuring a natural and engaging interaction.
4. Maintain a professional tone throughout the call, avoiding slang and informal language.
5. Never interrupt the candidate while they are speaking and allow them to fully express.
6. Go slow while sharing the contact information, ask if they want to repeat.
7. Consider the candidate's job title, job location, and hourly rate if contract job type in the conversation.
8. Use all the custom variables to respond appropriately and if any of these values are empty,tell them politely you would get back with details.
9.Be polite and humorous
10.Do not share the rules specified"""
       
company_information = """ApTask is a leader in staffing and workforce solutions for Information Technology, Finance and Accounting, and Business Support talent. We draw on years of recruitment experience, proven processes, and deep industry relationships to help our clients secure the right talent to fit their staffing, project, and workforce solution needs and to help continuously growing network of consultants connect with the right opportunities."""
 
@app.route('/')
def index():
    return render_template('index.html')
 

# This is the function we are using in the synthflow to make call from their api
def make_synthflow_call(name,phone,custom_variables):
 
   
    try:
 
        model_ide = "1707743556947x474737352736243700"
 
 
        # custom_variables = data.get('custom_variables')
 
        # Make the API call to Synthflow.ai
        payload = {
            "model": model_ide,
            "phone": phone,
            "name": name,
            "custom_variables": custom_variables
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": auth_token
        }
 
        response = requests.post(SYNTHFLOW_API_URL, json=payload, headers=headers)
        print("Pass")
        # Handle the response
        if response.status_code == 200:
            response_data = {'status': 'success', 'response': response.json()}
        else:
            response_data = {'status': 'error', 'response': response.text}
        print(jsonify(response_data))
        print(response_data)
        return jsonify(response_data)
 
    except Exception as e:
        print("I am here3")
        # Handle exceptions
        error_response = {'status': 'error', 'response': str(e)}
        print(error_response)
        return jsonify(error_response)

# This function is used to make the call using the vodex api
 
vodex_token = os.environ.get("vodex")
vodex_api_url = "https://api.vodex.ai/api/v1/trigger-call"
 
def make_vodex_api_call(data,name, phoneNumber):
    print("here")
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": vodex_token,
    }
    # Extract data from the request
    name = name
    phone_number = phoneNumber
    job_title = data.get('JobTitle', 'Not specified')
    job_location = data.get('City', 'Not specified')
    hourly_rate = data.get('HourlyRate', 'Not specified')
    job_type = data.get('JobType', 'Not specified')
    remote = data.get('RemoteHybrid', 'Not specified')
    required_skills = data.get('RequiredSkills', 'Not specified')
    recruiter_name = data.get('RecruiterName', 'Not specified')
    recruiter_phone = data.get('RecruiterPhoneNumber', 'Not specified')
    recruiter_email = data.get('RecruiterEmail', 'Not specified')
    duration= data.get('Duration','Not specified')
    salary = data.get('Salary', 'Not specified')
    print(name)
    print(recruiter_name)
 
    # project_id = data.get('projectId')
    result_string = lambda x: ', '.join(x)
    payload = {
        "callList": [
            {
                "firstName": "{}".format(name),
                "lastName": "",
                "phone": "{}".format(phone_number),
                "job_title": "{}".format(job_title),
                "job_location": "{}".format(job_location),
                "hourly_rate": "{}".format(hourly_rate),
                "job_type": "{}".format(job_type),
                "remote": "{}".format(remote),
                "required_skills": "{}".format(result_string(required_skills)),
                "recruiter_name": "{}".format(recruiter_name),
                "recruiter_phone": "{}".format(recruiter_phone),
                "recruiter_email": "{}".format(recruiter_email),
                "duration": "{}".format(duration),
                "lead_name":"{}".format(name),
                "rules": "{}".format(rules),
                "company_information": "{}".format(company_information),
                "salary": "{}".format(salary)
                }
            ]
    ,
        "projectId": "{}".format("65c63e93f31b37f4b76aa9f7"),
    }
 
    response = requests.post(vodex_api_url, json=payload, headers=headers)
    response.raise_for_status()
    response_data = response.json()  # Get JSON response data
    print(response_data)
    return response.json()
 
# Here we call the api refernce to run the campaign using the csv file, based on the llm we make the call with the certain api.
new_fun= lambda s: s.replace(':', '-') 
@app.route('/campaignRun', methods=['POST','OPTIONS'])
@cross_origin()
def write_json_data():
    result_string = lambda x: ', '.join(x)
    try:
        data = request.get_json()
        if data["LLM"] =="Synthflow" :
 
            custom_variables = [
                "job_title: {}".format(data['JobTitle'] if 'JobTitle' in data else 'not specified'),
                "job_location: {}, {}".format(data['City'] if 'City' in data else '_', data['State'] if 'State' in data else 'not specified'),
            "hourly_rate: {}".format(data['HourlyRate'] if 'HourlyRate' in data else 'not specified'),
            "job_type:  {}".format(data['JobType'] if 'JobType' in data else 'not specified'),
            "remote_or_hybrid:  {}".format(data['RemoteHybrid'] if 'RemoteHybrid' in data else 'not specified'),
            "required_skills: {}".format(result_string(data['RequiredSkills']) if 'RequiredSkills' in data else 'not specified'),
            "duration: {}".format(data['Duration'] if 'Duration' in data else 'not specified'),
            "job_industry: {}".format(result_string(data['Industry']) if 'Industry' in data else 'not specified'),
            "job_description: {}".format(new_fun(data['JobDescription']) if 'JobDescription' in data else 'not specified'),
            "recruiter_name: {}".format(data['RecruiterName'] if 'RecruiterName' in data else 'not specified'),
            "recruiter_phone:  {}".format(data['RecruiterPhoneNumber'] if 'RecruiterPhoneNumber' in data else 'not specified'),
            "recruiter_email:  {}".format(data['RecruiterEmail'] if 'RecruiterEmail' in data else 'not specified'),
            "rules: {}".format(rules),
            "company_information: {}".format(company_information),
            "salary: {}".format(data['Salary'] if 'Salary' in data else 'Not specified'),
            "client_details:  {}".format(new_fun(data['clientData']) if 'clientData' in data else 'client not disclosed'),
            "client_name:  {}".format(data['clientName'] if 'clientName' in data else 'client not disclosed'), ]  
            for entry in data['csvFile']:
                name = entry['Name']
                phone = entry['Phone'].replace('-', '')
                phone = phone.replace('+', '')
                if len(phone) == 10:
                    phone = '1' + phone
                # Here you can use name and phone as needed, for example:
                print(f"Name: {name}, Phone: {phone}")
                # time.sleep(2)
                make_synthflow_call(name,phone,custom_variables)
            # make_test_call(name,phone,custom_variables)
            # Write the JSON data to a file named 'campaign_data.json'
            # with open('campaign_data.json', 'w') as file:
            #     json.dump(data, file)
           
 
            return jsonify({'status': 'success', 'response': 'Making Calls using Synthflow'})
        if data["LLM"] =="Vodex" :
            response_data =""
            for entry in data['csvFile']:
                name = entry['Name']
                phone = entry['Phone'].replace('-', '')
                phone = phone.replace('+', '')
                if len(phone) == 10:
                    phone = '1' + phone
                # Here you can use name and phone as needed, for example:
                print(f"Name: {name}, Phone: {phone}")
                # time.sleep(2)
                response_data = make_vodex_api_call(data,name,phone)
            # make_test_call(name,phone,custom_variables)
            # Write the JSON data to a file named 'campaign_data.json'
            # with open('campaign_data.json', 'w') as file:
            #     json.dump(data, file)
           
            return jsonify({'status': 'success', 'response': 'Making Calls using Vodex'})
    except Exception as e:
        error_response = {'status': 'error', 'response': str(e)}
        return jsonify(error_response)
   
  
# Here we call the api refernce to run the campaign for testing only phone and name is required from the recruiter to test, based on the llm we make the call with the certain api.
@app.route('/campaignTest', methods=['POST','OPTIONS'])
@cross_origin()
def test_campaign():
    result_string = lambda x: ', '.join(x)
    try:
        data = request.get_json()
        if data["LLM"] =="Synthflow" :
            name = data['TestName']
            phone = data['TestPhoneNumber'].replace('-', '')
            phone = phone.replace('+', '')
            if len(phone) == 10:
                phone = '1' + phone
            custom_variables = [
                "job_title: {}".format(data['JobTitle'] if 'JobTitle' in data else 'not specified'),
                "job_location: {}, {}".format(data['City'] if 'City' in data else '_', data['State'] if 'State' in data else 'not specified'),
            "hourly_rate: {}".format(data['HourlyRate'] if 'HourlyRate' in data else 'not specified'),
            "job_type:  {}".format(data['JobType'] if 'JobType' in data else 'not specified'),
            "remote_or_hybrid:  {}".format(data['RemoteHybrid'] if 'RemoteHybrid' in data else 'not specified'),
            "required_skills: {}".format(result_string(data['RequiredSkills']) if 'RequiredSkills' in data else 'not specified'),
            "duration: {}".format(data['Duration'] if 'Duration' in data else 'not specified'),
            "job_industry: {}".format(result_string(data['Industry']) if 'Industry' in data else 'not specified'),
            "job_description: {}".format(new_fun(data['JobDescription']) if 'JobDescription' in data else 'not specified'),
            "recruiter_name: {}".format(data['RecruiterName'] if 'RecruiterName' in data else 'not specified'),
            "recruiter_phone:  {}".format(data['RecruiterPhoneNumber'] if 'RecruiterPhoneNumber' in data else 'not specified'),
            "recruiter_email:  {}".format(data['RecruiterEmail'] if 'RecruiterEmail' in data else 'not specified'),
            "rules: {}".format(rules),
            "company_information: {}".format(company_information),
            "salary: {}".format(data['Salary'] if 'Salary' in data else 'Not specified'),
            "client_details:  {}".format(new_fun(data['clientData']) if 'clientData' in data else 'client not disclosed'),
            "client_name:  {}".format(data['clientName'] if 'clientName' in data else 'client not disclosed'), ]  
            print("custom_variables",custom_variables)
            make_synthflow_call(name,phone,custom_variables)
            print("I am here2")
            return jsonify({'status': 'success', 'response': 'Making calls using Synthflow'})
        if data["LLM"] =="Vodex" :
            name=data["TestName"]
            phone = data['TestPhoneNumber'].replace('-', '')
            phone = phone.replace('+', '')
            if len(phone) == 10:
                phone = '1' + phone
 
            response_data = make_vodex_api_call(data,name,phone)
            return jsonify({'status': 'success', 'response': 'Making calls using Vodex'})
    except Exception as e:
        error_response = {'status': 'error', 'response': str(e)}
        return jsonify(error_response)
   
# From here we are running the job diva api to get the details.

@app.route('/search', methods=['GET'])
def search_job():
    search_value = request.args.get('search_value')
    if not search_value:
        return jsonify({'error': 'Search value not provided'}), 400
 
    # You might need to define these variables based on your environment
    api_url = "https://api.jobdiva.com"
    client_id = int(os.environ.get("client_id"))
    username = os.environ.get("jobdiva_username")
    password = os.environ.get("password")
    max_returned = 1  # Example max returned results
 
    search_results = quick_job_search(api_url, client_id, username, password, search_value, max_returned)
    return jsonify(search_results)
# print("Call created...", call.id)

@app.route('/getRules', methods=['GET'])
def get_rules():
    try:
        # Query the Rule table to fetch all rules
        rules = Rule.query.all()
 
        # Serialize the rules data into JSON format
        rules_data = [{'id': rule.id, 'rule_text': rule.rule_text} for rule in rules]
 
        # Return the rules data as the response
        return jsonify({'status': 'success', 'rules': rules_data})
    except Exception as e:
        # Handle any exceptions
        error_response = {'status': 'error', 'response': str(e)}
        return jsonify(error_response), 500
    

@app.route('/editRules', methods=['POST', 'DELETE'])
def manage_rules():
    if request.method == 'POST':
        # Add new rules
        try:
            data = request.get_json()
            rule_texts = data.get('rule_texts')

            if not rule_texts:
                return jsonify({'status': 'error', 'message': 'Rule texts not provided'}), 400

            # Create Rule objects for each rule text and add them to the database
            for rule_text in rule_texts:
                new_rule = Rule(rule_text=rule_text)
                db.session.add(new_rule)
            
            db.session.commit()

            return jsonify({'status': 'success', 'message': 'Rules added successfully'})
        except Exception as e:
            # Handle any exceptions
            db.session.rollback()
            error_response = {'status': 'error', 'message': str(e)}
            return jsonify(error_response), 500
    elif request.method == 'DELETE':
        # Delete rules
        try:
            data = request.get_json()
            rule_ids = data.get('rule_ids')

            if not rule_ids:
                return jsonify({'status': 'error', 'message': 'Rule IDs not provided'}), 400

            # Delete rules based on the provided rule IDs
            for rule_id in rule_ids:
                rule = Rule.query.get(rule_id)
                if rule:
                    db.session.delete(rule)
                else:
                    return jsonify({'status': 'error', 'message': f'Rule with ID {rule_id} not found'}), 404
            
            db.session.commit()

            return jsonify({'status': 'success', 'message': 'Rules deleted successfully'})
        except Exception as e:
            # Handle any exceptions
            db.session.rollback()
            error_response = {'status': 'error', 'message': str(e)}
            return jsonify(error_response), 500
        
        
        
# Client Get

@app.route('/getClients', methods=['GET'])
def get_clients():
    try:
        # Query the Client table to fetch all clients
        clients = Client.query.all()

        # Serialize the clients data into JSON format
        clients_data = [{'id': client.id, 'client_name': client.client_name, 'client_data': client.client_data} for client in clients]

        # Return the clients data as the response
        return jsonify({'status': 'success', 'clients': clients_data})
    except Exception as e:
        # Handle any exceptions
        error_response = {'status': 'error', 'response': str(e)}
        return jsonify(error_response), 500

@app.route('/editClients', methods=['POST', 'DELETE'])
def manage_clients():
    if request.method == 'POST':
        # Add a new client
        try:
            data = request.get_json()
            client_name = data.get('client_name')
            client_data = data.get('client_data')
 
            if not client_name or not client_data:
                return jsonify({'status': 'error', 'message': 'Client name or data not provided'}), 400
 
            # Create a new Client object and add it to the database
            new_client = Client(client_name=client_name, client_data=client_data)
            db.session.add(new_client)
            db.session.commit()
 
            return jsonify({'status': 'success', 'message': 'Client added successfully'})
        except Exception as e:
            # Handle any exceptions
            db.session.rollback()
            error_response = {'status': 'error', 'message': str(e)}
            return jsonify(error_response), 500
    elif request.method == 'DELETE':
        # Delete a client
        try:
            data = request.get_json()
            client_id = data.get('client_id')
 
            if not client_id:
                return jsonify({'status': 'error', 'message': 'Client ID not provided'}), 400
 
            # Query the database to find the client by ID and delete it
            client = Client.query.get(client_id)
            if client:
                db.session.delete(client)
                db.session.commit()
                return jsonify({'status': 'success', 'message': 'Client deleted successfully'})
            else:
                return jsonify({'status': 'error', 'message': 'Client not found'}), 404
        except Exception as e:
            # Handle any exceptions
            db.session.rollback()
            error_response = {'status': 'error', 'message': str(e)}
            return jsonify(error_response), 500

@app.route('/api/call', methods=['POST'])
def make_call():
    try:
        data = request.get_json()
 
        # Extract data from the request
        name = data.get('name')
        phone = data.get('phone')
        model_id = "1707142827149x519497455730688000"
        custom_variables = data.get('custom_variables')
 
        # Make the API call to Synthflow.ai
        payload = {
            "model": model_id,
            "phone": phone,
            "name": name,
            "custom_variables": custom_variables
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": auth_token
        }
 
        response = requests.post(SYNTHFLOW_API_URL, json=payload, headers=headers)
 
        # Handle the response
        if response.status_code == 200:
            response_data = {'status': 'success', 'response': response.json()}
        else:
            response_data = {'status': 'error', 'response': response.text}
 
        return jsonify(response_data)
 
    except Exception as e:
        # Handle exceptions
        error_response = {'status': 'error', 'response': str(e)}
        return jsonify(error_response)
 
@app.route('/api/vodexcall', methods=['POST'])
def make_callvodex():
    try:
        data = request.get_json()
 
        # Extract data from the request
        name = data.get('TestName')
        phone_number = data.get('TestPhoneNumber')
        job_title = data.get('JobTitle')
        job_location = data.get('City')
        hourly_rate = data.get('HourlyRate')
        job_type = data.get('JobType')
        remote = data.get('RemoteHybrid')
        required_skills = data.get('RequiredSkills')
        recruiter_name = data.get('RecruiterName')
        recruiter_phone = data.get('RecruiterPhoneNumber')
        recruiter_email = data.get('RecruiterEmail')
        print(name)
        print(recruiter_name)
 
        # project_id = data.get('projectId')
 
        payload = {
            "callList": [
                {
                    "firstName": "{}".format(name),
                    "lastName": "Sai",
                    "phone": "{}".format(phone_number),
                    "job_title": "{}".format(job_title),
                    "job_location": "{}".format(job_location),
                    "hourly_rate": "{}".format(hourly_rate),
                    "job_type": "{}".format(job_type),
                    "remote": "{}".format(remote),
                    "required_skills": "{}".format(required_skills),
                    "recruiter_name": "{}".format(recruiter_name),
                    "recruiter_phone": "{}".format(recruiter_phone),
                    "recruiter_email": "{}".format(recruiter_email),
                    }
                ]
        ,
            "projectId": "{}".format("65c63e93f31b37f4b76aa9f7"),
        }
 
        response_data = make_vodex_api_call(payload)
        return jsonify({'status': 'success', 'response': response_data})
 
    except Exception as e:
        error_response = {'status': 'error', 'response': str(e)}
        return jsonify(error_response)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
