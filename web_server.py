# -*- coding: utf-8 -*-
import socket
import re
import multiprocessing
import sys


class WSGIServer:
    def __init__(self, port, app, static_path):
        # 创建套接字
        self.tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 绑定端口
        self.tcp_server_socket.bind(("", port))
        # 添加监听
        self.tcp_server_socket.listen(128)

        self.application = app
        self.static_path = static_path

    def service_client(self, new_socket):
        """为这个客户端返回数据"""
        # 接受浏览器发送的请求
        # GET / HTTP/1.1
        # ......
        request = new_socket.recv(1024).decode("utf-8")
        # print(request)

        request_lines = request.splitlines()
        print("")
        print(">" * 20)
        print(request_lines)

        file_name = ""
        ret = re.match(r"[^/]+(/[^ ]*)", request_lines[0])
        if ret:
            file_name = ret.group(1)
            if file_name == "/":
                file_name = "/index.html"

        # 返回http格式的数据，给浏览器
        # 如果请求的资源不是以.html结尾，那么就认为是静态资源（css/js/png/jpg等）
        if not file_name.endswith(".html"):
            try:
                f = open(self.static_path + file_name, "rb")
            except Exception as e:
                response = "HTTP/1.1 404 NOT FOUND\r\n"
                response += "\r\n"
                response += "----file not found----"
                new_socket.send(response.encode("utf-8"))
                print(e)
            else:
                html_content = f.read()
                f.close()

                # 准备发送给浏览器的数据---header
                response = "HTTP/1.1 200 OK\r\n"
                response += "\r\n"

                # 准备发送给浏览器的数据---body
                # response += "hahaha"

                # 将header发送给浏览器
                new_socket.send(response.encode("utf-8"))
                # 将body发送给浏览器
                new_socket.send(html_content)
        else:
            # 如果是以.html结尾，那么就认为是动态资源的请求

            env = dict()
            env["PATH_INFO"] = file_name
            body = self.application(env, self.set_response_header)

            header = "HTTP/1.1 %s\r\n" % self.status

            for temp in self.headers:
                header += "%s:%s\r\n" % (temp[0], temp[1])

            header += "\r\n"

            response = header + body
            new_socket.send(response.encode("utf-8"))

        # 关闭套接
        new_socket.close()

    def set_response_header(self, status, headers):
        self.status = status
        self.headers = [("server", "mini_web v8.8")]
        self.headers += headers

    def run_forever(self):
        """用来完成整体控制"""
        while True:
            # 等待客户端请求
            new_socket, client_addr = self.tcp_server_socket.accept()
            p = multiprocessing.Process(target=self.service_client, args=(new_socket,))
            p.start()

            new_socket.close()
        # 关闭监听套接字
        self.tcp_server_socket.close()


def main():
    """控制整体，创建一个web服务器对象，然后调用这个对象的run_forever方法运行"""
    if len(sys.argv) == 3:
        try:
            port = int(sys.argv[1])
            frame_app_name = sys.argv[2]
        except Exception as e:
            print("端口输入错误。。。", e)
            return
    else:
        print("请按照以下方式运行：")
        print("python xxx.py 7890 mini_frame:application")
        return

    ret = re.match(r"([^:]+):(.*)", frame_app_name)
    if ret:
        frame_name = ret.group(1)
        app_name = ret.group(2)
    else:
        print("请按照以下方式运行：")
        print("python xxx.py 7890 mini_frame:application")
        return

    with open("./web_server.conf") as f:
        conf_info = eval(f.read())
    # 此时conf_info是一个字典，里面的数据为：
    # {
    #     "static_path": "./static"
    #      "dynamic_path": "./dynamic"
    # }

    sys.path.append(conf_info["dynamic_path"])

    frame = __import__(frame_name)
    app = getattr(frame, app_name)

    wsgi_server = WSGIServer(port, app, conf_info["static_path"])
    wsgi_server.run_forever()


if __name__ == '__main__':
    main()
