import json
import base64

def encode(src, config):
	data = {}
	for k, v in config.items():
		if isinstance(v, str):
			with open(f"{src}/{v}", "rb") as f:
				data[k] = base64.b64encode(f.read()).decode()
		elif isinstance(v, list):
			data[k] = []
			for p in v:
				with open(f"{src}/{p}", "rb") as f:
					data[k].append(base64.b64encode(f.read()).decode())
		elif isinstance(v, dict):
			data[k] = encode(src, v)
	return data

def update(path, *data):
	try: 
		with open(path, "r") as file: media = json.loads(file.read())
	except:
		media = {}
	for d in data: media.update(d)
	with open(path, "w") as file: file.write(json.dumps(media, indent=4))

graphics = {
	"startbg": "startbg.png",
	"signboardpole": "signboardpole.png",
	"snow": ["snow1.png", "snow2.png"],
	"signboard": ["signboard1.png", "signboard2.png", "signboard3.png"],
	"cancelbutton": "cancelbutton.png",
}
audio = {
	"m1": "m1.mp3"
}

update("media.json", encode("graphics", graphics), encode("audio", audio))
