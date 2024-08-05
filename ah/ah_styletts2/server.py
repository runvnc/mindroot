from flask import Flask, request, Response

app = Flask(__name__)

if __name__ == '__main__':
    app.run()

@app.route("/")
def hello():
  return ''

@app.route('/question')
def askQuestion():
  def stream():
    pass
  return Response(stream(), mimetype='text/event-stream')

import base64
from scipy.io.wavfile import write

def ndarrayToBase64(arr):
    bytes_wav = bytes()
    byte_io = io.BytesIO(bytes_wav)
    write(byte_io, SAMPLE_RATE, arr)
    wav_bytes = byte_io.read()
    audio_data = base64.b64encode(wav_bytes).decode('UTF-8')
    return audio_data

import openai

CHAR_BUFFER_LEN = 100

def generateAudioSseEvent(text):
    if not text:
      return 'data: %s\n\n' % json.dumps({"text": ""})
    audio = ndarrayToBase64(textToSpeech(text))
    return 'data: %s\n\n' % json.dumps({"audio": audio})

@app.route('/question')
def askQuestion():
    args = request.args
    question = args.get('question', 'How far is the moon from mars?')

    def stream():
        res = openai.ChatCompletion.create(
          model="gpt-3.5-turbo",
          messages=[{"role": "user", "content": question}],
          stream=True,
        )
        buff = ''
        for chunk in res:
            if len(chunk.choices[0]) and chunk.choices[0].delta and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                yield 'data: %s\n\n' % json.dumps({"text": content})
                if len(chunk.choices[0]) and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    buff += content
                    # Try to keep sentences together, making the voice flow smooth
                    last_delimiter_index = max(buff.rfind(p) for p in end_of_sentence_punctuation)
                    if last_delimiter_index == -1 and len(buff) < CHAR_BUFFER_LEN:
                        continue
                    current = buff[:last_delimiter_index + 1]
                    buff = buff[last_delimiter_index + 1:]
                    yield generateAudioSseEvent(current)
        yield generateAudioSseEvent(buff)
        yield 'data: %s\n\n' % json.dumps({"text": "", "audio": "", "done": True})
    return Response(stream(), mimetype='text/event-stream')


@app.route("/")
def hello():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <title>Realtime Text->Audio Generator</title>
    </head>
    <body>
    <input type="text" id="inputField" placeholder="Enter question here">
    <button onclick="sendMessage()">Send</button>
    <div id="result"></div>
    <script>
        var audioQueue = []
        var playing = false;
        const audioElement = new Audio();
        var currentIndex = 0;
        function playNextAudio() {
            if (currentIndex < audioQueue.length) {
              audioElement.src = audioQueue[currentIndex];
              audioElement.play();
              currentIndex++;
    
              audioElement.onended = function() {
                  playNextAudio();
              };
              
            } else {
              playing = false;
            }
        }
    
        function sendMessage() {
          var inputValue = document.getElementById('inputField').value;
          const queryString = '?question=' + encodeURIComponent(inputValue)
          var eventSource = new EventSource('/question' + queryString)
          eventSource.onmessage = function(event) {
            var message = JSON.parse(event.data);
            if (message.done) {
              console.log('Closing session')
              eventSource.close()
            }
            if (message.text) {
              document.getElementById("result").innerHTML += message.text;
            }
            if (message.audio) {
              audioQueue.push("data:audio/wav;base64," + message.audio)
              if (!playing) {
                playing = true;
                playNextAudio()
              }
            }
            console.log('Message: ' + message.text);
          };
        }
    </script>
    </body>
    </html>
    """
    return html
