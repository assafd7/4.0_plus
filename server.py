import socket
import os
import logging

logging.basicConfig(filename='server2.log', level=logging.DEBUG,
                    format="%(asctime)s -- %(lineno)d -- %(levelname)s - %(message)s")

MAX_PACKET = 1024
QUEUE_SIZE = 10
IP = '0.0.0.0'
PORT = 80
SOCKET_TIMEOUT = 2
WEB_ROOT = r"C:\Cyber\4.0\WEB-ROOT"
DEFAULT_URL = WEB_ROOT + r"\index.html"
CONTENT_TYPES = {
    "html": "text/html; charset=utf-8",
    "jpg": "image/jpeg",
    "css": "text/css",
    "js": "text/javascript; charset=UTF-8",
    "txt": "text/plain",
    "ico": "image/x-icon",
    "gif": "image/gif",
    "png": "image/png"
}
CONTENT_TYPES_BACKWARDS = {v: k for k, v in CONTENT_TYPES.items()}
REDIRECTION_DICTIONARY = {"/moved": "/index.html"}
REQUEST_VERBS = ['GET', 'POST']


def get_file_data(file_path):
    """
    receives file path
    returns file data in bytes
    """
    try:
        with open(file_path, 'rb') as file:
            file_data = file.read()
        return file_data
    except Exception as e:
        logging.error(f"Error reading file: {e}")
        return f"Error: {e}"


def file_exists_in_folder(file_path):
    """
    receives file path
    returns bool if file exists
    """
    return os.path.exists(file_path)


def cont_type_finder_file(uri):
    """
    receives file uri
    returns file type
    """
    folders_list = uri.split("/")
    folders_list = folders_list[-1].split(".")
    file_extension = folders_list[-1]
    if file_extension in CONTENT_TYPES:
        content_type_header = CONTENT_TYPES[file_extension]
        return content_type_header
    else:
        return "invalid file extension"


def find_query_params(uri):
    """
    Args:
        uri: uri containing query parameters from client

    Returns:
        dict of parameters and their values

    """
    all_query_params = uri.split("?")
    embedded_query_params = all_query_params[1]
    query_params_list = embedded_query_params.split('&')
    result_dict = {}
    for item in query_params_list:
        key, value = item.split('=')
        result_dict[key.strip()] = value.strip()
    return result_dict


def calculate_area(params):
    """
    Args:
        params: sufficient query parameters from client to make area calcs

    Returns:
        calculated area
    """
    area = int(params['height']) * int(params['width']) / 2
    return area


def has_query_params(uri):
    """
    checks if an uri has query params
    receives: uri
    return: bool if it has
    """
    return '?' in uri


def calculate_content_length(data, is_file_path):
    """
    receives a file path or a certain text and a flag to distinguish
    returns the length of the data
    """
    if is_file_path:
        try:
            logging.debug(f"file path is {data}")
            file_size = os.path.getsize(data)
            return file_size
        except Exception as e:
            logging.error(f"Error calculating content length: {e}")
            return None
    else:
        logging.debug(f"data is {data}")
        return len(data)


def image_request(file_name):
    """
    receives file's full name
    returns files data
    """
    upload_folder = r"c:\upload"
    file_path = os.path.join(upload_folder, file_name)

    try:
        with open(file_path, 'rb') as file:
            file_data = file.read()

        return file_data

    except FileNotFoundError:
        logging.error("File {} not found in the 'upload' folder.".format(file_name))
        return False
    except Exception as e:
        logging.error(f"Error sending file '{file_name}': {e}")


