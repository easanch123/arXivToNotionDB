import requests
import urllib.request as libreq
import feedparser
import re
import json
from datetime import datetime
import keys

# Base URLs
notion_url = 'https://api.notion.com' 
arxiv_url = 'http://export.arxiv.org/api'
scholar_url = 'https://api.semanticscholar.org'

breaking_words = ['n', 'no', 'exit', 'q', 'quit']
detailed_error = True

class NotionPapers:
	def __init__(self):
		self.post_url = notion_url + '/v1/pages/'
		self.id = keys.PAPER_DB_ID
		self.headers = {"Authorization": keys.INTEGRATION_TOKEN, "Content-Type": "application/json", "Notion-Version":"2021-07-27"}

	def appendNewPaper(self, code):
		authors, title, references = get_paper_info(code)
		data = {"parent": { "database_id": self.id },"properties": obtain_props(code, title, authors, references)}
		data = json.dumps(data)
		self.res = requests.request("POST", self.post_url, headers=self.headers, data=data)

def get_paper_info (paper_code):
    # receives the code of a arxiv paper
    # returns a list of authors, the title of the paper, and a list of references
    authors = []
    title = ''
    references = []
    with libreq.urlopen('http://export.arxiv.org/api/query?search_query=id:' + paper_code) as arxiv_res:
        paper_info = feedparser.parse(arxiv_res.read())
        try:
            authors = paper_info.entries[0].authors 
            title = paper_info.entries[0].title
        except:
        	print ("***Error: Couldn't get authors and title***")

    with libreq.urlopen('https://api.semanticscholar.org/v1/paper/arXiv:' + paper_code) as sch_res:
    	str_res = str(sch_res.read())
    	start = end = re.search(r'"references":', str_res).span()[1]
    	string = str_res[start:]
    	bracket = 0
    	for char in string:
    		end += 1
    		if char == '[':
    			bracket += 1
    		elif char == ']':
    			bracket -= 1
    			if bracket == 0:
    				break
    	references = get_reference_titles(string[:end])
    return authors, title, references

def get_reference_titles (reference_data):
    # receives a long string with reference data
    # returns an array tailored for notion's multiselect
    
    references = []
    for detail in reference_data.split(','):
        if "title" in detail:
            ref = detail.split(':')[1][1:-1]
            if len(ref) >= 100:
                ref = ref[:98]
            references.append({"name": ref})
    return references

def obtain_props(code, title, authors, references):
	return {"Name": {
				"title": [{"text": {"content": title}}]},
			"Authors": {
				"multi_select": authors},
			"Tags": {
				"multi_select": []},
			"References": {
				"multi_select": references},
			"Link": {
				"url": f"https://arxiv.org/pdf/{code}.pdf" },
			"Discovered": {
				"created_time": {"start": datetime.now().isoformat()}},
			"Last analysis": {
				"last_edited_time": {"start": datetime.now().isoformat()}},
			"Published": {
				"date": {"start": datetime.now().isoformat()}},
			"Keywords": {
				"rich_text": [{"text": {"content": ""}}]},
			"Category": {
				"select": { "name": "Paper"}}
			}

def main():
	notion_db = NotionPapers()
	code = str(input("Enter the code of a paper in arXiv: "))
	while code.lower() not in breaking_words:
		notion_db.appendNewPaper(code)
		if notion_db.res.status_code != 200:
			print ("Paper could not be added to your Notion database")
			if detailed_error:
				print (notion_db.res.content)
		code = str(input("Enter the code of a paper in arXiv: "))

if __name__ == '__main__':
	main()