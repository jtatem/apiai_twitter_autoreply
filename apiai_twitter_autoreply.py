import twitter
import time
import apiai
import json
import sys
import os
import random

# Load configs

execfile('./apiai_twitter_autoreply.conf')

def logwrite(s):
  timestamp = time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time()))
  f = open(logfile, 'a')
  if s[-1] != '\n':
    s += '\n'
  if s[0] != ' ':
    s = ' ' + s
  s = timestamp + s
  f.write(s)
  f.close()
  return None


def get_mentions(sinceId=None, maxcount=200):
  api = twitter.Api(consumer_key=consumer_key, consumer_secret=consumer_secret, access_token_key=access_key, access_token_secret=access_secret, input_encoding=None)
  try:
    result = api.GetMentions(since_id=sinceId, count=maxcount)
    return result
  except:
    logwrite('Error when grabbing recent @ mentions: {}'.format(sys.exc_info()))
    return []

def ai_text_req(reqstr):
  ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN, SUBSCRIPTION_KEY)
  request = ai.text_request()
  request.lang = 'en'
  request.query=reqstr
  response = request.getresponse()
  return json.loads(response.read())

def post_ai(message, replytoid=None):
  try:
    if replytoid is not None:
      api = twitter.Api(consumer_key=consumer_key, consumer_secret=consumer_secret, access_token_key=access_key, access_token_secret=access_secret, input_encoding=None)
      status = api.PostUpdate(message, in_reply_to_status_id=replytoid)
    return status.GetId()
  except:
    return None

def post_reply(reqstr, requsr, replytoid):
  logwrite('Sending request to api.ai with text: {}'.format(reqstr))
  airesp = ai_text_req(reqstr)
  resptxt = airesp['result']['fulfillment']['speech']
  if resptxt == '':
    logwrite('Empty response from api.ai for text "{}", falling back to a default response'.format(reqstr)) 
    resptxt = random.choice(fallbackresplist)
  post_str = '@{} {}'.format(requsr, resptxt)
  logwrite('Posting in reply to {} with text: {}'.format(requsr, resptxt))
  return post_ai(post_str, replytoid)


if __name__ == '__main__':
  logwrite('Starting up')
  if os.path.exists(lastidfile):
    f = open(lastidfile, 'r')
    last_id = int(f.read().rstrip())
    f.close()
    logwrite('Last ID file found.  Starting from ID {}'.format(last_id))
  else:
    last_id = None
    logwrite('No last ID file found, starting from the beginning')
  try:
    while True:
      logwrite('Getting recent @ mentions')
      statuslist = get_mentions(sinceId=last_id)
      logwrite('Got {} @ mentions'.format(len(statuslist)))
      for i in range(len(statuslist) - 1, -1, -1):
        post_user = statuslist[i].user.screen_name
        post_id = statuslist[i].id
        last_id = post_id
        post_text = statuslist[i].text.replace('@' + twitter_screen_name, '')
        if post_user not in ignorelist:
          logwrite('Found post ID {} from user {} with text: {}'.format(post_id, post_user, post_text))
          post_reply(post_text, post_user, post_id)     
        else:
          logwrite('Ignoring post ID {} from user {}'.format(post_id, post_user))     
      f = open(lastidfile, 'w')
      f.write(str(last_id) + '\n')
      f.close()
      time.sleep(check_interval)
  except KeyboardInterrupt:
    logwrite('Keyboard interrupt received, shutting down')

