from ws4py.client.threadedclient import WebSocketClient
import json
from hashlib import sha256
from base64 import b64encode
from time import sleep

class OBSProxy(WebSocketClient):
  def __init__(self, url, *args, **kwargs):
    # magic
    protocols = kwargs.pop("protocols", ["obsapi"])
    super(OBSProxy, self).__init__(url, protocols=protocols,
                                    *args, **kwargs) # TODO: may throw

    # implementation details
    self._callbacks = {}
    self._pending = {}
    self._counter = 0

  def authenticate(self, password=None):
    ok, authreq_response = self.call("GetAuthRequired")
    if not authreq_response["authRequired"]:
      return True

    if password is None:
      return False # TODO: raise error?

    # authentication is required
    salt = authreq_response["salt"]
    challenge = authreq_response["challenge"]

    # evil magic
    intermediate = b64encode(sha256(password + salt).digest())
    auth = b64encode(sha256(intermediate + challenge).digest())

    ok, auth_response = self.call("Authenticate", auth=auth)
    # if ok then we are autenticated
    # else auth_response is errorstring
    return ok, auth_response


  def call(self, rqtype, message=None, **kwargs):
    if message is None:
      message = kwargs
    message["request-type"] = rqtype
    response = self.llrecv(self.llsend(message))

    assert("status" in response)
    if response["status"] == "ok":
      del response["status"]
      return True, response
    elif response["status"] == "error":
      error = response["error"]
      return False, error
    else:
      raise Exception("unknown response status")


  def on(self, update_type, func):
    if func is None:
      if update_type in self._callbacks:
        del self._callbacks[update_type]
    else:
      self._callbacks[update_type] = func


  # low level data exchange


  def llsend(self, message):
    self._counter += 1
    message_id = str(self._counter)
    message["message-id"] = message_id
    message_string = json.dumps(message)

    self.send(message_string) # TODO: may throw?

    self._pending[message_id] = None
    return message_id


  def llrecv(self, message_id):
    assert(message_id in self._pending)

    message = self._pending[message_id]
    while message is None:
      message = self._pending[message_id]
      sleep(0.1) # TODO: block istead of sleep? and what about timeout?
      # TODO: what if we lose connection before receiving response?

    if message is not None:
      del self._pending[message_id]

    return message


  def received_message(self, recv_message):
    message_string = recv_message.data # ws4py-specific
    message = json.loads(message_string) # TODO: may throw?

    if "message-id" in message:
      # response for client-initiated request
      message_id = message["message-id"]
      del message["message-id"]
      self._pending[message_id] = message
    elif "update-type" in message:
      # server-initiated update
      update_type = message["update-type"]
      del message["update-type"]
      if update_type in self._callbacks:
        self._callbacks[update_type](message) # TODO: unpack message as **kwargs
    else: # unknown message
      pass