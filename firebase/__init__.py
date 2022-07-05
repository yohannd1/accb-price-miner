import time
import re
import collections
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import date
import database
from tabulate import tabulate

def get_methods(object, spacing=20):
  methodList = []
  for method_name in dir(object):
    try:
        if callable(getattr(object, method_name)):
            methodList.append(str(method_name))
    except Exception:
        methodList.append(str(method_name))
  processFunc = (lambda s: ' '.join(s.split())) or (lambda s: s)
  for method in methodList:
    try:
        print(str(method.ljust(spacing)) + ' ' +
              processFunc(str(getattr(object, method).__doc__)[0:90]))
    except Exception:
        print(method.ljust(spacing) + ' ' + ' getattr() failed')


def print_tab(df):

    """Printa um set de dados iteráveis de forma organizada e tabulada no console."""
    print(tabulate(df, headers="keys", tablefmt="psql"))

def save_search(search):

	with open('search.json', 'w+') as f:
			f.write(json.dumps(search, sort_keys=True, indent=4))

class Firebase:

	def __init__(self):

		cred = credentials.Certificate('./firebaseConfig.json')
		firebase_admin.initialize_app(cred)
		self.db = firestore.client()
		self.local_db = database.Database()
		self.db = self.db.collection(u"searches")
		# self.send_search_all()]
		self.test_get_search()

	def test_get_search(self):

		today = date.today()
		self.date_id = f"{today.month}-{today.year}"
		result = self.get_searches_by_date(self.date_id).to_dict()
		# Pesquisa não encontrada
		if(isinstance(result, list) or result is None):
			return False

		for cep in result:
			print("+---------------------------------------")
			print("+ " + cep + ":")
			print("+---------------------------------------")
			if(isinstance(result[cep], list)):
				for item in result[cep]:
					print_tab(json.loads(item))
			else:
				print_tab(json.loads(result[cep]))
			time.sleep(10)

	def send_search_all(self):

		searches = self.local_db.db_get_search(where="done", value="1");

		today = date.today()
		self.date_id = f"{today.month}-{today.year}"
		searches = [item for item in searches if "-".join(item[3].split("-")[1:]) != self.date_id]

		if(len(searches) == 0):

			return False

		result = self.db.document(self.date_id).get()

		if(isinstance(result, list)):

			search_info = {
				'date': self.date_id
			}
			self.add_search(self.date_id, search_info)

			for search in searches:
				items = self.local_db.db_get_search_item(search[0])
				items = self.format_daily_search(items)
				self.add_daily_search(items)

		else:

			for search in searches:
				items = self.local_db.db_get_search_item(search[0])
				items = self.format_daily_search(items)
				self.add_daily_search(items)

	def format_daily_search(self, search):

			# (1, 'BANANA PRATA KG', 'SUPERMERCADOS COMPRE AQUI', 'DOS CAPUCHINHOS 238 NOSSA SENHORA DA CONCEI O 45605260, ITABUNA', 'R$ 6,99', 'BANANA DA PRATA')
			new_search = {}
			for item in search:

				id , name, store, address, price, keyword = item
				pattern = re.compile(r"45\d{3}", re.IGNORECASE)
				cep = re.findall(pattern, address)[0]

				if(cep in new_search):
					new_search[cep].append({
					"id": str(id) if str(id) != None else "",
					"name": str(name) if str(name) != None else "",
					"store": str(store) if str(store) != None else "",
					"address": str(address) if str(address) != None else "",
					"price": str(price) if str(price) != None else "",
					"keyword": str(keyword) if str(keyword) != None else ""
				})
				else:
					new_search[cep] = []
					new_search[cep].append({
						"id": str(id) if str(id) != None else "",
						"name": str(name) if str(name) != None else "",
						"store": str(store) if str(store) != None else "",
						"address": str(address) if str(address) != None else "",
						"price": str(price) if str(price) != None else "",
						"keyword": str(keyword) if str(keyword) != None else ""
					})

			return collections.OrderedDict(sorted(new_search.items()))

	def add_search(self, date, search):

		ref = self.db.collection(u'searches')
		ref.document(date).set(search)

	def remove_search(self, date):

		ref = self.db.collection(u'searches')
		ref.document(date).delete()

	def get_searches(self):

		ref = self.db.collection(u'searches')
		return ref.get()

	def add_daily_search(self, daily_search):

		save_search(daily_search)
		res = self.db.document(f"{self.date_id}")
		for search in daily_search:
			try:
				res.update({search: firestore.ArrayUnion([json.dumps(daily_search[search])])})
			except:
				res.set({search: [json.dumps(daily_search[search])]})

	def get_searches_by_date(self, date):

		return self.db.document(date).get()


fire = Firebase()
