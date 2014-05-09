from __future__ import print_function

from obsremote import OBSProxy

if __name__ == '__main__':
  url = "ws://127.0.0.1:4444/"
  password = "admin" # default obs remote password

  obsproxy = OBSProxy(url)
  try:
    obsproxy.connect() # OBSProxy creates own background thread
    ok, response = obsproxy.authenticate(password)
    if not ok:
      print("Authentication has failed:", response)
    else:

      print("OBS client is running, Ctrl^C to stop")



      # send request using python named arguments
      obsproxy.call("ToggleMute", channel="microphone")

      # send request and process response
      ok, response = obsproxy.call("GetStreamingStatus")
      if response["streaming"]:
        print("on air!")
      else:
        print("off air")

      # if there's hyphen in argument name
      # you can use slightly different interface
      obsproxy.call("SetCurrentScene", { "scene-name": "Scene" })

      # set callbacks to server updates
      obsproxy.on("StreamStarting", lambda msg: print("started streaming"))
      obsproxy.on("StreamStopping", lambda msg: print("stopped streaming"))

      

      obsproxy.run_forever() # listen for updates
  except KeyboardInterrupt:
    print("OBS client is shutting down")
  finally:
    obsproxy.close()
    obsproxy.run_forever() # acts like thread.join
    print("OBS client stopped")