def handle_get(resource, client_socket):
    """
    handles the GET request line and sends appropriate response
    receives resource and client socket
    returns none
    """
    if resource == '' or (resource == "/"):
        uri = DEFAULT_URL
        empty_uri = True
    else:
        uri = resource
        empty_uri = False

    is_file = False
    msg_body = b''
    error_message = b''
    file_path = ""

    if has_query_params(uri):
        request = uri.split('?')
        request = request[0]
    else:
        request = uri

    # problems or services
    if request == '/forbidden':
        error_message = "HTTP/1.1 403 FORBIDDEN\r\n\r\n\r\n".encode()
        logging.debug("Sent 403 FORBIDDEN response")

    elif request in REDIRECTION_DICTIONARY:
        error_message = "HTTP/1.1 302 REDIRECTION\r\nlocation: /\r\n\r\n\r\n".encode()
        logging.debug("Sent 302 REDIRECTION response")

    elif request == "/error":
        error_message = "HTTP/1.1 500 INTERNAL SERVER ERROR\r\n\r\n\r\n".encode()
        logging.debug("Sent 500 INTERNAL SERVER ERROR response")

    elif request == "/calculate-next":
        if has_query_params(uri):
            num = find_query_params(uri)
            if num["num"].isdigit():
                msg_body = int(num["num"]) + 1
            else:
                error_message = "HTTP/1.1 400 BAD REQUEST\r\n\r\n\r\n".encode()
        else:
            logging.debug(f"no query params, uri = {uri}")

    elif request == "/calculate-area":
        if has_query_params(uri):
            params = find_query_params(uri)
            if params["height"].isdigit() and params["width"].isdigit():
                area = calculate_area(params)
                msg_body = area
            else:
                error_message = "HTTP/1.1 400 BAD REQUEST\r\n\r\n\r\n".encode()
        else:
            logging.debug("no query params, uri = {}".format(uri))

    elif request == "/image":
        is_file = True
        if has_query_params(uri):
            params = find_query_params(uri)
            image_name = params["image-name"]
            msg_body = image_request(image_name)
            if not msg_body:
                error_message = "HTTP/1.1 404 NOT FOUND\r\n\r\n\r\n".encode()
        else:
            logging.debug("no query params, uri = {}".format(uri))

    else:
        is_file = True
        if not empty_uri:
            file_path = WEB_ROOT + uri
            logging.debug(f"a {file_path}")
        else:
            file_path = uri
            logging.debug(f"b {file_path}")

        if not file_exists_in_folder(file_path):
            error_message = "HTTP/1.1 404 NOT FOUND\r\n\r\n\r\n".encode()
            logging.debug(f"Sent 404 NOT FOUND response {uri}")
        else:
            msg_body = get_file_data(file_path)

    if error_message == b'':
        if is_file:
            logging.debug("is file true")
            content_type_header = cont_type_finder_file(uri)
            content_length_header = calculate_content_length(file_path, is_file)
            logging.debug("clac complete")
        else:
            logging.debug("is file false")
            msg_body = str(msg_body).encode()
            content_type_header = "text/html; charset=utf-8"
            content_length_header = calculate_content_length(msg_body, is_file)

        response_message = (f"HTTP/1.1 200 OK\r\nContent-Type: {content_type_header}\r\nContent-Length: "
                            f" {content_length_header}\r\n\r\n")
        logging.debug(f"response_message is {response_message}")
        client_socket.send(response_message.encode())
        client_socket.sendall(msg_body)
        logging.debug("Sent 200 OK response with msg body")
    else:
        logging.debug("there is an error")
        client_socket.send(error_message)
        logging.error("sent error message {}".format(error_message))


def organize_headers(headers_embd):
    """
    organize the headers of the message and their values sent by the client
    receives: headers embedded
    return dict of headers
    """
    headers_dict = {}
    lines = headers_embd.split('\r\n')
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            headers_dict[key.strip()] = value.strip()

    logging.debug(f"headers are {headers_dict}")

    return headers_dict


def upload_to_folder(file_type, file_bytes, file_name):
    """
    add a given file to 'upload' folder
    receives file type (extension without a dot at the start), bytes and name
    return none
    """

    logging.debug(f"file name: {file_name} file type: {file_type}")

    folder_path = r'c:\upload'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    file_path = os.path.join(folder_path, f"{file_name}.{file_type}")
    logging.debug(f"file path is: {file_path} ")
    logging.debug(f"file_bytes are: {file_bytes}")
    try:
        with open(r"c:\upload\test_file.txt", 'w') as file:
            file.write(str(file_bytes))
        with open(file_path, 'wb') as file:
            file.write(file_bytes)
        print(f"File saved successfully at: {file_path}")
    except Exception as e:
        print(f"Error saving file: {e}")


