import requests
from bs4 import BeautifulSoup
from time import sleep

import json

URLS =	{
			"1": "http://omsk-meteo.ru/templates/my/phpj/informer/AjaxInformer.php",
			"2": "https://pogoda.mail.ru/prognoz/noyabrsk/24hours/",
		}

HEADERS =	{
				"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0",
		   		"accept": "*/*",
			}
#парс погоды омска, тюмени, хма
def get_weather_omsk_tumen_hm(city: str) -> tuple:
	"""Возвращает кортеж со словарём с данными о погоде"""
	KEYS_HTML = {"omsk": ("info_omsk_data", 1), "tumen": ("info_tumen_data", 2), 
				 "hm":("info_xmao_data", 3)}
	#если введён неправильный город
	try:
		tag_city = KEYS_HTML[city.strip()]
	except:
		return (dict(), False, "Ошибка названия города")
	
	response = requests.get(URLS["1"], headers=HEADERS)
	soup = BeautifulSoup(response.text, "lxml").find(id=tag_city[0])
	#если сайт ещё не загрузил данные, то он возвращает None
	if soup is None:
		return (dict(), False, "Сайт ещё не загрузил данные")

	params, weathers = ["temp", "humi", "pres", "wind", "prec"], dict()
	for param, shift in zip(params, range(5, 11)):
		#скипаем 9 индекс(он не нужен)
		if shift == 9:
			shift += 1
		#бывает, что некоторых параметров просто нету, поэтому try-except
		try:
			weathers[param] = soup.find(id=f"info_city{tag_city[1]}_{shift}").text.strip().split()
			#разбрасываем параметры по тегам некоторые имеют особенности
			if param == "temp": 
				weathers[param] = weathers[param][0]
			elif param == "prec": 
				weathers[param] = " ".join(weathers[param][1:])
			else: 
				weathers[param] = weathers[param][1]
		except:
			weathers[param] = None
	#если все параметры None, то у нас проблема(((9
	if any(map(lambda val: False if val is None else True, weathers.values())):
		return (weathers, True)
	return (dict(), False, "Ошибка парсинга")

#парс погоды ноябрьска
def get_weather_noyabrsk() -> tuple:
	"""Возвращает кортеж со словарём с данными о погоде"""
	response = requests.get(URLS["2"], headers=HEADERS)
	soup = BeautifulSoup(response.text, "lxml").find("div", class_="p-forecast__current")
	result = [item.text for item in soup.find_all("span")]
	weathers =	{
					"temp": result[2].split('°')[0],
					"humi": result[18].split('%')[0],
					"pres": result[11].split()[0],
					"wind": result[13].split()[0],
					"prec": result[3].capitalize()
				}
	if any(map(lambda val: False if val is None else True, weathers.values())):
		return (weathers, True)
	return (dict(), False, "Ошибка парсинга")

def json_packager(data: dict, filename: str) -> None:
	"""запихивает список словарей с инфой погоды в json"""
	with open(filename, 'w', encoding="utf-8") as file:
		json.dump(data, fp=file, indent=3, ensure_ascii=False)

def beautiful_print(data: list) -> None:
	"""Выводит данные о всех 4-ёх городах в наглядном виде"""
	translate = {
					"params":	{
									"temp": "Температура", "humi": "Влажность", 
									"pres": "Давление", "wind": "Скорость ветра", 
				 					"prec": "Погода",
				 				},
					"cities":	{
				 					"omsk": "Омске",
				 					"tumen": "Тюмени",
				 					"hm": "Ханты-Мансийске",
				 					"noyabrsk": "Ноябрьске",
				 				}
				 }
	for city, pack in data.items():
		print(f"Погода в {translate['cities'][city]}")
		for key, value in pack[0].items():
			if value is None:
				print(f"\t{translate['params'][key]}: Нет данных")
			elif key == "temp":
				print(f"\t{translate['params'][key]}: {value} °C")
			elif key == "humi":
				print(f"\t{translate['params'][key]}: {value} %")
			elif key == "pres":
				print(f"\t{translate['params'][key]}: {value} мм р. с.")
			elif key == "wind":
				print(f"\t{translate['params'][key]}: {value} м/с")
			elif key == "prec":
				print(f"\t{translate['params'][key]}: {value}\n")


#проверка парсера
if __name__ == "__main__":
	result = dict()
	cities_parser1 = ["omsk", "tumen", "hm"]
	city_parser2 = "noyabrsk"

	for city in cities_parser1:
		result.setdefault(city, get_weather_omsk_tumen_hm(city))
		sleep(1)
	result.setdefault(city_parser2, get_weather_noyabrsk())
	beautiful_print(result)
	json_packager(data=result, filename="parse_data.json")
