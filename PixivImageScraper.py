import bs4
import sys
import urllib.request, urllib.error, urllib.parse
import http.client
from socket import error as SocketError
import ssl
import os.path
import argparse
import multiprocessing as mp
import datetime
import pickle as pickle
import plyvel
import re
import json
import random
import signal
import concurrent.futures
import time
from multiprocessing import Process
SEED_EXIST          = True
SEED_NO_EXIST       = False
# set default state to scrape web pages in Amazon Kindle
def makeCookie(name, value):
    import http.cookiejar
    return http.cookiejar.Cookie(
        version=0, 
        name=name, 
        value=value,
        port=None, 
        port_specified=False,
        domain="kahdev.bur.st", 
        domain_specified=True, 
        domain_initial_dot=False,
        path="/", 
        path_specified=True,
        secure=False,
        expires=None,
        discard=False,
        comment=None,
        comment_url=None,
        rest=None
    )
def html_adhoc_fetcher(url):
  """ 
  標準のアクセス回数はRETRY_NUMで定義されている 
  """
  html = None
  retrys = [i for i in range(2)]
  for _ in retrys :
    import http.cookiejar, random
    jar = http.cookiejar.CookieJar()
    jar.set_cookie(makeCookie("session-token", ""))
    jar.set_cookie(makeCookie("PHPSESSID", "374f0bb5f7425c4c75f3c7cd0123689a"))
    ses_rand = round(random.random())
    if ses_rand == 0:
      jar.set_cookie(makeCookie("PHPSESSID", "5994399_b2be5341b1a9b7c34088e962b697a261"))
    else:
      jar.set_cookie(makeCookie("PHPSESSID", "5994399_79083e004df24ff1c4224888c65b60be"))
    headers = {"Accept-Language": "en-US,en;q=0.5","User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Referer": "http://thewebsite.com","Connection": "keep-alive" } 
    request = urllib.request.Request(url=url, headers=headers)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    _TIME_OUT = 5.
    try:
      html = opener.open(request, timeout = _TIME_OUT).read()
    except Exception as e:
      print(e)
      continue
    break
  if html == None:
      return (None, None, None)

  soup = bs4.BeautifulSoup(html, "html.parser")
  title = (lambda x:str(x.string) if x != None else 'Untitled')(soup.title )
  return (html, title, soup)

def exit_gracefully(signum, frame):
  signal.signal(signal.SIGINT, original_sigint)
  try:
    if input("\nReally quit? (y/n)> ").lower().startswith('y'):
      sys.exit(1)
  except KeyboardInterrupt:
    print("Ok ok, quitting")
    sys.exit(1)
  signal.signal(signal.SIGINT, exit_gracefully)


"""
内側の画像を取得して保存用
"""
def parse_img(url, imgurl, tagname):
  import urllib.request, urllib.parse, urllib.error, random
  import http.cookiejar
  jar = http.cookiejar.CookieJar()
  jar.set_cookie(makeCookie("device_token", "08a49c60aaeb60e12623e7ba23b31e22"))
  jar.set_cookie(makeCookie("PHPSESSID", "5994399_b2be5341b1a9b7c34088e962b697a261"))
  ses_rand = int(random.random()*2 )

  if ses_rand == 0:
    jar.set_cookie(makeCookie("PHPSESSID", "5994399_b2be5341b1a9b7c34088e962b697a261"))
  else:
    jar.set_cookie(makeCookie("PHPSESSID", "5994399_79083e004df24ff1c4224888c65b60be"))

  headers = {"Accept-Language": "en-US,en;q=0.5","User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Referer": "http://thewebsite.com","Connection": "keep-alive"  } 
  request = urllib.request.Request(url=imgurl, headers=headers)
  request.add_header('Referer', url)
  opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

  """ illsut id """
  linker = re.search(r"(illust_id=\d{1,})", url).group(1)
  for _ in range(20):
    n = 1024*1024
    try:
      con = opener.open(request).read(n)
    except  urllib.error.HTTPError as e:
      continue
    if len(con) == 0:
      print("ゼロエラーです", imgurl)
      continue
    open('imgs/' + linker + '.jpg', 'wb').write(con)
    open('metas/{}.json'.format(linker), "w").write( json.dumps({'linker':linker + '.jpg', 'tags': tagname, 'url':url, 'imgurl':imgurl }) )
    print("発見した画像", tagname, url, imgurl)
    break