def handle_post(resource, client_socket, headers_and_body_embd):
    """
    handle the POST request and calls functions to deal with it
    receives a resource, client socket and the body and headers and embedded
    returns none
    """
    headers_dict = headers_and_body_embd[0]
    msg_body = headers_and_body_embd[1]

    file_name_dict = find_query_params(resource)
    file_name = file_name_dict['file-name'].split(".")[0]
    logging.debug(f"headers are {headers_dict}")
    file_type = CONTENT_TYPES_BACKWARDS[headers_dict["Content-Type"]]  # check why returning plain

    upload_to_folder(file_type, msg_body, file_name)
    client_socket.send("HTTP/1.1 200 OK\r\n\r\n\r\n".encode())
    logging.debug("sent HTTP/1.1 200 OK and uploaded ")


def handle_client_request(cmd_and_res, client_socket, headers_and_body):
    """
    handles client request and call functions to handle response
    receives the command and resource of the request
    returns none
    """
    command = cmd_and_res[0]
    resource = cmd_and_res[1]

    logging.debug(f"comd = {command}, resource = {resource}")
    if command == 'GET':
        handle_get(resource, client_socket)
        logging.debug("passed handle get")
    elif command == 'POST':
        handle_post(resource, client_socket, headers_and_body)
    else:
        logging.debug(f"other command is <{command}>")


def validate_http_request(request):
    request_parts = request.split(" ")
    logging.debug(f"{request_parts}")
    if len(request_parts) != 3 or request_parts[0] not in REQUEST_VERBS or request_parts[2] != "HTTP/1.1\r\n":
        return False, None
    else:
        if request_parts[0] == 'GET':
            cmd_and_res = [request_parts[0], request_parts[1]]
            return True, cmd_and_res
        elif request_parts[0] == 'POST':
            cmd_and_res = [request_parts[0], request_parts[1]]
            return True, cmd_and_res


def socket_handle(client_socket):
    """
    handles initial socket request
    receives: client socket
    return: request line received, bool if there is an ongoing connection and tuple of headers dict and message body
    """
    try:
        message = ''
        while "\r\n" not in message:
            message += client_socket.recv(1).decode()

        headers = ''
        while '\r\n\r\n' not in headers:
            headers += client_socket.recv(1).decode()
        headers_embd = headers[:-4]
        headers_dict = organize_headers(headers_embd)
        logging.debug(f"headers dict: {headers_dict}")

        if "Content-Length" in headers_dict:
            body_length = int(headers_dict["Content-Length"])
            body = b''
            while body_length > 1024:
                body += client_socket.recv(MAX_PACKET)
                body_length -= 1024
            if body_length <= 1024:
                body += client_socket.recv(body_length)
        else:
            logging.debug("no body in message")
            body = b''

        headers_and_body = (headers_dict, body)

        return message, True, headers_and_body
    except Exception as e:
        logging.error(f"Error handling socket: {e}")
        return f"Error: {e}", False, "no rest of message"


def handle_client(client_socket):
    """
    handles client request
    receives: client socket
    returns: none
    """
    logging.debug('Client connected')
    while True:
        client_decoded_request, connection, headers_and_body = socket_handle(client_socket)
        if not connection:
            logging.debug(client_decoded_request)
            return
        valid_http, cmd_and_res = validate_http_request(client_decoded_request)
        logging.debug(f"{valid_http} {cmd_and_res}")
        if valid_http:
            logging.debug('Got a valid HTTP request')
            handle_client_request(cmd_and_res, client_socket, headers_and_body)
        else:
            client_socket.send("HTTP/1.1 400 BAD REQUEST\r\n".encode())
            logging.debug("Sent 400 BAD REQUEST response")
            break


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((IP, PORT))
        server_socket.listen(QUEUE_SIZE)
        logging.info("Listening for connections on port %d" % PORT)

        while True:
            client_socket, client_address = server_socket.accept()
            try:
                logging.debug('New connection received')
                client_socket.settimeout(SOCKET_TIMEOUT)
                handle_client(client_socket)
                logging.debug("passed handle")
            except socket.error as err:
                logging.error('Received socket exception - ' + str(err))
            finally:
                client_socket.close()
    except TimeoutError:
        server_socket.close()
    except socket.error as err:
        logging.error('Received socket exception - ' + str(err))
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
