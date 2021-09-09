import os
import json
import time
from datetime import datetime , timedelta
import re
import pandas as pd

import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen

def matching_cat(cat) :
#     print('matching_cat :',cat)
    ## outer, top, bottom, skirt, dress, others
    res = ''
    if cat == 'OUTWEAR' :
        res = 'outer'
    if cat == 'KNIT&CARDICAN' :
        res = 'top'
    if cat == 'TOP' :
        res = 'top'
    if cat == 'DRESS' :
        res = 'dress'
    if cat == 'SLIP ' :
        res = 'others'
    if cat == 'BOTTOM' :
        res = 'bottom'
        
    return res

def brand_match(brand,brandlist) :
#     print('brand_match :',brand)
    if any(brandlist.iloc[:,1].str.contains(brand)) :
        brand_matching = brandlist.iloc[:,0][brandlist.iloc[:,1].str.contains(brand).tolist().index(True)]
    elif any(brandlist.iloc[:,2].str.contains(brand)) :
        brand_matching = brandlist.iloc[:,0][brandlist.iloc[:,2].str.contains(brand).tolist().index(True)]
    elif any(brandlist.iloc[:,3].str.contains(brand)) :
        brand_matching = brandlist.iloc[:,0][brandlist.iloc[:,3].str.contains(brand).tolist().index(True)]
    elif any(brandlist.iloc[:,4].str.contains(brand)) :
        brand_matching = brandlist.iloc[:,0][brandlist.iloc[:,4].str.contains(brand).tolist().index(True)]
    else :
        brand_matching = 'etc'
    
    return brand_matching

def get_size(text,split_string) :
#     print('get_size :',text)
    text=text.replace(split_string,'').split(' ')
    text=[i for i in text if i!='']
    
    size = {}
    for i,s in enumerate(text) :
        if i%2==0 :
            size[s] = 0 
            key = s
        else :
            size[key] = s
            
    if '가슴' in size.keys() :
        size['chest'] = size.pop('가슴')
    if '허리' in size.keys() :
        size['waist'] = size.pop('허리')
            
    for i in list(size.keys()) :
        if (i!='chest') and (i!='waist') :
            del size[i]
        else :
            try :
                size[i] = str(size[i])
            except :
                del size[i]
    
    return size


