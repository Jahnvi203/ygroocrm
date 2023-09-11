import requests
import re
from copy import deepcopy
from flask import Flask, render_template, request, redirect, url_for, session, abort
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY
import os
import time
import pytz

app = Flask(__name__)
app.secret_key = os.getenv("app_secret_key")

@app.route('/')
def index():
    if 'login_email' not in session or 'login_pwd' not in session:
        return redirect(url_for("login"))
    elif session['access_level'] != "admin" and session['access_level'] != "sales":
        abort(403)
    else:
        table_df = pd.read_csv("static/resources/reminders.csv")
        table_df = table_df[table_df['Show'] == True].sort_values('Due Date & Time')
        today_dt = datetime.now(timezone(timedelta(hours = 5, minutes = 30)))
        current_week_dt = datetime.now(timezone(timedelta(hours = 5, minutes = 30))) + timedelta(days = 7)
        pending_df = table_df[pd.to_datetime(table_df['Due Date & Time']).dt.date < today_dt.date()]
        due_today_df = table_df[pd.to_datetime(table_df['Due Date & Time']).dt.date == today_dt.date()]
        due_week_df = table_df[(today_dt.date() < pd.to_datetime(table_df['Due Date & Time']).dt.date) & (pd.to_datetime(table_df['Due Date & Time']).dt.date <= current_week_dt.date())]
        pending_list = pending_df.values.tolist()
        due_today_list = due_today_df.values.tolist()
        due_week_list = due_week_df.values.tolist()
        pending_rows_html = ""
        due_today_rows_html = ""
        due_week_rows_html = ""
        if len(pending_list) > 0:
            pending_rows_html = ""
            for i in range(len(pending_list)):
                new_dt = datetime.strptime(pending_list[i][7], "%Y-%m-%dT%H:%M").replace(tzinfo = pytz.timezone('Asia/Kolkata'))
                due_since = datetime.now(timezone(timedelta(hours = 5, minutes = 30))) - new_dt
                due_since = due_since.days
                pending_rows_html += f"""<tr>
                    <td><input id="reminder_check_{pending_list[i][0]}" onchange="check_reminder({pending_list[i][0]})" type="checkbox"></td>
                    <td>{pending_list[i][1]}</td>
                    <td>{pending_list[i][3]}</td>
                    <td>{pending_list[i][5]}</td>
                    <td>{pending_list[i][6]}</td>
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
                new_dt = datetime.strptime(due_today_list[i][7], "%Y-%m-%dT%H:%M").replace(tzinfo = pytz.timezone('Asia/Kolkata'))
                due_since = datetime.now(timezone(timedelta(hours = 5, minutes = 30))) - new_dt
                due_since = due_since.days
                due_today_rows_html += f"""<tr>
                    <td><input id="reminder_check_{due_today_list[i][0]}" onchange="check_reminder({due_today_list[i][0]})" type="checkbox"></td>
                    <td>{due_today_list[i][1]}</td>
                    <td>{due_today_list[i][3]}</td>
                    <td>{due_today_list[i][5]}</td>
                    <td>{due_today_list[i][6]}</td>
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
                new_dt = datetime.strptime(due_week_list[i][7], "%Y-%m-%dT%H:%M").replace(tzinfo = pytz.timezone('Asia/Kolkata'))
                due_since = datetime.now(timezone(timedelta(hours = 5, minutes = 30))) - new_dt
                due_since = due_since.days
                due_week_rows_html += f"""<tr>
                    <td><input id="reminder_check_{due_week_list[i][0]}" onchange="check_reminder({due_week_list[i][0]})" type="checkbox"></td>
                    <td>{due_week_list[i][1]}</td>
                    <td>{due_week_list[i][3]}</td>
                    <td>{due_week_list[i][5]}</td>
                    <td>{due_week_list[i][6]}</td>
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

@app.route('/companies')
def companies():
    if 'login_email' not in session or 'login_pwd' not in session:
        return redirect(url_for("login"))
    elif session['access_level'] != "admin" and session['access_level'] != "sales":
        abort(403)
    else:
        table_df = pd.read_csv("static/resources/companies.csv")
        table = table_df.values.tolist()
        statuses = ['Prospect', 'Called', 'Emailed', 'Not Interested', 'Proposal Sent', 'Meeting Scheduled', 'MoU Signed']
        if len(table) > 0:
            rows_html = ""
            for i in range(len(table)):
                rows_html += f"""<tr>
                    <td>{table[i][0]}</td>
                    <td>{table[i][1]}</td>
                    <td>{table[i][2]}</td>
                    <td>{table[i][3]}</td>
                    <td>
                        <select id="status_{table[i][0]}" onchange="status_change({table[i][0]}, this.value)">
                            <option value="Prospect"{" selected" if table[i][4] == "Prospect" else ""}>Prospect</option>
                            <option value="Called"{" selected" if table[i][4] == "Called" else ""}>Called</option>
                            <option value="Emailed"{" selected" if table[i][4] == "Emailed" else ""}>Emailed</option>
                            <option value="Not Interested"{" selected" if table[i][4] == "Not Interested" else ""}>Not Interested</option>
                            <option value="Proposal Sent"{" selected" if table[i][4] == "Proposal Sent" else ""}>Proposal Sent</option>
                            <option value="Meeting Scheduled"{" selected" if table[i][4] == "Meeting Scheduled" else ""}>Meeting Scheduled</option>
                            <option value="In Discussion (Hot)"{" selected" if table[i][4] == "In Discussion (Hot)" else ""}>In Discussion (Hot)</option>
                            <option value="In Discussion (Cold)"{" selected" if table[i][4] == "In Discussion (Cold)" else ""}>In Discussion (Cold)</option>
                            <option value="MoU Signed"{" selected" if table[i][4] == "MoU Signed" else ""}>MoU Signed</option>
                        </select>
                    </td>
                    <td><button id="edit_company_{table[i][0]}" class="edit_button" data-bs-toggle="modal" data-bs-target="#edit_company_modal_{table[i][0]}">Edit</button></td>
                    <td><a href="/company/{table[i][0]}"><button class="view_button">View</button></a></td>
                </tr>
                <div class="modal fade" id="edit_company_modal_{table[i][0]}" tabindex="-1" aria-hidden="true">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Edit {table[i][1]}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="row">
                                    <div class="col-md-3">
                                        <label for="edit_company_name_{table[i][0]}">Name</label>
                                    </div>
                                    <div class="col-md-9">
                                        <input id="edit_company_name_{table[i][0]}" type="text" value="{table[i][1]}">
                                    </div>
                                    <div class="my-2"></div>
                                </div>
                                <div class="row">
                                    <div class="col-md-3">
                                        <label for="edit_company_state_{table[i][0]}">State</label>
                                    </div>
                                    <div class="col-md-9">
                                        <select id="edit_company_state_{table[i][0]}">
                                            <option value="Karnataka"{" selected" if table[i][2] == "Karnataka" else ""}>Karnataka</option>
                                            <option value="Punjab"{" selected" if table[i][2] == "Punjab" else ""}>Punjab</option>
                                            <option value="Maharashtra"{" selected" if table[i][2] == "Maharashtra" else ""}>Maharashtra</option>
                                            <option value="Uttar Pradesh"{" selected" if table[i][2] == "Uttar Pradesh" else ""}>Uttar Pradesh</option>
                                            <option value="Tamil Nadu"{" selected" if table[i][2] == "Tamil Nadu" else ""}>Tamil Nadu</option>
                                            <option value="Delhi"{" selected" if table[i][2] == "Delhi" else ""}>Delhi</option>
                                        </select>
                                    </div>
                                    <div class="my-2"></div>
                                </div>
                                <div class="row">
                                    <div class="col-md-3">
                                        <label for="edit_company_website_{table[i][0]}">Website</label>
                                    </div>
                                    <div class="col-md-9">
                                        <input id="edit_company_website_{table[i][0]}" type="text" value="{table[i][3]}">
                                    </div>
                                    <div class="my-2"></div>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" onclick="company_change({table[i][0]})" class="view_button" data-bs-dismiss="modal">Save</button>
                            </div>
                        </div>
                    </div>
                </div>"""
            table_html = f"""<table class="table table-responsive">
                <tr>
                    <th>S.No.</th>
                    <th>Company</th>
                    <th>State</th>
                    <th>Website</th>
                    <th>Status</th>
                    <th>Edit</th>
                    <th>View</th>
                </tr>
                {rows_html}
            </table>"""
        else:
            table_html = "None"
        return render_template("companies.html", table_html = table_html)

@app.route('/contacts')
def contacts():
    if 'login_email' not in session or 'login_pwd' not in session:
        return redirect(url_for("login"))
    elif session['access_level'] != "admin" and session['access_level'] != "sales":
        abort(403)
    else:
        table_df = pd.read_csv("static/resources/contacts.csv")
        table = table_df.values.tolist()
        rows_html = ""
        if len(table) > 0:
            for i in range(len(table)):
                rows_html += f"""<tr>
                    <td>{table[i][0]}</td>
                    <td>{table[i][1]}</td>
                    <td>{table[i][2]}</td>
                    <td>{table[i][4]}</td>
                    <td>{table[i][5]}</td>
                    <td>{table[i][6]}</td>
                    <td><a href="/contact/{table[i][0]}/communication"><button class="view_button">Communication</button></a></td>
                    <td><a href="https://secure.helpscout.net/customers/{table[i][7]}" target="_blank"><button id="hs_url_{table[i][0]}" class="edit_button">Start</button></a></td>
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

