from flask import Flask, request, render_template

import requests
import sendgrid
from pymongo import MongoClient

import os
import json

app = Flask(__name__)
app.debug = True

sg = sendgrid.SendGridClient(os.environ.get("SG_USER"), os.environ.get("SG_PASSWORD"))

client = MongoClient(os.environ.get("MONGOHQ_URL"))
db = client['hackpr']
coll = db['etsy']

etsy_api_key = os.environ.get("ETSY_API_KEY")

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
	if request.method == "GET":
		return render_template('register.html')
	elif request.method == "POST":
		user = {
			'name': request.form['name'],
			'email': request.form['email']
		}
		coll.insert(user)
		return render_template('index.html')

@app.route('/listings/<keywords>')
def listings(keywords):
	# Get Etsy suggestions
	r = requests.get("https://openapi.etsy.com/v2/listings/active?api_key=%s&limit=15&keywords=%s" % (etsy_api_key, keywords))
	results = r.json()['results']
	suggestions = []
	for result in results:
		image = requests.get("https://openapi.etsy.com/v2/listings/%s/images?api_key=%s" % (result['listing_id'], etsy_api_key))
		suggestions.append({
			"title": result['title'],
			"description": result['description'],
			"url": result['url'],
			"image": image.json()['results'][0]['url_170x135']
		})
	# prepare sendgrid email
	email_html_body = render_template('email.html', suggestions=suggestions)
	message = sendgrid.Mail()
	message.set_subject("Holiday Reminder!")
	message.set_from("Christian Rodriguez <christian.etpr10@gmail.com>")
	message.set_html(email_html_body)
	# Add list of users
	to_list = []
	for user in coll.find():
		to_list.append("%s <%s>" % (user['name'], user['email']))
	message.add_to(to_list)
	# Send email and print results
	status, msg = sg.send(message)
	print status
	print msg
	return msg

if __name__ == '__main__':
	app.run()