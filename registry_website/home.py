# Root endpoint with fallback HTML
#@app.get("/", response_class=HTMLResponse)
#async def root(request: Request):
#    if templates:
#        return templates.TemplateResponse("index.html", {"request": request})
#    else:
 #        return HTMLResponse('''
<!DOCTYPE html>
<html>
<head>
    <title>MindRoot Registry</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; }
        h1 { color: #333; }
        .api-link { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 MindRoot Registry</h1>
        <p>Welcome to the MindRoot Plugin and Agent Registry</p>
        <p><a href="/docs" class="api-link">View API Documentation</a></p>
        <h2>Quick Stats</h2>
        <p>Visit <a href="/stats">/stats</a> for registry statistics</p>
    </div>
</body>
</html>
        ''')