def main() :

    brandlist=pd.read_csv('brandlist.csv',keep_default_na=False)
    storeName = '탐나다'
    main_url = 'https://tamnada.co.kr'

    cats = {'women_OUTWEAR' : ['https://tamnada.co.kr/product/list.html?cate_no=24&page=',9],
            'women_KNIT&CARDICAN' : ['https://tamnada.co.kr/product/list.html?cate_no=26&page=',12],
            'women_TOP' : ['https://tamnada.co.kr/product/list.html?cate_no=27&page=',63],
            'women_DRESS' : ['https://tamnada.co.kr/product/list.html?cate_no=68&page=',16],
            'women_SLIP' : ['https://tamnada.co.kr/product/list.html?cate_no=368&page=',10],
            'women_BOTTOM' : ['https://tamnada.co.kr/product/list.html?cate_no=42&page=',24],

            'men_OUTWEAR' : ['https://tamnada.co.kr/product/list.html?cate_no=111&page=',6],
            'men_KNIT&CARDICAN' : ['https://tamnada.co.kr/product/list.html?cate_no=60&page=',5],
            'men_TOP' : ['https://tamnada.co.kr/product/list.html?cate_no=49&page=',40],
            'men_BOTTOM' : ['https://tamnada.co.kr/product/list.html?cate_no=332&page=',11] 
           }

    print(cats,'\n','len(cats) :',len(cats))


    start = time.time()
    n_files = 1
    for c in range(len(cats)) : 
        cat = list(cats.keys())[c]
        pages = list(cats.values())[c][1]
        pages = list(range(1,pages+1))  

        if not os.path.exists('/'.join([storeName,cat])) :
                os.makedirs('/'.join([storeName,cat]), exist_ok=True)   

        cat_start = time.time()
        n_iter = 1
        for p in pages : 
            url = list(cats.values())[c][0] + str(p)
            html = urlopen(url)
            soup = bs(html, "html.parser")
            urls = soup.select('#info > div.description > strong') # items
            isSoldOuts = soup.select('#itsp1 > ul > li')
            isSoldOuts = [True if isSoldOuts[i].select('.promotion')[0].find('img') is not None else False for i in range(len(urls))]

            print('item count : ',len(urls))
            n = 1
            page_start = time.time()
            for u in range(len(urls)) : 
                item = main_url + urls[u].find('a').attrs['href']
                html = urlopen(item)
                soup = bs(html, "html.parser")

                name = str(soup.select('.name')[0])
                name = name[(name.find('<h3 class="name">')+len('<h3 class="name">')):].replace('<br/>',' ').replace('</h3>','')
                # storeName
                category = matching_cat(cat.split('_')[1])
                gender = cat.split('_')[0]
                brand = soup.select('.cont')[0].text
                brand = re.search(r'브랜드 :(.*?)컨디션 :', brand).group(1).replace(" ","").lower()
                brand = ''.join(filter(str.isalnum, brand)) 
                brand = brand_match(brand,brandlist)
                originalPrice = soup.select('#span_product_price_text')[0].text
                originalPrice = str(''.join(re.findall('\d+', originalPrice)))
                salePrice = soup.select('#span_product_price_sale')[0].text
                salePrice = salePrice[:salePrice.find('(')]
                salePrice = str(''.join(re.findall('\d+', salePrice)))
                thumbnailUrl = '#contents > div.xans-element-.xans-product.xans-product-detail > div.detailArea > div.xans-element-.xans-product.xans-product-image.imgArea > div.imginfo > div.keyImg > div > img'
                thumbnailUrl = 'https:' + soup.select(thumbnailUrl)[0].attrs['src']
                contentUrl = item
                isSoldOut = isSoldOuts[u]
                sizes = soup.select('.cont')[0].text
                sizes = re.search(r'실측길이(.*?)권장사이즈', sizes).group(1).replace("( cm ) ","")
                size = get_size(sizes,':')


                result = {
                            "name":name,
                            "storeName":storeName,
                            "category":category,
                            "gender":gender,
                            "brand":brand,
                            "originalPrice":originalPrice,
                            "salePrice":salePrice,
                            "thumbnailUrl":thumbnailUrl,
                            "contentUrl":contentUrl,
                            "isSoldOut":isSoldOut,
                            "size":size
                            }

                file_name='/'.join([storeName,cat,'page'+str(p)+'_'+str(n)+'.json'])
                with open(file_name, "w") as json_file:
                    json.dump(result, json_file)

#                 print('----- ',f' files : {n_files} , {cat} {n_iter}th  pages : {p}/{pages[-1]}')
#                 print(result)
#                 print()
                if n%50 == 0 :
                    print()
                    print('----- ',f' files : {n_files} , {cat} {n_iter}th  pages : {p}/{pages[-1]}')
                    print(result)
                    page_run_time = timedelta(seconds=time.time() - page_start)
                    print('Average - runtime : ',page_run_time.seconds/n,' seconds')
                    print('category run time : ', "{:0>8}".format(str(timedelta(seconds=time.time() - cat_start))))
                    print('Total run time : ', "{:0>8}".format(str(timedelta(seconds=time.time() - start))))
                    print()

                n_files += 1
                n+=1
                n_iter +=1

#                 time.sleep(0.1)

        print(f'------------ END : {cat}')
        print('category run time : ', "{:0>8}".format(str(timedelta(seconds=time.time() - cat_start))))


    print('\n','Total run time : ', "{:0>8}".format(str(timedelta(seconds=time.time() - start))))
    print('END !!!!!!!!!!!!!!')

    
if __name__ == '__main__' :
    main()




















