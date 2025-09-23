from app.api.main import app

with app.test_client() as c:
    # preflight OPTIONS for /api/chat/stream
    rv = c.open('/api/chat/stream', method='OPTIONS', json={})
    print('/api/chat/stream OPTIONS status, headers: ', rv.status_code, rv.headers.get('Access-Control-Allow-Origin'))

    # POST to /api/chat/stream with minimal body
    rv = c.post('/api/chat/stream', json={'query':'hi'}, environ_base={'REMOTE_ADDR':'127.0.0.1'})
    print('/api/chat/stream POST status, headers: ', rv.status_code, rv.headers.get('Access-Control-Allow-Origin'))

    # POST to /api/chat (non-stream) - expect json response
    rv = c.post('/api/chat', json={'query':'hi'}, environ_base={'REMOTE_ADDR':'127.0.0.1'})
    print('/api/chat POST status, headers: ', rv.status_code, rv.headers.get('Access-Control-Allow-Origin'))
