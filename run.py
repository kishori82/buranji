import routes

app = routes.app
app.debug = True
app.port = 6000

if __name__=="__main__":
    app.run()
