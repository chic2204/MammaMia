import requests
from bs4 import BeautifulSoup,SoupStrainer
import re
import time
from info import is_movie,get_info_imdb,get_info_tmdb
import config
TF_FAST_SEARCH = config.TF_FAST_SEARCH
TF_DOMAIN = config.TF_DOMAIN


##FOR NOW ONLY MOVIES WORK, I HOPE I CAN FIX SERIES
def search(showname,ismovie,date):
    url = f'https://www.tanti.bond/search/{showname}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")
    if ismovie == 1:
        all_link = soup.select('#movies .col .list-media')
        for link in all_link:
            url = link['href']
            response = requests.get(url)
            pattern = r'Data di rilascio\s*</div>\s*<div class="text">\s*(\d{4})\s*</div>'
            found_date = re.search(pattern, response.text)
            release_date = str(found_date.group(1))
            if release_date == date:
                tid= url.split('-')[-1]
                #Return URL and even the soup so I can use it later
                #I try to get doodstream link inside this function so I do not have to get again the response
                return tid,url
    elif ismovie == 0: 
        all_link = soup.select('#series .col .list-media')
        for link in all_link:
            base_url = link['href']
            url = f'{base_url}-1-season-1-episode'
            response = requests.get(url)
            pattern = r'Data di rilascio\s*</div>\s*<div class="text">\s*(\d{4})\s*</div>'
            found_date = re.search(pattern, response.text)
            release_date = str(found_date.group(1))
            if release_date == date:
                tid= url.split('-')[1]
                soup = BeautifulSoup(response.text, 'lxml')
                a_tag = soup.find('a', class_='dropdown-toggle btn-service selected')
                embed_id = a_tag['data-embed']
                #I try to get doodstream link inside this function so I do not have to get again the response
                return url,embed_id
            
def fast_search(showname,ismovie):
    url = f'https://www.tanti.bond/search/{showname}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")
    if ismovie == 1:
        first_link = soup.select_one('#movies .col .list-media')
        url = first_link['href']
        tid= url.split('-')[1]
        return tid,url
    elif ismovie == 0: 
        first_link = soup.select_one('#series .col .list-media')
        base_url = first_link['href']
        url = f'{base_url}-1-season-1-episode'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        a_tag = soup.find('a', class_='dropdown-toggle btn-service selected')
        embed_id = a_tag['data-embed']
        return url,embed_id



def get_protect_link(id,url):
        #Get the link where the Iframe is located, which contains the doodstream url kind of. 
        response = requests.get(f"https://p.hdplayer.casa/myadmin/play.php?id={id}")
        soup = BeautifulSoup(response.text, "lxml", parse_only=SoupStrainer('iframe'))
        protect_link = soup.iframe['src'] 
        if "protect" in protect_link:
            return  protect_link
        else:
            #DO this in case the movie has  a 3D version etc
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'lxml')
            a_tag = soup.find('a', class_='dropdown-toggle btn-service selected')
            embed_id = a_tag['data-embed']
            headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Referer': url
            }
            #Parameters needed is the embed ID
            data = {
            'id': embed_id
            }
            ajax_url = "https://www.tanti.bond/ajax/embed"
            response = requests.post(ajax_url, headers=headers, data=data)
            hdplayer = response.text[43:-27]
            response = requests.get(hdplayer)
            soup = BeautifulSoup(response.text, 'lxml')
            links_dict = {}
            li_tags = soup.select('ul.nav.navbar-nav li.dropdown')
            for li_tag in li_tags:
                a_tag = li_tag.find('a')
                if a_tag:
                    title = a_tag.text.strip() 
                    #Since tantifilm player is broken I just skip it
                    if title == "1" or "Tantifilm" in title:
                        continue # Get the text of the <a> tag
                    href = a_tag['href']  
                    response = requests.get(href)
                    soup = BeautifulSoup(response.text, "lxml", parse_only=SoupStrainer('iframe'))
                    protect_link = soup.iframe['src'] 
                    if "protect" in protect_link:
                        url = true_url(protect_link)
                        links_dict[title] = url
            return  links_dict
                         # Get the value of the href attribute
                    

