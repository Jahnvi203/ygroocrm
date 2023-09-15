import requests
import re
from copy import deepcopy
from flask import Flask, render_template, request, redirect, url_for, session, abort
from flask_pymongo import PyMongo
from pymongo import MongoClient
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY
import os
import time
import pytz
from requests.utils import requote_uri
import traceback

app = Flask(__name__)
app.secret_key = os.getenv("app_secret_key")
app.config['MONGO_URI'] = f'mongodb+srv://Jahnvi203:{os.getenv("mongodb_pwd").replace("@", "%40")}@cluster0.cn63w2k.mongodb.net/ygroocrm?retryWrites=true&w=majority'
mongo = PyMongo(app)

companies_col = mongo.db.companies
contacts_col = mongo.db.contacts
meetings_col = mongo.db.meetings
reminders_col = mongo.db.reminders
phone_comms_col = mongo.db.phone_comms
contact_lists_col = mongo.db.contact_lists
lists_contacts_col = mongo.db.lists_contacts
bulk_emails_col = mongo.db.bulk_emails
log_col = mongo.db.log
bearer_col = mongo.db.bearer
users_col = mongo.db.users

@app.route('/')
def index():
    if 'login_email' not in session or 'login_pwd' not in session:
        return redirect(url_for("login"))
    elif session['access_level'] != "admin" and session['access_level'] != "sales":
        abort(403)
    else:
        try:
            today_dt = datetime.now(timezone(timedelta(hours = 5, minutes = 30))).strftime('%Y-%m-%dT%H:%M:%SZ')
            current_week_dt = (datetime.now(timezone(timedelta(hours = 5, minutes = 30))) + timedelta(days = 7)).strftime('%Y-%m-%dT%H:%M:%SZ')
            pending_list = list(reminders_col.find({
                'Show': True,
                'Due Date & Time': {'$lt': today_dt}
            }).sort('Due Date & Time'))
            due_today_list = list(reminders_col.find({
                'Show': True,
                'Due Date & Time': {'$gte': today_dt, '$lt': current_week_dt}
            }).sort('Due Date & Time'))
            due_week_list = list(reminders_col.find({
                'Show': True,
                'Due Date & Time': {'$gte': current_week_dt}
            }).sort('Due Date & Time'))
            pending_rows_html = ""
            due_today_rows_html = ""
            due_week_rows_html = ""
            if len(pending_list) > 0:
                pending_rows_html = ""
                for i in range(len(pending_list)):
                    new_dt = datetime.strptime(pending_list[i]['Due Date & Time'], "%Y-%m-%dT%H:%M").replace(tzinfo = pytz.timezone('Asia/Kolkata'))
                    due_since = datetime.now(timezone(timedelta(hours = 5, minutes = 30))) - new_dt
                    due_since = due_since.days
                    pending_rows_html += f"""<tr>
                        <td><input id="reminder_check_{pending_list[i]['Reminder ID']}" onchange="check_reminder({pending_list[i]['Reminder ID']})" type="checkbox"></td>
                        <td>{pending_list[i]['Reminder']}</td>
                        <td>{pending_list[i]['Company']}</td>
                        <td>{pending_list[i]['Contact']}</td>
                        <td>{pending_list[i]['Recurrence']}</td>
                        <td><p class="attention">{new_dt.strftime("%d/%m/%Y %I:%M %p")}</p></td>
                        <td><p class="attention">{due_since} days</p></td>
                    </tr>"""
                pending_html = f"""<table class="table table-responsive">
                    <tr>
                        <th></th>
                        <th>Note</th>
                        <th>Company</th>
                        <th>Contact</th>
                        <th>Recurrence</th>
                        <th>Due Date & Time</th>
                        <th>Due Since</th>
                    </tr>
                    {pending_rows_html}
                </table>"""
            else:
                pending_html = "None"
            if len(due_today_list) > 0:
                due_today_rows_html = ""
                for i in range(len(due_today_list)):
                    new_dt = datetime.strptime(due_today_list[i]['Due Date & Time'], "%Y-%m-%dT%H:%M").replace(tzinfo = pytz.timezone('Asia/Kolkata'))
                    due_since = datetime.now(timezone(timedelta(hours = 5, minutes = 30))) - new_dt
                    due_since = due_since.days
                    due_today_rows_html += f"""<tr>
                        <td><input id="reminder_check_{due_today_list[i]['Reminder ID']}" onchange="check_reminder({due_today_list[i]['Reminder ID']})" type="checkbox"></td>
                        <td>{due_today_list[i]['Reminder']}</td>
                        <td>{due_today_list[i]['Company']}</td>
                        <td>{due_today_list[i]['Contact']}</td>
                        <td>{due_today_list[i]['Recurrence']}</td>
                        <td><p class="attention">{new_dt.strftime("%d/%m/%Y %I:%M %p")}</p></td>
                    </tr>"""
                due_today_html = f"""<table class="table table-responsive">
                    <tr>
                        <th></th>
                        <th>Note</th>
                        <th>Company</th>
                        <th>Contact</th>
                        <th>Recurrence</th>
                        <th>Due Date & Time</th>
                    </tr>
                    {due_today_rows_html}
                </table>"""
            else:
                due_today_html = "None"
            if len(due_week_list) > 0:
                due_week_rows_html = ""
                for i in range(len(due_week_list)):
                    new_dt = datetime.strptime(due_week_list[i]['Due Date & Time'], "%Y-%m-%dT%H:%M").replace(tzinfo = pytz.timezone('Asia/Kolkata'))
                    due_since = datetime.now(timezone(timedelta(hours = 5, minutes = 30))) - new_dt
                    due_since = due_since.days
                    due_week_rows_html += f"""<tr>
                        <td><input id="reminder_check_{due_week_list[i]['Reminder ID']}" onchange="check_reminder({due_week_list[i]['Reminder ID']})" type="checkbox"></td>
                        <td>{due_week_list[i]['Reminder']}</td>
                        <td>{due_week_list[i]['Company']}</td>
                        <td>{due_week_list[i]['Contact']}</td>
                        <td>{due_week_list[i]['Recurrence']}</td>
                        <td><p class="attention">{new_dt.strftime("%d/%m/%Y %I:%M %p")}</p></td>
                    </tr>"""
                due_week_html = f"""<table class="table table-responsive">
                    <tr>
                        <th></th>
                        <th>Note</th>
                        <th>Company</th>
                        <th>Contact</th>
                        <th>Recurrence</th>
                        <th>Due Date & Time</th>
                    </tr>
                    {due_week_rows_html}
                </table>"""
            else:
                due_week_html = "None"
            return render_template("index.html", pending_html = pending_html, due_today_html = due_today_html, due_week_html = due_week_html)
        except Exception as e:
            traceback.print_exc()
            return render_template("error.html", error = e)

