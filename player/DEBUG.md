# DEBUG

## Networking

- Make sure the ip address is right in config.py
- Check you are getting messages:

```
socat UDP4-RECV:6005,reuseaddr,bind=192.168.1.140 STDOUT,nonblock=1
``` 

## CPU

Asyncio loops can make excessive CPU load when running with sleep(0). Test with test.py the delays needed for your CPU to run smooth without much lag.