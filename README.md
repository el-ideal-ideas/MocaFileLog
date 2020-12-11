# MocaFileLog
Save, Get, log messages via HTTP protocol.
MocaFileLog based on the [Sanic](https://github.com/huge-success/sanic) web framework, Sanic is a higher performance web framework.

### Requirements
- python3.7 or higher (recommended python3.8)
- Linux or macOS (Don't support windows)

### Install
```
git clone https://github.com/el-ideal-ideas/MocaFileLog.git
cd MocaFileLog
python3 -m pip install --upgrade -r requirements.txt
```

### HTTP Usage
You can use this system via HTTP or HTTPS protocol.
If you want to send some parameter such as api-key.
You can use `URL parameter` or `Form parameter` or `json body`

##### Config sample
```json
{
  "sample1": {
    "host": "0.0.0.0",
    "port": 5700,
    "use_ipv6": false,
    "file": "sample1.log",
    "level": 0
  },
  "sample2": {
    "host": "0.0.0.0",
    "port": 5701,
    "use_ipv6": false,
    "file": "sample2.log",
    "level": 0
  }
}
```
If you want to write log messages to sample1.log,  you need to use port 5700.
If you want to write log messages to sample2.log,  you need to use port 5701.

- `http://<your-ip>:<your-port>/moca-file-log/details`
    - This URI can get details information about the log file.
    - parameters
        - api_key (string | max-length: 1024 | required) your API key.
        - root_pass (string | max-length: 1024 | required) the root password of MocaFileLog.
        
        
- `http://<your-ip>:<your-port>/moca-file-log/save-log`
    - This URI can save log message to the log file.
    - parameters
        - api_key (string | max-length: 1024 | required) your API key.
        - level (int | 0, 1, 2, 3, 4 | optional) the level of log message, 
            0: DEBUG, 1: INFO, 2: WARNING, 3: ERROR, 4: CRITICAL
        - message (string | max-length: 8192 | required) the log message.
    

- `http://<your-ip>:<your-port>/moca-file-log/save-logs`
    - This URI can save log messages to the log file.
    - parameters
        - logs (list of dict | max-length: 1024 | required)
            - a list of log messages
            - [{"level": 0, "message": "log message"}, {"level": 0, "message": "log message"}]
            

- `http://<your-ip>:<your-port>/moca-file-log/download-logs`
    - This URI can download the log file.
    - parameters
        - api_key (string | max-length: 1024 | required) your API key.
        - root_pass (string | max-length: 1024 | required) the root password of MocaFileLog.
    

- `http://<your-ip>:<your-port>/moca-file-log/get-logs`
    - This URI can get all log messages.
    - parameters
        - api_key (string | max-length: 1024 | required) your API key.
        - root_pass (string | max-length: 1024 | required) the root password of MocaFileLog.
    

- `http://<your-ip>:<your-port>/moca-file-log/get-latest-logs`
    - This URI can get latest 1024 log messages.
    - parameters
        - api_key (string | max-length: 1024 | required) your API key.
        - root_pass (string | max-length: 1024 | required) the root password of MocaFileLog.
    

- `http://<your-ip>:<your-port>/moca-file-log/clear-logs`
    - This URI can remove all logs.
    - parameters
        - api_key (string | max-length: 1024 | required) your API key.
        - root_pass (string | max-length: 1024 | required) the root password of MocaFileLog.


### Console Usage
- `python3 moca.py version`
    - Show the version of this system.
- `python3 moca.py update`
    - Update modules via pip
- `python3 moca.py update-system`
    - Get the latest version of code from github and update system.
- `python3 moca.py reset-system`
    - Reset all data and update system.
- `python3 moca.py run <the name of log>`
    - Run this system.
- `python3 moca.py start`
    - Run this system on background.
- `python3 moca.py stop`
    - Stop background process.
- `python3 moca.py restart`
    - Restart background process.
- `python3 moca.py status`
    - Show the status of this system.
- `python3 moca.py turn-on`
    - Stop maintenance mode.
- `python3 moca.py turn-off`
    - Start maintenance mode.
- `python3 moca.py clear-logs`
    - Clear logs

### Log config format
```
{
  "sample1": {
    "host": "0.0.0.0",
    "port": 5700,
    "use_ipv6": false,
    "file": "sample1.log",
    "level": 0
  },
  "the name of log": {
    "host": "the host address of this server.",
    "port": the port of this server,
    "use_ipv6": true or false,
    "file": "the name of the log file",  // If this value is not starts with `/` the path will be starts from the commands folder. 
    "level": the level of the log file, system will only save logs that higher than this level.
  }
}
```
#### After your changed `configs/log.json` will be reloaded automatically.

### API-KEY format
```
{
    "key": string  // The value of api-key.
    "status": true or false  // If the value is false, This api-key will be blocked.
    "allowed_path": a list of string  // A list of allowed paths
    "required": {
      "headers": dict,  // When you use this api-key, All required must contains these headers.
      "args": dict  // When you use this api-key, All required must contains these arguments.
    },
    "ip": * or a list of string  // This api-key can be used from these ip addresses.
    "rate": string  // The rate limit of this api-key.
    "delay": 0  // If this value is not 0, the response will be waiting `delay` seconds.
    "info": string // You can write any information.
}
```

#### After your changed `configs/api_key.json` will be reloaded automatically.

### server.json
```
{
  "ssl": {  // HTTPS configuration.
    "cert": null,
    "key": null
  },
  "debug": false,  // Show debug information.
  "access_log": false,  // Save access log.
  "log_level": 20,  // The logging level of sanic server.
  "auto_reload": false,  // when you changed the source code, reload sanic server.
  "backlog": 100,  // a number of unaccepted connections that the system will allow before refusing new connections.
  "headers": {},  // You can set some headers to all response.
  "access_control_allowed_credentials": true,
  "access_control_allowed_origins": ["https://localhost", "http://localhost", "https://127.0.0.1", "http://127.0.0.1"],
  "access_control_allowed_methods": ["GET", "HEAD", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"],
  "access_control_allow_headers": "*",
  "access_control_max_age": 600,
  "access_control_expose_headers": "*",
  "stream_large_files": false,  // a parameter of sanic static route.
  "rate_limiter_redis_storage": null,  // you can use redis to save the rate limiting data. (When you are using multiple workers, in-memory storage can't share between workers.)
  "pyjs_secret": null, // AES encryption, If the request contains Moca-Encryption header, Middleware will try decrypt the request body.
}
```

### system.json
```
{
  "maintenance_mode": false,  // If the value is true, all requests will get 503 response.
  "maintenance_mode_whitelist": ["127.0.0.1"],  // a ip whitelist of maintenance mode.
  "referer": {  // allowed referer
    "allowed_referer": [
      "https:\/\/localhost",
      "https:\/\/127.0.0.1",
      "http:\/\/localhost",
      "http:\/\/127.0.0.1"
    ],
    "force": false  // If this value is true, all requests must have referer header.
  },
  "force_headers": {  // All requests must have these headers.

  },
  "dos_detect": 5000,  // If the access rate is higher than `dos_detect/seconds`, the target ip will be blocked.
  "root_pass": "mochimochi"  // The root password, If valid root password is in your request, You can use all commands without command-pass checking.
}
```
#### After your changed `configs/system.json` will be reloaded automatically.

### Sanic server configuration.

For more details, you can see https://sanic.readthedocs.io/en/latest/sanic/config.html

| Variable | Default | Description |
| -------- | ------- | ----------- |
| REQUEST_MAX_SIZE | 100000000 | How big a request may be (bytes) |
| REQUEST_BUFFER_QUEUE_SIZE | 100 | Request streaming buffer queue size |
| REQUEST_TIMEOUT | 60 | How long a request can take to arrive (sec) | 
| RESPONSE_TIMEOUT | 60 | How long a response can take to process (sec) |
| KEEP_ALIVE | True | Disables keep-alive when False |
| KEEP_ALIVE_TIMEOUT | 5 | How long to hold a TCP connection open (sec)|
| WEBSOCKET_MAX_SIZE | 2^20 | Maximum size for incoming messages (bytes)|
| WEBSOCKET_MAX_QUEUE | 32 | Maximum length of the queue that holds incoming messages |
| WEBSOCKET_READ_LIMIT | 2^16 | High-water limit of the buffer for incoming bytes |
| WEBSOCKET_WRITE_LIMIT | 2^16 | High-water limit of the buffer for outgoing bytes |
| WEBSOCKET_PING_INTERVAL | 20 | A Ping frame is sent every ping_interval seconds. |
| WEBSOCKET_PING_TIMEOUT | 20 | Connection is closed when Pong is not received after ping_timeout seconds |
| GRACEFUL_SHUTDOWN_TIMEOUT | 15.0 | How long to wait to force close non-idle connection (sec) |
| ACCESS_LOG | True | Disable or enable access log |
| FORWARDED_SECRET | None | Used to securely identify a specific proxy server (see below) |
| PROXIES_COUNT | None | The number of proxy servers in front of the app (e.g. nginx; see below) |
| FORWARDED_FOR_HEADER | "X-Forwarded-For" | The name of "X-Forwarded-For" HTTP header that contains client and proxy ip |
| REAL_IP_HEADER | None | The name of “X-Real-IP” HTTP header that contains real client ip |

#### For reference:
- Apache httpd server default keepalive timeout = 5 seconds
- Nginx server default keepalive timeout = 75 seconds
- Nginx performance tuning guidelines uses keepalive = 15 seconds
- IE (5-9) client hard keepalive limit = 60 seconds
- Firefox client hard keepalive limit = 115 seconds
- Opera 11 client hard keepalive limit = 120 seconds
- Chrome 13+ client keepalive limit > 300+ seconds

### startup, atexit
`startup.py` `startup.sh` will be executed before the api-server started.
`atexit.py` `atexit.sh` will be executed after the api-server stopped.
You can add any code to these files.

### Update
If you want to update your MocaFileLog system.  
Just download the latest source code from this repository, and replace the src directory.  
(Maybe you need to check the latest configs format)

### License (MIT)
MIT License

Copyright 2020.1.17 <el.ideal-ideas: https://www.el-ideal-ideas.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
