import routes

app = routes.app
app.debug = True

if __name__=="__main__":
    app.run(debug=True)