@app.route('/companies')
def companies():
    if 'login_email' not in session or 'login_pwd' not in session:
        return redirect(url_for("login"))
    elif session['access_level'] != "admin" and session['access_level'] != "sales":
        abort(403)
    else:
        try:
            table = list(companies_col.find())
            statuses = ['Prospect', 'Called', 'Emailed', 'Not Interested', 'Proposal Sent', 'Meeting Scheduled', 'MoU Signed']
            if len(table) > 0:
                rows_html = ""
                for i in range(len(table)):
                    rows_html += f"""<tr>
                        <td>{table[i]['Company ID']}</td>
                        <td>{table[i]['Company']}</td>
                        <td>{table[i]['State']}</td>
                        <td>{table[i]['Sector']}</td>
                        <td>{table[i]['Employees']}</td>
                        <td>
                            <select id="status_{table[i]['Company ID']}" onchange="status_change({table[i]['Company ID']}, this.value)">
                                <option value="Prospect"{" selected" if table[i]['Status'] == "Prospect" else ""}>Prospect</option>
                                <option value="Called"{" selected" if table[i]['Status'] == "Called" else ""}>Called</option>
                                <option value="Emailed"{" selected" if table[i]['Status'] == "Emailed" else ""}>Emailed</option>
                                <option value="Not Interested"{" selected" if table[i]['Status'] == "Not Interested" else ""}>Not Interested</option>
                                <option value="Proposal Sent"{" selected" if table[i]['Status'] == "Proposal Sent" else ""}>Proposal Sent</option>
                                <option value="Meeting Scheduled"{" selected" if table[i]['Status'] == "Meeting Scheduled" else ""}>Meeting Scheduled</option>
                                <option value="In Discussion (Hot)"{" selected" if table[i]['Status'] == "In Discussion (Hot)" else ""}>In Discussion (Hot)</option>
                                <option value="In Discussion (Cold)"{" selected" if table[i]['Status'] == "In Discussion (Cold)" else ""}>In Discussion (Cold)</option>
                                <option value="MoU Signed"{" selected" if table[i]['Status'] == "MoU Signed" else ""}>MoU Signed</option>
                            </select>
                        </td>
                        <td><button id="edit_company_{table[i]['Company ID']}" class="edit_button" data-bs-toggle="modal" data-bs-target="#edit_company_modal_{table[i]['Company ID']}">Edit</button></td>
                        <td><a href="/company/{table[i]['Company ID']}"><button class="view_button">View</button></a></td>
                    </tr>
                    <div class="modal fade" id="edit_company_modal_{table[i]['Company ID']}" tabindex="-1" aria-hidden="true">
                        <div class="modal-dialog">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title">Edit {table[i]['Company']}</h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body">
                                    <div class="row">
                                        <div class="col-md-3">
                                            <label for="edit_company_name_{table[i]['Company ID']}">Name</label>
                                        </div>
                                        <div class="col-md-9">
                                            <input id="edit_company_name_{table[i]['Company ID']}" type="text" value="{table[i]['Company']}">
                                        </div>
                                        <div class="my-2"></div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-3">
                                            <label for="edit_company_state_{table[i]['Company ID']}">State</label>
                                        </div>
                                        <div class="col-md-9">
                                            <select id="edit_company_state_{table[i]['Company ID']}">
                                                <option value="Dubai Marina"{" selected" if table[i]['State'] == "Dubai Marina" else ""}>Dubai Marina</option>
                                                <option value="Mumbai"{" selected" if table[i]['State'] == "Mumbai" else ""}>Mumbai</option>
                                                <option value="Bengaluru"{" selected" if table[i]['State'] == "Bengaluru" else ""}>Bengaluru</option>
                                                <option value="Pune"{" selected" if table[i]['State'] == "Pune" else ""}>Pune</option>
                                                <option value="Morelia"{" selected" if table[i]['State'] == "Morelia" else ""}>Morelia</option>
                                                <option value="Kolkata"{" selected" if table[i]['State'] == "Kolkata" else ""}>Kolkata</option>
                                                <option value="Lille"{" selected" if table[i]['State'] == "Lille" else ""}>Lille</option>
                                                <option value="Delhi"{" selected" if table[i]['State'] == "Delhi" else ""}>Delhi</option>
                                                <option value="London"{" selected" if table[i]['State'] == "London" else ""}>London</option>
                                                <option value="Mooresville"{" selected" if table[i]['State'] == "Mooresville" else ""}>Mooresville</option>
                                                <option value="Seattle"{" selected" if table[i]['State'] == "Seattle" else ""}>Seattle</option>
                                                <option value="Stockholm"{" selected" if table[i]['State'] == "Stockholm" else ""}>Stockholm</option>
                                                <option value="Minneapolis"{" selected" if table[i]['State'] == "Minneapolis" else ""}>Minneapolis</option>
                                                <option value="Chennai"{" selected" if table[i]['State'] == "Chennai" else ""}>Chennai</option>
                                                <option value="Gurgaon"{" selected" if table[i]['State'] == "Gurgaon" else ""}>Gurgaon</option>
                                                <option value="Noida"{" selected" if table[i]['State'] == "Noida" else ""}>Noida</option>
                                                <option value="Abu Dhabi"{" selected" if table[i]['State'] == "Abu Dhabi" else ""}>Abu Dhabi</option>
                                                <option value="Howrah"{" selected" if table[i]['State'] == "Howrah" else ""}>Howrah</option>
                                                <option value="New Delhi"{" selected" if table[i]['State'] == "New Delhi" else ""}>New Delhi</option>
                                                <option value="Gurugram"{" selected" if table[i]['State'] == "Gurugram" else ""}>Gurugram</option>
                                                <option value="Fremont"{" selected" if table[i]['State'] == "Fremont" else ""}>Fremont</option>
                                                <option value="Dubai"{" selected" if table[i]['State'] == "Dubai" else ""}>Dubai</option>
                                                <option value="Jaipur"{" selected" if table[i]['State'] == "Jaipur" else ""}>Jaipur</option>
                                                <option value="Goa"{" selected" if table[i]['State'] == "Goa" else ""}>Goa</option>
                                                <option value="Ahmedabad"{" selected" if table[i]['State'] == "Ahmedabad" else ""}>Ahmedabad</option>
                                                <option value="Kochi"{" selected" if table[i]['State'] == "Kochi" else ""}>Kochi</option>
                                                <option value="Visakhapatnam"{" selected" if table[i]['State'] == "Visakhapatnam" else ""}>Visakhapatnam</option>
                                                <option value="Hyderabad"{" selected" if table[i]['State'] == "Hyderabad" else ""}>Hyderabad</option>
                                                <option value="Coimbatore"{" selected" if table[i]['State'] == "Coimbatore" else ""}>Coimbatore</option>
                                                <option value="Delhi"{" selected" if table[i]['State'] == "Delhi" else ""}>Delhi</option>
                                                <option value="Boca Raton"{" selected" if table[i]['State'] == "Boca Raton" else ""}>Boca Raton</option>
                                                <option value="Tiruppur"{" selected" if table[i]['State'] == "Tiruppur" else ""}>Tiruppur</option>
                                                <option value="Gandhi Nagar"{" selected" if table[i]['State'] == "Gandhi Nagar" else ""}>Gandhi Nagar</option>
                                                <option value="Raipur"{" selected" if table[i]['State'] == "Raipur" else ""}>Raipur</option>
                                                <option value="Alappuzha"{" selected" if table[i]['State'] == "Alappuzha" else ""}>Alappuzha</option>
                                                <option value="Bhagalpur"{" selected" if table[i]['State'] == "Bhagalpur" else ""}>Bhagalpur</option>
                                                <option value="Hyderabad"{" selected" if table[i]['State'] == "Hyderabad" else ""}>Hyderabad</option>
                                                <option value="Manama"{" selected" if table[i]['State'] == "Manama" else ""}>Manama</option>
                                                <option value="Riyadh"{" selected" if table[i]['State'] == "Riyadh" else ""}>Riyadh</option>
                                                <option value="San Francisco"{" selected" if table[i]['State'] == "San Francisco" else ""}>San Francisco</option>
                                                <option value="Delft"{" selected" if table[i]['State'] == "Delft" else ""}>Delft</option>
                                                <option value="Sambalpur"{" selected" if table[i]['State'] == "Sambalpur" else ""}>Sambalpur</option>
                                                <option value="Shahjahanpur"{" selected" if table[i]['State'] == "Shahjahanpur" else ""}>Shahjahanpur</option>
                                                <option value="Navi Mumbai"{" selected" if table[i]['State'] == "Navi Mumbai" else ""}>Navi Mumbai</option>
                                                <option value="Faridabad"{" selected" if table[i]['State'] == "Faridabad" else ""}>Faridabad</option>
                                            </select>
                                        </div>
                                        <div class="my-2"></div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-3">
                                            <label for="edit_company_sector_{table[i]['Company ID']}">Sector</label>
                                        </div>
                                        <div class="col-md-9">
                                            <select id="edit_company_sector_{table[i]['Company ID']}">
                                                <option value="Information Technology"{" selected" if table[i]['Sector'] == "Information Technology" else ""}>Information Technology</option>
                                                <option value="Healthcare"{" selected" if table[i]['Sector'] == "Healthcare" else ""}>Healthcare</option>
                                                <option value="Finance"{" selected" if table[i]['Sector'] == "Finance" else ""}>Finance</option>
                                                <option value="Education"{" selected" if table[i]['Sector'] == "Education" else ""}>Education</option>
                                                <option value="Manufacturing"{" selected" if table[i]['Sector'] == "Manufacturing" else ""}>Manufacturing</option>
                                                <option value="Retail"{" selected" if table[i]['Sector'] == "Retail" else ""}>Retail</option>
                                                <option value="Telecommunications"{" selected" if table[i]['Sector'] == "Telecommunications" else ""}>Telecommunications</option>
                                                <option value="Hospitality"{" selected" if table[i]['Sector'] == "Hospitality" else ""}>Hospitality</option>
                                                <option value="Energy"{" selected" if table[i]['Sector'] == "Energy" else ""}>Energy</option>
                                                <option value="Transportation"{" selected" if table[i]['Sector'] == "Transportation" else ""}>Transportation</option>
                                                <option value="Entertainment"{" selected" if table[i]['Sector'] == "Entertainment" else ""}>Entertainment</option>
                                                <option value="Agriculture"{" selected" if table[i]['Sector'] == "Agriculture" else ""}>Agriculture</option>
                                                <option value="Construction"{" selected" if table[i]['Sector'] == "Construction" else ""}>Construction</option>
                                                <option value="Pharmaceuticals"{" selected" if table[i]['Sector'] == "Pharmaceuticals" else ""}>Pharmaceuticals</option>
                                                <option value="Automotive"{" selected" if table[i]['Sector'] == "Automotive" else ""}>Automotive</option>
                                                <option value="Media"{" selected" if table[i]['Sector'] == "Media" else ""}>Media</option>
                                                <option value="Real Estate"{" selected" if table[i]['Sector'] == "Real Estate" else ""}>Real Estate</option>
                                                <option value="Aerospace"{" selected" if table[i]['Sector'] == "Aerospace" else ""}>Aerospace</option>
                                                <option value="Environmental"{" selected" if table[i]['Sector'] == "Environmental" else ""}>Environmental</option>
                                                <option value="Government"{" selected" if table[i]['Sector'] == "Government" else ""}>Government</option>
                                            </select>
                                        </div>
                                        <div class="my-2"></div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-3">
                                            <label for="edit_company_employees_{table[i]['Company ID']}">Employees</label>
                                        </div>
                                        <div class="col-md-9">
                                            <select id="edit_company_employees_{table[i]['Company ID']}">
                                                <option value="1k-5k"{" selected" if table[i]['Employees'] == "1k-5k" else ""}>1k-5k</option>
                                                <option value="5k-10k"{" selected" if table[i]['Employees'] == "5k-10k" else ""}>5k-10k</option>
                                                <option value="10k-50k"{" selected" if table[i]['Employees'] == "10k-50k" else ""}>10k-50k</option>
                                                <option value="1 Lakh+"{" selected" if table[i]['Employees'] == "1 Lakh+" else ""}>1 Lakh+</option>
                                            </select>
                                        </div>
                                        <div class="my-2"></div>
                                    </div>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" onclick="company_change({table[i]['Company ID']})" class="view_button" data-bs-dismiss="modal">Save</button>
                                </div>
                            </div>
                        </div>
                    </div>"""
                table_html = f"""<table class="table table-responsive">
                    <tr>
                        <th>S.No.</th>
                        <th>Company</th>
                        <th>State</th>
                        <th>Sector</th>
                        <th>Status</th>
                        <th>Employees</th>
                        <th>Edit</th>
                        <th>View</th>
                    </tr>
                    {rows_html}
                </table>"""
            else:
                table_html = "None"
            return render_template("companies.html", table_html = table_html)
        except Exception as e:
            traceback.print_exc()
            return render_template("error.html", error = e)

@app.route('/contacts')
def contacts():
    if 'login_email' not in session or 'login_pwd' not in session:
        return redirect(url_for("login"))
    elif session['access_level'] != "admin" and session['access_level'] != "sales":
        abort(403)
    else:
        try:
            table = list(contacts_col.find())
            rows_html = ""
            if len(table) > 0:
                for i in range(len(table)):
                    rows_html += f"""<tr>
                        <td>{table[i]['Contact ID']}</td>
                        <td>{table[i]['Name']}</td>
                        <td>{table[i]['Designation']}</td>
                        <td>{table[i]['Company']}</td>
                        <td>{table[i]['Email']}</td>
                        <td>{table[i]['Mobile']}</td>
                        <td><a href="/contact/{table[i]['Contact ID']}/communication"><button class="view_button">Communication</button></a></td>
                        <td><a href="https://secure.helpscout.net/customers/{table[i]['HelpScout ID']}" target="_blank"><button id="hs_url_{table[i]['Contact ID']}" class="edit_button">Start</button></a></td>
                    </tr>"""
                table_html = f"""<table class="table table-responsive">
                    <tr>
                        <th>S.No.</th>
                        <th>Name</th>
                        <th>Designation</th>
                        <th>Company</th>
                        <th>Email</th>
                        <th>Mobile</th>
                        <th>Communication</th>
                        <th>Start</th>
                    </tr>
                    {rows_html}
                </table>"""
            else:
                table_html = "None"
            return render_template("contacts.html", table_html = table_html)
        except Exception as e:
            traceback.print_exc()
            return render_template("error.html", error = e)