@app.route('/process-status-change', methods = ['POST'])
def process_status_change():
    company_id = int(request.form['company_id'])
    new_status = request.form['new_status']
    table_df = pd.read_csv("static/resources/companies.csv")
    table_df.loc[table_df['Company ID'] == company_id, 'Status'] = new_status
    table_df.to_csv("static/resources/companies.csv", index = False)
    return "Status Change Processed Successfully"

@app.route('/company/<id>')
def view_company(id):
    if 'login_email' not in session or 'login_pwd' not in session:
        return redirect(url_for("login"))
    else:
        id = int(id)
        companies_df = pd.read_csv("static/resources/companies.csv")
        company_row = companies_df[companies_df['Company ID'] == id].values.tolist()[0]
        company_options_html = ""
        for company in companies_df[['Company ID', 'Company']].values.tolist():
            company_options_html += f'<option value="{company[1]}_{company[0]}"{" selected" if company[1] == company_row[1] else ""}>{company[1]}</option>'
        status = f"""<select id="status_{id}" onchange="status_change({company_row[0]}, this.value)">
            <option value="Prospect"{" selected" if company_row[4] == "Prospect" else ""}>Prospect</option>
            <option value="Called"{" selected" if company_row[4] == "Called" else ""}>Called</option>
            <option value="Emailed"{" selected" if company_row[4] == "Emailed" else ""}>Emailed</option>
            <option value="Not Interested"{" selected" if company_row[4] == "Not Interested" else ""}>Not Interested</option>
            <option value="Proposal Sent"{" selected" if company_row[4] == "Proposal Sent" else ""}>Proposal Sent</option>
            <option value="Meeting Scheduled"{" selected" if company_row[4] == "Meeting Scheduled" else ""}>Meeting Scheduled</option>
            <option value="In Discussion (Hot)"{" selected" if company_row[4] == "In Discussion (Hot)" else ""}>In Discussion (Hot)</option>
            <option value="In Discussion (Cold)"{" selected" if company_row[4] == "In Discussion (Cold)" else ""}>In Discussion (Cold)</option>
            <option value="MoU Signed"{" selected" if company_row[4] == "MoU Signed" else ""}>MoU Signed</option>
        </select>"""
        contacts_df = pd.read_csv("static/resources/contacts.csv")
        contacts_df = contacts_df[contacts_df['Company ID'] == company_row[0]]
        contacts = contacts_df.values.tolist()
        meetings_df = pd.read_csv("static/resources/meetings.csv")
        meetings_df = meetings_df[meetings_df['Company ID'] == company_row[0]]
        meetings = meetings_df.values.tolist()
        reminders_df = pd.read_csv("static/resources/reminders.csv")
        reminders_df = reminders_df[reminders_df['Company ID'] == company_row[0]]
        reminders_df = reminders_df[reminders_df['Show'] == True].sort_values('Due Date & Time')
        reminders = reminders_df.values.tolist()
        company_contact_options_html = ""
        contacts_html = ""
        meetings_html = ""
        reminders_html = ""
        if len(contacts) > 0:
            for contact in contacts:
                company_contact_options_html += f'<option value="{contact[1]}_{contact[0]}">{contact[1]}</option>'
                contacts_html += f"""<tr>
                    <td>{contact[1]}</td>
                    <td>{contact[2]}</td>
                    <td>{contact[5]}</td>
                    <td>{contact[6]}</td>
                    <td><button id="edit_contact_{contact[0]}" class="edit_button" data-bs-toggle="modal" data-bs-target="#edit_contact_modal_{contact[0]}">Edit</button></td>
                    <td><a href="/contact/{contact[0]}/communication"><button class="view_button">Communication</button></a></td>
                    <td><a href="https://secure.helpscout.net/customers/{contact[7]}" target="_blank"><button id="hs_url_{contact[0]}" class="edit_button">Start</button></a></td>
                </tr>
                <div class="modal fade" id="edit_contact_modal_{contact[0]}" tabindex="-1" aria-hidden="true">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Edit {contact[1]} from {contact[4]}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="row">
                                    <div class="col-md-3">
                                        <label for="edit_contact_company_{contact[0]}">Company</label>
                                    </div>
                                    <div class="col-md-9">
                                        <select id="edit_contact_company_{contact[0]}" disabled>
                                            {company_options_html}
                                        </select>
                                    </div>
                                    <div class="my-2"></div>
                                </div>
                                <div class="row">
                                    <div class="col-md-3">
                                        <label for="edit_contact_name_{contact[0]}">Name</label>
                                    </div>
                                    <div class="col-md-9">
                                        <input id="edit_contact_name_{contact[0]}" type="text" value="{contact[1]}">
                                    </div>
                                    <div class="my-2"></div>
                                </div>
                                <div class="row">
                                    <div class="col-md-3">
                                        <label for="edit_contact_designation_{contact[0]}">Designation</label>
                                    </div>
                                    <div class="col-md-9">
                                        <input id="edit_contact_designation_{contact[0]}" type="text" value="{contact[2]}">
                                    </div>
                                    <div class="my-2"></div>
                                </div>
                                <div class="row">
                                    <div class="col-md-3">
                                        <label for="edit_contact_email_{contact[0]}">Email</label>
                                    </div>
                                    <div class="col-md-9">
                                        <input id="edit_contact_email_{contact[0]}" type="email" value="{contact[5]}" disabled>
                                    </div>
                                    <div class="my-2"></div>
                                </div>
                                <div class="row">
                                    <div class="col-md-3">
                                        <label for="edit_contact_mobile_{contact[0]}">Mobile</label>
                                    </div>
                                    <div class="col-md-9">
                                        <input id="edit_contact_mobile_{contact[0]}" type="tel" value="{contact[6]}">
                                    </div>
                                    <div class="my-2"></div>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" onclick="contact_change({contact[0]})" class="view_button" data-bs-dismiss="modal">Save</button>
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
                    <td>{meeting[1]}</td>
                    <td>{datetime.strptime(meeting[4], "%Y-%m-%dT%H:%M").strftime("%d/%m/%Y %I:%M %p")}</td>
                    <td>{datetime.strptime(meeting[5], "%Y-%m-%dT%H:%M").strftime("%d/%m/%Y %I:%M %p")}</td>
                    <td>{meeting[6]}</td>
                    <td>{meeting[7]}</td>
                    <td><button id="edit_meeting_{meeting[0]}" class="edit_button" data-bs-toggle="modal" data-bs-target="#edit_meeting_modal_{meeting[0]}">Edit</button></td>
                </tr>
                <div class="modal fade" id="edit_meeting_modal_{meeting[0]}" tabindex="-1" aria-hidden="true">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Edit {meeting[1]} Meeting from {meeting[3]}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="row">
                                    <div class="col-md-3">
                                        <label for="edit_meeting_company_{meeting[0]}">Company</label>
                                    </div>
                                    <div class="col-md-9">
                                        <select id="edit_meeting_company_{meeting[0]}" disabled>
                                            {company_options_html}
                                        </select>
                                    </div>
                                    <div class="my-2"></div>
                                </div>
                                <div class="row">
                                    <div class="col-md-3">
                                        <label for="edit_meeting_type_{meeting[0]}">Type</label>
                                    </div>
                                    <div class="col-md-9">
                                        <select id="edit_meeting_type_{meeting[0]}">
                                            <option value="Introduction"{" selected" if meeting[1] == "Introduction" else None}>Introduction</option>
                                            <option value="Demo"{" selected" if meeting[1] == "Demo" else None}>Demo</option>
                                            <option value="Go-Live"{" selected" if meeting[1] == "Go-Live" else None}>Go-Live</option>
                                        </select>
                                    </div>
                                    <div class="my-2"></div>
                                </div>
                                <div class="row">
                                    <div class="col-md-3">
                                        <label for="edit_meeting_start_{meeting[0]}">Start Date & Time</label>
                                    </div>
                                    <div class="col-md-9">
                                        <input type="datetime-local" id="edit_meeting_start_{meeting[0]}" value="{meeting[4]}">
                                    </div>
                                    <div class="my-2"></div>
                                </div>
                                <div class="row">
                                    <div class="col-md-3">
                                        <label for="edit_meeting_end_{meeting[0]}">End Date & Time</label>
                                    </div>
                                    <div class="col-md-9">
                                        <input type="datetime-local" id="edit_meeting_end_{meeting[0]}" value={meeting[5]}>
                                    </div>
                                    <div class="my-2"></div>
                                </div>
                                <div class="row">
                                    <div class="col-md-3">
                                        <label for="edit_meeting_prods_{meeting[0]}">Product(s) Pitched</label>
                                    </div>
                                    <div class="col-md-9">
                                        <input id="ygroo_training" class="edit_meeting_prods_{meeting[0]}" type="checkbox" value="YGROO TRAINING"{" checked" if "YGROO TRAINING" in meeting[6].split(", ") else ""}>
                                        <label for="ygroo_training">YGROO TRAINING</label>
                                        <br>
                                        <input id="ygroo_art" class="edit_meeting_prods_{meeting[0]}" type="checkbox" value="YGROO ART"{" checked" if "YGROO ART" in meeting[6].split(", ") else ""}>
                                        <label for="ygroo_art">YGROO ART</label>
                                        <br>
                                        <input id="ygroo_pro" class="edit_meeting_prods_{meeting[0]}" type="checkbox" value="YGROO PRO"{" checked" if "YGROO PRO" in meeting[6].split(", ") else ""}>
                                        <label for="ygroo_pro">YGROO PRO</label>
                                        <br>
                                        <input id="ygroo_studio" class="edit_meeting_prods_{meeting[0]}" type="checkbox" value="YGROO STUDIO"{" checked" if "YGROO STUDIO" in meeting[6].split(", ") else ""}>
                                        <label for="ygroo_studio">YGROO STUDIO</label>
                                        <br>
                                        <input id="ygroo_care" class="edit_meeting_prods_{meeting[0]}" type="checkbox" value="YGROO CARE"{" checked" if "YGROO CARE" in meeting[6].split(", ") else ""}>
                                        <label for="ygroo_care">YGROO CARE</label>
                                        <br>
                                        <input id="ygroo_careers" class="edit_meeting_prods_{meeting[0]}" type="checkbox" value="YGROO CAREERS"{" checked" if "YGROO CAREERS" in meeting[6].split(", ") else ""}>
                                        <label for="ygroo_careers">YGROO CAREERS</label>
                                    </div>
                                    <div class="my-2"></div>
                                </div>
                                <div class="row">
                                    <div class="col-md-3">
                                        <label for="edit_meeting_agenda_{meeting[0]}">Agenda</label>
                                    </div>
                                    <div class="col-md-9">
                                        <textarea id="edit_meeting_agenda_{meeting[0]}" rows="5">{meeting[7]}</textarea>
                                    </div>
                                    <div class="my-2"></div>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" onclick="meeting_change({meeting[0]})" class="view_button" data-bs-dismiss="modal">Save</button>
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
                    <td><input id="reminder_check_{reminder[0]}" onchange="check_reminder({reminder[0]})" type="checkbox"></td>
                    <td>{reminder[1]}</td>
                    <td>{reminder[5]}</td>
                    <td>{reminder[6]}</td>
                    <td>{datetime.strptime(reminder[7], "%Y-%m-%dT%H:%M").strftime("%d/%m/%Y %I:%M %p")}</td>
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
        return render_template("view_company.html", id = id, name = company_row[1], state = company_row[2], website = company_row[3], status = status, contacts_html = contacts_table_html, meetings_html = meetings_table_html, reminders_html = reminders_table_html, company_options_html = company_options_html, company_contact_options_html = company_contact_options_html)

@app.route('/process-company-change', methods = ['POST'])
def process_company_change():
    table_df = table_df = pd.read_csv("static/resources/companies.csv")
    table_df.loc[table_df['Company ID'] == int(request.form['id']), 'Company'] = request.form['name']
    table_df.loc[table_df['Company ID'] == int(request.form['id']), 'State'] = request.form['state']
    table_df.loc[table_df['Company ID'] == int(request.form['id']), 'Website'] = request.form['website']
    table_df.to_csv("static/resources/companies.csv", columns = ['Company ID', 'Company', 'State', 'Website', 'Status'], index = False)
    table_df = table_df = pd.read_csv("static/resources/contacts.csv")
    contacts_df = table_df[table_df['Company ID'] == int(request.form['id'])]['HelpScout ID']
    contacts_list = contacts_df.unique()
    bearer_token = get_bearer_token()
    headers = {'Authorization': f"Bearer {bearer_token}"}
    for contact in contacts_list:
        body = [{
            "op" : "replace",
            "path" : "/organization",
            "value" : f"{request.form['name']}"
        }]
        requests.patch(f"https://api.helpscout.net/v2/customers/{contact}", headers = headers, json = body)
    table_df.loc[table_df['Company ID'] == int(request.form['id']), 'Company'] = request.form['name']
    table_df.to_csv("static/resources/contacts.csv", columns = ['Contact ID', 'Name', 'Designation', 'Company ID', 'Company', 'Email', 'Mobile'], index = False)
    return "Company Change Processed Successfully"

@app.route('/process-contact-change', methods = ['POST'])
def process_contact_change():
    table_df = table_df = pd.read_csv("static/resources/contacts.csv")
    table_df.loc[table_df['Contact ID'] == int(request.form['id']), 'Name'] = request.form['name']
    table_df.loc[table_df['Contact ID'] == int(request.form['id']), 'Designation'] = request.form['designation']
    table_df.loc[table_df['Contact ID'] == int(request.form['id']), 'Company ID'] = int(request.form['company_id'])
    table_df.loc[table_df['Contact ID'] == int(request.form['id']), 'Company'] = request.form['company_name']
    table_df.loc[table_df['Contact ID'] == int(request.form['id']), 'Email'] = request.form['email']
    table_df.loc[table_df['Contact ID'] == int(request.form['id']), 'Mobile'] = request.form['mobile']
    table_df.to_csv("static/resources/contacts.csv", columns = ['Contact ID', 'Name', 'Designation', 'Company ID', 'Company', 'Email', 'Mobile', 'HelpScout ID'], index = False)
    hs_id = table_df[table_df['Contact ID'] == int(request.form['id'])].values.tolist()[0][7]
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
        "value": request.form['mobile']
    })
    response = requests.get(f"https://api.helpscout.net/v2/customers/{hs_id}/emails", headers = headers)
    email_id = response.json()['_embedded']['emails'][0]['id']
    requests.put(f"https://api.helpscout.net/v2/customers/{hs_id}/emails/{email_id}", headers = headers, json = {
        "type": "work",
        "value": request.form['email']
    })
    return "Contact Change Processed Successfully"

@app.route('/contact/<id>/communication')
def get_contact_comms(id):
    if 'login_email' not in session or 'login_pwd' not in session:
        return redirect(url_for("login"))
    elif session['access_level'] != "admin" and session['access_level'] != "sales":
        abort(403)
    else:
        id = int(id)
        current_dt = datetime.utcnow()
        current_dt = current_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        table_df = pd.read_csv("static/resources/contacts.csv")
        name = table_df[table_df['Contact ID'] == id].values.tolist()[0][1]
        designation = table_df[table_df['Contact ID'] == id].values.tolist()[0][2]
        company = table_df[table_df['Contact ID'] == id].values.tolist()[0][4]
        email = table_df[table_df['Contact ID'] == id].values.tolist()[0][5]
        mobile = table_df[table_df['Contact ID'] == id].values.tolist()[0][6]
        active_response = get_comms(299086, "email", "modifiedAt", "desc", "active", email)["_embedded"]["conversations"]
        closed_response = get_comms(299086, "email", "modifiedAt", "desc", "closed", email)["_embedded"]["conversations"]
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
        phone_comms_df = pd.read_csv("static/resources/phone_comms.csv")
        phone_comms_df = phone_comms_df[phone_comms_df['Contact ID'] == id]
        phone_comms_list = phone_comms_df.values.tolist()
        if len(phone_comms_list) > 0:
            phone_comms_rows_html = ""
            for phone_comm in phone_comms_list:
                phone_comms_rows_html += f"""<tr>
                    <td>{datetime.strptime(phone_comm[3], "%Y-%m-%dT%H:%M").strftime("%d/%m/%Y %I:%M %p")}</td>
                    <td>{datetime.strptime(phone_comm[4], "%Y-%m-%dT%H:%M").strftime("%d/%m/%Y %I:%M %p")}</td>
                    <td>{phone_comm[5]}</td>
                    <td>{phone_comm[6]}</td>
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
        return render_template("view_contact_communication.html", id = id, name = name, designation = designation, email = email, mobile = mobile, company = company, active_response_html = active_response_html, closed_response_html = closed_response_html, phone_comms_html = phone_comms_html)

