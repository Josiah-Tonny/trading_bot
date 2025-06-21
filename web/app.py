from flask import Flask, render_template, request, jsonify


app = Flask(__name__)
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/message', methods=['POST'])
def api_message():
    data = request.json
    # Process the incoming message
    response = {"reply": f"You said: {data.get('message')}"}
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)