@app.route('/process-status-change', methods = ['POST'])
def process_status_change():
    try:
        company_id = int(request.form['company_id'])
        new_status = request.form['new_status']
        companies_col.update_one({'Company ID': company_id}, {"$set": {'Status': new_status}})
        return "Status Change Processed Successfully"
    except Exception as e:
        traceback.print_exc()
        return render_template("error.html", error = e)

@app.route('/company/<id>')
def view_company(id):
    if 'login_email' not in session or 'login_pwd' not in session:
        return redirect(url_for("login"))
    elif session['access_level'] != "admin" and session['access_level'] != "sales":
        abort(403)
    else:
        try:
            id = int(id)
            company_row = companies_col.find_one({'Company ID': id})
            company_options_html = ""
            for company in list(companies_col.find()):
                company_options_html += f'<option value="{company["Company"]}_{company["Company ID"]}"{" selected" if company["Company"] == company_row["Company"] else ""}>{company["Company"]}</option>'
            status = f"""<select id="status_{id}" onchange="status_change({company_row['Company ID']}, this.value)">
                <option value="Prospect"{" selected" if company_row['Status'] == "Prospect" else ""}>Prospect</option>
                <option value="Called"{" selected" if company_row['Status'] == "Called" else ""}>Called</option>
                <option value="Emailed"{" selected" if company_row['Status'] == "Emailed" else ""}>Emailed</option>
                <option value="Not Interested"{" selected" if company_row['Status'] == "Not Interested" else ""}>Not Interested</option>
                <option value="Proposal Sent"{" selected" if company_row['Status'] == "Proposal Sent" else ""}>Proposal Sent</option>
                <option value="Meeting Scheduled"{" selected" if company_row['Status'] == "Meeting Scheduled" else ""}>Meeting Scheduled</option>
                <option value="In Discussion (Hot)"{" selected" if company_row['Status'] == "In Discussion (Hot)" else ""}>In Discussion (Hot)</option>
                <option value="In Discussion (Cold)"{" selected" if company_row['Status'] == "In Discussion (Cold)" else ""}>In Discussion (Cold)</option>
                <option value="MoU Signed"{" selected" if company_row['Status'] == "MoU Signed" else ""}>MoU Signed</option>
            </select>"""
            contacts = list(contacts_col.find({'Company ID': id}))
            meetings = list(meetings_col.find({'Company ID': id}))
            reminders = list(reminders_col.find({'Company ID': id, 'Show': True}))
            company_contact_options_html = ""
            contacts_html = ""
            meetings_html = ""
            reminders_html = ""
            if len(contacts) > 0:
                for contact in contacts:
                    company_contact_options_html += f'<option value="{contact["Name"]}_{contact["Contact ID"]}">{contact["Name"]}</option>'
                    contacts_html += f"""<tr>
                        <td>{contact['Name']}</td>
                        <td>{contact['Designation']}</td>
                        <td>{contact['Email']}</td>
                        <td>{contact['Mobile']}</td>
                        <td><button id="edit_contact_{contact['Contact ID']}" class="edit_button" data-bs-toggle="modal" data-bs-target="#edit_contact_modal_{contact['Contact ID']}">Edit</button></td>
                        <td><a href="/contact/{contact['Contact ID']}/communication"><button class="view_button">Communication</button></a></td>
                        <td><a href="https://secure.helpscout.net/customers/{contact['HelpScout ID']}" target="_blank"><button id="hs_url_{contact['Contact ID']}" class="edit_button">Start</button></a></td>
                    </tr>
                    <div class="modal fade" id="edit_contact_modal_{contact['Contact ID']}" tabindex="-1" aria-hidden="true">
                        <div class="modal-dialog">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title">Edit {contact['Name']} from {contact['Company']}</h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body">
                                    <div class="row">
                                        <div class="col-md-3">
                                            <label for="edit_contact_company_{contact['Contact ID']}">Company</label>
                                        </div>
                                        <div class="col-md-9">
                                            <select id="edit_contact_company_{contact['Contact ID']}" disabled>
                                                {company_options_html}
                                            </select>
                                        </div>
                                        <div class="my-2"></div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-3">
                                            <label for="edit_contact_name_{contact['Contact ID']}">Name</label>
                                        </div>
                                        <div class="col-md-9">
                                            <input id="edit_contact_name_{contact['Contact ID']}" type="text" value="{contact['Name']}">
                                        </div>
                                        <div class="my-2"></div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-3">
                                            <label for="edit_contact_designation_{contact['Contact ID']}">Designation</label>
                                        </div>
                                        <div class="col-md-9">
                                            <input id="edit_contact_designation_{contact['Contact ID']}" type="text" value="{contact['Designation']}">
                                        </div>
                                        <div class="my-2"></div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-3">
                                            <label for="edit_contact_email_{contact['Contact ID']}">Email</label>
                                        </div>
                                        <div class="col-md-9">
                                            <input id="edit_contact_email_{contact['Contact ID']}" type="email" value="{contact['Email']}" disabled>
                                        </div>
                                        <div class="my-2"></div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-3">
                                            <label for="edit_contact_mobile_{contact['Contact ID']}">Mobile</label>
                                        </div>
                                        <div class="col-md-9">
                                            <input id="edit_contact_mobile_{contact['Contact ID']}" type="tel" value="{contact['Mobile']}">
                                        </div>
                                        <div class="my-2"></div>
                                    </div>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" onclick="contact_change({contact['Contact ID']})" class="view_button" data-bs-dismiss="modal">Save</button>
                                </div>
                            </div>
                        </div>
                    </div>"""
                contacts_table_html = f"""<table class="table table-responsive">
                    <tbody>
                        <tr>
                            <th>Name</th>
                            <th>Designation</th>
                            <th>Email</th>
                            <th>Mobile</th>
                            <th>Edit</th>
                            <th>Communication</th>
                            <th>Start</th>
                        </tr>
                        {contacts_html}
                    </tbody>
                </table>"""
            else:
                contacts_table_html = "None"
            if len(meetings) > 0:
                for meeting in meetings:
                    meetings_html += f"""<tr>
                        <td>{meeting['Type']}</td>
                        <td>{datetime.strptime(meeting['Start Date & Time'], "%Y-%m-%dT%H:%M").strftime("%d/%m/%Y %I:%M %p")}</td>
                        <td>{datetime.strptime(meeting['End Date & Time'], "%Y-%m-%dT%H:%M").strftime("%d/%m/%Y %I:%M %p")}</td>
                        <td>{meeting['Product(s)']}</td>
                        <td>{meeting['Agenda']}</td>
                        <td><button id="edit_meeting_{meeting['Meeting ID']}" class="edit_button" data-bs-toggle="modal" data-bs-target="#edit_meeting_modal_{meeting['Meeting ID']}">Edit</button></td>
                    </tr>
                    <div class="modal fade" id="edit_meeting_modal_{meeting['Meeting ID']}" tabindex="-1" aria-hidden="true">
                        <div class="modal-dialog">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title">Edit {meeting['Type']} Meeting from {meeting['Company']}</h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body">
                                    <div class="row">
                                        <div class="col-md-3">
                                            <label for="edit_meeting_company_{meeting['Meeting ID']}">Company</label>
                                        </div>
                                        <div class="col-md-9">
                                            <select id="edit_meeting_company_{meeting['Meeting ID']}" disabled>
                                                {company_options_html}
                                            </select>
                                        </div>
                                        <div class="my-2"></div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-3">
                                            <label for="edit_meeting_type_{meeting['Meeting ID']}">Type</label>
                                        </div>
                                        <div class="col-md-9">
                                            <select id="edit_meeting_type_{meeting['Meeting ID']}">
                                                <option value="Introduction"{" selected" if meeting['Type'] == "Introduction" else None}>Introduction</option>
                                                <option value="Demo"{" selected" if meeting['Type'] == "Demo" else None}>Demo</option>
                                                <option value="Go-Live"{" selected" if meeting['Type'] == "Go-Live" else None}>Go-Live</option>
                                            </select>
                                        </div>
                                        <div class="my-2"></div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-3">
                                            <label for="edit_meeting_start_{meeting['Meeting ID']}">Start Date & Time</label>
                                        </div>
                                        <div class="col-md-9">
                                            <input type="datetime-local" id="edit_meeting_start_{meeting['Meeting ID']}" value="{meeting['Start Date & Time']}">
                                        </div>
                                        <div class="my-2"></div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-3">
                                            <label for="edit_meeting_end_{meeting['Meeting ID']}">End Date & Time</label>
                                        </div>
                                        <div class="col-md-9">
                                            <input type="datetime-local" id="edit_meeting_end_{meeting['Meeting ID']}" value={meeting['End Date & Time']}>
                                        </div>
                                        <div class="my-2"></div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-3">
                                            <label for="edit_meeting_prods_{meeting['Meeting ID']}">Product(s) Pitched</label>
                                        </div>
                                        <div class="col-md-9">
                                            <input id="ygroo_training" class="edit_meeting_prods_{meeting['Meeting ID']}" type="checkbox" value="YGROO TRAINING"{" checked" if "YGROO TRAINING" in meeting['Product(s)'].split(", ") else ""}>
                                            <label for="ygroo_training">YGROO TRAINING</label>
                                            <br>
                                            <input id="ygroo_art" class="edit_meeting_prods_{meeting['Meeting ID']}" type="checkbox" value="YGROO ART"{" checked" if "YGROO ART" in meeting['Product(s)'].split(", ") else ""}>
                                            <label for="ygroo_art">YGROO ART</label>
                                            <br>
                                            <input id="ygroo_pro" class="edit_meeting_prods_{meeting['Meeting ID']}" type="checkbox" value="YGROO PRO"{" checked" if "YGROO PRO" in meeting['Product(s)'].split(", ") else ""}>
                                            <label for="ygroo_pro">YGROO PRO</label>
                                            <br>
                                            <input id="ygroo_studio" class="edit_meeting_prods_{meeting['Meeting ID']}" type="checkbox" value="YGROO STUDIO"{" checked" if "YGROO STUDIO" in meeting['Product(s)'].split(", ") else ""}>
                                            <label for="ygroo_studio">YGROO STUDIO</label>
                                            <br>
                                            <input id="ygroo_care" class="edit_meeting_prods_{meeting['Meeting ID']}" type="checkbox" value="YGROO CARE"{" checked" if "YGROO CARE" in meeting['Product(s)'].split(", ") else ""}>
                                            <label for="ygroo_care">YGROO CARE</label>
                                            <br>
                                            <input id="ygroo_careers" class="edit_meeting_prods_{meeting['Meeting ID']}" type="checkbox" value="YGROO CAREERS"{" checked" if "YGROO CAREERS" in meeting['Product(s)'].split(", ") else ""}>
                                            <label for="ygroo_careers">YGROO CAREERS</label>
                                        </div>
                                        <div class="my-2"></div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-3">
                                            <label for="edit_meeting_agenda_{meeting['Meeting ID']}">Agenda</label>
                                        </div>
                                        <div class="col-md-9">
                                            <textarea id="edit_meeting_agenda_{meeting['Meeting ID']}" rows="5">{meeting['Agenda']}</textarea>
                                        </div>
                                        <div class="my-2"></div>
                                    </div>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" onclick="meeting_change({meeting['Meeting ID']})" class="view_button" data-bs-dismiss="modal">Save</button>
                                </div>
                            </div>
                        </div>
                    </div>"""
                meetings_table_html = f"""<table class="table table-responsive">
                    <tbody>
                        <tr>
                            <th>Type</th>
                            <th>Start Date & Time</th>
                            <th>End Date & Time</th>
                            <th>Product(s) Pitched</th>
                            <th>Agenda</th>
                            <th>Edit</th>
                        </tr>
                        {meetings_html}
                    </tbody>
                </table>"""
            else:
                meetings_table_html = "None"
            if len(reminders) > 0:
                for reminder in reminders:
                    reminders_html += f"""<tr>
                        <td><input id="reminder_check_{reminder['Reminder ID']}" onchange="check_reminder({reminder['Reminder ID']})" type="checkbox"></td>
                        <td>{reminder['Reminder']}</td>
                        <td>{reminder['Contact']}</td>
                        <td>{reminder['Recurrence']}</td>
                        <td>{datetime.strptime(reminder['Due Date & Time'], "%Y-%m-%dT%H:%M").strftime("%d/%m/%Y %I:%M %p")}</td>
                    </tr>"""
                reminders_table_html = f"""<table class="table table-responsive">
                    <tbody>
                        <tr>
                            <th></th>
                            <th>Note</th>
                            <th>Contact</th>
                            <th>Recurrence</th>
                            <th>Due Date & Time</th>
                        </tr>
                        {reminders_html}
                    </tbody>
                </table>"""
            else:
                reminders_table_html = "None"
            return render_template("view_company.html", id = id, name = company_row['Company'], state = company_row['State'], sector = company_row['Sector'], employees = company_row['Employees'], status = status, contacts_html = contacts_table_html, meetings_html = meetings_table_html, reminders_html = reminders_table_html, company_options_html = company_options_html, company_contact_options_html = company_contact_options_html)
        except Exception as e:
            traceback.print_exc()
            return render_template("error.html", error = e)

