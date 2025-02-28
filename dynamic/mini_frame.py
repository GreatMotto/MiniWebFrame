# -*- coding: utf-8 -*-
import re
from pymysql import connect
import urllib.parse
import logging

"""
URL_FUNC_DICT = {
    "/index.html": index,
    "/center.html": center
}
"""

URL_FUNC_DICT = dict()


def route(url):
    def set_func(func):
        # URL_FUNC_DICT["/index.py"] = index
        URL_FUNC_DICT[url] = func

        def call_func(*args, **kwargs):
            return func(*args, **kwargs)

        return call_func

    return set_func


@route(r"/index.html")
def index(ret):
    with open("./templates/index.html", encoding="utf-8") as f:
        content = f.read()
    # my_stock_info = "从MySQL查出来主页数据。。。"
    # content = re.sub(r"\{%content%\}", my_stock_info, content)
    # 创建Connection连接
    conn = connect(host='localhost', port=3306, user='root', password='mysql', database='stock_db', charset='utf8')
    # 获得Cursor对象
    cs = conn.cursor()

    sql = """select * from info;"""
    cs.execute(sql)
    stock_infos = cs.fetchall()

    cs.close()
    conn.close()

    tr_template = """
    <tr>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>%s</td>
        <td>
            <input type="button" value="添加" id="toAdd" name="toAdd" systemidvaule="%s">
        </td>
    </tr>
    
    """

    html = ""
    for line_info in stock_infos:
        html += tr_template % (
            line_info[0], line_info[1], line_info[2], line_info[3], line_info[4], line_info[5], line_info[6],
            line_info[7], line_info[1])

    content = re.sub(r"\{%content%\}", html, content)

    return content


@route(r"/center.html")
def center(ret):
    with open("./templates/center.html", encoding="utf-8") as f:
        content = f.read()

        # my_stock_info = "从MySQL查出来个人中心数据。。。"
        # content = re.sub(r"\{%content%\}", my_stock_info, content)

        # 创建Connection连接
        conn = connect(host='localhost', port=3306, user='root', password='mysql', database='stock_db', charset='utf8')
        # 获得Cursor对象
        cs = conn.cursor()

        sql = """select i.code,i.short,i.chg,i.turnover,i.price,i.highs,f.note_info from info as i inner join focus as f on i.id=f.info_id;"""
        cs.execute(sql)
        stock_infos = cs.fetchall()

        cs.close()
        conn.close()

        tr_template = """
        <tr>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>
                <a type="button" class="btn btn-default btn-xs" href="/update/%s.html"> <span class="glyphicon glyphicon-star" aria-hidden="true"></span> 修改 </a>
            </td>
            <td>
                <input type="button" value="删除" id="toDel" name="toDel" systemidvaule="%s">
            </td>
        </tr>

        """

        html = ""
        for line_info in stock_infos:
            html += tr_template % (
                line_info[0], line_info[1], line_info[2], line_info[3], line_info[4], line_info[5], line_info[6],
                line_info[0], line_info[0])

        content = re.sub(r"\{%content%\}", html, content)

    return content


# 给路由添加正则表达式的原因：在实际开发时，url中往往会带有很多参数，例如/add/000007.html中000007就是参数，
# 如果没有正则的话，那么就需要编写N次@route来进行添加 url对应的函数 到字典中，此时字典中的键值对有N个，浪费空间
# 而采用了正则的话，那么只要编写1次@route就可以完成多个 url例如/add/00007.html /add/000036.html等对应同一个函数，此时字典中的键值对个数会少很多
@route(r"/add/(\d+)\.html")
def add_focus(ret):
    # 获取股票代码
    stock_code = ret.group(1)
    # '''
    # 判断是否有这个股票
    # 创建Connection连接
    conn = connect(host='localhost', port=3306, user='root', password='mysql', database='stock_db', charset='utf8')
    # 获得Cursor对象
    cs = conn.cursor()

    sql = """select * from info where code=%s;"""

    cs.execute(sql, (stock_code,))
    if not cs.fetchall():
        cs.close()
        conn.close()
        return "非法请求，股票代码不存在。。。"

    # 判断以下是否已经关注过
    sql = """select * from info as i inner join focus as f on i.id=f.info_id where i.code=%s;"""
    cs.execute(sql, (stock_code,))
    # 如果查出来了，那么表示已经关注过
    if cs.fetchall():
        cs.close()
        conn.close()
        return "已经关注过，请勿重复关注。。。"

    # 添加关注
    sql = """insert into focus (info_id) select id from info where code=%s;"""
    cs.execute(sql, (stock_code,))
    conn.commit()
    cs.close()
    conn.close()
    # '''
    return "关注成功 %s" % stock_code


