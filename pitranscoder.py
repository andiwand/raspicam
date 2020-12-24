from picamera import mmal, mmalobj as mo

source = mo.MMALPythonSource('/data/1543232646.mjpeg')

target = mo.MMALPythonTarget('/data/1543232646.h264')

print('decoder init ...')
decoder = mo.MMALVideoDecoder()
decoder.inputs[0].format = mmal.MMAL_ENCODING_MJPEG
decoder.inputs[0].framesize = (1296, 972)
decoder.inputs[0].framerate = 25
decoder.inputs[0].commit()
decoder.outputs[0].copy_from(decoder.inputs[0])
#decoder.outputs[0].format = mmal.MMAL_ENCODING_I420
decoder.outputs[0].commit()
print('decoder set.')

print('encoder init ...')
encoder = mo.MMALVideoEncoder()
encoder.inputs[0].format = mmal.MMAL_ENCODING_I420
#encoder.inputs[0].framesize = (640, 480)
encoder.inputs[0].commit()
encoder.outputs[0].copy_from(encoder.inputs[0])
encoder.outputs[0].format = mmal.MMAL_ENCODING_H264
encoder.outputs[0].bitrate = 17000000
encoder.outputs[0].commit()
p = encoder.outputs[0].params[mmal.MMAL_PARAMETER_PROFILE]
p.profile[0].profile = mmal.MMAL_VIDEO_PROFILE_H264_HIGH
p.profile[0].level = mmal.MMAL_VIDEO_LEVEL_H264_41
encoder.outputs[0].params[mmal.MMAL_PARAMETER_PROFILE] = p
encoder.outputs[0].params[mmal.MMAL_PARAMETER_VIDEO_ENCODE_INLINE_HEADER] = True
encoder.outputs[0].params[mmal.MMAL_PARAMETER_INTRAPERIOD] = 30
encoder.outputs[0].params[mmal.MMAL_PARAMETER_VIDEO_ENCODE_INITIAL_QUANT] = 22
encoder.outputs[0].params[mmal.MMAL_PARAMETER_VIDEO_ENCODE_MAX_QUANT] = 22
encoder.outputs[0].params[mmal.MMAL_PARAMETER_VIDEO_ENCODE_MIN_QUANT] = 22
print('encoder set.')

print(source)
print(decoder)
print(encoder)
print(target)

print('connect ...')
decoder.inputs[0].connect(source.outputs[0])
print(1)
encoder.inputs[0].connect(decoder.outputs[0])
print(2)
target.inputs[0].connect(encoder.outputs[0])
print('enable connections ...')
target.connection.enable()
encoder.connection.enable()
decoder.connection.enable()
source.connection.enable()
print('enable filters ...')
target.enable()
encoder.enable()
decoder.enable()
source.enable()

print('wait ...')
source.wait()
target.wait()

target.disable()
encoder.disable()
decoder.disable()
source.disable()
target.inputs[0].disconnect()
encoder.inputs[0].disconnect()
decoder.inputs[0].disconnect()
source.inputs[0].disconnect()

