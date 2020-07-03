import json
import os
import re
import requests
from bs4 import BeautifulSoup
import sys

wiki_article_base_url = 'https://en.wikipedia.org/wiki/%s'
google_search_base_url = 'https://www.google.com/search?q=%s'

help_msg = 'Usage:\n %s [city name] [city id]\n%s [city name] [city id] [latitude] [longitude]' % (
    os.path.basename(sys.argv[0]), os.path.basename(sys.argv[0]))


def _deg_tude_to_float(tude: str):
    multiplier = 1 if tude[-1] in ['N', 'E'] else -1
    tude = tude.replace('°', '-').replace('′', '-').replace('″', '-')
    return multiplier * sum(float(x) / 60 ** n for n, x in enumerate(tude[:-2].split('-')))


def _float_letter_tude_to_sign(tude):
    multiplier = 1 if tude[-1] in ['N', 'E'] else -1
    return multiplier * float(tude.replace(' ', '')[:-1])


def _no_conversion(tude):
    return float(tude)


geodata_regex = {
    'deg_min_sec': ('^\d\d?\d?°\d?\d?′?\d?\d?″?[NEWS]', _deg_tude_to_float),
    'float_letter': ('^\d\d?\d?\.?\d*[NEWS]', _float_letter_tude_to_sign),
    'float_sign': ('^-?\d\d?\d?\.?\d*', _no_conversion)
}

wiki_classes = {

}


def _convert_tude(tude):
    for regex in geodata_regex.keys():
        if re.match(geodata_regex[regex][0], tude) is not None:
            return geodata_regex[regex][1](tude)
    raise KeyError('Wrong coordinates formatting. Use one of following:\n'
                   '1°0′0″S 1°0′0″E\n'
                   '1.0000S 1.0000E\n'
                   '-1.0000 1.0000')


def _get_soup(url):
    page = requests.get(url)
    return BeautifulSoup(page.content, 'html.parser')


def get_city_data(name, coords=None):
    soup = _get_soup(wiki_article_base_url % name)
    geoloc = (soup.find(class_='latitude').text.replace(' ', ''), soup.find(class_='longitude').text.replace(' ', ''))

    result = {
        'name_de': None,
        'name_es': None,
        'name_fr': None,
        'name_ru': None,
        'name_zh': None,
        'elevation': None,  #
        'population': None,  #
        'year_of_survey': None,  #
        'year_of_city_founding': None,
        'city_url': None,
        'area': None,
        'region': None
    }

    population_check = False

    geodata_raw = soup.find(class_='infobox geography vcard')
    rows = geodata_raw.find('tbody').findAll('tr')
    for line in rows:
        header = line.find('th')
        if header is not None:
            if 'Elevation' in header.text:
                result['elevation'] = line.find('td').text
            elif 'Population' in header.text:
                try:
                    result['year_of_survey'] = re.search('\(.*?(\d\d\d\d).*?\)', header.text).group(1)
                except AttributeError:
                    pass
                result['population'] = int(max(re.findall(
                    '.*?(\d*).*?', rows[list(rows).index(line) + 1].find('td').text.replace(',', ''))))
            elif 'Country' in header.text:
                row = rows[list(rows).index(line) + 1]
                result.pop('region')
                result[row.find('th').text.lower()] = row.find('td').text
            elif 'Website' in header.text:
                result["city_url"] = line.find('td').text.lower()
            elif 'Settled' in header.text or 'Founded' in header.text:
                result['year_of_city_founding'] = line.find('td').text
            elif 'Area' in header.text:
                row = rows[list(rows).index(line) + 1]
                result['area'] = row.find('td').text if 'km' in row.find('td').text or 'mi' in row.find('td').text \
                    else result['area']

    print(json.dumps(result, indent=4))

    # print(geodata_raw)
    # print(geodata_raw.find(class_='td', string=lambda text: re.match('(\d*ft)? ?\(?\d*m\)?', text)))


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] in ['help', 'h']:
        print(help_msg)
    try:
        if len(sys.argv) == 2:
            get_city_data(sys.argv[1])
        elif len(sys.argv) == 4:
            get_city_data(sys.argv[1], (sys.argv[2], sys.argv[3]))
    except IndexError:
        print(help_msg, file=sys.stderr)