@app.route('/process-company-change', methods = ['POST'])
def process_company_change():
    try:
        companies_col.update_one({'Company ID': int(request.form['id'])}, {"$set": {"Company": request.form['name'], "State": request.form['state'], "Sector": request.form['sector'], "Employees": request.form['employees']}})
        contacts_col.update_many({'Company ID': int(request.form['id'])}, {"$set": {"Company": request.form['name']}})
        meetings_col.update_many({'Company ID': int(request.form['id'])}, {"$set": {"Company": request.form['name']}})
        reminders_col.update_many({'Company ID': int(request.form['id'])}, {"$set": {"Company": request.form['name']}})
        log_col.update_many({'Company ID': int(request.form['id'])}, {"$set": {"Company": request.form['name']}})
        lists_contacts_col.update_many({'Company ID': int(request.form['id'])}, {"$set": {"Company": request.form['name']}})
        bearer_token = get_bearer_token()
        headers = {'Authorization': f"Bearer {bearer_token}"}
        for contact in contacts_col.find({'Company ID': int(request.form['id'])}):
            body = [{
                "op" : "replace",
                "path" : "/organization",
                "value" : f"{request.form['name']}"
            }]
            requests.patch(f"https://api.helpscout.net/v2/customers/{contact['HelpScout ID']}", headers = headers, json = body)
        return "Company Change Processed Successfully"
    except Exception as e:
        traceback.print_exc()
        return render_template("error.html", error = e)

@app.route('/process-contact-change', methods = ['POST'])
def process_contact_change():
    try:
        contacts_col.update_many({'Contact ID': int(request.form['id'])}, {"$set": {"Name": request.form['name'], "Designation": request.form['designation'], "Company ID": int(request.form['company_id']), "Company": request.form['company_name'], "Email": request.form['email'], "Mobile": request.form['mobile']}})
        reminders_col.update_many({'Contact ID': int(request.form['id'])}, {"$set": {"Cotact": request.form['name']}})
        log_col.update_many({'Contact ID': int(request.form['id'])}, {"$set": {"Contact": request.form['name'], "Designation": request.form['designation'], "Company ID": int(request.form['company_id']), "Company": request.form['company_name'], "Email": request.form['email'], "Mobile": request.form['mobile']}})
        lists_contacts_col.update_many({'Contact ID': int(request.form['id'])}, {"$set": {"Contact": request.form['name'], "Designation": request.form['designation'], "Company ID": int(request.form['company_id']), "Company": request.form['company_name'], "Email": request.form['email'], "Mobile": request.form['mobile']}})
        hs_id = contacts_col.find_one({'Contact ID': int(request.form['id'])})['HelpScout ID']
        bearer_token = get_bearer_token()
        headers = {'Authorization': f"Bearer {bearer_token}"}
        name = re.sub(r'\.(?!\s)', '. ', request.form['name'])
        names = name.split()
        names = [item.title() for item in names]
        if len(names) > 1:
            first_name = " ".join(names[:-1])
            last_name = names[-1]
            body = {
                "firstName": first_name,
                "lastName": last_name,
                "organization": request.form['company_name'],
                "jobTitle": request.form['designation'],
                "phone": str(request.form['mobile'])
            }
        else:
            first_name = names[0]
            body = {
                "firstName": first_name,
                "organization": request.form['company_name'],
                "jobTitle": request.form['designation'],
                "phone": str(request.form['mobile'])
            }
        requests.put(f"https://api.helpscout.net/v2/customers/{hs_id}", headers = headers, json = body)
        response = requests.get(f"https://api.helpscout.net/v2/customers/{hs_id}/phones", headers = headers)
        mobile_id = response.json()['_embedded']['phones'][0]['id']
        requests.put(f"https://api.helpscout.net/v2/customers/{hs_id}/phones/{mobile_id}", headers = headers, json = {
            "type": "mobile",
            "value": str(request.form['mobile'])
        })
        response = requests.get(f"https://api.helpscout.net/v2/customers/{hs_id}/emails", headers = headers)
        email_id = response.json()['_embedded']['emails'][0]['id']
        requests.put(f"https://api.helpscout.net/v2/customers/{hs_id}/emails/{email_id}", headers = headers, json = {
            "type": "work",
            "value": request.form['email']
        })
        return "Contact Change Processed Successfully"
    except Exception as e:
        traceback.print_exc()
        return render_template("error.html", error = e)

@app.route('/contact/<id>/communication')
def get_contact_comms(id):
    if 'login_email' not in session or 'login_pwd' not in session:
        return redirect(url_for("login"))
    elif session['access_level'] != "admin" and session['access_level'] != "sales":
        abort(403)
    else:
        try:
            id = int(id)
            current_dt = datetime.utcnow()
            current_dt = current_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            contact = contacts_col.find_one({'Contact ID': id})
            active_response = get_comms(299086, "email", "modifiedAt", "desc", "active", contact['Email'])["_embedded"]["conversations"]
            closed_response = get_comms(299086, "email", "modifiedAt", "desc", "closed", contact['Email'])["_embedded"]["conversations"]
            active_response_rows_html = ""
            closed_response_rows_html = ""
            if len(active_response) > 0:
                for comm in active_response:
                    if "time" in comm["customerWaitingSince"]:
                        ts_1 = datetime.strptime(comm["customerWaitingSince"]["time"], '%Y-%m-%dT%H:%M:%SZ')
                        ts_2 = datetime.strptime(current_dt, '%Y-%m-%dT%H:%M:%SZ')
                        wait = ts_2 - ts_1
                        active_response_rows_html += f"""<tr>
                            <td>{comm["subject"]}</td>
                            <td>{comm["preview"]}...</td>
                            <td>{comm["threads"]}</td>
                            <td>{wait.days} days</td>
                            <td><a href="https://secure.helpscout.net/conversation/{comm["_links"]["self"]["href"].split("/")[-1]}" target="_blank"">View</a></td>
                        </tr>"""
                    else:
                        active_response_rows_html += f"""<tr>
                            <td>{comm["subject"]}</td>
                            <td>{comm["preview"]}...</td>
                            <td>{comm["threads"]}</td>
                            <td>NA</td>
                            <td><a href="https://secure.helpscout.net/conversation/{comm["_links"]["self"]["href"].split("/")[-1]}" target="_blank"">View</a></td>
                        </tr>"""
                active_response_html = f"""<table class="table table-responsive">
                    <tbody>
                        <tr>
                            <th>Subject</th>
                            <th>Preview</th>
                            <th>Threads</th>
                            <th>Waiting Since</th>
                            <th>View</th>
                        </tr>
                        {active_response_rows_html}
                    </tbody>
                </table>"""
            else:
                active_response_html = "None"
            if len(closed_response) > 0:
                for comm in closed_response:
                    closed_response_rows_html += f"""<tr>
                        <td>{comm["subject"]}</td>
                        <td>{comm["preview"]}...</td>
                        <td>{comm["threads"]}</td>
                        <td><a href="https://secure.helpscout.net/conversation/{comm["_links"]["self"]["href"].split("/")[-1]}" target="_blank">View</a></td>
                    </tr>"""
                closed_response_html = f"""<table class="table table-responsive">
                    <tbody>
                        <tr>
                            <th>Subject</th>
                            <th>Preview</th>
                            <th>Threads</th>
                            <th>View</th>
                        </tr>
                        {closed_response_rows_html}
                    </tbody>
                </table>"""
            else:
                closed_response_html = "None"
            phone_comms_list = list(phone_comms_col.find({'Contact ID': id}))
            if len(phone_comms_list) > 0:
                phone_comms_rows_html = ""
                for phone_comm in phone_comms_list:
                    phone_comms_rows_html += f"""<tr>
                        <td>{datetime.strptime(phone_comm['Start Date & Time'], "%Y-%m-%dT%H:%M").strftime("%d/%m/%Y %I:%M %p")}</td>
                        <td>{datetime.strptime(phone_comm['End Date & Time'], "%Y-%m-%dT%H:%M").strftime("%d/%m/%Y %I:%M %p")}</td>
                        <td>{phone_comm['Product(s)']}</td>
                        <td>{phone_comm['Notes']}</td>
                    </tr>"""
                phone_comms_html = f"""<table class="table table-responsive">
                    <tbody>
                        <tr>
                            <th>Start Date & Time</th>
                            <th>End Date & Time</th>
                            <th>Product(s) Pitched</th>
                            <th>Notes</th>
                        </tr>
                        {phone_comms_rows_html}
                    </tbody>
                </table>"""
            else:
                phone_comms_html = "None"
            return render_template("view_contact_communication.html", id = id, name = contact['Name'], designation = contact['Designation'], email = contact['Email'], mobile = contact['Mobile'], company = contact['Company'], active_response_html = active_response_html, closed_response_html = closed_response_html, phone_comms_html = phone_comms_html)
        except Exception as e:
            traceback.print_exc()
            return render_template("error.html", error = e)