def get_bearer_token():
    bearer_token = os.getenv('bearer_token')
    bearer_expiry = os.getenv('bearer_expiry')
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
        os.environ["bearer_token"] = bearer_token_new
        os.environ["bearer_expiry"] = bearer_expiry_new
        return bearer_token_new
    else:
        return bearer_token

def get_comms(mailbox, type, sort_by, sort_order, status, email):
    if status == "all":
        url = f'https://api.helpscout.net/v2/conversations?mailbox={mailbox}&type={type}&sortField={sort_by}&sortOrder={sort_order}&query=(email:"{email}")'
    else:
        url = f'https://api.helpscout.net/v2/conversations?mailbox={mailbox}&type={type}&status={status}&sortField={sort_by}&sortOrder={sort_order}&query=(email:"{email}")'
    bearer_token = get_bearer_token()
    headers = {'Authorization': f"Bearer {bearer_token}"}
    response = requests.get(url, headers = headers)
    data = response.json()
    return data

@app.route('/add-company', methods = ['POST'])
def add_company():
    name = request.form['name']
    state = request.form['state']
    website = request.form['website']
    status = request.form['status']
    table_df = pd.read_csv("static/resources/companies.csv")
    matches = (table_df['Company'].str.strip().str.lower() == name.strip().lower()) | (table_df['Website'].str.strip().str.lower() == website.strip().lower())
    if len(table_df[matches].values.tolist()) > 0:
        return "Company Already Added"
    else:
        table_list = table_df.values.tolist()
        if len(table_list) > 0:
            id = table_list[-1][0] + 1
        else:
            id = 1
        table_list.append([id, name, state, website, status])
        table_df = pd.DataFrame(table_list, columns = ['Company ID', 'Company', 'State', 'Website', 'Status'])
        table_df.to_csv("static/resources/companies.csv", index = False)
        return "Company Added Successfully"

