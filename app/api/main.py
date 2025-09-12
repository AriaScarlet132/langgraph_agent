from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
	return 'LangGraph 智能体 REST API 服务已启动'

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8000, debug=True)