def get_bearer_token():
    try:
        bearer_token = bearer_col.find_one({'Key': 'Bearer Token'})['Value']
        bearer_expiry = bearer_col.find_one({'Key': 'Bearer Expiry'})['Value']
        bearer_expiry_dt = datetime.strptime(bearer_expiry, "%Y-%m-%d %H:%M:%S").replace(tzinfo = timezone.utc)
        current_dt = datetime.now(timezone.utc)
        if current_dt >= bearer_expiry_dt:
            url = f"https://api.helpscout.net/v2/oauth2/token?grant_type=client_credentials&client_id={os.getenv('client_id')}&client_secret={os.getenv('client_secret')}"
            response = requests.post(url)
            bearer_token_new = response.json()['access_token']
            response_dt = response.headers['Date']
            response_dt = datetime.strptime(response_dt, "%a, %d %b %Y %H:%M:%S %Z")
            bearer_expiry_new = response_dt + timedelta(days = 2)
            bearer_expiry_new = bearer_expiry_new.strftime("%Y-%m-%d %H:%M:%S")
            render_url = "https://api.render.com/v1/services/srv-cil9vtp5rnuvtguq88t0/env-vars"
            headers = {
                "accept": "application/json",
                "content-type": "application/json"
            }
            payload = [
                {
                    "key": "bearer_token",
                    "value": bearer_token_new
                },
                {
                    "key": "bearer_expiry",
                    "value": bearer_expiry_new
                }
            ]
            requests.put(render_url, json = payload, headers = headers)
            bearer_col.update_one({'Key': 'Bearer Token'}, {"$set": {"Value": bearer_token_new}})
            bearer_col.update_one({'Key': 'Bearer Expiry'}, {"$set": {"Value": bearer_expiry_new}})
            return bearer_token_new
        else:
            return bearer_token
    except Exception as e:
        traceback.print_exc()
        return render_template("error.html", error = e)

def get_comms(mailbox, type, sort_by, sort_order, status, email):
    try:
        if status == "all":
            url = f'https://api.helpscout.net/v2/conversations?mailbox={mailbox}&type={type}&sortField={sort_by}&sortOrder={sort_order}&query=(email:"{email}")'
        else:
            url = f'https://api.helpscout.net/v2/conversations?mailbox={mailbox}&type={type}&status={status}&sortField={sort_by}&sortOrder={sort_order}&query=(email:"{email}")'
        bearer_token = get_bearer_token()
        headers = {'Authorization': f"Bearer {bearer_token}"}
        response = requests.get(url, headers = headers)
        data = response.json()
        return data
    except Exception as e:
        traceback.print_exc()
        return render_template("error.html", error = e)

@app.route('/add-company', methods = ['POST'])
def add_company():
    try:
        name = request.form['name']
        state = request.form['state']
        sector = request.form['sector']
        employees = request.form['employees']
        status = request.form['status']
        matches = list(companies_col.find({
            'Company': {
                '$regex': f'^{re.escape(name)}$',
                '$options': 'i'
            }
        }))
        if len(matches) > 0:
            return "Company Already Added"
        else:
            companies_col.insert_one({
                "Company ID": companies_col.count_documents({}) + 1,
                "Company": name,
                "State": state,
                "Sector": sector,
                "Employees": employees,
                "Status": status
            })
            return "Company Added Successfully"
    except Exception as e:
        traceback.print_exc()
        return render_template("error.html", error = e)