@app.route('/add-contact', methods = ['POST'])
def add_contact():
    name = request.form['name']
    designation = request.form['designation']
    company_id = int(request.form['company_id'])
    company = request.form['company_name']
    email = request.form['email']
    mobile = request.form['mobile']
    table_df = pd.read_csv("static/resources/contacts.csv")
    matches = (table_df['Name'].str.strip().str.lower() == name.strip().lower()) | (table_df['Email'].str.strip().str.lower() == email.strip().lower()) | (table_df['Mobile'] == mobile)
    if len(table_df[matches].values.tolist()) > 0:
        return "Contact Already Added"
    else:
        table_list = table_df.values.tolist()
        hs_id = create_contact(name, mobile, email, designation, company)
        if len(table_list) > 0:
            id = table_list[-1][0] + 1
        else:
            id = 1
        table_list.append([id, name, designation, company_id, company, email, mobile, hs_id])
        table_df = pd.DataFrame(table_list, columns = ['Contact ID', 'Name', 'Designation', 'Company ID', 'Company', 'Email', 'Mobile', 'HelpScout ID'])
        table_df.to_csv("static/resources/contacts.csv", index = False)
        return "Contact Added Successfully"

@app.route('/add-phone-comm/<id>', methods = ['POST'])
def add_phone_comm(id):
    id = int(id)
    table_df = pd.read_csv("static/resources/contacts.csv")
    name = table_df[table_df['Contact ID'] == id].values.tolist()[0][1]
    table_df = pd.read_csv("static/resources/phone_comms.csv")
    start_dt = request.form['start_dt']
    end_dt = request.form['end_dt']
    prods = request.form['prods']
    notes = request.form['notes']
    table_list = table_df.values.tolist()
    if len(table_list) > 0:
        comm_id = table_list[-1][0] + 1
    else:
        comm_id = 1
    table_list.append([comm_id, id, name, start_dt, end_dt, prods, notes])
    table_df = pd.DataFrame(table_list, columns = ['Comm ID', 'Contact ID', 'Name', 'Start Date & Time', 'End Date & Time', 'Product(s) Pitched', 'Notes'])
    table_df.to_csv("static/resources/phone_comms.csv", index = False)
    return "Phone Communication Added Successfully"