@route(r"/del/(\d+)\.html")
def del_focus(ret):
    # 获取股票代码
    stock_code = ret.group(1)
    # '''
    # 判断是否有这个股票
    # 创建Connection连接
    conn = connect(host='localhost', port=3306, user='root', password='mysql', database='stock_db', charset='utf8')
    # 获得Cursor对象
    cs = conn.cursor()

    sql = """select * from info where code=%s;"""

    cs.execute(sql, (stock_code,))
    if not cs.fetchone():
        cs.close()
        conn.close()
        return "非法请求，股票代码不存在。。。"

    # 判断以下是否已经关注过
    sql = """select * from info as i inner join focus as f on i.id=f.info_id where i.code=%s;"""
    cs.execute(sql, (stock_code,))
    # 如果没有关注过，表示非法请求
    if not cs.fetchone():
        cs.close()
        conn.close()
        return "删除未关注的股票，非法请求。。。"

    # 取消关注
    sql = """delete from focus where info_id = (select id from info where code=%s);"""
    cs.execute(sql, (stock_code,))
    conn.commit()
    cs.close()
    conn.close()
    # '''
    return "取消关注成功 %s" % stock_code


@route(r"/update/(\d+)\.html")
def show_update_page(ret):
    """显示修改页面"""
    # 获取估计代码
    stock_code = ret.group(1)

    # 打开模板
    with open("./templates/update.html", encoding="utf-8") as f:
        content = f.read()

    # 根据股票代码查询相关备注信息
    # 创建Connection连接
    conn = connect(host='localhost', port=3306, user='root', password='mysql', database='stock_db', charset='utf8')
    # 获得Cursor对象
    cs = conn.cursor()

    sql = """select f.note_info from focus as f inner join info as i on f.info_id=i.id where i.code=%s;"""
    cs.execute(sql, (stock_code,))
    stock_infos = cs.fetchone()
    note_info = stock_infos[0]

    cs.close()
    conn.close()

    content = re.sub(r"\{%code%\}", stock_code, content)
    content = re.sub(r"\{%note_info%\}", note_info, content)

    return content


@route(r"/update/(\d+)/(.*)\.html")
def save_update_page(ret):
    """保存修改的信息"""
    stock_code = ret.group(1)
    comment = urllib.parse.unquote(ret.group(2))
    # 创建Connection连接
    conn = connect(host='localhost', port=3306, user='root', password='mysql', database='stock_db', charset='utf8')
    # 获得Cursor对象
    cs = conn.cursor()

    sql = """update focus set note_info=%s where info_id = (select id from info where code=%s);"""
    cs.execute(sql, (comment, stock_code))
    conn.commit()

    cs.close()
    conn.close()

    return """修改成功。。。"""


def application(env, start_response):
    start_response("200 OK", [("Content-Type", "text/html;charset=utf-8")])

    file_name = env["PATH_INFO"]
    # file_name = "/index.py"

    logging.basicConfig(level=logging.INFO,
                        filename='./log.txt',
                        filemode='a',
                        format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

    logging.info("Visited is: %s" % file_name)

    try:
        # return URL_FUNC_DICT[file_name]()
        for url, func in URL_FUNC_DICT.items():
            ret = re.match(url, file_name)
            if ret:
                return func(ret)
        else:
            logging.warning("no corresponding function...")
            return "请求的url(%s)没有对应的函数...." % file_name
    except Exception as e:
        return "产生了异常：%s" % str(e)
