import sys
import os
import io
import time
import json
from threading import Condition
import psutil
import picamera
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

def getStatus():
    return {
        'temp_cpu': psutil.sensors_temperatures()['cpu-thermal'][0].current,
        'use_cpu': psutil.cpu_percent() * 1E-2,
        'use_ram': psutil.virtual_memory().percent * 1E-2,
        'free_root': psutil.disk_usage('/').free,
        'free_data': psutil.disk_usage('/data').free
    }

def getData():
    paths = [os.path.join('/data', p) for p in os.listdir('/data') if os.path.isfile(os.path.join('/data', p)) and p.endswith('.mjpeg')]
    return [{'path': os.path.splitext(os.path.basename(p))[0], 'mjpeg_size': os.path.getsize(p), 'encoded': os.path.isfile(os.path.splitext(p)[0] + '.mp4')} for p in paths]

class PreviewOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()
    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class HttpHandler(BaseHTTPRequestHandler):
    index = b"""
<html>
<head>
  <title>raspicam</title>
</head>
<body>
  <img src="/preview.mjpeg"/>
  <br/>
  <button id="record" onclick="onrecord()">record</button>

  <script>
function call(action, callback) {
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (xhttp.readyState != 4) {
      return;
    }
    if (xhttp.status != 200) {
      return;
    }
    callback(xhttp.responseText);
  }
  xhttp.open("GET", "/action/" + action, true);
  xhttp.send(null);
}

bt_record = document.getElementById("record");
function onrecord() {
  bt_record.disabled = true;
  if (bt_record.innerHTML === "record") {
    call("record", record);
  } else {
    call("stop", stop);
  }
}
function record(response) {
  console.log(response);
  bt_record.innerHTML = "stop";
  bt_record.disabled = false;
}
function stop(response) {
  console.log(response);
  bt_record.innerHTML = "record";
  bt_record.disabled = false;
}
  </script>
</body>
</html>
"""
    def nextRecordingPath(self):
        return '/data/%d.mjpeg' % time.time()

    def do_GET(self):
        if self.path == '/preview.mjpeg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-type','multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()

            try:
                while True:
                    with preview.condition:
                        preview.condition.wait()
                        frame = preview.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                print('removed preview client %s with %s' % (self.client_address, str(e)))
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write(self.index)
        elif self.path == '/action/status':
            self.send_response(200)
            self.end_headers()
            status = json.dumps(getStatus())
            self.wfile.write(status.encode('us-ascii'))
        elif self.path == '/action/record':
            path = self.nextRecordingPath()
            camera.start_recording(path, format='mjpeg', splitter_port=1)
            camera.wait_recording(10)
            self.send_response(200)
            self.end_headers()
        elif self.path == '/action/stop':
            camera.stop_recording(splitter_port=1)
            self.send_response(200)
            self.end_headers()
        else:
            self.send_error(404)
            self.end_headers()

class ThreadedHttpServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    allow_reuse_addrss = True
    daemon_threads = True

def main():
    preview_resolution = (640, 480)

    global camera
    camera = picamera.PiCamera()
    camera.resolution = (1296, 972)#(1920, 1080)
    camera.framerate = 42#30

    global preview
    preview = PreviewOutput()
    camera.start_recording(preview, format='mjpeg', splitter_port=2, resize=preview_resolution)

    try:
        server = ThreadedHttpServer(('0.0.0.0', 8080), HttpHandler)
        print('server started')
        server.serve_forever()
    finally:
        try:
            camera.stop_recording(splitter_port=2)
            camera.stop_recording(splitter_port=1)
        except:
            pass

if __name__ == '__main__':
    main()