@app.route('/meetings')
def meetings():
    if 'login_email' not in session or 'login_pwd' not in session:
        return redirect(url_for("login"))
    elif session['access_level'] != "admin" and session['access_level'] != "sales":
        abort(403)
    else:
        table_df = pd.read_csv("static/resources/meetings.csv")
        table = table_df.values.tolist()
        rows_html = ""
        if len(table) > 0:
            for i in range(len(table)):
                rows_html += f"""<tr>
                    <td>{table[i][0]}</td>
                    <td>{table[i][1]}</td>
                    <td>{table[i][3]}</td>
                    <td>{datetime.strptime(table[i][4], "%Y-%m-%dT%H:%M").strftime("%d/%m/%Y %I:%M %p")}</td>
                    <td>{datetime.strptime(table[i][5], "%Y-%m-%dT%H:%M").strftime("%d/%m/%Y %I:%M %p")}</td>
                    <td>{table[i][6]}</td>
                    <td>{table[i][7]}</td>
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

@app.route('/add-meeting', methods = ['POST'])
def add_meeting():
    meeting_type = request.form['meeting_type']
    company_id = int(request.form['company_id'])
    company = request.form['company_name']
    start_dt = request.form['start_dt']
    end_dt = request.form['end_dt']
    prods = request.form['prods']
    agenda = request.form['agenda']
    table_df = pd.read_csv("static/resources/meetings.csv")
    matches = (table_df['Type'] == meeting_type) & (table_df['Company ID'] == company_id) & (table_df['Start Date & Time'] == start_dt) & (table_df['End Date & Time'] == end_dt)
    if len(table_df[matches].values.tolist()) > 0:
        return "Meeting Already Added"
    else:
        table_list = table_df.values.tolist()
        if len(table_list) > 0:
            id = table_list[-1][0] + 1
        else:
            id = 1
        table_list.append([id, meeting_type, company_id, company, start_dt, end_dt, prods, agenda])
        table_df = pd.DataFrame(table_list, columns = ['Meeting ID', 'Type', 'Company ID', 'Company', 'Start Date & Time', 'End Date & Time', 'Product(s) Pitched', 'Agenda'])
        table_df.to_csv("static/resources/meetings.csv", index = False)
        return "Meeting Added Successfully"
    
@app.route('/process-meeting-change', methods = ['POST'])
def process_meeting_change():
    table_df = table_df = pd.read_csv("static/resources/meetings.csv")
    table_df.loc[table_df['Meeting ID'] == int(request.form['id']), 'Type'] = request.form['meeting_type']
    table_df.loc[table_df['Meeting ID'] == int(request.form['id']), 'Company ID'] = int(request.form['company_id'])
    table_df.loc[table_df['Meeting ID'] == int(request.form['id']), 'Company'] = request.form['company_name']
    table_df.loc[table_df['Meeting ID'] == int(request.form['id']), 'Start Date & Time'] = request.form['start_dt']
    table_df.loc[table_df['Meeting ID'] == int(request.form['id']), 'End Date & Time'] = request.form['end_dt']
    table_df.loc[table_df['Meeting ID'] == int(request.form['id']), 'Product(s) Pitched'] = request.form['prods']
    table_df.loc[table_df['Meeting ID'] == int(request.form['id']), 'Agenda'] = request.form['agenda']
    table_df.to_csv("static/resources/meetings.csv", columns = ['Meeting ID', 'Type', 'Company ID', 'Company', 'Start Date & Time', 'End Date & Time', 'Product(s) Pitched', 'Agenda'], index = False)
    return "Meeting Change Processed Successfully"

def create_contact(name, mobile, email, designation, company):
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

@app.route('/reminders')
def reminders():
    if 'login_email' not in session or 'login_pwd' not in session:
        return redirect(url_for("login"))
    elif session['access_level'] != "admin" and session['access_level'] != "sales":
        abort(403)
    else:
        table_df = pd.read_csv("static/resources/reminders.csv")
        table_df = table_df[table_df['Show'] == True].sort_values('Due Date & Time')
        table = table_df.values.tolist()
        rows_html = ""
        if len(table) > 0:
            for i in range(len(table)):
                rows_html += f"""<tr>
                    <td><input id="reminder_check_{table[i][0]}" onchange="check_reminder({table[i][0]})" type="checkbox"></td>
                    <td>{table[i][1]}</td>
                    <td>{table[i][3]}</td>
                    <td>{table[i][5]}</td>
                    <td>{table[i][6]}</td>
                    <td>{datetime.strptime(table[i][7], "%Y-%m-%dT%H:%M").strftime("%d/%m/%Y %I:%M %p")}</td>
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

