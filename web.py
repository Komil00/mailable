from flask import Flask, request, Response, send_file
import json
import requests
import re
import database
import re
def strip_script_tags(page_source: str) -> str:
    pattern = re.compile(r'\s?on\w+="[^"]+"\s?')
    result = re.sub(pattern, "", page_source)
    pattern2 = re.compile(r'<script[\s\S]+?/script>')
    result = re.sub(pattern2, "", result)
    return result
  
app = Flask(__name__)
@app.route('/')
def index():
    return send_file("web/index.html")

@app.route('/404')
def error_page():
    return send_file("web/404.html")

@app.route('/assets/<asset>')
def assets(asset):
    return send_file(f"assets/{asset}")

@app.route('/arc-sw.js')
def arc():
    return send_file("arc-sw.js")

@app.route('/favicon.ico')
def ico():
    return send_file("web/static/images/favicon.ico")

@app.route('/i.png')
def im():
    return send_file("i.png")

@app.route('/<id>', methods=['GET'])
def pages(id):
    print(id)
    url = f"https://paste.theostrich.eu.org/api/documents/{id}"
    req = requests.get(url)
    res = json.loads(req.text)
    content = res['result']['content']
    nojs = strip_script_tags(content)

    styles = '''    <style>
    
  
      body {
        
        font-family: sans-serif;
        -webkit-font-smoothing: antialiased;
        font-size: 14px;
        line-height: 1.4;
        -webkit-text-size-adjust: 100%; 
      }



      .body {
        
        width: 100%; 
      }

      a {
        color: #3498db;
        text-decoration: none; 
      }


.header{
width:100%;
height:80px;
display:block;
background-color:#101010;
}
.header img{
max-width:100%;
max-height:100%;
margin-left:10px;
}
.inner_header{
width:1000px;
height:100%;
display:flex;
margin:-80px;
margin-left:70px;
}
.logo_container{
height:100%;
display:table;
float:left;
}
.logo_container h1{
color:white;
height:100%;
display:table-cell;
vertical-align:middle;
font-family:'Montserrat';
font-size:32px;
font-weight:200;
}
.logo_container h1 span{
font-weight:800;
}
.navigation{
position: absolute;
right: 150px;
float:right;
height:100%;
margin-left:100px;
}
.navigation a{
height:50px;
display:table;
float:left;
padding:0px 10px;
}
.navigation a:last-child{
padding-right:0px;
}
.navigation a li{
display:table-cell;
vertical-align:middle;
height:100%;
color:white;
font-family:'Montserrat';
font-size:16px;
}
.site-nav-icon {
    height: 15px;
    margin: -5px 0 0;
}



    </style>'''
    tag = '''
<header>

<div Class="header">
<img src="i.png"/>
<div Class="inner_header">
<div Class="logo_container">
<h1>THE<span>OSTRICH</span></h1>
</div>
</header>

'''
    meta = '''<meta name="viewport" content="width=device-width, initial-scale=1.0">\
<link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.0.7/css/all.css">
'''
    return meta + tag + nojs + styles + "<script async src=\"https://arc.io/widget.min.js#cen231VF\"></script>"




  
def run():
    app.run(host="0.0.0.0", port=8080)
