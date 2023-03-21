import argparse
from mastodon import Mastodon
import html2text
import openai
import os

# setup bot
openai.api_key = '...'

# Set up Mastodon
mastodon = Mastodon(
    access_token = '...',
    api_base_url = '...'
)

# record bot id
my_id = ..

# deal with mentions
def iterate_through():

	# grab the last mention notification id
	lastnotificationid = ...
	with open ("chatbot_checkpoints.txt", 'r') as f:
		for line in f:
			lastnotificationid = max(lastnotificationid,int(line.split(", ")[0]))
	# id of the last notification. Note the queue is FILO

	# grab all noficiations since last one, mentions only
	notifications = mastodon.notifications(since_id=lastnotificationid,mentions_only=True)

	print("Total notifications"+str(len(notifications))+
		", starting from chkpt",str(lastnotificationid))

	for post in notifications:
		with open("chatbot_checkpoints.txt", "a") as f:
			f.write(str(post['id']) + ', ' + post['type'] + '\n')
		# skip other notifications	
		if post['type']!='mention':
			continue

		# get input text
		h=html2text.HTML2Text()
		h.ignore_links = True
    # remove html from string. Also remove @bot 
		inputtext = h.handle(post["status"]["content"]).replace("@bot","").strip("\n")
    
    # set up chatgpt context
		messages = [{"role": "system", "content": ""},]	
		token_counter = 0 # count limit context token length: too expensive to onboard long conversation

		# load context
		if post['status']['in_reply_to_id']:
			context_dict = [[x["account"]["id"], h.handle(x["content"]).replace("@words","").strip("\n")] 
					for x in mastodon.status_context(post['status']['id'])['ancestors']]
			for d in context_dict:
				if d[0]!=my_id:
          # record user's toot as user
					messages.append({"role": "user", "content": d[1]},)
				else:
          # record bot's toot as assistant
					messages.append({"role": "assistant", "content": d[1]},)
			token_counter += len(d[1])

		# don't load too much, if context is too long, just refresh
		if token_counter > 4000:
			messages = [{"role": "system", "content": ""},]	

		messages.append({"role": "user", "content": inputtext},)
		chat_completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
		# get the reply
		reply = chat_completion.choices[0].message.content
		mastodon.status_reply(post['status'],reply)

if __name__ == "__main__":
	iterate_through()