@app.route('/add-reminder', methods = ['POST'])
def add_reminder():
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

def get_reminder_entries(reminder, start_date, end_date, recurrence, time, company_id, company, contact_id, contact):
    if recurrence == "One Time":
        freq = DAILY
    elif recurrence == 'Weekly':
        freq = WEEKLY
    elif recurrence == 'Monthly':
        freq = MONTHLY
    dates = list(rrule(freq, dtstart = start_date, until = end_date, interval = 1))
    table_df = pd.read_csv("static/resources/reminders.csv")
    for entry in dates:
        matches = (table_df['Reminder'].str.strip().str.lower() == reminder.strip().lower()) & (table_df['Due Date & Time'] == entry)
        if len(table_df[matches].values.tolist()) == 0:
            table_list = table_df.values.tolist()
            if len(table_list) > 0:
                id = table_list[-1][0] + 1
            else:
                id = 1
            due_dt = datetime.combine(entry, time)
            due_dt = due_dt.strftime("%Y-%m-%dT%H:%M")
            table_list.append([id, reminder, company_id, company, contact_id, contact, recurrence, due_dt, True])
            table_df = pd.DataFrame(table_list, columns = ['Reminder ID', 'Reminder', 'Company ID', 'Company', 'Contact ID', 'Contact', 'Recurrence', 'Due Date & Time', 'Show'])
            table_df.to_csv("static/resources/reminders.csv", index = False)
    return None

@app.route('/check-reminder', methods = ['POST'])
def check_reminder():
    id = int(request.form['id'])
    table_df = pd.read_csv("static/resources/reminders.csv")
    table_df.loc[table_df['Reminder ID'] == id, 'Show'] = False
    table_df.to_csv("static/resources/reminders.csv", columns = ["Reminder ID", "Reminder", "Company ID", "Company", "Contact ID", "Contact", "Recurrence", "Due Date & Time", "Show"], index = False)
    return "Reminder Checked"

@app.route('/send-log', methods = ['GET', 'POST'])
def send_log():
    log_id = int(request.form['id'])
    logs_df = pd.read_csv("static/resources/bulk_emails.csv")
    log_row = logs_df[logs_df['Log ID'] == log_id].values.tolist()[0]
    log_name = log_row[1]
    contacts_list_id = log_row[2]
    contacts_list_name = log_row[3]
    prod = log_row[4]
    contacts_to_send = pd.read_csv(f"static/resources/contact_lists/{contacts_list_name}.csv").values.tolist()
    bearer_token = get_bearer_token()
    headers = {'Authorization': f"Bearer {bearer_token}"}
    if len(contacts_to_send) != 0:
        session['email_stopped_at'] = "Not started yet"
        try:
            for contact in contacts_to_send:
                bulk_email_df = pd.read_csv("static/resources/bulk_emails_log.csv")
                bulk_email_list = bulk_email_df.values.tolist()
                if prod == "YGROO.TRAINING":
                    subject = f"Revolutionize L&D with AI-Powered L&DaaS at {contact[6]}"
                    text = f"""Dear {contact[3]},
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
                elif prod == "YGROO.ART":
                    subject = f"Revolutionalise Talent Aqcuisition at {contact[6]} with our AI-Driven Solution"
                    text = f"""Dear {contact[3]},
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
                        "id": contact[9]
                    },
                    "threads": [
                        {
                            "type": "reply",
                            "customer": {
                                "id": contact[9]
                            },
                            "text": text
                        }
                    ],
                    "tags": [log_name.lower(), contacts_list_name.lower(), prod.lower()]
                }
                response = requests.post("https://api.helpscout.net/v2/conversations", headers = headers, json = body)
                conv_id = response.headers['Resource-ID']
                conv_date_sent = response.headers['Date']
                bulk_email_list.append([log_id, log_name, contacts_list_id, contacts_list_name, contact[2], contact[3], contact[4], contact[5], contact[6], prod, pytz.utc.localize(datetime.strptime(conv_date_sent, '%a, %d %b %Y %H:%M:%S %Z')).astimezone(pytz.timezone('Asia/Kolkata')), conv_id, "No", "Not Opened"])
                session['email_stopped_at'] = contact[7]
                bulk_email_df_new = pd.DataFrame(bulk_email_list, columns = ['Log ID', 'Log Name', 'Contacts List ID', 'Contacts List Name', 'Contact ID', 'Contact Name', 'Designation', 'Company ID', 'Company Name', 'Product', 'Date Sent', 'HelpScout ID', 'Opened Status', 'Opened Date & Time'])
                bulk_email_df_new.to_csv("static/resources/bulk_emails_log.csv", index = False)
            record_sent_status = pd.read_csv("static/resources/bulk_emails.csv")
            record_sent_status.loc[record_sent_status['Log ID'] == log_id, 'Sent Status'] = "Yes"
            record_sent_status.to_csv("static/resources/bulk_emails.csv", index = False)
            return "Bulk Emails Sent Out Successfully"
        except:
            print("Log ID:", log_id)
            print("Email Stopped At:", session['email_stopped_at'])
            record_sent_status = pd.read_csv("static/resources/bulk_emails.csv")
            record_sent_status.loc[record_sent_status['Log ID'] == log_id, 'Sent Status'] = "Partial"
            record_sent_status.to_csv("static/resources/bulk_emails.csv", index = False)
            return "Stopped at", session['email_stopped_at']
    else:
        return "No Contacts in List"

@app.route('/contact-lists', methods = ['GET', 'POST'])
def contact_lists():
    if 'login_email' not in session or 'login_pwd' not in session:
        return redirect(url_for("login"))
    elif session['access_level'] != "admin" and session['access_level'] != "sales":
        abort(403)
    else:
        table = pd.read_csv("static/resources/contacts.csv").values.tolist()
        if len(table) != 0:
            rows_html = ""
            for i in range(len(table)):
                rows_html += f"""<tr>
                    <td><input id="list_contact_{table[i][0]}" type="checkbox" value="{table[i][0]}"></td>
                    <td>{table[i][1]}</td>
                    <td>{table[i][2]}</td>
                    <td>{table[i][4]}</td>
                    <td>{table[i][5]}</td>
                    <td>{table[i][6]}</td>
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
        lists_table = pd.read_csv("static/resources/contact_lists.csv").values.tolist()
        if len(lists_table) != 0:    
            rows_lists_html = ""
            for i in range(len(lists_table)):
                rows_lists_html += f"""<tr>
                    <td>{lists_table[i][0]}</td>
                    <td>{lists_table[i][1]}</td>
                    <td><a href="/contact-list/{lists_table[i][0]}"><button class="view_button">View</button></a></td>
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