"""
スパイダー部分、エントロピーがいくらでも上がるので、実装には気をつけないと行けない
"""
def analyzing(url):
  _links = set()
  html, title, soup = html_adhoc_fetcher(url)
  if soup == None:
    print('bs4がギブアップしました', url)
    return None

  tags = soup.find_all('a')
  tags_save = []
  for tag in tags:
    urllocal = tag.get('href')
    if urllocal != None and '/tags.php?tag=' in urllocal:
      urlparam = urllocal.split('=').pop()
      decode_urlparam = urllib.parse.unquote(urlparam)
      tags_save.append(decode_urlparam)
  
  for imgurl in [x for x in [img.get('src') for img in  soup.find_all('img')] if x!=None]:
    if '600x600' not in imgurl:
      continue
    parse_img(url, imgurl,','.join(tags_save))
  
  tags = soup.find_all('a')
  for tag in tags:
    urllocal = tag.get('href')
    if urllocal != None and '/tags.php?tag=' in urllocal:
      fullurl = 'http://www.pixiv.net/' + urllocal
      _links.add(fullurl)
          
    if urllocal != None and '/search.php?word=' in urllocal:
      fullurl = 'http://www.pixiv.net/' + urllocal
      _links.add(fullurl)
    
    if urllocal != None and '/member_illust.php?' in urllocal:
      if 'http://' not in urllocal:
        fullurl = 'http://www.pixiv.net/' + urllocal
      else:
        fullurl = urllocal
      _links.add(fullurl)
  return (url, _links)

if __name__ == '__main__':
  # store the original SIGINT handler
  original_sigint = signal.getsignal(signal.SIGINT)
  signal.signal(signal.SIGINT, exit_gracefully)

  parser = argparse.ArgumentParser(description='Process Kindle Referenced Index Score.')
  parser.add_argument('--URL', help='set default URL which to scrape at first')
  parser.add_argument('--depth', help='how number of url this program will scrape')
  parser.add_argument('--mode', help='you can specify mode...')
  parser.add_argument('--refresh', help='create snapshot(true|false)')
  parser.add_argument('--file', help='input filespath')
  parser.add_argument('--active', help='spcific active thread number')

  args_obj = vars(parser.parse_args())

  depth = (lambda x:int(x) if x else 10)( args_obj.get('depth') )
  
  mode = (lambda x:x if x else 'undefined')( args_obj.get('mode') )

  refresh    = (lambda x:False if x=='false' else True)( args_obj.get('refresh') )

  active    = (lambda x:15 if x==None else int(x) )( args_obj.get('active') )

  filename = args_obj.get('file')

  if mode == 'scrape' or mode == 'level':
    db = plyvel.DB('pixiv_htmls', create_if_missing=True)
    """
    SnapshotDealデーモンが出力するデータをもとにスクレイピングを行う
    NOTE: SQLの全アクセスは非常に動作コストが高く、推奨されない
    NOTE: Snapshotが何もない場合、initialize_parse_and_map_data_to_local_dbを呼び出して初期化を行う
    """
    seed = "http://www.pixiv.net/member_illust.php?mode=medium&illust_id=60675452" 
   
   
    def save_links(links):
      """ 一応 pickleで保存　"""
      open("links.pkl", "wb").write( pickle.dumps(links) )
  
    try:
      links = pickle.loads(open("links.pkl", "rb").read())
      links.add( seed )
    except FileNotFoundError as e:
      print(e)
      links = set([seed])
      
    while links != set():
      try:
        with concurrent.futures.ProcessPoolExecutor(max_workers=250) as executor:
          for url_links in executor.map(analyzing, links):
            if url_links is None:
              continue
            """ leveldbに終わったリンクを保存 """
            url, _links = url_links
            db.put(bytes(url, "utf8"), bytes("finish", "utf8"))

            """ 終わったリンクを破棄 """
            links.remove(url)
            """ linksバッファーをアップデート """
            for _link in _links:
              if db.get(bytes(_link, "utf8")) is None:
                links.add(_link)
          
            """ 非同期保存 """
        p = Process(target=save_links, args=(links,))
        p.start()
      except urllib.error.URLError as e:
        """ DNSがおかしくなるとこの例外が起きるらしい """
        print(e)
        time.sleep(2.)
        


