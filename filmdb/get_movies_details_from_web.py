import requests
from bs4 import BeautifulSoup


def get_image_url_and_synopsis_by_title(title):
    if title == 'M*A*S*H (1970)':
        title = 'MASH (1970)'

    image_url = None
    url = 'https://www.whatismymovie.com/results?text=' + title
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'lxml')

    for raw_img in soup.find_all('img'):
        link = raw_img.get('src')
        if 'images' in link:
            image_url = 'https://www.whatismymovie.com/' + link
            break

    plot = soup.find_all("div", {"class": "plot-box"})
    metadata = soup.find_all("div", {"class": "metascore"})
    synopsis = None

    if plot:
        if metadata:
            synopsis = plot[0].text.replace(metadata[0].text, '')
        else:
            synopsis = plot[0].text
    return image_url, synopsis