@app.route('/add-list', methods = ['POST'])
def add_list():
    list_name = request.form['name']
    list_contacts = request.form.getlist('contacts[]')
    lists_df = pd.read_csv("static/resources/contact_lists.csv")
    same_name_found = lists_df['List Name'].str.lower().eq(list_name.lower()).any()
    if same_name_found:
        return "List Already Added"
    else:
        lists_list = lists_df.values.tolist()
        lists_list.append([list(lists_df.shape)[0] + 1, list_name])
        lists_df_new = pd.DataFrame(lists_list, columns = ['List ID', 'List Name'])
        lists_df_new.to_csv("static/resources/contact_lists.csv", index = False)
        contacts_df = pd.read_csv("static/resources/contacts.csv")
        list_to_add = []
        for contact in list_contacts:
            contact_row = contacts_df[contacts_df['Contact ID'] == int(contact)].values.tolist()[0]
            list_to_add.append([list(lists_df.shape)[0] + 1, list_name, contact_row[0], contact_row[1], contact_row[2], contact_row[3], contact_row[4], contact_row[5], contact_row[6], contact_row[7]])
        list_to_add_df = pd.DataFrame(list_to_add, columns = ['List ID', 'Name', 'Contact ID', 'Contact Name', 'Designation', 'Company ID', 'Company', 'Email', 'Mobile', 'HelpScout ID'])
        list_to_add_df.to_csv(f"static/resources/contact_lists/{list_name}.csv", index = False)
        return "List Added Successfully"

@app.route('/contact-list/<id>', methods = ['GET', 'POST'])
def view_contact_list(id):
    if 'login_email' not in session or 'login_pwd' not in session:
        return redirect(url_for("login"))
    elif session['access_level'] != "admin" and session['access_level'] != "sales":
        abort(403)
    else:
        lists_df = pd.read_csv("static/resources/contact_lists.csv")
        list_name = list(lists_df[lists_df['List ID'] == int(id)]['List Name'].unique())[0]
        list_df = pd.read_csv(f"static/resources/contact_lists/{list_name}.csv")
        table = list_df.values.tolist()
        if len(table) != 0:
            rows_html = ""
            for i in range(len(table)):
                rows_html += f"""<tr>
                    <td>{i + 1}</td>
                    <td>{table[i][3]}</td>
                    <td>{table[i][4]}</td>
                    <td>{table[i][6]}</td>
                    <td>{table[i][7]}</td>
                    <td>{table[i][8]}</td>
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
        return render_template("view_contact_list.html", table_html = table_html, list_name = list_name, list_id = int(id))

@app.route('/edit-list/<id>', methods = ['GET', 'POST'])
def edit_list(id):
    if 'login_email' not in session or 'login_pwd' not in session:
        return redirect(url_for("login"))
    elif session['access_level'] != "admin" and session['access_level'] != "sales":
        abort(403)
    else:
        contacts_df = pd.read_csv("static/resources/contacts.csv")
        contacts_list = contacts_df.values.tolist()
        lists_df = pd.read_csv("static/resources/contact_lists.csv")
        list_name = list(lists_df[lists_df['List ID'] == int(id)]['List Name'].unique())[0]
        list_contacts = list(pd.read_csv(f"static/resources/contact_lists/{list_name}.csv")['Contact ID'].unique())
        if len(contacts_list) != 0:
            rows_edit_html = ""
            for i in range(len(contacts_list)):
                rows_edit_html += f"""<tr>
                    <td><input id="edit_list_contact_{contacts_list[i][0]}" value={contacts_list[i][0]} type="checkbox"{" checked" if contacts_list[i][0] in list_contacts else ""}></td>
                    <td>{contacts_list[i][1]}</td>
                    <td>{contacts_list[i][2]}</td>
                    <td>{contacts_list[i][4]}</td>
                    <td>{contacts_list[i][5]}</td>
                    <td>{contacts_list[i][6]}</td>
                </tr>"""
            table_edit_html = f"""<table class="table table-responsive">
                <tr>
                    <th></th>
                    <th>Contact Name</th>
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

@app.route('/save-edit-list', methods = ['POST'])
def save_edit_list():
    list_id = int(request.form['id'])
    list_name = request.form['name']
    list_contacts = request.form.getlist("contacts[]")
    lists_df = pd.read_csv("static/resources/contact_lists.csv")
    if list_name in list(lists_df[lists_df['List ID'] != list_id]['List Name'].unique()):
        return "List Already Added"
    else:
        list_contacts_df = pd.read_csv(f"static/resources/contact_lists/{list_name}.csv")
        lists_df.loc[lists_df['List ID'] == list_id, 'List Name'] = list_name
        lists_df.to_csv("static/resources/contact_lists.csv", index = False)
        list_contacts_df['Name'] = list_name
        list_contacts_list = []
        contacts_df = pd.read_csv("static/resources/contacts.csv")
        for contact in list_contacts:
            contact_row = contacts_df[contacts_df['Contact ID'] == int(contact)].values.tolist()[0]
            list_contacts_list.append([list_id, list_name, contact_row[0], contact_row[1], contact_row[2], contact_row[3], contact_row[4], contact_row[5], contact_row[6], contact_row[7]])
        list_contacts_df_new = pd.DataFrame(list_contacts_list, columns = ['List ID', 'Name', 'Contact ID', 'Contact Name', 'Designation', 'Company ID', 'Company', 'Email', 'Mobile', 'HelpScout ID'])
        list_contacts_df_new.to_csv(f"static/resources/contact_lists/{list_name}.csv", index = False)
        return "List Edited Successfully"

