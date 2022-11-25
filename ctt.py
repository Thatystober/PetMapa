import clipboard


f = open("_testnow.json", "w")
f.write(clipboard.paste())
f.close()
