encoder = mo.MMALImageEncoder()
encoder.inputs[0].format = mmal.MMAL_ENCODING_RGB24
encoder.inputs[0].framesize = (640, 480)
encoder.inputs[0].commit()
encoder.outputs[0].copy_from(encoder.inputs[0])
encoder.outputs[0].format = mmal.MMAL_ENCODING_JPEG
encoder.outputs[0].commit()
encoder.outputs[0].params[mmal.MMAL_PARAMETER_JPEG_Q_FACTOR] = 90

rgb_data = io.open('image.data', 'rb')
jpg_data = io.open('image.jpg', 'wb')
def image_callback(port, buf):
    jpg_data.write(buf.data)
    return bool(buf.flags & mmal.MMAL_BUFFER_HEADER_FLAG_FRAME_END)

encoder.outputs[0].enable(image_callback)

encoder.inputs[0].enable(lamdba port, buf: True)
buf = encoder.inputs[0].get_buffer()
buf.data = rgb_data.read()
encoder.inputs[0].send_buffer(buf)

encoder.outputs[0].disable()
encoder.inputs[0].disable()
jpg_data.close()
rgb_data.close()