@app.route('/bulk-email-log', methods = ['GET', 'POST'])
def bulk_email():
    if 'login_email' not in session or 'login_pwd' not in session:
        return redirect(url_for("login"))
    else:
        bulk_emails_list = pd.read_csv("static/resources/bulk_emails.csv").values.tolist()
        if len(bulk_emails_list) != 0:
            rows_html = ""
            for row in bulk_emails_list:
                if row[5] == "No":
                    sent_status = f"""<button class="edit_button" id="send_log_button_{row[0]}" type="button" onclick="send_log({row[0]}, send_log_button_{row[0]})">Send</button>"""
                elif row[5] == "Yes":
                    sent_status = f"""<button class="disabled_button" id="send_log_button_{row[0]}" type="button" onclick="send_log({row[0]}, send_log_button_{row[0]})" disabled>Sent</button>"""
                elif row[5] == "Partial":
                    sent_status = f"""<button class="disabled_button" id="send_log_button_{row[0]}" type="button" onclick="send_log({row[0]}, send_log_button_{row[0]})" disabled>Partially Sent</button>"""
                rows_html += f"""<tr>
                    <td>{row[0]}</td>
                    <td>{row[1]}</td>
                    <td>{row[3]}</td>
                    <td>{row[4]}</td>
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
        dropdown_options = pd.read_csv("static/resources/contact_lists.csv")[['List ID', 'List Name']].values.tolist()
        dropdown_options_html = ""
        for option in dropdown_options:
            dropdown_options_html += f"<option value='{option[0]}'>{option[1]}</option>"
        if os.getenv("last_opened_check_dt"):
            lodt = f"Checked at {os.getenv('ast_opened_check_dt')}"
        else:
            lodt = "Not Checked"
    return render_template("bulk_email.html", access_level = session['access_level'], dropdown_options_html = dropdown_options_html, table_html = table_html, lodt = lodt)

@app.route('/bulk-email-opened-status', methods = ['GET', 'POST'])
def bulk_email_opened_status():
    bearer_token = get_bearer_token()
    headers = {'Authorization': f"Bearer {bearer_token}"}
    bulk_email_df = pd.read_csv("static/resources/bulk_emails_log.csv")
    bulk_email_df = bulk_email_df[bulk_email_df['Opened Status'] == "No"]
    bulk_email_list = bulk_email_df.values.tolist()
    if len(bulk_email_list) != 0:
        session['check_stopped_at'] = "Not started yet"
        try:
            for row in bulk_email_list:
                response = requests.get(f"https://api.helpscout.net/v2/conversations/{str(row[11])}?embed=threads", headers = headers)
                if "openedAt" in response.json()['_embedded']['threads'][0]:
                    opened_dt = response.json()['_embedded']['threads'][0]['openedAt']
                    opened_dt = datetime.strptime(opened_dt, "%Y-%m-%dT%H:%M:%SZ")
                    opened_dt = opened_dt.replace(tzinfo = timezone.utc).astimezone(timezone(timedelta(hours = 5, minutes = 30)))
                    row[12] = "Yes"
                    row[13] = opened_dt
                    session['check_stopped_at'] = row[9]
            bulk_email_df_new = pd.DataFrame(bulk_email_list, columns = ['Log ID', 'Log Name', 'Contacts List ID', 'Contacts List Name', 'Contact ID', 'Contact Name', 'Designation', 'Company ID', 'Company Name', 'Product', 'Date Sent', 'HelpScout ID', 'Opened Status', 'Opened Date & Time'])
            os.environ['last_opened_status_checked'] = str(datetime.now(pytz.timezone('Asia/Kolkata')))
            print(os.getenv('last_opened_status_checked'))
            os.environ['check_type'] = "complete"
            bulk_email_df_new.to_csv("static/resources/bulk_emails_log.csv", index = False)
            message = "Opened Status Checked Successfully"
        except Exception as e:
            print(e)
            bulk_email_df_new = pd.DataFrame(bulk_email_list, columns = ['Log ID', 'Log Name', 'Contacts List ID', 'Contacts List Name', 'Contact ID', 'Contact Name', 'Designation', 'Company ID', 'Company Name', 'Product', 'Date Sent', 'HelpScout ID', 'Opened Status', 'Opened Date & Time'])
            os.environ['last_opened_status_checked'] = str(datetime.now(pytz.timezone('Asia/Kolkata')))
            print(os.getenv('last_opened_status_checked'))
            os.environ['check_type'] = "partial"
            bulk_email_df_new.to_csv("static/resources/bulk_emails_log.csv", index = False)
            print("HelpScout ID:", str(row[11]))
            print("Email Stopped At:", session['check_stopped_at'])
            message = f"Stopped at {session['check_stopped_at']}"
    else:
        message = "No Bulk Emails Sent Out"
        os.environ['last_opened_status_checked'] = str(datetime.now(pytz.timezone('Asia/Kolkata')))
        print(os.getenv('last_opened_status_checked'))
    log_df = pd.read_csv("static/resources/bulk_emails_log.csv")
    opened_df = log_df[log_df['Opened Status'] == "Yes"].sort_values('Opened Date & Time', ascending = False)
    closed_df = log_df[log_df['Opened Status'] == "No"].sort_values('Date Sent', ascending = True)
    opened_list = opened_df.values.tolist()
    closed_list = closed_df.values.tolist()
    opened_rows_html = ""
    closed_rows_html = ""
    if len(opened_list) != 0:
        for i in range(len(opened_list)):
            opened_rows_html += f"""<tr>
                <td>{i + 1}</td>
                <td>{opened_list[i][1]}</td>
                <td>{opened_list[i][3]}</td>
                <td>{opened_list[i][5]}</td>
                <td>{opened_list[i][6]}</td>
                <td>{opened_list[i][8]}</td>
                <td>{opened_list[i][9]}</td>
                <td>{str(datetime.strptime(opened_list[i][10], "%Y-%m-%d %H:%M:%S%z").strftime("%d/%m/%Y %I:%M %p"))}</td>
                <td>{str(datetime.strptime(opened_list[i][13], "%Y-%m-%d %H:%M:%S%z").strftime("%d/%m/%Y %I:%M %p"))}</td>
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
    if len(closed_list) != 0:
        for i in range(len(closed_list)):
            closed_rows_html += f"""<tr>
                <td>{i + 1}</td>
                <td>{closed_list[i][1]}</td>
                <td>{closed_list[i][3]}</td>
                <td>{closed_list[i][5]}</td>
                <td>{closed_list[i][6]}</td>
                <td>{closed_list[i][8]}</td>
                <td>{closed_list[i][9]}</td>
                <td>{str(datetime.strptime(opened_list[i][10], "%Y-%m-%d %H:%M:%S%z").strftime("%d/%m/%Y %I:%M %p"))}</td>
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
    last_checked = f"Last checked at {str(datetime.strptime(os.getenv('last_opened_status_checked'), '%Y-%m-%d %H:%M:%S.%f%z').strftime('%d/%m/%Y %I:%M %p'))} ({os.getenv('check_type')})"
    return render_template("view_bulk_email.html", last_checked = last_checked, opened_table_html = opened_table_html, closed_table_html = closed_table_html, message = message)

@app.route('/add-bulk-email-log', methods = ['GET', 'POST'])
def add_bulk_email_log():
    log_name = request.form['name']
    product = request.form['product']
    log_list_id = request.form['list_id']
    log_list_name = request.form['list_name']
    bulk_email_df = pd.read_csv("static/resources/bulk_emails.csv")
    same_name_found = bulk_email_df['Log Name'].str.lower().eq(log_name.lower()).any()
    if same_name_found:
        return "Bulk Email Log Already Added"
    else:
        bulk_email_list = bulk_email_df.values.tolist()
        bulk_email_list.append([len(bulk_email_list) + 1, log_name, log_list_id, log_list_name, product, "No"])
        bulk_email_df_new = pd.DataFrame(bulk_email_list, columns = ['Log ID', 'Log Name', 'Contacts List ID', 'Contacts List Name', 'Product', 'Sent Status'])
        bulk_email_df_new.to_csv("static/resources/bulk_emails.csv", index = False)
        return "Bulk Email Log Added Successfully"

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
    users_df = pd.read_csv("static/resources/users.csv")
    if email in users_df['Email'].values:
        correct_pwd = list(users_df[users_df["Email"] == email]['Password'].unique())[0]
        if pwd != correct_pwd:
            return "Incorrect Password"
        else:
            session['login_email'] = email
            session['login_pwd'] = pwd
            session['access_level'] = list(users_df[users_df["Email"] == email]['Access Level'].unique())[0]
            return "Logged In"
    else:
        return "Not Registered"

@app.route("/logout", methods = ['GET', 'POST'])
def logout():
    session.pop('login_email', default = None)
    session.pop('login_pwd', default = None)
    session.pop('access_level', default = None)
    return "Logged Out Successfully"