@app.route('/add-contact', methods = ['POST'])
def add_contact():
    try:
        name = request.form['name']
        designation = request.form['designation']
        company_id = int(request.form['company_id'])
        company = request.form['company_name']
        email = request.form['email']
        mobile = request.form['mobile']
        matches = list(companies_col.find({
            '$or': [
                {'Name': {'$regex': f'^{re.escape(name)}$', '$options': 'i'},
                {'Email': {'$regex': f'^{re.escape(email)}$', '$options': 'i'}
            ]
        }))
        if len(matches) > 0:
            return "Contact Already Added"
        else:
            hs_id = create_contact(name, mobile, email, designation, company)
            contacts_col.insert_one({
                "Contact ID": contacts_col.count_documents({}) + 1,
                "Name": name,
                "Designation": designation,
                "Company ID": company_id,
                "Company": company,
                "Email": email,
                "Mobile": mobile,
                "HelpScout ID": hs_id
            })
            return "Contact Added Successfully"
    except Exception as e:
        traceback.print_exc()
        return render_template("error.html", error = e)

@app.route('/add-phone-comm/<id>', methods = ['POST'])
def add_phone_comm(id):
    try:
        id = int(id)
        name = contacts_col.find_one({"Contact ID": id})['Name']
        start_dt = request.form['start_dt']
        end_dt = request.form['end_dt']
        prods = request.form['prods']
        notes = request.form['notes']
        phone_comms_col.insert_one({
            "Comm ID": phone_comms_col.count_documents({}) + 1,
            "Contact ID": id,
            "Contact": name,
            "Start Date & Time": start_dt,
            "End Date & Time": end_dt,
            "Product(s)": prods,
            "Notes": notes
        })
        return "Phone Communication Added Successfully"
    except Exception as e:
        traceback.print_exc()
        return render_template("error.html", error = e)

@app.route('/meetings')
def meetings():
    if 'login_email' not in session or 'login_pwd' not in session:
        return redirect(url_for("login"))
    elif session['access_level'] != "admin" and session['access_level'] != "sales":
        abort(403)
    else:
        try:
            table = list(meetings_col.find())
            rows_html = ""
            if len(table) > 0:
                for i in range(len(table)):
                    rows_html += f"""<tr>
                        <td>{table[i]['Meeting ID']}</td>
                        <td>{table[i]['Type']}</td>
                        <td>{table[i]['Company']}</td>
                        <td>{datetime.strptime(table[i]['Start Date & Time'], "%Y-%m-%dT%H:%M").strftime("%d/%m/%Y %I:%M %p")}</td>
                        <td>{datetime.strptime(table[i]['End Date & Time'], "%Y-%m-%dT%H:%M").strftime("%d/%m/%Y %I:%M %p")}</td>
                        <td>{table[i]['Product(s)']}</td>
                        <td>{table[i]['Agenda']}</td>
                    </tr>"""
                table_html = f"""<table class="table table-responsive">
                    <tr>
                        <th>S.No.</th>
                        <th>Type</th>
                        <th>Company</th>
                        <th>Start Date & Time</th>
                        <th>End Date & Time</th>
                        <th>Product(s) Pitched</th>
                        <th>Agenda</th>
                    </tr>
                    {rows_html}
                </table>"""
            else:
                table_html = "None"
            return render_template("meetings.html", table_html = table_html)
        except Exception as e:
            traceback.print_exc()
            return render_template("error.html", error = e)

@app.route('/add-meeting', methods = ['POST'])
def add_meeting():
    try:
        meeting_type = request.form['meeting_type']
        company_id = int(request.form['company_id'])
        company = request.form['company_name']
        start_dt = request.form['start_dt']
        end_dt = request.form['end_dt']
        prods = request.form['prods']
        agenda = request.form['agenda']
        matches = list(companies_col.find({
            '$and': [
                {'Type': meeting_type},
                {'Company ID': company_id},
                {'Start Date & Time': start_dt},
                {'End Date & Time': end_dt}
            ]
        }))
        if len(matches) > 0:
            return "Meeting Already Added"
        else:
            meetings_col.insert_one({
                'Meeting ID': meetings_col.count_documents({}) + 1,
                'Type': meeting_type,
                'Company ID': company_id,
                'Company': company,
                'Start Date & Time': start_dt,
                'End Date & Time': end_dt,
                'Product(s)': prods,
                'Agenda': agenda
            })
            return "Meeting Added Successfully"
    except Exception as e:
        traceback.print_exc()
        return render_template("error.html", error = e)
    
@app.route('/process-meeting-change', methods = ['POST'])
def process_meeting_change():
    try:
        meetings_col.update_one({'Meeting ID'} == int(request.form['id']), {"$set": {"Type": request.form['meeting_type'], "Company ID": int(request.form['company_id']), "Company": request.form['company_name'], "Start Date & Time": request.form['start_dt'], "Due Date & Time": request.form['end_dt'], "Product(s)": request.form['prods'], "Agenda": request.form['agenda']}})
        return "Meeting Change Processed Successfully"
    except Exception as e:
        traceback.print_exc()
        return render_template("error.html", error = e)

def create_contact(name, mobile, email, designation, company):
    try:
        name = re.sub(r'\.(?!\s)', '. ', name)
        names = name.split()
        names = [item.title() for item in names]
        if len(names) > 1:
            first_name = " ".join(names[:-1])
            last_name = names[-1]
            body = {
                "firstName": first_name,
                "lastName": last_name,
                "organization": company,
                "jobTitle": designation,
                "phone": str(mobile),
                "emails": [{
                    "type": "work",
                    "value": email,
                }],
                "phones": [{
                    "type": "mobile",
                    "value": mobile,
                }]
            }
        else:
            first_name = names[0]
            body = {
                "firstName": first_name,
                "organization": company,
                "jobTitle": designation,
                "phone": str(mobile),
                "emails": [{
                    "type": "work",
                    "value": email,
                }],
                "phones": [{
                    "type": "mobile",
                    "value": mobile,
                }]
            }
        bearer_token = get_bearer_token()
        headers = {'Authorization': f"Bearer {bearer_token}"}
        response = requests.get(f'https://api.helpscout.net/v2/customers?query=(email:"{email}")', headers = headers)
        contacts_list = response.json()['_embedded']['customers']
        if len(contacts_list) == 0:
            response = requests.post("https://api.helpscout.net/v2/customers", headers = headers, json = body)
            data = response.headers
            return data['Resource-ID']
        else:
            hs_id = contacts_list[0]['id']
            response = requests.put(f"https://api.helpscout.net/v2/customers/{hs_id}", headers = headers, json = body)
            requests.post(f"https://api.helpscout.net/v2/customers/{hs_id}/phones", headers = headers, json = {
                "type": "mobile",
                "value": mobile
            })
            return hs_id
    except Exception as e:
        traceback.print_exc()
        return render_template("error.html", error = e)

@app.route('/reminders')
def reminders():
    if 'login_email' not in session or 'login_pwd' not in session:
        return redirect(url_for("login"))
    elif session['access_level'] != "admin" and session['access_level'] != "sales":
        abort(403)
    else:
        try:
            table = list(reminders_col.find({'Show': True}).sort('Due Date & Time'))
            rows_html = ""
            if len(table) > 0:
                for i in range(len(table)):
                    rows_html += f"""<tr>
                        <td><input id="reminder_check_{table[i]['Reminder ID']}" onchange="check_reminder({table[i]['Reminder ID']})" type="checkbox"></td>
                        <td>{table[i]['Reminder']}</td>
                        <td>{table[i]['Company']}</td>
                        <td>{table[i]['Contact']}</td>
                        <td>{table[i]['Recurrence']}</td>
                        <td>{datetime.strptime(table[i]['Due Date & Time'], "%Y-%m-%dT%H:%M").strftime("%d/%m/%Y %I:%M %p")}</td>
                    </tr>"""
                table_html = f"""<table class="table table-responsive">
                    <tr>
                        <th></th>
                        <th>Reminder</th>
                        <th>Company</th>
                        <th>Contact</th>
                        <th>Recurrence</th>
                        <th>Due Date & Time</th>
                    </tr>
                    {rows_html}
                </table>"""
            else:
                table_html = "None"
            return render_template("reminders.html", table_html = table_html)
        except Exception as e:
            traceback.print_exc()
            return render_template("error.html", error = e)

@app.route('/add-reminder', methods = ['POST'])
def add_reminder():
    try:
        reminder = request.form['reminder']
        recurrence = request.form['recurrence']
        company_id = int(request.form['company_id'])
        company = request.form['company_name']
        contact_id = int(request.form['contact_id'])
        contact = request.form['contact_name']
        start_dt = request.form['start_dt']
        end_dt = request.form['end_dt']
        start_date = datetime.strptime(start_dt, "%Y-%m-%dT%H:%M").date()
        end_date = datetime.strptime(end_dt, "%Y-%m-%dT%H:%M").date()
        start_time = datetime.strptime(start_dt, "%Y-%m-%dT%H:%M").time()
        end_time = datetime.strptime(end_dt, "%Y-%m-%dT%H:%M").time()
        if start_time > end_time:
            end_dt -= timedelta(days = 1)
        get_reminder_entries(reminder, start_date, end_date, recurrence, start_time, company_id, company, contact_id, contact)
        return "Reminder Added Successfully"
    except Exception as e:
        traceback.print_exc()
        return render_template("error.html", error = e)

def get_reminder_entries(reminder, start_date, end_date, recurrence, time, company_id, company, contact_id, contact):
    try:
        if recurrence == "One Time":
            freq = DAILY
        elif recurrence == 'Weekly':
            freq = WEEKLY
        elif recurrence == 'Monthly':
            freq = MONTHLY
        dates = list(rrule(freq, dtstart = start_date, until = end_date, interval = 1))
        for entry in dates:
            matches = list(reminders_col.find({
                '$and': [
                    {'Reminder': {'$regex': f'^{re.escape(reminder)}$', '$options': 'i'},
                    {'Due Date & Time': entry}
                ]
            }))
            if len(matches) == 0:
                due_dt = datetime.combine(entry, time)
                due_dt = due_dt.strftime("%Y-%m-%dT%H:%M")
                reminders_col.insert_one({
                    'Reminder ID': reminders_col.count_documents({}) + 1,
                    'Reminder': reminder,
                    'Company ID': company_id,
                    'Company': company,
                    'Contact ID': contact_id,
                    'Contact': contact,
                    'Recurrence': recurrence,
                    'Due Date & Time': due_dt,
                    'Show': True
                })
        return None
    except Exception as e:
        traceback.print_exc()
        return render_template("error.html", error = e)

@app.route('/check-reminder', methods = ['POST'])
def check_reminder():
    try:
        id = int(request.form['id'])
        reminders_col.update_one({'Reminder ID': id}, {"$set": {
            'Show': False
        }})
        return "Reminder Checked Successfully"
    except Exception as e:
        traceback.print_exc()
        return render_template("error.html", error = e)

@app.route('/contact-lists', methods = ['GET', 'POST'])
def contact_lists():
    if 'login_email' not in session or 'login_pwd' not in session:
        return redirect(url_for("login"))
    elif session['access_level'] != "admin" and session['access_level'] != "sales":
        abort(403)
    else:
        try:
            table = list(contacts_col.find())
            if len(table) != 0:
                rows_html = ""
                for i in range(len(table)):
                    rows_html += f"""<tr>
                        <td><input id="list_contact_{table[i]['Contact ID']}" type="checkbox" value="{table[i]['Contact ID']}"></td>
                        <td>{table[i]['Name']}</td>
                        <td>{table[i]['Designation']}</td>
                        <td>{table[i]['Company']}</td>
                        <td>{table[i]['Email']}</td>
                        <td>{table[i]['Mobile']}</td>
                    </tr>"""
                table_html = f"""<table class="table table-responsive">
                    <tr>
                        <th></th>
                        <th>Name</th>
                        <th>Designation</th>
                        <th>Company</th>
                        <th>Email</th>
                        <th>Mobile</th>
                    </tr>
                    {rows_html}
                </table>"""
            else:
                table_html = ""
            lists_table = list(contact_lists_col.find())
            if len(lists_table) != 0:    
                rows_lists_html = ""
                for i in range(len(lists_table)):
                    rows_lists_html += f"""<tr>
                        <td>{lists_table[i]['List ID']}</td>
                        <td>{lists_table[i]['Name']}</td>
                        <td><a href="/contact-list/{lists_table[i]['List ID']}"><button class="view_button">View</button></a></td>
                    </tr>"""
                table_lists_html = f"""<table class="table table-responsive">
                    <tr>
                        <th>S.No.</th>
                        <th>Name</th>
                        <th>View</th>
                    </tr>
                    {rows_lists_html}
                </table>"""
            else:
                table_lists_html = ""
            return render_template("contact_lists.html", list_contacts_html = table_html, lists_table_html = table_lists_html)
        except Exception as e:
            traceback.print_exc()
            return render_template("error.html", error = e)

@app.route('/add-list', methods = ['POST'])
def add_list():
    try:
        list_name = request.form['name']
        list_contacts = request.form.getlist('contacts[]')
        same_name_found = list(contact_lists_col.find({
            'List Name': {
                '$regex': f'^{re.escape(list_name)}$',
                '$options': 'i'  # 'i' option for case-insensitive matching
            }
        }))
        if len(same_name_found) > 0:
            return "List Already Added"
        else:
            contact_lists_col.insert_one({
                'List ID': contact_lists_col.count_documents({}) + 1,
                'Name': list_name
            })
            for contact in list_contacts:
                contact_row = contacts_col.find_one({'Contact ID': int(contact)})
                lists_contacts_col.insert_one({
                    'List ID': contact_lists_col.count_documents({}),
                    'Name': list_name,
                    'Contact ID': contact_row['Contact ID'],
                    'Contact': contact_row['Name'],
                    'Designation': contact_row['Designation'],
                    'Company ID': contact_row['Company ID'],
                    'Company': contact_row['Company'],
                    'Email': contact_row['Email'],
                    'Mobile': contact_row['Mobile'],
                    'HelpScout ID': contact_row['HelpScout ID']
                })
            return "List Added Successfully"
    except Exception as e:
        traceback.print_exc()
        return render_template("error.html", error = e)

@app.route('/contact-list/<id>', methods = ['GET', 'POST'])
def view_contact_list(id):
    if 'login_email' not in session or 'login_pwd' not in session:
        return redirect(url_for("login"))
    elif session['access_level'] != "admin" and session['access_level'] != "sales":
        abort(403)
    else:
        try:
            table = list(lists_contacts_col.find({'List ID': int(id)}))
            if len(table) != 0:
                rows_html = ""
                for i in range(len(table)):
                    rows_html += f"""<tr>
                        <td>{i + 1}</td>
                        <td>{table[i]['Contact']}</td>
                        <td>{table[i]['Designation']}</td>
                        <td>{table[i]['Company']}</td>
                        <td>{table[i]['Email']}</td>
                        <td>{table[i]['Mobile']}</td>
                    </tr>"""
                table_html = f"""<table class="table table-responsive">
                    <tr>
                        <th>S.No.</th>
                        <th>Contact Name</th>
                        <th>Designation</th>
                        <th>Company</th>
                        <th>Email</th>
                        <th>Mobile</th>
                    </tr>
                    {rows_html}
                </table>"""
                
            else:
                table_html = ""
            return render_template("view_contact_list.html", table_html = table_html, list_name = contact_lists_col.find_one({'List ID': int(id)})['Name'], list_id = int(id))
        except Exception as e:
            traceback.print_exc()
            return render_template("error.html", error = e)

@app.route('/edit-list/<id>', methods = ['GET', 'POST'])
def edit_list(id):
    if 'login_email' not in session or 'login_pwd' not in session:
        return redirect(url_for("login"))
    elif session['access_level'] != "admin" and session['access_level'] != "sales":
        abort(403)
    else:
        try:
            contacts_list = list(contacts_col.find())
            list_name = contact_lists_col.find_one({'List ID': int(id)})['Name']
            list_contacts = lists_contacts_col.distinct('Contact ID', {'List ID': int(id)})
            if len(contacts_list) != 0:
                rows_edit_html = ""
                for i in range(len(contacts_list)):
                    rows_edit_html += f"""<tr>
                        <td><input id="edit_list_contact_{contacts_list[i]['Contact ID']}" value={contacts_list[i]['Contact ID']} type="checkbox"{" checked" if contacts_list[i]['Contact ID'] in list_contacts else ""}></td>
                        <td>{contacts_list[i]['Contact']}</td>
                        <td>{contacts_list[i]['Designation']}</td>
                        <td>{contacts_list[i]['Company']}</td>
                        <td>{contacts_list[i]['Email']}</td>
                        <td>{contacts_list[i]['Mobile']}</td>
                    </tr>"""
                table_edit_html = f"""<table class="table table-responsive">
                    <tr>
                        <th></th>
                        <th>Name</th>
                        <th>Designation</th>
                        <th>Company</th>
                        <th>Email</th>
                        <th>Mobile</th>
                    </tr>
                    {rows_edit_html}
                </table>"""
            else:
                table_edit_html = ""
            return render_template("edit_contact_list.html", list_id = id, list_name = list_name, table_edit_html = table_edit_html)
        except Exception as e:
            traceback.print_exc()
            return render_template("error.html", error = e)

@app.route('/save-edit-list', methods = ['POST'])
def save_edit_list():
    list_id = int(request.form['id'])
    list_name = request.form['name']
    list_contacts = request.form.getlist("contacts[]")
    if len(list(contact_lists_col.find({'Name': list_name}))) > 0:
        return "List Already Added"
    else:
        try:
            contact_lists_col.update_one({'List ID': list_id}, {"$set": {"Name": list_name}})
            lists_contacts_col.delete_many({'List ID': list_id})
            for contact in list_contacts:
                contact_row = contacts_col.find_one({'Contact ID': int(contact)})
                lists_contacts_col.insert_one({
                    'List ID': list_id,
                    'Name': list_name,
                    'Contact ID': int(contact),
                    'Contact': contact_row['Name'],
                    'Desigation': contact_row['Designation'],
                    'Company ID': contact_row['Company ID'],
                    'Company': contact_row['Company'],
                    'Email': contact_row['Email'],
                    'Mobile': contact_row['Mobile'],
                    'HelpScout ID': contact_row['HelpScout ID']
                })
            return "List Edited Successfully"
        except Exception as e:
            traceback.print_exc()
            return render_template("error.html", error = e)

@app.route('/bulk-email-log', methods = ['GET', 'POST'])
def bulk_email():
    if 'login_email' not in session or 'login_pwd' not in session:
        return redirect(url_for("login"))
    else:
        try:
            bulk_emails_list = list(bulk_emails_col.find())
            if len(bulk_emails_list) != 0:
                rows_html = ""
                for row in bulk_emails_list:
                    if row['Sent Status'] == "No":
                        sent_status = f"""<button class="edit_button" id="send_log_button_{row['Log ID']}" type="button" onclick="send_log({row['Log ID']}, send_log_button_{row['Log ID']})">Send</button>"""
                    elif row['Sent Status'] == "Yes":
                        sent_status = f"""<button class="disabled_button" id="send_log_button_{row['Log ID']}" type="button" onclick="send_log({row['Log ID']}, send_log_button_{row['Log ID']})" disabled>Sent</button>"""
                    elif row['Sent Status'] == "Partial":
                        sent_status = f"""<button class="disabled_button" id="send_log_button_{row['Log ID']}" type="button" onclick="send_log({row['Log ID']}, send_log_button_{row['Log ID']})" disabled>Partially Sent</button>"""
                    rows_html += f"""<tr>
                        <td>{row['Log ID']}</td>
                        <td>{row['Name']}</td>
                        <td>{row['Contacts List Name']}</td>
                        <td>{row['Product']}</td>
                        <td>{sent_status}</td>
                    </tr>"""
                table_html = f"""<table class="table table-responsive">
                    <tr>
                        <th>S.No.</th>
                        <th>Log Name</th>
                        <th>Contacts List</th>
                        <th>Product</th>
                        <th>Send</th>
                    </tr>
                    {rows_html}
                </table>"""
            else:
                table_html = ""
            dropdown_options = contact_lists_col.distinct("List ID")
            dropdown_options_html = ""
            for option in dropdown_options:
                dropdown_options_html += f"<option value='{option}'>{contact_lists_col.find_one({'List ID': option})['Name']}</option>"
            if os.getenv("last_opened_check_dt"):
                lodt = f"Checked at {os.getenv('ast_opened_check_dt')}"
            else:
                lodt = "Not Checked"
            return render_template("bulk_email.html", access_level = session['access_level'], dropdown_options_html = dropdown_options_html, table_html = table_html, lodt = lodt)
        except Exception as e:
            traceback.print_exc()
            return render_template("error.html", error = e)

@app.route('/send-log', methods = ['GET', 'POST'])
def send_log():
    log_id = int(request.form['id'])
    log_row = bulk_emails_col.find_one({'Log ID': log_id})
    contacts_to_send = list(lists_contacts_col.find({"List ID": int(log_row['Contacts List ID'])}))
    bearer_token = get_bearer_token()
    headers = {'Authorization': f"Bearer {bearer_token}"}
    if len(contacts_to_send) > 0:
        session['email_stopped_at'] = "Not started yet"
        try:
            for contact in contacts_to_send:
                if log_row['Product'] == "YGROO.TRAINING":
                    subject = f"Revolutionize L&D with AI-Powered L&DaaS at {contact['Company']}"
                    text = f"""Dear {contact['Contact']},
                    <br><br>
                    I hope this email finds you well.
                    <br><br>
                    Introducing a transformative solution that will revolutionize Learning & Development for your company - YGROO.TRAINING.
                    <br><br>
                    In today's business landscape, the need to <b>develop talent better, faster, and at lower costs</b> has never been more critical. This is where YGROO.TRAINING comes into play with our innovative Learning and Development as a Service (L&DaaS) platform.
                    <br><br>
                    <b>Experience the Future with L&DaaS</b>
                    <br><br>
                    Making the shift from traditional in-house training to L&DaaS can significantly impact your company's growth trajectory. Our platform offers a <b>unique edge</b> that sets us apart:
                    <br>
                    <ol>
                        <li>
                            <b>AI-Powered Personalization:</b> Our AI allows us to create precise benchmarks for skills, competencies, and behaviours specific to each job role to design personalized learning journeys for your employees.
                        </li>
                        <li>
                            <b>World-Class Learning Experience:</b> We combine emerging technologies, modern content, and experienced instructors using a mix of online and instructor-led methods to maximize engagement and retention.
                        </li>
                        <li>
                            <b>End-to-End Training Solutions:</b> YGROO.TRAINING covers all your training needs from onboarding, skills enhancement, compliance, job role-based training, to executive development.
                        </li>
                        <li>
                            <b>Global Unity, Local Impact:</b> Our platform transcends language and geographical barriers, fostering a culture of excellence across your global workforce.
                        </li>
                        <li>
                            <b>Certifications that Matter:</b> Elevate your team's standing with a range of certifications, from skill and job role certifications to accredited micro-credentials, master classes, and even international degrees.
                        </li>
                        <li>
                            <b>Embrace the Future Today:</b> Our commitment to growth and excellence is motivated by a social cause, not just profits.
                        </li>
                    </ol>
                    <br>
                    Let us show you how our platform could benefit your talent development initiatives.
                    <br><br>
                    Please let me know a convenient time for you to schedule a meeting.
                    <br><br><br>
                    Thank you,
                    <br>
                    Kishore Kumar"""
                elif log_row['Product'] == "YGROO.ART":
                    subject = f"Revolutionalise Talent Aqcuisition at {contact['Company']} with our AI-Driven Solution"
                    text = f"""Dear {contact['Contact']},
                    <br><br>
                    I hope this email finds you well.
                    <br><br>
                    Introducing a pioneering AI-driven solution, YGROO.ART to revolutionize the way your company acquire and develops talent.
                    <br><br>
                    In today's business landscape, the need to <b>source, recruit and retail top-tier talent</b> has never been more critical. This is where YGROO.ART comes into play to ensure:
                    <br>
                    <ol>
                        <li><b>Increased Retention:</b> Our AI matches candidates based on skills, competencies, and behaviours required by their job role. </li>
                        <li><b>Faster Recruitment:</b> Through our cloud-based AI solution and efficient service delivery models, to accelerate recruitment to hire anytime and anywhere.</li>
                        <li><b>Cost Efficiency:</b> Say goodbye to fixed costs. Save costs up to 50% with YGROO.ART as compared to traditional recruitment agency models.</li>
                    </ol>
                    <br>
                    <b>Our Unique Edge</b>
                    <br>
                    <ol>
                        <li>
                            <b>AI-Driven Precision:</b> Our solution offers behavioural, skill and competency assessments against job-role based benchmarks for candidates as well as Work & Study programs to nurture and retain talent.
                        </li>
                        <li>
                            <b>High Scalability:</b> Assess 1000s of candidates anywhere, anytime without compromising on speed or quality.
                        </li>
                        <li>
                            <b>Retention Guarantee:</b> Be confident in your hires with our industry-first retention guarantee of 6 months. If a sourced candidate leaves in 6 months, we provide a free replacement.
                        </li>
                        <li>
                            <b>Phenomenal Price Performance:</b> Harnessing emerging technologies and economies of scale, we can deliver 30-50% cost savings.
                        </li>
                    </ol>
                    <br>
                    <b>Comprehensive Solutions Tailored to Your Needs</b>
                    <br><br>
                    We understand your company's requirements are unique. That's why YGROO.ART offers tailored solutions that suit your unique needs.
                    <br>
                    <ol>
                        <li>
                            <b>ASSESS & RECRUIT:</b> Source top-tier candidates at scale with a success fee of <b>7% of annual CTC</b>.
                        </li>
                        <li>
                            <b>ASSESS, RECRUIT & TRAIN:</b> Source and train candidates based on your requirements for a success fee of <b>11% of annual CTC</b>.
                        </li>
                        <li>
                            <b>WORK & STUDY PROGRAMS:</b> Enhance retention and provide new hires with online diplomas and degrees, either covered by your company or the candidates themselves.
                        </li><li>
                            <b>BOOTCAMPS:</b> Identify and train pre-qualified interns and apprentices, all for a success fee of <b>10% of annual CTC</b>.
                        </li>
                    </ol>
                    <br>
                    See how YGROO.ART can benefit your talent acquisition and development initiatives.
                    <br><br>
                    Please let me know a convenient time for you to schedule a meeting.
                    <br><br><br>
                    Thank you,
                    <br>
                    Kishore Kumar"""
                body = {
                    "subject": subject,
                    "type": "email",
                    "mailboxId": 299086,
                    "status": "active",
                    "customer": {
                        "id": contact['HelpScout ID']
                    },
                    "threads": [
                        {
                            "type": "reply",
                            "customer": {
                                "id": contact['HelpScout ID']
                            },
                            "text": text
                        }
                    ],
                    "tags": [log_row['Name'].lower(), log_row['Contacts List Name'].lower(), log_row['Product'].lower()]
                }
                response = requests.post("https://api.helpscout.net/v2/conversations", headers = headers, json = body)
                conv_id = response.headers['Resource-ID']
                conv_date_sent = response.headers['Date']
                log_col.insert_one({
                    'Log ID': log_id,
                    'Name': log_row['Name'],
                    'Contacts List ID': log_row['Contacts List ID'],
                    'Contacts List Name': log_row['Contacts List Name'],
                    'Contact ID': contact['Contact ID'],
                    'Contact': contact['Contact'],
                    'Designation': contact['Designation'],
                    'Company ID': contact['Company ID'],
                    'Company': contact['Company'],
                    'Email': contact['Email'],
                    'Mobile': contact['Mobile'],
                    'Product': log_row['Product'],
                    'Date & Time Sent': pytz.utc.localize(datetime.strptime(conv_date_sent, '%a, %d %b %Y %H:%M:%S %Z')).astimezone(pytz.timezone('Asia/Kolkata')),
                    'HelpScout ID': conv_id,
                    'Opened Status': "No",
                    'Opened Date & Time': "Not Opened"
                })
                session['email_stopped_at'] = contact['Email']
            bulk_emails_col.update_one({'Log ID': log_id}, {"$set": {"Sent Status": "Yes"}})
            return "Bulk Emails Sent Out Successfully"
        except Exception as e:
            traceback.print_exc()
            print("Log ID:", log_id)
            print("Email Stopped At:", session['email_stopped_at'])
            if session['email_stopped_at'] == "Not started yet":
                bulk_emails_col.update_one({'Log ID': log_id}, {"$set": {"Sent Status": "No"}})
                return session['email_stopped_at']
            else:
                bulk_emails_col.update_one({'Log ID': log_id}, {"$set": {"Sent Status": "Partial"}})
                return "Stopped at", session['email_stopped_at']
    else:
        return "No Contacts in List"

@app.route('/bulk-email-opened-status', methods = ['GET', 'POST'])
def bulk_email_opened_status():
    bearer_token = get_bearer_token()
    headers = {'Authorization': f"Bearer {bearer_token}"}
    bulk_email_list = list(log_col.find({"Opened Status": "No"}))
    if len(bulk_email_list) > 0:
        session['check_stopped_at'] = "Not started yet"
        try:
            for row in bulk_email_list:
                response = requests.get(f"https://api.helpscout.net/v2/conversations/{str(row['HelpScout ID'])}?embed=threads", headers = headers)
                if "openedAt" in response.json()['_embedded']['threads'][0]:
                    opened_dt = response.json()['_embedded']['threads'][0]['openedAt']
                    opened_dt = datetime.strptime(opened_dt, "%Y-%m-%dT%H:%M:%SZ")
                    opened_dt = opened_dt.replace(tzinfo = timezone.utc).astimezone(timezone(timedelta(hours = 5, minutes = 30)))
                    log_col.update_one({"_id": row['_id']}, {"$set": {"Opened Status": "Yes", "Opened Date & Time": opened_dt}})
                    session['check_stopped_at'] = row['Email']
            last_opened_status_checked = datetime.now(pytz.timezone('Asia/Kolkata'))
            check_type = "complete"
            message = "Opened Status Checked Successfully"
        except Exception as e:
            traceback.print_exc()
            last_opened_status_checked = datetime.now(pytz.timezone('Asia/Kolkata'))
            check_type = "partial"
            print("HelpScout ID:", str(row['HelpScout ID']))
            print("Email Stopped At:", session['check_stopped_at'])
            message = f"Stopped at {session['check_stopped_at']}"
    else:
        message = "No Bulk Emails Sent Out"
        last_opened_status_checked = datetime.now(pytz.timezone('Asia/Kolkata'))
        check_type = "complete"
    opened_list = list(log_col.find({"Opened Status": "Yes"}).sort('Opened Date & Time', -1))
    closed_list = list(log_col.find({"Opened Status": "No"}).sort("Date & Time Sent"))
    opened_rows_html = ""
    closed_rows_html = ""
    if len(opened_list) > 0:
        for i in range(len(opened_list)):
            opened_rows_html += f"""<tr>
                <td>{i + 1}</td>
                <td>{opened_list[i]['Name']}</td>
                <td>{opened_list[i]['Contacts List Name']}</td>
                <td>{opened_list[i]['Contact']}</td>
                <td>{opened_list[i]['Designation']}</td>
                <td>{opened_list[i]['Company']}</td>
                <td>{opened_list[i]['Product']}</td>
                <td>{str(datetime.strptime(str(opened_list[i]['Date & Time Sent'].astimezone(pytz.timezone('Asia/Kolkata'))), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %I:%M %p"))}</td>
                <td>{str(datetime.strptime(str(opened_list[i]['Opened Date & Time'].replace(tzinfo = pytz.timezone('Asia/Kolkata'))), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %I:%M %p"))}</td>
            </tr>"""
        opened_table_html = f"""<table class="table table-responsive">
            <tr>
                <th>S.No.</th>
                <th>Log</th>
                <th>Contacts List</th>
                <th>Contact</th>
                <th>Designation</th>
                <th>Company</th>
                <th>Product</th>
                <th>Date & Time Sent</th>
                <th>Date & Time Opened</th>
            </tr>
            {opened_rows_html}
        </table>"""
    else:
        opened_table_html = "No opened emails."
    if len(closed_list) > 0:
        for i in range(len(closed_list)):
            closed_rows_html += f"""<tr>
                <td>{i + 1}</td>
                <td>{closed_list[i]['Name']}</td>
                <td>{closed_list[i]['Contacts List Name']}</td>
                <td>{closed_list[i]['Contact']}</td>
                <td>{closed_list[i]['Designation']}</td>
                <td>{closed_list[i]['Company']}</td>
                <td>{closed_list[i]['Product']}</td>
                <td>{str(datetime.strptime(str(closed_list[i]['Date & Time Sent'].astimezone(pytz.timezone('Asia/Kolkata'))), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %I:%M %p"))}</td>
            </tr>"""
        closed_table_html = f"""<table class="table table-responsive">
            <tr>
                <th>S.No.</th>
                <th>Log</th>
                <th>Contacts List</th>
                <th>Contact</th>
                <th>Designation</th>
                <th>Company</th>
                <th>Product</th>
                <th>Date & Time Sent</th>
            </tr>
            {closed_rows_html}
        </table>"""
    else:
        closed_table_html = "No unopened emails."
    last_checked = f"Last checked at {last_opened_status_checked.strftime('%d/%m/%Y %I:%M %p')} ({check_type})"
    return render_template("view_bulk_email.html", last_checked = last_checked, opened_table_html = opened_table_html, closed_table_html = closed_table_html, message = message)

@app.route('/add-bulk-email-log', methods = ['GET', 'POST'])
def add_bulk_email_log():
    try:
        log_name = request.form['name']
        product = request.form['product']
        log_list_id = request.form['list_id']
        log_list_name = request.form['list_name']
        matches = list(bulk_emails_col.find({
            'Name': {
                '$regex': f'^{re.escape(log_name)}$',
                '$options': 'i'
            }
        }))
        if len(matches) > 0:
            return "Bulk Email Log Already Added"
        else:
            bulk_emails_col.insert_one({
                'Log ID': bulk_emails_col.count_documents({}) + 1,
                'Name': log_name,
                'Contacts List ID': int(log_list_id),
                'Contacts List Name': log_list_name,
                'Product': product,
                'Sent Status': "No"
            })
            return "Bulk Email Log Added Successfully"
    except Exception as e:
        traceback.print_exc()
        return render_template("error.html", error = e)

@app.route('/login')
def login():
    if "login_email" in session and "login_pwd" in session:
        return redirect(url_for("index"))
    else:
        return render_template("login.html")

@app.route('/check-login-credentials', methods = ['POST'])
def check_login_credentials():
    email = request.form['email']
    pwd = request.form['pwd']
    if email in users_col.distinct('Email'):
        correct_pwd = users_col.find_one({'Email': email})['Password']
        if pwd != correct_pwd:
            return "Incorrect Password"
        else:
            session['login_email'] = email
            session['login_pwd'] = pwd
            session['access_level'] = users_col.find_one({'Email': email})['Access Level']
            return "Logged In"
    else:
        return "Not Registered"

@app.route("/logout", methods = ['GET', 'POST'])
def logout():
    session.pop('login_email', default = None)
    session.pop('login_pwd', default = None)
    session.pop('access_level', default = None)
    return "Logged Out Successfully"