def get_nuovo_indirizzo_and_protect_link(url,embed_id,season,episode):
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Referer': url
    }
    #Parameters needed is the embed ID
    data = {
    'id': embed_id
}
    ajax_url = "https://www.tanti.bond/ajax/embed"
    response = requests.post(ajax_url, headers=headers, data=data)
    nuovo_indirizzo = response.text[43:-27]
    response = requests.get(nuovo_indirizzo)
    soup = BeautifulSoup(response.text, 'lxml')
    #Get season
    season = season - 1
    li_tags = soup.select('ul.nav.navbar-nav > li.dropdown')
    if len(li_tags) != 1:
        link = li_tags[season].find('a')['href']
        response = requests.get(link)
        soup = BeautifulSoup(response.text, 'lxml')
        option_tag = soup.select(f'select[name="ep_select"] > option:nth-of-type({episode})')[0]
        link = option_tag['value']
        #Let's find protect link now
        response = requests.get(link)
        soup = BeautifulSoup(response.text, "lxml", parse_only=SoupStrainer('iframe'))
        protect_link = soup.iframe['src'] 
        return  protect_link

    else:
        #If there is only one season than 
        option_tag = soup.select('select.dynamic_select > option')[episode]
        link = option_tag['value']
        #Let's find protect link now
        response = requests.get(link)
        soup = BeautifulSoup(response.text, "lxml", parse_only=SoupStrainer('iframe'))
        protect_link = soup.iframe['src'] 
        return  protect_link


def true_url(protect_link):
    print(protect_link)
    # Define headers
    headers = {
        "Range": "bytes=0-",
        "Referer": "https://d000d.com/",
    }
    response = requests.get(protect_link)
    link = response.url
    #Get the ID
    doodstream_id = link.rsplit('/e/', 1)[-1]
    # Make a GET request
    
    if response.status_code == 200:
        # Get unique timestamp for the request      
        real_time = str(int(time.time()))

        # Regular Expression Pattern for the match
        pattern = r"(\/pass_md5\/.*?)'.*(\?token=.*?expiry=)"
        
        # Find the match 
        match = re.search(pattern, response.text, re.DOTALL)

        # If a match was found
        if match:
            # Create real link (match[0] includes all matched elements)
            url =f'https://d000d.com{match[1]}'
            rebobo = requests.get(url, headers=headers)
            real_url = f'{rebobo.text}123456789{match[2]}{real_time}'
            print(real_url)
            return real_url
        else:
            print("No match found in the text.")
            return None
  
    print("Error: Could not get the response.")
    return None




#Get temporaly ID
def tantifilm(imdb):
    urls = None
    try:
        general = is_movie(imdb)
        ismovie = general[0]
        imdb_id = general[1]
        type = "Tuttifilm"
        if ismovie == 0 : 
            season = int(general[2])
            episode = int(general[3])
            if "tt" in imdb:
                if TF_FAST_SEARCH == "0":
                    showname,date = get_info_imdb(imdb_id,ismovie,type)
                    url,embed_id = search(showname,ismovie,date)
                elif TF_FAST_SEARCH == "1":
                    showname = get_info_imdb(imdb_id,ismovie,type)
                    url,embed_id = fast_search(showname,ismovie)
            else:
                    #else just equals them
                    tmdba = imdb_id.replace("tmdb:","")
                    if TF_FAST_SEARCH == "0":
                        showname,date = get_info_tmdb(tmdba,ismovie,type)
                        url,embed_id = search(showname,ismovie,date)
                    elif TF_FAST_SEARCH == "1":
                        showname= get_info_tmdb(tmdba,ismovie,type)
                        url,embed_id = fast_search(showname,ismovie)
            protect_link = get_nuovo_indirizzo_and_protect_link(url,embed_id,season,episode)
            url = true_url(protect_link)
            return url
        elif ismovie == 1:
            if "tt" in imdb:
                #Get showname
                    if TF_FAST_SEARCH == "0":
                        showname,date = get_info_imdb(imdb_id,ismovie,type)
                        tid,url = search(showname,ismovie,date)
                    elif TF_FAST_SEARCH == "1":
                        showname = get_info_imdb(imdb_id,ismovie,type)
                        date = None
                        tid,url = fast_search(showname,ismovie)
            else:
            
                #else just equals themtantifilm("tt2096673")

                if TF_FAST_SEARCH == "0":
                    showname,date = get_info_tmdb(imdb,ismovie,type)
                    tid,url = search(showname,ismovie,date)
                elif TF_FAST_SEARCH == "1":
                    showname = get_info_tmdb(imdb,ismovie,type)
                    tid,url = fast_search(showname,ismovie)
            protect_link = get_protect_link(tid,url)
            if not isinstance(protect_link, str):
                urls = protect_link
                return urls
            url = true_url(protect_link)
            return url

    except Exception as e:
        if urls or url == None:
            print("Tantifilm Error")